"""Offline transactional sink for validated TwitterAPI.io search windows.

Never fetches, calls AI, publishes, initializes the production DB, or overwrites a
saved original. Callers must back up their working database before applying data.
Coverage means the provider exhausted this exact search, not complete X history.
"""
from __future__ import annotations

from datetime import datetime, timezone
from email.utils import parsedate_to_datetime
import json
from pathlib import Path
import re
import sqlite3

from .db import get_conn
from .models import RawPost


class IngestError(ValueError):
    pass


def _iso(value: datetime) -> str:
    if not isinstance(value, datetime) or value.tzinfo is None or value.utcoffset() is None:
        raise IngestError('explicit timezone required')
    if value.microsecond:
        raise IngestError('window/checkpoint timestamps must be whole seconds')
    return value.astimezone(timezone.utc).isoformat().replace('+00:00', 'Z')


def _identity(handle, stream):
    if not isinstance(handle, str) or not re.fullmatch(r'[A-Za-z0-9_]{1,15}', handle):
        raise IngestError('invalid handle')
    if stream not in ('daily', 'catchup'):
        raise IngestError('invalid coverage stream')


def get_coverage(db_path, handle, stream='daily'):
    """Read existing coverage without creating a DB or table; return dict or None."""
    _identity(handle, stream)
    path = Path(db_path).resolve()
    with sqlite3.connect(path.as_uri() + '?mode=ro', uri=True) as conn:
        conn.row_factory = sqlite3.Row
        exists = conn.execute("SELECT 1 FROM sqlite_master WHERE type='table' AND name='twitterapi_coverage'").fetchone()
        if not exists:
            return None
        row = conn.execute('SELECT * FROM twitterapi_coverage WHERE handle=? AND stream=?',
                           (handle.lower(), stream)).fetchone()
        return dict(row) if row else None


def _posts(handle, start, end, rows, captured_at):
    if not isinstance(rows, list) or not rows:
        raise IngestError('empty search remains unverified')
    result = {}
    for item in rows:
        if not isinstance(item, dict):
            raise IngestError('invalid tweet object')
        post_id = item.get('id')
        if not isinstance(post_id, str) or not re.fullmatch(r'\d+', post_id):
            raise IngestError('post ID must be a decimal string')
        author = item.get('author')
        if (not isinstance(author, dict) or str(author.get('userName', '')).lower() != handle.lower()
                or author.get('unavailable') or author.get('protected')):
            raise IngestError('wrong or unavailable author')
        text = item.get('text')
        if not isinstance(text, str) or not text.strip():
            raise IngestError('missing text')
        try:
            published = parsedate_to_datetime(item['createdAt'])
            pub_iso = _iso(published)
            if not start <= published < end:
                raise ValueError()
            encoded = json.dumps(item, ensure_ascii=False, sort_keys=True, allow_nan=False)
        except (ValueError, TypeError, KeyError):
            raise IngestError('invalid date/window or raw JSON') from None
        # Preserve the exact returned text, including whitespace.
        post = RawPost(post_id=post_id, source_id='tw_' + handle, platform='twitter',
                       published_at=pub_iso, captured_at=captured_at, raw_text=text,
                       raw_url=f'https://x.com/{handle}/status/{post_id}', raw_json=encoded)
        if post_id in result:
            prior = result[post_id]
            if prior.raw_text != post.raw_text or prior.published_at != post.published_at:
                raise IngestError('conflicting duplicate within window')
        else:
            result[post_id] = post
    return list(result.values())


