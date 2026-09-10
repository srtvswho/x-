from datetime import datetime, timezone
import copy
import gzip
import hashlib
import json
from pathlib import Path
import sys
import unittest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from signalboard.focus_labels import build_labels, explicit_security_long, ROOT

NOW=datetime(2026,9,10,12,tzinfo=timezone.utc)
SOURCE='tw_aleabitoreddit'
def fixture():
    events=[];ev=[]
    for i,(t,date) in enumerate([('CRDO','2025-03-01'),('MRVL','2025-04-01'),('AAOI','2026-09-09')]):
        e={'source_id':SOURCE,'post_id':str(i),'ticker':t,'published_at':date,'captured_at':date,
           'direction':'long','raw_text':f'I am long ${t}.','interpretation_current':True}
        events.append(e)
        ev.append(dict(e,strict_eligible=True,identity_exclusion=None,group='US_equity',
                       raw_hash=hashlib.sha256(e['raw_text'].encode()).hexdigest(),
                       results={'60':{'exit_date':'2025-08-01','direction_return':.3,'excess':{'SOXX':.15}}} if i<2 else {}))
    return events,{'events':ev,'prices_as_of':'2026-09-09'}
def run(events,ev):return build_labels(events,ev,{},NOW,seeds=[])

def test_three_overlapping_tags_and_no_buy_probability():
    events,ev=fixture();a=next(x for x in run(events,ev)['alerts'] if x['ticker']=='AAOI')
    assert a['tags']==['field_discovery','quarter_supported','rolling_supported']
    assert a['is_live'] and not a['automatic_buy']
    assert a['quarter_profile']['n']==2 and a['rolling_profile']['n']==2

def test_insufficient_history_still_gets_discovery():
    events,ev=fixture();ev['events'][0]['results']={}
    a=next(x for x in run(events,ev)['alerts'] if x['ticker']=='AAOI')
    assert a['tags']==['field_discovery']

def test_quarter_and_post_cutoffs_are_different_and_future_returns_excluded():
    events,ev=fixture()
    for e in ev['events'][:2]:e['results']['60']['exit_date']='2026-08-01'
    a=next(x for x in run(events,ev)['alerts'] if x['ticker']=='AAOI')
    assert a['tags']==['field_discovery','rolling_supported']
    for e in ev['events'][:2]:e['results']['60']['exit_date']='2026-09-09'
    a=next(x for x in run(events,ev)['alerts'] if x['ticker']=='AAOI')
    assert a['tags']==['field_discovery']

def test_repeat_reversal_and_backfill_do_not_become_live_new_calls():
    events,ev=fixture();events.append(dict(events[-1],post_id='repeat',published_at='2026-09-10'))
    assert len([a for a in run(events,ev)['alerts'] if a['ticker']=='AAOI'])==1
    events.insert(0,dict(events[-1],post_id='old-short',direction='short',published_at='2025-01-01',captured_at='2025-01-01'))
    assert not [a for a in run(events,ev)['alerts'] if a['ticker']=='AAOI']
    events,ev=fixture();events[-1]['published_at']='2026-09-05';events[-1]['captured_at']='2026-09-09'
    a=next(x for x in run(events,ev)['alerts'] if x['ticker']=='AAOI')
    assert a['backfill'] and not a['is_live']
    events,ev=fixture();events.append(dict(events[-1],post_id='later-short',direction='short',published_at='2026-09-10'))
    a=next(x for x in run(events,ev)['alerts'] if x['ticker']=='AAOI')
    assert a['withdrawn'] and not a['is_live'] and a['tags']

def test_missing_or_unreviewed_market_does_not_inherit_positive_tags():
    events,ev=fixture();ev['events'].pop()
    a=next(x for x in run(events,ev)['alerts'] if x['ticker']=='AAOI')
    assert not a['tags'] and a['issues']
    events,ev=fixture();events[-1]['interpretation_current']=False
    a=next(x for x in run(events,ev)['alerts'] if x['ticker']=='AAOI')
    assert not a['tags']

def test_security_attribution_conditions_and_negation():
    for text,t in [('If supply tightens, margins improve.\nI am long $MU.','MU'),
                   ('My daughter got a gift from Dell.\nLong $DELL.','DELL'),
                   ("I am initiating a position in $LITE. If TPU grows, margins improve.",'LITE')]:
        assert explicit_security_long(text,t),text
    for text in ['I would buy $MU if it falls.','I am not long $MU.',"Don't buy $MU.",
                 'An analyst says buy $MU.', '> Long $MU', 'Buy a Micron SSD.',
                 'Buy $NVDA. $MU supplies its memory.', 'I will buy $MU tomorrow.',
                 'Are you long $MU?', 'RT @someone: Long $MU.']:
        assert not explicit_security_long(text,'MU'),text

def test_exact_historical_replay_equivalence_for_all_three_labels():
    scored=json.load(gzip.open(ROOT/'outputs/kol_reaudit_20260910/scored_events.json.gz','rt'))
    ev=json.load(gzip.open(ROOT/'outputs/focus_backtest_20260910/policy_evidence.json.gz','rt'))
    live=build_labels(scored,ev,{},NOW)
    labels={int(a['post_id']).__str__()+':'+a['source_id']+':'+a['ticker']:a for a in live['alerts']}
    replay=json.load(gzip.open(ROOT/'outputs/post_incremental_value_20260910/results.json.gz','rt'))
    n=0
    for d in replay['decisions']:
        if not d['confirmed_field']:continue
        a=labels[str(d['post_id'])+':'+d['source_id']+':'+d['ticker']]
        assert 'field_discovery' in a['tags']
        tag='quarter_supported' if d['mode']=='frozen_quarter' else 'rolling_supported'
        assert (tag in a['tags'])==(d['profile']['classification']=='positive'),(d['ticker'],tag)
        n+=1
    assert n==50
    scoped=[a for a in live['alerts'] if '2025-10-01'<=a['published_at']<'2026-09-10']
    assert [sum(t in a['tags'] for a in scoped) for t in ['field_discovery','quarter_supported','rolling_supported']]==[25,10,14]

if __name__=='__main__':
    suite=unittest.TestSuite(unittest.FunctionTestCase(v) for k,v in list(globals().items()) if k.startswith('test_'))
    raise SystemExit(not unittest.TextTestRunner(verbosity=2).run(suite).wasSuccessful())
