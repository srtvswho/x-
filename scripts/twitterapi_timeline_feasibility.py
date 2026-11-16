"""One bounded new-period feasibility pass. No publication or retries."""
from copy import deepcopy
from datetime import datetime,timezone
import json,os,subprocess,sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from signalboard.twitterapi_io import Client,FetchError
from signalboard.twitterapi_state_store import GitBranchStore
from signalboard.twitterapi_recovery import HANDLES,utc
from signalboard.twitterapi_timeline import accumulate,TimelineError

EXPECTED='767064a66569714626f0cafbc5a146b0a36c02a7'
OP='timeline-feasibility-20261116'
START=datetime(2026,11,15,16,tzinfo=timezone.utc)

def run(store,client_factory,now,out):
    state,revision=store.load()
    if revision!=EXPECTED or 'timeline_feasibility' in state:raise FetchError('changed ledger; no call')
    config=state['config']
    if (state['reserved_credits']!=900 or config['credit_limit']!=30000 or
        config['expires_at']!='2026-11-22T08:10:00+00:00' or config.get('bonus_only') is not True or
        config.get('no_payment_instrument_verified') is not True or config.get('recharge_credits')!=0 or config.get('max_balance_reads')!=0 or
        not START<now<=datetime(2026,11,16,16,tzinfo=timezone.utc) or now>=utc(config['expires_at'])):raise FetchError('grant mismatch')
    state=deepcopy(state)
    record={'operation':OP,'historical_gap_preserved':True,'start':START.isoformat(),'end':now.isoformat(),'attempts':[],'status':'running'}
    state['timeline_feasibility']=record
    receipt={'operation':OP,'accounts':[],'production_changed':False,'summary_status':'not_requested','historical_gap_preserved':True}
    client=None
    for handle in HANDLES:
        if state['reserved_credits']+315>30000 or datetime.now(timezone.utc)>=utc(config['expires_at']):
            record['status']='quota_or_expiry_stop';break
        attempt={'handle':handle,'credits':315,'status':'pending','endpoint':'last_tweets','cursor':''}
        record['attempts'].append(attempt);state['reserved_credits']+=315
        revision=store.save(state,revision)
        stage='transport_or_json'
        try:
            if client is None:client=client_factory();client.deadline=utc(config['expires_at'])
            data=client.get('/twitter/user/last_tweets',{'userName':handle,'includeReplies':'true','cursor':''})
            stage='validation'
            result=accumulate([data],handle,START,now)
            attempt.update(status='observed',complete=result.complete,reason=result.reason,tweets=result.tweets)
            receipt['accounts'].append({'handle':handle,'complete':result.complete,'reason':result.reason,'tweets':len(result.tweets)})
            if not result.complete:record['status']='incomplete_stop'
            stage='persistence';revision=store.save(state,revision)
            if not result.complete:break
        except Exception as exc:
            reason=exc.code if isinstance(exc,TimelineError) else stage
            receipt['accounts'].append({'handle':handle,'complete':False,'reason':reason})
            if stage!='persistence':
                attempt.update(status='failed',reason=reason);record['status']='failed_stop'
                try:revision=store.save(state,revision)
                except Exception:pass
            break
    success=len(receipt['accounts'])==8 and all(x['complete'] for x in receipt['accounts'])
    receipt.update(all_eight_complete=success,reserved_credits=state['reserved_credits'])
    Path(out).parent.mkdir(parents=True,exist_ok=True);Path(out).write_text(json.dumps(receipt,indent=2))
    return success

def main():
    e=os.environ
    if (e.get('GITHUB_REPOSITORY')!='srtvswho/x-' or e.get('GITHUB_REF')!='refs/heads/master' or e.get('GITHUB_EVENT_NAME')!='push' or
        e.get('GITHUB_WORKFLOW_REF')!='srtvswho/x-/.github/workflows/twitterapi-finite-recovery.yml@refs/heads/master' or
        e.get('AI_ENABLED')!='false' or e.get('ALLOW_EXPENSIVE_AI_JOB')!='false' or e.get('AI_DRY_RUN')!='true' or
        subprocess.check_output(['git','rev-parse','HEAD'],text=True).strip()!=e.get('RECOVERY_CODE_SHA')):raise FetchError('execution gate rejected')
    return 0 if run(GitBranchStore(Path.cwd()),lambda:Client(e.get('TWITTERAPI_IO_KEY')),datetime.now(timezone.utc).replace(microsecond=0),'recovery_output/timeline_receipt.json') else 2
if __name__=='__main__':
    try:sys.exit(main())
    except Exception:
        print('Timeline feasibility stopped; no retry.');sys.exit(1)
