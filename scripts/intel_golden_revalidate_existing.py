#!/usr/bin/env python3
"""Create the formal zero-AI Golden report from the completed audit artifact."""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import sqlite3
import sys
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from signalboard.db import init_db

ROOT = Path(__file__).resolve().parent.parent
DEFAULT_AUDIT = ROOT / "outputs/thesis_engine_v11/archive/2026-08-30/v11_audit.original.json"
DEFAULT_ORIGINAL = ROOT / "outputs/thesis_engine_v11/archive/2026-08-30/golden_results.original.json"
DEFAULT_CASES = ROOT / "tests/golden_cases.json"
VALIDATOR_VERSION = "golden-validator-v1.1.0-capex-bilingual"


def _now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="milliseconds").replace("+00:00", "Z")


def _norm(text: str) -> str:
    return re.sub(r"\s+", " ", text.casefold())


def _concept_hit(corpus: str, concepts: list[str]) -> bool:
    return all(any(_norm(option) in corpus for option in concept.split("|")) for concept in concepts)


def _db_integrity(con: sqlite3.Connection, case_id: str, spec: dict) -> dict:
    post_ids = spec["seed_post_ids"]
    placeholders = ",".join("?" for _ in post_ids)
    counts = {
        "posts": int(con.execute(f"SELECT COUNT(*) FROM raw_posts WHERE post_id IN ({placeholders})", post_ids).fetchone()[0]),
        "claims": int(con.execute(f"SELECT COUNT(*) FROM claims WHERE source_post_id IN ({placeholders})", post_ids).fetchone()[0]),
        "media": int(con.execute(f"SELECT COUNT(*) FROM media_assets WHERE post_id IN ({placeholders}) AND analysis_status='complete'", post_ids).fetchone()[0]),
        "theses": int(con.execute("SELECT COUNT(*) FROM theses WHERE author_id='golden_case_consensus' AND thesis_id LIKE 'thesis_golden_%'").fetchone()[0]),
        "research_case": int(con.execute("SELECT COUNT(*) FROM research_case_analyses WHERE case_id=?", (case_id,)).fetchone()[0]),
    }
    passed = counts["posts"] == len(post_ids) and counts["claims"] > 0 and counts["media"] > 0 and counts["theses"] >= 2 and counts["research_case"] == 1
    return {"status": "PASS" if passed else "FAIL", **counts}


