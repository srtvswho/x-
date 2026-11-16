"""One explicitly authorized observation. Never resolves the original uncertain page.

Keeps prior evidence byte-for-byte equivalent in JSON; generic scheduler remains
blocked. Durable extra reservation is never refunded and forbids a second call.
"""
from copy import deepcopy
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from signalboard.twitterapi_io import Client, FetchError
from signalboard.twitterapi_paging import _check_state, _utc, _validated_rows
from signalboard.twitterapi_state_store import GitBranchStore

EXPECTED_REVISION='550f29844c8fc676cc922945dad9bd13255890de'
SCOPE=['aleabitoreddit','2026-11-11T16:00:00+00:00','2026-11-12T16:00:00+00:00']
OPERATION='page2-observation-once-20261115'
CONFIG_SHA='7f69ddfd026f5c68fadb74b6c4b312b75d2893f0b06d04dd72848df35ace1756'

def observe(store,client_factory,now,receipt_path):
    state,revision=store.load()
    if revision!=EXPECTED_REVISION or 'one_time_observation' in state:
        raise FetchError('original revision changed or one-time observation already reserved; no call')
    config=state['config'];_check_state(state,config)
    digest=hashlib.sha256(json.dumps(config,sort_keys=True,separators=(',',':')).encode()).hexdigest()
    if digest!=CONFIG_SHA or config.get('bonus_only') is not True or config.get('recharge_credits')!=0 or config.get('no_payment_instrument_verified') is not True or config.get('max_balance_reads')!=0:
        raise FetchError('bonus proof/config mismatch')
    if now>=_utc(config['expires_at']) or state['reserved_credits']!=600 or state['reserved_credits']+300>min(config['credit_limit'],30000):
        raise FetchError('expiry or quota mismatch')
    if len(state['windows'])!=1:raise FetchError('unexpected window state')
    entry=next(iter(state['windows'].values()))
    if entry['scope']!=SCOPE or entry['status']!='uncertain' or len(entry['pages'])!=1 or entry['pending']['page']!=2 or not entry['cursor']:
        raise FetchError('exact uncertain second page required')
    new=deepcopy(state)
    record={'operation':OPERATION,'original_revision':revision,'prior_reserved_credits':600,'credits':300,
            'status':'reserved_uncertain','reserved_at':now.isoformat(),'scope':SCOPE,
            'request_cursor':entry['cursor'],'original_pending':deepcopy(entry['pending'])}
    new['one_time_observation']=record;new['reserved_credits']=900
    reserved=store.save(new,revision)
    receipt={'operation':OPERATION,'reserved_credits':900,'original_stop_preserved':True,'provider_attempts':0,'production_changed':False,'summary_status':'not_requested'}
    stage='before_transport';success=False
    try:
        if datetime.now(timezone.utc)>=_utc(config['expires_at']):raise FetchError('expired')
        client=client_factory();client.deadline=_utc(config['expires_at'])
        stage='transport_or_json';receipt['provider_attempts']=1
        start,end=map(_utc,SCOPE[1:])
        data=client.get('/twitter/tweet/advanced_search',{'query':f'from:{SCOPE[0]} since_time:{int(start.timestamp())} until_time:{int(end.timestamp())}','queryType':'Latest','cursor':entry['cursor']})
        stage='schema'
        rows=data.get('tweets');more=data.get('has_next_page');cursor=data.get('next_cursor')
        if not isinstance(rows,list) or len(rows)>20 or type(more) is not bool or not isinstance(cursor,str):raise FetchError('schema')
        terminal=not more or not cursor or cursor==entry['cursor']
        # Validate original posts independently of documented terminal cursor shape.
        valid=_validated_rows({'tweets':rows,'has_next_page':False,'next_cursor':''},SCOPE[0],start,end)
        response={'tweets':valid,'has_next_page':more,'next_cursor':cursor}
        record.update(status='observed',response=response,terminal_signal=terminal)
        receipt.update(status='observed',tweet_count=len(valid),terminal_signal=terminal)
        stage='persistence';store.save(new,reserved);success=True
    except Exception:
        # Only fixed stage labels, never exception text, raw errors, request headers.
        receipt.update(status='uncertain',failure_stage=stage)
        if stage!='persistence':
            record.update(status='failed',failure_stage=stage)
            try:store.save(new,reserved)
            except Exception:receipt['diagnostic_persistence']='unconfirmed'
    finally:
        Path(receipt_path).parent.mkdir(parents=True,exist_ok=True)
        Path(receipt_path).write_text(json.dumps(receipt,indent=2))
    return success

def main():
    e=os.environ
    if (e.get('GITHUB_REPOSITORY')!='srtvswho/x-' or e.get('GITHUB_REF')!='refs/heads/master' or e.get('GITHUB_EVENT_NAME')!='push' or
        e.get('GITHUB_WORKFLOW_REF')!='srtvswho/x-/.github/workflows/twitterapi-finite-recovery.yml@refs/heads/master' or
        e.get('AI_ENABLED')!='false' or e.get('ALLOW_EXPENSIVE_AI_JOB')!='false' or e.get('AI_DRY_RUN')!='true' or
        subprocess.check_output(['git','rev-parse','HEAD'],text=True).strip()!=e.get('RECOVERY_CODE_SHA')):
        raise FetchError('execution gate rejected')
    return 0 if observe(GitBranchStore(Path.cwd()),lambda:Client(e.get('TWITTERAPI_IO_KEY')),datetime.now(timezone.utc).replace(microsecond=0),'recovery_output/one_reread_receipt.json') else 2
if __name__=='__main__':
    try:sys.exit(main())
    except Exception:
        print('One-time observation blocked; no automatic retry.');sys.exit(1)
