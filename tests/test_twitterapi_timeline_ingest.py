"""Synthetic offline cache only; never opens production DB or fetches data."""
import copy
from datetime import datetime,timedelta,timezone
from email.utils import format_datetime
from pathlib import Path
import sqlite3
import tempfile
import unittest
from signalboard.db import init_db
from signalboard.twitterapi_ingest import IngestError
from signalboard.twitterapi_recovery import HANDLES
from signalboard.twitterapi_timeline_ingest import ingest_timeline_cache

START=datetime(2026,11,15,16,tzinfo=timezone.utc);END=START+timedelta(hours=8)
class Tests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.db=Path(self.tmp.name)/'working.db';init_db(self.db)
        self.state={'timeline_feasibility':{'operation':'synthetic','historical_gap_preserved':True,
            'start':START.isoformat(),'end':END.isoformat(),'status':'running','attempts':[
                {'handle':h,'endpoint':'last_tweets','cursor':'','status':'observed','complete':True,
                 'reason':'start_boundary_crossed','tweets':([] if i>0 else [{'id':'9007199254740993123','text':' exact text ',
                 'author':{'userName':h},'createdAt':format_datetime(START+timedelta(hours=1))}])}
                for i,h in enumerate(HANDLES)]}}
    def tearDown(self):self.tmp.cleanup()
    def run_import(self,**kw):
        return ingest_timeline_cache(self.db,self.state,expected_operation='synthetic',expected_start=kw.get('start',START),expected_end=END,captured_at=END)
    def counts(self):
        with sqlite3.connect(self.db) as c:
            rows=c.execute('SELECT COUNT(*) FROM raw_posts').fetchone()[0]
            exists=c.execute("SELECT 1 FROM sqlite_master WHERE name='twitterapi_timeline_coverage'").fetchone()
            return rows,c.execute('SELECT COUNT(*) FROM twitterapi_timeline_coverage').fetchone()[0] if exists else 0
    def test_eight_atomic_including_evidenced_empty(self):
        r=self.run_import();self.assertTrue(r['all_eight_complete']);self.assertEqual(self.counts(),(1,8))
        self.assertEqual(r['accounts'][1]['in_window_count'],0)
    def test_idempotent_and_changed_original_preserved(self):
        self.run_import();self.state['timeline_feasibility']['attempts'][0]['tweets'][0]['text']='changed'
        r=self.run_import();self.assertEqual(self.counts(),(1,8));self.assertEqual(r['accounts'][0]['changed_originals_preserved'],1)
        with sqlite3.connect(self.db) as c:self.assertEqual(c.execute('SELECT raw_text FROM raw_posts').fetchone()[0],' exact text ')
    def test_scope_replay_rejected(self):
        with self.assertRaises(IngestError):self.run_import(start=START-timedelta(days=1))
        self.assertEqual(self.counts(),(0,0))
    def test_missing_or_duplicate_account_rejected(self):
        for duplicate in (False,True):
            original=copy.deepcopy(self.state)
            a=self.state['timeline_feasibility']['attempts'];a.pop()
            if duplicate:a.append(copy.deepcopy(a[0]))
            with self.assertRaises(IngestError):self.run_import()
            self.assertEqual(self.counts(),(0,0));self.state=original
    def test_partial_unverified_or_wrong_endpoint_rejected(self):
        for key,value in [('complete',False),('reason','empty_unverified'),('status','pending'),('endpoint','advanced_search')]:
            attempt=self.state['timeline_feasibility']['attempts'][-1];old=attempt[key];attempt[key]=value
            with self.assertRaises(IngestError):self.run_import()
            self.assertEqual(self.counts(),(0,0));attempt[key]=old
    def test_invalid_late_tweet_rejects_all(self):
        a=self.state['timeline_feasibility']['attempts'];a[-1]['tweets']=copy.deepcopy(a[0]['tweets'])
        with self.assertRaises(IngestError):self.run_import()
        self.assertEqual(self.counts(),(0,0))
    def test_sql_failure_rolls_back_all(self):
        self.run_import()
        with sqlite3.connect(self.db) as c:
            c.execute('DELETE FROM twitterapi_timeline_coverage');c.execute('DELETE FROM raw_posts')
            c.execute("CREATE TRIGGER fail_last BEFORE INSERT ON twitterapi_timeline_coverage WHEN NEW.handle='gsmferrari' BEGIN SELECT RAISE(ABORT,'test'); END")
        with self.assertRaises(sqlite3.IntegrityError):self.run_import()
        self.assertEqual(self.counts(),(0,0))
    def test_replay_trial_and_daily_adapter(self):
        from unittest.mock import patch
        from signalboard.twitterapi_timeline_ingest import replay_completed_timeline
        from signalboard.twitterapi_timeline_daily import START as boundary
        record=self.state['timeline_feasibility']
        record['operation']='timeline-feasibility-20261116';record['end']=boundary.isoformat()
        daily_end=boundary+timedelta(days=1)
        self.state['timeline_daily']=[{'start':boundary.isoformat(),'end':daily_end.isoformat(),'status':'complete'}]
        attempts=[dict(handle=h,complete=True,reason='start_boundary_crossed',tweets=[]) for h in HANDLES]
        with patch('signalboard.twitterapi_timeline_daily.completed_attempts',return_value=attempts) as validated:
            r=replay_completed_timeline(self.db,self.state,captured_at=daily_end)
            validated.assert_called_once();self.assertEqual(len(r['intervals']),2)
            self.assertEqual(self.counts(),(1,16))
            replay_completed_timeline(self.db,self.state,captured_at=daily_end)
            self.assertEqual(self.counts(),(1,16))
    def test_replay_incomplete_daily_refused(self):
        from signalboard.twitterapi_timeline_ingest import replay_completed_timeline
        from signalboard.twitterapi_timeline_daily import START as boundary
        record=self.state['timeline_feasibility'];record['operation']='timeline-feasibility-20261116';record['end']=boundary.isoformat()
        self.state['timeline_daily']=[{'start':boundary.isoformat(),'end':(boundary+timedelta(days=1)).isoformat(),'status':'running'}]
        with self.assertRaises(ValueError):replay_completed_timeline(self.db,self.state,captured_at=boundary+timedelta(days=1))
        self.assertEqual(self.counts(),(1,8))
    def test_old_search_coverage_untouched(self):
        with sqlite3.connect(self.db) as c:
            c.execute('CREATE TABLE twitterapi_coverage (marker TEXT)');c.execute("INSERT INTO twitterapi_coverage VALUES ('keep')")
        self.run_import()
        with sqlite3.connect(self.db) as c:self.assertEqual(c.execute('SELECT * FROM twitterapi_coverage').fetchall(),[('keep',)])

if __name__=='__main__':unittest.main()
