import importlib.util
import json
import os
from pathlib import Path
import sqlite3
from datetime import datetime, timezone

import pytest

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('campaign', ROOT / 'scripts/intel_history_campaign.py')
campaign = importlib.util.module_from_spec(spec)
spec.loader.exec_module(campaign)


@pytest.fixture
def db(tmp_path):
    path = tmp_path / 'campaign.db'
    with sqlite3.connect(path) as con:
        con.executescript('''CREATE TABLE raw_posts(post_id TEXT, source_id TEXT, published_at TEXT);
            CREATE TABLE extractions_intel(post_id TEXT, prompt_version TEXT);
            INSERT INTO raw_posts VALUES ('a','tw_jukan05','2025-01-01'),
                ('b','tw_jukan05','2025-01-02'), ('c','tw_jukan05','2025-01-03');''')
    return path


def test_continues_to_empty_queue_and_checkpoints(db, tmp_path):
    attempted = []
    identities = []
    checkpoints = []
    def batch(db, limit, apply, output, timeout):
        plan = campaign.read_plan(db, limit)
        attempted.extend(plan['selected_post_ids'])
        identities.append(os.getenv('AI_RUN_ID'))
        with sqlite3.connect(db) as con:
            con.executemany('INSERT INTO extractions_intel VALUES (?,?)',
                            [(p, plan['prompt_version']) for p in plan['selected_post_ids']])
        return {'batch_status': 'completed', 'resolved_this_run': len(plan['selected_post_ids']),
                'pending_total': plan['pending_total'] - len(plan['selected_post_ids'])}
    report = campaign.drain(db, 1, tmp_path / 'report.json', batch_fn=batch,
                            checkpoint_every=2, checkpoint_fn=lambda: checkpoints.append(len(attempted)))
    assert attempted == ['a', 'b', 'c']
    assert len(set(identities)) == 1
    assert checkpoints == [2, 3]
    assert report['resolved_this_job'] == 3
    assert report['campaign_status'] == 'extraction_complete'
    assert report['history_complete'] is False


def test_no_progress_stops_and_preserves_pending(db, tmp_path):
    attempts = []
    def batch(*args, **kwargs):
        attempts.append(1)
        return {'batch_status': 'incomplete', 'resolved_this_run': 0,
                'pending_total': 3, 'unresolved_attempted_post_ids': ['a']}
    report = campaign.drain(db, 1, tmp_path / 'report.json', batch_fn=batch)
    assert len(attempts) == 1
    assert report['campaign_status'] == 'blocked'
    assert report['pending_total'] == 3
    assert json.loads((tmp_path / 'report.json').read_text()) == report


def test_expired_time_slice_is_resumable_without_call(db, tmp_path):
    report = campaign.drain(db, 1, tmp_path / 'report.json', max_seconds=0,
                            batch_fn=lambda *a, **kw: pytest.fail('Time slice must stop'))
    assert report['campaign_status'] == 'checkpointed_for_resume'
    assert report['pending_total'] == 3


def test_scheduled_gate_stops_after_completion_block_or_expiry():
    config = {'enabled': True, 'expires_at': '2026-09-10T00:00:00Z', 'campaign_id': 'stable'}
    now = datetime(2026, 9, 7, tzinfo=timezone.utc)
    assert campaign.gate(config, {}, now)
    assert campaign.gate(config, {'campaign_id': 'stable', 'campaign_status': 'checkpointed_for_resume'}, now)
    for status in ('completed', 'blocked'):
        assert not campaign.gate(config, {'campaign_id': 'stable', 'campaign_status': status}, now)
    assert not campaign.gate(config, {}, datetime(2026, 9, 11, tzinfo=timezone.utc))
    assert not campaign.gate(dict(config, enabled=False), {}, now)


def test_old_interpretations_are_revisited_in_chronological_order(db):
    with sqlite3.connect(db) as con:
        con.execute("INSERT INTO extractions_intel VALUES ('a','old-version')")
    assert campaign.read_plan(db, 1)['selected_post_ids'] == ['a']


