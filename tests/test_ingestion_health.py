import sqlite3
import unittest
from datetime import datetime, timezone, timedelta
from signalboard.ingestion_health import recent_timeline_coverage

NOW=datetime(2026,11,16,8,tzinfo=timezone.utc)
class Tests(unittest.TestCase):
    def setUp(self):
        self.c=sqlite3.connect(':memory:')
        self.c.execute('CREATE TABLE twitterapi_timeline_coverage(handle,coverage_start,coverage_end,provider,endpoint,completion_reason,verified_at,in_window_count)')
    def add(self, **kw):
        row=dict(handle='Jukan05',coverage_start='2026-11-15T16:00:00Z',coverage_end='2026-11-16T02:39:16Z',provider='twitterapi.io',endpoint='last_tweets',completion_reason='start_boundary_crossed',verified_at='2026-11-16T03:00:00Z',in_window_count=0)
        row.update(kw);self.c.execute('INSERT INTO twitterapi_timeline_coverage VALUES (?,?,?,?,?,?,?,?)',tuple(row.values()))
    def test_verified_zero_is_not_missing_capture_and_does_not_write(self):
        self.add();n=self.c.total_changes
        self.assertEqual(recent_timeline_coverage(self.c,NOW)['jukan05']['count'],0)
        self.assertEqual(n,self.c.total_changes)
    def test_no_table_is_not_fresh(self):
        self.assertEqual(recent_timeline_coverage(sqlite3.connect(':memory:'),NOW),{})
    def test_old_recently_replayed_window_is_not_fresh(self):
        self.add(coverage_start='2026-11-10T00:00:00Z',coverage_end='2026-11-11T00:00:00Z')
        self.assertEqual(recent_timeline_coverage(self.c,NOW),{})
    def test_unverified_wrong_provider_future_or_bad_dates_fail_closed(self):
        for kw in [dict(provider='other'),dict(endpoint='advanced_search'),dict(completion_reason='incomplete'),dict(coverage_end='2026-11-17T00:00:00Z'),dict(verified_at='2026-11-17T00:00:00Z'),dict(coverage_start='invalid'),dict(in_window_count=-1)]:
            with self.subTest(kw=kw):
                self.c.execute('DELETE FROM twitterapi_timeline_coverage');self.add(**kw)
                self.assertEqual(recent_timeline_coverage(self.c,NOW),{})
    def test_daily_window_expires_after_cadence_grace(self):
        self.add();self.assertFalse(recent_timeline_coverage(self.c,NOW+timedelta(days=2)))
if __name__=='__main__':unittest.main()
