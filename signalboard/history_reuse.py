"""Reuse saved interpretations for call tracking, without pretending to rerun a prompt.

Reviews retain original payloads and versions. A changed raw post or a later
extraction invalidates a review. This is call coverage, not Claim/Theme coverage.
No network or model call is made by this module.
"""
from __future__ import annotations

from collections import Counter
from datetime import datetime, timezone
import hashlib
import gzip
import json
from pathlib import Path
import re
import sqlite3

VERSION = 'history-reuse-v1'
DDL = '''CREATE TABLE IF NOT EXISTS historical_call_reviews (
    post_id TEXT PRIMARY KEY, source_id TEXT NOT NULL, raw_hash TEXT NOT NULL,
    reviewed_at TEXT NOT NULL, review_version TEXT NOT NULL,
    origin TEXT NOT NULL, origin_version TEXT NOT NULL,
    origin_payload TEXT NOT NULL, events_json TEXT NOT NULL,
    extraction_id INTEGER, reason TEXT NOT NULL
);'''


def restore_archives(db, root, sources):
    """Restore exact owned raw posts and retain partial candidate evidence.

    Candidate reports save selected best/worst events, not full post labels.
    They are retained as evidence, never counted as fully reviewed posts.
    """
    con = sqlite3.connect(db)
    con.row_factory = sqlite3.Row
    con.execute('''CREATE TABLE IF NOT EXISTS historical_candidate_evidence (
        post_id TEXT, ticker TEXT, direction TEXT, artifact TEXT, raw_hash TEXT,
        payload TEXT, PRIMARY KEY(post_id,ticker,direction,artifact))''')
    handles = {s.removeprefix('tw_').lower(): s for s in sources}
    counts = Counter()
    conflicts = []

    def restore(item, artifact):
        src = handles.get(str(item.get('handle', '')).lower())
        if not src or not item.get('post_id') or not item.get('text'):
            return None
        pid, text = str(item['post_id']), item['text']
        pub = item['published_at']
        datetime.fromisoformat(pub.replace('Z', '+00:00'))
        existing = con.execute('SELECT * FROM raw_posts WHERE post_id=?', (pid,)).fetchone()
        if existing:
            if existing['source_id'] != src or existing['raw_text'].strip() != text.strip():
                conflicts.append({'post_id': pid, 'artifact': artifact, 'reason': 'raw_identity_or_text_mismatch'})
                return None
            return dict(existing)
        post = {'post_id': pid, 'source_id': src, 'published_at': pub, 'raw_text': text}
        con.execute('''INSERT INTO raw_posts(post_id,source_id,platform,published_at,
            captured_at,raw_text,raw_url,raw_json,content_hash) VALUES(?,?,?,?,?,?,?,?,?)''',
            (pid, src, 'twitter', pub, datetime.now(timezone.utc).isoformat(), text,
             item.get('url') or f'https://x.com/{item["handle"]}/status/{pid}',
             json.dumps({'restored_from': artifact, 'saved_post': item}, ensure_ascii=False),
             hashlib.sha256(text.encode()).hexdigest()))
        counts['restored_raw_posts'] += 1
        return post

    for path in sorted((Path(root) / 'outputs').glob('*/raw_posts.json.gz')):
        artifact = str(path.relative_to(root))
        rows = json.load(gzip.open(path, 'rt'))
        if isinstance(rows, list):
            for item in rows:
                restore(item, artifact)
    for path in sorted((Path(root) / 'outputs').glob('*validation*/validation.json')):
        artifact = str(path.relative_to(root))
        data = json.loads(path.read_text())
        for rank in data.get('ranking', []):
            for event in rank.get('best', []) + rank.get('worst', []):
                post = restore(event.get('post', {}), artifact)
                if not post or event.get('direction') not in ('long', 'short') or not event.get('ticker'):
                    continue
                con.execute('INSERT OR REPLACE INTO historical_candidate_evidence VALUES(?,?,?,?,?,?)',
                    (post['post_id'], event['ticker'], event['direction'], artifact,
                     raw_hash(post), json.dumps(event, ensure_ascii=False)))
                counts['candidate_evidence_records'] += 1
    con.commit()
    con.close()
    return {'counts': dict(counts), 'conflicts': conflicts,
            'candidate_reports_are_partial': True, 'additional_api_calls': 0}


