import sqlite3,unittest
from signalboard.recovery_freshness import recovery_freshness,recovery_banner
from signalboard.twitterapi_timeline_history import BOUNDARIES,END,OPERATION
class Tests(unittest.TestCase):
 def setUp(self):
  self.c=sqlite3.connect(':memory:');self.c.execute('CREATE TABLE twitterapi_timeline_coverage(handle,coverage_start,coverage_end,operation,provider,endpoint,completion_reason,verified_at,in_window_count)')
 def add(self,n=8):
  for h,start in list(BOUNDARIES.items())[:n]:self.c.execute('INSERT INTO twitterapi_timeline_coverage VALUES(?,?,?,?,?,?,?,?,?)',(h,start,END,OPERATION,'twitterapi.io','last_tweets','start_boundary_crossed',END,0))
 def test_exact_all8_only(self):
  self.add();m=recovery_freshness(self.c);self.assertEqual(m['historical_gap']['status'],'known_last_fetch_gap_closed_earlier_unverified')
  self.assertIn('更早历史仍未核验完整',recovery_banner(m));self.assertEqual(m['ai_status'],'independent_not_verified_by_fetch')
 def test_partial_not_closed(self):
  self.add(7);self.assertEqual(recovery_freshness(self.c)['historical_gap']['status'],'not_verified_closed')
 def test_wider_interval_not_claimed(self):
  self.add();self.c.execute("UPDATE twitterapi_timeline_coverage SET coverage_start='2026-11-12T00:00:00Z' WHERE handle='jukan05'")
  self.assertEqual(recovery_freshness(self.c)['historical_gap']['status'],'not_verified_closed')
 def test_wrong_provider_not_closed(self):
  self.add();self.c.execute("UPDATE twitterapi_timeline_coverage SET provider='other'")
  self.assertEqual(recovery_freshness(self.c)['historical_gap']['status'],'not_verified_closed')
if __name__=='__main__':unittest.main()
