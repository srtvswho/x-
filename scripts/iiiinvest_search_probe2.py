"""Distinct bounded search diagnostics after a definitive zero-cost empty run.

Never retries an uncertain paid POST. Keeps the original $0.021 reservation and
reserves three $0.021 diagnostic caps before any $2.916 bulk capture.
"""
import datetime as dt
import json
import os
from pathlib import Path
import urllib.request
import iiiinvest_capture_20261110 as m

m.OUT = Path('outputs/iiiinvest_20261110_probe2')
RESERVED_PRIOR = 0.021
PROBE_CAP = 0.021
MAX_PROBES = 3
BULK_CAP = 3.0 - RESERVED_PRIOR - MAX_PROBES * PROBE_CAP

def keep_log(label, run_id):
    try:
        req=urllib.request.Request(m.API+'/actor-runs/'+run_id+'/log',headers={'Authorization':'Bearer '+os.environ['APIFY_TOKEN']})
        with urllib.request.urlopen(req,timeout=30) as response:
            value=response.read().decode('utf-8','replace')
        path=m.OUT/(label+'_actor_log.txt');path.parent.mkdir(parents=True,exist_ok=True);path.write_text(value)
    except Exception as e:
        m.save(label+'_log_fetch_error.json',{'type':type(e).__name__,'message':str(e)})

def main():
    m.save('budget.json',{'hard_total_budget_usd':3.0,'prior_run_id':'KMm0sTPlFZxus0XJr','prior_reported_cost_usd':0.0,
       'prior_reservation_retained_usd':RESERVED_PRIOR,'new_probe_reservations_usd':MAX_PROBES*PROBE_CAP,
       'bulk_reservation_usd':BULK_CAP,'paid_POST_retries':0})
    keep_log('prior_empty','KMm0sTPlFZxus0XJr')
    actor=m.api('/acts/'+m.ACTOR)['data'];cutoff=dt.datetime.now(dt.timezone.utc).isoformat()
    pricing=max((p for p in actor['pricingInfos'] if m.iso(p['startedAt'])<=m.iso(cutoff)),key=lambda p:m.iso(p['startedAt']))
    events=pricing.get('pricingPerEvent',{}).get('actorChargeEvents',{})
    assert pricing['pricingModel']=='PAY_PER_EVENT' and set(events)=={'apify-default-dataset-item'}
    rates=[float(v['tieredEventPriceUsd']) for v in events['apify-default-dataset-item']['eventTieredPricingUsd'].values()]
    assert rates and max(rates)<=m.MAX_RATE
    m.save('pricing.json',pricing);build=actor['taggedBuilds']['latest']['buildNumber']
    plans=[
      ('simple_until',['from:iiiinvest until:2026-04-15'],{'sort':'Latest','disableMaximization':False}),
      ('short_period_top',['from:iiiinvest since:2026-04-01 until:2026-04-15'],{'sort':'Top','disableMaximization':False}),
      ('native_dates',['from:iiiinvest'],{'author':'iiiinvest','start':'2022-11-07','end':'2026-04-15','sort':'Latest','disableMaximization':False}),
    ]
    runs=[];success=None
    for label,queries,extra in plans:
        result=m.capture(label,queries,50,PROBE_CAP,build,extra=extra)
        runs.append(result);keep_log(label,result['run']['id']);m.publish_receipt(runs,cutoff)
        valid=[p for p in result['items'] if isinstance(p,dict) and m.author(p)==m.HANDLE and p.get('id') and p.get('createdAt') and (p.get('text') or p.get('fullText'))]
        assert result['run']['status']=='SUCCEEDED','Failed/uncertain run: no paid retry'
        assert all(int(p['id'])<m.KNOWN_EARLIEST_ID for p in valid),'Date filter ignored; no bulk'
        if valid:
            success=label
            m.save('successful_probe.json',{'label':label,'rows':len(valid),'fields':sorted({k for p in valid for k in p}),'min_id':min(int(p['id']) for p in valid),'max_id':max(int(p['id']) for p in valid)})
            break
    if success is None:
        m.save('blocker.json',{'reason':'All three distinct historical search strategies returned zero valid author rows; do not infer absent history','bulk_started':False})
        return
    config=json.loads(m.CONFIG.read_text())
    # Date windows do not overlap the free timeline; a few probe duplicates are
    # retained/deduplicated, to avoid relying on the unsupported max_id operator.
    queries=[q.replace('until:2026-04-16','until:2026-04-15') for q in config['queries']]
    extra={'sort':'Top' if success=='short_period_top' else 'Latest','disableMaximization':False}
    limit=int((BULK_CAP-0.001)/m.MAX_RATE)
    result=m.capture('bulk_dates',queries,limit,BULK_CAP,build,extra=extra)
    runs.append(result);keep_log('bulk_dates',result['run']['id']);m.publish_receipt(runs,cutoff)
    assert result['run']['status']=='SUCCEEDED'
    assert not result['cap_reached'],'Cap reached; incomplete history'

if __name__=='__main__':main()
