import copy,sqlite3,tempfile,unittest
from datetime import datetime,timezone
from pathlib import Path
from signalboard.db import init_db
from signalboard.twitterapi_paging import initialize_state
from signalboard.twitterapi_timeline_history import initialize_history,BOUNDARIES
from signalboard.twitterapi_history_ingest import ingest_completed_history
NOW=datetime(2026,11,16,12,tzinfo=timezone.utc)
class Store:
 def __init__(self):
  self.state=initialize_state(dict(grant_id='bonus-recovery-20261115-7d-30000',credit_limit=30000,expires_at='2026-11-22T08:10:00Z',max_pages_per_window=100,mode='recovery',windows=[dict(handle='jukan05',start='2026-11-12T00:00:00Z',end='2026-11-13T00:00:00Z')],bonus_only=True,no_payment_instrument_verified=True,recharge_credits=0));self.rev=0
 def load(self):return copy.deepcopy(self.state),self.rev
 def save(self,state,rev):self.state=copy.deepcopy(state);self.rev+=1;return self.rev
class Tests(unittest.TestCase):
 def setUp(self):
  self.tmp=tempfile.TemporaryDirectory();self.db=Path(self.tmp.name)/'copy.db';init_db(self.db)
  s=Store();seeds={}
  for i,h in enumerate(BOUNDARIES):
   seeds[h]=[{'status':'success','has_next_page':False,'next_cursor':'','data':{'tweets':[
      {'id':str(9007199254740993123+i),'text':' preserved ','createdAt':'Fri Nov 13 12:00:00 +0000 2026','author':{'userName':h}}]}}]
  initialize_history(s,seeds,BOUNDARIES);self.state=s.state
 def tearDown(self):self.tmp.cleanup()
 def run_import(self):return ingest_completed_history(self.db,self.state,captured_at=NOW)
 def counts(self):
  with sqlite3.connect(self.db) as c:
   n=c.execute('SELECT COUNT(*) FROM raw_posts').fetchone()[0]
   present=c.execute("SELECT 1 FROM sqlite_master WHERE name='twitterapi_timeline_coverage'").fetchone()
   return n,c.execute('SELECT COUNT(*) FROM twitterapi_timeline_coverage').fetchone()[0] if present else 0
 def test_real_validation_per_account_scope_and_idempotency(self):
  r=self.run_import();self.assertEqual(self.counts(),(8,8));self.assertTrue(r['earlier_history_remains_unverified'])
  self.assertGreater(len({x['coverage_start'] for x in r['accounts']}),1)
  self.assertEqual(sum(x['new_persisted'] for x in self.run_import()['accounts']),0)
 def test_partial_rejected_before_any_transaction(self):
  self.state['timeline_history']['accounts']['jukan05']['status']='incomplete'
  with self.assertRaises(ValueError):self.run_import()
  self.assertEqual(self.counts(),(0,0))
 def test_changed_boundary_rejected(self):
  self.state['timeline_history']['accounts']['jukan05']['start']='2026-11-12T00:00:00Z'
  with self.assertRaises(ValueError):self.run_import()
  self.assertEqual(self.counts(),(0,0))
 def test_raw_cache_mutation_rejected(self):
  self.state['timeline_history']['accounts']['jukan05']['seed_pages'][0]['data']['tweets'][0]['text']='tampered'
  with self.assertRaises(ValueError):self.run_import()
  self.assertEqual(self.counts(),(0,0))
 def test_sql_failure_rolls_back_all(self):
  with sqlite3.connect(self.db) as c:
   c.execute("CREATE TRIGGER fail_last BEFORE INSERT ON raw_posts WHEN NEW.source_id='tw_gsmferrari' BEGIN SELECT RAISE(ABORT,'synthetic'); END")
  with self.assertRaises(sqlite3.IntegrityError):self.run_import()
  self.assertEqual(self.counts(),(0,0))
 def test_existing_original_flags_and_search_checkpoint_preserved(self):
  self.run_import()
  with sqlite3.connect(self.db) as c:
   c.execute("UPDATE raw_posts SET raw_text='prior original',is_deleted=1,archive_url='saved'")
   c.execute('CREATE TABLE twitterapi_coverage(marker TEXT)');c.execute("INSERT INTO twitterapi_coverage VALUES ('keep')")
  r=self.run_import();self.assertEqual(sum(x['changed_originals_preserved'] for x in r['accounts']),8)
  with sqlite3.connect(self.db) as c:
   self.assertEqual(c.execute('SELECT DISTINCT raw_text,is_deleted,archive_url FROM raw_posts').fetchall(),[('prior original',1,'saved')])
   self.assertEqual(c.execute('SELECT * FROM twitterapi_coverage').fetchall(),[('keep',)])
if __name__=='__main__':unittest.main()
