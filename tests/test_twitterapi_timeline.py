"""Offline synthetic timeline fixtures, no credentials or transport."""
from copy import deepcopy
from datetime import datetime, timezone
import unittest
from signalboard.twitterapi_timeline import TimelineError, validate_page, accumulate

START = datetime(2026, 11, 15, 16, tzinfo=timezone.utc)
END = datetime(2026, 11, 16, 2, 34, tzinfo=timezone.utc)

def tweet(id='9007199254740993123', at='Sun Nov 15 20:00:00 +0000 2026'):
    return {'id':id,'text':'synthetic','createdAt':at,'author':{'userName':'Jukan05'}}

def page(rows=None, more=False, cursor='', pin=None):
    return {'status':'success','data':{'tweets':[tweet()] if rows is None else rows,'pin_tweet':pin},
            'has_next_page':more,'next_cursor':cursor}

class Tests(unittest.TestCase):
    def fold(self, *pages):return accumulate(list(pages),'jukan05',START,END)
    def error(self, data, code):
        with self.assertRaises(TimelineError) as caught:validate_page(data,'jukan05')
        self.assertEqual(str(caught.exception),code)
        self.assertEqual(caught.exception.code,code)
    def test_nested_schema_and_string_id(self):
        result=validate_page(page(),'jukan05')
        self.assertEqual(result.tweets[0]['id'],'9007199254740993123')
        self.assertTrue(self.fold(page()).complete)
    def test_envelope_field_codes(self):
        cases=[(None,'response.object'),({},'response.status'),({'status':'private-secret'},'response.status')]
        for value,code in cases:self.error(value,code)
        for field,value,code in [('data',[],'response.data'),('has_next_page',1,'response.has_next_page'),('next_cursor',None,'response.next_cursor')]:
            p=page();p[field]=value;self.error(p,code)
        p=page();p['data']['tweets']={};self.error(p,'response.data.tweets')
        self.error(page([tweet()]*21),'response.data.tweets.limit')
        p=page();p['tweets']=p.pop('data')['tweets'];self.error(p,'response.data')
    def test_tweet_field_codes(self):
        self.error(page([None]),'tweet.object')
        for key,value,code in [('id',123,'tweet.id'),('id','１２３','tweet.id'),('text','','tweet.text'),('text',None,'tweet.text'),('author',None,'tweet.author'),('author',{'userName':'other'},'tweet.author.userName'),('author',{'userName':'jukan05','protected':True},'tweet.author.availability'),('createdAt',None,'tweet.createdAt'),('createdAt','secret-error','tweet.createdAt'),('createdAt','Sun Nov 15 20:00:00 2026','tweet.createdAt'),('createdAt','Mon Nov 15 20:00:00 +0000 2026','tweet.createdAt')]:
            row=tweet();row[key]=value;self.error(page([row]),code)
    def test_pin_old_not_boundary_or_evidence(self):
        pin=tweet('9','Sun Nov 01 00:00:00 +0000 2026')
        result=self.fold(page(more=True,cursor='a',pin=pin))
        self.assertFalse(result.complete);self.assertEqual(result.reason,'continuation_required')
        result=self.fold(page([],pin=pin))
        self.assertFalse(result.complete);self.assertEqual(result.reason,'empty_unverified')
        self.assertEqual(len(result.tweets),0)
    def test_empty_pin_object_is_absent(self):
        validated=validate_page(page(pin={}),'jukan05')
        self.assertIsNone(validated.pin_tweet)
        self.assertEqual(len(validated.tweets),1)
        result=self.fold(page([],pin={}))
        self.assertFalse(result.complete)
        self.assertEqual(result.reason,'empty_unverified')
    def test_current_pin_included_but_not_evidence(self):
        pin=tweet('99')
        result=self.fold(page([],pin=pin))
        self.assertFalse(result.complete)
        self.assertEqual(result.reason,'empty_unverified')
        self.assertEqual([r['id'] for r in result.tweets],['99'])
        result=self.fold(page(pin=pin))
        self.assertTrue(result.complete)
        self.assertEqual(len(result.tweets),2)
        result=self.fold(page(pin=tweet()))
        self.assertEqual(len(result.tweets),1)
    def test_pin_conflict_across_main_and_pages(self):
        pin=tweet();pin['text']='conflict'
        with self.assertRaises(TimelineError) as caught:self.fold(page(pin=pin))
        self.assertEqual(caught.exception.code,'tweet.id.conflict')
        with self.assertRaises(TimelineError):
            self.fold(page([tweet('88')],True,'a',pin=pin),page())
    def test_invalid_pin_rejected(self):
        self.error(page(pin={'id':'secret'}),'tweet.id')
    def test_outside_rows_filtered_and_boundary_crossed(self):
        rows=[tweet('1','Mon Nov 16 03:00:00 +0000 2026'),tweet('2'),tweet('3','Sun Nov 15 15:59:59 +0000 2026')]
        result=self.fold(page(rows,True,'a'))
        self.assertTrue(result.complete);self.assertEqual(result.reason,'start_boundary_crossed')
        self.assertEqual([r['id'] for r in result.tweets],['2'])
    def test_end_exclusive_start_inclusive(self):
        result=self.fold(page([tweet('1','Mon Nov 16 02:34:00 +0000 2026'),tweet('2','Sun Nov 15 16:00:00 +0000 2026')],True,'a'))
        self.assertFalse(result.complete);self.assertEqual([r['id'] for r in result.tweets],['2'])
    def test_validate_entire_page_before_boundary(self):
        self.error(page([tweet('1','Sun Nov 15 15:00:00 +0000 2026'),tweet('2')],True,'a'),'timeline.order')
        with self.assertRaises(TimelineError):self.fold(page([tweet('1','Sun Nov 15 15:00:00 +0000 2026'),{'id':'2'}]))
    def test_order_across_pages(self):
        with self.assertRaises(TimelineError) as caught:
            self.fold(page([tweet('1','Sun Nov 15 18:00:00 +0000 2026')],True,'a'),page([tweet('2')]))
        self.assertEqual(caught.exception.code,'timeline.order')
    def test_multiple_pages_old_boundary(self):
        result=self.fold(page(more=True,cursor='a'),page([tweet('2','Sun Nov 15 17:00:00 +0000 2026')],True,'b'),page([tweet('3','Sun Nov 15 15:00:00 +0000 2026')]))
        self.assertTrue(result.complete);self.assertEqual(result.pages,3);self.assertEqual(len(result.tweets),2)
    def test_initial_empty_unverified(self):
        result=self.fold(page([]));self.assertFalse(result.complete);self.assertEqual(result.reason,'empty_unverified')
    def test_empty_final_after_evidence(self):
        result=self.fold(page(more=True,cursor='a'),page([]))
        self.assertTrue(result.complete);self.assertEqual(result.reason,'timeline_exhausted')
    def test_broken_or_repeated_cursor_incomplete(self):
        for p in [page([],True,'a'),page(more=True,cursor='')]:
            result=self.fold(p);self.assertFalse(result.complete);self.assertEqual(result.reason,'pagination_incomplete')
        result=self.fold(page(more=True,cursor='a'),page(more=True,cursor='a'))
        self.assertFalse(result.complete);self.assertEqual(result.reason,'pagination_incomplete')
    def test_duplicate_and_conflict(self):
        result=self.fold(page(more=True,cursor='a'),page())
        self.assertEqual(len(result.tweets),1)
        changed=tweet();changed['text']='changed'
        with self.assertRaises(TimelineError) as caught:self.fold(page(more=True,cursor='a'),page([changed]))
        self.assertEqual(caught.exception.code,'tweet.id.conflict')
    def test_pure_no_input_mutation(self):
        p=page();before=deepcopy(p);result=self.fold(p);result.tweets[0]['text']='mutation'
        self.assertEqual(p,before)
    def test_scope_errors(self):
        for args in [([], 'bad handle',START,END),([], 'jukan05',END,START),([], 'jukan05',START.replace(tzinfo=None),END),({},'jukan05',START,END)]:
            with self.assertRaises(TimelineError):accumulate(*args)

if __name__=='__main__':unittest.main()
