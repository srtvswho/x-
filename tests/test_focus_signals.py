from datetime import datetime, timezone
import hashlib
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from signalboard.focus_signals import assess, normalize, profile

NOW = datetime(2026, 9, 10, 12, tzinfo=timezone.utc)
SOURCE = 'tw_jukan05'
COVERAGE = {SOURCE: {'raw_posts': 500, 'history_days': 500, 'review_complete': True,
                     'raw_end': '2026-09-10T10:00:00+00:00'}}


def call(t='ALAB', pid='new', date='2026-09-09T10:00:00+00:00', direction='long', text=None):
    return {'source_id': SOURCE, 'post_id': pid, 'ticker': t, 'published_at': date,
            'direction': direction, 'raw_text': text or f'I am buying ${t} shares. Undervalued.',
            'captured_at': date, 'raw_url': 'https://x.com/jukan05/status/'+pid}


def evidence():
    rows = []
    for i,t in enumerate(['NVDA','AMD','AVGO','MU','TSM']):
        e=call(t, str(i), f'2025-{1+i:02d}-01T10:00:00+00:00')
        e.update(strict_eligible=True,strict_exclusion=None,identity_exclusion=None,group='US_equity',
                 raw_hash=hashlib.sha256(e['raw_text'].encode()).hexdigest(),
                 results={'60': {'exit_date': '2025-08-01', 'direction_return': .2, 'excess': {'SOXX': .1}}})
        rows.append(e)
    return {'events':rows,'version':'test','reviewed_at':'2026-09-10','prices_as_of':'2026-09-09'}


def run(rows, ev=None, coverage=None):
    return assess(rows, ev or evidence(), COVERAGE if coverage is None else coverage, NOW)


def test_trusted_field_new_security_is_priority_but_not_a_buy_or_probability():
    a=run([call()])['alerts'][0]
    assert a['priority']=='priority'
    assert a['profile']['n']==5
    assert a['profile']['up_probability'] is None
    assert a['automatic_buy'] is False
    assert a['decision_stage']=='research_candidate'


def test_repeated_calls_do_not_realert_and_id_is_stable():
    first=call(); second=call(pid='repeat',date='2026-09-10T10:00:00+00:00')
    a=run([first])['alerts']; b=run([second,first])['alerts']
    assert len(b)==1 and a[0]['id']==b[0]['id']
    assert not run([call(pid='old',date='2025-01-01T00:00:00+00:00'),first])['alerts']


def test_old_short_then_long_is_not_new_security():
    assert not run([call(pid='old',date='2025-01-01',direction='short'),call()])['alerts']


def test_listing_alias_does_not_create_new_issuer():
    assert not run([call('000660.KS','old','2025-01-01'),call('SKHY')])['alerts']


def test_backfill_is_not_live_priority_and_old_posts_are_not_new():
    e=call(date='2026-09-05T10:00:00+00:00');e['captured_at']='2026-09-09T00:00:00+00:00'
    a=run([e])['alerts'][0]
    assert a['backfill'] and a['priority']=='review'
    assert not run([call(date='2025-01-01')])['alerts']


def test_future_outcomes_and_candidate_ticker_do_not_train_its_alert():
    ev=evidence()
    for e in ev['events']:e['results']['60']['exit_date']='2026-09-09'
    a=run([call()],ev)['alerts'][0]
    assert a['profile']['n']==0 and a['priority']=='review'
    p=profile(evidence()['events'],SOURCE,'semis',60,NOW,exclude_ticker='NVDA')
    assert p['n']==4 and all(e['ticker']!='NVDA' for e in p['samples'])


def test_many_posts_on_one_winner_are_not_independent_samples():
    ev=evidence()
    for e in ev['events']:e['ticker']='NVDA'
    assert run([call()],ev)['alerts'][0]['profile']['n']==1
    assert run([call()],ev)['alerts'][0]['priority']=='review'


