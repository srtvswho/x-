#!/usr/bin/env python3
"""Quarterly frozen-profile replay of the unchanged focus policy; no paid calls.

Uses the current retained corpus/semantic audit, so this is a retrospective
public-post replay, NOT a blind or actual-system-availability backtest.
"""
from __future__ import annotations
from collections import Counter, defaultdict
from datetime import datetime, timedelta, timezone
from functools import lru_cache
import bisect
import gzip
import json
from pathlib import Path
import statistics
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
import signalboard.focus_signals as engine

OUT = ROOT/'outputs/focus_backtest_20260910'
WINDOWS = [('2025-10-01', '2026-01-01'), ('2026-01-01', '2026-04-01'),
           ('2026-04-01', '2026-07-01'), ('2026-07-01', '2026-09-10')]


def summarize(rows, horizon):
    scored = [(r, r['outcomes'].get(str(horizon if horizon != 'recommended' else r['profile']['horizon'])))
              for r in rows if horizon != 'recommended' or r.get('profile')]
    scored = [(r,o) for r,o in scored if o]
    vals = [o['direction_return'] for _,o in scored]
    bypost = defaultdict(list)
    bystock = defaultdict(list)
    for r,o in scored:
        bypost[r['post_id']].append(o['direction_return'])
        bystock[r['ticker']].append(o['direction_return'])
    def med(a): return statistics.median(a) if a else None
    return {'n':len(vals),'signals':len(rows),'posts':len(bypost),'tickers':len(bystock),
        'wins':sum(v>0 for v in vals),'hit':sum(v>0 for v in vals)/len(vals) if vals else None,
        'mean':statistics.mean(vals) if vals else None,'median':med(vals),
        'median_excess':{b:med([o['excess'][b]for _,o in scored if b in o['excess']]) for b in ['SPY','SOXX']},
        'excess_hit':{b:(sum(v>0 for v in a)/len(a) if (a:=[o['excess'][b]for _,o in scored if b in o['excess']]) else None)for b in ['SPY','SOXX']},
        'adverse_20pct_count':sum(o.get('adverse_close',0)<=-.2 for _,o in scored),
        'worst_adverse_close':min([o.get('adverse_close',0)for _,o in scored],default=None),
        'post_equal_mean':statistics.mean(statistics.mean(v)for v in bypost.values()) if bypost else None,
        'ticker_equal_mean':statistics.mean(statistics.mean(v)for v in bystock.values()) if bystock else None}


