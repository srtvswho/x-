#!/usr/bin/env python3
"""Review only ambiguous multi-security calls; never rerun post extraction."""
import argparse
from concurrent.futures import ThreadPoolExecutor,as_completed
import json
from pathlib import Path
import os
import sqlite3
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from signalboard.call_attribution import candidates,save,SYSTEM,SCHEMA,VERSION,validate
from signalboard.history_reuse import raw_hash
from signalboard.ai.router import call_json
from intel_history_backfill import write_report


def review_prompt(post, prior_error=None):
    saved=json.loads(post['raw_response'])
    data={'raw_post':post['raw_text'],'candidate_tickers':post['candidate_tickers'],
          'saved_summary':saved.get('summary_100'),'saved_claims':saved.get('claims',[])}
    if prior_error:
        # A semantic retry must not replay a SUCCESS-ledger request verbatim.
        data['previous_validation_error']=prior_error
        data['retry_instruction']='Correct the JSON contract; do not relax evidence requirements.'
    return json.dumps(data,ensure_ascii=False)


def remember_response(db, post, payload, error):
    # Keep paid responses even when semantic validation fails. Never overwrite
    # original post interpretations, manual reviews, or the cumulative ledger.
    with sqlite3.connect(db,timeout=30) as con:
        con.execute('''CREATE TABLE IF NOT EXISTS call_attribution_attempts (
            id INTEGER PRIMARY KEY, post_id TEXT, extraction_id INTEGER,
            raw_hash TEXT, version TEXT, payload TEXT, validation_error TEXT,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP)''')
        con.execute('''INSERT INTO call_attribution_attempts
            (post_id,extraction_id,raw_hash,version,payload,validation_error)
            VALUES(?,?,?,?,?,?)''', (post['post_id'],post['id'],raw_hash(post),VERSION,
            json.dumps(payload,ensure_ascii=False),error))


def batch_status(previous, selected_count, successes, remaining):
    canary_passed=previous.get('canary_passed',False)
    if not canary_passed and selected_count:
        canary_passed=successes / selected_count >= 0.8
    blocked=bool(remaining and (not successes or not canary_passed or
                 (selected_count and successes / selected_count < 0.5)))
    return canary_passed, blocked


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--db',default='/workspace/data/signalboard_full.db')
    p.add_argument('--apply',action='store_true')
    p.add_argument('--daily',action='store_true',help='Use the existing daily extraction budget')
    p.add_argument('--limit',type=int,default=200)
    p.add_argument('--report',default='outputs/call_attribution_review.json')
    args=p.parse_args()
    with sqlite3.connect(args.db) as con:
        pending=candidates(con)
    if not args.apply:
        write_report(args.report,{'version':VERSION,'pending':len(pending),'selected':[p['post_id'] for p in pending[:args.limit]]})
        return
    config=json.loads(Path('config/history_repair_campaign.json').read_text())
    if not args.daily and os.getenv('AI_RUN_ID')!=config['campaign_id']:
        raise SystemExit('Stable campaign budget ID required')
    previous=json.loads(Path(args.report).read_text()) if Path(args.report).exists() else {}
    if previous.get('version')!=VERSION:
        previous={}
    attempts=dict(previous.get('failed_attempts',{}))
    untouched=[p for p in pending if not attempts.get(p['post_id'])]
    limit=args.limit if previous.get('canary_passed') else min(args.limit,6)
    selected=(untouched or [p for p in pending if attempts.get(p['post_id'],0)<2])[:limit]
    errors={}; successes=[]
    def review(post):
        prior_error=(previous.get('errors',{}).get(post['post_id']) or
                     'Prior response failed validation') if attempts.get(post['post_id']) else None
        prompt=review_prompt(post,prior_error)
        result=call_json('bulk_post_processing',SYSTEM,prompt,SCHEMA,
            max_output_tokens=1600,max_output_tokens_ceiling=6400,max_retries=2,
            prompt_version=VERSION,entity_type='per_security_review',entity_id=post['post_id'])
        error=None
        try:
            validate(result.data,post)
        except Exception as exc:
            error=f'{type(exc).__name__}: {exc}'
            raise
        finally:
            remember_response(args.db,post,result.data,error)
        return result.data
    with ThreadPoolExecutor(max_workers=6) as pool:
        futures={pool.submit(review,post):post for post in selected}
        for future in as_completed(futures):
            post=futures[future]
            try:
                payload=future.result()
                with sqlite3.connect(args.db,timeout=30) as con: save(con,post,payload)
                successes.append(post['post_id'])
                attempts.pop(post['post_id'],None)
            except Exception as e:
                errors[post['post_id']]=f'{type(e).__name__}: {e}'
                attempts[post['post_id']]=attempts.get(post['post_id'],0)+1
    with sqlite3.connect(args.db) as con: remaining=len(candidates(con))
    canary_passed,blocked=batch_status(previous,len(selected),len(successes),remaining)
    report={'version':VERSION,'pending':remaining,'resolved':len(successes),
            'selected_count':len(selected),'canary_passed':canary_passed,
            'status':'blocked' if blocked else 'pending' if remaining else 'completed',
            'errors':errors,'failed_attempts':attempts}
    write_report(args.report,report)
    if blocked and not args.daily:
        campaign_path=Path('outputs/history_repair_campaign.json')
        campaign=json.loads(campaign_path.read_text()) if campaign_path.exists() else {}
        campaign.update(campaign_id=config['campaign_id'],
            repair_revision=config['repair_revision'],campaign_status='blocked',
            blocked_reason='per_security_review_validation_failed',
            per_security_review_pending=remaining,stored_history_call_review_complete=False)
        write_report(campaign_path,campaign)
    print(json.dumps(report,ensure_ascii=False),flush=True)
    if blocked:raise SystemExit('Per-security review blocked; successes and paid responses persisted')


if __name__=='__main__':main()
