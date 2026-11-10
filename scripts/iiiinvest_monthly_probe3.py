"""Exhaust disjoint calendar-month searches under the original cumulative $3.

Annual search missed a separately observed Jan 31 post. Monthly search is a new
coverage pass, not an uncertain paid POST retry. Previous final costs and event
counts are re-read before reserving nine new runs of at most $0.28 each.
"""
import datetime as dt
import json
from pathlib import Path
import iiiinvest_capture_20261110 as m
from iiiinvest_search_probe2 import keep_log

m.OUT=Path('outputs/iiiinvest_20261110_monthly3')
PREVIOUS=['KMm0sTPlFZxus0XJr','LSaHGMb8ax6fq6E6d','rSuDqYndVjd1xa0Jr']
RUN_CAP=0.28

def main():
    previous=[]
    prior_upper=0.0
    for rid in PREVIOUS:
        r=m.api('/actor-runs/'+rid)['data']
        assert r['status'] in m.TERMINAL
        charged=int(r.get('chargedEventCounts',{}).get('apify-default-dataset-item',0))
        upper=max(float(r.get('usageTotalUsd') or 0),charged*m.MAX_RATE)
        previous.append({'run_id':rid,'status':r['status'],'usage_usd':r.get('usageTotalUsd'),'charged_events':charged,'conservative_charge_upper_usd':upper})
        prior_upper+=upper
    # Keep a further 8.4 cents reserved for all earlier smoke/probe caps even
    # though the API already shows them terminal and near/at zero cost.
    prior_upper+=0.084
    months=[]
    year,month=2022,11
    while (year,month)<=(2026,4):
        first=f'{year:04}-{month:02}-01'
        if (year,month)==(2022,11):first='2022-11-07'
        next_year,next_month=(year+1,1) if month==12 else (year,month+1)
        end=f'{next_year:04}-{next_month:02}-01'
        if (year,month)==(2026,4):end='2026-04-16'
        months.append(f'from:iiiinvest since:{first} until:{end}')
        year,month=next_year,next_month
    groups=[months[i:i+5] for i in range(0,len(months),5)]
    assert len(months)==42 and len(groups)==9
    assert prior_upper+len(groups)*RUN_CAP<=3.0
    m.save('cumulative_budget.json',{'hard_budget_usd':3.0,'prior_runs':previous,'extra_prior_reservation_usd':0.084,
        'new_run_caps_usd':[RUN_CAP]*len(groups),'cumulative_reserved_upper_usd':prior_upper+len(groups)*RUN_CAP,'paid_POST_retries':0})
    actor=m.api('/acts/'+m.ACTOR)['data'];cutoff=dt.datetime.now(dt.timezone.utc).isoformat()
    pricing=max((p for p in actor['pricingInfos'] if m.iso(p['startedAt'])<=m.iso(cutoff)),key=lambda p:m.iso(p['startedAt']))
    events=pricing.get('pricingPerEvent',{}).get('actorChargeEvents',{})
    assert pricing['pricingModel']=='PAY_PER_EVENT' and set(events)=={'apify-default-dataset-item'}
    rates=[float(v['tieredEventPriceUsd']) for v in events['apify-default-dataset-item']['eventTieredPricingUsd'].values()]
    assert rates and max(rates)<=m.MAX_RATE
    m.save('pricing.json',pricing);m.save('monthly_queries.json',months)
    build=actor['taggedBuilds']['latest']['buildNumber'];runs=[]
    for index,queries in enumerate(groups,1):
        label=f'months_{index:02}'
        r=m.capture(label,queries,697,RUN_CAP,build,extra={'disableMaximization':False,'sort':'Latest'})
        runs.append(r);keep_log(label,r['run']['id']);m.publish_receipt(runs,cutoff)
        assert r['run']['status']=='SUCCEEDED','Failed run: no paid retry'
    all_ids={str(p['id']) for r in runs for p in r['items'] if isinstance(p,dict) and p.get('id') and m.author(p)==m.HANDLE}
    m.save('coverage_checks.json',{'known_jan31_post_id':'2017456331486318871',
      'known_jan31_found':'2017456331486318871' in all_ids,
      'monthly_queries':42,'actor_runs':len(runs),'all_runs_succeeded':all(r['run']['status']=='SUCCEEDED' for r in runs),
      'any_run_output_cap_reached':any(r['cap_reached'] for r in runs),
      'boundary_overlap_note':'Apr 15 full UTC day deliberately overlaps at most one free-timeline day to prevent a gap before 07:35:20; deduplicate by post ID',
      'full_history_verified':False})

if __name__=='__main__':main()
