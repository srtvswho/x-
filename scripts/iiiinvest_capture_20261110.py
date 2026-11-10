"""Bounded fallback capture; never deployed or executed automatically by local reads.

Runs only when APIFY_TOKEN is supplied by the isolated Actions workflow.
No production database writes, no paid POST retries, raw results kept in artifacts.
"""
import datetime as dt
import email.utils
import json
import os
from pathlib import Path
import time
import urllib.parse
import urllib.request

API = 'https://api.apify.com/v2'
ACTOR = 'apidojo~tweet-scraper'
OUT = Path('outputs/iiiinvest_20261110')
TOTAL_CAP = 3.0
MAX_RATE = 0.0004
HANDLE = 'iiiinvest'
KNOWN_EARLIEST_ID = 2044318642817642799
CONFIG = Path('config/iiiinvest_20261110.json')
TERMINAL = {'SUCCEEDED', 'FAILED', 'ABORTED', 'TIMED-OUT'}


def save(name, value):
    p = OUT / name
    p.parent.mkdir(parents=True, exist_ok=True)
    tmp = p.with_suffix(p.suffix + '.tmp')
    tmp.write_text(json.dumps(value, ensure_ascii=False, indent=2))
    tmp.replace(p)


def api(path, method='GET', data=None, params=None):
    url = API + path
    if params:
        url += '?' + urllib.parse.urlencode(params)
    request = urllib.request.Request(url, method=method, headers={
        'Authorization': 'Bearer ' + os.environ['APIFY_TOKEN'],
        'Content-Type': 'application/json'},
        data=json.dumps(data).encode() if data is not None else None)
    # An uncertain POST must never be retried. GET failures also stop this job;
    # the saved run ID lets the owner inspect/resume without another paid run.
    with urllib.request.urlopen(request, timeout=45) as response:
        return json.load(response)


def iso(value):
    return dt.datetime.fromisoformat(value.replace('Z', '+00:00'))


def author(item):
    person = item.get('author') or {}
    return str(person.get('userName') or person.get('username') or '').lower()


def publish_receipt(runs, cutoff):
    posts = {}
    other_authors = 0
    for record in runs:
        for item in record.get('items', []):
            if not isinstance(item, dict) or item.get('noResults'):
                continue
            if author(item) != HANDLE:
                other_authors += 1
                continue
            ident = str(item.get('id') or '')
            if ident:
                posts[ident] = item
    ordered = sorted(posts.values(), key=lambda p: int(p['id']))
    save('posts.json', ordered)
    media = []
    for item in ordered:
        entities = item.get('extendedEntities') or item.get('entities') or {}
        for index, entry in enumerate(entities.get('media') or []):
            media.append({'post_id': str(item['id']), 'index': index, **entry})
    save('media_index.json', media)
    timestamps = [p.get('createdAt') or p.get('created_at') for p in ordered]
    monthly = {}
    for value in timestamps:
        try:
            stamp = email.utils.parsedate_to_datetime(value)
        except (TypeError, ValueError):
            stamp = iso(value)
        month = stamp.strftime('%Y-%m')
        monthly[month] = monthly.get(month, 0) + 1
    receipt = {
        'account': HANDLE, 'cutoff_utc': cutoff, 'unique_posts': len(posts),
        'other_author_rows': other_authors,
        'known_free_history_earliest_id': str(KNOWN_EARLIEST_ID),
        'all_ids_before_free_history': all(int(p['id']) < KNOWN_EARLIEST_ID for p in ordered),
        'month_counts': monthly,
        'run_ids': [r['run']['id'] for r in runs],
        'usage_usd': sum(float(r['run'].get('usageTotalUsd') or 0) for r in runs),
        'hard_budget_usd': TOTAL_CAP, 'paid_retries': 0,
        'all_runs_succeeded': all(r['run']['status'] == 'SUCCEEDED' for r in runs),
        'cap_reached': any(r['cap_reached'] for r in runs),
        'earliest_post_time': timestamps[0] if timestamps else None,
        'latest_post_time': timestamps[-1] if timestamps else None,
        'full_history_verified': False,
        'coverage_note': 'Search exhaustion alone does not prove all X history; compare month coverage and independent public timelines.',
        'production_modified': False,
    }
    save('receipt.json', receipt)
    print(json.dumps(receipt), flush=True)


