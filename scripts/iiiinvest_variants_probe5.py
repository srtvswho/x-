"""Check independent historical query variants under the original cumulative $3.

Annual search missed a separately observed Jan 31 post. Monthly search is a new
coverage pass, not an uncertain paid POST retry. Previous final costs and event
counts are re-read before reserving eleven new runs of at most $0.16 each.
"""
import datetime as dt
import json
from pathlib import Path
import iiiinvest_capture_20261110 as m
from iiiinvest_search_probe2 import keep_log

m.OUT=Path('outputs/iiiinvest_20261110_variants5')
PREVIOUS=['KMm0sTPlFZxus0XJr', 'rSuDqYndVjd1xa0Jr', 'LSaHGMb8ax6fq6E6d', '4oQosKamAvVaLqZtm', 'KqwDxIK01gKNY5yVC', 'lA5TAy2AiFcjgzsc7', 'S5XI9IDnU16ltrImL', 'J40PfGZ4DUvbveQ2L', '0Szi9bOmsRXgeop8Y', '7DS96MXJ7H20yrqfY', 'tyKR0erIAQWoh68cj', 'tg0ouljsn25TQNDOO', 'VGVi1F13Bfmdx0OMd', 'abMVn6abkj274BYpp', 'ybNHTqggk5mdl5iRw', 'hNfsQqEPE6Ix0bjQ6', 'Er5UQ5i64kbjrP8KA', 'rkFUFjlTWGiPedxQ2', 'gvKW4AlSZcK2iJ7vq', '0eXyeFVh6uSKH0cg8', 'bqGHM6AqnjQMsjthh', 'Qe8E44Kg06isGNO0B', 'TpTblNl1h8YXIWNsR']
RUN_CAP=0.20

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
    base='from:iiiinvest since:2022-11-07 until:2026-04-16'
    months=[base+' filter:replies',base+' -filter:replies',base+' filter:nativeretweets',base+' include:nativeretweets',
      'from:1589763597705437184 since:2022-11-07 until:2026-04-16']
    groups=[months[i:i+5] for i in range(0,len(months),5)]
    assert len(months)==5 and len(groups)==1
    assert prior_upper+len(groups)*RUN_CAP<=3.0
    m.save('cumulative_budget.json',{'hard_budget_usd':3.0,'prior_runs':previous,'extra_prior_reservation_usd':0.084,
        'new_run_caps_usd':[RUN_CAP]*len(groups),'cumulative_reserved_upper_usd':prior_upper+len(groups)*RUN_CAP,'paid_POST_retries':0})
    actor=m.api('/acts/'+m.ACTOR)['data'];cutoff=dt.datetime.now(dt.timezone.utc).isoformat()
    pricing=max((p for p in actor['pricingInfos'] if m.iso(p['startedAt'])<=m.iso(cutoff)),key=lambda p:m.iso(p['startedAt']))
    events=pricing.get('pricingPerEvent',{}).get('actorChargeEvents',{})
    assert pricing['pricingModel']=='PAY_PER_EVENT' and set(events)=={'apify-default-dataset-item'}
    rates=[float(v['tieredEventPriceUsd']) for v in events['apify-default-dataset-item']['eventTieredPricingUsd'].values()]
    assert rates and max(rates)<=m.MAX_RATE
    m.save('pricing.json',pricing);m.save('variant_queries.json',months)
    build=actor['taggedBuilds']['latest']['buildNumber'];runs=[]
    for index,queries in enumerate(groups,1):
        label=f'variants_{index:02}'
        r=m.capture(label,queries,497,RUN_CAP,build,extra={'disableMaximization':False,'sort':'Latest'})
        runs.append(r);keep_log(label,r['run']['id']);m.publish_receipt(runs,cutoff)
        assert r['run']['status']=='SUCCEEDED','Failed run: no paid retry'
    all_ids={str(p['id']) for r in runs for p in r['items'] if isinstance(p,dict) and p.get('id') and m.author(p)==m.HANDLE}
    m.save('coverage_checks.json',{'scope':'independent_reply_nonreply_nativeRT_and_numeric_author_checks',
      'variant_queries':5,'actor_runs':len(runs),'all_runs_succeeded':all(r['run']['status']=='SUCCEEDED' for r in runs),
      'any_run_output_cap_reached':any(r['cap_reached'] for r in runs),
      'coverage_note':'These are independent index checks, not a profile timeline or a substitute for completed monthly/daily capture; all versions retained',
      'full_history_verified':False})

if __name__=='__main__':main()
