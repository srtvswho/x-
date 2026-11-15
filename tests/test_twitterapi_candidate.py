"""Synthetic config proof; never initializes a live grant."""
import copy
import hashlib
import json
import unittest
from datetime import datetime,timezone
from scripts.twitterapi_recovery_candidate import check_config
class ConfigTests(unittest.TestCase):
    def setUp(self):
        self.config={'grant_id':'test-only','max_balance_reads':0,'preflight_mode':'dashboard_evidence','recharge_credits':0,'max_pages_per_window':5,'credit_limit':600,'verified_bonus_credits':1000,
        'expires_at':'2026-11-16T00:00:00Z','bonus_expires_at':'2026-11-17T00:00:00Z',
        'bonus_only':True,'no_payment_instrument_verified':True,'mode':'catchup',
        'windows':[{'handle':'jukan05','start':'2026-11-14T00:00:00Z','end':'2026-11-15T00:00:00Z'}]}
        self.env=dict(RECOVERY_ENABLED='true',GITHUB_EVENT_NAME='workflow_dispatch',
        GITHUB_REF='refs/heads/recovery/twitterapi-free',AI_ENABLED='false',
        ALLOW_EXPENSIVE_AI_JOB='false',AI_DRY_RUN='true',RECOVERY_GRANT_ID='test-only')
        self.env['RECOVERY_CONFIG_SHA256']=self.digest(self.config)
        self.env['RECOVERY_SELECTED_WINDOWS']=json.dumps(self.config['windows'])
        self.now=datetime(2026,11,15,tzinfo=timezone.utc)
    def digest(self,c):return hashlib.sha256(json.dumps(c,sort_keys=True,separators=(',',':')).encode()).hexdigest()
    def test_exact_approved_config(self):self.assertEqual(len(check_config(self.config,self.env,self.now)),1)
    def test_each_gate_required(self):
        for key in self.env:
            env=self.env.copy();del env[key]
            with self.assertRaises(ValueError):check_config(self.config,env,self.now)
    def test_cannot_raise_budget(self):
        c=copy.deepcopy(self.config);c['credit_limit']=900
        with self.assertRaises(ValueError):check_config(c,self.env,self.now)
    def test_expired_bonus(self):
        c=copy.deepcopy(self.config);c['bonus_expires_at']='2026-11-15T00:00:00Z';e=self.env.copy();e['RECOVERY_CONFIG_SHA256']=self.digest(c)
        with self.assertRaises(ValueError):check_config(c,e,self.now)
    def test_duplicate_handle(self):
        c=copy.deepcopy(self.config);c['windows']*=2;e=self.env.copy();e['RECOVERY_CONFIG_SHA256']=self.digest(c)
        with self.assertRaises(ValueError):check_config(c,e,self.now)
    def test_subset_does_not_shrink_full_grant(self):
        c=copy.deepcopy(self.config)
        c['windows'].append({'handle':'aleabitoreddit','start':'2026-11-14T00:00:00Z','end':'2026-11-15T00:00:00Z'})
        e=self.env.copy();e['RECOVERY_CONFIG_SHA256']=self.digest(c)
        self.assertEqual(len(check_config(c,e,self.now)),1)
        self.assertEqual(len(c['windows']),2)
    def test_no_invented_bonus_expiry_required(self):
        c=copy.deepcopy(self.config);del c['bonus_expires_at']
        e=self.env.copy();e['RECOVERY_CONFIG_SHA256']=self.digest(c)
        self.assertEqual(len(check_config(c,e,self.now)),1)
    def test_balance_reads_rejected(self):
        c=copy.deepcopy(self.config);c['max_balance_reads']=1
        e=self.env.copy();e['RECOVERY_CONFIG_SHA256']=self.digest(c)
        with self.assertRaises(ValueError):check_config(c,e,self.now)
    def test_no_master_or_ai(self):
        for key,value in [('GITHUB_REF','refs/heads/master'),('AI_ENABLED','true'),('GITHUB_EVENT_NAME','schedule')]:
            e=self.env.copy();e[key]=value
            with self.assertRaises(ValueError):check_config(self.config,e,self.now)
if __name__=='__main__':unittest.main()

