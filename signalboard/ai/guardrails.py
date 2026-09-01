"""Fail-closed budget and audit controls for every routed paid AI request."""
from __future__ import annotations

import json
import os
import sqlite3
import sys
import uuid
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


ATTEMPTED_STATUSES = ("PENDING", "SUCCESS", "FAILED", "CANCELLED", "UNKNOWN_COST")
EXPENSIVE_JOB_KINDS = {
    "golden_full",
    "historical_media_backfill",
    "historical_claim_verification",
    "full_thesis_regeneration",
}
STAGE_BY_WORKLOAD = {
    "bulk_post_processing": "extract",
    "daily_summary": "extract",
    "media_understanding": "media",
    "theme_canonicalization": "theme",
    "claim_verification": "claim",
    "thesis_update": "thesis",
    "cross_author_analysis": "thesis",
    "ai_analyst": "analyst",
    "research_case_synthesis": "analyst",
    "deep_investment_analysis": "analyst",
    "golden_evaluation": "golden",
    "embedding": "theme",
}
STAGE_BUDGET_ENV = {
    "extract": "EXTRACT_MAX_COST_PER_RUN",
    "media": "MEDIA_MAX_COST_PER_RUN",
    "theme": "THEME_MAX_COST_PER_RUN",
    "claim": "CLAIM_MAX_COST_PER_RUN",
    "thesis": "THESIS_MAX_COST_PER_RUN",
    "analyst": "ANALYST_MAX_COST_PER_RUN",
    "golden": "GOLDEN_MAX_COST_PER_RUN",
}
STAGE_BUDGET_DEFAULT = {
    "extract": 0.10,
    "media": 0.15,
    "theme": 0.10,
    "claim": 0.20,
    "thesis": 0.15,
    "analyst": 0.15,
    "golden": 0.0,
}


class AIGuardrailBlocked(RuntimeError):
    """Raised before credentials/network access when a paid request is forbidden."""

    def __init__(self, reason: str, *, status: str = "BUDGET_BLOCKED") -> None:
        super().__init__(reason)
        self.reason = reason
        self.status = status


class AIDryRun(AIGuardrailBlocked):
    def __init__(self, plan: dict[str, Any]) -> None:
        super().__init__("AI_DRY_RUN", status="SKIPPED")
        self.plan = plan


@dataclass(frozen=True)
class RequestPermit:
    ledger_id: str
    stage: str
    estimated_input_tokens: int
    estimated_output_tokens: int
    estimated_cost: float


def _truthy(name: str, default: bool = False) -> bool:
    raw = os.getenv(name)
    if raw is None:
        return default
    return raw.strip().lower() in {"1", "true", "yes", "on"}


def _number(name: str, default: float) -> float:
    raw = os.getenv(name)
    if raw is None or not raw.strip():
        return default
    try:
        value = float(raw)
    except ValueError as exc:
        raise AIGuardrailBlocked(f"INVALID_{name}", status="SKIPPED") from exc
    if value < 0:
        raise AIGuardrailBlocked(f"INVALID_{name}", status="SKIPPED")
    return value


def _integer(name: str, default: int) -> int:
    value = _number(name, float(default))
    if value != int(value):
        raise AIGuardrailBlocked(f"INVALID_{name}", status="SKIPPED")
    return int(value)


def _now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="milliseconds").replace("+00:00", "Z")


def _ledger_path() -> Path:
    return Path(os.getenv("AI_LEDGER_DB_PATH", "/workspace/data/signalboard_full.db"))


def _connect() -> sqlite3.Connection:
    path = _ledger_path()
    from signalboard.db import init_db

    init_db(path)
    con = sqlite3.connect(path, timeout=30)
    con.row_factory = sqlite3.Row
    con.execute("PRAGMA busy_timeout=30000")
    return con


def _identity() -> tuple[str, str]:
    run_id = os.getenv("AI_RUN_ID") or os.getenv("GITHUB_RUN_ID") or f"local-{os.getpid()}"
    workflow = os.getenv("AI_WORKFLOW") or os.getenv("GITHUB_WORKFLOW") or "local"
    return run_id, workflow


