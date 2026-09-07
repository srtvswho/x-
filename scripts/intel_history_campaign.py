#!/usr/bin/env python3
"""Drain stored historical extraction in one campaign with durable checkpoints.

The workflow supplies a stable AI_RUN_ID across batches/restarts, so retries never
reset the total campaign budget. No credentials, model routes or budgets are
changed here. Scheduling is explicitly enabled by the tracked campaign config.
"""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import gzip
import json
import os
from pathlib import Path
import shutil
import sqlite3
import subprocess
import sys
import time

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / 'scripts'))
from intel_history_backfill import read_plan, run_backfill, write_report
from signalboard.history_reuse import recover, restore_archives, apply_evidence_reviews
from signalboard.extract.prompts_intel import PROMPT_VERSION
from common import SRC2KOL
from signalboard.ai.guardrails import ACCOUNTED_COST_SQL, ATTEMPTED_STATUSES

CONFIG = ROOT / 'config/history_repair_campaign.json'
REPORT = ROOT / 'outputs/history_repair_campaign.json'
BASELINE = ROOT / 'outputs/first_call_campaign_before.json'
AUDIT = ROOT / 'outputs/first_call_campaign_audit.json'
REUSE = ROOT / 'outputs/history_reuse_report.json'


def ledger_summary(db, run_id):
    with sqlite3.connect(f'file:{Path(db).resolve()}?mode=ro', uri=True) as con:
        if not con.execute("SELECT 1 FROM sqlite_master WHERE name='ai_usage_ledger'").fetchone():
            return {'attempts': 0, 'accounted_usd': 0, 'usage_cost_usd': 0, 'initial_estimated_usd': 0}
        marks = ','.join('?' for _ in ATTEMPTED_STATUSES)
        row = con.execute(f'''SELECT COUNT(*), COALESCE(SUM({ACCOUNTED_COST_SQL}),0),
            COALESCE(SUM(CASE WHEN status='SUCCESS' THEN actual_cost_if_available ELSE 0 END),0),
            COALESCE(SUM(estimated_cost),0) FROM ai_usage_ledger
            WHERE run_id=? AND status IN ({marks})''', (run_id, *ATTEMPTED_STATUSES)).fetchone()
    return dict(zip(('attempts', 'accounted_usd', 'usage_cost_usd', 'initial_estimated_usd'), row))


def checkpoint(db, paths):
    """Called between batches, never while an extractor is writing the database."""
    snapshot = ROOT / 'data/history_checkpoint.db'
    with sqlite3.connect(db) as source, sqlite3.connect(snapshot) as target:
        source.backup(target)
    # Cancellation can interrupt a batch between its report writes. Derive
    # coverage from the exact backed-up database, never from a stale green log.
    actual = read_plan(snapshot, 400)
    from signalboard.call_attribution import candidates
    with sqlite3.connect(f'file:{snapshot}?mode=ro', uri=True) as con:
        actual['per_security_review_pending'] = len(candidates(con))
    actual['stored_history_call_review_complete'] = (
        actual['stored_history_call_review_complete'] and not actual['per_security_review_pending'])
    write_report(ROOT / 'outputs/signalboard_history_rebuild_latest.json', actual)
    if REPORT.exists():
        report = json.loads(REPORT.read_text())
        report.update(actual)
        if report.get('campaign_id'):
            report['ledger'] = ledger_summary(snapshot, report['campaign_id'])
        write_report(REPORT, report)
    compressed = ROOT / 'data/signalboard.db.gz'
    temporary = compressed.with_suffix('.gz.tmp')
    with snapshot.open('rb') as src, gzip.open(temporary, 'wb') as dst:
        shutil.copyfileobj(src, dst)
    temporary.replace(compressed)
    snapshot.unlink()
    paths = [*paths, ROOT / 'outputs/call_attribution_review.json', ROOT / 'outputs/international_price_refresh.json']
    tracked = [str(compressed.relative_to(ROOT))]
    tracked.extend(str(Path(p).resolve().relative_to(ROOT)) for p in paths if Path(p).exists())
    subprocess.run(['git', 'add', '--', *tracked], cwd=ROOT, check=True)
    diff = subprocess.run(['git', 'diff', '--cached', '--quiet'], cwd=ROOT)
    if diff.returncode == 1:
        subprocess.run(['git', 'commit', '-m', 'Checkpoint full historical call repair [skip daily]'], cwd=ROOT, check=True)
        # Fast-forward only: if another writer broke the shared lock, stop safely.
        subprocess.run(['git', 'push', 'origin', 'HEAD:master'], cwd=ROOT, check=True)
    elif diff.returncode:
        raise RuntimeError('Could not inspect checkpoint changes')


