"""Synthetic journal tests: no API, dispatch, workflow or production writes."""
import copy
import json
import os
from pathlib import Path
import tempfile
from unittest.mock import patch
import unittest
from datetime import datetime, timedelta, timezone
from email.utils import format_datetime
from signalboard.twitterapi_paging import initialize_state, _scope
from scripts.twitterapi_schedule_plan import plan_next

NOW=datetime(2026,11,15,tzinfo=timezone.utc)
class Store:
    def __init__(self,state):self.state=state;self.reads=0
    def load(self):self.reads+=1;return copy.deepcopy(self.state),0

class Tests(unittest.TestCase):
    def setUp(self):
        self.policy={'grant_id':'synthetic','credit_limit':30000,'expires_at':(NOW+timedelta(days=7)).isoformat(),
            'max_pages_per_window':1,'mode':'recovery','max_balance_reads':0,'preflight_mode':'dashboard_evidence',
            'recharge_credits':0,'bonus_only':True,'no_payment_instrument_verified':True,'verified_bonus_credits':100000,
            'windows':[{'handle':h,'start':(NOW+timedelta(days=d)).isoformat(),'end':(NOW+timedelta(days=d+1)).isoformat()}
                for h in ('jukan05','aleabitoreddit') for d in (-2,-1,0)]}
        self.store=Store(initialize_state(self.policy))
    def plan(self):return plan_next(self.store,expected_policy=self.policy,now=NOW)
    def cache(self,index,status):
        w=self.store.state['config']['windows'][index];key,scope,start,end=_scope(w['handle'],w['start'],w['end'])
        pending=None;pages=[];cursor=''
        if status=='uncertain':pending={'page':1,'cursor':'','credits':300}
        else:
            more=status in ('page_cap_partial','continuation_ready');cursor='next' if more else ''
            rows=[] if status=='empty_unverified' else [{'id':'123','text':'synthetic',
                'createdAt':format_datetime(start+timedelta(hours=1)),'author':{'userName':w['handle']}}]
            pages=[{'request_cursor':'','next_cursor':cursor,'has_next_page':more,'tweets':rows}]
        self.store.state['windows'][key]={'scope':list(scope),'pages':pages,'pending':pending,'status':status,'cursor':cursor}
        self.store.state['reserved_credits']+=300
    def test_oldest_only_once_per_account_single_read(self):
        r=self.plan();self.assertEqual(r['status'],'ready');self.assertEqual(len(r['selected_windows']),2)
        self.assertTrue(all(w['start']==(NOW-timedelta(days=2)).isoformat() for w in r['selected_windows']))
        self.assertEqual(self.store.reads,1);self.assertFalse(r['daily_promotion'])
    def test_complete_advances_only_that_account(self):
        self.cache(0,'search_exhausted');r=self.plan()
        w=next(w for w in r['selected_windows'] if w['handle']=='jukan05')
        self.assertEqual(w['start'],(NOW-timedelta(days=1)).isoformat())
    def test_any_blocked_account_globally_stops(self):
        for status in ('uncertain','empty_unverified','page_cap_partial'):
            self.setUp();self.cache(0,status)
            self.assertEqual(self.plan()['status'],'stop')
            self.assertEqual(self.plan()['selected_windows'],[])
    def test_interrupted_continuation_stops(self):
        self.policy['max_pages_per_window']=2
        self.store=Store(initialize_state(self.policy));self.cache(0,'continuation_ready')
        self.assertEqual(self.plan()['reason'],'interrupted_account')
    def test_cli_ready_wait_stop_and_sanitized_failure(self):
        from scripts.twitterapi_schedule_plan import main
        old=os.getcwd()
        with tempfile.TemporaryDirectory() as tmp:
            try:
                os.chdir(tmp);Path('config').mkdir()
                Path('config/twitterapi_recovery_grant.json').write_text(json.dumps(self.policy))
                for status,code,ready in [('ready',0,'true'),('wait',0,'false'),('stop',2,'false')]:
                    decision={'status':status,'reason':'synthetic','selected_windows':[]}
                    with patch.dict(os.environ,{'GITHUB_OUTPUT':str(Path(tmp)/'outputs')}), patch('signalboard.twitterapi_state_store.GitBranchStore') as factory, patch('scripts.twitterapi_schedule_plan.plan_next',return_value=decision) as planner:
                        self.assertEqual(main(),code)
                        factory.assert_called_once();planner.assert_called_once()
                        self.assertEqual(json.loads(Path('recovery_output/plan.json').read_text()),decision)
                        self.assertEqual(Path('outputs').read_text().splitlines()[-1],'ready='+ready)
                Path('config/twitterapi_recovery_grant.json').write_text('invalid')
                with patch('signalboard.twitterapi_state_store.GitBranchStore') as factory:
                    self.assertEqual(main(),2);factory.assert_not_called()
                self.assertEqual(json.loads(Path('recovery_output/selected_windows.json').read_text()),[])
            finally:os.chdir(old)
    def test_future_is_never_selected(self):
        for i in (0,1,3,4):self.cache(i,'search_exhausted')
        self.assertEqual(self.plan()['status'],'wait')
    def test_expiry(self):
        self.policy['expires_at']=NOW.isoformat();self.store=Store(initialize_state(self.policy))
        self.assertEqual(self.plan()['reason'],'expired')
    def test_exhausted_budget(self):
        self.policy['credit_limit']=300;self.store=Store(initialize_state(self.policy));self.cache(0,'search_exhausted')
        self.assertEqual(self.plan()['reason'],'budget_exhausted')
    def test_tampered_accounting_rejected(self):
        self.store.state['reserved_credits']=300
        with self.assertRaises(Exception):self.plan()
    def test_no_unknown_balance_calls(self):
        self.policy['max_balance_reads']=1;self.store=Store(initialize_state(self.policy))
        self.assertEqual(self.plan()['reason'],'finite_bonus_scope_invalid')
    def test_noncontiguous_grant_stops(self):
        del self.policy['windows'][1];self.store=Store(initialize_state(self.policy))
        self.assertEqual(self.plan()['reason'],'noncontiguous_grant')

if __name__=='__main__':unittest.main()
