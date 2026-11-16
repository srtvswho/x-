from datetime import datetime,timezone
import json,os,sqlite3,subprocess,sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from signalboard.twitterapi_state_store import GitBranchStore
from signalboard.twitterapi_timeline_ingest import replay_completed_timeline
from signalboard.twitterapi_timeline_daily import plan,run_daily,completed_attempts
from signalboard.twitterapi_paging import _check_state
from signalboard.twitterapi_io import Client
from signalboard.twitterapi_history_ingest import ingest_completed_history

def main():
    e=os.environ
    if (e.get('GITHUB_REPOSITORY')!='srtvswho/x-' or e.get('GITHUB_REF')!='refs/heads/master' or e.get('GITHUB_EVENT_NAME') not in ('push','schedule') or
        e.get('GITHUB_WORKFLOW_REF')!='srtvswho/x-/.github/workflows/twitterapi-finite-recovery.yml@refs/heads/master' or
        e.get('AI_ENABLED')!='false' or e.get('ALLOW_EXPENSIVE_AI_JOB')!='false' or e.get('AI_DRY_RUN')!='true' or
        subprocess.check_output(['git','rev-parse','HEAD'],text=True).strip()!=e.get('GITHUB_SHA')):raise ValueError('execution gate')
    now=datetime.now(timezone.utc).replace(microsecond=0)
    store=GitBranchStore(Path.cwd());state,revision=store.load();_check_state(state,state['config'])
    for batch in state.get('timeline_daily',[]):completed_attempts(batch)
    selection=plan(state,now)
    if selection['status'] in ('expired','blocked_previous_attempt','budget_stop'):raise ValueError(selection['status'])
    if e['GITHUB_EVENT_NAME']=='schedule' and selection['status']=='ready':
        result=run_daily(Client(e.get('TWITTERAPI_IO_KEY')),store,now=now)
        if result['status']!='complete':raise ValueError('daily stopped')
        state,revision=store.load();_check_state(state,state['config'])
    db='data/signalboard_full.db'
    with sqlite3.connect(db) as c:
        before=c.execute("SELECT count(*) FROM sqlite_master WHERE type='table' AND name='twitterapi_timeline_coverage'").fetchone()[0]
        count=c.execute('SELECT count(*) FROM twitterapi_timeline_coverage').fetchone()[0] if before else 0
    result=replay_completed_timeline(db,state,captured_at=now)
    history=state.get('timeline_history',{}).get('accounts',{})
    if len(history)==8 and all(a.get('status')=='complete' for a in history.values()):
        result['historical_ingest']=ingest_completed_history(db,state,captured_at=now)
    with sqlite3.connect(db) as c:
        after=c.execute('SELECT count(*) FROM twitterapi_timeline_coverage').fetchone()[0]
        if c.execute('PRAGMA integrity_check').fetchone()[0]!='ok':raise ValueError('database integrity')
    changed=(after!=count or any(a['new_persisted'] for r in result['intervals'] for a in r['accounts'])
             or any(a['new_persisted'] for a in result.get('historical_ingest',{}).get('accounts',[])))
    Path('recovery_output').mkdir(exist_ok=True)
    Path('recovery_output/ingest_receipt.json').write_text(json.dumps({'state_revision':revision,'ingest':result,'publish_needed':changed,'selection':selection['status']},indent=2))
    with open(e['GITHUB_OUTPUT'],'a') as f:f.write('publish='+str(changed).lower()+'\n')
if __name__=='__main__':
    try:main()
    except Exception:
        print('Timeline recovery stopped; no retry or partial publication.');sys.exit(1)