def drain(db, limit, output, *, max_seconds=16800, checkpoint_every=1,
          checkpoint_fn=None, batch_fn=run_backfill, clock=time.monotonic,
          repair_revision=None):
    started = clock()
    initial = read_plan(db, limit)
    run_id = os.environ.get('AI_RUN_ID', 'local-history-plan')
    batch_output = Path(output).with_name('signalboard_history_rebuild_latest.json')
    previous = json.loads(Path(output).read_text()) if Path(output).exists() else {}
    failures = dict(previous.get('failed_post_attempts', {})) if (
        previous.get('campaign_id') == run_id and
        previous.get('repair_revision') == repair_revision) else {}
    batches = 0
    no_progress = 0
    while True:
        # Failed posts wait until untouched posts have drained. Two batch attempts
        # per post/revision are allowed, each still subject to the shared AI ledger.
        excluded = set(failures)
        plan = read_plan(db, limit, excluded)
        if plan['pending_total'] and not plan['selected_post_ids']:
            excluded = {pid for pid, attempts in failures.items() if attempts >= 2}
            plan = read_plan(db, limit, excluded)
        report = dict(plan, campaign_id=run_id, repair_revision=repair_revision,
                      workflow_run_id=os.getenv('GITHUB_RUN_ID'),
                      initial_pending_this_job=initial['pending_total'],
                      resolved_this_job=initial['pending_total'] - plan['pending_total'],
                      batches_this_job=batches, ledger=ledger_summary(db, run_id),
                      failed_post_attempts=dict(failures), deferred_post_ids=sorted(failures),
                      elapsed_seconds=round(clock() - started, 1),
                      campaign_status='running')
        if not plan['pending_total']:
            report['campaign_status'] = 'extraction_complete'
        elif clock() - started >= max_seconds:
            report['campaign_status'] = 'checkpointed_for_resume'
        elif not plan['selected_post_ids']:
            report.update(campaign_status='blocked', blocked_reason='unresolved_posts',
                          unresolved_attempted_post_ids=sorted(failures))
        write_report(output, report)
        if report['campaign_status'] != 'running':
            break
        before_attempts = report['ledger']['attempts']
        batch = batch_fn(db, limit, True, batch_output,
                        timeout=min(1200, max(1, max_seconds - (clock() - started))),
                        **({'excluded_post_ids': excluded} if excluded else {}))
        batches += 1
        unresolved = set(batch.get('unresolved_attempted_post_ids', []))
        for pid in plan['selected_post_ids']:
            if pid in unresolved:
                failures[pid] = failures.get(pid, 0) + 1
            else:
                failures.pop(pid, None)
        no_progress = no_progress + 1 if not batch['resolved_this_run'] else 0
        report.update(read_plan(db, limit))
        report.update(batches_this_job=batches, ledger=ledger_summary(db, run_id),
                      resolved_this_job=initial['pending_total'] - report['pending_total'],
                      failed_post_attempts=dict(failures), deferred_post_ids=sorted(failures),
                      last_batch_status=batch['batch_status'])
        print(json.dumps({'batch': batches, 'resolved': batch['resolved_this_run'],
                          'pending': report['pending_total'], 'deferred': len(failures),
                          'ledger': report['ledger']}), flush=True)
        # A partial success is progress. Stop only on a global failure/budget block,
        # or after two batches with no persisted results; never spin without API work.
        if no_progress >= 2 or (no_progress and report['ledger']['attempts'] == before_attempts):
            report.update(campaign_status='blocked', blocked_reason='no_progress',
                          unresolved_attempted_post_ids=sorted(failures))
        write_report(output, report)
        if report['campaign_status'] == 'blocked':
            break
        if checkpoint_fn and batches % checkpoint_every == 0:
            checkpoint_fn()
    if checkpoint_fn:
        checkpoint_fn()
    return report


