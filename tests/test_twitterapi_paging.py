"""Synthetic payloads; no network, no provider credits."""
from copy import deepcopy
from datetime import datetime,timezone
import unittest
from signalboard.twitterapi_io import FetchError
from signalboard.twitterapi_paging import initialize_state,advance_page,cached_window
START=datetime(2026,11,14,tzinfo=timezone.utc)
END=datetime(2026,11,15,tzinfo=timezone.utc)
NOW=datetime(2026,11,15,12,tzinfo=timezone.utc)
def policy(**kw):
    result=dict(grant_id='explicit-test',credit_limit=1800,expires_at='2026-11-16T00:00:00+00:00',
                max_pages_per_window=6,mode='catchup',windows=[{'handle':'jukan05','start':START.isoformat(),'end':END.isoformat()}])
    result.update(kw);return result
def tweet(id='9007199254740993123',text='synthetic'):
    return dict(id=id,text=text,createdAt='Sat Nov 14 12:00:00 +0000 2026',author={'userName':'jukan05'})
def page(rows=None,more=False,cursor=''):
    return dict(tweets=[tweet()] if rows is None else rows,has_next_page=more,next_cursor=cursor)
class Store:
    def __init__(self,p=None):self.state=initialize_state(p or policy());self.rev=0;self.saves=0;self.fail_save=None
    def load(self):return deepcopy(self.state),self.rev
    def save(self,state,expected_revision):
        self.saves+=1
        if self.saves==self.fail_save:raise RuntimeError('storage failure')
        if expected_revision!=self.rev:raise RuntimeError('CAS mismatch')
        self.state=deepcopy(state);self.rev+=1;return self.rev
class Client:
    def __init__(self,*pages,store=None):self.pages=list(pages);self.calls=[];self.store=store
    def get(self,path,params):
        if self.store:
            assert self.store.state['reserved_credits']>=300
            assert any(w['pending'] for w in self.store.state['windows'].values())
        self.calls.append((path,params))
        data=self.pages.pop(0)
        if isinstance(data,Exception):raise data
        return data
