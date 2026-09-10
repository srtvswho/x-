#!/usr/bin/env python3
"""Verify temporal isolation and all scored 20/60/120-day US price outcomes."""
import bisect
import copy
from datetime import datetime, timedelta
import gzip
import hashlib
import json
from pathlib import Path
import sys
from zoneinfo import ZoneInfo
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from scripts.backtest_post_incremental_value import ROOT,OUT,INPUT,first_records,training,stamp

def run():
    r=json.load(gzip.open(OUT/'results.json.gz','rt'))
    before=json.load(gzip.open(OUT/'decisions_before_outcomes.json.gz','rt'))
    assert all('outcomes' not in x for x in before)
    assert hashlib.sha256(INPUT.read_bytes()).hexdigest()==r['protocol']['input_sha256']
    events=json.load(gzip.open(INPUT,'rt'));first=first_records(events)
    count=0
    for c in before:
        if not c['profile']:continue
        cutoff=stamp(c['profile']['cutoff'])
        assert training(first,c,cutoff)==c['profile']
        # Poison every not-yet-available outcome: decisions must remain identical.
        poisoned=copy.deepcopy(first)
        for e in poisoned:
            for o in e.get('results',{}).values():
                if stamp(o['exit_date'])+timedelta(days=1)>cutoff:
                    o['direction_return']=1e6;o['excess']['SOXX']=-1e6
        assert training(poisoned,c,cutoff)==c['profile']
        for s in c['profile']['samples']:
            assert s['ticker']!=c['ticker']
            assert stamp(s['exit_date'])+timedelta(days=1)<=cutoff
            assert stamp(s['published_at'])<cutoff
        assert len({s['ticker'] for s in c['profile']['samples']})==c['profile']['n']
        count+=1
    cache={}
    def prices(symbol):
        if symbol in cache:return cache[symbol]
        p=ROOT/'outputs/kol_reaudit_20260910/prices'/f'{symbol}.json'
        if not p.exists():return []
        v=json.loads(p.read_text())
        if 'error' in v:return []
        q=v['indicators']['quote'][0];tz=ZoneInfo(v['meta']['exchangeTimezoneName'])
        a=[]
        for i,ts in enumerate(v.get('timestamp',[])):
            day=datetime.fromtimestamp(ts,tz).date().isoformat()
            if day<='2026-09-09' and q['open'][i] and q['close'][i]:
                a.append({'ts':ts,'date':day,'open':q['open'][i],'close':q['close'][i]})
        cache[symbol]=a;return a
    index={e['event_index']:e for e in events}
    bench={b:{x['date']:x for x in prices(b)} for b in ['SPY','SOXX']}
    scored=0;entries=0
    for c in [x for x in r['decisions'] if x['mode']=='frozen_quarter']+r['early_rows']:
        e=index[c['event_index']]
        a=prices(e['price_symbol'])
        if not c['entry_date']:continue
        pos=bisect.bisect_right([x['ts'] for x in a],stamp(c['published_at']).timestamp())
        assert a[pos]['date']==c['entry_date']
        assert abs(a[pos]['open']-c['entry_open'])<1e-8
        entries+=1
        for h in [20,60,120]:
            o=c['outcomes'].get(str(h))
            if not o:continue
            path=a[pos:pos+h]
            assert len(path)==h and path[-1]['date']==o['exit_date']
            sessions=sorted(d for d in bench['SPY'] if c['entry_date']<=d<=o['exit_date'])
            assert sessions==[x['date'] for x in path]
            ret=path[-1]['close']/path[0]['open']-1
            assert abs(ret-o['direction_return'])<1e-10
            for b in ['SPY','SOXX']:
                bret=bench[b][o['exit_date']]['close']/bench[b][c['entry_date']]['open']-1
                assert abs(ret-bret-o['excess'][b])<1e-10
            scored+=1
    result={'status':'pass','temporal_poison_checks':count,'independent_entry_checks':entries,
            'independent_return_and_benchmark_checks':scored,
            'decision_only_file_has_no_candidate_outcomes':True,
            'protocol_sha256':hashlib.sha256((OUT/'protocol.json').read_bytes()).hexdigest(),
            'results_sha256':hashlib.sha256((OUT/'results.json.gz').read_bytes()).hexdigest()}
    (OUT/'validation.json').write_text(json.dumps(result,indent=2))
    print(json.dumps(result))
if __name__=='__main__':run()
