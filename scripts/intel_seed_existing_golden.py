#!/usr/bin/env python3
"""Idempotently seed archived Golden research without invoking any AI provider."""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import sqlite3
import sys
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from signalboard.db import init_db

ROOT = Path(__file__).resolve().parent.parent
DEFAULT_AUDIT = ROOT / "outputs/thesis_engine_v11/archive/2026-08-30/v11_audit.original.json"
DEFAULT_CASES = ROOT / "tests/golden_cases.json"
ARCHIVED_MEDIA_PROMPT_VERSION = "media-v1.1.0-archived-golden"
ARCHIVED_MODEL = "gpt-5.6-terra"
SEED_AUTHOR = "golden_case_consensus"


def _sha(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def _loads(value: str | None) -> dict[str, Any]:
    try:
        parsed = json.loads(value or "{}")
        return parsed if isinstance(parsed, dict) else {}
    except json.JSONDecodeError:
        return {}


def _media_url(con: sqlite3.Connection, post_id: str, media_id: str) -> str:
    row = con.execute("SELECT source_url FROM media_assets WHERE media_id=?", (media_id,)).fetchone()
    if row and row[0]:
        return str(row[0])
    raw = con.execute("SELECT raw_json FROM raw_posts WHERE post_id=?", (post_id,)).fetchone()
    payload = _loads(raw[0] if raw else None)
    expected = media_id.split("_", 1)[-1]
    for item in ((payload.get("extendedEntities") or {}).get("media") or []):
        if str(item.get("id_str") or item.get("id") or "") == expected:
            url = str(item.get("media_url_https") or item.get("media_url") or "").strip()
            if url:
                return url
    return f"archived://golden/{media_id}"


def _counts(con: sqlite3.Connection) -> dict[str, int]:
    names = [
        "raw_posts", "post_references", "post_graph_memberships", "media_assets", "media_analyses",
        "claims", "claim_verifications", "themes", "claim_themes", "underlying_sources",
        "source_memberships", "theses", "thesis_versions", "thesis_evidence", "thesis_analyses",
        "research_case_analyses", "golden_validations", "ai_usage_ledger",
    ]
    return {name: int(con.execute(f"SELECT COUNT(*) FROM {name}").fetchone()[0]) for name in names}


def seed(db_path: str | Path, audit_path: str | Path = DEFAULT_AUDIT, cases_path: str | Path = DEFAULT_CASES) -> dict[str, Any]:
    if os.getenv("AI_ENABLED", "false").strip().lower() in {"1", "true", "yes", "on"}:
        raise RuntimeError("Archived Golden seed refuses to run while AI_ENABLED=true")
    if os.getenv("SEED_EXISTING_RESULTS_ONLY", "false").strip().lower() not in {"1", "true", "yes", "on"}:
        raise RuntimeError("Set SEED_EXISTING_RESULTS_ONLY=true to acknowledge the zero-AI seed path")

    audit_file = Path(audit_path)
    audit = json.loads(audit_file.read_text(encoding="utf-8"))
    specs = json.loads(Path(cases_path).read_text(encoding="utf-8"))
    init_db(db_path)
    con = sqlite3.connect(db_path, timeout=120)
    con.execute("PRAGMA foreign_keys=ON")
    before = _counts(con)
    audit_digest = hashlib.sha256(audit_file.read_bytes()).hexdigest()

    try:
        for case_id, graph in audit["golden_evidence_graphs"].items():
            spec = specs[case_id]
            source_time = graph["research_case_analysis"]["updated_at"]
            theme_name = "China WFE" if case_id.startswith("case_a_") else "ABF substrate"
            theme_id = "theme_" + _sha(theme_name.casefold())[:20]
            existing = con.execute("SELECT theme_id FROM themes WHERE lower(name)=lower(?) LIMIT 1", (theme_name,)).fetchone()
            if existing:
                theme_id = str(existing[0])
            else:
                con.execute(
                    """INSERT INTO themes(theme_id,name,description,aliases_json,created_by,created_at,updated_at)
                       VALUES (?,?,?,?,?,?,?)""",
                    (theme_id, theme_name, f"Golden production thesis: {spec['title']}", "[]", "archived_golden", source_time, source_time),
                )

            for post in graph["posts"]:
                post_id = str(post["post_id"])
                published = str(post.get("published_at") or source_time)
                text = str(post.get("text") or "")
                con.execute(
                    """INSERT OR IGNORE INTO raw_posts
                       (post_id,source_id,platform,published_at,captured_at,raw_text,raw_url,raw_json,content_hash)
                       VALUES (?,?,?,?,?,?,?,?,?)""",
                    (post_id, post.get("source_id") or "golden_archive", "x", published, published, text,
                     f"https://x.com/i/status/{post_id}", None, _sha(text)),
                )
                con.execute(
                    """INSERT OR IGNORE INTO post_graph_memberships
                       (root_post_id,post_id,depth,reference_type,crawl_status,crawled_at)
                       VALUES (?,?,0,'original','complete',?)""", (post_id, post_id, source_time),
                )

            for edge in graph["edges"]:
                con.execute(
                    """INSERT INTO post_references
                       (source_post_id,target_post_id,reference_type,fetch_status,discovered_at,last_attempt_at)
                       VALUES (?,?,?,?,?,?)
                       ON CONFLICT(source_post_id,target_post_id,reference_type) DO UPDATE SET
                         fetch_status=excluded.fetch_status,last_attempt_at=excluded.last_attempt_at""",
                    (str(edge["source_post_id"]), str(edge["target_post_id"]), edge.get("type") or "referenced",
                     edge.get("status") or "pending", source_time, source_time),
                )

            for media in graph["media"]:
                media_id, post_id = str(media["media_id"]), str(media["post_id"])
                analysis = media.get("analysis") or {}
                source_url = _media_url(con, post_id, media_id)
                content_hash = str(media.get("hash") or _sha(json.dumps(analysis, sort_keys=True, ensure_ascii=False)))
                con.execute(
                    """INSERT INTO media_assets
                       (media_id,post_id,source_url,storage_url,media_type,content_hash,download_status,
                        analysis_status,created_at,updated_at)
                       VALUES (?,?,?,?,?,?,?,?,?,?)
                       ON CONFLICT(media_id) DO UPDATE SET content_hash=excluded.content_hash,
                         download_status='complete',analysis_status='complete',updated_at=excluded.updated_at""",
                    (media_id, post_id, source_url, source_url, "image", content_hash, "complete", "complete", source_time, source_time),
                )
                con.execute(
                    """INSERT INTO media_analyses
                       (media_id,prompt_version,provider,model,input_hash,analysis_json,created_at)
                       VALUES (?,?,?,?,?,?,?)
                       ON CONFLICT(media_id) DO UPDATE SET prompt_version=excluded.prompt_version,
                         provider=excluded.provider,model=excluded.model,input_hash=excluded.input_hash,
                         analysis_json=excluded.analysis_json""",
                    (media_id, ARCHIVED_MEDIA_PROMPT_VERSION, "openai", ARCHIVED_MODEL, content_hash,
                     json.dumps(analysis, ensure_ascii=False, sort_keys=True), source_time),
                )

            claim_ids: list[str] = []
            for claim in graph["claims"]:
                claim_id = str(claim["claim_id"])
                claim_ids.append(claim_id)
                text = str(claim["text"])
                status = str(claim.get("verification") or "UNVERIFIED")
                con.execute(
                    """INSERT INTO claims
                       (claim_id,claim_text,claim_type,author_id,companies_json,themes_json,source_post_id,
                        evidence_ids_json,confidence,verification_status,point_in_time,content_hash,created_at)
                       VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)
                       ON CONFLICT(claim_id) DO UPDATE SET claim_text=excluded.claim_text,
                         claim_type=excluded.claim_type,author_id=excluded.author_id,themes_json=excluded.themes_json,
                         verification_status=excluded.verification_status,content_hash=excluded.content_hash""",
                    (claim_id, text, claim.get("type") or "OPINION", claim.get("author") or None, "[]",
                     json.dumps([theme_name], ensure_ascii=False), str(claim.get("post_id") or "") or None, "[]",
                     0.9 if claim.get("type") == "FACT" else 0.75, status, source_time, _sha(text.casefold()), source_time),
                )
                con.execute(
                    """INSERT INTO claim_themes(claim_id,theme_id,confidence) VALUES (?,?,?)
                       ON CONFLICT(claim_id,theme_id) DO UPDATE SET confidence=excluded.confidence""",
                    (claim_id, theme_id, 1.0),
                )

            claim_post = {str(x["claim_id"]): str(x.get("post_id") or "") for x in graph["claims"]}
            for verification in graph["claim_verifications"]:
                claim_id = str(verification["claim_id"])
                if claim_id not in claim_ids:
                    continue
                con.execute(
                    """INSERT INTO claim_verifications
                       (claim_id,verification_version,importance_score,status,rationale,corrected_claim,
                        sources_json,model,verified_at)
                       VALUES (?,1,?,?,?,?,?,?,?)
                       ON CONFLICT(claim_id,verification_version) DO UPDATE SET status=excluded.status,
                         rationale=excluded.rationale,corrected_claim=excluded.corrected_claim,
                         sources_json=excluded.sources_json,model=excluded.model""",
                    (claim_id, 90.0, verification.get("status") or "UNVERIFIED",
                     verification.get("rationale") or "Archived Golden verification",
                     verification.get("corrected_claim") or None,
                     json.dumps(verification.get("sources") or [], ensure_ascii=False, sort_keys=True),
                     ARCHIVED_MODEL, source_time),
                )

            post_ids = [str(x["post_id"]) for x in graph["posts"]]
            for source in graph["underlying_sources"]:
                sid = str(source["underlying_source_id"])
                source_class = str(source.get("class") or "UNKNOWN")
                url = str(source.get("url") or "").strip() or None
                con.execute(
                    """INSERT INTO underlying_sources
                       (underlying_source_id,canonical_url,publisher,title,source_class,created_at,updated_at)
                       VALUES (?,?,?,?,?,?,?)
                       ON CONFLICT(underlying_source_id) DO UPDATE SET canonical_url=excluded.canonical_url,
                         publisher=excluded.publisher,title=excluded.title,source_class=excluded.source_class,
                         updated_at=excluded.updated_at""",
                    (sid, url, source.get("publisher"), source.get("title"), source_class, source_time, source_time),
                )
                mentions = max(1, min(len(post_ids), int(source.get("social_mentions") or 1)))
                for post_id in post_ids[:mentions]:
                    con.execute(
                        """INSERT OR IGNORE INTO source_memberships
                           (underlying_source_id,evidence_type,evidence_id,mention_post_id,relation_type,created_at)
                           VALUES (?,'post',?,?,'mentions',?)""", (sid, post_id, post_id, source_time),
                    )

            analysis_record = graph["research_case_analysis"]
            analysis = analysis_record["analysis"]
            analysis_json = json.dumps(analysis, ensure_ascii=False, sort_keys=True)
            source_digest = _sha(audit_digest + "\n" + case_id)
            thesis_id = "thesis_golden_" + _sha(case_id)[:20]
            summary = str(analysis.get("ai_assessment") or spec["title"])
            con.execute(
                """INSERT INTO theses
                   (thesis_id,author_id,theme_id,current_version,current_thesis,thesis_summary,
                    confidence,first_seen,last_updated)
                   VALUES (?,?,?,1,?,?,?,?,?)
                   ON CONFLICT(thesis_id) DO UPDATE SET theme_id=excluded.theme_id,current_version=1,
                     current_thesis=excluded.current_thesis,thesis_summary=excluded.thesis_summary,
                     confidence=excluded.confidence,last_updated=excluded.last_updated""",
                (thesis_id, SEED_AUTHOR, theme_id, analysis_json, summary, 0.9, source_time, source_time),
            )
            snapshot = {"title": spec["title"], "case_id": case_id, **analysis}
            con.execute(
                """INSERT INTO thesis_versions
                   (thesis_id,version_number,snapshot_json,change_type,thesis_change_score,evidence_digest,model,created_at)
                   VALUES (?,1,?,'INITIAL',1,?,?,?)
                   ON CONFLICT(thesis_id,version_number) DO UPDATE SET snapshot_json=excluded.snapshot_json,
                     evidence_digest=excluded.evidence_digest,model=excluded.model""",
                (thesis_id, json.dumps(snapshot, ensure_ascii=False, sort_keys=True), source_digest,
                 analysis_record.get("model") or ARCHIVED_MODEL, source_time),
            )
            for claim_id in claim_ids:
                con.execute(
                    """INSERT INTO thesis_evidence(thesis_id,version_number,claim_id,evidence_weight)
                       VALUES (?,1,?,1) ON CONFLICT(thesis_id,version_number,claim_id) DO NOTHING""",
                    (thesis_id, claim_id),
                )
            con.execute(
                """INSERT INTO thesis_analyses
                   (thesis_id,thesis_version,analysis_json,model,analysis_mode,created_at)
                   VALUES (?,1,?,?,?,?)
                   ON CONFLICT(thesis_id,thesis_version) DO UPDATE SET analysis_json=excluded.analysis_json,
                     model=excluded.model,analysis_mode=excluded.analysis_mode""",
                (thesis_id, analysis_json, analysis_record.get("model") or ARCHIVED_MODEL,
                 "ARCHIVED_GOLDEN_AI", source_time),
            )
            con.execute(
                """INSERT INTO research_case_analyses(case_id,title,analysis_json,source_digest,model,updated_at)
                   VALUES (?,?,?,?,?,?)
                   ON CONFLICT(case_id) DO UPDATE SET title=excluded.title,analysis_json=excluded.analysis_json,
                     source_digest=excluded.source_digest,model=excluded.model,updated_at=excluded.updated_at""",
                (case_id, spec["title"], analysis_json, source_digest,
                 analysis_record.get("model") or ARCHIVED_MODEL, source_time),
            )
        con.commit()
        after = _counts(con)
    except Exception:
        con.rollback()
        raise
    finally:
        con.close()

    return {
        "mode": "existing_results_only",
        "ai_enabled": False,
        "openai_calls": 0,
        "openai_cost_usd": 0.0,
        "source_audit_sha256": audit_digest,
        "before": before,
        "after": after,
        "delta": {key: after[key] - before[key] for key in after},
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--db", required=True)
    parser.add_argument("--audit", default=str(DEFAULT_AUDIT))
    parser.add_argument("--cases", default=str(DEFAULT_CASES))
    parser.add_argument("--output")
    args = parser.parse_args()
    result = seed(args.db, args.audit, args.cases)
    rendered = json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True)
    if args.output:
        out = Path(args.output)
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(rendered + "\n", encoding="utf-8")
    print(rendered)


if __name__ == "__main__":
    main()