def _insert_event(
    con: sqlite3.Connection,
    *,
    status: str,
    workload: str,
    stage: str,
    provider: str,
    model: str,
    estimated_input_tokens: int,
    estimated_output_tokens: int,
    estimated_cost: float,
    input_hash: str,
    prompt_version: str,
    entity_type: str | None,
    entity_id: str | None,
    reason: str | None = None,
) -> str:
    ledger_id = uuid.uuid4().hex
    run_id, workflow = _identity()
    finished = None if status == "PENDING" else _now()
    metadata = {"workload": workload}
    if reason:
        metadata["reason"] = reason
    con.execute(
        """INSERT INTO ai_usage_ledger
           (ledger_id,run_id,workflow,stage,entity_type,entity_id,provider,model,
            request_started_at,request_finished_at,input_tokens,output_tokens,
            estimated_cost,status,input_hash,prompt_version,metadata_json)
           VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
        (
            ledger_id, run_id, workflow, stage, entity_type, entity_id, provider, model,
            _now(), finished, estimated_input_tokens, estimated_output_tokens,
            estimated_cost, status, input_hash, prompt_version,
            json.dumps(metadata, ensure_ascii=False, sort_keys=True),
        ),
    )
    con.commit()
    return ledger_id


def _blocked_event(**kwargs: Any) -> None:
    try:
        con = _connect()
        try:
            _insert_event(con, **kwargs)
        finally:
            con.close()
    except Exception as exc:
        print(f"AI_GUARDRAIL_LEDGER_ERROR {type(exc).__name__}: {exc}", file=sys.stderr)


def estimate_tokens(system: str, user: str, image_count: int = 0) -> int:
    # Conservative pre-call approximation: UTF-8 bytes / 3 plus high-detail image reserve.
    return max(1, (len(system.encode("utf-8")) + len(user.encode("utf-8")) + 2) // 3) + image_count * 1800


def preflight(
    *,
    workload: str,
    provider: str,
    model: str,
    system: str,
    user: str,
    image_count: int,
    max_output_tokens: int,
    prices_per_million: tuple[float, float, float],
    input_hash: str,
    prompt_version: str,
    entity_type: str | None = None,
    entity_id: str | None = None,
) -> RequestPermit:
    stage = STAGE_BY_WORKLOAD.get(workload, workload)
    estimated_input = estimate_tokens(system, user, image_count)
    estimated_output = max(0, max_output_tokens)
    input_rate, _cached_rate, output_rate = prices_per_million
    estimated_cost = round((estimated_input * input_rate + estimated_output * output_rate) / 1_000_000, 8)
    event = dict(
        workload=workload, stage=stage, provider=provider, model=model,
        estimated_input_tokens=estimated_input, estimated_output_tokens=estimated_output,
        estimated_cost=estimated_cost, input_hash=input_hash, prompt_version=prompt_version,
        entity_type=entity_type, entity_id=entity_id,
    )

    if not _truthy("AI_ENABLED"):
        _blocked_event(status="SKIPPED", reason="AI_DISABLED", **event)
        raise AIGuardrailBlocked("AI_DISABLED", status="SKIPPED")

    job_kind = os.getenv("AI_JOB_KIND", "incremental").strip().lower()
    expensive = job_kind in EXPENSIVE_JOB_KINDS or _truthy("AI_EXPENSIVE_JOB")
    if expensive and not _truthy("ALLOW_EXPENSIVE_AI_JOB"):
        _blocked_event(status="SKIPPED", reason="EXPENSIVE_JOB_BLOCKED", **event)
        raise AIGuardrailBlocked("EXPENSIVE_JOB_BLOCKED", status="SKIPPED")

    if estimated_cost <= 0 and model != "text-embedding-3-small":
        _blocked_event(status="BUDGET_BLOCKED", reason="UNKNOWN_MODEL_PRICE", **event)
        raise AIGuardrailBlocked("UNKNOWN_MODEL_PRICE")

    run_id, _workflow = _identity()
    try:
        con = _connect()
    except Exception as exc:
        raise AIGuardrailBlocked(f"LEDGER_UNAVAILABLE:{type(exc).__name__}", status="SKIPPED") from exc
    try:
        if not _truthy("FORCE_REANALYZE"):
            duplicate = con.execute(
                """SELECT 1 FROM ai_usage_ledger
                   WHERE stage=? AND model=? AND prompt_version=? AND input_hash=? AND status='SUCCESS'
                   LIMIT 1""",
                (stage, model, prompt_version, input_hash),
            ).fetchone()
            if duplicate:
                _insert_event(con, status="SKIPPED", reason="DUPLICATE_SUCCESS", **event)
                raise AIGuardrailBlocked("DUPLICATE_SUCCESS", status="SKIPPED")

        placeholders = ",".join("?" for _ in ATTEMPTED_STATUSES)
        attempted_count = int(con.execute(
            f"SELECT COUNT(*) FROM ai_usage_ledger WHERE run_id=? AND status IN ({placeholders})",
            (run_id, *ATTEMPTED_STATUSES),
        ).fetchone()[0])
        if attempted_count >= _integer("AI_MAX_CALLS_PER_RUN", 20):
            _insert_event(con, status="BUDGET_BLOCKED", reason="CALL_LIMIT_EXCEEDED", **event)
            raise AIGuardrailBlocked("CALL_LIMIT_EXCEEDED")

        run_cost = float(con.execute(
            f"SELECT COALESCE(SUM(estimated_cost),0) FROM ai_usage_ledger WHERE run_id=? AND status IN ({placeholders})",
            (run_id, *ATTEMPTED_STATUSES),
        ).fetchone()[0])
        if run_cost + estimated_cost > _number("AI_MAX_COST_PER_RUN_USD", 0.50):
            _insert_event(con, status="BUDGET_BLOCKED", reason="RUN_BUDGET_EXCEEDED", **event)
            raise AIGuardrailBlocked("RUN_BUDGET_EXCEEDED")

        daily_cost = float(con.execute(
            f"""SELECT COALESCE(SUM(estimated_cost),0) FROM ai_usage_ledger
                WHERE substr(request_started_at,1,10)=substr(?,1,10) AND status IN ({placeholders})""",
            (_now(), *ATTEMPTED_STATUSES),
        ).fetchone()[0])
        if daily_cost + estimated_cost > _number("AI_MAX_DAILY_COST_USD", 1.00):
            _insert_event(con, status="DAILY_BUDGET_EXCEEDED", reason="DAILY_BUDGET_EXCEEDED", **event)
            raise AIGuardrailBlocked("DAILY_BUDGET_EXCEEDED", status="DAILY_BUDGET_EXCEEDED")

        stage_env = STAGE_BUDGET_ENV.get(stage, f"{stage.upper()}_MAX_COST_PER_RUN")
        stage_limit = _number(stage_env, STAGE_BUDGET_DEFAULT.get(stage, 0.0))
        stage_cost = float(con.execute(
            f"""SELECT COALESCE(SUM(estimated_cost),0) FROM ai_usage_ledger
                WHERE run_id=? AND stage=? AND status IN ({placeholders})""",
            (run_id, stage, *ATTEMPTED_STATUSES),
        ).fetchone()[0])
        if stage_cost + estimated_cost > stage_limit:
            _insert_event(con, status="BUDGET_BLOCKED", reason="STAGE_BUDGET_EXCEEDED", **event)
            raise AIGuardrailBlocked("STAGE_BUDGET_EXCEEDED")

        if _truthy("AI_DRY_RUN"):
            plan = {
                "would_call_model": True,
                "model": model,
                "provider": provider,
                "stage": stage,
                "number_of_calls": attempted_count + 1,
                "estimated_input_tokens": estimated_input,
                "estimated_output_tokens": estimated_output,
                "estimated_cost": estimated_cost,
                "actual_api_calls": 0,
            }
            _insert_event(con, status="SKIPPED", reason="DRY_RUN", **event)
            print(json.dumps(plan, ensure_ascii=False, sort_keys=True))
            raise AIDryRun(plan)

        ledger_id = _insert_event(con, status="PENDING", **event)
        return RequestPermit(ledger_id, stage, estimated_input, estimated_output, estimated_cost)
    finally:
        con.close()


def finish_success(
    permit: RequestPermit,
    *,
    input_tokens: int,
    cached_input_tokens: int,
    output_tokens: int,
    actual_cost: float,
) -> None:
    con = _connect()
    try:
        con.execute(
            """UPDATE ai_usage_ledger SET request_finished_at=?,input_tokens=?,cached_input_tokens=?,
               output_tokens=?,actual_cost_if_available=?,status='SUCCESS' WHERE ledger_id=?""",
            (_now(), input_tokens, cached_input_tokens, output_tokens, actual_cost, permit.ledger_id),
        )
        con.commit()
    finally:
        con.close()


def finish_failure(permit: RequestPermit, error: BaseException) -> None:
    con = _connect()
    try:
        con.execute(
            """UPDATE ai_usage_ledger SET request_finished_at=?,status='FAILED',error_type=?
               WHERE ledger_id=?""",
            (_now(), type(error).__name__, permit.ledger_id),
        )
        con.commit()
    finally:
        con.close()