def capture(label, queries, max_items, cap, build, extra=None):
    assert 1 <= len(queries) <= 5
    assert cap >= max_items * MAX_RATE
    body = {
        'customMapFunction': '(object) => { return {...object} }',
        'includeSearchTerms': True, 'maxItems': max_items,
        'onlyImage': False, 'onlyQuote': False, 'onlyTwitterBlue': False,
        'onlyVerifiedUsers': False, 'onlyVideo': False,
        'searchTerms': queries, 'sort': 'Latest', 'disableMaximization': True,
    }
    if extra:
        body.update(extra)
    save(label + '/input.json', body)
    save(label + '/reservation.json', {
        'cap_usd': cap, 'max_items': max_items, 'paid_post_attempted': True,
        'retry_allowed': False, 'requested_at': dt.datetime.now(dt.timezone.utc).isoformat(),
    })
    run = api('/acts/' + ACTOR + '/runs', 'POST', body, {
        'maxTotalChargeUsd': cap, 'maxItems': max_items, 'timeout': 900,
        'restartOnError': 'false', 'build': build,
    })['data']
    save(label + '/run.json', run)
    print(json.dumps({'phase': label, 'run_id': run['id'], 'status': run['status'], 'cap_usd': cap}), flush=True)
    confirmed = run.get('options', {}).get('maxTotalChargeUsd')
    if confirmed is None or float(confirmed) > cap + 0.000001:
        api('/actor-runs/' + run['id'] + '/abort', 'POST', {})
        raise RuntimeError('Provider did not confirm cost cap; run aborted')
    deadline = time.monotonic() + 960
    while run['status'] not in TERMINAL:
        if time.monotonic() > deadline:
            api('/actor-runs/' + run['id'] + '/abort', 'POST', {})
            raise RuntimeError('Deadline exceeded; no paid retry')
        time.sleep(5)
        run = api('/actor-runs/' + run['id'])['data']
        save(label + '/run.json', run)
    assert float(run.get('usageTotalUsd') or 0) <= cap + 0.000001
    items = []
    # Free dataset pagination: retain every raw field, no language/reply filter.
    offset = 0
    while True:
        page = api('/datasets/' + run['defaultDatasetId'] + '/items', params={
            'format': 'json', 'clean': 'false', 'offset': offset, 'limit': 1000,
        })
        assert isinstance(page, list)
        items.extend(page)
        if len(page) < 1000:
            break
        offset += len(page)
    save(label + '/raw_posts.json', items)
    record = {'run': run, 'items': items, 'cap_reached': len(items) >= max_items}
    return record


def main():
    config = json.loads(CONFIG.read_text())
    assert config['handle'] == HANDLE
    assert float(config['hard_budget_usd']) <= TOTAL_CAP
    assert config['paid_retries'] == 0
    assert config['production_changes'] is False
    actor = api('/acts/' + ACTOR)['data']
    cutoff = dt.datetime.now(dt.timezone.utc).isoformat()
    prices = [p for p in actor['pricingInfos'] if iso(p['startedAt']) <= iso(cutoff)]
    pricing = max(prices, key=lambda p: iso(p['startedAt']))
    events = pricing.get('pricingPerEvent', {}).get('actorChargeEvents', {})
    assert pricing['pricingModel'] == 'PAY_PER_EVENT'
    assert set(events) == {'apify-default-dataset-item'}, 'Unreviewed extra charge type'
    event = events['apify-default-dataset-item']
    rates = [float(v['tieredEventPriceUsd']) for v in event.get('eventTieredPricingUsd', {}).values()]
    assert rates and max(rates) <= MAX_RATE, 'Rate above $0.40 / 1000; stop before paying'
    assert float(pricing.get('minimalMaxTotalChargeUsd') or 0) <= 0.001
    save('pricing.json', pricing)
    build = actor['taggedBuilds']['latest']['buildNumber']
    queries = config['queries']
    assert int(config['known_earliest_post_id']) == KNOWN_EARLIEST_ID
    assert len(queries) <= 5
    assert all('from:iiiinvest ' in q and 'until:' in q and 'since:' in q for q in queries)
    runs = []
    # Search older history, never a profile timeline that repeats the 3200 cap.
    smoke_query = config['smoke_query'] + ' max_id:' + str(KNOWN_EARLIEST_ID - 1)
    smoke = capture('smoke', [smoke_query], 50, 0.021, build)
    runs.append(smoke)
    publish_receipt(runs, cutoff)
    valid = [p for p in smoke['items'] if isinstance(p, dict) and author(p) == HANDLE and p.get('id') and p.get('createdAt') and (p.get('text') or p.get('fullText'))]
    assert smoke['run']['status'] == 'SUCCEEDED' and valid, 'Smoke failed; retained partial data, no bulk'
    assert float(smoke['run'].get('usageTotalUsd') or 0) <= 0.021
    assert all(int(p['id']) < KNOWN_EARLIEST_ID for p in valid), 'Historical query ignored; no bulk'
    save('smoke/field_audit.json', {'valid_author_posts': len(valid),
         'returned_fields': sorted({k for p in valid for k in p}),
         'earliest_id': min(int(p['id']) for p in valid),
         'latest_id': max(int(p['id']) for p in valid),
         'actual_usage_usd': smoke['run'].get('usageTotalUsd'),
         'price_per_1000_usd': MAX_RATE * 1000})
    # Reserve the full smoke cap, not only reported charge, so delayed billing
    # cannot push aggregate spend above $3.00. Bulk is one paid attempt.
    remaining = round(TOTAL_CAP - 0.021, 6)
    limit = min(int(config.get('max_items', 7400)), int((remaining - 0.001) / MAX_RATE))
    assert limit >= 50
    # Latest smoke pagination is continued below its oldest ID, with disjoint
    # annual windows. This avoids paying again for the smoke or free timeline.
    older_than = min(int(p['id']) for p in valid) - 1
    queries = [q + ' max_id:' + str(older_than) for q in queries]
    bulk = capture('bulk', queries, limit, remaining, build)
    runs.append(bulk)
    publish_receipt(runs, cutoff)
    assert bulk['run']['status'] == 'SUCCEEDED', 'Partial data retained; no paid retry'
    assert not bulk['cap_reached'], 'Cap reached: historical coverage remains incomplete'


if __name__ == '__main__':
    main()
