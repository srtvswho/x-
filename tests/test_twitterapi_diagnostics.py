"""Offline diagnostic fixtures only; no live payload or network evidence.

Official pagination permits empty repeated cursors as a stop signal. Current
strict reader rejects that shape. This is a plausible branch, not a diagnosis
of any real run. All failures must retain the stop/charged-reservation state.
"""
import unittest
from unittest.mock import patch
from test_twitterapi_paging import Store, Client, page, policy, START, END, NOW
from signalboard.twitterapi_io import FetchError
from signalboard.twitterapi_paging import advance_page

class DiagnosticFixtures(unittest.TestCase):
    def setUp(self):
        self.clock=patch('signalboard.twitterapi_paging._current_time',return_value=NOW)
        self.clock.start();self.addCleanup(self.clock.stop)
    def step(self,c,s):
        return advance_page(c,s,'jukan05',START,END,now=NOW,expected_policy=policy())
    def assert_stopped(self,s,c):
        self.assertEqual(s.state['reserved_credits'],600)
        entry=next(iter(s.state['windows'].values()))
        self.assertEqual(entry['status'],'uncertain')
        self.assertEqual(len(entry['pages']),1)
        self.assertEqual(entry['pending']['page'],2)
        calls=len(c.calls)
        with self.assertRaises(FetchError):self.step(c,s)
        self.assertEqual(len(c.calls),calls)
    def test_documented_empty_repeated_cursor_is_possible_failure_branch(self):
        s=Store();c=Client(page(more=True,cursor='cursor-a'),page([],more=True,cursor='cursor-a'))
        self.step(c,s)
        with self.assertRaises(FetchError):self.step(c,s)
        self.assert_stopped(s,c)
    def test_synthetic_network_failure_retains_stop(self):
        s=Store();c=Client(page(more=True,cursor='a'),TimeoutError('synthetic network failure'))
        self.step(c,s)
        with self.assertRaises(FetchError) as caught:self.step(c,s)
        self.assertNotIn('synthetic',str(caught.exception))
        self.assert_stopped(s,c)
    def test_synthetic_http_failure_retains_stop(self):
        s=Store();c=Client(page(more=True,cursor='a'),FetchError('HTTP fixture 429'))
        self.step(c,s)
        with self.assertRaises(FetchError) as caught:self.step(c,s)
        self.assertNotIn('429',str(caught.exception))
        self.assert_stopped(s,c)
    def test_synthetic_schema_failure_retains_stop(self):
        s=Store();c=Client(page(more=True,cursor='a'),{'tweets':'invalid schema fixture'})
        self.step(c,s)
        with self.assertRaises(FetchError):self.step(c,s)
        self.assert_stopped(s,c)
    def test_synthetic_persistence_failure_retains_stop(self):
        s=Store();c=Client(page(more=True,cursor='a'),page([]))
        self.step(c,s)
        s.fail_save=4 # page2 reserved successfully; response persistence fails
        with self.assertRaises(FetchError):self.step(c,s)
        self.assert_stopped(s,c)

if __name__=='__main__':unittest.main()
