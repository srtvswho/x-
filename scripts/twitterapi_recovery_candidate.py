"""Disabled-by-default candidate runner. No default-branch writes or publication.

A preexisting reviewed state branch/config is required. Never creates/renews grants.
This script cannot be used to turn the smoke exception into standing authorization.
"""
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
    if now>=utc(config['expires_at']) or now>=utc(config['bonus_expires_at']):
        raise ValueError('grant or verified bonus expired')
    if type(config.get('credit_limit')) is not int or not 300<=config['credit_limit']<=config.get('verified_bonus_credits',0):
        raise ValueError('invalid bounded grant')
    if type(config.get('max_balance_reads')) is not int or not 1<=config['max_balance_reads']<=16:
        raise ValueError('explicit balance request cap required')
    if config.get('mode') not in ('daily','catchup'):
        raise ValueError('explicit recovery mode required')
    windows=config.get('windows',[])
    if not isinstance(windows,list) or not 1<=len(windows)<=8:
        raise ValueError('explicit bounded windows required')
    seen=set()
    for w in windows:
        h=w['handle'];a,b=utc(w['start']),utc(w['end'])
        if h.lower() not in {x.lower() for x in HANDLES} or h.lower() in seen or not 0<(b-a).total_seconds()<=86400 or b>now:
            raise ValueError('invalid or duplicate approved window')
        if a.microsecond or b.microsecond:
            raise ValueError('whole seconds required')
        seen.add(h.lower())
    return windows


def main():
    # Delayed imports: offline config tests need no store/network initialization.
    from signalboard.twitterapi_state_store import GitBranchStore
    from signalboard.twitterapi_paging import advance_page, cached_window, balance_preflight
    store=GitBranchStore(Path.cwd())
    state,revision=store.load()  # Missing branch/config is a blocker, never an initializer.
    config=state['config']
    now=datetime.now(timezone.utc).replace(microsecond=0)
    windows=check_config(config,os.environ,now)
    cached=[cached_window(store,w['handle'],utc(w['start']),utc(w['end']),expected_policy=config) for w in windows]
    if any(w.reason=='uncertain' for w in cached):
        raise FetchError('uncertain page requires reconciliation before preflight')
    needs_request=any(not w.complete and w.reason not in ('empty_unverified','page_cap_partial') for w in cached)
    if not Path('recovery_output/working.db').is_file():
        raise ValueError('working snapshot missing')
    for spec in windows:
        handle=next(h for h in HANDLES if h.lower()==spec['handle'].lower())
        coverage=get_coverage('recovery_output/working.db',handle,config['mode'])
        if config['mode']=='daily' and (not coverage or utc(coverage['coverage_end'])!=utc(spec['start'])):
            raise ValueError('daily coverage not ready before preflight')
    client=None
    if needs_request:
        client=Client(os.environ.get('TWITTERAPI_IO_KEY'))
        balance_preflight(client,store,expected_policy=config)
    receipts=[];steps=0
    try:
        for spec in windows:
            handle=next(h for h in HANDLES if h.lower()==spec['handle'].lower());start,end=utc(spec['start']),utc(spec['end'])
            coverage=get_coverage('recovery_output/working.db',handle,config['mode'])
            if config['mode']=='daily' and (not coverage or utc(coverage['coverage_end'])!=start):
                raise ValueError('daily requires matching verified coverage; use reviewed catchup')
            # At most two new pages/account and 16 for this invocation. The durable
            # grant and cached cursor survive subsequent explicitly authorized runs.
            for _ in range(2):
                if steps>=16:break
                window=advance_page(client,store,handle,start,end,now=datetime.now(timezone.utc).replace(microsecond=0),expected_policy=config)
                steps+=1
                if window.complete or window.reason in ('empty_unverified',):break
            coverage=get_coverage('recovery_output/working.db',handle,config['mode'])
            receipt=ingest_window('recovery_output/working.db',handle,start,end,window,
                captured_at=datetime.now(timezone.utc).replace(microsecond=0),stream=config['mode'],
                expected_coverage_end=coverage['coverage_end'] if coverage else None)
            receipts.append(receipt)
    finally:
        Path('recovery_output').mkdir(exist_ok=True)
        Path('recovery_output/receipt.json').write_text(json.dumps({'accounts':receipts,
            'page_step_attempts':steps,'production_changed':False,'summary_status':'not_requested',
            'publication_status':'not_requested','bonus_delta':'not_observable_from_recharge_endpoint'},indent=2))
    return 0 if len(receipts)==len(windows) and all(r['checkpoint_changed'] for r in receipts) else 2

if __name__=='__main__':
    try:sys.exit(main())
    except Exception:
        # Do not leak provider messages, repo credentials, requests or raw content.
        print('Recovery blocked/failed; inspect durable state and receipt before any retry.')
        sys.exit(1)