def make_audit(db, baseline=BASELINE):
    sys.path.insert(0, str(ROOT / 'scripts/dashboard'))
    from build_dashboard import query_call_performance
    from common import select_call_performance_targets
    with sqlite3.connect(f'file:{Path(db).resolve()}?mode=ro', uri=True) as con:
        rows = query_call_performance(con)
        targets = {(r['source_id'], r['ticker']): r for r in select_call_performance_targets(con)}
        plan = read_plan(db, 400)
        from signalboard.call_attribution import candidates
        per_security_pending = candidates(con)
        issues = []
        for row in rows:
            target = targets.get((row['source_id'], row['ticker']))
            if not target or (target['call_date'], target['direction']) != (row['call_date'], row['direction']):
                issues.append({'source_id': row['source_id'], 'ticker': row['ticker'], 'error': 'price_anchor_mismatch'})
            price, current = row['call_price'], row['now_price']
            if price not in (None, 0) and current is not None:
                expected = round((current / price - 1) * 100, 2) * (1 if row['direction'] == 'long' else -1)
                if abs(expected - row['directional_return']) > 0.001:
                    issues.append({'source_id': row['source_id'], 'ticker': row['ticker'], 'error': 'return_mismatch'})
    old = json.loads(Path(baseline).read_text()) if Path(baseline).exists() else {'rows': []}
    old_by = {(r['source_id'], r['ticker']): r for r in old['rows']}
    changes = []
    for row in rows:
        previous = old_by.get((row['source_id'], row['ticker']))
        if previous is None or (previous['post_id'], previous['direction']) != (row['post_id'], row['direction']):
            changes.append({'source_id': row['source_id'], 'ticker': row['ticker'],
                            'before': {k: previous.get(k) for k in ('call_date', 'post_id', 'direction')} if previous else None,
                            'after': {k: row[k] for k in ('call_date', 'post_id', 'direction', 'raw_url', 'raw_text')}})
    removed = [r for k, r in old_by.items() if k not in targets]
    return {'generated_at': datetime.now(timezone.utc).isoformat(),
            'pending_total': plan['pending_total'], 'sources': plan['sources'],
            'stored_history_extraction_complete': plan['stored_history_extraction_complete'],
            'stored_history_call_review_complete': plan['stored_history_call_review_complete'] and not per_security_pending,
            'raw_history_coverage': 'unverified', 'structural_errors': issues,
            'per_security_review_pending': len(per_security_pending),
            'rows': rows, 'changed_anchors': changes,
            'removed_anchors': [{k: r[k] for k in ('source_id', 'ticker', 'post_id', 'call_date')} for r in removed],
            'prices_missing': [{k: r[k] for k in ('source_id', 'ticker', 'call_date', 'price_unavailable_reason')} for r in rows
                               if r['call_price'] in (None, 0) or r['now_price'] is None],
            'jukan_focus': [r for r in rows if r['source_id'] == 'tw_jukan05' and r['ticker'] in ('MU', 'SNDK')]}


