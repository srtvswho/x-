#!/usr/bin/env python3
"""Frozen, offline diagnostic replay. Does not modify the live signal policy."""
from __future__ import annotations
import collections
from datetime import timedelta
import csv
import gzip
import hashlib
import html
import json
from pathlib import Path
import statistics as st
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from signalboard.focus_signals import AUTHORS, DOMAINS, security_key, stamp, ticker

OUT = ROOT / 'outputs/post_incremental_value_20260910'
INPUT = ROOT / 'outputs/kol_reaudit_20260910/scored_events.json.gz'
WINDOWS = [('2025-10-01', '2026-01-01'), ('2026-01-01', '2026-04-01'),
           ('2026-04-01', '2026-07-01'), ('2026-07-01', '2026-09-10')]
# Entire first-call texts in the preset author fields were examined without
# printing their outcomes. These are event identities, never performance picks.
REVIEWED = {19,24,27,30,51,69,75,203,245,250,276,297,482,631,632,777,810,
            1109,1110,1503,1522,1524,1573,1616,1749,1890,1972,1984,2000,
            2178,2179,2326,2622,2864,3062,3289,3328,3329,4013,4027,4031,
            4419,4456,4541,5423,5424,5467,5529}
QUARANTINE = {
    2326: 'GFS: entry is explicitly conditional on a price drop; no trigger model.',
    4419: 'STX: earnings relay and disagreement with memory bears; no clear security-specific stock recommendation.',
    5467: 'MU: mocks a third-party bear; disagreement alone is not an explicit own long recommendation.',
    5529: 'AEVA: possible operating benefit from competitor restrictions; no explicit stock view.',
}

def dump(path, data):
    payload = json.dumps(data, ensure_ascii=False, indent=2, allow_nan=False).encode()
    path.write_bytes(gzip.compress(payload, mtime=0) if path.suffix == '.gz' else payload)

def first_records(events):
    first = {}
    for e in sorted(events, key=lambda e: (stamp(e['published_at']), str(e['post_id']), ticker(e['ticker']))):
        if e['strict_eligible']:
            first.setdefault((e['source_id'], security_key(e['ticker'])), e)
    return list(first.values())

def field(e):
    return next((d for d, _ in AUTHORS[e['source_id']][1]
                 if ticker(e['ticker']) in DOMAINS[d]['tickers']), None)

def confirmed(e):
    return e['event_index'] in REVIEWED and e['event_index'] not in QUARANTINE

def us(e):
    return e.get('group') == 'US_equity' and not e.get('identity_exclusion')

def freeze():
    OUT.mkdir(parents=True, exist_ok=True)
    events = json.load(gzip.open(INPUT, 'rt'))
    first = first_records(events)
    observed = {e['event_index'] for e in first if e['direction'] == 'long' and field(e)}
    assert observed == REVIEWED, (observed - REVIEWED, REVIEWED - observed)
    protocol = {
        'version': 'incremental-value-diagnostic-v2', 'as_of': '2026-09-09',
        'input_sha256': hashlib.sha256(INPUT.read_bytes()).hexdigest(),
        'frozen_at_utc': __import__('datetime').datetime.now(__import__('datetime').timezone.utc).isoformat(),
        'primary_horizon_sessions': 60, 'sensitivity_horizons': [20,120],
        'main_windows': WINDOWS, 'main_mode': 'frozen_quarter',
        'sensitivity_mode': 'rolling_at_post',
        'baseline': 'all first eligible own-long records in stored history, all eight authors; US equity and designated equity ETFs only in return tables',
        'first_means': 'first audited directional call, either direction; earlier short excludes later long from novelty',
        'semantic_rule': 'reuse frozen event-level adjudication; remove secondary whole-post keyword veto; manually reviewed preset-field first calls; quarantine four ambiguous texts',
        'missing_first_price': 'retain first identity and report missing; never replace with a later priced/winning call',
        'training': 'first directional-long records from same author and fixed first matching field; candidate issuer excluded; only fully matured 60-session outcomes before cutoff',
        'research_positive': 'at least 2 distinct tickers and 2 distinct posts; median SOXX excess > 0 and SOXX beat fraction >= 0.60; no calibrated win probability',
        'research_other': 'enough samples but historical result condition not met',
        'unknown': 'fewer than 2 tickers or 2 posts; remains in discovery baseline',
        'conservative_sensitivity': 'at least 3 tickers, 3 posts, 2 starting quarters, positive-return fraction >= .60, SOXX beat fraction >= .60, median excess > 0 (old supported tier)',
        'controlled_ablation': 'old broad keyword gate + old evidence; corrected semantics + old evidence; corrected semantics + research-positive grouping',
        'reporting': 'event median, beat fraction, post-equal and ticker-equal means; all groups and every quarterly window; matched field-window controls; no portfolio P&L',
        'peer_control': 'same-field currently defined basket, excluding candidate; only prices available on exact entry/exit dates; ex-post static universe, diagnostic only',
        'lookback': 'pre-October-2025 first calls reported separately as descriptive discovery history, not validation of October rule',
        'price_policy': 'frozen Yahoo OHLC, first regular open strictly after post, nth session close, no dividends/costs; incomplete windows excluded and counted',
        'not_blind': True,
        'limitations': ['v2 is a diagnostic revision after seeing v1 failures, not preregistered out-of-sample evidence',
                       'authors, field memberships and saved semantic labels were assembled retrospectively',
                       'correlated stocks, posts and overlapping horizons are not independent trades',
                       'global baseline labels have not all been manually certified; narrow field first calls were read',
                       'quarantined first calls keep novelty uncertain; later calls are not silently substituted',
                       'same-field mapping is inherited and broad; SOXX is an imperfect benchmark for optical/power subindustries'],
        'paid_calls': 0,
    }
    if (OUT/'protocol.json').exists():
        raise RuntimeError('Protocol already frozen. Do not overwrite after inspecting results.')
    dump(OUT/'protocol.json', protocol)
    reviewed = []
    for e in first:
        if e['event_index'] in REVIEWED:
            reviewed.append({k:e[k] for k in ['event_index','source_id','post_id','ticker','published_at','raw_text','raw_url']}
                            | {'raw_sha256':hashlib.sha256(e['raw_text'].encode()).hexdigest(),
                               'decision':'quarantine' if e['event_index'] in QUARANTINE else 'confirmed_long_view',
                               'reason':QUARANTINE.get(e['event_index'], 'Own current constructive stock view, portfolio recommendation, valuation view or explicit long disclosure; operating conditions do not negate current stance.')})
    dump(OUT/'semantic_review.json', reviewed)
    print('Frozen protocol and text-only review:', len(reviewed), 'records')

