"""Two-account, two-request pilot. No DB/checkpoint/model/deploy writes."""
import json
import os
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from signalboard.twitterapi_io import Client, Budget, FetchError, search


# One manual experiment based on the user's 2026-11-15 dashboard evidence:
# 0 recharge credits + 100K bonus credits; user confirmed no card.
# The official balance API documents only recharge_credits, NOT bonus balance.
# This exception expires, stays branch-only, and never changes production guards.
def bonus_pilot_allowed(env, recharge_credits, now):
    return (
        env.get('TWITTERAPI_BONUS_PILOT_EVIDENCE') == 'dashboard-2026-11-15-100k-no-card'
        and env.get('GITHUB_EVENT_NAME') == 'workflow_dispatch'
        and env.get('GITHUB_REF') == 'refs/heads/recovery/twitterapi-free'
        and env.get('GITHUB_ACTOR') == 'srtvswho'
        and env.get('GITHUB_RUN_ATTEMPT') == '1'
        and env.get('AI_ENABLED') == 'false'
        and env.get('ALLOW_EXPENSIVE_AI_JOB') == 'false'
        and env.get('AI_DRY_RUN') == 'true'
        and recharge_credits == 0
        and datetime(2026, 11, 15, tzinfo=timezone.utc) <= now
        < datetime(2026, 11, 16, tzinfo=timezone.utc)
    )

def main():
    if os.environ.get('TWITTERAPI_FREE_CREDIT_VERIFIED') != 'true':
        raise FetchError('free credits and no auto-recharge must be verified before pilot')
    client = Client(os.environ.get('TWITTERAPI_IO_KEY'))
    before = client.credits()
    bonus_mode = bonus_pilot_allowed(os.environ, before, datetime.now(timezone.utc))
    if os.environ.get('TWITTERAPI_BONUS_PILOT_EVIDENCE') and not bonus_mode:
        raise FetchError('bonus-only pilot guard refused; no search sent')
    if before < 1000 and not bonus_mode:
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
                      'recharge_credit_delta': before - after if after is not None else None,
                      'bonus_credit_delta': None,
                      'balance_mode': 'dashboard_bonus_one_off' if bonus_mode else 'recharge_api',
                      'search_credit_upper_bound': 600,
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
