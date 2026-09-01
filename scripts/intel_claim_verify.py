#!/usr/bin/env python3
"""Verify high-importance Claims with source-prioritized Responses web search."""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import sqlite3
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from signalboard.ai.guardrails import AIGuardrailBlocked
from signalboard.ai.router import call_json_web, record_usage
from signalboard.db import init_db
from scripts.intel_source_dedup import canonical_url

DB_PATH = "/workspace/data/signalboard_full.db"
VERIFY_VERSION = 1

SCHEMA = {
    "type": "object", "additionalProperties": False,
    "properties": {
        "status": {"type": "string", "enum": [
            "UNVERIFIED", "SUPPORTED_BY_PRIMARY", "SUPPORTED_BY_SECONDARY",
            "PARTIALLY_SUPPORTED", "CONTRADICTED", "UNVERIFIABLE",
        ]},
        "rationale": {"type": "string"},
        "corrected_claim": {"type": "string"},
        "sources": {"type": "array", "items": {
            "type": "object", "additionalProperties": False,
            "properties": {
                "title": {"type": "string"}, "url": {"type": "string"},
                "publisher": {"type": "string"},
                "source_tier": {"type": "string", "enum": ["PRIMARY", "SECONDARY", "INDUSTRY"]},
                "support": {"type": "string", "enum": ["SUPPORTS", "PARTIAL", "CONTRADICTS", "CONTEXT_ONLY"]},
                "finding": {"type": "string"},
            },
            "required": ["title", "url", "publisher", "source_tier", "support", "finding"],
        }},
        "unknowns": {"type": "array", "items": {"type": "string"}},
    },
    "required": ["status", "rationale", "corrected_claim", "sources", "unknowns"],
}

SYSTEM = """你是投资研究事实核验员，必须使用 web search。
证据优先级：1) 公司公告/财报/IR、交易所文件、SEC、政府官方数据；2) Reuters/Bloomberg/FT/WSJ；3) 行业媒体。
X/社交帖子只能是 AUTHOR CLAIM，绝不能独立确认事实。必须区分公告事实、媒体报道、作者推论和未知。
SUPPORTED_BY_PRIMARY 需要直接的一级来源；只有权威媒体则用 SUPPORTED_BY_SECONDARY。
若原话把“长期总共5座”误写成“额外新建5座”，必须 PARTIALLY_SUPPORTED 或 CONTRADICTED 并给 corrected_claim。
不要用搜索摘要替代来源内容，不要编造 URL。"""


def importance_score(claim_type: str, confidence: float, text: str) -> float:
    base = {"FACT": 88, "FORECAST": 78, "RISK": 76, "CATALYST": 75,
            "VALUATION": 70, "INFERENCE": 62, "OPINION": 45,
            "POSITION": 35, "QUESTION": 20}.get(claim_type, 40)
    numeric = 7 if any(ch.isdigit() for ch in text) else 0
    return min(100.0, round(base + numeric + (confidence - 0.5) * 10, 1))


