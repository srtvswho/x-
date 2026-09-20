"""Source-linked author reading briefs, rebuilt offline with every publication.

Topic matching only organizes prose; it NEVER assigns a direction to a security.
Directions come from the existing reviewed per-security call history. Summaries
are extractive reading aids, not a new semantic adjudication or trading signal.
"""
from __future__ import annotations

from collections import defaultdict
from datetime import datetime, timedelta, timezone
import re

VERSION = 'author-reading-v1'
WINDOWS = {'0': 1, '0.25': 7, '1': 30, '3': 90, '6': 180, '12': 365}
TOPICS = [
    ('光通信与光子学', r'光通信|光模块|光子|激光|\bcpo\b|\binp\b|\bsivers\b|\bsive\b|\baxti\b'),
    ('存储供需与盈利', r'存储|内存|\bmemory\b|\bhbm\b|\bdram\b|\bnand\b|\bmicron\b'),
    ('AI 算力与资本开支', r'算力|资本开支|\bcapex\b|\bgpu\b|\bnvidia\b|\bnvda\b|\bneocloud\b|\biren\b|\bnbis\b'),
    ('市场走势与宏观', r'市场|宏观|美联储|利率|去杠杆|企稳|触底|双顶|标普|纳指|\bspx\b|\bsoxx\b|\bMAGS\b'),
    ('加密资产', r'加密|比特币|\bbtc\b|\bcrypto\b|\bsol\b'),
    ('芯片竞争与技术路线', r'芯片|封装|晶圆|代工|\btsm\b|\bcpu\b|\basml\b'),
    ('公司经营与投资', r'公司|投资|盈利|估值|收入|合作|机器人|软件|\bstock\b'),
]
CONDITIONAL = re.compile(r'条件性|(?:如果|一旦|若).{0,45}(?:买入|加仓|做多|做空|卖出)|触底后|企稳后|等待.{0,12}(?:再|买)|(?:buy|sell|long|short).{0,30}\b(?:if|once)\b', re.I)
RISK = re.compile(r'风险|抛压|谨慎|尚未|不确定|但|除非|条件|回调|去杠杆|企稳|触底|双顶|下跌|bearish|deleverag', re.I)


def stamp(s):
    d = datetime.fromisoformat(s.replace('Z', '+00:00'))
    return d.replace(tzinfo=timezone.utc) if d.tzinfo is None else d.astimezone(timezone.utc)


def topic(r):
    text = r.get('summary') or r.get('raw_text') or ''
    scores = [(len(re.findall(pattern, text, re.I)), -i, name) for i, (name, pattern) in enumerate(TOPICS)]
    specific = [s for s in scores[:-1] if s[0]]
    score, _, name = max(specific or scores)
    return name if score else '其他讨论'


def author_voice(r):
    return str(r.get('attribution') or '').upper() in ('', 'ORIGINAL', 'NA', 'ENDORSED', 'RELAYED+COMMENT', 'DISAGREED')


def prose(r):
    # Preserve all negation, conditions and company names from the saved reading.
    s = re.sub(r'\s+', ' ', r.get('summary') or '').strip()
    return re.sub(r'^作者', '', s).rstrip('。.;；') + '。' if s else ''


def ref(r):
    return {'post_id': str(r['post_id']), 'date': r['published_at'], 'text': prose(r),
            'url': '/posts/' + str(r['post_id'])}


def horizon(r):
    # Only explicit horizons may be compared; an unspecified horizon cannot prove a reversal.
    s = (r.get('summary') or '') + ' ' + (r.get('raw_text') or '')
    short = bool(re.search(r'短期|短线|这周|几天|short.term|near.term', s, re.I))
    long = bool(re.search(r'长期|中期|多年|long.term|mid.term|202[7-9]|203\d', s, re.I))
    return '不同期限并存' if short and long else '短期' if short else '中长期' if long else '期限未说明'


def representative(rows):
    # Choose a substantive, recent argument over a bare ticker, disclosure or recap.
    newest = max(stamp(r['published_at']) for r in rows)
    def score(r):
        text = r.get('summary') or ''
        reason = len(re.findall(r'因为|认为|反驳|指出|供给|需求|短缺|盈利|价格|资本开支|导致|估值|预期|预计|产能|风险', text))
        age = (newest-stamp(r['published_at'])).total_seconds()/86400
        newsletter = bool(re.search(r'汇总|产业动态|本周要闻|市场综述|每日要闻', text))
        thesis = bool(re.search(r'超级周期|核心|不会改变|不会打断|高确信|认为.*(?:需求|供给|盈利|短缺)|反驳', text))
        return (min(reason, 5)*2 + 4*thesis - 8*newsletter + min(len(text), 150)/50 - age/20, r['published_at'])
    return max(rows, key=score)


