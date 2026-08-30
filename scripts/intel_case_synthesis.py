#!/usr/bin/env python3
"""Cross-theme synthesis for bounded, human-defined research cases."""
from __future__ import annotations

import argparse
import hashlib
import json
import sqlite3
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from signalboard.ai.router import call_json, record_usage
from signalboard.db import init_db

DB_PATH = "/workspace/data/signalboard_full.db"
CASES = Path(__file__).resolve().parent.parent / "tests" / "golden_cases.json"

SCHEMA = {
    "type": "object", "additionalProperties": False,
    "properties": {
        "author_views": {"type": "array", "items": {"type": "object", "additionalProperties": False,
            "properties": {"author": {"type": "string"}, "view": {"type": "string"}},
            "required": ["author", "view"]}},
        "facts": {"type": "array", "items": {"type": "string"}},
        "verified_evidence": {"type": "array", "items": {"type": "string"}},
        "logic_chain": {"type": "array", "items": {"type": "string"}},
        "corrections": {"type": "array", "items": {"type": "string"}},
        "contradictions": {"type": "array", "items": {"type": "string"}},
        "ai_assessment": {"type": "string"},
        "counter_case": {"type": "array", "items": {"type": "string"}},
        "second_order_effects": {"type": "array", "items": {"type": "string"}},
        "beneficiaries": {"type": "array", "items": {"type": "string"}},
        "negative_exposure": {"type": "array", "items": {"type": "string"}},
        "risks": {"type": "array", "items": {"type": "string"}},
        "valuation_questions": {"type": "array", "items": {"type": "string"}},
        "catalysts": {"type": "array", "items": {"type": "string"}},
        "invalidation_conditions": {"type": "array", "items": {"type": "string"}},
        "unknowns": {"type": "array", "items": {"type": "string"}},
        "actionability": {"type": "string", "enum": [
            "NOT_ACTIONABLE", "WATCH", "RESEARCH", "BUY_CANDIDATE", "HEDGE_CANDIDATE", "AVOID"
        ]},
        "scores": {"type": "object", "additionalProperties": False, "properties": {
            "thesis_quality": {"type": "integer", "minimum": 0, "maximum": 100},
            "evidence_quality": {"type": "integer", "minimum": 0, "maximum": 100},
            "novelty": {"type": "integer", "minimum": 0, "maximum": 100},
            "mispricing_potential": {"type": "integer", "minimum": 0, "maximum": 100},
            "actionability": {"type": "integer", "minimum": 0, "maximum": 100}
        }, "required": ["thesis_quality", "evidence_quality", "novelty", "mispricing_potential", "actionability"]}
    },
    "required": ["author_views", "facts", "verified_evidence", "logic_chain", "corrections",
                 "contradictions", "ai_assessment", "counter_case", "second_order_effects",
                 "beneficiaries", "negative_exposure", "risks", "valuation_questions", "catalysts",
                 "invalidation_conditions", "unknowns", "actionability", "scores"]
}

SYSTEM = """你是独立的跨 Theme 半导体研究 Analyst。输入是一个人工定义边界的 Golden Research Case，而不是预设答案。
必须把社交原话、图片内容、经核验事实、作者推论和 AI 推论分开；同一 underlying_source_id 的转发只算一份证据。
逐条回答 audit_questions，但答案必须由输入证据支持；若证据不足，明确放进 unknowns，不可迎合问题暗示。
检查数字口径、总量/增量、时间范围、架构条件和因果链跳步。主动生成 counter case、contradiction 与 second-order effects。
actionability 只能是 NOT_ACTIONABLE/WATCH/RESEARCH/BUY_CANDIDATE/HEDGE_CANDIDATE/AVOID；绝不输出 BUY/SELL。"""


def _context_ids(con: sqlite3.Connection, seeds: list[str]) -> list[str]:
    rows = con.execute(
        f"SELECT DISTINCT post_id FROM post_graph_memberships WHERE root_post_id IN ({','.join('?' for _ in seeds)})",
        seeds,
    ).fetchall()
    return sorted(set(seeds) | {r[0] for r in rows})


