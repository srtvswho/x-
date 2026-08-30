#!/usr/bin/env python3
"""Incrementally version Author × Theme theses from newly extracted claims."""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import sqlite3
import sys
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from signalboard.ai.router import call_json, record_usage
from signalboard.db import init_db

DB_PATH = "/workspace/data/signalboard_full.db"

THESIS_SCHEMA = {
    "type": "object",
    "additionalProperties": False,
    "properties": {
        "current_thesis": {"type": "string"},
        "thesis_summary": {"type": "string"},
        "bull_case": {"type": "string"},
        "bear_case": {"type": "string"},
        "key_drivers": {"type": "array", "items": {"type": "string"}},
        "key_risks": {"type": "array", "items": {"type": "string"}},
        "companies_positive": {"type": "array", "items": {"type": "string"}},
        "companies_negative": {"type": "array", "items": {"type": "string"}},
        "time_horizon": {"type": "string"},
        "confidence": {"type": "number", "minimum": 0, "maximum": 1},
        "change_type": {"type": "string", "enum": [
            "NO_CHANGE", "CONFIDENCE_UP", "CONFIDENCE_DOWN", "THESIS_EXPANSION",
            "THESIS_REVERSAL", "NEW_RISK", "NEW_CATALYST", "NEW_COMPANY",
            "TIME_HORIZON_CHANGE",
        ]},
        "thesis_change_score": {"type": "number", "minimum": 0, "maximum": 100},
        "change_summary": {"type": "string"},
        "facts": {"type": "array", "items": {"type": "string"}},
        "author_opinions": {"type": "array", "items": {"type": "string"}},
        "ai_inferences": {"type": "array", "items": {"type": "string"}},
        "missing_evidence": {"type": "array", "items": {"type": "string"}},
    },
    "required": [
        "current_thesis", "thesis_summary", "bull_case", "bear_case", "key_drivers",
        "key_risks", "companies_positive", "companies_negative", "time_horizon",
        "confidence", "change_type", "thesis_change_score", "change_summary", "facts",
        "author_opinions", "ai_inferences", "missing_evidence",
    ],
}

SYSTEM_PROMPT = """你是 SignalBoard 的 Thesis 版本编辑器。根据新 Claim 增量更新 Author × Theme Thesis。
必须严格区分 FACT、来源/作者观点和 AI INFERENCE；UNVERIFIED Claim 不能写成已证实事实。
判断新证据相对旧 Thesis 的变化类型，不因重复表述提高 confidence，也不把同一新闻的多次转发算多份证据。
只做研究判断；不得仅因作者看多就给 BUY。输出必须完全符合 JSON Schema。"""


def _now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _thesis_id(author_id: str, theme_id: str) -> str:
    return "thesis_" + hashlib.sha256(f"{author_id}\n{theme_id}".encode()).hexdigest()[:24]


def _pending_groups(con: sqlite3.Connection, limit: int) -> list[tuple]:
    return con.execute(
        """
        SELECT c.author_id, t.theme_id, t.name, MAX(c.point_in_time) AS newest_claim,
               th.thesis_id, th.current_version, th.last_updated
        FROM claims c
        JOIN claim_themes ct ON ct.claim_id=c.claim_id
        JOIN themes t ON t.theme_id=ct.theme_id
        LEFT JOIN theses th ON th.author_id=c.author_id AND th.theme_id=t.theme_id
        WHERE c.author_id LIKE 'tw_%'
          AND c.source_post_id IS NOT NULL
          AND (th.last_updated IS NULL OR c.point_in_time > th.last_updated)
        GROUP BY c.author_id, t.theme_id, t.name, th.thesis_id, th.current_version, th.last_updated
        ORDER BY newest_claim DESC
        LIMIT ?
        """,
        (limit,),
    ).fetchall()


def _claim_rows(con: sqlite3.Connection, author_id: str, theme_id: str, limit: int = 24) -> list[dict]:
    rows = con.execute(
        """
        SELECT c.claim_id, c.claim_text, c.claim_type, c.companies_json,
               c.time_horizon, c.confidence, c.verification_status,
               c.point_in_time, c.source_post_id
        FROM claims c JOIN claim_themes ct ON ct.claim_id=c.claim_id
        WHERE c.author_id=? AND ct.theme_id=?
        ORDER BY c.point_in_time DESC, c.created_at DESC
        LIMIT ?
        """,
        (author_id, theme_id, limit),
    ).fetchall()
    return [
        {
            "claim_id": r[0], "claim_text": r[1], "claim_type": r[2],
            "companies": json.loads(r[3] or "[]"), "time_horizon": r[4],
            "confidence": r[5], "verification_status": r[6],
            "point_in_time": r[7], "source_post_id": r[8],
        }
        for r in rows
    ]


