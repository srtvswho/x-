"""Disabled-by-default candidate runner. No default-branch writes or publication.

A preexisting reviewed state branch/config is required. Never creates/renews grants.
This script cannot be used to turn the smoke exception into standing authorization.
"""
from copy import deepcopy
import hashlib
import json
import os
from pathlib import Path
import sys
from datetime import datetime, timezone
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from signalboard.twitterapi_io import Client, FetchError
from signalboard.twitterapi_recovery import HANDLES, utc
from signalboard.twitterapi_ingest import get_coverage, ingest_window


def check_config(config, env, now):
    expected=hashlib.sha256(json.dumps(config,sort_keys=True,separators=(',',':')).encode()).hexdigest()
    if env.get('RECOVERY_ENABLED')!='true' or env.get('GITHUB_EVENT_NAME')!='workflow_dispatch' or env.get('GITHUB_REF')!='refs/heads/recovery/twitterapi-free':
        raise ValueError('disabled or wrong execution scope')
    if env.get('AI_ENABLED')!='false' or env.get('ALLOW_EXPENSIVE_AI_JOB')!='false' or env.get('AI_DRY_RUN')!='true':
        raise ValueError('AI flags must remain disabled')
    if env.get('RECOVERY_CONFIG_SHA256')!=expected or env.get('RECOVERY_GRANT_ID')!=config.get('grant_id'):
        raise ValueError('reviewed configuration identity mismatch')
    if config.get('no_payment_instrument_verified') is not True or config.get('bonus_only') is not True:
        raise ValueError('bonus-only/no-payment proof required')
    from signalboard.twitterapi_paging import select_windows
    if now >= utc(config['expires_at']):
        raise ValueError('grant expired')
    if config.get('bonus_expires_at') and now >= utc(config['bonus_expires_at']):
        raise ValueError('verified bonus expired')
    if (type(config.get('credit_limit')) is not int or
            not 300 <= config['credit_limit'] <= min(30000, config.get('verified_bonus_credits', 0))):
        raise ValueError('invalid bounded grant')
    if (config.get('preflight_mode') != 'dashboard_evidence' or
            type(config.get('recharge_credits')) is not int or config['recharge_credits'] != 0 or
            config.get('max_balance_reads') != 0):
        raise ValueError('zero-recharge dashboard evidence and zero balance calls required')
    if not 1 <= config.get('max_pages_per_window', 0) <= 10:
        raise ValueError('bounded per-account page cap required')
    if config.get('mode') not in ('daily', 'catchup', 'recovery'):
        raise ValueError('explicit recovery mode required')
    all_windows=config.get('windows', [])
    if not all_windows:
        raise ValueError('immutable full grant windows required')
    for w in all_windows:
        a,b=utc(w['start']),utc(w['end'])
        if w['handle'].lower() not in {h.lower() for h in HANDLES} or not 0 < (b-a).total_seconds() <= 86400 or a.microsecond or b.microsecond:
            raise ValueError('invalid approved window')
    selected=json.loads(env.get('RECOVERY_SELECTED_WINDOWS', 'null'))
    windows=select_windows(config, selected)
    if any(utc(w['end']) > now for w in windows):
        raise ValueError('selected future window')
    return windows