def test_audit_matches_anchors_and_keeps_prices_missing_explicit(tmp_path):
    from test_first_call_repair import database, post
    con = database()
    post(con, 'old', '2024-01-01T00:00:00Z')
    post(con, 'new', '2026-01-01T00:00:00Z')
    con.commit()
    db = tmp_path / 'audit.db'
    with sqlite3.connect(db) as disk:
        con.backup(disk)
    audit = campaign.make_audit(db, tmp_path / 'none.json')
    assert audit['structural_errors'] == []
    assert audit['jukan_focus'][0]['post_id'] == 'old'
    assert audit['prices_missing'][0]['call_date'] == '2024-01-01'
    assert audit['stored_history_extraction_complete'] is False


def test_partial_failures_defer_until_healthy_posts_finish(db, tmp_path, monkeypatch):
    attempted = []
    def batch(db, limit, apply, output, timeout, excluded_post_ids=()):
        plan = campaign.read_plan(db, limit, excluded_post_ids)
        ids = plan['selected_post_ids']
        attempted.append(ids)
        failed = ['a'] if 'a' in ids and len(attempted) == 1 else []
        with sqlite3.connect(db) as con:
            con.executemany('INSERT INTO extractions_intel VALUES (?,?)',
                [(p, plan['prompt_version']) for p in ids if p not in failed])
        return {'batch_status': 'incomplete' if failed else 'completed',
                'resolved_this_run': len(ids) - len(failed),
                'unresolved_attempted_post_ids': failed}
    report = campaign.drain(db, 2, tmp_path / 'r.json', batch_fn=batch)
    assert attempted == [['a', 'b'], ['c'], ['a']]
    assert report['campaign_status'] == 'extraction_complete'
    assert report['failed_post_attempts'] == {}


def test_deferred_posts_stay_in_coverage_and_retry_counts_survive_resume(db, tmp_path):
    output = tmp_path / 'r.json'
    output.write_text(json.dumps({'campaign_id': os.getenv('AI_RUN_ID', 'local-history-plan'),
        'repair_revision': 'v1', 'failed_post_attempts': {'a': 2, 'b': 2, 'c': 2}}))
    report = campaign.drain(db, 2, output, repair_revision='v1',
        batch_fn=lambda *a, **kw: pytest.fail('Exhausted posts must not be retried'))
    assert report['selected_post_ids'] == []
    assert report['pending_total'] == 3
    assert report['stored_history_call_review_complete'] is False
    assert report['campaign_status'] == 'blocked'
    assert report['blocked_reason'] == 'unresolved_posts'


def test_two_partially_failed_batches_do_not_stop_campaign(db, tmp_path):
    with sqlite3.connect(db) as con:
        con.executemany('INSERT INTO raw_posts VALUES (?, ?, ?)',
            [(p, 'tw_jukan05', '2025-02-01') for p in ('d', 'e', 'f')])
    attempted = []
    def batch(db, limit, apply, output, timeout, excluded_post_ids=()):
        plan = campaign.read_plan(db, limit, excluded_post_ids)
        ids = plan['selected_post_ids']
        attempted.append(ids)
        failed = [ids[0]] if len(attempted) <= 2 else []
        with sqlite3.connect(db) as con:
            con.executemany('INSERT INTO extractions_intel VALUES (?,?)',
                [(p, plan['prompt_version']) for p in ids if p not in failed])
        return {'batch_status': 'incomplete' if failed else 'completed',
                'resolved_this_run': len(ids) - len(failed), 'unresolved_attempted_post_ids': failed}
    report = campaign.drain(db, 2, tmp_path / 'r.json', batch_fn=batch)
    assert attempted == [['a', 'b'], ['c', 'd'], ['e', 'f'], ['a', 'c']]
    assert report['pending_total'] == 0


def test_only_new_repair_revision_reopens_blocked_campaign():
    config = {'enabled': True, 'expires_at': '2026-09-10T00:00:00Z',
              'campaign_id': 'same-budget', 'repair_revision': 'json-v1'}
    now = datetime(2026, 9, 7, tzinfo=timezone.utc)
    report = {'campaign_id': 'same-budget', 'campaign_status': 'blocked'}
    assert campaign.gate(config, report, now)
    assert not campaign.gate(config, dict(report, repair_revision='json-v1'), now)
    assert not campaign.gate(config, dict(report, campaign_status='completed'), now)
