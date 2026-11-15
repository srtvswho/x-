import unittest
from datetime import datetime, timezone
from signalboard.twitterapi_io import Budget, FetchError, search
START = datetime(2026,11,14,tzinfo=timezone.utc)
END = datetime(2026,11,15,tzinfo=timezone.utc)
def tweet(id='9007199254740993123'):
    return dict(id=id,text='test',createdAt='Sat Nov 14 12:00:00 +0000 2026',author={'userName':'jukan05'})
def page(rows=None, more=False, cursor=''):
    return dict(tweets=[tweet()] if rows is None else rows,has_next_page=more,next_cursor=cursor)
class Fake:
    def __init__(self,*pages): self.pages=list(pages); self.calls=[]
    def get(self,path,params):
        self.calls.append((path,params)); return self.pages.pop(0)
class Tests(unittest.TestCase):
    def run_search(self,client,n=1): return search(client,'jukan05',START,END,Budget(n),n)
    def test_string_id(self): self.assertEqual(self.run_search(Fake(page())).tweets[0]['id'],'9007199254740993123')
    def test_numeric_id_rejected(self):
        with self.assertRaises(FetchError): self.run_search(Fake(page([tweet(9007199254740993123)])))
    def test_partial(self): self.assertFalse(self.run_search(Fake(page(more=True,cursor='a'))).complete)
    def test_empty_not_healthy(self): self.assertFalse(self.run_search(Fake(page([]))).complete)
    def test_missing_pagination(self):
        with self.assertRaises(FetchError): self.run_search(Fake({'tweets':[]}))
    def test_dedupe(self): self.assertEqual(len(self.run_search(Fake(page(more=True,cursor='a'),page()),2).tweets),1)
    def test_stalled_cursor(self):
        with self.assertRaises(FetchError): self.run_search(Fake(page(more=True,cursor='a'),page(more=True,cursor='a')),2)
    def test_wrong_author(self):
        row=tweet(); row['author']['userName']='other'
        with self.assertRaises(FetchError): self.run_search(Fake(page([row])))
    def test_out_of_window(self):
        row=tweet(); row['createdAt']='Sun Nov 15 12:00:00 +0000 2026'
        with self.assertRaises(FetchError): self.run_search(Fake(page([row])))
    def test_budget_shared(self):
        budget=Budget(1); client=Fake(page())
        search(client,'jukan05',START,END,budget)
        with self.assertRaises(FetchError): search(client,'jukan05',START,END,budget)
        self.assertEqual(len(client.calls),1)
    def test_query(self):
        client=Fake(page());self.run_search(client)
        self.assertIn('since_time:1794614400',client.calls[0][1]['query'])
    def test_failure_no_retry(self):
        client=Fake({})
        with self.assertRaises(FetchError): self.run_search(client)
        self.assertEqual(len(client.calls),1)
if __name__=='__main__': unittest.main()