class Tests(unittest.TestCase):
    def step(self,c,s,**kw):return advance_page(c,s,'jukan05',START,END,now=kw.pop('now',NOW),expected_policy=kw.pop('expected_policy',policy()),**kw)
    def test_claim_before_call_and_cache(self):
        s=Store();c=Client(page(),store=s);w=self.step(c,s)
        self.assertTrue(w.complete);self.assertEqual(s.state['reserved_credits'],300)
        self.assertEqual(w.request_scope,('jukan05',START.isoformat(),END.isoformat()))
        self.assertTrue(cached_window(s,'jukan05',START,END,expected_policy=policy()).complete)
    def test_resume_next_cursor_without_repeat(self):
        s=Store();c=Client(page(more=True,cursor='next'),page([tweet('123')]))
        self.assertFalse(self.step(c,s).complete);self.assertTrue(self.step(c,s).complete)
        self.assertEqual([x[1]['cursor'] for x in c.calls],['','next'])
        self.assertTrue(self.step(c,s).complete);self.assertEqual(len(c.calls),2)
    def test_empty_final_after_nonempty_complete(self):
        s=Store();c=Client(page(more=True,cursor='next'),page([]))
        self.step(c,s);self.assertTrue(self.step(c,s).complete)
    def test_empty_first_unverified(self):
        s=Store();c=Client(page([]));w=self.step(c,s)
        self.assertFalse(w.complete);self.assertEqual(w.reason,'empty_unverified')
        self.step(c,s);self.assertEqual(len(c.calls),1)
    def test_uncertain_api_never_retry(self):
        s=Store();c=Client(RuntimeError('secret-not-log'))
        with self.assertRaises(FetchError):self.step(c,s)
        with self.assertRaises(FetchError):self.step(c,s)
        self.assertEqual(len(c.calls),1);self.assertEqual(s.state['reserved_credits'],300)
    def test_claim_save_failure_sends_no_request(self):
        s=Store();s.fail_save=1;c=Client(page())
        with self.assertRaises(RuntimeError):self.step(c,s)
        self.assertEqual(c.calls,[])
    def test_response_save_failure_blocks_resume(self):
        s=Store();s.fail_save=2;c=Client(page())
        with self.assertRaises(FetchError):self.step(c,s)
        with self.assertRaises(FetchError):self.step(c,s)
        self.assertEqual(len(c.calls),1)
    def test_invalid_response_consumes_and_blocks(self):
        s=Store();c=Client({'tweets':[]})
        with self.assertRaises(FetchError):self.step(c,s)
        self.assertEqual(s.state['reserved_credits'],300)
        with self.assertRaises(FetchError):self.step(c,s)
    def test_cursor_cycle_blocks(self):
        s=Store();c=Client(page(more=True,cursor='a'),page(more=True,cursor='a'))
        self.step(c,s)
        with self.assertRaises(FetchError):self.step(c,s)
    def test_conflicting_duplicate_blocks(self):
        s=Store();c=Client(page(more=True,cursor='a'),page([tweet(text='changed')]))
        self.step(c,s)
        with self.assertRaises(FetchError):self.step(c,s)
    def test_duplicate_same_preserved_once(self):
        s=Store();c=Client(page(more=True,cursor='a'),page())
        self.step(c,s);self.assertEqual(len(self.step(c,s).tweets),1)
    def test_expiry_blocks_before_reserve(self):
        s=Store();c=Client(page())
        with self.assertRaises(FetchError):self.step(c,s,now=datetime(2026,11,16,tzinfo=timezone.utc))
        self.assertEqual(c.calls,[]);self.assertEqual(s.state['reserved_credits'],0)
    def test_budget_not_reset_by_new_worker(self):
        p=policy(credit_limit=300);s=Store(p);c=Client(page(more=True,cursor='a'))
        self.step(c,s,expected_policy=p)
        with self.assertRaises(FetchError):self.step(c,s,expected_policy=p)
        self.assertEqual(len(c.calls),1)
    def test_hard_window_cap(self):
        p=policy(max_pages_per_window=1);s=Store(p);c=Client(page(more=True,cursor='a'))
        self.assertEqual(self.step(c,s,expected_policy=p).reason,'page_cap_partial')
        self.step(c,s,expected_policy=p);self.assertEqual(len(c.calls),1)
    def test_changed_policy_rejected(self):
        s=Store();c=Client(page())
        with self.assertRaises(FetchError):self.step(c,s,expected_policy=policy(credit_limit=9999))
        self.assertEqual(c.calls,[])
    def test_scope_outside_grant_rejected(self):
        s=Store();c=Client(page())
        with self.assertRaises(FetchError):advance_page(c,s,'other',START,END,now=NOW,expected_policy=policy())
        self.assertEqual(c.calls,[])
    def test_corrupt_reservation_count_blocks(self):
        s=Store();s.state['reserved_credits']=300;c=Client(page())
        with self.assertRaises(FetchError):self.step(c,s)
        self.assertEqual(c.calls,[])
    def test_cached_completion_tamper_blocks(self):
        s=Store();c=Client(page(more=True,cursor='a'));self.step(c,s)
        entry=next(iter(s.state['windows'].values()));entry['status']='search_exhausted'
        with self.assertRaises(FetchError):cached_window(s,'jukan05',START,END,expected_policy=policy())
    def test_cached_row_tamper_blocks(self):
        s=Store();c=Client(page());self.step(c,s)
        next(iter(s.state['windows'].values()))['pages'][0]['tweets'][0]['id']=123
        with self.assertRaises(FetchError):cached_window(s,'jukan05',START,END,expected_policy=policy())
    def test_optional_bonus_proof_bound(self):
        p=policy(bonus_only=True,no_payment_instrument_verified=True,
                 bonus_expires_at='2026-11-16T00:00:00Z',verified_bonus_credits=1800)
        self.assertEqual(initialize_state(p)['config']['bonus_expires_at'],'2026-11-16T00:00:00+00:00')
        with self.assertRaises(ValueError):initialize_state(dict(p,verified_bonus_credits=1700))
        with self.assertRaises(ValueError):initialize_state(dict(p,no_payment_instrument_verified=False))
        with self.assertRaises(ValueError):initialize_state(dict(p,bonus_expires_at='2026-11-15T00:00:00Z'))
    def test_cas_claim_conflict_no_request(self):
        class Conflict(Store):
            def save(self,state,revision):raise RuntimeError('concurrent edit')
        s=Conflict();c=Client(page())
        with self.assertRaises(RuntimeError):self.step(c,s)
        self.assertEqual(c.calls,[])
if __name__=='__main__':unittest.main()


class BalanceTests(unittest.TestCase):
    def test_cap_and_durable_unknown(self):
        from signalboard.twitterapi_paging import balance_preflight
        p=policy(max_balance_reads=1);s=Store(p)
        class Balance:
            def credits(self):return 0
        balance_preflight(Balance(),s,expected_policy=p)
        self.assertEqual(s.state['balance_reads'],['zero_recharge'])
        with self.assertRaises(FetchError):balance_preflight(Balance(),s,expected_policy=p)
        s=Store(p)
        class Unknown:
            def credits(self):raise RuntimeError('timeout')
        with self.assertRaises(RuntimeError):balance_preflight(Unknown(),s,expected_policy=p)
        self.assertEqual(s.state['balance_reads'],['pending'])
        with self.assertRaises(FetchError):balance_preflight(Balance(),s,expected_policy=p)
    def test_invalid_cache_blocks_balance(self):
        from signalboard.twitterapi_paging import balance_preflight
        p=policy(max_balance_reads=1);s=Store(p);s.state['reserved_credits']=300
        class Never:
            def credits(self):raise AssertionError('must not request')
        with self.assertRaises(FetchError):balance_preflight(Never(),s,expected_policy=p)
