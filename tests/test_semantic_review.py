import hashlib
import sys
import unittest
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(ROOT),str(ROOT/'scripts/dashboard')]
from signalboard.semantic_review import reviews, apply_reviews, post_reviews, review_market_records
from test_first_call_repair import database, post
from common import query_call_performance_events
from build_dashboard import query_call_performance, get_prices

class SemanticReviewTests(unittest.TestCase):
    def test_reviewed_posts_flow_through_shared_query_without_rewriting_raw(self):
        for review in reviews():
            with self.subTest(post=review['post_id']):
                con=database()
                ticker='NVDA' if review['ticker']=='*' else review['ticker']
                post(con,review['post_id'],'2026-01-01',source=review['source_id'],
                     ticker=ticker,text=review['raw_text'],direction='short')
                events=query_call_performance_events(con)
                if review['decision']=='correct_direction':
                    self.assertEqual(events[0]['direction'],'long')
                    con.execute('INSERT INTO ticker_prices VALUES(?,?,?,?,?)',(ticker,'2026-01-01',10,20,'2026-09-11'))
                    self.assertEqual(query_call_performance(con)[0]['directional_return'],100)
                else:
                    self.assertEqual(events,[])
                self.assertEqual(con.execute('SELECT direction FROM extractions_intel').fetchone()[0],'short')
                self.assertEqual(con.execute('SELECT raw_text FROM raw_posts').fetchone()[0],review['raw_text'])
                con.close()

    def test_changed_source_is_quarantined(self):
        review=next(r for r in reviews() if r['decision']=='correct_direction')
        e=dict(review,raw_text=review['raw_text']+' edited',direction='short')
        self.assertEqual(apply_reviews([e]),[])
        self.assertEqual(post_reviews(e['source_id'],e['post_id'],e['raw_text'])[0]['decision'],'quarantine')

    def test_single_security_correction_does_not_change_other_security(self):
        review=next(r for r in reviews() if r['ticker']=='IREN')
        rows=review_market_records([dict(review,ticker=['IREN','NBIS'],direction='short')])
        self.assertEqual([(r['ticker'],r['direction']) for r in rows],[(['IREN'],'long'),(['NBIS'],'short')])
        self.assertEqual(review['direction'],'long')

    def test_source_identity_and_hash_are_required(self):
        for review in reviews():
            self.assertEqual(hashlib.sha256(review['raw_text'].encode()).hexdigest(),review['raw_sha256'])
            self.assertEqual(post_reviews('different',review['post_id'],review['raw_text']),[])

    def test_product_purchase_remains_visible_without_stock_direction(self):
        review=next(r for r in reviews() if r['ticker']=='MU')
        row,=review_market_records([dict(review,ticker=['MU'],direction='long')])
        self.assertEqual(row['direction'],'neutral')
        self.assertEqual(row['raw_text'],review['raw_text'])

if __name__=='__main__':
    unittest.main()
