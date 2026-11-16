"""Offline last_tweets validation and window coverage. No transport or activation.

Coverage means traversal of this provider's timeline, not proof of full X history.
Only ordinary timeline rows establish chronology; the separate pin never does.
"""
from copy import deepcopy
from dataclasses import dataclass, field
from datetime import datetime, timezone
import re


class TimelineError(ValueError):
    """Only constant, field-specific codes are exposed, never provider text."""
    def __init__(self, code):
        self.code = code
        super().__init__(code)


def _fail(code):
    raise TimelineError(code) from None


def _handle(handle):
    if not isinstance(handle, str) or not re.fullmatch(r'[A-Za-z0-9_]{1,15}', handle):
        _fail('scope.handle')
    return handle.lower()


def _timestamp(value):
    if not isinstance(value, str):
        _fail('tweet.createdAt')
    try:
        # Require the complete documented Twitter timestamp, including weekday.
        parsed = datetime.strptime(value, '%a %b %d %H:%M:%S %z %Y')
        if parsed.strftime('%a %b %d %H:%M:%S %z %Y') != value:
            _fail('tweet.createdAt')
        return parsed.astimezone(timezone.utc)
    except (ValueError, TypeError, OverflowError):
        _fail('tweet.createdAt')


def _row(row, handle):
    if not isinstance(row, dict):
        _fail('tweet.object')
    if not isinstance(row.get('id'), str) or not re.fullmatch(r'[0-9]+', row['id']):
        _fail('tweet.id')
    if not isinstance(row.get('text'), str) or not row['text'].strip():
        _fail('tweet.text')
    author = row.get('author')
    if not isinstance(author, dict):
        _fail('tweet.author')
    if not isinstance(author.get('userName'), str) or author['userName'].lower() != handle:
        _fail('tweet.author.userName')
    if author.get('unavailable') or author.get('protected'):
        _fail('tweet.author.availability')
    return deepcopy(row), _timestamp(row.get('createdAt'))


@dataclass
class TimelinePage:
    tweets: list
    timestamps: list
    has_next_page: bool
    next_cursor: str
    pin_tweet: dict | None = None


def validate_page(payload, handle):
    """Validate nested last_tweets envelope; ignore unrecognized metadata."""
    handle = _handle(handle)
    if not isinstance(payload, dict):
        _fail('response.object')
    if payload.get('status') != 'success':
        _fail('response.status')
    data = payload.get('data')
    if not isinstance(data, dict):
        _fail('response.data')
    rows = data.get('tweets')
    if not isinstance(rows, list):
        _fail('response.data.tweets')
    if len(rows) > 20:
        _fail('response.data.tweets.limit')
    if type(payload.get('has_next_page')) is not bool:
        _fail('response.has_next_page')
    if not isinstance(payload.get('next_cursor'), str):
        _fail('response.next_cursor')
    validated = [_row(row, handle) for row in rows]
    timestamps = [time for _, time in validated]
    if any(a < b for a, b in zip(timestamps, timestamps[1:])):
        _fail('timeline.order')
    pin = data.get('pin_tweet')
    if pin == {}:
        pin = None
    if pin is not None:
        pin, _ = _row(pin, handle)
    return TimelinePage([row for row, _ in validated], timestamps,
                        payload['has_next_page'], payload['next_cursor'], pin)


@dataclass
class TimelineWindow:
    tweets: list = field(default_factory=list)
    complete: bool = False
    reason: str = 'not_started'
    pages: int = 0
    next_cursor: str = ''
    request_scope: tuple | None = None


def accumulate(pages, handle, start, end):
    """Fold consecutive response pages for one frozen [start, end) scope.

    No retries, requests or persistence. Missing continuation remains incomplete.
    The caller must supply pages in actual request order beginning at cursor ''.
    """
    handle = _handle(handle)
    if not isinstance(start, datetime) or not isinstance(end, datetime) or not start.tzinfo or not end.tzinfo:
        _fail('scope.time')
    if start.microsecond or end.microsecond or start >= end:
        _fail('scope.time')
    if not isinstance(pages, (list, tuple)):
        _fail('response.pages')
    result = TimelineWindow(request_scope=(handle, start.astimezone(timezone.utc).isoformat(), end.astimezone(timezone.utc).isoformat()))
    last = None
    seen_ids = {}
    seen_cursors = {''}
    evidence = False
    for raw in pages:
        page = validate_page(raw, handle)
        result.pages += 1
        if page.timestamps and last is not None and page.timestamps[0] > last:
            _fail('timeline.order')
        for row, published in zip(page.tweets, page.timestamps):
            old = seen_ids.get(row['id'])
            if old and (old['text'] != row['text'] or old['createdAt'] != row['createdAt']):
                _fail('tweet.id.conflict')
            if old is None:
                seen_ids[row['id']] = row
                if start <= published < end:
                    result.tweets.append(row)
        # A pin can be a valid window post, but is never traversal evidence.
        if page.pin_tweet is not None:
            pin = page.pin_tweet
            published = _timestamp(pin['createdAt'])
            old = seen_ids.get(pin['id'])
            if old and (old['text'] != pin['text'] or old['createdAt'] != pin['createdAt']):
                _fail('tweet.id.conflict')
            if old is None:
                seen_ids[pin['id']] = pin
                if start <= published < end:
                    result.tweets.append(pin)
        if page.timestamps:
            evidence = True
            last = page.timestamps[-1]
        # Broken nonterminal pagination cannot certify coverage, even if old rows occur.
        if page.has_next_page and (not page.tweets or not page.next_cursor or page.next_cursor in seen_cursors):
            result.reason = 'pagination_incomplete'
            return result
        if page.timestamps and page.timestamps[-1] < start:
            result.complete = True
            result.reason = 'start_boundary_crossed'
            return result
        if not page.has_next_page:
            result.complete = evidence
            result.reason = 'timeline_exhausted' if evidence else 'empty_unverified'
            return result
        seen_cursors.add(page.next_cursor)
        result.next_cursor = page.next_cursor
        result.reason = 'continuation_required'
    return result
