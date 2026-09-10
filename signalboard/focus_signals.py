"""First security calls in an author's demonstrated field. No network or model calls.

Evidence strength is a review priority, never a calibrated probability of profit.
Only outcomes that had finished before the candidate post inform its assessment.
"""
from __future__ import annotations

from collections import Counter, defaultdict
from datetime import datetime, timedelta, timezone
import gzip
import hashlib
import json
from pathlib import Path
import re
import statistics

ROOT = Path(__file__).resolve().parents[1]
UTC = timezone.utc
DOMAINS = {
    'memory': {'label': '存储', 'tickers': set('MU SNDK WDC STX DRAM 000660.KS 005930.KS 285A.T'.split())},
    'optics': {'label': '光通信链', 'tickers': set('AAOI LITE COHR AXTI POET AEHR AEVA TSEM AOSL GFS POWI SMTC FN MRVL CRDO'.split())},
    'semis': {'label': '半导体', 'tickers': set('MU SNDK WDC STX NVDA AMD AVGO INTC TSM ASML AMAT LRCX KLAC MRVL QCOM SOXX SMH CRDO ALAB ARM TXN ADI NXPI ON MPWR STM UMC GFS TSEM AMKR TER MCHP SWKS QRVO LSCC POWI AOSL SMTC'.split())},
}
# Chosen horizons and fields are disclosed, not optimized anew for each alert.
AUTHORS = {
    'tw_jukan05': ('Jukan', [('memory', 60), ('semis', 60)]),
    'tw_aleabitoreddit': ('Serenity', [('optics', 120), ('memory', 60)]),
    'tw_FeroceResearch': ('Feroce', [('memory', 60)]),
    'tw_TradexWhisperer': ('Tradex', [('memory', 60)]),
    'tw_zephyr_z9': ('Zephyr', [('semis', 60)]),
    'tw_austinsemis': ('Austin', [('semis', 20)]),
    'tw_DGretta_Author': ('DGretta', [('memory', 60)]),
    'tw_gsmferrari': ('gsmferrari', []),
}
ALIASES = {'MICRON': 'MU', 'SANDISK': 'SNDK', 'INTEL': 'INTC', 'NVIDIA': 'NVDA',
           'CREDO': 'CRDO', 'HYNIX': '000660.KS', 'SK HYNIX': '000660.KS',
           'SAMSUNG': '005930.KS', 'KIOXIA': '285A.T', 'BRKB': 'BRK-B', 'BRK.B': 'BRK-B'}
AMBIGUOUS = {'SKHY', 'SIVE', 'SIVEF', 'TI', 'AI', 'BTC', 'ETH', 'SOL', 'WTI', 'GOLD', 'SILVER', 'DRO'}
BUY = re.compile(r'\b(?:buy(?:ing)?|bought|long|bullish|undervalued|accumulat\w*|price target|stock pick)\b|买入|做多|看多|低估|建仓|加仓|\b(?:acheteur|achat|haussier)\b', re.I)
CONDITIONAL = re.compile(r'\b(?:if|unless|would|waiting|wait for|should i)\b|如果|等待|\b(?:si|attendrai)\b', re.I)
NON_STOCK = re.compile(r'buy (?:what (?:you|u) need|electronics|devices|a token generator)|buy one at|gift from|consumer SSD|购买.*(?:电脑|硬盘)', re.I)
AMBIGUOUS_TONE = re.compile(r'sold (?:the fuck )?out|go ahead.*short|guide on how to.*short|\b(?:shorting|bearish|overvalued)\b|做空|看空', re.I)
CHECKS = ['确认原帖确实针对该证券，核实引用、条件和反讽',
          '判断生意和现金流是否在能力圈内，核实关键事实与反证',
          '比较当前价格与保守内在价值，检查安全边际及是否已经涨价反映',
          '确定适合的期限、仓位与基于事实的退出条件']


def stamp(value):
    dt = datetime.fromisoformat(str(value).replace('Z', '+00:00'))
    return dt.replace(tzinfo=UTC) if dt.tzinfo is None else dt.astimezone(UTC)


def ticker(value):
    value = str(value).strip().upper().lstrip('$')
    return ALIASES.get(value, value)