def raw_hash(post):
    return hashlib.sha256(json.dumps([post['source_id'], post['published_at'],
        post['raw_text']], ensure_ascii=False).encode()).hexdigest()


def table_exists(con, name):
    return bool(con.execute("SELECT 1 FROM sqlite_master WHERE type='table' AND name=?", (name,)).fetchone())


def load_reviews(con):
    """Only reviews of this exact raw post and latest extraction are authoritative."""
    if not table_exists(con, 'historical_call_reviews'):
        return {}
    cursor = con.execute('''SELECT h.*, r.raw_text, r.published_at,
        r.source_id AS raw_source FROM historical_call_reviews h
        JOIN raw_posts r ON r.post_id=h.post_id''')
    names = [d[0] for d in cursor.description]
    rows = [dict(zip(names, r)) for r in cursor]
    latest = {}
    if table_exists(con, 'extractions_intel'):
        cols = {r[1] for r in con.execute('PRAGMA table_info(extractions_intel)')}
        if 'id' in cols:
            for pid, eid in con.execute('''SELECT post_id,id FROM extractions_intel
                ORDER BY julianday(extracted_at),id'''):
                latest[pid] = eid
    valid = {}
    for r in rows:
        if (r['review_version'] != VERSION or r['source_id'] != r['raw_source'] or
                raw_hash(r) != r['raw_hash'] or latest.get(r['post_id']) != r['extraction_id']):
            continue
        valid[r['post_id']] = r
    return valid


def candidate_events(con):
    """Partial saved event evidence never overrides a later full interpretation."""
    if not table_exists(con, 'historical_candidate_evidence'):
        return []
    cursor = con.execute('''SELECT h.*,r.source_id,r.published_at,r.raw_text,r.raw_url
        FROM historical_candidate_evidence h JOIN raw_posts r ON r.post_id=h.post_id
        WHERE NOT EXISTS(SELECT 1 FROM extractions_intel e WHERE e.post_id=r.post_id)''')
    names = [d[0] for d in cursor.description]
    result = []
    for row in cursor:
        r = dict(zip(names, row))
        if r['raw_hash'] != raw_hash(r):
            continue
        payload = json.loads(r['payload'])
        r.update(history_source=r['artifact'], bottleneck=None,
                 evidence_reason=payload.get('reason', ''))
        result.append(r)
    return result


def strings(value):
    if not value:
        return []
    if isinstance(value, str):
        try:
            value = json.loads(value)
        except (ValueError, TypeError):
            value = [value]
    return value if isinstance(value, list) else [value] if isinstance(value, str) else []


