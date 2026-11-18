"""Interpret verified daily timeline windows using the saved database and a per-window ledger."""
import argparse
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import sqlite3
import subprocess
import sys

import intel_resume_queue as queue
from signalboard.twitterapi_timeline_daily import HANDLES

# The previous paid recovery already covered every saved post through this capture boundary.
FIRST_WINDOW = '2026-11-17T02:39:16Z'
STATE = Path('outputs/daily-ai-windows.json')
DB = Path('data/signalboard_full.db')
REVIEW = Path('outputs/daily-ai-review.json')


def read_json(path):
    return json.loads(path.read_text())


def choose(con, state, today, manual=False):
    rows = con.execute("""SELECT coverage_start,coverage_end,handle
        FROM twitterapi_timeline_coverage WHERE coverage_start>=?
        AND operation='timeline-daily-' || coverage_start AND provider='twitterapi.io'
        AND endpoint='last_tweets' AND completion_reason IN ('start_boundary_crossed','timeline_exhausted')
        ORDER BY coverage_start, coverage_end""", (FIRST_WINDOW,))
    groups = {}
    for start, end, handle in rows:
        groups.setdefault((start, end), set()).add(handle.lower())
    # Prefer finishing a publication before paying for other work. A failed window
    # stays visible and cannot starve future windows or repeatedly spend on the same day.
    choices = []
    boundary = FIRST_WINDOW
    for (start, end), handles in groups.items():
        if start != boundary or handles != set(HANDLES) or end <= start:
            break
        boundary = end
        entry = state.get(end, {})
        if entry.get('status') == 'verified':
            continue
        if entry.get('status') == 'ready_to_publish':
            choices.append((0, start, end, 'publish'))
        elif not entry or manual or entry.get('attempt_day') != today:
            choices.append((1 if not entry else 2, start, end, 'interpret'))
    if choices:
        _, start, end, action = min(choices)
        return {'action': action, 'start': start, 'end': end, 'coverage_end': boundary}
    return {'action': 'wait', 'coverage_end': boundary,
            'outstanding': [e for e, record in state.items() if record['status'] != 'verified']}


def save(state):
    STATE.parent.mkdir(exist_ok=True)
    tmp = STATE.with_suffix('.tmp')
    tmp.write_text(json.dumps(state, ensure_ascii=False, indent=2) + '\n')
    tmp.replace(STATE)


def checkpoint(state):
    save(state)
    subprocess.run(['bash', 'scripts/checkpoint_daily_ai.sh'], check=True)


def process(con, selection, state, today):
    start, end = selection['start'], selection['end']
    campaign = 'daily-ai-' + end.replace(':', '')
    os.environ['AI_CAMPAIGN_ID'] = campaign
    if not os.getenv('DEEPSEEK_API_KEY') or os.getenv('AI_ENABLED') != 'true':
        raise RuntimeError('DeepSeek not configured')
    window = state.setdefault(end, {'start': start})
    window.update(status='in_progress', attempt_day=today, campaign=campaign)
    queue.prepare(con, campaign, start, end)
    # A checkpoint before the first call also prevents cascading automatic retries.
    checkpoint(state)
    for deferred in (False, True):
        while True:
            receipt = queue.report(con, campaign, start, end)
            if not receipt['deferred' if deferred else 'pending']:
                break
            before = receipt['counts'].get('complete', 0), receipt['attempted_calls'], receipt['pending']
            error = queue.run_step(con, campaign=campaign, retry_deferred=deferred)
            receipt = queue.report(con, campaign, start, end)
            window['extraction'] = receipt
            checkpoint(state)
            after = receipt['counts'].get('complete', 0), receipt['attempted_calls'], receipt['pending']
            if error or before == after:
                raise RuntimeError(error or 'No recoverable extraction progress')
    if not window.get('review_complete'):
        os.environ['AI_RUN_ID'] = campaign + '/review'
        prior = None
        while True:
            result = subprocess.run([sys.executable, 'scripts/intel_call_attribution.py',
                '--db', str(DB), '--apply', '--daily', '--limit', '100',
                '--queue-campaign', campaign, '--report', str(REVIEW)])
            review = read_json(REVIEW)
            window['pending_directions'] = review['pending']
            checkpoint(state)
            result.check_returncode()
            if not review['pending']:
                break
            if prior == review['pending'] and not review['resolved']:
                raise RuntimeError('Remaining security directions require review')
            prior = review['pending']
        window['review_complete'] = True
        checkpoint(state)
    os.environ['AI_RUN_ID'] = campaign + '/summary'
    subprocess.run([sys.executable, 'scripts/dashboard/intel_gen_summaries.py', '--backfill-days', '2'], check=True)
    summaries = read_json(Path(os.environ['SUMMARY_OUT_PATH']))
    if not summaries.get('refresh_complete'):
        raise RuntimeError('Summary segments pending')
    window.update(status='ready_to_publish', extraction=queue.report(con, campaign, start, end),
                  summary_generated_at=summaries['generated_at'])
    checkpoint(state)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('phase', choices=['plan', 'interpret', 'accept'])
    parser.add_argument('--end')
    args = parser.parse_args()
    state = read_json(STATE) if STATE.exists() else {}
    today = datetime.now(timezone.utc).date().isoformat()
    with sqlite3.connect(DB, timeout=120) as con:
        if args.phase == 'accept':
            window = state[args.end]
            receipt = read_json(Path('outputs/daily-ai-production.json'))
            manifest = read_json(Path('dashboard_deploy_dist/build-manifest.json'))
            if (window['status'] != 'ready_to_publish' or receipt['status'] != 'verified'
                    or receipt['source_commit'] != manifest['source_commit'] or len(receipt['checked_files']) != 7):
                raise ValueError('Current production receipt required')
            window.update(status='verified', production=receipt)
            save(state)
            return
        selected = choose(con, state, today, os.getenv('GITHUB_EVENT_NAME') == 'workflow_dispatch')
        print(json.dumps(selected), flush=True)
        if args.phase == 'plan':
            if os.getenv('GITHUB_OUTPUT'):
                with open(os.environ['GITHUB_OUTPUT'], 'a') as f:
                    for k in ('action', 'end'):
                        print(f'{k}={selected.get(k, "")}', file=f)
            return
        if selected['action'] != 'interpret' or selected['end'] != args.end:
            raise ValueError('Selected window changed')
        process(con, selected, state, today)


if __name__ == '__main__':
    main()