def revalidate(
    db_path: str | Path,
    *,
    audit_path: str | Path = DEFAULT_AUDIT,
    original_path: str | Path = DEFAULT_ORIGINAL,
    cases_path: str | Path = DEFAULT_CASES,
    timestamp: str | None = None,
) -> dict:
    if os.getenv("AI_ENABLED", "false").strip().lower() in {"1", "true", "yes", "on"}:
        raise RuntimeError("Deterministic Golden revalidation refuses AI_ENABLED=true")
    init_db(db_path)
    audit_file, original_file = Path(audit_path), Path(original_path)
    audit = json.loads(audit_file.read_text(encoding="utf-8"))
    original = json.loads(original_file.read_text(encoding="utf-8"))
    specs = json.loads(Path(cases_path).read_text(encoding="utf-8"))
    original_by_id = {row["case_id"]: row for row in original["results"]}
    validated_at = timestamp or os.getenv("GOLDEN_VALIDATION_TIMESTAMP") or _now()
    audit_hash = hashlib.sha256(audit_file.read_bytes()).hexdigest()
    original_hash = hashlib.sha256(original_file.read_bytes()).hexdigest()
    run_id = os.getenv("AI_RUN_ID", "golden-productionization-zero-ai")

    con = sqlite3.connect(db_path, timeout=120)
    results = []
    for case_id, spec in specs.items():
        old = original_by_id[case_id]
        categories = json.loads(json.dumps(old["categories"], ensure_ascii=False))
        integrity = _db_integrity(con, case_id, spec)
        if integrity["status"] != "PASS":
            raise RuntimeError(f"{case_id} production seed integrity failed: {integrity}")
        if case_id.startswith("case_a_"):
            # The completed audit passed every category except one exact keyword check.
            # Re-run only that deterministic matcher against the immutable audit corpus.
            corpus = _norm(json.dumps(audit["golden_evidence_graphs"][case_id], ensure_ascii=False, sort_keys=True))
            checks = [{"concepts": concepts, "pass": _concept_hit(corpus, concepts)} for concepts in spec["expected_logic"]]
            categories["expected_logic"] = {
                "status": "PASS" if all(row["pass"] for row in checks) else "PARTIAL",
                "checks": checks,
            }
            if categories["expected_logic"]["status"] != "PASS":
                raise RuntimeError("Case A bilingual deterministic matcher did not pass")
        if any(category["status"] != "PASS" for category in categories.values()):
            raise RuntimeError(f"{case_id} preserved Golden categories are not all PASS")
        result = {
            "case_id": case_id,
            "title": spec["title"],
            "status": "PASS",
            "original_status": old["overall"],
            "ai_analysis_source": "existing completed Golden audit",
            "source_ai_model": audit["golden_evidence_graphs"][case_id]["research_case_analysis"]["model"],
            "source_ai_completed_at": audit["golden_evidence_graphs"][case_id]["research_case_analysis"]["updated_at"],
            "revalidation": "deterministic only" if case_id.startswith("case_a_") else "existing PASS preserved; deterministic integrity check only",
            "additional_openai_calls": 0,
            "additional_openai_cost_usd": 0.0,
            "categories": categories,
            "production_seed_integrity": integrity,
        }
        if case_id.startswith("case_a_"):
            result["original_discrepancy"] = {
                "expected_keyword": "CapEx",
                "actual_research_wording": "资本开支",
                "resolution": "validator now accepts CapEx | 资本开支",
                "capex_or_capital_expenditure": "PASS",
                "wfe": "PASS",
            }
        results.append(result)

    attempted = int(con.execute(
        """SELECT COUNT(*) FROM ai_usage_ledger
           WHERE run_id=? AND provider='openai' AND status IN ('PENDING','SUCCESS','FAILED','CANCELLED','UNKNOWN_COST')""",
        (run_id,),
    ).fetchone()[0])
    if attempted:
        raise RuntimeError(f"Zero-AI acceptance failed: {attempted} OpenAI ledger attempts found for run {run_id}")

    report = {
        "report_type": "Golden Validation Report",
        "validator_version": VALIDATOR_VERSION,
        "validation_timestamp": validated_at,
        "mode": "archived_ai_result_deterministic_revalidation",
        "source_audit": str(audit_file.relative_to(ROOT)),
        "source_audit_sha256": audit_hash,
        "original_golden_result": str(original_file.relative_to(ROOT)),
        "original_golden_result_sha256": original_hash,
        "openai_calls": 0,
        "openai_estimated_cost_usd": 0.0,
        "results": results,
        "summary": {"PASS": 2, "PARTIAL": 0, "FAIL": 0},
    }
    for result in results:
        con.execute(
            """INSERT INTO golden_validations
               (case_id,status,validator_version,report_json,source_audit_sha256,validation_timestamp,
                mode,additional_ai_calls,additional_ai_cost_usd)
               VALUES (?,?,?,?,?,?,?,?,?)
               ON CONFLICT(case_id) DO UPDATE SET status=excluded.status,
                 validator_version=excluded.validator_version,report_json=excluded.report_json,
                 source_audit_sha256=excluded.source_audit_sha256,
                 validation_timestamp=excluded.validation_timestamp,mode=excluded.mode,
                 additional_ai_calls=excluded.additional_ai_calls,
                 additional_ai_cost_usd=excluded.additional_ai_cost_usd""",
            (result["case_id"], "PASS", VALIDATOR_VERSION, json.dumps(result, ensure_ascii=False, sort_keys=True),
             audit_hash, validated_at, result["revalidation"], 0, 0.0),
        )
    con.commit()
    con.close()
    return report


def _markdown(report: dict) -> str:
    rows = [
        "# Golden Validation Report",
        "",
        f"- Validator: `{report['validator_version']}`",
        f"- Validation timestamp: `{report['validation_timestamp']}`",
        f"- Source audit SHA-256: `{report['source_audit_sha256']}`",
        "- OpenAI calls: **0**",
        "- OpenAI estimated cost: **$0.00**",
        "",
    ]
    for result in report["results"]:
        rows.extend([
            f"## {result['title']}", "",
            "**PASS**", "",
            f"- AI analysis source: {result['ai_analysis_source']}",
            f"- Revalidation: {result['revalidation']}",
            "- Additional OpenAI calls: 0", "- Additional OpenAI cost: $0.00", "",
        ])
        if "original_discrepancy" in result:
            discrepancy = result["original_discrepancy"]
            rows.extend([
                "Original discrepancy:", "",
                f"- Expected keyword: `{discrepancy['expected_keyword']}`",
                f"- Actual research wording: `{discrepancy['actual_research_wording']}`",
                f"- Resolution: `{discrepancy['resolution']}`",
                "- CapEx / 资本开支: PASS", "- WFE: PASS", "",
            ])
    return "\n".join(rows).rstrip() + "\n"


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--db", required=True)
    parser.add_argument("--audit", default=str(DEFAULT_AUDIT))
    parser.add_argument("--original", default=str(DEFAULT_ORIGINAL))
    parser.add_argument("--cases", default=str(DEFAULT_CASES))
    parser.add_argument("--output", default="outputs/thesis_engine_v11/golden_validation_report.json")
    parser.add_argument("--markdown", default="outputs/thesis_engine_v11/golden_validation_report.md")
    args = parser.parse_args()
    report = revalidate(args.db, audit_path=args.audit, original_path=args.original, cases_path=args.cases)
    output, markdown = Path(args.output), Path(args.markdown)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    markdown.write_text(_markdown(report), encoding="utf-8")
    print(json.dumps({"summary": report["summary"], "openai_calls": 0, "openai_cost_usd": 0.0}, sort_keys=True))


if __name__ == "__main__":
    main()