def intel_decision(row, post):
    """Reuse unambiguous v2.0.1 results; quarantine known attribution hazards."""
    try:
        payload = json.loads(row['raw_response'])
    except (ValueError, TypeError):
        return None, 'invalid_json'
    required = ('direction', 'ticker', 'attribution', 'is_retrospective',
                'is_disclosure', 'is_self_reported_returns', 'summary_100')
    if not isinstance(payload, dict) or any(k not in payload for k in ('direction', 'ticker', 'attribution', 'summary_100')):
        return None, 'missing_semantic_fields'
    if re.search(r'无法获取|无法访问|内容缺失|推文为空|未提供|no content|unavailable',
                 str(payload['summary_100']), re.I):
        return None, 'missing_content_interpretation'
    direction = payload['direction']
    if direction not in ('long', 'short', 'neutral'):
        return None, 'invalid_direction'
    # Old neutral results already answered the first-call question. Missing
    # Claims/Themes alone is never a reason to pay for this repair again.
    if direction == 'neutral':
        return [], 'saved_neutral_or_historical'
    if any(k not in payload for k in required[3:6]):
        return None, 'missing_semantic_fields'
    if any(payload[k] not in (0, 1) for k in required[3:6]):
        return None, 'invalid_flags'
    if any(payload[k] for k in required[3:6]):
        return [], 'saved_neutral_or_historical'
    attr = str(payload['attribution']).upper()
    if attr in ('RELAYED', 'RC'):
        return [], 'saved_pure_relay'
    if attr != 'ORIGINAL':
        return None, 'ambiguous_attribution'
    tickers = strings(payload['ticker'])
    if len(tickers) != 1 or (direction == 'short' and payload.get('short_skeptical') != 0):
        return None, 'ambiguous_ticker_direction'
    # v2.0.1 incorrectly treated institutional "we believe" as the author's
    # view. Only directly attributable single-stock decisions are reusable.
    text = post['raw_text']
    if re.search(r'JPMorgan|Morgan Stanley|Goldman|BofA|UBS|Citi(?:group)?|research note|analyst|\bRT @', text, re.I):
        return None, 'possible_external_judgment'
    if not re.search(r"\bI(?:['’]m| am)?\s+(?:just\s+)?(?:bought|buy|buying|sold|sell|selling|shorting|believe|think|expect)|^\s*(?:bullish|bearish|buy|avoid)\b|我(?:认为|看好|看多|看空|买入|加仓|做空)", text, re.I):
        return None, 'needs_author_evidence'
    return [{'ticker': tickers[0], 'direction': direction,
             'reason': payload['summary_100']}], 'saved_direct_author_signal'


def cache_decision(cache, post, db):
    """Validate v1.4.1 input hash, then retain its per-ticker predictions."""
    from signalboard.extract.context import assemble, render_for_llm
    try:
        payload = json.loads(cache['response_json'])
        item = json.loads(post['raw_json'])
        if str(payload.get('post_id')) != post['post_id']:
            return None, 'cache_post_mismatch'
        anchor = item.get('text') or item.get('full_text') or item.get('rawContent') or ''
        if anchor.strip() != post['raw_text'].strip():
            return None, 'cache_text_changed'
        rendered = render_for_llm(assemble(item, db, source_user_id=item.get('userId')))
        digest = hashlib.sha256((post['post_id'] + cache['prompt_version'] + rendered).encode()).hexdigest()
        if digest != cache['input_hash']:
            return None, 'cache_context_changed'
        if not isinstance(payload.get('predictions'), list) or not isinstance(payload.get('flags'), list):
            return None, 'cache_invalid_schema'
        if type(payload.get('has_prediction')) is not bool:
            return None, 'cache_invalid_schema'
        flags = {f.get('flag_type') for f in payload['flags'] if isinstance(f, dict)}
        if flags & {'victory_lap', 'position_disclosure', 'self_reported_returns'}:
            # A flag plus a new prediction can be a mixed post; do not erase it.
            return (None, 'cache_mixed_historical') if payload['predictions'] else ([], 'saved_historical')
        if payload['has_prediction'] != bool(payload['predictions']):
            return None, 'cache_inconsistent_prediction'
        events = []
        for p in payload['predictions']:
            if (p.get('resolution_status') != 'resolved' or p.get('direction') not in ('long', 'short')
                    or not p.get('ticker') or p.get('hedged')
                    or p.get('claim_type') not in ('directional', 'price_target')):
                return None, 'cache_ambiguous_prediction'
            events.append({'ticker': p['ticker'], 'direction': p['direction'],
                           'reason': p.get('thesis_summary', '')})
        return events, 'saved_per_ticker_predictions'
    except (ValueError, TypeError, KeyError, AttributeError):
        return None, 'cache_invalid_payload'


