#!/usr/bin/env python3
"""Independent Terra analyst and cross-author synthesis for important Theses."""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import sqlite3
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from signalboard.ai.router import call_json, record_usage
from signalboard.db import init_db

DB_PATH = "/workspace/data/signalboard_full.db"

ANALYST_SCHEMA = {
    "type": "object", "additionalProperties": False,
    "properties": {
        "author_view": {"type": "string"}, "facts": {"type": "array", "items": {"type": "string"}},
        "verified_evidence": {"type": "array", "items": {"type": "string"}},
        "logic_chain": {"type": "array", "items": {"type": "string"}},
        "ai_assessment": {"type": "string"}, "counter_case": {"type": "array", "items": {"type": "string"}},
        "second_order_effects": {"type": "array", "items": {"type": "string"}},
        "beneficiaries": {"type": "array", "items": {"type": "string"}},
        "negative_exposure": {"type": "array", "items": {"type": "string"}},
        "valuation_questions": {"type": "array", "items": {"type": "string"}},
        "actionability": {"type": "string", "enum": [
            "NOT_ACTIONABLE", "WATCH", "RESEARCH", "BUY_CANDIDATE", "HEDGE_CANDIDATE", "AVOID"
        ]},
        "catalysts": {"type": "array", "items": {"type": "string"}},
        "invalidation_conditions": {"type": "array", "items": {"type": "string"}},
        "unknowns": {"type": "array", "items": {"type": "string"}},
        "scores": {"type": "object", "additionalProperties": False, "properties": {
            "thesis_quality": {"type": "integer", "minimum": 0, "maximum": 100},
            "evidence_quality": {"type": "integer", "minimum": 0, "maximum": 100},
            "novelty": {"type": "integer", "minimum": 0, "maximum": 100},
            "mispricing_potential": {"type": "integer", "minimum": 0, "maximum": 100},
            "actionability": {"type": "integer", "minimum": 0, "maximum": 100},
        }, "required": ["thesis_quality", "evidence_quality", "novelty", "mispricing_potential", "actionability"]},
    },
    "required": [
        "author_view", "facts", "verified_evidence", "logic_chain", "ai_assessment", "counter_case",
        "second_order_effects", "beneficiaries", "negative_exposure", "valuation_questions",
        "actionability", "catalysts", "invalidation_conditions", "unknowns", "scores",
    ],
}

CROSS_SCHEMA = {
    "type": "object", "additionalProperties": False,
    "properties": {
        "consensus": {"type": "array", "items": {"type": "string"}},
        "disagreement": {"type": "array", "items": {"type": "string"}},
        "different_assumptions": {"type": "array", "items": {"type": "string"}},
        "different_time_horizons": {"type": "array", "items": {"type": "string"}},
        "different_preferred_stocks": {"type": "array", "items": {"type": "string"}},
        "same_thesis_different_parts": {"type": "array", "items": {"type": "string"}},
        "true_conflicts": {"type": "array", "items": {"type": "string"}},
        "ai_synthesis": {"type": "string"},
    },
    "required": ["consensus", "disagreement", "different_assumptions", "different_time_horizons",
                 "different_preferred_stocks", "same_thesis_different_parts", "true_conflicts", "ai_synthesis"],
}

SYSTEM = """你是独立的半导体投资研究 Analyst，不是作者观点复述器。
严格分开 AUTHOR VIEW、FACT、VERIFIED EVIDENCE、AI INFERENCE。相同 underlying source 的社交转发只算一份证据。
主动寻找反例、矛盾、二阶影响、时间跨度冲突和估值仍待回答的问题。未经验证的数字不能进入 facts。
actionability 只能使用 NOT_ACTIONABLE/WATCH/RESEARCH/BUY_CANDIDATE/HEDGE_CANDIDATE/AVOID；BUY_CANDIDATE 只表示值得深度估值，不是买入建议。
不得输出 BUY 或 SELL。"""

CROSS_SYSTEM = """你负责 Cross-Author Thesis。区分真正观点分歧与同一因果链的不同环节；
比较假设、时间跨度和偏好股票。同一 underlying source 的转发不是独立共识。不得给 BUY/SELL。"""


