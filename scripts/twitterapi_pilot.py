"""Two-account, two-request pilot. No DB/checkpoint/model/deploy writes."""
import json
import os
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from signalboard.twitterapi_io import Client, Budget, FetchError, search


def main():
    if os.environ.get('TWITTERAPI_FREE_CREDIT_VERIFIED') != 'true':
        raise FetchError('free credits and no auto-recharge must be verified before pilot')
    client = Client(os.environ.get('TWITTERAPI_IO_KEY'))
    before = client.credits()
    if before < 1000:
        raise FetchError('insufficient verified credits; no search sent')
    budget = Budget(2)
    end = datetime.now(timezone.utc).replace(microsecond=0)
    results = []
    failure = None
    after = None
    try:
        for handle in ('jukan05', 'aleabitoreddit'):
            window = search(client, handle, end - timedelta(days=1), end, budget)
            results.append({'handle': handle, 'fetched': len(window.tweets),
                            'fetch_status': window.reason, 'window_complete': window.complete,
                            'sample_ids': [t['id'] for t in window.tweets[:2]],
                            'summary_status': 'not_requested', 'checkpoint_changed': False})
            print(json.dumps({'account_checkpoint': results[-1], 'search_requests': budget.used}), flush=True)
        after = client.credits()
    except FetchError as exc:
        failure = str(exc)
    print(json.dumps({'results': results, 'search_requests': budget.used,
                      'credit_delta': before - after if after is not None else None,
                      'failure': failure, 'production_changed': False}))
    # Partial evidence is retained; never repeat completed calls automatically.
    return 0 if not failure and len(results) == 2 and all(r['fetched'] for r in results) else 2

if __name__ == '__main__':
    try:
        sys.exit(main())
    except FetchError as exc:
        print(json.dumps({'fetch_status': 'blocked_or_failed', 'reason': str(exc),
                          'summary_status': 'not_requested', 'checkpoint_changed': False}))
        sys.exit(1)
