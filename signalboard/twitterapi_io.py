"""Fail-closed TwitterAPI.io reader. No retries, redirects, writes or payment API.

Official schema: docs.twitterapi.io/api-reference/endpoint/tweet_advanced_search.
A completed search window is not proof of complete X history or account availability.
"""
from dataclasses import dataclass, field
from datetime import datetime, timezone
from email.utils import parsedate_to_datetime
import json
import re
import time
import urllib.request

BASE = 'https://api.twitterapi.io'

class FetchError(RuntimeError):
    pass

class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, *args, **kwargs):
        raise FetchError('redirect refused')

@dataclass
class Budget:
    # One page is documented as <=20 tweets, 15 credits each. No retries.
    max_pages: int = 2
    used: int = 0

    def take(self):
        if not 1 <= self.max_pages <= 16 or self.used >= self.max_pages:
            raise FetchError('page budget exhausted')
        self.used += 1

class Client:
    def __init__(self, key):
        if not key:
            raise FetchError('missing TWITTERAPI_IO_KEY')
        self._key = key
        self._last_request = None
        self.deadline = None
        self._opener = urllib.request.build_opener(NoRedirect())

    def get(self, path, params=None):
        from urllib.parse import urlencode
        if path not in ('/oapi/my/info', '/twitter/tweet/advanced_search', '/twitter/user/last_tweets'):
            raise FetchError('endpoint refused')
        if self._last_request is not None:
            time.sleep(max(0, 5.1 - (time.monotonic() - self._last_request)))
        if self.deadline is not None and datetime.now(timezone.utc) >= self.deadline:
            raise FetchError('grant expired before transport')
        self._last_request = time.monotonic()
        req = urllib.request.Request(BASE + path + ('?' + urlencode(params) if params else ''),
                                     headers={'X-API-Key': self._key})
        try:
            with self._opener.open(req, timeout=30) as response:
                data = json.load(response)
        except Exception:
            # Never include HTTP response, request, key, or provider message in logs.
            raise FetchError('provider transport/JSON failure; no retry') from None
        if not isinstance(data, dict) or data.get('error') or data.get('status') == 'error':
            raise FetchError('provider error envelope')
        return data

    def credits(self):
        credits = self.get('/oapi/my/info').get('recharge_credits')
        if type(credits) is not int or credits < 0:
            raise FetchError('unknown credit balance')
        return credits

@dataclass
class Window:
    tweets: list = field(default_factory=list)
    complete: bool = False
    reason: str = 'not_started'
    pages: int = 0
    request_scope: tuple | None = None


def search(client, handle, start, end, budget, max_pages=1):
    if not re.fullmatch(r'[A-Za-z0-9_]{1,15}', handle):
        raise ValueError('invalid handle')
    if not start.tzinfo or not end.tzinfo or start >= end or start.microsecond or end.microsecond:
        raise ValueError('explicit ordered UTC window required')
    if not 1 <= max_pages <= 16:
        raise ValueError('invalid page cap')
    query = f'from:{handle} since_time:{int(start.timestamp())} until_time:{int(end.timestamp())}'
    scope = (handle.lower(), start.astimezone(timezone.utc).isoformat(), end.astimezone(timezone.utc).isoformat())
    result, cursor, cursors, ids = Window(request_scope=scope), '', set(), set()
    for _ in range(max_pages):
        budget.take()
        data = client.get('/twitter/tweet/advanced_search',
                          {'query': query, 'queryType': 'Latest', 'cursor': cursor})
        result.pages += 1
        rows, more, next_cursor = data.get('tweets'), data.get('has_next_page'), data.get('next_cursor')
        if not isinstance(rows, list) or len(rows) > 20 or type(more) is not bool or not isinstance(next_cursor, str):
            raise FetchError('invalid page schema')
        for row in rows:
            if not isinstance(row, dict):
                raise FetchError('invalid tweet')
            if not isinstance(row.get('id'), str) or not re.fullmatch(r'\d+', row['id']):
                raise FetchError('tweet ID must remain a decimal string')
            author = row.get('author') or {}
            if not isinstance(author, dict) or str(author.get('userName','')).lower() != handle.lower() or author.get('unavailable') or author.get('protected'):
                raise FetchError('unexpected/unavailable author')
            try:
                published = parsedate_to_datetime(row['createdAt'])
                if not published.tzinfo or not start <= published < end:
                    raise ValueError()
            except Exception:
                raise FetchError('missing or out-of-window timestamp') from None
            if not isinstance(row.get('text'), str) or not row['text'].strip():
                raise FetchError('missing tweet text')
            if row['id'] not in ids:
                ids.add(row['id'])
                result.tweets.append(row)
        if not more:
            result.complete = True
            result.reason = 'search_exhausted' if result.tweets else 'empty_unverified'
            # An empty search cannot establish that a protected/unavailable account is healthy.
            if not result.tweets:
                result.complete = False
            return result
        if not rows or not next_cursor or next_cursor in cursors:
            raise FetchError('inconsistent/stalled pagination')
        cursors.add(next_cursor)
        cursor = next_cursor
    result.reason = 'page_cap_partial'
    return result
