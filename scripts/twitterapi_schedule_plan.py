"""Read-only finite-trial selector. Does not fetch, dispatch, write or renew grants.

Recovery scopes remain catch-up scopes; this planner does not promote daily
coverage. The caller must enforce the runner's approved execution gates.
"""
import json
import os
from pathlib import Path
import sys
from datetime import datetime, timezone
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from collections import defaultdict
from signalboard.twitterapi_paging import _check_state, _policy, _scope, _utc, select_windows
from signalboard.twitterapi_recovery import HANDLES


def plan_next(store, *, expected_policy, now):
    """Load/validate once, return sanitized ready/wait/stop decision and subset.

    A failed/uncertain account blocks the entire trial. Only the oldest unfinished
    immutable scope of each account may run, at most one scope per account.
    """
    state, _ = store.load()
    _check_state(state, expected_policy)
    policy = _policy(expected_policy)
    now = _utc(now)
    def result(status, reason, windows=None):
        return {'status': status, 'reason': reason, 'selected_windows': windows or [],
                'reserved_credits': state['reserved_credits'],
                'production_changed': False, 'daily_promotion': False}
    if (policy['credit_limit'] > 30000 or policy['max_pages_per_window'] > 10 or
            policy.get('preflight_mode') != 'dashboard_evidence' or
            policy.get('max_balance_reads') != 0 or policy.get('recharge_credits') != 0 or
            policy.get('bonus_only') is not True or policy.get('no_payment_instrument_verified') is not True or
            policy.get('verified_bonus_credits', 0) < policy['credit_limit']):
        return result('stop', 'finite_bonus_scope_invalid')
    if now >= _utc(policy['expires_at']) or (policy.get('bonus_expires_at') and now >= _utc(policy['bonus_expires_at'])):
        return result('stop', 'expired')
    if any(e.get('pending') or e['status'] in ('uncertain', 'empty_unverified', 'page_cap_partial')
           for e in state['windows'].values()) or 'pending' in state.get('balance_reads', []):
        return result('stop', 'account_requires_review')
    if any(e['status'] == 'continuation_ready' for e in state['windows'].values()):
        return result('stop', 'interrupted_account')
    if state['reserved_credits'] + 300 > min(30000, policy['credit_limit']):
        return result('stop', 'budget_exhausted')
    grouped = defaultdict(list)
    for w in policy['windows']:
        if w['handle'].lower() not in {h.lower() for h in HANDLES} or (_utc(w['end'])-_utc(w['start'])).total_seconds() > 86400:
            return result('stop', 'window_scope_invalid')
        grouped[w['handle']].append(w)
    selected=[]
    for handle in sorted(grouped):
        scopes=sorted(grouped[handle],key=lambda w:_utc(w['start']))
        for previous, following in zip(scopes, scopes[1:]):
            if _utc(previous['end']) != _utc(following['start']):
                return result('stop', 'noncontiguous_grant')
        for w in scopes:
            key, _, _, end = _scope(w['handle'], w['start'], w['end'])
            if state['windows'].get(key, {}).get('status') == 'search_exhausted':
                continue
            if end <= now:
                selected.append(w)
            break
    selected.sort(key=lambda w:(_utc(w['start']), w['handle']))
    if not selected:
        return result('wait', 'no_due_incomplete_windows')
    # Each selection needs at least one reservation; never select more accounts
    # than the remaining lifetime allowance can start.
    count=min(8, (policy['credit_limit']-state['reserved_credits'])//300)
    return result('ready', 'oldest_due_scopes', select_windows(policy, selected[:count]))


def main():
    from signalboard.twitterapi_state_store import GitBranchStore
    output = Path('recovery_output')
    output.mkdir(exist_ok=True)
    # Reset outputs before reading state so stale artifacts never authorize work.
    plan = {'status': 'stop', 'reason': 'invalid_or_unavailable_state',
            'selected_windows': [], 'production_changed': False, 'daily_promotion': False}
    output.joinpath('plan.json').write_text(json.dumps(plan, indent=2))
    output.joinpath('selected_windows.json').write_text('[]')
    try:
        policy = json.loads(Path('config/twitterapi_recovery_grant.json').read_text())
        plan = plan_next(GitBranchStore(Path.cwd()), expected_policy=policy,
                         now=datetime.now(timezone.utc).replace(microsecond=0))
    except Exception:
        # Never emit provider text, credentials, raw payloads or git errors.
        pass
    output.joinpath('plan.json').write_text(json.dumps(plan, indent=2))
    output.joinpath('selected_windows.json').write_text(json.dumps(plan['selected_windows']))
    if os.environ.get('GITHUB_OUTPUT'):
        with open(os.environ['GITHUB_OUTPUT'], 'a') as stream:
            stream.write('ready=' + ('true' if plan['status'] == 'ready' else 'false') + '\n')
    return 2 if plan['status'] == 'stop' else 0


if __name__ == '__main__':
    sys.exit(main())
