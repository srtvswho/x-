from copy import deepcopy
from datetime import datetime,timezone
import unittest
from signalboard.twitterapi_timeline_history import initialize_history,advance_history,history_reserved_credits,HANDLES,BOUNDARIES,run_history,completed_attempts
from signalboard.twitterapi_paging import initialize_state,_check_state
NOW=datetime(2026,11,16,5,tzinfo=timezone.utc)
def tweet(handle,id='123',at='Sat Nov 14 20:00:00 +0000 2026'):
    return {'id':id,'text':'fixture','createdAt':at,'author':{'userName':handle}}
def page(handle,more=True,cursor='next',at='Sat Nov 14 20:00:00 +0000 2026'):
    return {'status':'success','data':{'tweets':[tweet(handle,at=at)]},'has_next_page':more,'next_cursor':cursor}
class Store:
    def __init__(self):
        self.state=initialize_state(dict(grant_id='bonus-recovery-20261115-7d-30000',credit_limit=30000,expires_at='2026-11-22T08:10:00Z',max_pages_per_window=100,mode='recovery',windows=[{'handle':'jukan05','start':'2026-11-12T00:00:00Z','end':'2026-11-13T00:00:00Z'}],bonus_only=True,no_payment_instrument_verified=True,recharge_credits=0));self.rev=0;self.saves=0;self.fail=None
    def load(self):return deepcopy(self.state),self.rev
    def save(self,state,rev):
        self.saves+=1
        if self.saves==self.fail:raise RuntimeError('storage')
        if rev!=self.rev:raise RuntimeError('CAS')
        _check_state(state,state['config'])
        self.state=deepcopy(state);self.rev+=1;return self.rev
class Client:
    def __init__(self,store,*responses):self.store=store;self.responses=list(responses);self.calls=[]
    def get(self,path,params):
        assert self.store.state['reserved_credits']>=315
        self.calls.append((path,params));r=self.responses.pop(0)
        if isinstance(r,Exception):raise r
        return r
