import unittest, tempfile, json
from copy import deepcopy
from pathlib import Path
from unittest.mock import patch
from datetime import datetime,timezone
from scripts import twitterapi_one_reread as m
from signalboard.twitterapi_io import FetchError
from signalboard.twitterapi_paging import _check_state
from test_twitterapi_paging import Store, Client, page, policy, START, END, NOW

class Once(unittest.TestCase):
    def fixture(self):
        from signalboard.twitterapi_paging import advance_page
        s=Store();c=Client(page(more=True,cursor='next'),TimeoutError())
        with patch('signalboard.twitterapi_paging._current_time',return_value=NOW):
            advance_page(c,s,'jukan05',START,END,now=NOW,expected_policy=policy())
            try:advance_page(c,s,'jukan05',START,END,now=NOW,expected_policy=policy())
            except FetchError:pass
        return s
    def run_case(self,data, fail=None):
        s=self.fixture();old=deepcopy(s.state);original=s.load()[1]
        p=s.state['config'];p.update(bonus_only=True,recharge_credits=0,no_payment_instrument_verified=True,max_balance_reads=0)
        old=deepcopy(s.state)
        import hashlib
        digest=hashlib.sha256(json.dumps(p,sort_keys=True,separators=(',',':')).encode()).hexdigest()
        c=Client(data);temp=tempfile.TemporaryDirectory();self.addCleanup(temp.cleanup)
        if fail:s.fail_save=fail
        class Clock:
            @staticmethod
            def now(tz):return NOW
        with patch.object(m,'EXPECTED_REVISION',original),patch.object(m,'CONFIG_SHA',digest),patch.object(m,'SCOPE',['jukan05',START.isoformat(),END.isoformat()]),patch.object(m,'datetime',Clock):
            ok=m.observe(s,lambda:c,NOW,Path(temp.name)/'receipt.json')
            self.assertEqual(s.state['reserved_credits'],900)
            self.assertEqual(s.state['windows'],old['windows']);self.assertEqual(s.state['config'],old['config'])
            with self.assertRaises(FetchError):m.observe(s,lambda:c,NOW,Path(temp.name)/'second.json')
        self.assertEqual(len(c.calls),1)
        return ok,json.loads((Path(temp.name)/'receipt.json').read_text()),s
    def test_empty_repeated_cursor_observed_not_unlocked(self):
        ok,r,s=self.run_case(page([],more=True,cursor='next'));self.assertTrue(ok);self.assertTrue(r['terminal_signal'])
    def test_nonterminal_observation_stops(self):
        ok,r,s=self.run_case(page(more=True,cursor='next2'));self.assertTrue(ok);self.assertFalse(r['terminal_signal'])
    def test_transport_once(self):
        ok,r,s=self.run_case(TimeoutError('secret'));self.assertFalse(ok);self.assertEqual(r['failure_stage'],'transport_or_json');self.assertNotIn('secret',json.dumps(r))
    def test_schema_once(self):
        ok,r,s=self.run_case({'tweets':'bad'});self.assertFalse(ok);self.assertEqual(r['failure_stage'],'schema')
    def test_response_save_failure_never_retry(self):
        ok,r,s=self.run_case(page([]),fail=5);self.assertFalse(ok);self.assertEqual(r['failure_stage'],'persistence')
