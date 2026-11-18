"""Durable missing-only extraction queue; offline planning is the default."""
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
import argparse
import json
import os
from pathlib import Path
import sqlite3
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import intel_extract as extract
from signalboard.ai.guardrails import ACCOUNTED_COST_SQL, ATTEMPTED_STATUSES

CAMPAIGN = 'missing-ai-20261118'
SOURCES = ('tw_jukan05', 'tw_aleabitoreddit', 'tw_zephyr_z9', 'tw_austinsemis',
           'tw_DGretta_Author', 'tw_FeroceResearch', 'tw_TradexWhisperer', 'tw_gsmferrari')
SINCE, UNTIL = '2026-11-05T00:00:00Z', '2026-11-18T00:00:00Z'


def prepare(con):
    con.execute('''CREATE TABLE IF NOT EXISTS ai_resume_queue (
        campaign TEXT, post_id TEXT, shard INTEGER, status TEXT DEFAULT 'pending',
        attempts INTEGER DEFAULT 0, payload TEXT, error TEXT,
        PRIMARY KEY(campaign,post_id))''')
    # Any existing interpretation is retained, regardless of its prompt version.
    posts = con.execute('''SELECT r.post_id FROM raw_posts r
        WHERE julianday(r.published_at)>=julianday(?) AND julianday(r.published_at)<julianday(?)
        AND r.source_id IN (?,?,?,?,?,?,?,?)
        AND NOT EXISTS(SELECT 1 FROM extractions_intel e WHERE e.post_id=r.post_id)
        ORDER BY julianday(r.published_at),r.post_id''', (SINCE, UNTIL, *SOURCES)).fetchall()
    existing = con.execute('SELECT count(*) FROM ai_resume_queue WHERE campaign=?', (CAMPAIGN,)).fetchone()[0]
    known = {r[0] for r in con.execute('SELECT post_id FROM ai_resume_queue WHERE campaign=?', (CAMPAIGN,))}
    for (pid,) in posts:
        if pid not in known:
            if existing >= 2000:
                raise ValueError('Queue exceeds bounded scope')
            con.execute('INSERT INTO ai_resume_queue(campaign,post_id,shard) VALUES(?,?,?)', (CAMPAIGN, pid, existing // 350))
            existing += 1
    con.commit()


def report(con):
    counts = dict(con.execute('SELECT status,count(*) FROM ai_resume_queue WHERE campaign=? GROUP BY status', (CAMPAIGN,)))
    prefix = CAMPAIGN + '/'
    paid = con.execute(f'''SELECT count(*),coalesce(sum({ACCOUNTED_COST_SQL}),0)
        FROM ai_usage_ledger WHERE substr(run_id,1,?)=? AND status IN (?,?,?,?,?)''',
        (len(prefix), prefix, *ATTEMPTED_STATUSES)).fetchone()
    return {'campaign': CAMPAIGN, 'since': SINCE, 'until_exclusive': UNTIL, 'counts': counts,
            'pending': counts.get('pending', 0), 'deferred': counts.get('deferred', 0),
            'attempted_calls': paid[0], 'accounted_usd': round(paid[1], 8)}


def run_step(con, limit=75, retry_deferred=False):
    rows = con.execute('''SELECT r.post_id,r.source_id,r.raw_text,r.published_at,q.shard,q.payload
        FROM ai_resume_queue q JOIN raw_posts r USING(post_id)
        WHERE q.campaign=? AND q.status=? AND (?=0 OR q.attempts<2)
        ORDER BY q.shard,julianday(r.published_at),r.post_id LIMIT ?''',
        (CAMPAIGN, 'deferred' if retry_deferred else 'pending', int(retry_deferred), limit)).fetchall()
    if not rows:
        return None
    shard = rows[0][4]
    posts = [dict(zip(('post_id','source_id','raw_text','published_at','shard','payload'), r)) for r in rows if r[4] == shard]
    os.environ['AI_RUN_ID'] = f'{CAMPAIGN}/extract-{shard}'
    extract.MAX_RETRIES = 0  # The queue owns retries; HTTP/budget failures stop the batch.
    blocked = None
    def request(post):
        if post['payload']:
            return {'ok': True, 'extraction': json.loads(post['payload']), 'raw_response': post['payload']}
        if retry_deferred:
            result = extract.call_deepseek(post['post_id'], post['raw_text'],
                                          max_output_tokens=3000, max_retries=1)
            if result['ok']:
                result['raw_response'] = result['raw']
            return result
        return extract.extract_one(post)
    # One real request first, then at most five in flight. Never fan out into an outage.
    groups = [posts[:1]] + [posts[i:i+5] for i in range(1, len(posts), 5)]
    for group in groups:
        with ThreadPoolExecutor(max_workers=5) as pool:
            results = list(pool.map(request, group))
        for post, result in zip(group, results):
            pid = post['post_id']
            if result['ok']:
                payload = result['raw_response']
                con.execute('UPDATE ai_resume_queue SET payload=?,attempts=attempts+? WHERE campaign=? AND post_id=?',
                            (payload, 0 if post['payload'] else 1, CAMPAIGN, pid))
                con.commit()  # Save paid response before downstream semantic persistence.
                if extract.persist_extraction(con, pid, post['source_id'], payload, result['extraction']):
                    con.execute("UPDATE ai_resume_queue SET status='complete',error=NULL WHERE campaign=? AND post_id=?", (CAMPAIGN, pid))
                    if result.get('ai_result'):
                        extract.record_usage(con, result['ai_result'], workload='bulk_post_processing', object_type='post', object_id=pid)
                else:
                    blocked = 'PERSISTENCE_FAILED'
            else:
                error = result.get('error', 'unknown')
                con.execute('UPDATE ai_resume_queue SET error=?,attempts=attempts+1 WHERE campaign=? AND post_id=?', (error, CAMPAIGN, pid))
                if error.startswith(('JSONDecodeError:', 'AIOutputTruncatedError:')):
                    con.execute("UPDATE ai_resume_queue SET status='deferred' WHERE campaign=? AND post_id=?", (CAMPAIGN, pid))
                else:
                    blocked = error
            con.commit()
        if blocked:
            break
    return blocked


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--db', required=True)
    ap.add_argument('--apply', action='store_true')
    ap.add_argument('--retry-deferred', action='store_true',
                    help='One bounded 3000/6000-token recovery for incomplete JSON only')
    ap.add_argument('--report', default='outputs/ai-resume.json')
    args = ap.parse_args()
    extract.init_db(args.db)
    con = sqlite3.connect(args.db, timeout=120)
    extract.init_extractions_table(con)
    prepare(con)
    blocked = None
    if args.apply:
        if datetime.now(timezone.utc) >= datetime(2026, 11, 22, 8, 10, tzinfo=timezone.utc):
            raise SystemExit('Campaign expired')
        if os.getenv('AI_CAMPAIGN_ID') != CAMPAIGN or os.getenv('AI_CAMPAIGN_MAX_COST_USD') != '2.00':
            raise SystemExit('Campaign budget gate')
        blocked = run_step(con, retry_deferred=args.retry_deferred)
    receipt = report(con)
    receipt['blocked'] = blocked
    Path(args.report).parent.mkdir(parents=True, exist_ok=True)
    Path(args.report).write_text(json.dumps(receipt, ensure_ascii=False, indent=2))
    print(json.dumps(receipt, ensure_ascii=False), flush=True)
    con.close()
    if blocked:
        raise SystemExit(2)


if __name__ == '__main__':
    main()