def _targets(con: sqlite3.Connection, limit: int, post_ids: list[str] | None) -> list[dict]:
    where = ["NOT EXISTS (SELECT 1 FROM claim_verifications cv WHERE cv.claim_id=c.claim_id AND cv.verification_version=?)"]
    params: list[object] = [VERIFY_VERSION]
    if post_ids:
        where.append(f"c.source_post_id IN ({','.join('?' for _ in post_ids)})")
        params.extend(post_ids)
    rows = con.execute(
        f"""SELECT c.claim_id,c.claim_text,c.claim_type,c.author_id,c.companies_json,c.themes_json,
                   c.time_horizon,c.confidence,c.point_in_time,c.source_post_id,
                   EXISTS(
                     SELECT 1 FROM thesis_evidence te JOIN theses t ON t.thesis_id=te.thesis_id
                     WHERE te.claim_id=c.claim_id AND t.current_version=1
                   ) AS new_thesis,
                   EXISTS(
                     SELECT 1 FROM thesis_evidence te JOIN thesis_versions tv
                       ON tv.thesis_id=te.thesis_id AND tv.version_number=te.version_number
                     WHERE te.claim_id=c.claim_id AND tv.thesis_change_score>=0.5
                   ) AS thesis_change,
                   EXISTS(
                     SELECT 1 FROM thesis_evidence te JOIN thesis_analyses ta
                       ON ta.thesis_id=te.thesis_id AND ta.thesis_version=te.version_number
                     WHERE te.claim_id=c.claim_id AND (
                       ta.analysis_json LIKE '%\"actionability\": \"BUY_CANDIDATE\"%'
                       OR ta.analysis_json LIKE '%\"actionability\": \"HEDGE_CANDIDATE\"%'
                       OR ta.analysis_json LIKE '%\"actionability\": \"AVOID\"%'
                     )
                   ) AS high_actionability
            FROM claims c WHERE {' AND '.join(where)} ORDER BY c.confidence DESC, c.created_at DESC""", params
    ).fetchall()
    targets = []
    importance_threshold = float(os.getenv("CLAIM_VERIFY_IMPORTANCE_THRESHOLD", "80"))
    author_confidence_threshold = float(os.getenv("CLAIM_VERIFY_AUTHOR_CONFIDENCE_THRESHOLD", "0.85"))
    for row in rows:
        score = importance_score(row[2], float(row[7]), row[1])
        priority_reasons = []
        if bool(row[10]):
            priority_reasons.append("new_thesis")
        if bool(row[11]):
            priority_reasons.append("thesis_change")
        if bool(row[12]):
            priority_reasons.append("high_actionability")
        if row[3] and float(row[7]) >= author_confidence_threshold:
            priority_reasons.append("high_confidence_author_claim")
        if score >= importance_threshold and priority_reasons:
            targets.append({
                "claim_id": row[0], "claim_text": row[1], "claim_type": row[2], "author_id": row[3],
                "companies": json.loads(row[4] or "[]"), "themes": json.loads(row[5] or "[]"),
                "time_horizon": row[6], "confidence": row[7], "point_in_time": row[8],
                "source_post_id": row[9], "importance_score": score,
                "priority_reasons": priority_reasons,
            })
    targets.sort(key=lambda item: (-item["importance_score"], -item["confidence"], item["claim_id"]))
    return targets[:limit]


def _source_id(url: str) -> str:
    return "ext_" + hashlib.sha256(canonical_url(url).encode()).hexdigest()[:24]