def ingest_window(db_path, handle, start, end, window, *, captured_at,
                  stream='daily', expected_coverage_end=None):
    """Atomically insert new originals and advance contiguous search coverage.

    ``expected_coverage_end`` is the previously read ``coverage_end`` string;
    None means no previous checkpoint is expected. All records are revalidated
    before opening a write transaction. Partial/failed/empty windows do nothing.
    Existing raw originals and every derived/interpretation table stay untouched.
    This function deliberately leaves legacy scrape_state unchanged.
    """
    _identity(handle, stream)
    start_iso, end_iso, capture_iso = _iso(start), _iso(end), _iso(captured_at)
    if start >= end or captured_at < end:
        raise IngestError('invalid window or capture before window end')
    receipt = {'handle': handle, 'stream': stream, 'new_persisted': 0,
               'existing_preserved': 0, 'changed_originals_preserved': 0,
               'checkpoint_changed': False, 'summary_status': 'not_requested'}
    if window.complete is not True or window.reason != 'search_exhausted':
        return dict(receipt, fetch_status=window.reason, coverage_status='not_advanced')
    expected_scope = (handle.lower(), start.astimezone(timezone.utc).isoformat(),
                      end.astimezone(timezone.utc).isoformat())
    if getattr(window, 'request_scope', None) != expected_scope:
        raise IngestError('completed search scope does not match requested coverage')
    posts = _posts(handle, start, end, window.tweets, capture_iso)
    if not Path(db_path).is_file():
        raise IngestError('initialized working database required')
    with get_conn(db_path) as conn:
        conn.execute('BEGIN IMMEDIATE')
        # Explicit transaction keeps DDL, inserts and coverage atomic on failure.
        conn.execute('''CREATE TABLE IF NOT EXISTS twitterapi_coverage (
            handle TEXT NOT NULL, stream TEXT NOT NULL,
            coverage_start TEXT NOT NULL, coverage_end TEXT NOT NULL,
            latest_post_id TEXT NOT NULL, latest_post_published_at TEXT NOT NULL,
            verified_at TEXT NOT NULL, provider TEXT NOT NULL,
            PRIMARY KEY(handle, stream))''')
        old = conn.execute('SELECT * FROM twitterapi_coverage WHERE handle=? AND stream=?',
                           (handle.lower(), stream)).fetchone()
        actual = old['coverage_end'] if old else None
        if actual != expected_coverage_end:
            raise IngestError('coverage changed concurrently; reread without refetching')
        if old and (start_iso > old['coverage_end'] or start_iso < old['coverage_start'] or end_iso < old['coverage_end']):
            raise IngestError('coverage gap/backward extension refused')
        for post in posts:
            prior = conn.execute('SELECT source_id, raw_text, published_at FROM raw_posts WHERE post_id=?',
                                 (post.post_id,)).fetchone()
            if prior:
                if prior['source_id'].lower() != post.source_id.lower():
                    raise IngestError('existing ID belongs to another source')
                receipt['existing_preserved'] += 1
                if prior['raw_text'] != post.raw_text or prior['published_at'] != post.published_at:
                    receipt['changed_originals_preserved'] += 1
                continue
            conn.execute('''INSERT INTO raw_posts
                (post_id, source_id, platform, published_at, captured_at, raw_text,
                 raw_url, raw_json, content_hash, is_deleted, archive_url)
                VALUES (:post_id,:source_id,:platform,:published_at,:captured_at,
                        :raw_text,:raw_url,:raw_json,:content_hash,:is_deleted,:archive_url)''', post.to_row())
            receipt['new_persisted'] += 1
        latest = max(posts, key=lambda p: (p.published_at, int(p.post_id)))
        latest_id, latest_time = latest.post_id, latest.published_at
        if old and (old['latest_post_published_at'], int(old['latest_post_id'])) > (latest_time, int(latest_id)):
            latest_id, latest_time = old['latest_post_id'], old['latest_post_published_at']
        conn.execute('''INSERT INTO twitterapi_coverage
            (handle,stream,coverage_start,coverage_end,latest_post_id,latest_post_published_at,verified_at,provider)
            VALUES (?,?,?,?,?,?,?,'twitterapi.io')
            ON CONFLICT(handle,stream) DO UPDATE SET
            coverage_end=excluded.coverage_end, latest_post_id=excluded.latest_post_id,
            latest_post_published_at=excluded.latest_post_published_at,verified_at=excluded.verified_at''',
            (handle.lower(), stream, old['coverage_start'] if old else start_iso, end_iso,
             latest_id, latest_time, capture_iso))
    receipt.update(checkpoint_changed=True, fetch_status='search_exhausted',
                   coverage_status='provider_search_exhausted', coverage_end=end_iso)
    return receipt
