#!/usr/bin/env python3
"""Deterministic Golden Case acceptance; checks evidence structure, not prose similarity."""
from __future__ import annotations

import argparse
import json
import re
import sqlite3
from pathlib import Path

DB_PATH = "/workspace/data/signalboard_full.db"
CASES = Path(__file__).resolve().parent.parent / "tests" / "golden_cases.json"


def _norm(text: str) -> str:
    return re.sub(r"\s+", " ", text.casefold())


def _concept_hit(corpus: str, concepts: list[str]) -> bool:
    return all(any(_norm(option) in corpus for option in concept.split("|")) for concept in concepts)


def _status(hits: int, total: int) -> str:
    if total == 0 or hits == total:
        return "PASS"
    if hits:
        return "PARTIAL"
    return "FAIL"


def _text_corpora(con: sqlite3.Connection, post_ids: list[str], case_id: str) -> dict[str, str]:
    placeholders = ",".join("?" for _ in post_ids)
    sqls = {
        "raw": f"SELECT raw_text FROM raw_posts WHERE post_id IN ({placeholders})",
        "claims": f"SELECT claim_text FROM claims WHERE source_post_id IN ({placeholders})",
        "media": f"SELECT analysis_json FROM media_analyses ma JOIN media_assets m ON m.media_id=ma.media_id WHERE m.post_id IN ({placeholders})",
        "verification": f"SELECT cv.rationale||' '||COALESCE(cv.corrected_claim,'')||' '||cv.sources_json FROM claim_verifications cv JOIN claims c ON c.claim_id=cv.claim_id WHERE c.source_post_id IN ({placeholders})",
    }
    corpora = {name: _norm("\n".join(str(r[0] or "") for r in con.execute(sql, post_ids).fetchall()))
               for name, sql in sqls.items()}
    corpora["thesis"] = _norm("\n".join(str(r[0] or "") for r in con.execute("SELECT snapshot_json FROM thesis_versions").fetchall()))
    corpora["analyst"] = _norm("\n".join(str(r[0] or "") for r in con.execute("SELECT analysis_json FROM thesis_analyses").fetchall()))
    corpora["cross"] = _norm("\n".join(str(r[0] or "") for r in con.execute("SELECT analysis_json FROM cross_author_theses").fetchall()))
    case_row = con.execute("SELECT analysis_json FROM research_case_analyses WHERE case_id=?", (case_id,)).fetchone()
    corpora["case"] = _norm(case_row[0] if case_row else "")
    return corpora