def verify_claims(con: sqlite3.Connection, limit: int, post_ids: list[str] | None = None) -> dict:
    stats = {"selected": 0, "verified": 0, "failed_retryable": 0, "cost_usd": 0.0, "statuses": {}}
    for claim in _targets(con, limit, post_ids):
        stats["selected"] += 1
        try:
            result = call_json_web(
                "claim_verification", SYSTEM,
                json.dumps({
                    "claim": claim,
                    "instruction": "寻找截至当前可用的最高优先级独立来源；逐字核验数量、时点、总量/增量与条件。",
                }, ensure_ascii=False),
                SCHEMA, schema_name="signalboard_claim_verification", max_output_tokens=2600, timeout=180,
                prompt_version=f"claim-verification-v{VERIFY_VERSION}", entity_type="claim", entity_id=claim["claim_id"],
            )
            data = result.data
            returned_urls = {canonical_url(str(x.get("url") or "")) for x in (result.sources or []) if x.get("url")}
            accepted_sources = []
            for source in data["sources"]:
                if not source["url"]:
                    continue
                url = canonical_url(source["url"])
                # Structured URLs must be grounded in the web_search call's full source list.
                if url not in returned_urls:
                    continue
                source["url"] = url
                accepted_sources.append(source)
                sid = _source_id(url)
                con.execute(
                    """INSERT INTO external_sources
                       (source_id,source_type,publisher,title,url,primary_or_secondary,reliability_score,crawl_status)
                       VALUES (?,?,?,?,?,?,?,'complete')
                       ON CONFLICT(url) DO UPDATE SET publisher=excluded.publisher,title=excluded.title,
                         primary_or_secondary=excluded.primary_or_secondary,crawl_status='complete',
                         updated_at=strftime('%Y-%m-%dT%H:%M:%fZ','now')""",
                    (sid, "verification", source["publisher"], source["title"], url,
                     source["source_tier"].lower(), 0.95 if source["source_tier"] == "PRIMARY" else 0.85),
                )
                actual = con.execute("SELECT source_id FROM external_sources WHERE url=?", (url,)).fetchone()[0]
                uid = "underlying_" + hashlib.sha256(f"url:{url}".encode()).hexdigest()[:24]
                con.execute(
                    """INSERT OR IGNORE INTO underlying_sources
                       (underlying_source_id,canonical_url,publisher,title,source_class)
                       VALUES (?,?,?,?,?)""", (uid, url, source["publisher"], source["title"], source["source_tier"]),
                )
                con.execute(
                    """INSERT OR IGNORE INTO source_memberships
                       (underlying_source_id,evidence_type,evidence_id,mention_post_id,relation_type)
                       VALUES (?,'external',?,?,'verifies')""", (uid, actual, claim["source_post_id"]),
                )
            # Do not allow a supported status without a retained independent source.
            status = data["status"]
            if status.startswith("SUPPORTED") and not accepted_sources:
                status = "UNVERIFIED"
                data["rationale"] += " 未保留到可追溯的 web_search 来源。"
            con.execute(
                """INSERT OR REPLACE INTO claim_verifications
                   (claim_id,verification_version,importance_score,status,rationale,corrected_claim,sources_json,model)
                   VALUES (?,?,?,?,?,?,?,?)""",
                (claim["claim_id"], VERIFY_VERSION, claim["importance_score"], status, data["rationale"],
                 data["corrected_claim"] or None, json.dumps(accepted_sources, ensure_ascii=False), result.model),
            )
            con.execute("UPDATE claims SET verification_status=? WHERE claim_id=?", (status, claim["claim_id"]))
            record_usage(con, result, workload="claim_verification", object_type="claim", object_id=claim["claim_id"])
            con.commit()
            stats["verified"] += 1
            stats["statuses"][status] = stats["statuses"].get(status, 0) + 1
            stats["cost_usd"] = round(stats["cost_usd"] + result.estimated_cost_usd, 8)
        except AIGuardrailBlocked as exc:
            con.rollback()
            stats["budget_blocked"] = stats.get("budget_blocked", 0) + 1
            stats["stop_reason"] = exc.reason
            print(f"AI_GUARDRAIL_STOP claim={claim['claim_id']} reason={exc.reason}")
            break
        except Exception as exc:
            con.rollback()
            record_usage(con, None, workload="claim_verification", object_type="claim", object_id=claim["claim_id"], error=exc)
            con.commit()
            stats["failed_retryable"] += 1
            print(f"warning: verification failed claim={claim['claim_id']}: {type(exc).__name__}: {exc}")
    return stats


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--db", default=DB_PATH)
    ap.add_argument("--limit", type=int, default=8)
    ap.add_argument("--post-ids")
    args = ap.parse_args()
    if args.limit < 0 or args.limit > 50:
        raise SystemExit("--limit must be between 0 and 50")
    if args.limit > int(os.getenv("CLAIM_VERIFY_MAX_ITEMS", "8")):
        os.environ.setdefault("AI_JOB_KIND", "historical_claim_verification")
    init_db(args.db)
    con = sqlite3.connect(args.db, timeout=120)
    post_ids = [x.strip() for x in (args.post_ids or "").split(",") if x.strip()]
    stats = verify_claims(con, args.limit, post_ids or None)
    con.close()
    print(json.dumps(stats, ensure_ascii=False, sort_keys=True))


if __name__ == "__main__":
    main()