def training(first, candidate, cutoff):
    samples = []
    for e in first:
        if (e['source_id'] != candidate['source_id'] or e['direction'] != 'long'
                or not us(e) or not confirmed(e)
                or ticker(e['ticker']) not in DOMAINS[candidate['field']]['tickers']
                or security_key(e['ticker']) == security_key(candidate['ticker'])
                or stamp(e['published_at']) >= cutoff):
            continue
        o = e.get('results', {}).get('60')
        if not o or stamp(o['exit_date']) + timedelta(days=1) > cutoff:
            continue
        ex = o.get('excess', {}).get('SOXX')
        if ex is None: continue
        samples.append({'event_index':e['event_index'],'ticker':e['ticker'],'post_id':str(e['post_id']),
                        'published_at':e['published_at'],'exit_date':o['exit_date'],
                        'return':o['direction_return'],'excess':ex})
    n = len(samples)
    posts = len({x['post_id'] for x in samples})
    quarters = len({(stamp(x['published_at']).year,(stamp(x['published_at']).month-1)//3) for x in samples})
    med = st.median(x['excess'] for x in samples) if samples else None
    beat = sum(x['excess'] > 0 for x in samples)/n if n else None
    win = sum(x['return'] > 0 for x in samples)/n if n else None
    enough = n >= 2 and posts >= 2
    positive = enough and med > 0 and beat >= .6
    return {'n':n, 'posts':posts,'quarters':quarters, 'median_excess':med,'beat':beat,
            'classification':'positive' if positive else 'other' if enough else 'unknown',
            'conservative_supported':bool(n >= 3 and posts >= 3 and quarters >= 2 and med > 0 and beat >= .6 and win >= .6),
            'samples':samples,'cutoff':cutoff.isoformat()}

def summarize(rows, horizon, benchmark):
    valid = [(e,e.get('outcomes',{}).get(str(horizon))) for e in rows]
    valid = [(e,o) for e,o in valid if o and benchmark in o.get('excess',{})]
    vals = [o['direction_return'] for _,o in valid]
    excess = [o['excess'][benchmark] for _,o in valid]
    posts = collections.defaultdict(list)
    tickers = collections.defaultdict(list)
    for e,o in valid:
        posts[e['post_id']].append(o['excess'][benchmark])
        tickers[e['ticker']].append(o['excess'][benchmark])
    peer = [o['peer_excess'] for _,o in valid if o.get('peer_excess') is not None]
    return {'signals':len(rows),'n':len(valid),'missing_or_immature':len(rows)-len(valid),
            'posts':len(posts),'tickers':len(tickers),
            'return_median':st.median(vals) if vals else None,
            'excess_median':st.median(excess) if excess else None,
            'return_win':sum(v>0 for v in vals)/len(vals) if vals else None,
            'benchmark_beat':sum(v>0 for v in excess)/len(excess) if excess else None,
            'post_equal_excess_mean':st.mean(st.mean(v) for v in posts.values()) if posts else None,
            'ticker_equal_excess_mean':st.mean(st.mean(v) for v in tickers.values()) if tickers else None,
            'adverse_20pct':sum(o.get('adverse_close',0)<=-.2 for _,o in valid),
            'peer_n':len(peer),'peer_excess_median':st.median(peer) if peer else None,
            'peer_beat':sum(v>0 for v in peer)/len(peer) if peer else None}

def load_peers():
    from zoneinfo import ZoneInfo
    from datetime import datetime
    archive = OUT/'peer_prices.json.gz'
    if archive.exists():
        return json.load(gzip.open(archive,'rt'))
    prices = {}
    for t in sorted(set().union(*(d['tickers'] for d in DOMAINS.values()))):
        p = ROOT/'outputs/kol_reaudit_20260910/prices'/f'{t}.json'
        if not p.exists(): continue
        v = json.loads(p.read_text())
        if 'error' in v or v.get('meta',{}).get('currency') != 'USD': continue
        q = v['indicators']['quote'][0]
        tz = ZoneInfo(v['meta']['exchangeTimezoneName'])
        prices[t] = {datetime.fromtimestamp(ts,tz).date().isoformat():{'open':q['open'][i],'close':q['close'][i]}
                     for i,ts in enumerate(v.get('timestamp',[])) if q['open'][i] and q['close'][i]}
    dump(archive,prices)
    return prices

def run():
    protocol = json.loads((OUT/'protocol.json').read_text())
    assert protocol['input_sha256'] == hashlib.sha256(INPUT.read_bytes()).hexdigest()
    first = first_records(json.load(gzip.open(INPUT,'rt')))
    longs = [e for e in first if e['direction']=='long' and e['source_id'] in AUTHORS]
    candidates = [e for e in longs if '2025-10-01' <= e['published_at'] < '2026-09-10']
    # This stage emits decisions using only candidate identity and matured history.
    # Candidate forward outcomes are deliberately absent from its inputs.
    decisions = []
    for mode in ['frozen_quarter','rolling_at_post']:
        for start,end in WINDOWS:
            for e in candidates:
                if not (start <= e['published_at'] < end) or not us(e):continue
                c = {k:e[k] for k in ['event_index','source_id','post_id','ticker','published_at','raw_text','raw_url']}
                c.update(field=field(e),window=start,mode=mode,confirmed_field=bool(field(e) and confirmed(e)))
                if c['confirmed_field']:
                    cutoff = stamp(start) if mode=='frozen_quarter' else stamp(c['published_at'])
                    c['profile'] = training(first,c,cutoff)
                else: c['profile'] = None
                decisions.append(c)
    dump(OUT/'decisions_before_outcomes.json.gz',decisions)
    # Outcomes attach only after all decisions have been fixed and persisted.
    index = {e['event_index']:e for e in longs}
    peers = load_peers()
    def attach(c):
        e = index[c['event_index']]
        c.update(entry_date=e.get('entry_date'),entry_open=e.get('entry_open'),price_status=e.get('price_status'),
                 outcomes=json.loads(json.dumps(e.get('results',{}))))
        for o in c['outcomes'].values():
            if not c.get('field') or not c.get('entry_date'): continue
            samples = {}
            for t in sorted(DOMAINS[c['field']]['tickers']):
                if security_key(t)==security_key(c['ticker']):continue
                a,b = peers.get(t,{}).get(c['entry_date']),peers.get(t,{}).get(o['exit_date'])
                if a and b: samples[t] = b['close']/a['open']-1
            o['peer_returns'] = samples
            o['peer_excess'] = o['direction_return']-st.mean(samples.values()) if len(samples)>=2 else None
        return c
    decisions = [attach(c) for c in decisions]
    early = [attach({k:e[k] for k in ['event_index','source_id','post_id','ticker','published_at','raw_text','raw_url']}
                    | {'field':field(e),'confirmed_field':confirmed(e)})
             for e in longs if e['published_at']<'2025-10-01' and us(e) and field(e) and confirmed(e)]
    modes = {}
    for mode in ['frozen_quarter','rolling_at_post']:
        rows = [c for c in decisions if c['mode']==mode]
        fields = [c for c in rows if c['confirmed_field']]
        groups = {'all_first_us':rows,'field_discovery':fields,
                  **{f'field_{name}':[c for c in fields if c['profile']['classification']==name] for name in ['positive','other','unknown']},
                  'field_old_supported':[c for c in fields if c['profile']['conservative_supported']]}
        summaries = {g:{str(h):summarize(v,h,'SPY' if g=='all_first_us' else 'SOXX') for h in [20,60,120]} for g,v in groups.items()}
        matched = []
        for c in groups['field_positive']:
            control = [x for x in fields if x['window']==c['window'] and x['field']==c['field']
                       and x['event_index']!=c['event_index'] and x['profile']['classification']!='positive']
            co = [x['outcomes']['60']['excess']['SOXX'] for x in control if '60' in x['outcomes'] and 'SOXX' in x['outcomes']['60']['excess']]
            if '60' in c['outcomes'] and co:
                matched.append({'event_index':c['event_index'],'control_n':len(co),
                                'delta_vs_control_mean':c['outcomes']['60']['excess']['SOXX']-st.mean(co)})
        modes[mode] = {'groups':summaries,
            'windows':{start:{g:summarize([x for x in v if x['window']==start],60,'SPY' if g=='all_first_us' else 'SOXX') for g,v in groups.items()} for start,_ in WINDOWS},
            'authors':{s:{'all_first_us':summarize([c for c in rows if c['source_id']==s],60,'SPY'),
                          'field_discovery':summarize([c for c in fields if c['source_id']==s],60,'SOXX'),
                          'field_positive':summarize([c for c in groups['field_positive'] if c['source_id']==s],60,'SOXX')} for s in AUTHORS},
            'matched_field_window':matched,
            'matched_delta_median':st.median(x['delta_vs_control_mean'] for x in matched) if matched else None}
    report = {'protocol':protocol,'counts':{'all_first_long_candidates':len(candidates),
              'us_first_longs':sum(us(e) for e in candidates),
              'non_us_or_unresolved':sum(not us(e) for e in candidates),
              'preset_field_candidates':sum(bool(field(e)) for e in candidates),
              'preset_field_non_us':sum(bool(field(e)) and not us(e) for e in candidates),
              'preset_field_quarantined_us':sum(bool(field(e)) and us(e) and not confirmed(e) for e in candidates)},
              'modes':modes,'early_descriptive':{'60':summarize(early,60,'SOXX'),'120':summarize(early,120,'SOXX')},
              'early_rows':early,'decisions':decisions}
    # Exact v1 semantic-only ablation keeps v1 horizons, profiles and all other
    # recorded gates. The 60-session v2 grouping is a separate policy revision.
    old_path = ROOT/'outputs/focus_backtest_20260910/backtest.json.gz'
    old = json.load(gzip.open(old_path,'rt'))
    confirmed_keys = {(c['source_id'],c['post_id'],c['ticker']) for c in decisions if c['confirmed_field']}
    ablation = []
    for w in old['windows']:
        recovered = []
        for a in w['decisions']:
            issues = [x for x in a['issues'] if x != '股价方向、条件或语气需人工确认']
            if ((a['source_id'],a['post_id'],a['ticker']) in confirmed_keys and not issues
                    and (a['profile'] or {}).get('tier') in ['supported','strong']):
                recovered.append({'author':a['author'],'ticker':a['ticker'],'post_id':a['post_id']})
        ablation.append({'mode':w['mode'],'window':w['start'],'v1_selected':sum(a['priority'] in ['priority','field_watch'] for a in w['decisions']),
                         'semantic_only_selected':len(recovered),'recovered':recovered})
    report['v1_semantic_only_ablation'] = ablation
    report['ablation_input_sha256'] = hashlib.sha256(old_path.read_bytes()).hexdigest()
    dump(OUT/'results.json.gz',report)
    dump(OUT/'summary.json',{k:v for k,v in report.items() if k not in ['early_rows','decisions']})
    with (OUT/'decisions.csv').open('w',newline='') as f:
        cols=['mode','window','author','ticker','published_at','field','classification','historical_tickers','historical_posts',
              'return_20','return_60','return_120','excess_soxx_60','raw_url']
        w=csv.DictWriter(f,fieldnames=cols);w.writeheader()
        for c in decisions:
            p=c['profile'] or {}
            w.writerow({k:c.get(k) for k in ['mode','window','ticker','published_at','field','raw_url']}
                       | {'author':AUTHORS[c['source_id']][0],'classification':p.get('classification','outside_confirmed_field'),
                          'historical_tickers':p.get('n'),'historical_posts':p.get('posts'),
                          **{f'return_{h}':c['outcomes'].get(str(h),{}).get('direction_return') for h in [20,60,120]},
                          'excess_soxx_60':c['outcomes'].get('60',{}).get('excess',{}).get('SOXX')})
    print(json.dumps({'counts':report['counts'],'frozen':modes['frozen_quarter']['groups'],
                      'rolling':modes['rolling_at_post']['groups']},ensure_ascii=False,indent=2))

if __name__ == '__main__':
    {'freeze':freeze,'run':run}[sys.argv[1]]()
