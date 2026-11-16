"""Offline atomic import of an explicitly reviewed, completed timeline cache.

Cached completion is evidence from the reviewed traversal, not inferred from zero
posts. Coverage describes this provider interval only; old historical gaps and
search checkpoints remain untouched. No transport, AI or publication occurs.
"""
from pathlib import Path
from signalboard.twitterapi_existing_post import reconcile_existing_source
from .db import get_conn
from .twitterapi_ingest import IngestError, _iso, _posts
from .twitterapi_recovery import HANDLES, utc


def ingest_timeline_cache(db_path, state, *, expected_operation, expected_start,
                          expected_end, captured_at):
    start,end=utc(expected_start),utc(expected_end)
    start_iso,end_iso,capture_iso=_iso(start),_iso(end),_iso(captured_at)
    if start>=end or captured_at<end or not isinstance(expected_operation,str) or not expected_operation:
        raise IngestError('invalid reviewed timeline scope')
    record=state.get('timeline_feasibility',{})
    if (record.get('operation')!=expected_operation or record.get('historical_gap_preserved') is not True
            or utc(record['start'])!=start or utc(record['end'])!=end):
        raise IngestError('cached timeline scope mismatch')
    attempts=record.get('attempts')
    if not isinstance(attempts,list) or len(attempts)!=len(HANDLES):
        raise IngestError('all eight completed accounts required')
    prepared=[];seen=set()
    for attempt in attempts:
        handle=attempt.get('handle')
        if not isinstance(handle,str) or handle.lower() not in {h.lower() for h in HANDLES} or handle.lower() in seen:
            raise IngestError('invalid or duplicate timeline account')
        seen.add(handle.lower())
        canonical=next(h for h in HANDLES if h.lower()==handle.lower())
        if (attempt.get('endpoint')!='last_tweets' or attempt.get('cursor')!='' or
                attempt.get('status')!='observed' or attempt.get('complete') is not True or
                attempt.get('reason') not in ('start_boundary_crossed','timeline_exhausted')):
            raise IngestError('completed reviewed timeline evidence required')
        rows=attempt.get('tweets')
        if not isinstance(rows,list):raise IngestError('invalid cached tweet list')
        posts=_posts(canonical,start,end,rows,capture_iso) if rows else []
        prepared.append((canonical,attempt['reason'],posts))
    if not Path(db_path).is_file():raise IngestError('initialized working database required')
    receipts=[]
    with get_conn(db_path) as conn:
        conn.execute('BEGIN IMMEDIATE')
        conn.execute('''CREATE TABLE IF NOT EXISTS twitterapi_timeline_coverage (
            handle TEXT NOT NULL, coverage_start TEXT NOT NULL, coverage_end TEXT NOT NULL,
            operation TEXT NOT NULL, provider TEXT NOT NULL, endpoint TEXT NOT NULL,
            completion_reason TEXT NOT NULL, verified_at TEXT NOT NULL,
            in_window_count INTEGER NOT NULL,
            PRIMARY KEY(handle,coverage_start,coverage_end))''')
        for handle,reason,posts in prepared:
            old=conn.execute('SELECT * FROM twitterapi_timeline_coverage WHERE handle=? AND coverage_start=? AND coverage_end=?',
                             (handle.lower(),start_iso,end_iso)).fetchone()
            if old and (old['operation']!=expected_operation or old['provider']!='twitterapi.io' or
                        old['endpoint']!='last_tweets' or old['completion_reason']!=reason or old['in_window_count']!=len(posts)):
                raise IngestError('existing timeline coverage conflicts with reviewed cache')
            receipt={'handle':handle,'new_persisted':0,'existing_preserved':0,'changed_originals_preserved':0,'context_promoted':0,
                     'in_window_count':len(posts),'coverage_start':start_iso,'coverage_end':end_iso,
                     'coverage_status':'provider_timeline_complete','summary_status':'not_requested'}
            for post in posts:
                prior=conn.execute('SELECT source_id,platform,raw_text,published_at,raw_json FROM raw_posts WHERE post_id=?',(post.post_id,)).fetchone()
                if prior:
                    receipt['context_promoted'] += int(reconcile_existing_source(conn,prior,post,capture_iso))
                    receipt['existing_preserved']+=1
                    if prior['raw_text']!=post.raw_text or prior['published_at']!=post.published_at:
                        receipt['changed_originals_preserved']+=1
                else:
                    conn.execute('''INSERT INTO raw_posts
                        (post_id,source_id,platform,published_at,captured_at,raw_text,raw_url,raw_json,content_hash,is_deleted,archive_url)
                        VALUES (:post_id,:source_id,:platform,:published_at,:captured_at,:raw_text,:raw_url,:raw_json,:content_hash,:is_deleted,:archive_url)''',post.to_row())
                    receipt['new_persisted']+=1
            if not old:
                conn.execute('INSERT INTO twitterapi_timeline_coverage VALUES (?,?,?,?,?,?,?,?,?)',
                             (handle.lower(),start_iso,end_iso,expected_operation,'twitterapi.io','last_tweets',reason,capture_iso,len(posts)))
            receipts.append(receipt)
    return {'accounts':receipts,'all_eight_complete':True,'historical_gap_preserved':True,
            'summary_status':'not_requested','publication_status':'not_requested'}


def replay_completed_timeline(db_path, state, *, captured_at):
    """Replay reviewed trial and contiguous daily cache, never fetch or infer gaps.

    Completed daily payloads are revalidated by the capture module. An incomplete
    later batch blocks the caller from claiming recovery/publication success.
    """
    from .twitterapi_timeline_daily import completed_attempts, START, EXPIRES
    receipts=[ingest_timeline_cache(db_path,state,
        expected_operation='timeline-feasibility-20261116',
        expected_start='2026-11-15T16:00:00+00:00',expected_end=START,captured_at=captured_at)]
    previous=START
    for batch in state.get('timeline_daily',[]):
        start,end=utc(batch['start']),utc(batch['end'])
        if start!=previous or end>EXPIRES:
            raise IngestError('noncontiguous daily timeline cache')
        attempts=completed_attempts(batch)
        record={'operation':'timeline-daily-'+_iso(start),'historical_gap_preserved':True,
                'start':start.isoformat(),'end':end.isoformat(),
                'attempts':[dict(a,endpoint='last_tweets',cursor='',status='observed') for a in attempts]}
        receipts.append(ingest_timeline_cache(db_path,{'timeline_feasibility':record},
            expected_operation=record['operation'],expected_start=start,expected_end=end,captured_at=captured_at))
        previous=end
    return {'intervals':receipts,'all_eight_complete':True,'historical_gap_preserved':True,
            'coverage_end':_iso(previous),'summary_status':'not_requested','publication_status':'not_requested'}


def main():
    import argparse
    import json
    from datetime import datetime,timezone
    parser=argparse.ArgumentParser(description='Replay reviewed cache into a backed-up working DB; no network')
    parser.add_argument('--state',required=True)
    parser.add_argument('--db',required=True)
    parser.add_argument('--receipt',required=True)
    args=parser.parse_args()
    result=replay_completed_timeline(args.db,json.loads(Path(args.state).read_text()),
        captured_at=datetime.now(timezone.utc).replace(microsecond=0))
    Path(args.receipt).write_text(json.dumps(result,indent=2))


if __name__=='__main__':
    main()
