import unittest
from copy import deepcopy
from datetime import timedelta
from signalboard.twitterapi_timeline_daily import START, EXPIRES, HANDLES, plan, run_daily, completed_attempts, daily_reserved_credits


def initial():
    return {'schema':'twitterapi-page-journal-v1', 'reserved_credits':3420,
            'config':{'grant_id':'bonus-recovery-20261115-7d-30000', 'credit_limit':30000,
                      'expires_at':EXPIRES.isoformat(), 'bonus_only':True,
                      'no_payment_instrument_verified':True, 'recharge_credits':0,
                      'verified_bonus_credits':30000},
            'windows':{'old':{'pending':True}}, 'timeline_feasibility':{'preserved':True}}


class Store:
    def __init__(self): self.state=initial(); self.rev=0; self.fail=False
    def load(self): return deepcopy(self.state),self.rev
    def save(self,state,expected_revision):
        if self.fail or self.rev!=expected_revision: raise RuntimeError('CAS')
        self.state=deepcopy(state);self.rev+=1;return self.rev


class Client:
    def __init__(self,store,mode='complete'): self.store=store;self.mode=mode;self.calls=[]
    def get(self,path,params):
        self.calls.append((path,params))
        assert self.store.state['timeline_daily'][-1]['events'][-1]['kind']=='reserved'
        assert params['includeReplies']=='true'
        if self.mode=='error': raise RuntimeError('secret error not saved')
        if self.mode=='invalid': return {'diagnostic':'full payload retained'}
        when=START-timedelta(seconds=1) if self.mode=='complete' else START+timedelta(hours=2)
        row={'id':str(100+len(self.calls)), 'text':'post',
             'author':{'userName':params['userName']},
             'createdAt':when.strftime('%a %b %d %H:%M:%S %z %Y')}
        return {'status':'success','data':{'tweets':[row]},'has_next_page':True,
                'next_cursor':str(len(self.calls))}


class DailyTests(unittest.TestCase):
    def run_capture(self,mode='complete'):
        s=Store();c=Client(s,mode);now=START+timedelta(days=1)
        r=run_daily(c,s,now=now,clock=lambda:now)
        return s,c,r
    def test_complete_preserves_old_state_and_counts(self):
        s,c,r=self.run_capture()
        self.assertEqual(r['status'],'complete');self.assertEqual(len(c.calls),8)
        self.assertEqual(s.state['reserved_credits'],5940)
        self.assertEqual(s.state['windows'],initial()['windows'])
        self.assertEqual(s.state['timeline_feasibility'],initial()['timeline_feasibility'])
        self.assertEqual(len(s.state['timeline_daily'][0]['events']),24)
        self.assertEqual(daily_reserved_credits(s.state),2520)
        self.assertEqual(len(completed_attempts(s.state['timeline_daily'][0])),8)
        self.assertEqual(plan(s.state,START+timedelta(days=1))['status'],'not_due')
    def test_incomplete_stops_at_two_no_retry(self):
        s,c,r=self.run_capture('more')
        self.assertEqual(r['status'],'page_cap_incomplete');self.assertEqual(len(c.calls),2)
        self.assertEqual(run_daily(c,s,now=START+timedelta(days=2))['status'],'blocked_previous_attempt')
        self.assertEqual(len(c.calls),2)
    def test_error_fixed_reason_reservation_retained(self):
        s,c,r=self.run_capture('error')
        self.assertEqual(r['status'],'transport_uncertain');self.assertEqual(s.state['reserved_credits'],3735)
        self.assertNotIn('secret error',str(s.state))
    def test_invalid_payload_durable(self):
        s,c,r=self.run_capture('invalid')
        self.assertEqual(r['status'],'response.status')
        self.assertEqual(s.state['timeline_daily'][0]['events'][-1]['payload'],{'diagnostic':'full payload retained'})
    def test_cas_failure_prevents_request(self):
        s=Store();s.fail=True;c=Client(s)
        with self.assertRaises(RuntimeError):run_daily(c,s,now=START+timedelta(days=1))
        self.assertEqual(c.calls,[])
    def test_expired_no_request(self):
        s=Store();c=Client(s)
        self.assertEqual(run_daily(c,s,now=EXPIRES)['status'],'expired');self.assertEqual(c.calls,[])
    def test_midrun_expiry(self):
        s=Store();c=Client(s)
        r=run_daily(c,s,now=START+timedelta(days=1),clock=lambda:EXPIRES)
        self.assertEqual(r['status'],'expired');self.assertEqual(c.calls,[])
    def test_no_early_window(self):
        self.assertEqual(plan(initial(),START+timedelta(hours=23))['status'],'not_due')
    def test_budget_and_config(self):
        s=initial();s['reserved_credits']=29999
        self.assertEqual(plan(s,START+timedelta(days=1))['status'],'budget_stop')
        s['config']['credit_limit']=40000
        with self.assertRaises(ValueError):plan(s,START+timedelta(days=1))
    def test_pending_daily_blocks_old_pending_not_global(self):
        s=initial();s['timeline_daily']=[{'start':START.isoformat(),'end':(START+timedelta(days=1)).isoformat(),'status':'running'}]
        self.assertEqual(plan(s,START+timedelta(days=1))['status'],'blocked_previous_attempt')

if __name__=='__main__': unittest.main()