def make_brief(records, events, start, end, name, raw_dates):
    all_rows = [r for r in records if start <= stamp(r['published_at']) < end]
    # Collapse per-security semantic-review expansions back to a single original post.
    rows = list({str(r['post_id']): r for r in all_rows}.values())
    rows.sort(key=lambda r: stamp(r['published_at']))
    views = [r for r in rows if author_voice(r) and r.get('summary') and not r.get('is_retro') and not r.get('is_selfret') and not r.get('is_disc')]
    grouped = defaultdict(list)
    for r in views:
        grouped[topic(r)].append(r)
    topics = sorted(grouped, key=lambda t: (len(grouped[t]), max(r['published_at'] for r in grouped[t])), reverse=True)
    meaningful = [t for t in topics if t != '其他讨论']
    chosen_topics = (meaningful or topics)[:2]
    paragraphs = []
    if chosen_topics:
        main = '、'.join(chosen_topics)
        paragraphs.append({'text': f'{name} 在这段时间的已存发言主要围绕{main}。', 'sources': []})
        for t in chosen_topics:
            r = representative(grouped[t])
            first, last = grouped[t][0], grouped[t][-1]
            prefix = f'关于{t}，' if len(chosen_topics)>1 else ''
            paragraphs.append({'text': prefix + prose(r), 'sources': [ref(r)],
                               'coverage': f'{first["published_at"][:10]} 至 {last["published_at"][:10]} · {len(grouped[t])} 条相关发言'})
        used = {s['post_id'] for p in paragraphs for s in p['sources']}
        risks = [r for r in views if RISK.search(r.get('summary') or '') and str(r['post_id']) not in used]
        if risks:
            r = representative(risks)
            paragraphs.append({'text': '另外，' + prose(r), 'sources': [ref(r)]})
    else:
        paragraphs.append({'text': '这段时间尚无足够的作者观点解读；转发、持仓披露和普通动态仍保留在推文中。', 'sources': []})

    # Milestones span the full selected interval, rather than the last N posts.
    bins = defaultdict(list)
    for r in views:
        bucket = min(3, int((stamp(r['published_at'])-start).total_seconds()/max(1,(end-start).total_seconds())*4))
        bins[bucket].append(r)
    timeline = [dict(ref(representative(group)), topic=topic(representative(group))) for _, group in sorted(bins.items())]

    post_by_id = {str(r['post_id']): r for r in records}
    event_groups = defaultdict(list)
    for e in events:
        when = stamp(e['published_at'])
        if not start <= when < end:
            continue
        r = post_by_id.get(str(e['post_id']), e)
        if not author_voice(r):
            continue
        combined = (r.get('summary') or '') + ' ' + (e.get('evidence_reason') or '')
        conditional = bool(CONDITIONAL.search(combined))
        event_groups[e['ticker']].append({**ref(r), 'date': e['published_at'],
            'direction': e['direction'], 'conditional': conditional, 'horizon': horizon(r)})
    securities, changes = [], []
    for ticker, group in sorted(event_groups.items()):
        group.sort(key=lambda e: stamp(e['date']))
        # Conditional intent cannot overwrite an earlier unconditional view silently.
        latest = group[-1]
        securities.append({'ticker': ticker, **latest})
        for earlier, later in zip(group, group[1:]):
            if earlier['direction'] != later['direction'] and earlier['post_id'] != later['post_id']:
                changes.append({'ticker': ticker, 'before': earlier, 'after': later,
                    'label': '方向记录不同，需核对期限与条件'})
    securities.sort(key=lambda e: stamp(e['date']), reverse=True)
    changes.sort(key=lambda c: c['after']['date'], reverse=True)
    mentioned = defaultdict(list)
    for r in rows:
        for t in r.get('ticker', []):
            if t and t not in event_groups:
                mentioned[t].append(r)
    mentions = [{'ticker': t, **ref(max(rs, key=lambda r:stamp(r['published_at'])))} for t, rs in sorted(mentioned.items())]
    latest = ref(views[-1]) if views else None
    current_raw = [d for d in raw_dates if start <= stamp(d) < end]
    return {'paragraphs': paragraphs, 'timeline': timeline, 'changes': changes,
            'securities': securities, 'mentions': mentions, 'latest': latest,
            'post_count': len(current_raw), 'interpreted_count': len(rows), 'view_count': len(views),
            'first_post_at': min(current_raw, default=None), 'last_post_at': max(current_raw, default=None),
            'topics': chosen_topics, 'change_note': '下方按时间列出论点和条件；记录先后不自动代表改口。' if views else '证据不足，无法比较观点变化。'}


def build_author_briefs(conn, records, events, kols, as_of):
    end = stamp(as_of)
    by_author, event_author, dates = defaultdict(list), defaultdict(list), defaultdict(list)
    from common import SRC2KOL
    for r in records:
        by_author[r['kol']].append(r)
    for e in events:
        event_author[SRC2KOL.get(e['source_id'], e['source_id'])].append(e)
    for src, d in conn.execute('SELECT source_id,published_at FROM raw_posts'):
        if d:
            dates[SRC2KOL.get(src, src)].append(d)
    periods = {}
    for key, days in WINDOWS.items():
        start = end-timedelta(days=days)
        periods[key] = {'start': start.isoformat(), 'end': end.isoformat(), 'authors': {
            kol: make_brief(by_author[kol], event_author[kol], start, end, info['name'], dates[kol])
            for kol, info in kols.items()}}
    return {'version': VERSION, 'as_of': end.isoformat(), 'periods': periods}