def gate(config, report, now=None):
    now = now or datetime.now(timezone.utc)
    if not config['enabled'] or now >= datetime.fromisoformat(config['expires_at'].replace('Z', '+00:00')):
        return False
    if report.get('campaign_id') != config['campaign_id']:
        return True
    if report.get('campaign_status') == 'completed':
        return False
    if report.get('campaign_status') == 'price_gaps':
        return bool(config.get('repair_revision') and config['repair_revision'] != report.get('repair_revision'))
    if report.get('campaign_status') == 'blocked':
        # A tracked code repair may retry a blocked campaign, without a new budget.
        return bool(config.get('repair_revision') and
                    config['repair_revision'] != report.get('repair_revision'))
    return True


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--db', default='/workspace/data/signalboard_full.db')
    parser.add_argument('--limit', type=int, default=400)
    parser.add_argument('--apply', action='store_true')
    parser.add_argument('--continuous', action='store_true')
    parser.add_argument('--checkpoint-git', action='store_true')
    parser.add_argument('--gate', action='store_true')
    parser.add_argument('--checkpoint-only', action='store_true')
    parser.add_argument('--recover-only', action='store_true', help='Restore saved results with zero API calls')
    parser.add_argument('--audit', action='store_true')
    args = parser.parse_args()
    config = json.loads(CONFIG.read_text())
    if args.checkpoint_only:
        checkpoint(args.db, [REPORT, BASELINE, AUDIT, REUSE, ROOT / 'outputs/signalboard_history_rebuild_latest.json'])
        return
    if args.gate:
        previous = json.loads(REPORT.read_text()) if REPORT.exists() else {}
        enabled = gate(config, previous)
        # Manual read-only plans are always available. A paused campaign cannot
        # silently acquire a new budget through a workflow rerun.
        if os.getenv('GITHUB_EVENT_NAME') == 'workflow_dispatch' and os.getenv('APPLY') != 'true':
            enabled = True
        with open(os.environ['GITHUB_OUTPUT'], 'a') as out:
            out.write(f"run={str(enabled).lower()}\n")
        print(f'Campaign eligible: {enabled}', flush=True)
        return
    if args.audit:
        audit = make_audit(args.db)
        write_report(AUDIT, audit)
        if audit['structural_errors']:
            raise SystemExit('First-call/price anchor validation failed; inspect audit')
        if REPORT.exists():
            report = json.loads(REPORT.read_text())
            report['acceptance'] = {'changed_anchors': len(audit['changed_anchors']),
                                    'prices_missing': len(audit['prices_missing']),
                                    'per_security_review_pending': audit['per_security_review_pending'],
                                    'raw_history_coverage': 'unverified'}
            if not audit['pending_total']:
                report['campaign_status'] = ('attribution_pending' if audit['per_security_review_pending'] else
                    'completed' if not audit['prices_missing'] else 'price_gaps')
                report['repair_revision'] = config.get('repair_revision')
            write_report(REPORT, report)
        print(json.dumps({k: v for k, v in audit.items() if k in
                          ('pending_total', 'stored_history_extraction_complete', 'structural_errors')}, ensure_ascii=False))
        return
    if args.apply and os.environ.get('AI_RUN_ID') != config['campaign_id']:
        raise SystemExit('AI_RUN_ID must use the stable campaign id; budget resets are forbidden')
    if args.apply and not BASELINE.exists():
        write_report(BASELINE, make_audit(args.db))
    if args.apply or args.recover_only:
        if not BASELINE.exists():
            write_report(BASELINE, make_audit(args.db))
        archives = restore_archives(args.db, ROOT, SRC2KOL)
        evidence_count = apply_evidence_reviews(args.db, ROOT / 'config/first_call_evidence_reviews.json')
        reuse = recover(args.db, SRC2KOL, PROMPT_VERSION)
        reuse['reviewed_evidence_applied'] = evidence_count
        reuse['archives'] = archives
        write_report(REUSE, reuse)
        print(json.dumps({k: v for k, v in reuse.items() if k != 'pending'}, ensure_ascii=False), flush=True)
        if args.recover_only:
            write_report(AUDIT, make_audit(args.db))
            write_report(ROOT / 'outputs/signalboard_history_rebuild_latest.json', read_plan(args.db, args.limit))
            return
    if args.apply and args.continuous:
        hook = (lambda: checkpoint(args.db, [REPORT, BASELINE, AUDIT, REUSE, ROOT / 'outputs/signalboard_history_rebuild_latest.json'])) if args.checkpoint_git else None
        if hook:
            hook()
        report = drain(args.db, args.limit, REPORT, max_seconds=config['max_seconds_per_job'], checkpoint_fn=hook,
                       repair_revision=config.get('repair_revision'))
    else:
        report = run_backfill(args.db, args.limit, args.apply, ROOT / 'outputs/signalboard_history_rebuild_latest.json')
    print(json.dumps({k: v for k, v in report.items() if not k.endswith('post_ids')}, ensure_ascii=False, indent=2))
    if report.get('campaign_status') == 'blocked' or report.get('batch_status') == 'incomplete':
        raise SystemExit('Historical repair incomplete; checkpoint preserved, see failed posts and AI ledger')


if __name__ == '__main__':
    main()
