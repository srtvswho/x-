"""Finite bonus timeline capture. No transport creation, ingest or publication.

Caller supplies trusted Client and CAS store. Failed/pending batches need human
reconciliation, never automatic retries. Raw response pages stay in private state.
"""
from copy import deepcopy
from datetime import datetime, timedelta, timezone
from .twitterapi_timeline import accumulate, TimelineError

START = datetime(2026, 11, 16, 2, 39, 16, tzinfo=timezone.utc)
EXPIRES = datetime(2026, 11, 22, 8, 10, tzinfo=timezone.utc)
HANDLES = ('jukan05', 'aleabitoreddit', 'zephyr_z9', 'austinsemis',
           'dgretta_author', 'feroceresearch', 'tradexwhisperer', 'gsmferrari')
PAGE_CREDITS = 315


def utc(value):
    result = datetime.fromisoformat(value.replace('Z', '+00:00')) if isinstance(value, str) else value
    if not isinstance(result, datetime) or result.tzinfo is None or result.microsecond:
        raise ValueError('invalid_time')
    return result.astimezone(timezone.utc)


def plan(state, now):
    now = utc(now)
    c = state['config']
    if (state.get('schema') != 'twitterapi-page-journal-v1' or
        c.get('grant_id') != 'bonus-recovery-20261115-7d-30000' or
        c.get('credit_limit') != 30000 or utc(c['expires_at']) != EXPIRES or
        c.get('bonus_only') is not True or c.get('no_payment_instrument_verified') is not True or
        c.get('recharge_credits') != 0 or c.get('verified_bonus_credits', 0) < 30000 or
        type(state.get('reserved_credits')) is not int or not 3420 <= state['reserved_credits'] <= 30000):
        raise ValueError('invalid_grant')
    if now >= EXPIRES:
        return {'status': 'expired'}
    start = START
    for batch in state.get('timeline_daily', []):
        if utc(batch['start']) != start or utc(batch['end']) != min(start + timedelta(days=1), EXPIRES):
            raise ValueError('noncontiguous_daily')
        if batch.get('status') != 'complete':
            return {'status': 'blocked_previous_attempt'}
        start = utc(batch['end'])
    end = min(start + timedelta(days=1), EXPIRES)
    if now < end or start >= end:
        return {'status': 'not_due'}
    if state['reserved_credits'] + PAGE_CREDITS * len(HANDLES) > 30000:
        return {'status': 'budget_stop'}
    return {'status': 'ready', 'start': start.isoformat(), 'end': end.isoformat()}


def run_daily(client, store, *, now, clock=None):
    """Capture one due <=24h window. Never retry an existing batch.

    ``clock`` returns aware datetime for offline tests; live default checks actual
    time before every reservation/request. Client deadline is capped at expiry.
    """
    clock = clock or (lambda: datetime.now(timezone.utc).replace(microsecond=0))
    state, revision = store.load()
    selection = plan(state, now)
    if selection['status'] != 'ready':
        return selection
    state = deepcopy(state)
    batch = dict(start=selection['start'], end=selection['end'], status='running', events=[])
    state.setdefault('timeline_daily', []).append(batch)
    revision = store.save(state, revision)
    client.deadline = EXPIRES
    start, end = utc(batch['start']), utc(batch['end'])
    def save():
        nonlocal revision
        revision = store.save(state, revision)
    def stop(reason):
        batch['status'] = reason
        save()
        return {'status': reason, 'start': batch['start'], 'end': batch['end'], 'production_changed': False}
    for handle in HANDLES:
        pages, cursor = [], ''
        for number in range(2):
            if utc(clock()) >= EXPIRES:
                return stop('expired')
            if state['reserved_credits'] + PAGE_CREDITS > 30000:
                return stop('budget_stop')
            claim = {'kind': 'reserved', 'handle': handle, 'page': number + 1,
                     'cursor': cursor, 'credits': PAGE_CREDITS}
            batch['events'].append(claim)
            state['reserved_credits'] += PAGE_CREDITS
            save()  # CAS must succeed before any external call.
            try:
                payload = client.get('/twitter/user/last_tweets', {'userName': handle, 'cursor': cursor, 'includeReplies': 'true'})
            except Exception:
                return stop('transport_uncertain')
            # Full provider JSON only, never request headers/key or exception text.
            batch['events'].append({'kind': 'response', 'handle': handle,
                                    'page': number + 1, 'payload': deepcopy(payload)})
            save()  # Persist diagnostics even when validation later fails.
            pages.append(payload)
            try:
                window = accumulate(pages, handle, start, end)
            except TimelineError as error:
                return stop(error.code)
            batch['events'].append({'kind': 'validated', 'handle': handle,
                                    'page': number + 1, 'complete': window.complete,
                                    'reason': window.reason, 'tweets': len(window.tweets)})
            save()
            if window.complete:
                break
            if window.reason != 'continuation_required':
                return stop('incomplete')
            cursor = window.next_cursor
        else:
            return stop('page_cap_incomplete')
    batch['status'] = 'complete'
    save()
    return {'status': 'complete', 'start': batch['start'], 'end': batch['end'],
            'accounts': 8, 'ready_for_offline_ingest': True, 'production_changed': False,
            'summary_status': 'not_requested'}


def daily_reserved_credits(state):
    """Count appended reservations for shared ledger reconciliation (no baseline)."""
    total = 0
    for batch in state.get('timeline_daily', []):
        counts = {}
        for event in batch['events']:
            if event['kind'] != 'reserved':
                continue
            handle = event['handle']
            counts[handle] = counts.get(handle, 0) + 1
            if (handle not in HANDLES or event.get('credits') != PAGE_CREDITS or
                    event.get('page') != counts[handle] or counts[handle] > 2):
                raise ValueError('invalid_daily_reservation')
            total += PAGE_CREDITS
    return total


def completed_attempts(batch):
    """Return canonical all-eight cached attempts for offline ingestion only.

    Revalidates full raw pages rather than trusting saved complete flags. Window
    semantics remain timeline semantics; never relabel as advanced-search proof.
    """
    if batch.get('status') != 'complete':
        raise ValueError('incomplete_daily_batch')
    start, end = utc(batch['start']), utc(batch['end'])
    if start < START or end > EXPIRES or not timedelta(0) < end-start <= timedelta(days=1):
        raise ValueError('invalid_daily_scope')
    attempts = []
    for handle in HANDLES:
        events = [e for e in batch['events'] if e.get('handle') == handle]
        pages = [e['payload'] for e in events if e['kind'] == 'response']
        reserved = [e for e in events if e['kind'] == 'reserved']
        if not 1 <= len(pages) <= 2 or len(reserved) != len(pages):
            raise ValueError('invalid_daily_pages')
        window = accumulate(pages, handle, start, end)
        if not window.complete:
            raise ValueError('incomplete_daily_scope')
        attempts.append({'handle':handle, 'start':start.isoformat(), 'end':end.isoformat(),
                         'complete':True, 'reason':window.reason, 'tweets':window.tweets,
                         'pages':pages, 'credits':len(pages)*PAGE_CREDITS})
    return attempts
