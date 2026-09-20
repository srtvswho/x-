"""Regression cases for grounded author summaries and ticker attribution."""
import sys
from pathlib import Path
import unittest
sys.path.insert(0, str(Path(__file__).resolve().parents[1]/'scripts/dashboard'))
from author_briefs import make_brief, stamp


def row(pid, date, text, tickers=(), direction='long', **extra):
    return dict(post_id=pid, published_at=date+'T12:00:00+00:00', summary=text,
                raw_text=text, ticker=list(tickers), direction=direction, attribution='ORIGINAL', **extra)

class AuthorBriefTests(unittest.TestCase):
    def brief(self, rows, events=()):
        return make_brief(rows, events, stamp('2026-08-20T00:00:00Z'), stamp('2026-09-20T00:00:00Z'), 'Test', [r['published_at'] for r in rows])

    def test_mention_does_not_inherit_whole_post_direction(self):
        r=row('1','2026-09-01','作者看多 AXTI；把 SNDK 作为历史涨价的类比。',['AXTI','SNDK'])
        b=self.brief([r],[dict(r,ticker='AXTI')])
        self.assertEqual([s['ticker'] for s in b['securities']], ['AXTI'])
        self.assertEqual([s['ticker'] for s in b['mentions']], ['SNDK'])

    def test_conditions_are_not_unconditional_buys(self):
        r=row('1','2026-09-19','作者表示触底后考虑买入 SOL。',['SOL'])
        b=self.brief([r],[dict(r,ticker='SOL')])
        self.assertTrue(b['securities'][0]['conditional'])
        self.assertIn('触底后', b['paragraphs'][1]['text'])

    def test_same_security_opposite_horizons_are_not_confirmed_reversal(self):
        a=row('1','2026-08-22','作者长期看多 MU，需求持续增长。',['MU'])
        z=row('2','2026-09-18','作者短期看空 MU，需防回调。',['MU'],'short')
        b=self.brief([a,z],[dict(a,ticker='MU'),dict(z,ticker='MU')])
        self.assertEqual(b['securities'][0]['direction'],'short')
        self.assertEqual(len(b['changes']),1)
        c=b['changes'][0]
        self.assertIn('需核对',c['label'])
        self.assertEqual(c['before']['horizon'],'中长期')
        self.assertEqual(c['after']['horizon'],'短期')

    def test_full_window_timeline_and_no_future_leak(self):
        rows=[row('old','2026-08-22','作者认为存储短缺带来盈利改善。',['MU'])]
        rows += [row(str(i),'2026-09-18','作者认为激光供给不足。',['SIVE']) for i in range(40)]
        rows += [row('future','2026-09-21','未来未知内容',['NVDA'])]
        b=self.brief(rows)
        self.assertIn('old',[p['post_id'] for p in b['timeline']])
        self.assertEqual(b['post_count'],41)
        self.assertNotIn('future',str(b))

    def test_relay_disclosure_and_duplicate_posts(self):
        a=row('1','2026-09-01','转述券商看多',['MU']);a['attribution']='RELAYED'
        d=row('2','2026-09-02','作者披露持仓',['MU'],is_disc=1)
        b=self.brief([a,d,d],[dict(a,ticker='MU')])
        self.assertEqual(b['interpreted_count'],2)
        self.assertEqual(b['view_count'],0)
        self.assertEqual(b['securities'],[])
        self.assertIn('不足',b['change_note'])

    def test_no_posts_does_not_claim_unchanged(self):
        b=self.brief([])
        self.assertEqual(b['post_count'],0)
        self.assertIn('证据不足',b['change_note'])

if __name__=='__main__': unittest.main()