class Tests(unittest.TestCase):
    def setup_state(self,seed=False):
        s=Store();initialize_history(s,{h:[page(h)] if seed else [] for h in HANDLES},BOUNDARIES);return s
    def step(self,c,s):return advance_history(c,s,'jukan05',now=NOW,clock=lambda:NOW)
    def test_new_first_capture_continuation_complete(self):
        s=self.setup_state();old=page('jukan05',False,'','Thu Nov 12 07:43:00 +0000 2026');old['data']['tweets'][0]['id']='124'
        c=Client(s,page('jukan05'),old)
        self.assertEqual(self.step(c,s)['status'],'ready');self.assertEqual(self.step(c,s)['status'],'complete')
        self.assertEqual([p['cursor'] for _,p in c.calls],['','next'])
        self.assertEqual(s.state['reserved_credits'],630);self.assertEqual(history_reserved_credits(s.state),630)
        self.step(c,s);self.assertEqual(len(c.calls),2)
    def test_existing_full_seed_no_first_refresh(self):
        s=self.setup_state(True);c=Client(s,page('jukan05',False,''))
        self.step(c,s);self.assertEqual(c.calls[0][1]['cursor'],'next');self.assertEqual(s.state['reserved_credits'],315)
    def test_unknown_transport_blocks_retry(self):
        s=self.setup_state();c=Client(s,RuntimeError('do not leak'))
        self.assertEqual(self.step(c,s)['status'],'uncertain');self.assertEqual(self.step(c,s)['status'],'uncertain');self.assertEqual(len(c.calls),1)
    def test_response_saved_before_validation(self):
        s=self.setup_state();c=Client(s,{'status':'secret-invalid'})
        self.assertEqual(self.step(c,s),{'status':'invalid_response','reason':'response.status'})
        self.assertEqual(s.state['timeline_history']['accounts']['jukan05']['events'][-1]['kind'],'response')
        self.assertEqual(self.step(c,s)['status'],'invalid_response');self.assertEqual(len(c.calls),1)
    def test_cursor_drift_fails(self):
        s=self.setup_state(True);c=Client(s,page('jukan05',True,'b','Sun Nov 15 20:00:00 +0000 2026'))
        self.assertEqual(self.step(c,s)['reason'],'timeline.order')
    def test_repeated_cursor_stops(self):
        s=self.setup_state(True);c=Client(s,page('jukan05'))
        self.assertEqual(self.step(c,s)['status'],'incomplete')
    def test_save_failures_no_retry(self):
        s=self.setup_state();s.fail=s.saves+1;c=Client(s,page('jukan05'))
        with self.assertRaises(RuntimeError):self.step(c,s)
        self.assertEqual(c.calls,[])
        s=self.setup_state();s.fail=s.saves+2;c=Client(s,page('jukan05'))
        with self.assertRaises(RuntimeError):self.step(c,s)
        self.assertEqual(self.step(c,s)['status'],'uncertain');self.assertEqual(len(c.calls),1)
    def test_expiry(self):
        s=self.setup_state();c=Client(s)
        result=advance_history(c,s,'jukan05',now='2026-11-22T08:10:00Z')
        self.assertEqual(result['status'],'expired');self.assertEqual(c.calls,[])
    def test_no_reset(self):
        s=self.setup_state()
        with self.assertRaises(ValueError):initialize_history(s,{h:[] for h in HANDLES},BOUNDARIES)
    def test_daily_and_history_shared_checker(self):
        s=self.setup_state();c=Client(s,page('jukan05'));self.step(c,s)
        s.state['timeline_daily']=[{'events':[{'kind':'reserved','handle':'jukan05','page':1,'credits':315}]}];s.state['reserved_credits']+=315
        _check_state(s.state,s.state['config'])
        s.state['reserved_credits']-=1
        with self.assertRaises(Exception):_check_state(s.state,s.state['config'])
    def test_36_page_total_cap(self):
        s=self.setup_state();responses=[page('jukan05',True,'cursor'+str(i)) for i in range(36)]
        for i,response in enumerate(responses):response['data']['tweets'][0]['id']=str(i+1000)
        c=Client(s,*responses)
        for _ in range(36):self.assertEqual(self.step(c,s)['status'],'ready')
        self.assertEqual(history_reserved_credits(s.state),11340)
        self.assertEqual(self.step(c,s)['status'],'history_budget_stop')
        self.assertEqual(len(c.calls),36)
    def test_daily_minimum_hold(self):
        s=self.setup_state()
        # Synthetic already-spent daily claims; valid per-batch per-account counts.
        s.state['timeline_daily']=[{'events':[{'kind':'reserved','handle':h,'page':p,'credits':315} for h in HANDLES for p in (1,2)]} for _ in range(3)]
        s.state['reserved_credits']=15120
        c=Client(s)
        self.assertEqual(self.step(c,s)['status'],'daily_reserve_stop')
        self.assertEqual(c.calls,[])
    def test_nonterminal_no_progress_stops(self):
        s=self.setup_state(True);c=Client(s,page('jukan05',True,'different'))
        self.assertEqual(self.step(c,s),{'status':'incomplete','reason':'pagination_no_progress'})
    def test_empty_first_not_healthy(self):
        s=self.setup_state();payload=page('jukan05',False,'');payload['data']['tweets']=[];c=Client(s,payload)
        self.assertEqual(self.step(c,s)['status'],'incomplete')
        self.assertEqual(self.step(c,s)['status'],'incomplete')
        self.assertEqual(len(c.calls),1)
        self.assertEqual(s.state['timeline_history']['accounts']['jukan05']['events'][-1]['payload'],payload)
    def test_other_account_failure_blocks_globally(self):
        s=self.setup_state();c=Client(s,RuntimeError('unknown'))
        self.step(c,s)
        result=advance_history(c,s,'austinsemis',now=NOW,clock=lambda:NOW)
        self.assertEqual(result['status'],'blocked_previous_attempt');self.assertEqual(len(c.calls),1)
    def test_realtime_before_and_after_claim(self):
        expired=datetime(2026,11,22,8,10,tzinfo=timezone.utc)
        s=self.setup_state();c=Client(s)
        self.assertEqual(advance_history(c,s,'jukan05',now=NOW,clock=lambda:expired)['status'],'expired')
        self.assertEqual(s.state['reserved_credits'],0)
        times=iter([NOW,NOW,expired])
        result=advance_history(c,s,'jukan05',now=NOW,clock=lambda:next(times))
        self.assertEqual(result['status'],'expired_after_reservation')
        self.assertEqual(s.state['reserved_credits'],315);self.assertEqual(c.calls,[])
    def test_pending_ready_and_cursor_tamper_refused(self):
        s=self.setup_state();c=Client(s,RuntimeError('unknown'));self.step(c,s)
        account=s.state['timeline_history']['accounts']['jukan05'];account['status']='ready'
        with self.assertRaises(ValueError):_check_state(s.state,s.state['config'])
        s=self.setup_state(True);c=Client(s,RuntimeError('unknown'));self.step(c,s)
        s.state['timeline_history']['accounts']['jukan05']['events'][0]['cursor']='tampered'
        with self.assertRaises(ValueError):_check_state(s.state,s.state['config'])
    def test_runner_and_all_eight_completion_accessor(self):
        s=self.setup_state();c=Client(s,*[page(h,False,'','Thu Nov 12 07:43:00 +0000 2026') for h in HANDLES])
        result=run_history(c,s,now=NOW,clock=lambda:NOW)
        self.assertEqual(result['status'],'complete');self.assertEqual(len(c.calls),8)
        self.assertEqual(len(completed_attempts(s.state)),8)
        result=run_history(c,s,now=NOW,clock=lambda:NOW)
        self.assertEqual(result['steps'],0);self.assertEqual(len(c.calls),8)
    def test_accessor_refuses_partial(self):
        s=self.setup_state()
        with self.assertRaises(ValueError):completed_attempts(s.state)
if __name__=='__main__':unittest.main()
