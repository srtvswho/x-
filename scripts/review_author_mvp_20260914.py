#!/usr/bin/env python3
"""Freeze a source-only assistant review, then calculate descriptive event returns.

No paid calls. Review uses original text, not future prices. Original report and
labels stay frozen. This is an exploratory revised eligibility policy, not an
independent human review or a new extraction of omitted model signals.
"""
import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path
import sys
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'scripts'))
import author_mvp_20260913 as m

ACCEPT={0,4,6,11,12,15,16,17,18,19,20,25,26,29,30,33,34,35,36,39,41,43,44,45,54,55,56,57,61,62,63,64,65,66,68,73,74,85,99,109,110,111,112,130,131}
REASONS={
 'volatility_not_direction':[1],
 'ambiguous_asset_or_sector_target':[2,10,42,49,71,75,127],
 'irony_hyperbole_or_wish_not_clear_forecast':[3,14,21,38,46,47,48],
 'third_party_research_not_own_call':[5,27,28,93,97,98,106,107,108],
 'earnings_or_business_outlook_not_directional_asset_view':[7,22,67,70,72,78,79,88,90,91,92,94,95,96,100,101,102,103,104,105,113,114,115,119,120,121,122,123,124,125,126,132,133,134,135],
 'conditional_or_not_current_entry':[8,23,24,40,50,51,52,53,76,82,84,86,87,89,116,117,118],
 'wrong_asset_attribution':[9,31,32],
 'intraday_horizon_not_testable_at_next_date_open':[13,69],
 'model_direction_disagrees_with_source_path':[37,59,60],
 'duplicate_post_asset_direction':[58],
 'retrospective_not_new_forecast':[77,80,81,83],
 'allocation_discussion_without_direction':[128,129],
}

def freeze(source):
    path=source/'schema_audit/candidates.json'
    events=json.loads(path.read_text())
    exclusions={i:r for r,ids in REASONS.items() for i in ids}
    assert ACCEPT.isdisjoint(exclusions)
    assert ACCEPT | set(exclusions)==set(range(len(events)))
    decisions=[]
    for e in events:
        i=e['audit_index']
        decisions.append({k:e[k] for k in ['audit_index','id','author','ticker','direction','raw_hash','quote','url']} |
             {'accepted':i in ACCEPT,'reason':'own_current_direction_or_valuation_thesis' if i in ACCEPT else exclusions[i]})
    manifest={'policy':'assistant-source-review-v1-20260914','reviewer':'Codex assistant (not independent human)',
              'candidate_sha256':hashlib.sha256(path.read_bytes()).hexdigest(),
              'review_inputs':'Original post text and model proposal; no forward returns used to select decisions.',
              'scope':'Strict subset of persisted model proposals; ambiguous targets, conditional entries, pure business news, wrong directions excluded; no direction flips or newly invented signals.',
              'limitations':'Long-term views and event-specific horizons are retained as views, but fixed-horizon returns do not test their exact original targets. Quote metadata was corrected offline; original model did not receive quoted body.',
              'decisions':decisions}
    m.save(source/'schema_audit/review_manifest.json',manifest)
    print(json.dumps({'accepted':len(ACCEPT),'authors':dict(Counter(e['author'] for e in events if e['audit_index'] in ACCEPT))}))

def calculate(source):
    folder=source/'schema_audit'
    manifest=json.loads((folder/'review_manifest.json').read_text())
    assert hashlib.sha256((folder/'candidates.json').read_bytes()).hexdigest()==manifest['candidate_sha256']
    accepted={(d['id'],d['ticker'],d['direction']) for d in manifest['decisions'] if d['accepted']}
    labels=json.loads((folder/'labels.json').read_text())
    for p in labels:
        seen=set(); signals=[]
        for s in p['signals']:
            key=(p['id'],s['ticker'],s['direction'])
            if key in accepted and key not in seen:signals.append(s);seen.add(key)
        p['signals']=signals
    old_out,old_loader=m.OUT,m.load_prices
    def cached_loader(tickers,as_of):
        prices,missing={},set()
        for t in tickers:
            f=source/'prices'/f'{t}.json'
            if f.exists():prices[t]=m.yahoo_bars(json.loads(f.read_text()),as_of)
            else:missing.add(t)
        extra,failures=old_loader(missing,as_of)
        return prices|extra,failures
    m.OUT=folder;m.load_prices=cached_loader
    try:
        original=json.loads((source/'report.json').read_text())
        r=m.report(labels,original['coverage'],original['screening'])
        r['version']='assistant-reviewed-schema-correction-20260914'
        r['review_manifest_sha256']=hashlib.sha256((folder/'review_manifest.json').read_bytes()).hexdigest()
        r['limitations'][0]='Retrospectively selected authors; assistant source review is not independent human validation or a blind out-of-sample test.'
        r['limitations'] += [manifest['limitations'],'Strict review covers only 136 recovered proposals; rejected and omitted posts may contain other valid views. Counts do not measure author quality or all forecasts.','Fixed 5/20/60-bar returns are descriptive price reactions, not target-hit accuracy; explicit intraday-only forecasts are excluded.']
        r['review_counts']={'candidates':len(manifest['decisions']),'accepted':len(accepted),'excluded':len(manifest['decisions'])-len(accepted)}
        scopes={'memory':['MU','SNDK'],'other_semiconductor':['NVDA','TSM','AVGO','AMD','INTC','QCOM','ARM'],'equity_index':['SPY','QQQ']}
        r['fixed_asset_scope_note']='Additional descriptive identity-based groups because model domains vary for the same ticker. Original domain groups and benchmarks retained; these are not confidence gates.'
        r['fixed_asset_scopes']=scopes
        r['fixed_asset_20d']={a:{d:m.summarize([e for e in r['events'] if e['author']==a and e['ticker'] in ts],20,True) for d,ts in scopes.items()} for a in r['authors']}
        m.save(folder/'report.json',r)
        print(json.dumps({'review_counts':r['review_counts'],'prices':r['price_failures'],'authors':{k:{'signals':v['signals'],'20d':v['domain_results']['all']['nonoverlapping']['20']} for k,v in r['authors'].items()}}))
    finally:m.OUT=old_out;m.load_prices=old_loader

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('action',choices=['freeze','calculate']);p.add_argument('--source',type=Path,required=True)
    a=p.parse_args();globals()[a.action](a.source)
