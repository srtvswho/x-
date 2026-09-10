"""Three overlapping research labels, evaluated strictly at the original post time.

Historical semantic review is bound to the exact source/post/security/text.
New saved interpretations require a security-specific current long statement.
Labels are research metadata, never buy instructions or forecast probabilities.
"""
from collections import Counter
from datetime import timedelta
from functools import lru_cache
import gzip
import hashlib
import json
import re
import statistics

from signalboard.focus_signals import AUTHORS, DOMAINS, ROOT, UTC, fingerprint, security_key, stamp, ticker

LABELS = {'field_discovery':'领域内新观点','quarter_supported':'季度历史达标','rolling_supported':'发帖前历史达标'}
HISTORY = ROOT/'outputs/post_incremental_value_20260910'

@lru_cache(maxsize=1)
def frozen_adjudications():
    return json.load(gzip.open(ROOT/'outputs/kol_reaudit_20260910/scored_events.json.gz','rt'))

@lru_cache(maxsize=1)
def seed_evidence():
    reviews = json.loads((HISTORY/'semantic_review.json').read_text())
    scored = frozen_adjudications()
    by_index = {e['event_index']:e for e in scored}
    result = []
    for review in reviews:
        e = by_index[review['event_index']]
        assert hashlib.sha256(e['raw_text'].encode()).hexdigest() == review['raw_sha256']
        result.append(dict(e, semantic_confirmed=review['decision']=='confirmed_long_view',
                           semantic_reason=review['reason'], raw_hash=review['raw_sha256']))
    return result

def matched_field(e):
    return next((d for d,_ in AUTHORS.get(e['source_id'],('',[]))[1]
                 if ticker(e['ticker']) in DOMAINS[d]['tickers']),None)

def explicit_security_long(text, symbol):
    """Narrow fallback for new interpretations; uncertainty stays visible.

    Apply entry conditions and attribution locally, not to unrelated business
    conditions elsewhere in the post. Ambiguous/mixed directions require review.
    """
    t = re.escape(ticker(symbol))
    aliases = {'MU':'Micron','SNDK':'SanDisk','NVDA':'Nvidia','INTC':'Intel',
               'CRDO':'Credo','TSM':'TSMC','AVGO':'Broadcom'}
    target = r'(?:\$?\b'+t+r'\b'+ ('|\b'+re.escape(aliases[symbol])+r'\b' if symbol in aliases else '') + ')'
    if re.match(r'^\s*RT\s+@',text,re.I):return False
    for sentence in re.split(r'(?<=[.!?])\s+|\n+',text):
        if not re.search(target,sentence,re.I):continue
        if sentence.rstrip().endswith('?'):continue
        if re.search(r'^\s*[>“"]|\b(?:not|never|don.t|do not)\s+(?:buy|long|bullish|holding)|\bwill buy\b',sentence,re.I):continue
        # A shared paragraph is not sufficient attribution for a multi-stock call.
        if re.search(r'\b(?:if|unless|would|waiting|wait for|should i|could buy|might buy)\b|如果|等待',sentence,re.I):continue
        if re.search(r'\b(?:short|bearish|sell|sold|avoid|not buying|not bullish|used to|last year|last month|quote|said|says|he is|she is)\b|做空|看空|卖出|曾经',sentence,re.I):continue
        patterns = [r'\b(?:buy(?:ing)?|bought|long|bullish(?: on)?)\s+(?:more\s+)?'+target,
                    target+r'.{0,45}\b(?:undervalued|strong buy|screaming buy)\b',
                    r"\b(?:initiating|adding|taking|entered)\s+(?:a\s+)?(?:new\s+)?position\s+(?:in|on)\s+"+target,
                    r"\b(?:invested in|own shares of|holding shares of)\s+"+target,
                    r'(?:买入|看多|做多|加仓|建仓)\s*'+target]
        if any(re.search(p,sentence,re.I) for p in patterns):return True
    return False

def prepared(events, evidence, seeds=None):
    seeds = seed_evidence() if seeds is None else seeds
    seed_map = {fingerprint(e):e for e in seeds}
    frozen_map = {fingerprint(e):e for e in frozen_adjudications()}
    ev_map = {(e['source_id'],str(e['post_id']),ticker(e['ticker']),e['raw_hash']):e for e in evidence.get('events',[])}
    rows=[]
    for original in events:
        e=dict(original,ticker=ticker(original['ticker']))
        k=fingerprint(e); seed=seed_map.get(k); ev=ev_map.get(k) or frozen_map.get(k)
        e['eligible']=bool(ev.get('strict_eligible')) if ev else bool(e.get('strict_eligible',True))
        if ev:e['direction']=ev['direction']
        e['semantic_confirmed']=False;e['semantic_origin']='待核实'
        e['results']={}
        if seed:
            e['direction']=seed['direction'];e['eligible']=True
            e['semantic_confirmed']=seed['semantic_confirmed'];e['semantic_origin']='历史原帖人工复核'
            e['semantic_reason']=seed['semantic_reason'];e['results']=dict(seed.get('results',{}))
        elif e['eligible'] and e.get('interpretation_current') and e['direction']=='long':
            e['semantic_confirmed']=explicit_security_long(e.get('raw_text',''),e['ticker'])
            e['semantic_origin']='已存解读 + 明确证券表述核验' if e['semantic_confirmed'] else '证券方向或条件待核实'
        if ev:e['results'].update(ev.get('results',{}))
        market = ev or seed or {}
        e['identity_exclusion']=market.get('identity_exclusion') or e.get('identity_exclusion')
        e['us_equity']=market.get('group')=='US_equity'
        e['field']=matched_field(e)
        rows.append(e)
    return sorted(rows,key=lambda e:(stamp(e['published_at']),str(e['post_id']),e['ticker']))

