from __future__ import annotations

import json
import sqlite3

import pytest

from signalboard.ai.guardrails import AIDryRun, AIGuardrailBlocked
from signalboard.ai.router import call_text


@pytest.fixture
def guarded_env(tmp_path, monkeypatch):
    db = tmp_path / "ledger.db"
    monkeypatch.setenv("AI_LEDGER_DB_PATH", str(db))
    monkeypatch.setenv("AI_RUN_ID", "guardrail-acceptance")
    monkeypatch.setenv("AI_WORKFLOW", "pytest")
    monkeypatch.setenv("AI_MAX_COST_PER_RUN_USD", "10")
    monkeypatch.setenv("AI_MAX_DAILY_COST_USD", "10")
    monkeypatch.setenv("AI_MAX_CALLS_PER_RUN", "20")
    monkeypatch.setenv("MEDIA_MAX_COST_PER_RUN", "10")
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    monkeypatch.delenv("ALLOW_EXPENSIVE_AI_JOB", raising=False)
    monkeypatch.delenv("AI_DRY_RUN", raising=False)
    monkeypatch.delenv("AI_JOB_KIND", raising=False)
    return db


def _attempt() -> None:
    call_text("media_understanding", "system", "user", max_output_tokens=10, max_retries=0)


def _network_bomb(*_args, **_kwargs):
    raise AssertionError("network must not be reached")


def _events(db):
    con = sqlite3.connect(db)
    rows = con.execute("SELECT status,metadata_json FROM ai_usage_ledger ORDER BY request_started_at").fetchall()
    con.close()
    return [(status, json.loads(metadata)) for status, metadata in rows]


def test_ai_enabled_false_blocks_before_network(guarded_env, monkeypatch):
    monkeypatch.setenv("AI_ENABLED", "false")
    monkeypatch.setattr("signalboard.ai.router.requests.post", _network_bomb)
    with pytest.raises(AIGuardrailBlocked, match="AI_DISABLED"):
        _attempt()
    assert _events(guarded_env)[-1][0] == "SKIPPED"


def test_zero_run_budget_blocks_before_network(guarded_env, monkeypatch):
    monkeypatch.setenv("AI_ENABLED", "true")
    monkeypatch.setenv("AI_MAX_COST_PER_RUN_USD", "0")
    monkeypatch.setattr("signalboard.ai.router.requests.post", _network_bomb)
    with pytest.raises(AIGuardrailBlocked, match="RUN_BUDGET_EXCEEDED"):
        _attempt()
    assert _events(guarded_env)[-1][0] == "BUDGET_BLOCKED"


def test_zero_call_limit_blocks_before_network(guarded_env, monkeypatch):
    monkeypatch.setenv("AI_ENABLED", "true")
    monkeypatch.setenv("AI_MAX_CALLS_PER_RUN", "0")
    monkeypatch.setattr("signalboard.ai.router.requests.post", _network_bomb)
    with pytest.raises(AIGuardrailBlocked, match="CALL_LIMIT_EXCEEDED"):
        _attempt()
    assert _events(guarded_env)[-1][0] == "BUDGET_BLOCKED"


def test_dry_run_prints_estimate_and_makes_zero_calls(guarded_env, monkeypatch, capsys):
    monkeypatch.setenv("AI_ENABLED", "true")
    monkeypatch.setenv("AI_DRY_RUN", "true")
    monkeypatch.setattr("signalboard.ai.router.requests.post", _network_bomb)
    with pytest.raises(AIDryRun):
        _attempt()
    plan = json.loads(capsys.readouterr().out.strip().splitlines()[-1])
    assert plan["would_call_model"] is True
    assert plan["estimated_input_tokens"] > 0
    assert plan["estimated_output_tokens"] == 10
    assert plan["estimated_cost"] > 0
    assert plan["actual_api_calls"] == 0


def test_full_golden_requires_expensive_job_gate(guarded_env, monkeypatch):
    monkeypatch.setenv("AI_ENABLED", "true")
    monkeypatch.setenv("AI_JOB_KIND", "golden_full")
    monkeypatch.setenv("ALLOW_EXPENSIVE_AI_JOB", "false")
    monkeypatch.setattr("signalboard.ai.router.requests.post", _network_bomb)
    with pytest.raises(AIGuardrailBlocked, match="EXPENSIVE_JOB_BLOCKED"):
        _attempt()
    assert _events(guarded_env)[-1][0] == "SKIPPED"


@pytest.mark.parametrize('scope', ['AI_MAX_COST_PER_RUN_USD', 'AI_MAX_DAILY_COST_USD', 'MEDIA_MAX_COST_PER_RUN'])
def test_settled_usage_releases_reservation_for_all_budgets(guarded_env, monkeypatch, scope):
    from signalboard.ai.guardrails import preflight, finish_success
    monkeypatch.setenv('AI_ENABLED', 'true')
    monkeypatch.setenv(scope, '0.0015')
    def reserve(key):
        return preflight(workload='media_understanding', provider='openai', model='test',
                         system='s', user='u', image_count=0, max_output_tokens=1000,
                         prices_per_million=(1, 1, 1), input_hash=key, prompt_version='test')
    first = reserve('first')
    with pytest.raises(AIGuardrailBlocked):
        reserve('pending-would-overrun')
    finish_success(first, input_tokens=1, cached_input_tokens=0, output_tokens=99, actual_cost=0.0001)
    assert reserve('settled-fits').ledger_id


@pytest.mark.parametrize('status,actual', [('SUCCESS', None), ('FAILED', 0), ('PENDING', 0)])
def test_unknown_or_unfinished_cost_keeps_full_reservation(guarded_env, monkeypatch, status, actual):
    from signalboard.ai.guardrails import preflight
    monkeypatch.setenv('AI_ENABLED', 'true')
    monkeypatch.setenv('AI_MAX_COST_PER_RUN_USD', '0.0015')
    def reserve(key):
        return preflight(workload='media_understanding', provider='openai', model='test',
                         system='s', user='u', image_count=0, max_output_tokens=1000,
                         prices_per_million=(1, 1, 1), input_hash=key, prompt_version='test')
    first = reserve('first')
    with sqlite3.connect(guarded_env) as con:
        con.execute('UPDATE ai_usage_ledger SET status=?,actual_cost_if_available=? WHERE ledger_id=?',
                    (status, actual, first.ledger_id))
    with pytest.raises(AIGuardrailBlocked, match='RUN_BUDGET_EXCEEDED'):
        reserve('second')
