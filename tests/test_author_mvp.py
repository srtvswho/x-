import copy
from datetime import datetime, timezone, timedelta
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('mvp', ROOT/'scripts/author_mvp_20260913.py')
m = importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)


class AuthorMVPTests(unittest.TestCase):
    def post(self, text='$MU buy, bullish on memory', author='bboczeng'):
        return m.normalize({'id':'123','author':{'userName':author},'text':text,
                            'createdAt':'2026-01-01T13:00:00Z'},author)

    def label(self, **changes):
        signal = dict(ticker='MU',direction='bullish',domain='memory',quote='$MU buy',
                      conditional=False,context_complete=True,horizon='unspecified')
        signal.update(changes)
        return {'posts':[{'id':'123','kind':'prospective','reason':'test','signals':[signal]}]}

    def test_monthly_caps(self):
        for total,_ in m.AUTHORS.values():
            values = m.windows(total)
            self.assertEqual(sum(v[2] for v in values),total)
            self.assertEqual(str(values[0][0]),'2025-09-01')
            self.assertEqual(str(values[-1][1]),'2026-09-01')
            self.assertTrue(all(a[1]==b[0] for a,b in zip(values,values[1:])))

    def test_combined_and_stage_cap(self):
        with tempfile.TemporaryDirectory() as directory:
            ledger = m.Ledger(Path(directory)/'ledger.json')
            ledger.reserve('scrape','apify','1.5')
            ledger.reserve('ai','ai','3.4')
            with self.assertRaises(m.Stop): ledger.reserve('overflow','ai','.000001')
            self.assertEqual(sum(r['reserved_micro_usd'] for r in ledger.rows),4900000)

    def test_unknown_no_refund_and_duplicate_on_restart(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory)/'ledger.json'
            ledger = m.Ledger(path)
            row = ledger.reserve('x','apify','1.5')
            ledger.finish(row,status='UNKNOWN')
            ledger = m.Ledger(path)
            with self.assertRaises(m.Stop): ledger.reserve('x','apify','.1')
            with self.assertRaises(m.Stop): ledger.reserve('y','apify','.1')

    def test_success_does_not_recycle_budget(self):
        with tempfile.TemporaryDirectory() as directory:
            ledger=m.Ledger(Path(directory)/'ledger.json')
            row=ledger.reserve('x','ai','3.4')
            ledger.finish(row,status='SUCCESS',usage_cost_peak_upper_usd=.01)
            with self.assertRaises(m.Stop): ledger.reserve('y','ai','.01')

    def test_micro_dollar_rounds_up(self):
        with tempfile.TemporaryDirectory() as directory:
            ledger=m.Ledger(Path(directory)/'ledger.json')
            self.assertEqual(ledger.reserve('x','ai','.0000001')['reserved_micro_usd'],1)

    def test_ai_byte_bound(self):
        text='中文投资分析'*1000
        upper,cost=m.ai_bound(text)
        self.assertGreater(upper,len(text.encode()))
        self.assertGreater(float(cost),2400*1.2/1e6)

    def test_valid_label(self):
        result=m.validate_labels(self.label(),[self.post()])
        self.assertEqual(result[0]['signals'][0]['ticker'],'MU')

    def test_unstated_security_excluded(self):
        result=m.validate_labels(self.label(ticker='NVDA'),[self.post()])
        self.assertEqual(result[0]['signals'],[])

    def test_fabricated_quote_excluded(self):
        result=m.validate_labels(self.label(quote='MU will double'),[self.post()])
        self.assertEqual(result[0]['signals'],[])

    def test_conditional_excluded(self):
        self.assertFalse(m.validate_labels(self.label(conditional=True),[self.post()])[0]['signals'])

    def test_news_excluded(self):
        label=self.label()
        label['posts'][0]['kind']='news'
        self.assertFalse(m.validate_labels(label,[self.post()])[0]['signals'])

    def test_incomplete_context_excluded(self):
        post=self.post()
        post['quote_context_missing']=True
        self.assertFalse(m.validate_labels(self.label(),[post])[0]['signals'])

    def test_duplicate_model_ids_blocked(self):
        label=self.label()
        label['posts']*=2
        with self.assertRaises(m.Stop): m.validate_labels(label,[self.post()])

    def test_kobeissi_stock_call_excluded(self):
        self.assertFalse(m.validate_labels(self.label(),[self.post(author='KobeissiLetter')])[0]['signals'])

    def test_wrong_author_rejected(self):
        self.assertIsNone(m.normalize({'id':'x','text':'hello','author':{'userName':'wrong'}},'bboczeng'))

    def test_rules_no_future_data(self):
        posts=[dict(self.post(),id=str(i)) for i in range(20)]
        a,_=m.select_candidates(posts,5)
        b,_=m.select_candidates(list(reversed(posts)),5)
        self.assertEqual([p['id'] for p in a],[p['id'] for p in b])

    def test_pure_news_screened(self):
        self.assertEqual(m.prefilter(self.post('BREAKING: gold price at 3000')),'no_directional_cue')

    def test_oversized_not_truncated(self):
        self.assertEqual(m.prefilter(self.post('$MU buy '+'文'*6000)),'long_post_not_truncated')

    def test_next_day_entry_and_maturity(self):
        bars=[dict(date=f'2026-01-{d:02}',open=100,close=100+d) for d in range(1,10)]
        event=dict(published_at='2026-01-01T13:00:00Z',direction='bullish')
        value=m.outcome(event,bars,bars,5)
        self.assertEqual(value['entry_date'],'2026-01-02')
        self.assertEqual(value['exit_date'],'2026-01-06')
        self.assertAlmostEqual(value['direction_adjusted_excess'],0)
        self.assertIsNone(m.outcome(event,bars,bars,20))

    def test_short_and_benchmark(self):
        stock=[dict(date='2026-01-02',open=100,close=90)]
        bench=[dict(date='2026-01-02',open=100,close=95)]
        value=m.outcome(dict(published_at='2026-01-01',direction='bearish'),stock,bench,1)
        self.assertAlmostEqual(value['directional_return'],.1)
        self.assertAlmostEqual(value['direction_adjusted_excess'],.05)

    def test_nonoverlap(self):
        events=[dict(author='a',ticker='MU',published_at=f'2026-01-{d:02}',outcomes={'20':dict(
            entry_date=f'2026-01-{d+1:02}',exit_date='2026-02-01',underlying_return=.1,directional_return=.1)}) for d in range(1,4)]
        self.assertEqual(m.summarize(events,20)['n'],3)
        self.assertEqual(m.summarize(events,20,True)['n'],1)

    def test_missing_secrets_zero_calls(self):
        with tempfile.TemporaryDirectory() as directory,patch.object(m,'OUT',Path(directory)),patch.dict(m.os.environ,{},clear=True),patch.object(m,'request') as request:
            with self.assertRaises(m.Stop): m.preflight()
            request.assert_not_called()

    def test_pricing_fail_closed(self):
        p={'startedAt':'2026-01-01','pricingModel':'PAY_PER_EVENT','pricingPerEvent':{'actorChargeEvents':{
            'apify-default-dataset-item':{'eventTieredPricingUsd':{'FREE':{'tieredEventPriceUsd':.0004}}}}}}
        self.assertEqual(m.checked_pricing({'pricingInfos':[p]},m.now()),p)
        p['pricingPerEvent']['actorChargeEvents']['start']={}
        with self.assertRaises(m.Stop): m.checked_pricing({'pricingInfos':[p]},m.now())

    def test_workflow_no_schedule_no_production(self):
        workflow=(ROOT/'.github/workflows/author-mvp-20260913.yml').read_text()
        self.assertNotIn('schedule:',workflow)
        self.assertNotIn('HEAD:master',workflow)
        self.assertNotIn('build_dashboard',workflow)
        self.assertIn('Campaign already claimed',workflow)


if __name__=='__main__': unittest.main()
