"""Exhaust daily searches for two dense months under the original cumulative $3.

Annual search missed a separately observed Jan 31 post. Monthly search is a new
coverage pass, not an uncertain paid POST retry. Previous final costs and event
counts are re-read before reserving eleven new runs of at most $0.16 each.
"""
import datetime as dt
import json
from pathlib import Path
import iiiinvest_capture_20261110 as m
from iiiinvest_search_probe2 import keep_log

m.OUT=Path('outputs/iiiinvest_20261110_daily4')
PREVIOUS=['KMm0sTPlFZxus0XJr', 'rSuDqYndVjd1xa0Jr', 'LSaHGMb8ax6fq6E6d', '4oQosKamAvVaLqZtm', 'KqwDxIK01gKNY5yVC', 'lA5TAy2AiFcjgzsc7', 'S5XI9IDnU16ltrImL', 'J40PfGZ4DUvbveQ2L', '0Szi9bOmsRXgeop8Y', '7DS96MXJ7H20yrqfY', 'tyKR0erIAQWoh68cj', 'tg0ouljsn25TQNDOO']
RUN_CAP=0.16

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
    for start,end in [('2022-11-07','2022-12-01'),('2026-03-01','2026-04-01')]:
        day=dt.date.fromisoformat(start);stop=dt.date.fromisoformat(end)
        while day<stop:
            next_day=day+dt.timedelta(days=1)
            months.append(f'from:iiiinvest since:{day.isoformat()} until:{next_day.isoformat()}')
            day=next_day
    groups=[months[i:i+5] for i in range(0,len(months),5)]
    assert len(months)==55 and len(groups)==11
    assert prior_upper+len(groups)*RUN_CAP<=3.0
    m.save('cumulative_budget.json',{'hard_budget_usd':3.0,'prior_runs':previous,'extra_prior_reservation_usd':0.084,
        'new_run_caps_usd':[RUN_CAP]*len(groups),'cumulative_reserved_upper_usd':prior_upper+len(groups)*RUN_CAP,'paid_POST_retries':0})
    actor=m.api('/acts/'+m.ACTOR)['data'];cutoff=dt.datetime.now(dt.timezone.utc).isoformat()
    pricing=max((p for p in actor['pricingInfos'] if m.iso(p['startedAt'])<=m.iso(cutoff)),key=lambda p:m.iso(p['startedAt']))
    events=pricing.get('pricingPerEvent',{}).get('actorChargeEvents',{})
    assert pricing['pricingModel']=='PAY_PER_EVENT' and set(events)=={'apify-default-dataset-item'}
    rates=[float(v['tieredEventPriceUsd']) for v in events['apify-default-dataset-item']['eventTieredPricingUsd'].values()]
    assert rates and max(rates)<=m.MAX_RATE
    m.save('pricing.json',pricing);m.save('daily_queries.json',months)
    build=actor['taggedBuilds']['latest']['buildNumber'];runs=[]
    for index,queries in enumerate(groups,1):
        label=f'days_{index:02}'
        r=m.capture(label,queries,397,RUN_CAP,build,extra={'disableMaximization':False,'sort':'Latest'})
        runs.append(r);keep_log(label,r['run']['id']);m.publish_receipt(runs,cutoff)
        assert r['run']['status']=='SUCCEEDED','Failed run: no paid retry'
    all_ids={str(p['id']) for r in runs for p in r['items'] if isinstance(p,dict) and p.get('id') and m.author(p)==m.HANDLE}
    m.save('coverage_checks.json',{'dense_months':['2022-11','2026-03'],
      'daily_queries':55,'actor_runs':len(runs),'all_runs_succeeded':all(r['run']['status']=='SUCCEEDED' for r in runs),
      'any_run_output_cap_reached':any(r['cap_reached'] for r in runs),
      'coverage_note':'Daily queries subdivide the two months whose month-level results cluster near the observed per-query 200 limit; all earlier captures remain preserved',
      'full_history_verified':False})

if __name__=='__main__':main()