def test_one_post_basket_cannot_qualify_as_many_independent_calls():
    ev=evidence()
    for e in ev['events']:e['post_id']='one-post'
    assert run([call()],ev)['alerts'][0]['priority']=='review'


def test_no_domain_transfer_and_stale_baseline_or_missing_coverage_downgrades():
    assert run([call('LULU')])['alerts'][0]['priority']=='review'
    ev=evidence();ev['prices_as_of']='2026-01-01'
    assert run([call()],ev)['alerts'][0]['priority']=='review'
    assert run([call()],coverage={})['alerts'][0]['priority']=='review'


def test_product_buy_is_excluded_and_conditions_and_sarcasm_need_review():
    assert not run([call(text='Buy one at $120K, a token generator.')])['alerts']
    for text in ['I would buy $ALAB if it falls.', 'Go ahead and short $ALAB. I am bullish.']:
        assert run([call(text=text)])['alerts'][0]['priority']=='review'


def test_later_reversal_withdraws_priority():
    a=run([call(),call(pid='reversal',date='2026-09-10T10:00:00+00:00',direction='short')])['alerts'][0]
    assert a['priority']=='review' and any('反向' in x for x in a['issues'])


def test_changed_post_does_not_inherit_saved_semantic_adjudication():
    ev=evidence();e=ev['events'][0];e['strict_eligible']=False
    old=call('NVDA','0','2025-01-01T10:00:00+00:00')
    assert not normalize([old],ev)[0]['eligible']
    old['raw_text']='I am buying NVDA shares after fresh earnings.'
    assert normalize([old],ev)[0]['semantic_review']=='new_extraction'


def test_first_call_with_missing_price_does_not_get_replaced_by_later_winner():
    ev=evidence();first=dict(ev['events'][0],published_at='2024-01-01',post_id='earlier',results={})
    ev['events'].append(first)
    assert profile(ev['events'],SOURCE,'semis',60,NOW)['n']==4


def test_same_day_close_is_not_available_to_a_morning_post():
    ev=evidence()
    for e in ev['events']:e['results']['60']['exit_date']='2026-09-09'
    assert run([call()],ev)['alerts'][0]['profile']['n']==0


def test_refresh_entry_is_next_open_and_missing_market_days_fail_closed():
    from scripts.refresh_focus_evidence import outcome
    from signalboard.focus_signals import stamp
    prices=[{'ts':stamp(f'2026-09-0{i}T13:30:00+00:00').timestamp(), 'date':f'2026-09-0{i}',
             'open':100, 'close':100+i} for i in range(1,5)]
    e=call(date='2026-09-01T15:00:00+00:00')
    r=outcome(e,prices,prices,3)
    assert r['exit_date']=='2026-09-04' and abs(r['direction_return']-.04)<1e-9
    assert outcome(e,prices,prices[:2]+prices[3:],3) is None
    assert outcome(e,prices,prices,4) is None


def test_frozen_cutoff_excludes_results_that_matured_before_signal_but_after_cutoff():
    ev=evidence()
    for e in ev['events']:e['results']['60']['exit_date']='2026-08-15'
    assert run([call()],ev)['alerts'][0]['priority']=='priority'
    frozen=assess([call()],ev,COVERAGE,NOW,profile_as_of=datetime(2026,7,1,tzinfo=timezone.utc))
    assert frozen['alerts'][0]['profile']['n']==0
    assert frozen['alerts'][0]['priority']=='review'


def test_unobserved_future_post_is_not_available():
    e=call();e['captured_at']='2026-09-12T00:00:00+00:00'
    assert not run([e])['alerts']


if __name__ == '__main__':
    import unittest
    suite=unittest.TestSuite(unittest.FunctionTestCase(fn) for name,fn in list(globals().items()) if name.startswith('test_'))
    raise SystemExit(not unittest.TextTestRunner(verbosity=2).run(suite).wasSuccessful())
