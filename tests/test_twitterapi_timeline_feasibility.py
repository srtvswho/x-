import json,tempfile,unittest
from pathlib import Path
from copy import deepcopy
from datetime import datetime,timezone
from unittest.mock import patch
from scripts import twitterapi_timeline_feasibility as m
from signalboard.twitterapi_io import FetchError

class Store:
 def __init__(self):
  self.rev=m.EXPECTED;self.calls=0
  self.state={'reserved_credits':900,'windows':{'old':'preserved'},'one_time_observation':{'old':'preserved'},'config':dict(credit_limit=30000,expires_at='2026-11-22T08:10:00+00:00',bonus_only=True,no_payment_instrument_verified=True,recharge_credits=0,max_balance_reads=0)}
 def load(self):return deepcopy(self.state),self.rev
 def save(self,s,r):
  assert r==self.rev
  self.calls+=1;self.state=deepcopy(s);self.rev=str(self.calls);return self.rev
class Tests(unittest.TestCase):
 def test_all_eight_exactly_once(self):
  s=Store();old=deepcopy(s.state);calls=[]
  class C:
   def get(self,path,params):
    self_outer.assertEqual(s.state['reserved_credits'],900+315*(len(calls)+1));calls.append(params)
    return {'status':'success','data':{'tweets':[{'id':'900719925474099123','text':'fixture','createdAt':'Sun Nov 15 15:00:00 +0000 2026','author':{'userName':params['userName']}}]},'has_next_page':True,'next_cursor':'next'}
  self_outer=self
  with tempfile.TemporaryDirectory() as d:
   self.assertTrue(m.run(s,C,datetime(2026,11,16,2,tzinfo=timezone.utc),Path(d)/'r'))
   self.assertEqual(len(calls),8);self.assertEqual(s.state['reserved_credits'],3420)
   self.assertEqual(s.state['windows'],old['windows']);self.assertEqual(s.state['one_time_observation'],old['one_time_observation'])
   with self.assertRaises(FetchError):m.run(s,C,datetime(2026,11,16,2,tzinfo=timezone.utc),Path(d)/'r2')
   self.assertEqual(len(calls),8)
 def test_field_failure_stops_first(self):
  s=Store();calls=[]
  class C:
   def get(self,*a):calls.append(1);return {'status':'success','data':{'tweets':'secret'}}
  with tempfile.TemporaryDirectory() as d:
   self.assertFalse(m.run(s,C,datetime(2026,11,16,2,tzinfo=timezone.utc),Path(d)/'r'))
   r=json.loads((Path(d)/'r').read_text());self.assertEqual(r['accounts'][0]['reason'],'response.data.tweets');self.assertEqual(len(calls),1);self.assertEqual(s.state['reserved_credits'],1215)
 def test_transport_failure_stops_first(self):
  s=Store();calls=[]
  class C:
   def get(self,*a):calls.append(1);raise TimeoutError('secret')
  with tempfile.TemporaryDirectory() as d:
   self.assertFalse(m.run(s,C,datetime(2026,11,16,2,tzinfo=timezone.utc),Path(d)/'r'));self.assertEqual(len(calls),1)
   self.assertNotIn('secret',(Path(d)/'r').read_text())