def main():
    # Delayed imports: offline config tests need no store/network initialization.
    from signalboard.twitterapi_state_store import GitBranchStore
    from signalboard.twitterapi_paging import advance_page, cached_window
    store=GitBranchStore(Path.cwd())
    state,revision=store.load()  # Missing branch/config is a blocker, never an initializer.
    config=state['config']
    now=datetime.now(timezone.utc).replace(microsecond=0)
    windows=check_config(config,os.environ,now)
    db='recovery_output/working.db'
    if not Path(db).is_file():
        raise ValueError('working snapshot missing')
    # Recovery catch-up stays separate. Daily promotion is deliberately not
    # inferred from latest post timestamps or a partially exhausted account.
    stream='catchup' if config['mode']=='recovery' else config['mode']
    receipts=[];replayed=[];steps=0;stop_reason=None;client=None
    class Snapshot:
        def load(self):return deepcopy(state), revision
    snapshot=Snapshot()
    def require_contiguous(spec, coverage):
        start,end=utc(spec['start']),utc(spec['end'])
        earliest=min(utc(w['start']) for w in config['windows'] if w['handle'].lower()==spec['handle'].lower())
        if not coverage:
            if stream=='daily' or start!=earliest:
                raise ValueError('verified contiguous predecessor required before request')
        elif start > utc(coverage['coverage_end']) or start < utc(coverage['coverage_start']):
            raise ValueError('coverage gap or backward extension before request')
    def apply(spec, window):
        handle=next(h for h in HANDLES if h.lower()==spec['handle'].lower())
        start,end=utc(spec['start']),utc(spec['end'])
        coverage=get_coverage(db,handle,stream)
        if coverage and utc(coverage['coverage_start']) <= start and utc(coverage['coverage_end']) >= end:
            return {'handle':handle,'coverage_status':'already_covered','checkpoint_changed':False,
                    'summary_status':'not_requested'}
        require_contiguous(spec,coverage)
        if stream=='daily' and (not coverage or utc(coverage['coverage_end'])!=start):
            raise ValueError('daily coverage not ready; reviewed contiguous promotion required')
        return ingest_window(db,handle,start,end,window,
            captured_at=datetime.now(timezone.utc).replace(microsecond=0),stream=stream,
            expected_coverage_end=coverage['coverage_end'] if coverage else None)
    try:
        # Reconstruct all prior complete grant windows on each fresh snapshot.
        # The immutable cache retains original payloads; incomplete windows never
        # write data or coverage, and original rows remain insert-only.
        for spec in sorted(config['windows'],key=lambda w:(w['handle'].lower(),utc(w['start']))):
            window=cached_window(snapshot,spec['handle'],utc(spec['start']),utc(spec['end']),expected_policy=config)
            if window.complete:
                replayed.append(apply(spec,window))
        for spec in windows:
            start,end=utc(spec['start']),utc(spec['end'])
            window=cached_window(snapshot,spec['handle'],start,end,expected_policy=config)
            coverage=get_coverage(db,spec['handle'],stream)
            require_contiguous(spec,coverage)
            if stream=='daily':
                if not coverage or utc(coverage['coverage_end']) not in (start,end):
                    raise ValueError('daily coverage not ready before request')
            for _ in range(config['max_pages_per_window']):
                if window.complete or window.reason in ('uncertain','empty_unverified','page_cap_partial'):
                    break
                if client is None:
                    client=Client(os.environ.get('TWITTERAPI_IO_KEY'))
                    client.deadline=utc(config['expires_at'])
                # No balance endpoint: its tariff is unknown. Explicit dashboard
                # proof plus immutable all-API cap is required by check_config.
                window=advance_page(client,store,spec['handle'],start,end,
                    now=datetime.now(timezone.utc).replace(microsecond=0),expected_policy=config)
                steps+=1
            receipts.append(apply(spec,window))
            if not window.complete:
                stop_reason=window.reason
                break
    except Exception:
        stop_reason='blocked_or_uncertain'
        raise
    finally:
        Path('recovery_output/receipt.json').write_text(json.dumps({'accounts':receipts,
            'replayed':replayed,'stop_reason':stop_reason,
            'page_step_attempts':steps,'production_changed':False,'summary_status':'not_requested',
            'publication_status':'not_requested','bonus_delta':'not_observable_from_dashboard_evidence'},indent=2))
    return 0 if len(receipts)==len(windows) and stop_reason is None else 2

if __name__=='__main__':
    try:sys.exit(main())
    except Exception:
        # Do not leak provider messages, repo credentials, requests or raw content.
        print('Recovery blocked/failed; inspect durable state and receipt before any retry.')
        sys.exit(1)
