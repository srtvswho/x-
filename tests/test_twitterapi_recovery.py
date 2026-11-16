import tempfile
import unittest
from datetime import datetime, timezone
from signalboard.twitterapi_io import FetchError
from signalboard.twitterapi_recovery import CreditLedger, LedgerBudget, HANDLES, plan_windows
NOW=datetime(2026,11,15,tzinfo=timezone.utc)
class RecoveryTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.path=self.tmp.name+'/quota.db';self.ledger=CreditLedger(self.path)
        self.ledger.create_grant('approved-test',600,'2026-11-16T00:00:00Z')
    def tearDown(self):self.tmp.cleanup()
    def test_no_refund_after_crash(self):
        self.ledger.reserve('approved-test','one',NOW)
        other=CreditLedger(self.path);other.reserve('approved-test','two',NOW)
        with self.assertRaises(FetchError): other.reserve('approved-test','three',NOW)
    def test_no_repeated_page(self):
        self.ledger.reserve('approved-test','one',NOW)
        with self.assertRaises(FetchError):self.ledger.reserve('approved-test','one',NOW)
    def test_no_renew_or_raise(self):
        for credits,expiry in [(900,'2026-11-16T00:00:00Z'),(600,'2026-11-17T00:00:00Z')]:
            with self.assertRaises(FetchError):self.ledger.create_grant('approved-test',credits,expiry)
    def test_expiry(self):
        with self.assertRaises(FetchError):self.ledger.reserve('approved-test','one',datetime(2026,11,16,tzinfo=timezone.utc))
    def test_unknown_grant(self):
        with self.assertRaises(FetchError):self.ledger.reserve('unknown','one',NOW)
    def test_resume_budget_not_reset(self):
        first=LedgerBudget(self.ledger,'approved-test','daily-20261115',clock=lambda:NOW);first.take()
        resumed=LedgerBudget(self.ledger,'approved-test','daily-20261115',clock=lambda:NOW)
        with self.assertRaises(FetchError):resumed.take()
    def test_daily_requires_verified_coverage(self):
        result=plan_windows({},NOW,mode='daily');self.assertEqual(len(result),8)
        self.assertTrue(all(r['status']=='coverage_bootstrap_required' for r in result))
    def test_daily_does_not_sneak_in_catchup(self):
        r=plan_windows({h:'2026-11-12T00:00:00Z' for h in HANDLES},NOW,mode='daily')
        self.assertTrue(all(x['status']=='catchup_required' for x in r))
    def test_oldest_first_bounded_catchup(self):
        r=plan_windows({},NOW,mode='catchup',bootstrap={h:'2026-11-12T00:00:00Z' for h in HANDLES})
        self.assertTrue(all(x['end']=='2026-11-13T00:00:00+00:00' and x['max_pages']==2 for x in r))
        self.assertEqual(sum(x['reserved_search_credits'] for x in r),4800)
    def test_future_checkpoint_not_healthy(self):
        r=plan_windows({'jukan05':'2026-11-16T00:00:00Z'},NOW,mode='daily')
        self.assertEqual(r[0]['status'],'future_checkpoint')

class BatchTests(unittest.TestCase):
    def test_eight_account_offline_replay_and_partial(self):
        from signalboard.db import init_db
        from signalboard.twitterapi_io import Window
        from signalboard.twitterapi_recovery import apply_captured_batch
        with tempfile.TemporaryDirectory() as tmp:
            db=tmp+'/copy.db';init_db(db)
            plans=plan_windows({},NOW,mode='catchup',bootstrap={h:'2026-11-14T00:00:00Z' for h in HANDLES})
            captured={h:Window([{'id':str(9007199254740993123+i),'text':'synthetic fixture',
                'createdAt':'Sat Nov 14 12:00:00 +0000 2026','author':{'userName':h}}],True,'search_exhausted',1,request_scope=(h.lower(),'2026-11-14T00:00:00+00:00','2026-11-15T00:00:00+00:00'))
                for i,h in enumerate(HANDLES)}
            captured['jukan05'].complete=False;captured['jukan05'].reason='page_cap_partial'
            receipt=apply_captured_batch(db,plans,captured,captured_at=NOW,checkpoints={})
            self.assertFalse(receipt['all_eight_planned_windows_verified'])
            self.assertEqual(sum(x['checkpoint_changed'] for x in receipt['accounts']),7)
            self.assertEqual(receipt['summary_status'],'not_requested')
            self.assertEqual(receipt['publication_status'],'not_requested')

    def test_all_eight_complete_is_separate_from_publication(self):
        from signalboard.db import init_db
        from signalboard.twitterapi_io import Window
        from signalboard.twitterapi_recovery import apply_captured_batch
        with tempfile.TemporaryDirectory() as tmp:
            db=tmp+'/copy.db';init_db(db)
            plans=plan_windows({},NOW,mode='catchup',bootstrap={h:'2026-11-14T00:00:00Z' for h in HANDLES})
            captured={h:Window([{'id':str(9007199254740993123+i),'text':'synthetic fixture',
                'createdAt':'Sat Nov 14 12:00:00 +0000 2026','author':{'userName':h}}],True,'search_exhausted',1,request_scope=(h.lower(),'2026-11-14T00:00:00+00:00','2026-11-15T00:00:00+00:00'))
                for i,h in enumerate(HANDLES)}
            receipt=apply_captured_batch(db,plans,captured,captured_at=NOW,checkpoints={})
            self.assertTrue(receipt['all_eight_planned_windows_verified'])
            self.assertEqual(receipt['publication_status'],'not_requested')

if __name__=='__main__':unittest.main()
