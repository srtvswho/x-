"""Offline all-account historical timeline import; no network or publication.

Only exact independently revalidated per-account intervals are marked covered.
Earlier unverified history and all search/scrape checkpoints remain unchanged.
"""
from pathlib import Path
from signalboard.twitterapi_existing_post import reconcile_existing_source
from signalboard.db import get_conn
from signalboard.twitterapi_ingest import IngestError,_iso,_posts
from signalboard.twitterapi_recovery import HANDLES as CANONICAL,utc
from signalboard.twitterapi_timeline_history import completed_attempts,BOUNDARIES,END,OPERATION


def ingest_completed_history(db_path,state,*,captured_at):
    capture_iso=_iso(captured_at)
    # This validates journal accounting, immutable boundaries, raw provider pages,
    # chronological traversal and complete evidence for EVERY account first.
    attempts=completed_attempts(state)
    if len(attempts)!=8 or {a['handle'].lower() for a in attempts}!=set(BOUNDARIES):
        raise IngestError('all eight distinct historical accounts required')
    prepared=[]
    for a in attempts:
        handle=next(h for h in CANONICAL if h.lower()==a['handle'].lower())
        start,end=utc(a['start']),utc(a['end'])
        if start!=utc(BOUNDARIES[handle.lower()]) or end!=utc(END) or captured_at<end:
            raise IngestError('historical scope mismatch')
        if a.get('complete') is not True or a.get('reason') not in ('start_boundary_crossed','timeline_exhausted'):
            raise IngestError('historical completion evidence required')
        rows=a.get('tweets')
        if not isinstance(rows,list):raise IngestError('invalid historical cached tweets')
        posts=_posts(handle,start,end,rows,capture_iso) if rows else []
        prepared.append((handle,_iso(start),_iso(end),a['reason'],posts))
    if not Path(db_path).is_file():raise IngestError('initialized working copy required')
    receipts=[]
    with get_conn(db_path) as conn:
        conn.execute('BEGIN IMMEDIATE')
        conn.execute('''CREATE TABLE IF NOT EXISTS twitterapi_timeline_coverage (
            handle TEXT NOT NULL, coverage_start TEXT NOT NULL, coverage_end TEXT NOT NULL,
            operation TEXT NOT NULL, provider TEXT NOT NULL, endpoint TEXT NOT NULL,
            completion_reason TEXT NOT NULL, verified_at TEXT NOT NULL,
            in_window_count INTEGER NOT NULL, PRIMARY KEY(handle,coverage_start,coverage_end))''')
        for handle,start,end,reason,posts in prepared:
            old=conn.execute('SELECT * FROM twitterapi_timeline_coverage WHERE handle=? AND coverage_start=? AND coverage_end=?',
                             (handle.lower(),start,end)).fetchone()
            if old and (old['operation']!=OPERATION or old['provider']!='twitterapi.io' or old['endpoint']!='last_tweets'
                        or old['completion_reason']!=reason or old['in_window_count']!=len(posts)):
                raise IngestError('historical coverage conflicts')
            receipt={'handle':handle,'coverage_start':start,'coverage_end':end,'in_window_count':len(posts),
                     'new_persisted':0,'existing_preserved':0,'changed_originals_preserved':0,'context_promoted':0}
            for post in posts:
                prior=conn.execute('SELECT source_id,platform,raw_text,published_at,raw_json FROM raw_posts WHERE post_id=?',(post.post_id,)).fetchone()
                if prior:
                    receipt['context_promoted'] += int(reconcile_existing_source(conn,prior,post,capture_iso))
                    receipt['existing_preserved']+=1
                    if prior['raw_text']!=post.raw_text or prior['published_at']!=post.published_at:receipt['changed_originals_preserved']+=1
                else:
                    conn.execute('''INSERT INTO raw_posts
                        (post_id,source_id,platform,published_at,captured_at,raw_text,raw_url,raw_json,content_hash,is_deleted,archive_url)
                        VALUES (:post_id,:source_id,:platform,:published_at,:captured_at,:raw_text,:raw_url,:raw_json,:content_hash,:is_deleted,:archive_url)''',post.to_row())
                    receipt['new_persisted']+=1
            if not old:
                conn.execute('INSERT INTO twitterapi_timeline_coverage VALUES (?,?,?,?,?,?,?,?,?)',
                    (handle.lower(),start,end,OPERATION,'twitterapi.io','last_tweets',reason,capture_iso,len(posts)))
            receipts.append(receipt)
    return {'operation':OPERATION,'all_eight_complete':True,'accounts':receipts,
            'coverage_semantics':'provider_timeline_exact_intervals_only',
            'earlier_history_remains_unverified':True,'search_checkpoints_unchanged':True,
            'summary_status':'not_requested','publication_status':'not_requested'}