def update_pending_theses(con: sqlite3.Connection, limit: int) -> dict[str, float | int]:
    stats: dict[str, float | int] = {"selected": 0, "versioned": 0, "no_change": 0, "failed": 0, "cost_usd": 0.0}
    for author_id, theme_id, theme_name, newest_claim, existing_id, current_version, last_updated in _pending_groups(con, limit):
        stats["selected"] += 1
        thesis_id = existing_id or _thesis_id(author_id, theme_id)
        previous = None
        if existing_id and current_version:
            row = con.execute(
                "SELECT snapshot_json FROM thesis_versions WHERE thesis_id=? AND version_number=?",
                (existing_id, current_version),
            ).fetchone()
            if row:
                previous = json.loads(row[0])
        claims = _claim_rows(con, author_id, theme_id)
        user = json.dumps({
            "author_id": author_id,
            "theme": theme_name,
            "previous_thesis": previous,
            "recent_claims": claims,
            "instruction": "以 point_in_time 为准，只使用当时已知内容进行增量更新。",
        }, ensure_ascii=False)
        try:
            result = call_json(
                "thesis_update", SYSTEM_PROMPT, user, THESIS_SCHEMA,
                schema_name="signalboard_thesis_update", max_output_tokens=3200,
                timeout=120,
            )
            snapshot = result.data
            if not previous and snapshot["change_type"] == "NO_CHANGE":
                snapshot["change_type"] = "THESIS_EXPANSION"
                snapshot["change_summary"] = snapshot["change_summary"] or "首次建立 Thesis"
            now = _now_iso()
            if previous and snapshot["change_type"] == "NO_CHANGE":
                con.execute("UPDATE theses SET last_updated=? WHERE thesis_id=?", (newest_claim or now, thesis_id))
                record_usage(con, result, workload="thesis_update", object_type="thesis", object_id=thesis_id)
                con.commit()
                stats["no_change"] += 1
                stats["cost_usd"] = round(float(stats["cost_usd"]) + result.estimated_cost_usd, 8)
                continue

            version = int(current_version or 0) + 1
            con.execute(
                """
                INSERT INTO theses (
                    thesis_id, author_id, theme_id, current_version, current_thesis,
                    thesis_summary, confidence, first_seen, last_updated
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(author_id, theme_id) DO UPDATE SET
                    current_version=excluded.current_version,
                    current_thesis=excluded.current_thesis,
                    thesis_summary=excluded.thesis_summary,
                    confidence=excluded.confidence,
                    last_updated=excluded.last_updated
                """,
                (
                    thesis_id, author_id, theme_id, version, snapshot["current_thesis"],
                    snapshot["thesis_summary"], snapshot["confidence"],
                    claims[-1]["point_in_time"] or now, newest_claim or now,
                ),
            )
            evidence_digest = hashlib.sha256("\n".join(x["claim_id"] for x in claims).encode()).hexdigest()
            con.execute(
                """
                INSERT INTO thesis_versions (
                    thesis_id, version_number, snapshot_json, change_type,
                    thesis_change_score, evidence_digest, model
                ) VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    thesis_id, version, json.dumps(snapshot, ensure_ascii=False),
                    snapshot["change_type"], snapshot["thesis_change_score"],
                    evidence_digest, result.model,
                ),
            )
            for claim in claims:
                con.execute(
                    "INSERT OR IGNORE INTO thesis_evidence (thesis_id, version_number, claim_id) VALUES (?, ?, ?)",
                    (thesis_id, version, claim["claim_id"]),
                )
            change_id = "change_" + hashlib.sha256(f"{thesis_id}\n{version}".encode()).hexdigest()[:24]
            con.execute(
                """
                INSERT OR REPLACE INTO thesis_changes (
                    change_id, thesis_id, from_version, to_version, change_type, change_score, summary
                ) VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    change_id, thesis_id, version - 1 or None, version,
                    snapshot["change_type"], snapshot["thesis_change_score"], snapshot["change_summary"],
                ),
            )
            record_usage(con, result, workload="thesis_update", object_type="thesis", object_id=thesis_id)
            con.commit()
            stats["versioned"] += 1
            stats["cost_usd"] = round(float(stats["cost_usd"]) + result.estimated_cost_usd, 8)
        except Exception as exc:
            con.rollback()
            record_usage(con, None, workload="thesis_update", object_type="author_theme", object_id=f"{author_id}:{theme_id}", error=exc)
            con.commit()
            stats["failed"] += 1
            print(f"warning: thesis update failed author={author_id} theme={theme_name}: {type(exc).__name__}: {exc}")
    return stats


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--db", default=DB_PATH)
    parser.add_argument("--limit", type=int, default=int(os.getenv("THESIS_AI_MAX_UPDATES", "4")))
    args = parser.parse_args()
    if args.limit < 0 or args.limit > 30:
        raise SystemExit("--limit must be between 0 and 30")
    init_db(args.db)
    con = sqlite3.connect(args.db, timeout=120)
    stats = update_pending_theses(con, args.limit)
    con.close()
    print(json.dumps(stats, ensure_ascii=False, sort_keys=True))


if __name__ == "__main__":
    main()