def run():
    OUT.mkdir(parents=True,exist_ok=True)
    audit=ROOT/'outputs/kol_reaudit_20260910'
    scored=json.load(gzip.open(audit/'scored_events.json.gz','rt'))
    ev=engine.bootstrap(OUT/'policy_evidence.json.gz')
    rows=engine.normalize(scored,ev)
    first={}
    for e in rows:
        if e['eligible']:first.setdefault((e['source_id'],engine.security_key(e['ticker'])),e)
    first_longs=[e for e in first.values() if e['direction']=='long']
    context=json.load(gzip.open(OUT/'replay_context.json.gz','rt'))
    raw={source:[engine.stamp(pub) for pub in times]
         for source,times in context['raw_post_timestamps'].items()}
    capture_start=context['capture_start']
    for v in raw.values():v.sort()
    def coverage_at(before, live_at):
        coverage={}
        for source,times in raw.items():
            prior=times[:bisect.bisect_left(times,before)]
            latest=times[:bisect.bisect_right(times,live_at)]
            coverage[source]={'raw_posts':len(prior),'history_days':(prior[-1]-prior[0]).days if prior else 0,
                'history_start':prior[0].isoformat() if prior else None,
                'raw_end':latest[-1].isoformat() if latest else live_at.isoformat(),
                'review_complete':True,'review_assumption':'retrospective_complete_current_labels',
                'whole_history_verified':False}
        return coverage
    # Cache expensive shared profiles, without altering any threshold or gate.
    original_profile=engine.profile
    original_normalize=engine.normalize
    normalized_by_index={e['event_index']:e for e in rows}
    # Exact memoization of unchanged frozen text/decisions, not a second filter.
    engine.normalize=lambda events,evidence:[normalized_by_index[e['event_index']] for e in events]
    market_dates=context['market_dates']
    @lru_cache(maxsize=10000)
    def cached_profile(source,domain,horizon,before,exclude):
        return original_profile(ev['events'],source,domain,horizon,before,exclude)
    engine.profile=lambda evidence,source,domain,horizon,before,exclude_ticker=None:cached_profile(source,domain,horizon,before,exclude_ticker)
    results=[]
    try:
        for mode in ['frozen_quarter','rolling_at_post']:
            for start,end in WINDOWS:
                begin,finish=engine.stamp(start),engine.stamp(end)
                candidates=[e for e in first_longs if begin<=engine.stamp(e['published_at'])<finish and e['source_id'] in engine.AUTHORS]
                decisions=[]
                for e in candidates:
                    at=engine.stamp(e['published_at'])
                    before=begin if mode=='frozen_quarter' else at
                    # Date is the latest possible completed session boundary for
                    # this historical replay, used only by the freshness gate.
                    day_index=bisect.bisect_left(market_dates,at.date().isoformat())-1
                    replay_ev=dict(ev,prices_as_of=market_dates[day_index] if day_index>=0 else None)
                    prior=[dict(x,captured_at=None)for x in scored if engine.stamp(x['published_at'])<=at]
                    assessment=engine.assess(prior,replay_ev,coverage_at(before,at),now=at,recent_days=1,
                                             profile_as_of=before if mode=='frozen_quarter' else None)
                    match=[a for a in assessment['alerts'] if a['source_id']==e['source_id'] and a['post_id']==str(e['post_id']) and a['ticker']==e['ticker']]
                    if not match: continue
                    a=match[0]
                    # Outcomes are attached ONLY AFTER screening has finished.
                    a.update(outcomes=e.get('results',{}),entry_date=e.get('entry_date'),
                             entry_open=e.get('entry_open'),price_status=e.get('price_status'),group=e.get('group'),
                             test_window=start,mode=mode,training_cutoff=before.isoformat())
                    a['control_eligible']=bool(a['profile'] and not [x for x in a['issues'] if '跨标的历史样本' not in x])
                    for sample in (a.get('profile')or{}).get('samples',[]):
                        assert engine.stamp(sample['exit_date'])+timedelta(days=1)<=before
                        assert sample['ticker']!=a['ticker']
                    decisions.append(a)
                groups={
                    'priority':[a for a in decisions if a['priority']=='priority'],
                    'field_watch':[a for a in decisions if a['priority']=='field_watch'],
                    'actionable_combined':[a for a in decisions if a['priority'] in ['priority','field_watch']],
                    'same_field_control':[a for a in decisions if a['control_eligible']],
                    'same_field_unselected':[a for a in decisions if a['control_eligible'] and a['priority']=='review'],
                    'all_first_longs':[a for a in decisions if a['group']=='US_equity'],
                }
                results.append({'mode':mode,'start':start,'end_exclusive':end,'first_long_candidates':len(candidates),
                    'decisions':decisions,'priority_counts':dict(Counter(a['priority']for a in decisions)),
                    'rejection_reasons':dict(Counter(issue for a in decisions for issue in a['issues'])),
                    'groups':{key:{str(h):summarize(items,h)for h in [20,60,120,'recommended']}for key,items in groups.items()}})
                print(mode,start,'candidates',len(candidates),'counts',results[-1]['priority_counts'],flush=True)
    finally:
        engine.profile=original_profile
        engine.normalize=original_normalize
    report={'version':'focus-walk-forward-20260910','as_of':'2026-09-09','policy_commit':'20c1849',
        'windows':results,'thresholds_changed_after_results':False,'paid_calls':0,
        'actual_capture_start':capture_start,'blind_out_of_sample':False,
        'limitations':['Author selection, domains, horizons and semantic labels were defined using the current corpus.',
            'Historical public timestamps are replayed assuming prompt interpretation and historical ingestion; actual system snapshots are unavailable.',
            'No future outcome enters training; this does not remove retrospective author/domain selection bias.',
            'Only stored posts are available; missing/deleted history and unavailable prices can bias the sample.',
            'Overlapping author/stock and holding windows are correlated; reported averages are not account P&L.']}
    (OUT/'backtest.json').write_text(json.dumps(report,ensure_ascii=False,indent=2))
    (OUT/'backtest.json.gz').write_bytes(gzip.compress(json.dumps(report,ensure_ascii=False,separators=(',',':')).encode(),mtime=0))
    return report


if __name__=='__main__':run()
