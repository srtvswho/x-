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
from signalboard.ai.router import call_json
from intel_history_backfill import write_report


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
    attempts=previous.get('failed_attempts',{}) if previous.get('version')==VERSION else {}
    untouched=[p for p in pending if not attempts.get(p['post_id'])]
    selected=(untouched or [p for p in pending if attempts.get(p['post_id'],0)<2])[:args.limit]
    errors={}; successes=[]
    def review(post):
        saved=json.loads(post['raw_response'])
        prompt=json.dumps({'raw_post':post['raw_text'],'candidate_tickers':post['candidate_tickers'],
            'saved_summary':saved.get('summary_100'),'saved_claims':saved.get('claims',[])},ensure_ascii=False)
        result=call_json('bulk_post_processing',SYSTEM,prompt,SCHEMA,
            max_output_tokens=1600,max_output_tokens_ceiling=6400,max_retries=2,
            prompt_version=VERSION,entity_type='per_security_review',entity_id=post['post_id'])
        validate(result.data,post)
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
    report={'version':VERSION,'pending':remaining,'resolved':len(successes),'errors':errors,'failed_attempts':attempts}
    write_report(args.report,report)
    print(json.dumps(report,ensure_ascii=False),flush=True)
    if remaining and not successes:raise SystemExit('Per-security review incomplete; successes persisted')


if __name__=='__main__':main()
