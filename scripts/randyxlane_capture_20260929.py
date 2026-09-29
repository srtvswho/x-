"""One-account, one-paid-request capture. Raw data stays in Actions artifacts."""
import datetime as dt
import json
import os
from pathlib import Path
import time
import urllib.request
import urllib.parse

OUT = Path('outputs/randyxlane_20260929')
OUT.mkdir(parents=True, exist_ok=True)
API = 'https://api.apify.com/v2'
CAP = 0.801
MAX_ITEMS = 2000

def save(name, value):
    p = OUT / name
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(value, ensure_ascii=False, indent=2))

def api(path, method='GET', data=None, params=None):
    url = API + path
    if params:
        url += '?' + urllib.parse.urlencode(params)
    req = urllib.request.Request(url, method=method, headers={
        'Authorization': 'Bearer ' + os.environ['APIFY_TOKEN'],
        'Content-Type': 'application/json'},
        data=json.dumps(data).encode() if data is not None else None)
    with urllib.request.urlopen(req, timeout=45) as r:
        return json.load(r)

def iso(value):
    return dt.datetime.fromisoformat(value.replace('Z', '+00:00'))

def main():
    actor = api('/acts/apidojo~tweet-scraper')['data']
    now = dt.datetime.now(dt.timezone.utc)
    prices = [p for p in actor['pricingInfos'] if iso(p['startedAt']) <= now]
    pricing = max(prices, key=lambda p: iso(p['startedAt']))
    events = pricing.get('pricingPerEvent', {}).get('actorChargeEvents', {})
    assert pricing['pricingModel'] == 'PAY_PER_EVENT'
    assert set(events) == {'apify-default-dataset-item'}
    event = events['apify-default-dataset-item']
    rates = [v['tieredEventPriceUsd'] for v in event.get('eventTieredPricingUsd', {}).values()]
    assert rates and max(rates) <= .0004, 'Current price exceeds capture budget'
    assert (pricing.get('minimalMaxTotalChargeUsd') or 0) <= .001
    save('pricing.json', pricing)
    body = {
        'customMapFunction': '(object) => { return {...object} }',
        'includeSearchTerms': False, 'maxItems': MAX_ITEMS,
        'onlyImage': False, 'onlyQuote': False, 'onlyTwitterBlue': False,
        'onlyVerifiedUsers': False, 'onlyVideo': False,
        'searchTerms': ['from:randyxlane since:2015-01-01 until:2026-09-30'],
        'sort': 'Latest', 'disableMaximization': True}
    save('input.json', body)
    save('reservation.json', {'reserved_usd': CAP, 'requests': 1,
         'retry_allowed': False, 'requested_at': now.isoformat()})
    run = api('/acts/apidojo~tweet-scraper/runs', 'POST', body,
        {'maxTotalChargeUsd': CAP, 'maxItems': MAX_ITEMS, 'timeout': 600,
         'restartOnError': 'false', 'build': actor['taggedBuilds']['latest']['buildNumber']})['data']
    save('run.json', run)
    print(json.dumps({'apify_run_id': run['id'], 'status': run['status'], 'cap_usd': CAP}), flush=True)
    confirmed = run.get('options', {}).get('maxTotalChargeUsd')
    if confirmed is None or confirmed > CAP:
        api('/actor-runs/' + run['id'] + '/abort', 'POST', {})
        raise RuntimeError('Provider did not confirm cap')
    deadline = time.monotonic() + 660
    while run['status'] not in {'SUCCEEDED', 'FAILED', 'ABORTED', 'TIMED-OUT'}:
        if time.monotonic() > deadline:
            api('/actor-runs/' + run['id'] + '/abort', 'POST', {})
            raise RuntimeError('Deadline exceeded; no retry')
        time.sleep(5)
        run = api('/actor-runs/' + run['id'])['data']
        save('run.json', run)
    assert run.get('usageTotalUsd', 0) <= CAP + .000001
    items = api('/datasets/' + run['defaultDatasetId'] + '/items', params={
        'format': 'json', 'clean': 'true', 'limit': MAX_ITEMS})
    save('raw_posts.json', items)
    posts = []
    for item in items:
        if not isinstance(item, dict) or item.get('noResults'):
            continue
        author = item.get('author') or {}
        if str(author.get('userName', '')).lower() != 'randyxlane':
            continue
        posts.append({
            'id': str(item.get('id', '')), 'createdAt': item.get('createdAt'),
            'text': item.get('fullText') or item.get('text'), 'url': item.get('url'),
            'isReply': item.get('isReply'), 'isRetweet': item.get('isRetweet'),
            'inReplyToId': item.get('inReplyToId'), 'quote': item.get('quote'),
            'media': item.get('extendedEntities') or item.get('entities')})
    unique = {p['id']: p for p in posts if p['id']}
    save('posts.json', list(unique.values()))
    receipt = {'status': run['status'], 'items': len(items), 'unique_posts': len(unique),
        'apify_run_id': run['id'], 'usage_usd': run.get('usageTotalUsd'),
        'captured_at': now.isoformat(), 'full_history_verified': False,
        'cap_reached': len(items) >= MAX_ITEMS, 'production_modified': False}
    save('receipt.json', receipt)
    print(json.dumps(receipt), flush=True)
    assert run['status'] == 'SUCCEEDED', 'Partial output retained; no automatic retry'
    assert unique, 'No valid posts returned'
    media_index = []
    for item in items:
        if str((item.get('author') or {}).get('userName', '')).lower() != 'randyxlane':
            continue
        media = (item.get('extendedEntities') or {}).get('media') or (item.get('entities') or {}).get('media') or []
        for n, photo in enumerate(media):
            if photo.get('type') != 'photo':
                continue
            url = photo.get('media_url_https') or photo.get('media_url')
            if not url:
                continue
            parts = urllib.parse.urlsplit(url)
            if parts.hostname != 'pbs.twimg.com':
                continue
            url = urllib.parse.urlunsplit(('https', parts.netloc, parts.path, 'name=orig', ''))
            name = 'images/' + str(item['id']) + '_' + str(n) + '.jpg'
            record = {'post_id': str(item['id']), 'url': url, 'file': name}
            try:
                with urllib.request.urlopen(url, timeout=20) as r:
                    content = r.read(25000001)
                assert len(content) <= 25000000
                p = OUT / name
                p.parent.mkdir(parents=True, exist_ok=True)
                p.write_bytes(content)
                record.update(status='saved', bytes=len(content))
            except Exception as error:
                record.update(status='failed', error=type(error).__name__)
            media_index.append(record)
            save('media_index.json', media_index)
    print(json.dumps({'images_saved': sum(x['status']=='saved' for x in media_index), 'images_total': len(media_index)}), flush=True)
    # Free prices are archived for manual semantic review and event backtesting.
    tickers = 'SPY QQQ SOXX TQQQ TSLA META ORCL IONQ MCD NVDA MU SNDK AMD INTC TSM MSFT GOOGL AMZN AVGO CRM NOW SNOW ADBE BABA PDD JD RKLB PLTR GLD SLV COIN'.split()
    start = int(dt.datetime(2024, 1, 1, tzinfo=dt.timezone.utc).timestamp())
    end = int(dt.datetime(2026, 9, 29, tzinfo=dt.timezone.utc).timestamp())
    failures = {}
    for ticker in tickers:
        url = 'https://query1.finance.yahoo.com/v8/finance/chart/' + ticker + '?' + urllib.parse.urlencode({
            'period1': start, 'period2': end, 'interval': '1d', 'events': 'splits,div'})
        try:
            req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
            with urllib.request.urlopen(req, timeout=15) as r:
                data = json.load(r)
            save('prices/' + ticker + '.json', data)
        except Exception as error:
            failures[ticker] = type(error).__name__
    save('price_failures.json', failures)
    print(json.dumps({'price_files': len(tickers)-len(failures), 'price_failures': failures}), flush=True)

if __name__ == '__main__':
    main()