def evaluate_case(con: sqlite3.Connection, case_id: str, spec: dict) -> dict:
    post_ids = spec["seed_post_ids"]
    context_ids = {r[0] for r in con.execute(
        f"SELECT DISTINCT post_id FROM post_graph_memberships WHERE root_post_id IN ({','.join('?' for _ in post_ids)})",
        post_ids,
    ).fetchall()}
    evidence_post_ids = sorted(set(post_ids) | context_ids)
    present_posts = {r[0] for r in con.execute(
        f"SELECT post_id FROM raw_posts WHERE post_id IN ({','.join('?' for _ in post_ids)})", post_ids
    ).fetchall()}
    edge_results = []
    for source, target in spec["required_reference_edges"]:
        hit = con.execute(
            "SELECT 1 FROM post_references WHERE source_post_id=? AND target_post_id=? AND fetch_status='complete'",
            (source, target),
        ).fetchone() is not None
        edge_results.append({"source": source, "target": target, "pass": hit})
    media_results = []
    for media_id in spec["required_media_ids"]:
        row = con.execute(
            """SELECT m.analysis_status,ma.analysis_json FROM media_assets m
               LEFT JOIN media_analyses ma ON ma.media_id=m.media_id WHERE m.media_id=?""", (media_id,),
        ).fetchone()
        media_results.append({"media_id": media_id, "pass": bool(row and row[0] == "complete" and row[1]),
                              "status": row[0] if row else "MISSING"})
    corpora = _text_corpora(con, evidence_post_ids, case_id)
    # Each category is only allowed to pass from the appropriate structured layer.
    category_sources = {
        "expected_facts": ["claims", "media", "verification", "thesis", "analyst", "case"],
        "expected_logic": ["claims", "thesis", "analyst", "cross", "case"],
        "expected_corrections": ["verification", "analyst", "cross", "case"],
        "expected_risks": ["claims", "thesis", "analyst", "cross", "case"],
        "expected_beneficiaries": ["claims", "thesis", "analyst", "cross", "case"],
        "expected_losers": ["claims", "thesis", "analyst", "cross", "case"],
        "expected_unknowns": ["verification", "thesis", "analyst", "cross", "case"],
    }
    semantic = {}
    for field in ["expected_facts", "expected_logic", "expected_corrections", "expected_risks",
                  "expected_beneficiaries", "expected_losers", "expected_unknowns"]:
        corpus = _norm("\n".join(corpora[x] for x in category_sources[field]))
        results = [{"concepts": concepts, "pass": _concept_hit(corpus, concepts)} for concepts in spec[field]]
        semantic[field] = {"status": _status(sum(x["pass"] for x in results), len(results)), "checks": results}
    source_groups = con.execute(
        f"""SELECT underlying_source_id,COUNT(DISTINCT mention_post_id) mentions
            FROM source_memberships WHERE mention_post_id IN ({','.join('?' for _ in evidence_post_ids)})
              AND relation_type IN ('mentions','visual_representation')
            GROUP BY underlying_source_id ORDER BY mentions DESC""", evidence_post_ids,
    ).fetchall()
    independent_count = con.execute(
        f"SELECT COUNT(DISTINCT underlying_source_id) FROM source_memberships WHERE mention_post_id IN ({','.join('?' for _ in evidence_post_ids)})",
        evidence_post_ids,
    ).fetchone()[0]
    social_count = con.execute(
        f"SELECT COUNT(DISTINCT mention_post_id) FROM source_memberships WHERE mention_post_id IN ({','.join('?' for _ in evidence_post_ids)}) AND relation_type='mentions'",
        evidence_post_ids,
    ).fetchone()[0]
    source_dedup_pass = bool(source_groups and max(x[1] for x in source_groups) >= 2)
    claim_type_rows = con.execute(
        f"SELECT claim_type,verification_status FROM claims WHERE source_post_id IN ({','.join('?' for _ in evidence_post_ids)})",
        evidence_post_ids,
    ).fetchall()
    fact_count = sum(x[0] == "FACT" for x in claim_type_rows)
    opinion_count = sum(x[0] in {"OPINION", "FORECAST", "INFERENCE", "RISK"} for x in claim_type_rows)
    misverified_opinions = sum(
        x[0] == "OPINION" and x[1] in {"SUPPORTED_BY_PRIMARY", "SUPPORTED_BY_SECONDARY"}
        for x in claim_type_rows
    )
    separation_pass = fact_count > 0 and opinion_count > 0 and misverified_opinions == 0
    action_rows = [json.loads(r[0]) for r in con.execute("SELECT analysis_json FROM thesis_analyses").fetchall()]
    case_analysis = con.execute("SELECT analysis_json FROM research_case_analyses WHERE case_id=?", (case_id,)).fetchone()
    if case_analysis:
        action_rows.append(json.loads(case_analysis[0]))
    allowed = {"NOT_ACTIONABLE", "WATCH", "RESEARCH", "BUY_CANDIDATE", "HEDGE_CANDIDATE", "AVOID"}
    actionability_pass = bool(action_rows) and all(x.get("actionability") in allowed for x in action_rows)
    categories = {
        "seed_posts": {"status": _status(len(present_posts), len(post_ids)), "present": sorted(present_posts), "missing": sorted(set(post_ids)-present_posts)},
        "citation_chain": {"status": _status(sum(x["pass"] for x in edge_results), len(edge_results)), "checks": edge_results},
        "media_coverage": {"status": _status(sum(x["pass"] for x in media_results), len(media_results)), "checks": media_results},
        "source_deduplication": {"status": "PASS" if source_dedup_pass else "FAIL",
                                 "independent_evidence": independent_count,
                                 "social_mentions": social_count,
                                 "largest_same_source_group": max((x[1] for x in source_groups), default=0)},
        **semantic,
        "fact_opinion_separation": {"status": "PASS" if separation_pass else "FAIL",
                                    "facts": fact_count, "opinions_forecasts_inferences_risks": opinion_count,
                                    "supported_opinions_error": misverified_opinions},
        "actionability": {"status": "PASS" if actionability_pass else "FAIL"},
    }
    statuses = [x["status"] for x in categories.values()]
    overall = "PASS" if all(x == "PASS" for x in statuses) else ("FAIL" if statuses.count("FAIL") >= len(statuses) / 2 else "PARTIAL")
    return {"case_id": case_id, "title": spec["title"], "overall": overall, "categories": categories}


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--db", default=DB_PATH)
    ap.add_argument("--cases", default=str(CASES))
    ap.add_argument("--case", default="all")
    ap.add_argument("--output", default="outputs/thesis_engine_v11/golden_results.json")
    ap.add_argument("--require-pass", action="store_true")
    args = ap.parse_args()
    cases = json.loads(Path(args.cases).read_text(encoding="utf-8"))
    selected = cases if args.case == "all" else {args.case: cases[args.case]}
    con = sqlite3.connect(args.db, timeout=120)
    results = [evaluate_case(con, case_id, spec) for case_id, spec in selected.items()]
    con.close()
    report = {"results": results, "summary": {x: sum(r["overall"] == x for r in results) for x in ("PASS", "PARTIAL", "FAIL")}}
    out = Path(args.output)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(report["summary"], ensure_ascii=False, sort_keys=True))
    if args.require_pass and any(r["overall"] != "PASS" for r in results):
        raise SystemExit("Golden tests did not fully pass")


if __name__ == "__main__":
    main()