def history_profile(first, candidate, cutoff):
    samples=[]
    for e in first:
        if (e['source_id']!=candidate['source_id'] or e['direction']!='long'
                or not e['semantic_confirmed'] or not e['us_equity'] or e.get('identity_exclusion')
                or e['ticker'] not in DOMAINS[candidate['field']]['tickers']
                or security_key(e['ticker'])==security_key(candidate['ticker'])
                or stamp(e['published_at'])>=cutoff):continue
        o=e['results'].get('60')
        if not o or stamp(o['exit_date'])+timedelta(days=1)>cutoff:continue
        ex=o.get('excess',{}).get('SOXX')
        if ex is None:continue
        samples.append({'ticker':e['ticker'],'post_id':str(e['post_id']),'published_at':e['published_at'],
                        'exit_date':o['exit_date'],'return':o['direction_return'],'excess':ex})
    n=len(samples);posts=len({e['post_id'] for e in samples})
    med=statistics.median(e['excess'] for e in samples) if samples else None
    beat=sum(e['excess']>0 for e in samples)/n if n else None
    enough=n>=2 and posts>=2
    passed=bool(enough and med>0 and beat>=.6)
    return {'n':n,'posts':posts,'median_excess':med,'benchmark_win_rate':beat,'passed':passed,
            'status':'达标' if passed else '样本不足' if not enough else '历史表现未达标',
            'cutoff':cutoff.isoformat(),'horizon':60,'benchmark':'SOXX','samples':samples}

def build_labels(events,evidence,coverage,now,recent_days=7,seeds=None):
    rows=prepared(events,evidence,seeds)
    first={};latest={}
    for e in rows:
        if stamp(e['published_at'])>now or (e.get('captured_at') and stamp(e['captured_at'])>now):continue
        if e['eligible']:
            key=(e['source_id'],security_key(e['ticker']))
            first.setdefault(key,e);latest[key]=e
    records=list(first.values());alerts=[]
    prices_as_of=evidence.get('prices_as_of')
    stale=not prices_as_of or (now.date()-stamp(prices_as_of).date()).days>30
    for e in records:
        if e['direction']!='long' or not e['field']:continue
        at=stamp(e['published_at']);cov=coverage.get(e['source_id'],{})
        backfill=bool(e.get('captured_at') and stamp(e['captured_at'])-at>timedelta(days=2))
        issues=[]
        if not e['semantic_confirmed']:issues.append('原帖中的证券方向或入场条件仍需核实')
        if not e['us_equity'] or e.get('identity_exclusion'):issues.append('证券身份或美股交易市场尚未核验')
        quarter=at.replace(month=3*((at.month-1)//3)+1,day=1,hour=0,minute=0,second=0,microsecond=0)
        q=history_profile(records,e,quarter);p=history_profile(records,e,at)
        tags=[]
        if not issues:
            tags.append('field_discovery')
            if q['passed']:tags.append('quarter_supported')
            if p['passed']:tags.append('rolling_supported')
        recent=at>=now-timedelta(days=recent_days)
        withdrawn=latest[(e['source_id'],security_key(e['ticker']))]['direction']!='long'
        live=bool(tags and recent and not backfill and not withdrawn)
        alert_id=hashlib.sha256(f"research-labels:{e['source_id']}:{security_key(e['ticker'])}:{e['post_id']}".encode()).hexdigest()[:20]
        alerts.append({'id':alert_id,'source_id':e['source_id'],'author':AUTHORS[e['source_id']][0],
            'ticker':e['ticker'],'post_id':str(e['post_id']),'published_at':e['published_at'],
            'raw_text':e.get('raw_text',''),'raw_url':e.get('raw_url',''),'field':e['field'],
            'field_label':DOMAINS[e['field']]['label'],'tags':tags,'quarter_profile':q,'rolling_profile':p,
            'semantic_origin':e['semantic_origin'],'issues':issues,'backfill':backfill,'recent':recent,
            'is_live':live,'withdrawn':withdrawn,'history_complete':False,'history_scope':cov,
            'evidence_stale':stale,'score_freshness_note':'证据刷新不完整，历史达标计算可能遗漏已成熟样本' if stale else '',
            'automatic_buy':False,'novelty':'first_in_stored_directional_history'})
    alerts.sort(key=lambda e:(e['published_at'],e['id']),reverse=True)
    return {'version':'three-research-labels-v2','generated_at':now.isoformat(),'recent_days':recent_days,
            'labels':LABELS,'alerts':alerts,'counts':dict(Counter(t for a in alerts if a['is_live'] for t in a['tags'])),
            'history_counts':dict(Counter(t for a in alerts for t in a['tags'])),
            'evidence_prices_as_of':prices_as_of,'evidence_stale':stale,
            'policy':'领域内首次明确看多；至少 2 个不同标的、2 篇不同帖子；60 日 SOXX 中位超额为正且跑赢比例至少 60%。两种评分均排除候选自身，只用当时已成熟结果。',
            'overlap_note':'三个标签可重叠，仍只适用于已存历史内的首次看多；重复观点不继承标签。',
            'report_url':'/reports/post-incremental-value.html','paid_calls':0}
