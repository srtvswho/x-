"""Reviewed one-off raw-only catchup. No AI, DB ingestion or publication."""
import json
import hashlib
import os
from pathlib import Path
import re
import sqlite3
import subprocess
import sys
from datetime import datetime,timezone
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from signalboard.twitterapi_timeline_history import BOUNDARIES,HANDLES,initialize_history,run_history,utc


LEGACY_STATE_SHA256 = 'ebbf96f4822306e496f7edcd613bef8f6387c4d0daee53b8611ce3bfc9d37513'

def gate(env,head):
    if (env.get('GITHUB_REPOSITORY')!='srtvswho/x-' or env.get('GITHUB_EVENT_NAME')!='push' or
        env.get('GITHUB_REF')!='refs/heads/master' or
        env.get('GITHUB_RUN_ATTEMPT')!='1' or env.get('HISTORY_RAW_ONLY_APPROVED')!='true' or
        not re.fullmatch('[0-9a-f]{40}',env.get('HISTORY_REVIEWED_HEAD','')) or head!=env['HISTORY_REVIEWED_HEAD'] or
        env.get('AI_ENABLED')!='false' or env.get('ALLOW_EXPENSIVE_AI_JOB')!='false' or env.get('AI_DRY_RUN')!='true' or
        env.get('GITHUB_WORKFLOW_REF')!='srtvswho/x-/.github/workflows/twitterapi-history-recovery.yml@refs/heads/master'):
        raise ValueError('history_execution_not_approved')


def verify_database(path):
    con=sqlite3.connect('file:'+str(Path(path).resolve())+'?mode=ro',uri=True)
    try:observed={h.lower():v for h,v in con.execute('SELECT handle,last_fetched_at FROM scrape_state')}
    finally:con.close()
    if any(h not in observed or utc(observed[h])!=utc(t) for h,t in BOUNDARIES.items()):
        raise ValueError('canonical_checkpoint_mismatch')
    return dict(BOUNDARIES)


def run(store,client_factory,db,*,now,clock=None):
    boundaries=verify_database(db)
    state,_=store.load()
    legacy_digest=hashlib.sha256(json.dumps({k:state.get(k) for k in ('config','windows','one_time_observation','timeline_feasibility')},sort_keys=True,separators=(',',':')).encode()).hexdigest()
    if legacy_digest!=LEGACY_STATE_SHA256:raise ValueError('canonical_legacy_state_mismatch')
    if not 3420 <= state.get('reserved_credits',-1) <= 30000:raise ValueError('shared_accounting_floor')
    if 'timeline_history' not in state:
        # Existing filtered feasibility tweets are already ingested; no cursor
        # can be reconstructed from them. This is a new authorized first capture.
        initialize_history(store,{h:[] for h in HANDLES},boundaries)
    return run_history(client_factory(),store,now=now,clock=clock,max_steps=36)


def main():
    head=subprocess.check_output(['git','rev-parse','HEAD'],text=True).strip()
    gate(os.environ,head)
    from signalboard.twitterapi_state_store import GitBranchStore
    from signalboard.twitterapi_io import Client
    result=run(GitBranchStore(Path.cwd()),lambda:Client(os.environ.get('TWITTERAPI_IO_KEY')),
               os.environ['SIGNALBOARD_DB'],now=datetime.now(timezone.utc).replace(microsecond=0))
    # Never print raw bodies, credentials or tweet text. State holds cached pages.
    receipt={k:v for k,v in result.items() if k in ('status','reason','handle','steps','ready_for_offline_ingest')}
    receipt.update(ai_calls=0,database_changed=False,production_changed=False)
    Path('recovery_output').mkdir(exist_ok=True)
    Path('recovery_output/history_receipt.json').write_text(json.dumps(receipt,indent=2))
    print(json.dumps(receipt))
    return 0 if result['status']=='complete' else 2
if __name__=='__main__':
    try:raise SystemExit(main())
    except Exception:
        print('{"status":"history_failed_closed","ai_calls":0,"production_changed":false}')
        raise SystemExit(2) from None