def _thesis_payload(con: sqlite3.Connection, thesis_id: str, version: int) -> dict:
    row = con.execute(
        """SELECT th.author_id,t.name,tv.snapshot_json,tv.change_type,tv.thesis_change_score
           FROM theses th JOIN themes t ON t.theme_id=th.theme_id
           JOIN thesis_versions tv ON tv.thesis_id=th.thesis_id AND tv.version_number=?
           WHERE th.thesis_id=?""", (version, thesis_id),
    ).fetchone()
    claims = []
    for claim_id, text, ctype, status, post_id in con.execute(
        """SELECT c.claim_id,c.claim_text,c.claim_type,c.verification_status,c.source_post_id
           FROM thesis_evidence te JOIN claims c ON c.claim_id=te.claim_id
           WHERE te.thesis_id=? AND te.version_number=?""", (thesis_id, version),
    ).fetchall():
        verification = con.execute(
            """SELECT rationale,corrected_claim,sources_json FROM claim_verifications
               WHERE claim_id=? ORDER BY verification_version DESC LIMIT 1""", (claim_id,),
        ).fetchone()
        underlying = [r[0] for r in con.execute(
            "SELECT DISTINCT underlying_source_id FROM source_memberships WHERE mention_post_id=?", (post_id,)
        ).fetchall()]
        media = [json.loads(r[0]) for r in con.execute(
            """SELECT ma.analysis_json FROM media_assets m JOIN media_analyses ma ON ma.media_id=m.media_id
               WHERE m.post_id=?""", (post_id,)
        ).fetchall()]
        claims.append({
            "claim_id": claim_id, "text": text, "type": ctype, "verification_status": status,
            "verification": None if not verification else {
                "rationale": verification[0], "corrected_claim": verification[1],
                "sources": json.loads(verification[2] or "[]"),
            },
            "underlying_source_ids": underlying, "media_analysis": media,
        })
    return {
        "thesis_id": thesis_id, "version": version, "author_id": row[0], "theme": row[1],
        "author_thesis": json.loads(row[2]), "change_type": row[3], "change_score": row[4],
        "claims": claims,
        "evidence_accounting": {
            "social_mentions": len({x["claim_id"] for x in claims}),
            "independent_evidence": len({u for x in claims for u in x["underlying_source_ids"]}),
        },
    }


