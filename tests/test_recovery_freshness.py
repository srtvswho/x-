import sqlite3
import unittest
from signalboard.recovery_freshness import recovery_freshness, recovery_banner

class Tests(unittest.TestCase):
    def test_missing_table_is_not_healthy(self):
        con=sqlite3.connect(':memory:');meta=recovery_freshness(con)
        self.assertEqual(meta['status'],'not_recorded')
        self.assertEqual(recovery_banner(meta),'')
        self.assertEqual(meta['historical_gap']['status'],'not_verified_closed')
    def test_new_window_does_not_close_history_or_update_ai(self):
        con=sqlite3.connect(':memory:')
        con.execute('CREATE TABLE twitterapi_timeline_coverage(handle,coverage_start,coverage_end,completion_reason,verified_at,in_window_count)')
        con.execute('INSERT INTO twitterapi_timeline_coverage VALUES(?,?,?,?,?,?)',('jukan05','2026-11-15T16:00:00Z','2026-11-16T02:34:00Z','start_boundary_crossed','2026-11-16T03:00:00Z',3))
        before=con.total_changes;meta=recovery_freshness(con);banner=recovery_banner(meta)
        self.assertEqual(con.total_changes,before)
        self.assertEqual(meta['historical_gap']['status'],'not_verified_closed')
        self.assertEqual(meta['ai_status'],'independent_not_verified_by_fetch')
        self.assertIn('2026-11-16 00:00:00',banner)
        self.assertIn('2026-11-16 10:34:00',banner)
        self.assertIn('旧缺口尚未验证补齐',banner)
        self.assertIn('抓取成功不代表解读已更新',banner)
    def test_escape_handle(self):
        banner=recovery_banner({'timeline_windows':[{'handle':'<script>','coverage_start':'bad','coverage_end':'bad','in_window_count':0}]})
        self.assertNotIn('<script>',banner);self.assertIn('&lt;script&gt;',banner)

if __name__=='__main__':unittest.main()