def security_key(value):
    """Issuer novelty is separate from trading-listing/price identity."""
    value = ticker(value)
    return {'SKHY': 'SK_HYNIX', '000660.KS': 'SK_HYNIX', 'SIVE': 'SIVERS',
            'SIVEF': 'SIVERS', 'SIVE.ST': 'SIVERS'}.get(value, value)


def fingerprint(event):
    return (event['source_id'], str(event['post_id']), ticker(event['ticker']),
            hashlib.sha256(event.get('raw_text', '').encode()).hexdigest())


def bootstrap(path=None):
    path = Path(path or ROOT/'data/focus_evidence.json.gz')
    if not path.exists():
        return {'events': [], 'prices_as_of': None, 'reviewed_at': None, 'version': 'missing'}
    with gzip.open(path, 'rt') as f:
        return json.load(f)


def normalize(events, evidence):
    decisions = {(e['source_id'], str(e['post_id']), ticker(e['ticker']), e['raw_hash']): e
                 for e in evidence['events']}
    rows = []
    for original in events:
        e = dict(original, ticker=ticker(original['ticker']))
        decision = decisions.get(fingerprint(e))
        if decision:
            e['direction'] = decision['direction']
            e['eligible'] = bool(decision['strict_eligible'])
            e['exclusion'] = decision['strict_exclusion']
            e['identity_exclusion'] = decision['identity_exclusion']
        else:
            # Unreviewed first calls stay visible; they cannot become high-priority
            # just because a post-wide extraction contains "buy".
            e['eligible'] = True
            e['exclusion'] = None
            e['identity_exclusion'] = 'ambiguous_identity' if e['ticker'] in AMBIGUOUS else None
        text = e.get('raw_text', '')
        if NON_STOCK.search(text):
            e['eligible'] = False
            e['exclusion'] = 'non_stock_object'
        e['explicit_long'] = bool(BUY.search(text)) and not any(
            pattern.search(text) for pattern in (CONDITIONAL, NON_STOCK, AMBIGUOUS_TONE))
        stock_object = re.search(r'\b(?:shares?|stocks?|position|portfolio|undervalued|price target)\b|股票|股价|仓位', text, re.I)
        direct_security = re.search(r'\b(?:buy(?:ing)?|bought|bullish|long)\s+(?:on\s+|more\s+)?\$?'+re.escape(e['ticker'])+r'\b', text, re.I)
        e['explicit_long'] = e['explicit_long'] and bool(stock_object or direct_security)
        e['semantic_review'] = 'audit_screened' if decision else 'new_extraction'
        rows.append(e)
    return sorted(rows, key=lambda e:(stamp(e['published_at']), str(e['post_id']), e['ticker']))