def analyze(con: sqlite3.Connection, limit: int, themes: list[str] | None = None,
            deep_analysis: bool = False, post_ids: list[str] | None = None) -> dict:
    params: list[object] = []
    where = ["NOT EXISTS (SELECT 1 FROM thesis_analyses ta WHERE ta.thesis_id=th.thesis_id AND ta.thesis_version=th.current_version)"]
    if themes:
        where.append(f"lower(t.name) IN ({','.join('?' for _ in themes)})")
        params.extend(x.casefold() for x in themes)
    if post_ids:
        where.append(
            f"EXISTS (SELECT 1 FROM thesis_evidence te JOIN claims c ON c.claim_id=te.claim_id "
            f"WHERE te.thesis_id=th.thesis_id AND te.version_number=th.current_version "
            f"AND c.source_post_id IN ({','.join('?' for _ in post_ids)}))"
        )
        params.extend(post_ids)
    params.append(limit)
    rows = con.execute(
        f"""SELECT th.thesis_id,th.current_version,t.name FROM theses th JOIN themes t ON t.theme_id=th.theme_id
            WHERE th.current_version>0 AND {' AND '.join(where)}
            ORDER BY th.confidence DESC,th.last_updated DESC LIMIT ?""", params,
    ).fetchall()
    stats = {"selected": len(rows), "analyzed": 0, "cross_author": 0, "failed_retryable": 0, "cost_usd": 0.0}
    workload = "deep_investment_analysis" if deep_analysis else "ai_analyst"
    for thesis_id, version, theme_name in rows:
        try:
            payload = _thesis_payload(con, thesis_id, version)
            result = call_json(
                workload, SYSTEM, json.dumps(payload, ensure_ascii=False), ANALYST_SCHEMA,
                schema_name="signalboard_ai_analyst", max_output_tokens=4200, timeout=180,
            )
            con.execute(
                """INSERT OR REPLACE INTO thesis_analyses
                   (thesis_id,thesis_version,analysis_json,model,analysis_mode) VALUES (?,?,?,?,?)""",
                (thesis_id, version, json.dumps(result.data, ensure_ascii=False), result.model,
                 "SOL_DEEP" if deep_analysis else "TERRA"),
            )
            record_usage(con, result, workload=workload, object_type="thesis_analysis", object_id=thesis_id)
            con.commit()
            stats["analyzed"] += 1
            stats["cost_usd"] = round(stats["cost_usd"] + result.estimated_cost_usd, 8)
        except Exception as exc:
            con.rollback()
            record_usage(con, None, workload=workload, object_type="thesis_analysis", object_id=thesis_id, error=exc)
            con.commit()
            stats["failed_retryable"] += 1
            print(f"warning: analyst failed thesis={thesis_id}: {type(exc).__name__}: {exc}")

    # Cross-author only after individual analyses exist, and only when at least two authors cover the theme.
    theme_rows = con.execute(
        """SELECT t.theme_id,t.name FROM themes t JOIN theses th ON th.theme_id=t.theme_id
           WHERE th.current_version>0 AND t.parent_theme_id IS NULL
           GROUP BY t.theme_id,t.name HAVING COUNT(DISTINCT th.author_id)>=2"""
    ).fetchall()
    for theme_id, theme_name in theme_rows:
        if themes and theme_name.casefold() not in {x.casefold() for x in themes}:
            continue
        if post_ids:
            match = con.execute(
                f"""SELECT 1 FROM theses th JOIN thesis_evidence te ON te.thesis_id=th.thesis_id
                    JOIN claims c ON c.claim_id=te.claim_id
                    WHERE th.theme_id=? AND te.version_number=th.current_version
                      AND c.source_post_id IN ({','.join('?' for _ in post_ids)}) LIMIT 1""",
                [theme_id, *post_ids],
            ).fetchone()
            if not match:
                continue
        views = []
        for thesis_id, author_id, version, snapshot, analysis in con.execute(
            """SELECT th.thesis_id,th.author_id,th.current_version,tv.snapshot_json,ta.analysis_json
               FROM theses th JOIN thesis_versions tv ON tv.thesis_id=th.thesis_id AND tv.version_number=th.current_version
               LEFT JOIN thesis_analyses ta ON ta.thesis_id=th.thesis_id AND ta.thesis_version=th.current_version
               WHERE th.theme_id=?""", (theme_id,),
        ).fetchall():
            views.append({"author_id": author_id, "thesis": json.loads(snapshot),
                          "analysis": json.loads(analysis) if analysis else None})
        digest = hashlib.sha256(json.dumps(views, ensure_ascii=False, sort_keys=True).encode()).hexdigest()
        old = con.execute("SELECT source_digest FROM cross_author_theses WHERE theme_id=?", (theme_id,)).fetchone()
        if old and old[0] == digest:
            continue
        try:
            result = call_json(
                "cross_author_analysis", CROSS_SYSTEM,
                json.dumps({"theme": theme_name, "author_views": views}, ensure_ascii=False), CROSS_SCHEMA,
                schema_name="signalboard_cross_author", max_output_tokens=3000, timeout=180,
            )
            con.execute(
                """INSERT OR REPLACE INTO cross_author_theses
                   (theme_id,analysis_json,model,source_digest,updated_at)
                   VALUES (?,?,?,?,strftime('%Y-%m-%dT%H:%M:%fZ','now'))""",
                (theme_id, json.dumps(result.data, ensure_ascii=False), result.model, digest),
            )
            record_usage(con, result, workload="cross_author_analysis", object_type="theme", object_id=theme_id)
            con.commit()
            stats["cross_author"] += 1
            stats["cost_usd"] = round(stats["cost_usd"] + result.estimated_cost_usd, 8)
        except Exception as exc:
            con.rollback()
            record_usage(con, None, workload="cross_author_analysis", object_type="theme", object_id=theme_id, error=exc)
            con.commit()
            stats["failed_retryable"] += 1
    return stats


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--db", default=DB_PATH)
    ap.add_argument("--limit", type=int, default=4)
    ap.add_argument("--themes", help="逗号分隔 canonical theme names")
    ap.add_argument("--post-ids", help="逗号分隔精确 post_id；Golden 定向分析")
    ap.add_argument("--deep-analysis", action="store_true", help="仅用户主动触发；使用 Sol，不得用于 daily")
    args = ap.parse_args()
    if args.deep_analysis:
        os.environ.setdefault("AI_EXPENSIVE_JOB", "true")
    init_db(args.db)
    con = sqlite3.connect(args.db, timeout=120)
    themes = [x.strip() for x in (args.themes or "").split(",") if x.strip()]
    post_ids = [x.strip() for x in (args.post_ids or "").split(",") if x.strip()]
    stats = analyze(con, args.limit, themes or None, args.deep_analysis, post_ids or None)
    con.close()
    print(json.dumps(stats, ensure_ascii=False, sort_keys=True))


if __name__ == "__main__":
    main()
