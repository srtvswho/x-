"""Regression tests for duplicate summaries, partial failure and dated backfills."""
import importlib
import json
import sqlite3
import sys
from datetime import datetime, timezone
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parents[1] / 'scripts' / 'dashboard'))
summary = importlib.import_module('intel_gen_summaries')


@pytest.fixture
def summary_env(tmp_path, monkeypatch):
    db = tmp_path / 'data.db'
    out = tmp_path / 'summaries.json'
    monkeypatch.setattr(summary, 'DB_PATH', str(db))
    monkeypatch.setattr(summary, 'OUT_PATH', str(out))
    monkeypatch.setattr(summary, 'AS_OF', datetime(2026, 9, 6, 8, tzinfo=timezone.utc))
    monkeypatch.setattr(summary, 'ARCHIVE_DATE', None)
    monkeypatch.setattr(summary, 'STATE', None)
    monkeypatch.setattr(summary, 'record_usage', lambda *a, **kw: None)
    for key, value in {
        'AI_ENABLED': 'true', 'AI_DRY_RUN': 'false', 'FORCE_REANALYZE': 'false',
        'AI_LEDGER_DB_PATH': str(db), 'AI_RUN_ID': 'summary-test',
        'AI_MAX_COST_PER_RUN_USD': '10', 'AI_MAX_DAILY_COST_USD': '10',
        'EXTRACT_MAX_COST_PER_RUN': '10', 'AI_MAX_CALLS_PER_RUN': '100',
        'AI_ROUTE_DAILY_SUMMARY_PROVIDER': 'deepseek',
        'AI_ROUTE_DAILY_SUMMARY_MODEL': 'deepseek-v4-flash',
        'AI_JOB_KIND': 'incremental_daily',
    }.items():
        monkeypatch.setenv(key, value)
    return db, out


def test_successful_duplicate_reuses_persisted_output_without_second_paid_call(summary_env, monkeypatch):
    db, out = summary_env
    calls = []
    def provider(*args, **kwargs):
        calls.append(1)
        return '成功摘要', {'usage': {'prompt_tokens': 10, 'completion_tokens': 5}}, 'test-request'
    monkeypatch.setattr('signalboard.ai.router._request_deepseek', provider)
    assert summary.call_llm('system', 'same evidence') == '成功摘要'
    assert json.loads(out.read_text())['request_cache']
    # Load from disk exactly as a subsequent workflow process would.
    assert summary.call_llm('system', 'same evidence') == '成功摘要'
    assert len(calls) == 1
    assert summary.call_llm('system', 'new evidence') == '成功摘要'
    assert len(calls) == 2
    with sqlite3.connect(db) as con:
        assert con.execute("select count(*) from ai_usage_ledger where status='SUCCESS'").fetchone()[0] == 2


@pytest.mark.parametrize('reason', ['DUPLICATE_SUCCESS', 'RUN_BUDGET_EXCEEDED'])
def test_guardrail_failure_keeps_previous_segment_and_allows_next(summary_env, monkeypatch, reason):
    from signalboard.ai.guardrails import AIGuardrailBlocked
    state = {'person': {'old': '此前解读'}}
    monkeypatch.setattr(summary, 'STATE', state)
    errors = {}
    def blocked():
        raise AIGuardrailBlocked(reason)
    summary.generate_segment(state['person'], 'old', blocked, errors, 'austin/3')
    summary.generate_segment(state['person'], 'new', lambda: '最新解读', errors, 'jukan/0')
    assert state['person'] == {'old': '此前解读', 'new': '最新解读'}
    assert errors == {'austin/3': reason}
    assert json.loads(summary_env[1].read_text())['person']['new'] == '最新解读'


def test_backfill_uses_beijing_day_excluding_following_day(summary_env, monkeypatch):
    monkeypatch.setattr(summary, 'ARCHIVE_DATE', '2026-09-05')
    start, end = summary.window_bounds(1)
    assert start == '2026-09-04T16:00:00+00:00'
    assert end == '2026-09-05T16:00:00+00:00'
    monkeypatch.setattr(summary, 'ARCHIVE_DATE', '2026-09-06')
    assert summary.window_bounds(1)[1] == '2026-09-06T08:00:00+00:00'


def test_full_refresh_preserves_history_and_backfills_despite_one_failure(summary_env, monkeypatch):
    db, out = summary_env
    out.write_text(json.dumps({'generated_at': '2026-09-04T00:00:00Z', 'data_until': '2026-09-03',
                              'daily_history': {'2026-09-01': {'summary': '保留历史'}},
                              'person': {'austin': {'3': '旧解读'}}}))
    with sqlite3.connect(db) as con:
        con.execute('CREATE TABLE raw_posts (post_id TEXT, published_at TEXT, raw_text TEXT)')
    monkeypatch.setattr(summary, 'KOLS', {'austin': {}, 'jukan': {}})
    monkeypatch.setattr(summary, 'WINDOWS', {'0': 1, '3': 90})
    monkeypatch.setattr(summary, 'get_data_for_window', lambda *a: [])
    monkeypatch.setattr(summary, 'build_kols_prompt', lambda: 'abilities')
    monkeypatch.setattr(summary, 'gen_today_summary', lambda con: '每日新汇总')
    monkeypatch.setattr(summary, 'gen_consensus_summary', lambda *a: '每日共识')
    def person(con, kol, window, days):
        if kol == 'austin' and window == '3':
            raise RuntimeError('duplicate')
        return '每日个人新解读'
    monkeypatch.setattr(summary, 'gen_person_summary', person)
    monkeypatch.setattr(sys, 'argv', ['summaries', '--backfill-days', '2'])
    summary.main()
    data = json.loads(out.read_text())
    assert data['stale'] is True and data['refresh_complete'] is False
    assert data['generated_at'] == '2026-09-04T00:00:00Z'
    assert data['person']['austin']['3'] == '旧解读'
    assert data['person']['jukan']['3'] == '每日个人新解读'
    assert data['daily_history']['2026-09-01']['summary'] == '保留历史'
    days = [v for k, v in data['daily_history'].items() if k != '2026-09-01']
    assert len(days) == 2
    assert all(v['complete'] and len(v['person']) == 2 for v in days)


def test_failed_atomic_replace_preserves_existing_json(summary_env, monkeypatch):
    _, out = summary_env
    out.write_text('{"today":"previous"}')
    def fail(*a):
        raise OSError('replace failed')
    monkeypatch.setattr(summary.os, 'replace', fail)
    with pytest.raises(OSError):
        summary.atomic_save({'today': 'new'})
    assert json.loads(out.read_text()) == {'today': 'previous'}