def profile(evidence, source, domain, horizon, before, exclude_ticker=None):
    """One first long call per ticker; never include the candidate or future exits."""
    first = {}
    for e in sorted(evidence, key=lambda e:stamp(e['published_at'])):
        t = ticker(e['ticker'])
        if (e['source_id'] != source or e['direction'] != 'long' or not e['strict_eligible']
                or e.get('identity_exclusion') or e.get('group') != 'US_equity'
                or t not in DOMAINS[domain]['tickers'] or t == exclude_ticker):
            continue
        # Fix first per-security observation before testing maturity. Never
        # substitute a later winner when its genuine first call lacks a price.
        first.setdefault(t, e)
    samples = []
    for t, e in first.items():
        result = e.get('results', {}).get(str(horizon))
        if not result or stamp(e['published_at']) >= before:
            continue
        # Exit-day close must be over; date-only storage uses the next UTC day.
        if stamp(result['exit_date']) + timedelta(days=1) > before:
            continue
        excess = result.get('excess', {}).get('SOXX')
        if excess is None:
            continue
        samples.append({'ticker': t, 'post_id': str(e['post_id']), 'published_at': e['published_at'],
                        'exit_date': result['exit_date'], 'return': result['direction_return'], 'excess': excess})
    n = len(samples)
    wins = sum(e['return'] > 0 for e in samples)
    beats = sum(e['excess'] > 0 for e in samples)
    posts = len({e['post_id'] for e in samples})
    quarters = len({(stamp(e['published_at']).year, (stamp(e['published_at']).month-1)//3) for e in samples})
    median = statistics.median(e['excess'] for e in samples) if n else None
    tier = 'insufficient'
    if n >= 3 and posts >= 3 and quarters >= 2 and wins/n >= .6 and beats/n >= .6 and median > 0:
        tier = 'supported'
    if n >= 5 and posts >= 4 and quarters >= 2 and wins/n >= .6 and beats/n >= .6 and median > 0:
        tier = 'strong'
    return {'source_id': source, 'domain': domain, 'domain_label': DOMAINS[domain]['label'],
            'horizon': horizon, 'n': n, 'posts': posts, 'quarters': quarters, 'wins': wins,
            'hit_rate': wins/n if n else None, 'benchmark_win_rate': beats/n if n else None,
            'median_excess': median, 'benchmark': 'SOXX', 'tier': tier, 'samples': samples,
            'evidence_before': before.isoformat(), 'up_probability': None}


def assess(events, evidence, coverage, now=None, recent_days=7, profile_as_of=None):
    now = now or datetime.now(UTC)
    normalized = normalize(events, evidence)
    cutoff = now - timedelta(days=recent_days)
    evidence_stale = (not evidence.get('prices_as_of') or
                      (now.date()-stamp(evidence['prices_as_of']).date()).days > 30)
    first_seen, latest, source_latest = {}, {}, {}
    for e in normalized:
        if stamp(e['published_at']) > now or (e.get('captured_at') and stamp(e['captured_at']) > now):
            continue
        source_latest[e['source_id']] = e['published_at']
        if not e['eligible']:
            continue
        key = e['source_id'], security_key(e['ticker'])
        first_seen.setdefault(key, e)  # either direction: short->long is not a new security
        latest[key] = e
    alerts = []
    for (source, issuer), e in first_seen.items():
        if source not in AUTHORS or e['direction'] != 'long' or stamp(e['published_at']) < cutoff:
            continue
        author, scopes = AUTHORS[source]
        security = e['ticker']
        matching = [(d, n) for d, n in scopes if security in DOMAINS[d]['tickers']]
        # Domain choice is fixed in policy order, not whichever backtest looks best.
        chosen = matching[0] if matching else None
        p = None
        for domain, horizon in matching:
            evidence_before = min(stamp(e['published_at']), profile_as_of) if profile_as_of else stamp(e['published_at'])
            p = profile(evidence['events'], source, domain, horizon, evidence_before, security)
            if p['n'] >= 3: break
        issues = []
        if not chosen: issues.append('未匹配已验证领域，需确认行业归属或继续积累历史证据')
        if not e['explicit_long']: issues.append('股价方向、条件或语气需人工确认')
        if e.get('identity_exclusion'): issues.append('证券身份或交易市场未确认')
        if evidence_stale: issues.append('历史表现基准超过 30 天未更新或不可用')
        cov = coverage.get(source, {})
        if (now-stamp(cov.get('raw_end') or source_latest[source])).total_seconds() > 72*3600: issues.append('该作者最近数据超过 72 小时未更新')
        history_ready = cov.get('review_complete') and cov.get('raw_posts', 0) >= 100 and cov.get('history_days', 0) >= 180
        if not history_ready: issues.append('作者已存历史不足或仍有喊单审核欠账')
        if latest[(source, issuer)]['direction'] != 'long': issues.append('作者随后已出现反向观点')
        captured = e.get('captured_at')
        backfill = bool(captured and stamp(captured)-stamp(e['published_at']) > timedelta(days=2))
        if backfill: issues.append('较晚补入的历史记录，不作为实时新喊单')
        priority = 'review'
        if p and p['tier'] in ('supported', 'strong') and not issues:
            priority = 'priority' if p['tier'] == 'strong' else 'field_watch'
        if p and p['tier'] == 'insufficient': issues.append('跨标的历史样本或超额表现尚未达到门槛')
        key = f"first-security:{source}:{issuer}:{e['post_id']}"
        alerts.append({'id': hashlib.sha256(key.encode()).hexdigest()[:20], 'author': author,
            'source_id': source, 'ticker': security, 'post_id': str(e['post_id']),
            'published_at': e['published_at'], 'captured_at': captured, 'evaluated_at': now.isoformat(),
            'priority': priority, 'novelty': 'first_in_stored_history', 'history_complete': False,
            'history_scope': cov, 'backfill': backfill, 'raw_text': e.get('raw_text', ''),
            'raw_url': e.get('raw_url', ''), 'profile': p, 'issues': issues,
            'decision_stage': 'research_candidate', 'automatic_buy': False,
            'decision_checks': CHECKS, 'thesis': e.get('evidence_reason') or e.get('review_reason') or '',
            'semantic_review': e['semantic_review']})
    rank = {'priority': 0, 'field_watch': 1, 'review': 2}
    alerts.sort(key=lambda a:(rank[a['priority']], -stamp(a['published_at']).timestamp()))
    profiles = []
    for source, (name, scopes) in AUTHORS.items():
        for domain, horizon in scopes:
            profiles.append(dict(profile(evidence['events'], source, domain, horizon, min(now, profile_as_of) if profile_as_of else now), author=name))
    return {'version': 'trusted-first-call-v1', 'generated_at': now.isoformat(), 'recent_days': recent_days,
            'evidence_version': evidence.get('version'), 'evidence_prices_as_of': evidence.get('prices_as_of'),
            'evidence_stale': evidence_stale, 'alerts': alerts, 'profiles': profiles,
            'evidence_refresh': evidence.get('refresh', {}),
            'counts': dict(Counter(a['priority'] for a in alerts)), 'paid_calls': 0,
            'historical_replay_is_blind': False,
            'policy': {'strong': '至少 5 个标的、4 篇帖子、2 个季度；方向命中及跑赢 SOXX 比例均至少 60%，中位超额为正',
                       'supported': '至少 3 个标的、3 篇帖子、2 个季度，并满足相同表现条件',
                       'scope': '每位作者每标的仅保留最早多头观点；仅采用发帖前已经成熟的结果',
                       'meaning': '证据等级用于研究优先级，尚未校准为新标的上涨概率'}}


def build_from_database(conn, now=None):
    from scripts.dashboard.common import query_call_performance_events
    from signalboard.history_reuse import load_reviews
    from signalboard.extract.prompts_intel import PROMPT_VERSION
    from signalboard.call_attribution import candidates
    now = now or datetime.now(UTC)
    events = query_call_performance_events(conn)
    captured = {str(r[0]): r[1] for r in conn.execute('SELECT post_id,captured_at FROM raw_posts WHERE is_deleted=0')}
    events = [e for e in events if str(e['post_id']) in captured]
    for e in events: e['captured_at'] = captured.get(str(e['post_id']))
    reviews = load_reviews(conn)
    current = {str(r[0]) for r in conn.execute('SELECT DISTINCT post_id FROM extractions_intel WHERE prompt_version=?', (PROMPT_VERSION,))}
    pending = {str(p['post_id']) for p in candidates(conn)}
    for e in events:
        pid = str(e['post_id'])
        e['interpretation_current'] = (pid in reviews or pid in current) and pid not in pending
    # Unreviewed posts do not establish full semantic coverage. This gate can
    # only enable priority when the saved review pass has completed.
    coverage = {}
    for source in AUTHORS:
        rows = list(conn.execute('SELECT post_id,published_at FROM raw_posts WHERE source_id=? AND is_deleted=0', (source,)))
        times = [stamp(r[1]) for r in rows]
        coverage[source] = {'raw_posts': len(rows), 'history_start': min(times).isoformat() if times else None,
            'history_days': (max(times)-min(times)).days if times else 0,
            'raw_end': max(times).isoformat() if times else None,
            'review_complete': bool(rows) and all((str(r[0]) in reviews or str(r[0]) in current) and str(r[0]) not in pending for r in rows),
            'whole_history_verified': False}
    evidence = bootstrap()
    valid = {fingerprint(e) for e in events}
    evidence['events'] = [e for e in evidence['events'] if (e['source_id'], str(e['post_id']), ticker(e['ticker']), e['raw_hash']) in valid]
    result = assess(events, evidence, coverage, now)
    from signalboard.focus_labels import build_labels
    result['research_labels'] = build_labels(events, evidence, coverage, now)
    return result