class RunnerTests(unittest.TestCase):
    def test_resumes_cached_pages_then_ingests_without_replaying(self):
        import os,tempfile
        from pathlib import Path
        from datetime import timedelta
        from email.utils import format_datetime
        from unittest.mock import patch
        from signalboard.db import init_db
        from signalboard.twitterapi_paging import initialize_state
        from scripts.twitterapi_recovery_candidate import main
        now=datetime.now(timezone.utc).replace(hour=0,minute=0,second=0,microsecond=0)
        config={'grant_id':'offline-test','max_balance_reads':0,'preflight_mode':'dashboard_evidence','recharge_credits':0,'credit_limit':1500,'expires_at':(now+timedelta(days=1)).isoformat(),
          'max_pages_per_window':5,'mode':'catchup','windows':[{'handle':'jukan05','start':(now-timedelta(days=1)).isoformat(),'end':now.isoformat()}],
          'bonus_only':True,'no_payment_instrument_verified':True,'verified_bonus_credits':2000,
          'bonus_expires_at':(now+timedelta(days=2)).isoformat()}
        class Store:
            def __init__(self):self.state=initialize_state(config);self.rev=0
            def load(self):return copy.deepcopy(self.state),self.rev
            def save(self,state,revision):
                assert revision==self.rev;self.state=copy.deepcopy(state);self.rev+=1;return self.rev
        store=Store();seen=[];balance=[]
        class Fake:
            def credits(self):balance.append(1);return 0
            def get(self,path,params):
                seen.append(params['cursor']);i=len(seen)
                return {'tweets':[{'id':str(9007199254740993123+i),'text':'synthetic fixture',
                   'createdAt':format_datetime(now-timedelta(hours=12)),'author':{'userName':'jukan05'}}],
                   'has_next_page':i<3,'next_cursor':str(i) if i<3 else ''}
        env=dict(RECOVERY_ENABLED='true',GITHUB_EVENT_NAME='workflow_dispatch',GITHUB_REF='refs/heads/recovery/twitterapi-free',
                 AI_ENABLED='false',ALLOW_EXPENSIVE_AI_JOB='false',AI_DRY_RUN='true',RECOVERY_GRANT_ID='offline-test',
                 RECOVERY_SELECTED_WINDOWS=json.dumps(store.state['config']['windows']),
                 RECOVERY_CONFIG_SHA256=hashlib.sha256(json.dumps(store.state['config'],sort_keys=True,separators=(',',':')).encode()).hexdigest(),TWITTERAPI_IO_KEY='fake-offline-only')
        old=os.getcwd()
        with tempfile.TemporaryDirectory() as tmp,patch.dict(os.environ,env,clear=True),patch('signalboard.twitterapi_state_store.GitBranchStore',return_value=store),patch('scripts.twitterapi_recovery_candidate.Client',return_value=Fake()):
            try:
                os.chdir(tmp);Path('recovery_output').mkdir();init_db('recovery_output/working.db')
                self.assertEqual(main(),0)
                self.assertEqual(seen,['','1','2'])
                receipt=json.loads(Path('recovery_output/receipt.json').read_text())
                self.assertEqual(receipt['accounts'][0]['new_persisted'],3)
                self.assertFalse(receipt['production_changed'])
                self.assertEqual(store.state['reserved_credits'],900)
                Path('recovery_output/working.db').unlink()
                init_db('recovery_output/working.db')
                self.assertEqual(main(),0) # fresh snapshot rebuilds all complete cache
                restored=json.loads(Path('recovery_output/receipt.json').read_text())
                self.assertEqual(restored['replayed'][0]['new_persisted'],3)
                self.assertEqual(restored['accounts'][0]['coverage_status'],'already_covered')
                self.assertEqual(len(balance),0)
                self.assertEqual(seen,['','1','2'])
                # New isolated synthetic state: first account hits its page cap;
                # the second authorized account must not be requested.
                config['max_pages_per_window']=2
                config['windows'].append(dict(config['windows'][0],handle='aleabitoreddit'))
                store.state=initialize_state(config);store.rev=0;seen.clear()
                Path('recovery_output/working.db').unlink();init_db('recovery_output/working.db')
                os.environ['RECOVERY_CONFIG_SHA256']=hashlib.sha256(json.dumps(store.state['config'],sort_keys=True,separators=(',',':')).encode()).hexdigest()
                os.environ['RECOVERY_SELECTED_WINDOWS']=json.dumps(store.state['config']['windows'])
                self.assertEqual(main(),2)
                self.assertEqual(seen,['','1'])
                stopped=json.loads(Path('recovery_output/receipt.json').read_text())
                self.assertEqual(stopped['stop_reason'],'page_cap_partial')
                self.assertEqual(len(stopped['accounts']),1)
            finally:os.chdir(old)
