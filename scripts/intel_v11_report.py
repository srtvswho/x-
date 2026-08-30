#!/usr/bin/env python3
"""Produce the v1.1 evidence graph, coverage and cost audit as JSON."""
from __future__ import annotations

import argparse
import json
import sqlite3
from pathlib import Path

import sys
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from signalboard.db import init_db

DB_PATH = "/workspace/data/signalboard_full.db"
CASES = Path(__file__).resolve().parent.parent / "tests" / "golden_cases.json"


def _case_graph(con: sqlite3.Connection, case_id: str, spec: dict) -> dict:
    ids = spec["seed_post_ids"]
    ph = ",".join("?" for _ in ids)
    posts = [{"post_id": r[0], "source_id": r[1], "published_at": r[2], "text": r[3]}
             for r in con.execute(f"SELECT post_id,source_id,published_at,raw_text FROM raw_posts WHERE post_id IN ({ph}) ORDER BY published_at", ids)]
    edges = [{"source_post_id": r[0], "target_post_id": r[1], "type": r[2], "status": r[3]}
             for r in con.execute(f"SELECT source_post_id,target_post_id,reference_type,fetch_status FROM post_references WHERE source_post_id IN ({ph}) OR target_post_id IN ({ph})", ids + ids)]
    media = [{"media_id": r[0], "post_id": r[1], "status": r[2], "hash": r[3], "analysis": json.loads(r[4]) if r[4] else None}
             for r in con.execute(f"""SELECT m.media_id,m.post_id,m.analysis_status,m.content_hash,ma.analysis_json
                                      FROM media_assets m LEFT JOIN media_analyses ma ON ma.media_id=m.media_id
                                      WHERE m.post_id IN ({ph})""", ids)]
    claims = [{"claim_id": r[0], "post_id": r[1], "author": r[2], "type": r[3], "text": r[4], "verification": r[5]}
              for r in con.execute(f"SELECT claim_id,source_post_id,author_id,claim_type,claim_text,verification_status FROM claims WHERE source_post_id IN ({ph})", ids)]
    sources = [{"underlying_source_id": r[0], "class": r[1], "publisher": r[2], "title": r[3], "url": r[4], "social_mentions": r[5]}
               for r in con.execute(f"""SELECT us.underlying_source_id,us.source_class,us.publisher,us.title,us.canonical_url,
                                          COUNT(DISTINCT sm.mention_post_id)
                                   FROM underlying_sources us JOIN source_memberships sm USING(underlying_source_id)
                                   WHERE sm.mention_post_id IN ({ph}) GROUP BY us.underlying_source_id""", ids)]
    verification = [{"claim_id": r[0], "status": r[1], "rationale": r[2], "corrected_claim": r[3],
                     "sources": json.loads(r[4] or "[]")}
                    for r in con.execute(f"""SELECT cv.claim_id,cv.status,cv.rationale,cv.corrected_claim,cv.sources_json
                                             FROM claim_verifications cv JOIN claims c ON c.claim_id=cv.claim_id
                                             WHERE c.source_post_id IN ({ph}) ORDER BY cv.verified_at""", ids)]
    case_row = con.execute(
        "SELECT title,analysis_json,model,updated_at FROM research_case_analyses WHERE case_id=?", (case_id,)
    ).fetchone()
    case_analysis = ({"title": case_row[0], "analysis": json.loads(case_row[1]),
                      "model": case_row[2], "updated_at": case_row[3]} if case_row else None)
    return {"posts": posts, "edges": edges, "media": media, "claims": claims,
            "claim_verifications": verification, "underlying_sources": sources,
            "research_case_analysis": case_analysis,
            "missing_seed_posts": sorted(set(ids) - {x["post_id"] for x in posts})}


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--db", default=DB_PATH)
    ap.add_argument("--output", default="outputs/thesis_engine_v11/v11_audit.json")
    args = ap.parse_args()
    init_db(args.db)
    cases = json.loads(CASES.read_text(encoding="utf-8"))
    con = sqlite3.connect(args.db, timeout=120)
    counts = {table: con.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0] for table in [
        "post_references", "media_assets", "media_analyses", "claims", "themes", "theses",
        "underlying_sources", "claim_verifications", "thesis_analyses", "cross_author_theses",
        "research_case_analyses",
    ]}
    pending = con.execute("""SELECT COUNT(*) FROM media_assets m LEFT JOIN media_analyses a ON a.media_id=m.media_id
                             WHERE a.media_id IS NULL""").fetchone()[0]
    duplicate_known = con.execute("""SELECT COALESCE(SUM(n-1),0) FROM (
                                      SELECT content_hash,COUNT(*) n FROM media_assets
                                      WHERE content_hash IS NOT NULL GROUP BY content_hash HAVING COUNT(*)>1)""").fetchone()[0]
    media_usage = con.execute("""SELECT input_tokens,output_tokens,latency_ms FROM ai_usage
                                 WHERE workload='media_understanding' AND status='ok'""").fetchall()
    avg_in = sum(r[0] for r in media_usage) / len(media_usage) if media_usage else 1200
    avg_out = sum(r[1] for r in media_usage) / len(media_usage) if media_usage else 570
    avg_latency = sum(r[2] for r in media_usage) / len(media_usage) if media_usage else 7000
    upper_calls = max(0, pending - duplicate_known)
    est_cost = upper_calls * (avg_in * 2 + avg_out * 12) / 1_000_000
    report = {
        "counts": counts,
        "theme_fragmentation": {
            "claims_per_theme": round(counts["claims"] / max(1, counts["themes"]), 3),
            "singleton_themes": con.execute("""SELECT COUNT(*) FROM (SELECT t.theme_id,COUNT(ct.claim_id) n
                                                FROM themes t LEFT JOIN claim_themes ct USING(theme_id)
                                                GROUP BY t.theme_id HAVING n<=1)""").fetchone()[0],
        },
        "media_backfill_estimate": {
            "total_assets": counts["media_assets"], "already_analyzed": counts["media_analyses"],
            "pending_assets": pending, "known_hash_duplicates": duplicate_known,
            "vision_calls_upper_bound": upper_calls,
            "estimated_input_tokens": round(upper_calls * avg_in),
            "estimated_output_tokens": round(upper_calls * avg_out),
            "estimated_cost_usd": round(est_cost, 2),
            "estimated_runtime_minutes_sequential": round(upper_calls * avg_latency / 60000, 1),
            "batch_size": 30,
        },
        "golden_evidence_graphs": {case_id: _case_graph(con, case_id, spec) for case_id, spec in cases.items()},
        "openai_actual": {
            "calls": con.execute("SELECT COUNT(*) FROM ai_usage WHERE provider='openai'").fetchone()[0],
            "cost_usd_recorded": round(con.execute("SELECT COALESCE(SUM(estimated_cost_usd),0) FROM ai_usage WHERE provider='openai'").fetchone()[0], 6),
        },
    }
    con.close()
    out = Path(args.output)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({"counts": counts, "media_backfill_estimate": report["media_backfill_estimate"]}, ensure_ascii=False, sort_keys=True))


if __name__ == "__main__":
    main()