def save_review(con, post, events, *, origin, version, payload, extraction_id=None, reason):
    con.execute('''INSERT OR REPLACE INTO historical_call_reviews
        VALUES(?,?,?,?,?,?,?,?,?,?,?)''', (post['post_id'], post['source_id'], raw_hash(post),
        datetime.now(timezone.utc).isoformat(), VERSION, origin, version,
        payload, json.dumps(events, ensure_ascii=False), extraction_id, reason))


def apply_evidence_reviews(db, path):
    """Apply exact evidence, pinning any model override to its reviewed payload."""
    con = sqlite3.connect(db)
    con.row_factory = sqlite3.Row
    con.executescript(DDL)
    data = json.loads(Path(path).read_text())
    applied = 0
    for evidence in data['reviews']:
        post = con.execute('SELECT * FROM raw_posts WHERE post_id=?', (evidence['post_id'],)).fetchone()
        if not post or raw_hash(post) != evidence['raw_hash']:
            raise ValueError('Reviewed evidence does not match stored raw post: ' + evidence['post_id'])
        cols = {r[1] for r in con.execute('PRAGMA table_info(extractions_intel)')}
        response_col = 'raw_response' if 'raw_response' in cols else 'NULL AS raw_response'
        latest = con.execute(f'SELECT id,{response_col} FROM extractions_intel WHERE post_id=? ORDER BY julianday(extracted_at) DESC,id DESC LIMIT 1', (post['post_id'],)).fetchone()
        if evidence.get('reviewed_extraction_hash') and not latest:
            continue
        if latest and evidence.get('reviewed_extraction_hash') != hashlib.sha256((latest['raw_response'] or '').encode()).hexdigest():
            continue
        if post['post_id'] in load_reviews(con):
            continue
        save_review(con, post, evidence['events'], origin='reviewed_raw_evidence',
                    version=data['version'], payload=json.dumps(evidence, ensure_ascii=False),
                    extraction_id=latest['id'] if latest else None, reason=evidence['reason'])
        applied += 1
    con.commit()
    con.close()
    return applied


def recover(db, sources, current_version):
    con = sqlite3.connect(db)
    con.row_factory = sqlite3.Row
    con.executescript(DDL)
    valid = load_reviews(con)
    latest = {r['post_id']: dict(r) for r in con.execute(
        'SELECT * FROM extractions_intel ORDER BY julianday(extracted_at),id')}
    caches = {r['post_id']: dict(r) for r in con.execute(
        'SELECT * FROM extraction_cache ORDER BY julianday(created_at)')} if table_exists(con, 'extraction_cache') else {}
    counts, reasons, pending = Counter(), Counter(), []
    by_source = {}
    for row in con.execute('SELECT * FROM raw_posts ORDER BY julianday(published_at),post_id').fetchall():
        post = dict(row)
        if post['source_id'] not in sources:
            continue
        pid = post['post_id']
        old = latest.get(pid)
        if old and old['prompt_version'] == current_version:
            counts['current'] += 1
            continue
        if pid in valid:
            counts['already_reused'] += 1
            continue
        if old:
            events, reason = intel_decision(old, post)
            origin, version, payload = 'extractions_intel', old['prompt_version'], old['raw_response']
        elif pid in caches:
            cache = caches[pid]
            events, reason = cache_decision(cache, post, db)
            origin, version, payload = 'extraction_cache', cache['prompt_version'], cache['response_json']
        else:
            events, reason = None, 'no_saved_interpretation'
        reasons[reason] += 1
        if events is None:
            counts['pending'] += 1
            pending.append({'post_id': pid, 'source_id': post['source_id'], 'reason': reason})
            continue
        save_review(con, post, events, origin=origin, version=version, payload=payload,
                    extraction_id=old['id'] if old else None, reason=reason)
        counts['reused'] += 1
        by_source[post['source_id']] = by_source.get(post['source_id'], 0) + 1
    con.commit()
    con.close()
    return {'review_version': VERSION, 'counts': dict(counts), 'reasons': dict(reasons),
            'reused_by_source': by_source, 'pending': pending, 'additional_api_calls': 0}