def _payload(con: sqlite3.Connection, case_id: str, spec: dict) -> dict:
    ids = _context_ids(con, spec["seed_post_ids"])
    ph = ",".join("?" for _ in ids)
    posts = [{"post_id": r[0], "source_id": r[1], "published_at": r[2], "text": r[3]}
             for r in con.execute(f"SELECT post_id,source_id,published_at,raw_text FROM raw_posts WHERE post_id IN ({ph})", ids)]
    media = [json.loads(r[0]) for r in con.execute(
        f"""SELECT ma.analysis_json FROM media_assets m JOIN media_analyses ma ON ma.media_id=m.media_id
            WHERE m.post_id IN ({ph})""", ids).fetchall()]
    claims = []
    for row in con.execute(
        f"""SELECT c.claim_id,c.claim_text,c.claim_type,c.author_id,c.verification_status,c.source_post_id,
                   cv.rationale,cv.corrected_claim,cv.sources_json
            FROM claims c LEFT JOIN claim_verifications cv ON cv.claim_id=c.claim_id
              AND cv.verification_version=(SELECT MAX(v.verification_version) FROM claim_verifications v WHERE v.claim_id=c.claim_id)
            WHERE c.source_post_id IN ({ph}) ORDER BY c.point_in_time""", ids,
    ).fetchall():
        sources = json.loads(row[8] or "[]")[:4]
        claims.append({"claim_id": row[0], "text": row[1], "type": row[2], "author": row[3],
                       "verification_status": row[4], "source_post_id": row[5],
                       "verification_rationale": row[6], "corrected_claim": row[7], "sources": sources})
    source_groups = [{"underlying_source_id": r[0], "source_class": r[1], "publisher": r[2],
                      "title": r[3], "url": r[4], "social_mentions": r[5]}
                     for r in con.execute(
        f"""SELECT us.underlying_source_id,us.source_class,us.publisher,us.title,us.canonical_url,
                   COUNT(DISTINCT sm.mention_post_id) AS social_mentions
            FROM underlying_sources us JOIN source_memberships sm USING(underlying_source_id)
            WHERE sm.mention_post_id IN ({ph}) GROUP BY us.underlying_source_id
            ORDER BY social_mentions DESC LIMIT 30""", ids).fetchall()]
    related = []
    for row in con.execute(
        f"""SELECT DISTINCT th.thesis_id,th.author_id,t.name,tv.snapshot_json,ta.analysis_json
            FROM thesis_evidence te JOIN claims c ON c.claim_id=te.claim_id
            JOIN theses th ON th.thesis_id=te.thesis_id
            JOIN themes t ON t.theme_id=th.theme_id
            JOIN thesis_versions tv ON tv.thesis_id=th.thesis_id AND tv.version_number=th.current_version
            LEFT JOIN thesis_analyses ta ON ta.thesis_id=th.thesis_id AND ta.thesis_version=th.current_version
            WHERE c.source_post_id IN ({ph})""", ids).fetchall():
        related.append({"thesis_id": row[0], "author_id": row[1], "theme": row[2],
                        "thesis": json.loads(row[3]), "analyst": json.loads(row[4]) if row[4] else None})
    return {"case_id": case_id, "title": spec["title"], "audit_questions": spec.get("audit_questions", []),
            "posts": posts, "media": media, "claims": claims, "source_groups": source_groups,
            "author_theme_theses": related}


def synthesize(con: sqlite3.Connection, cases: dict, selected: list[str] | None = None) -> dict:
    stats = {"selected": 0, "synthesized": 0, "failed_retryable": 0, "cost_usd": 0.0}
    for case_id, spec in cases.items():
        if selected and case_id not in selected:
            continue
        stats["selected"] += 1
        payload = _payload(con, case_id, spec)
        digest = hashlib.sha256(json.dumps(payload, ensure_ascii=False, sort_keys=True).encode()).hexdigest()
        old = con.execute("SELECT source_digest FROM research_case_analyses WHERE case_id=?", (case_id,)).fetchone()
        if old and old[0] == digest:
            continue
        try:
            result = call_json(
                "research_case_synthesis", SYSTEM, json.dumps(payload, ensure_ascii=False), SCHEMA,
                schema_name="signalboard_research_case", max_output_tokens=5200, timeout=240,
            )
            con.execute(
                """INSERT OR REPLACE INTO research_case_analyses
                   (case_id,title,analysis_json,source_digest,model,updated_at)
                   VALUES (?,?,?,?,?,strftime('%Y-%m-%dT%H:%M:%fZ','now'))""",
                (case_id, spec["title"], json.dumps(result.data, ensure_ascii=False), digest, result.model),
            )
            record_usage(con, result, workload="research_case_synthesis", object_type="research_case", object_id=case_id)
            con.commit()
            stats["synthesized"] += 1
            stats["cost_usd"] = round(stats["cost_usd"] + result.estimated_cost_usd, 8)
        except Exception as exc:
            con.rollback()
            record_usage(con, None, workload="research_case_synthesis", object_type="research_case", object_id=case_id, error=exc)
            con.commit()
            stats["failed_retryable"] += 1
            print(f"warning: case synthesis failed case={case_id}: {type(exc).__name__}: {exc}")
    return stats


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--db", default=DB_PATH)
    ap.add_argument("--cases", default=str(CASES))
    ap.add_argument("--case", action="append", dest="selected")
    args = ap.parse_args()
    init_db(args.db)
    cases = json.loads(Path(args.cases).read_text(encoding="utf-8"))
    con = sqlite3.connect(args.db, timeout=120)
    stats = synthesize(con, cases, args.selected)
    con.close()
    print(json.dumps(stats, ensure_ascii=False, sort_keys=True))


if __name__ == "__main__":
    main()
