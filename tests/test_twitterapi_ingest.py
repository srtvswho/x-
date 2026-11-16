"""Synthetic offline fixtures only; live smoke did not archive full tweet bodies."""
import json
from pathlib import Path
import sqlite3
import tempfile
import unittest
from datetime import datetime, timedelta, timezone

from signalboard.db import init_db
from signalboard.twitterapi_io import Window
from signalboard.twitterapi_ingest import IngestError, get_coverage, ingest_window

START = datetime(2026, 11, 14, tzinfo=timezone.utc)
END = START + timedelta(days=1)

def tweet(id='9007199254740993123', text=' original text '):
    return {'id': id, 'text': text, 'createdAt': 'Sat Nov 14 12:00:00 +0000 2026',
            'author': {'userName': 'jukan05'}}

def window(rows=None, *, start=START, end=END, handle='jukan05'):
    return Window([tweet()] if rows is None else rows, True, 'search_exhausted', 1,
                  request_scope=(handle.lower(), start.astimezone(timezone.utc).isoformat(),
                                 end.astimezone(timezone.utc).isoformat()))

class Tests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.db = Path(self.temp.name) / 'working.db'
        init_db(self.db)
    def tearDown(self): self.temp.cleanup()
    def ingest(self, value=None, **kw):
        return ingest_window(self.db, 'jukan05', kw.pop('start', START), kw.pop('end', END),
                             value or window(), captured_at=END + timedelta(days=3), **kw)
    def rows(self):
        with sqlite3.connect(self.db) as c:
            return c.execute('SELECT post_id,raw_text,raw_json FROM raw_posts').fetchall()
    def test_atomic_success_and_string(self):
        result=self.ingest(); self.assertTrue(result['checkpoint_changed'])
        self.assertEqual(self.rows()[0][0], '9007199254740993123')
        self.assertEqual(self.rows()[0][1], ' original text ')
        self.assertEqual(get_coverage(self.db,'jukan05')['coverage_end'],'2026-11-15T00:00:00Z')
    def test_missing_scope_rejected(self):
        with self.assertRaisesRegex(IngestError, 'scope'):
            self.ingest(Window([tweet()], True, 'search_exhausted', 1))
        self.assertEqual(self.rows(), [])
        self.assertIsNone(get_coverage(self.db, 'jukan05'))
    def test_narrow_scope_cannot_claim_wide_coverage(self):
        with self.assertRaisesRegex(IngestError, 'scope'):
            self.ingest(window(), start=START-timedelta(days=1))
        self.assertEqual(self.rows(), [])
        self.assertIsNone(get_coverage(self.db, 'jukan05'))
    def test_wrong_handle_scope_rejected(self):
        with self.assertRaisesRegex(IngestError, 'scope'):
            self.ingest(window(handle='other'))
        self.assertEqual(self.rows(), [])
        self.assertIsNone(get_coverage(self.db, 'jukan05'))
    def test_partial_no_writes(self):
        r=self.ingest(Window([tweet()],False,'page_cap_partial',1))
        self.assertFalse(r['checkpoint_changed']);self.assertEqual(self.rows(),[])
        self.assertIsNone(get_coverage(self.db,'jukan05'))
    def test_empty_unverified(self):
        r=self.ingest(Window([],False,'empty_unverified',1));self.assertFalse(r['checkpoint_changed'])
        with self.assertRaises(IngestError): self.ingest(window([]))
    def test_invalid_second_rolls_back_all(self):
        row=tweet('123');row['createdAt']='broken'
        with self.assertRaises(IngestError):self.ingest(window([tweet(),row]))
        self.assertEqual(self.rows(),[]);self.assertIsNone(get_coverage(self.db,'jukan05'))
    def test_existing_never_overwritten(self):
        self.ingest();before=self.rows()
        r=self.ingest(window([tweet(text='changed')]),expected_coverage_end='2026-11-15T00:00:00Z')
        self.assertEqual(self.rows(),before);self.assertEqual(r['changed_originals_preserved'],1)
    def test_existing_interpretation_and_deletion_preserved(self):
        self.ingest()
        with sqlite3.connect(self.db) as c:
            c.execute("UPDATE raw_posts SET is_deleted=1,archive_url='saved-archive'")
            c.execute("""INSERT INTO predictions
                (prediction_id,post_id,source_id,published_at,captured_at,ticker,market,
                 direction,claim_type,horizon,conviction,thesis_summary,thesis_category)
                VALUES ('p','9007199254740993123','tw_jukan05','saved','saved','TEST','US',
                        'neutral','thematic','1m',1,'saved interpretation','saved')""")
            before=c.execute('SELECT * FROM predictions').fetchall()
        self.ingest(window([tweet(text='new provider text')]),expected_coverage_end='2026-11-15T00:00:00Z')
        with sqlite3.connect(self.db) as c:
            self.assertEqual(c.execute('SELECT * FROM predictions').fetchall(),before)
            self.assertEqual(c.execute('SELECT is_deleted,archive_url FROM raw_posts').fetchone(),(1,'saved-archive'))
    def test_duplicate_batch(self):
        self.ingest(window([tweet(),tweet()]));self.assertEqual(len(self.rows()),1)
    def test_conflicting_duplicate_rejected(self):
        with self.assertRaises(IngestError):self.ingest(window([tweet(),tweet(text='changed')]))
        self.assertEqual(self.rows(),[])
    def test_numeric_id_rejected(self):
        with self.assertRaises(IngestError):self.ingest(window([tweet(9007199254740993123)]))
    def test_gap_and_stale_checkpoint(self):
        self.ingest()
        with self.assertRaises(IngestError):self.ingest()
        row=tweet('123');row['createdAt']='Mon Nov 16 12:00:00 +0000 2026'
        with self.assertRaises(IngestError):self.ingest(window([row],start=END+timedelta(days=1),end=END+timedelta(days=2)),start=END+timedelta(days=1),end=END+timedelta(days=2),expected_coverage_end='2026-11-15T00:00:00Z')
        self.assertEqual(len(self.rows()),1)
    def test_contiguous_and_separate_stream(self):
        self.ingest()
        row=tweet('123');row['createdAt']='Sun Nov 15 12:00:00 +0000 2026'
        self.ingest(window([row],start=END,end=END+timedelta(days=1)),start=END,end=END+timedelta(days=1),expected_coverage_end='2026-11-15T00:00:00Z')
        self.ingest(stream='catchup')
        self.assertEqual(get_coverage(self.db,'jukan05')['coverage_end'],'2026-11-16T00:00:00Z')
        self.assertEqual(get_coverage(self.db,'jukan05','catchup')['coverage_end'],'2026-11-15T00:00:00Z')
    def test_db_error_rolls_back_posts_and_checkpoint(self):
        with sqlite3.connect(self.db) as c:
            c.execute("CREATE TRIGGER fail_second BEFORE INSERT ON raw_posts WHEN NEW.post_id='123' BEGIN SELECT RAISE(ABORT, 'test'); END")
        with self.assertRaises(sqlite3.IntegrityError):self.ingest(window([tweet(),tweet('123')]))
        self.assertEqual(self.rows(),[]);self.assertIsNone(get_coverage(self.db,'jukan05'))
    def test_wrong_existing_source_rolls_back(self):
        self.ingest()
        with sqlite3.connect(self.db) as c:c.execute("UPDATE raw_posts SET source_id='tw_other'")
        with self.assertRaises(IngestError):self.ingest(window([tweet('123'),tweet()]),expected_coverage_end='2026-11-15T00:00:00Z')
        self.assertEqual(len(self.rows()),1)
    def test_read_missing_db_does_not_create(self):
        missing=Path(self.temp.name)/'missing.db'
        with self.assertRaises(sqlite3.OperationalError):get_coverage(missing,'jukan05')
        self.assertFalse(missing.exists())

if __name__=='__main__':unittest.main()
