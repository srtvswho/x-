#!/usr/bin/env python3
"""Refresh first-call outcome evidence using bounded free daily bars, never models.

The UI build is offline. This runs in the existing daily pipeline and caches
prices across runs. Partial quote failures retain prior evidence and are exposed.
"""
from __future__ import annotations
import argparse
import bisect
from datetime import datetime, timedelta, timezone
import gzip
import hashlib
import json
import os
from pathlib import Path
import sqlite3
import sys
import urllib.parse
import urllib.request
from zoneinfo import ZoneInfo

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from signalboard.focus_signals import AUTHORS, DOMAINS, bootstrap, normalize, stamp
from scripts.dashboard.common import query_call_performance_events


def bars(payload, as_of):
    if 'meta' not in payload: return []
    zone = ZoneInfo(payload['meta']['exchangeTimezoneName'])
    quote = payload['indicators']['quote'][0]
    result = []
    for i, ts in enumerate(payload.get('timestamp', [])):
        date = datetime.fromtimestamp(ts, zone).date().isoformat()
        if date <= as_of and quote['open'][i] and quote['close'][i]:
            result.append({'ts': ts, 'date': date, 'open': quote['open'][i], 'close': quote['close'][i]})
    return result


def outcome(event, stock, benchmark, horizon):
    index = bisect.bisect_right([b['ts'] for b in stock], stamp(event['published_at']).timestamp())
    window = stock[index:index+horizon]
    if len(window) != horizon: return None
    start, end = window[0], window[-1]
    if (stamp(start['date']).date()-stamp(event['published_at']).date()).days > 5: return None
    market = [b for b in benchmark if start['date'] <= b['date'] <= end['date']]
    if [b['date'] for b in market] != [b['date'] for b in window]: return None
    value = end['close']/start['open']-1
    excess = value-(market[-1]['close']/market[0]['open']-1)
    return {'direction_return': value, 'underlying_return': value, 'exit_date': end['date'],
            'excess': {'SOXX': excess}}


def save(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix+'.tmp')
    tmp.write_bytes(gzip.compress(json.dumps(value, separators=(',', ':')).encode(), mtime=0))
    tmp.replace(path)


def refresh(database, max_requests=24, offline_prices=None, now=None, output=None, cache_path=None):
    now = now or datetime.now(timezone.utc)
    as_of = (now.date()-timedelta(days=1)).isoformat()
    evidence = bootstrap()
    cache_path = Path(cache_path or ROOT/'data/focus_price_cache.json.gz')
    cached = json.load(gzip.open(cache_path, 'rt')) if cache_path.exists() else {}
    with sqlite3.connect(f'file:{Path(database).resolve()}?mode=ro', uri=True) as conn:
        rows = normalize(query_call_performance_events(conn), evidence)
    first = {}
    for e in rows:
        if (e['source_id'] not in AUTHORS or e['direction'] != 'long' or not e['eligible']
                or e.get('identity_exclusion')): continue
        scopes = [d for d, _ in AUTHORS[e['source_id']][1] if e['ticker'] in DOMAINS[d]['tickers']]
        if not scopes: continue
        first.setdefault((e['source_id'], e['ticker']), e)
    selected = list(first.values())
    symbols = {'SOXX'} | {e['ticker'] for e in selected}
    # Oldest cache first. SOXX supplies both sector benchmark and market calendar.
    order = sorted(symbols, key=lambda t:(t != 'SOXX', cached.get(t, {}).get('as_of', ''), t))
    calls, failures, deferred = 0, [], []
    for symbol in order:
        if offline_prices:
            p = Path(offline_prices)/(symbol+'.json')
            if p.exists(): cached[symbol] = {'as_of': as_of, 'payload': json.loads(p.read_text())}
            continue
        if cached.get(symbol, {}).get('as_of') == as_of: continue
        if calls >= max_requests:
            deferred.append(symbol)
            continue
        calls += 1
        try:
            url = ('https://query1.finance.yahoo.com/v8/finance/chart/'+urllib.parse.quote(symbol, safe='')
                   +'?period1=1672531200&period2='+str(int(now.timestamp()))+'&interval=1d&events=splits%2Cdiv')
            with urllib.request.urlopen(urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'}), timeout=12) as response:
                payload = json.load(response)['chart']['result'][0]
            if not bars(payload, as_of): raise ValueError('No completed bars')
            cached[symbol] = {'as_of': as_of, 'payload': payload}
        except Exception:
            failures.append(symbol)
    market = bars(cached.get('SOXX', {}).get('payload', {}), as_of)
    existing = {(e['source_id'], e['post_id'], e['ticker']): e for e in evidence['events']}
    for e in selected:
        payload = cached.get(e['ticker'], {}).get('payload', {})
        meta = payload.get('meta', {})
        if meta.get('currency') != 'USD' or (meta.get('instrumentType') != 'EQUITY' and e['ticker'] not in {'SOXX', 'SMH', 'DRAM'}): continue
        series = bars(payload, as_of)
        key = e['source_id'], str(e['post_id']), e['ticker']
        if key not in existing or existing[key].get('raw_hash') != hashlib.sha256(e['raw_text'].encode()).hexdigest():
            # A fresh unambiguous extraction can accumulate outcomes; uncertainty
            # is retained instead of silently treating it as human adjudication.
            if not e['explicit_long']: continue
            existing[key] = {k:e[k] for k in ['source_id','post_id','ticker','direction','published_at']}
            existing[key].update(strict_eligible=True, strict_exclusion=None, identity_exclusion=None,
                group='US_equity', results={}, raw_hash=hashlib.sha256(e['raw_text'].encode()).hexdigest(),
                evidence_origin='automatic_explicit_call')
        target = existing[key]
        for horizon in {h for d,h in AUTHORS[e['source_id']][1] if e['ticker'] in DOMAINS[d]['tickers']}:
            result = outcome(e, series, market, horizon)
            if result: target['results'][str(horizon)] = result
    evidence.update(events=list(existing.values()), prices_as_of=market[-1]['date'] if market else evidence.get('prices_as_of'),
        refresh={'at':now.isoformat(), 'free_quote_requests':calls, 'failures':failures, 'deferred':deferred,
                 'paid_calls':0, 'automatic_new_evidence_is_human_reviewed':False})
    save(Path(output or ROOT/'data/focus_evidence.json.gz'), evidence)
    if not offline_prices: save(cache_path, cached)
    return evidence['refresh']


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--database', default=os.getenv('SIGNALBOARD_DB', str(ROOT/'data/signalboard_full.db')))
    parser.add_argument('--max-requests', type=int, default=24)
    parser.add_argument('--offline-prices', type=Path)
    parser.add_argument('--output', type=Path)
    args = parser.parse_args()
    if not 0 <= args.max_requests <= 24: parser.error('max requests must be 0..24')
    print(json.dumps(refresh(args.database,args.max_requests,args.offline_prices,output=args.output)))
