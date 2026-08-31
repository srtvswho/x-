#!/usr/bin/env python3
"""Close Candidate coverage and rank the best stock expression for v1.2.1.

This is an incremental continuation of v1.2.  It never reruns a successful
logic-chain analysis.  Only the six mechanically truncated seeded candidates
are analyzed, then every active RESEARCH/high-value WATCH opportunity receives
one deduplicated Best Expression analysis.
"""
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

from signalboard.ai.guardrails import AIGuardrailBlocked
from signalboard.ai.router import call_json_web, record_usage
from signalboard.db import init_db
from scripts.intel_opportunity_engine_v12 import (
    CHAIN_SCHEMA,
    CHAIN_SYSTEM,
    SEEDED_CANDIDATES,
    _candidate_evidence,
    _claim_rows,
    _cost_report,
    _enforce_actionability,
    _json,
    _persist_chain,
    _sanitize_sources,
    _stable_id,
    _synthesize,
    normalize_score_scale,
)


DB_PATH = "/workspace/data/signalboard_full.db"
OUTPUT_DIR = Path("outputs/opportunity_engine_v121")
CHAIN_PROMPT_VERSION = "logic-chain-v1.2.1-coverage"
BEST_EXPRESSION_PROMPT_VERSION = "best-expression-v1.2.1"

MISSING_CANDIDATE_IDS = [
    "candidate_esmt_legacy_dram",
    "candidate_samsung_hbm4_broadcom",
    "candidate_traditional_packaging_shortage",
    "candidate_cxmt_hbm3e",
    "candidate_gpu_server_price",
    "candidate_memory_architecture",
]

COMPANY_SCORE_SCHEMA = {
    "type": "object", "additionalProperties": False,
    "properties": {
        name: {"type": "number", "minimum": 0, "maximum": 100}
        for name in (
            "exposure_purity", "earnings_sensitivity", "evidence_quality",
            "competitive_position", "valuation_expectations", "catalyst", "risk"
        )
    },
    "required": [
        "exposure_purity", "earnings_sensitivity", "evidence_quality",
        "competitive_position", "valuation_expectations", "catalyst", "risk",
    ],
}

COMPANY_RANKING_SCHEMA = {
    "type": "object", "additionalProperties": False,
    "properties": {
        "rank": {"type": "integer", "minimum": 1, "maximum": 12},
        "company": {"type": "string"}, "ticker": {"type": "string"},
        "role": {"type": "string", "enum": ["BEST_EXPRESSION", "RUNNER_UP", "HIGHER_RISK", "AVOID", "OTHER"]},
        "best_expression_score": {"type": "number", "minimum": 0, "maximum": 100},
        "scores": COMPANY_SCORE_SCHEMA,
        "revenue_exposure": {"type": "string"}, "earnings_sensitivity": {"type": "string"},
        "evidence": {"type": "string"}, "competitive_position": {"type": "string"},
        "backlog_capacity": {"type": "string"}, "customer_exposure": {"type": "string"},
        "supply_response_risk": {"type": "string"}, "valuation": {"type": "string"},
        "expectations": {"type": "string", "enum": ["LOW", "REASONABLE", "HIGH", "EXTREME", "UNKNOWN"]},
        "expectations_gap": {"type": "string", "enum": ["POSITIVE", "NEUTRAL", "NEGATIVE", "UNKNOWN"]},
        "catalysts": {"type": "array", "maxItems": 4, "items": {"type": "string"}},
        "invalidation": {"type": "array", "maxItems": 4, "items": {"type": "string"}},
        "why_ranked": {"type": "string"},
    },
    "required": [
        "rank", "company", "ticker", "role", "best_expression_score", "scores",
        "revenue_exposure", "earnings_sensitivity", "evidence", "competitive_position",
        "backlog_capacity", "customer_exposure", "supply_response_risk", "valuation",
        "expectations", "expectations_gap", "catalysts", "invalidation", "why_ranked",
    ],
}

PICK_SCHEMA = {
    "type": "object", "additionalProperties": False,
    "properties": {"company": {"type": "string"}, "ticker": {"type": "string"}, "why": {"type": "string"}},
    "required": ["company", "ticker", "why"],
}

SOURCE_SCHEMA = {
    "type": "object", "additionalProperties": False,
    "properties": {
        "title": {"type": "string"}, "url": {"type": "string"}, "publisher": {"type": "string"},
        "tier": {"type": "string", "enum": ["PRIMARY", "SECONDARY", "INDUSTRY", "UNKNOWN"]},
        "finding": {"type": "string"},
    },
    "required": ["title", "url", "publisher", "tier", "finding"],
}

SUB_OPPORTUNITY_SCHEMA = {
    "type": "object", "additionalProperties": False,
    "properties": {
        "name": {"type": "string"}, "mechanism": {"type": "string"},
        "companies": {"type": "array", "maxItems": 8, "items": {"type": "string"}},
    },
    "required": ["name", "mechanism", "companies"],
}

BEST_EXPRESSION_SCHEMA = {
    "type": "object", "additionalProperties": False,
    "properties": {
        "opportunity_id": {"type": "string"}, "title": {"type": "string"},
        "should_split": {"type": "boolean"},
        "sub_opportunities": {"type": "array", "maxItems": 7, "items": SUB_OPPORTUNITY_SCHEMA},
        "rankings": {"type": "array", "minItems": 2, "maxItems": 12, "items": COMPANY_RANKING_SCHEMA},
        "best_expression": PICK_SCHEMA, "runner_up": PICK_SCHEMA,
        "higher_risk_alternative": PICK_SCHEMA, "avoid_or_priced_in": PICK_SCHEMA,
        "no_clear_winner": {"type": "boolean"},
        "thesis_strength": {"type": "string", "enum": ["HIGH", "MEDIUM", "LOW"]},
        "expectations_gap": {"type": "string", "enum": ["POSITIVE", "NEUTRAL", "NEGATIVE", "UNKNOWN"]},
        "price_in_summary": {"type": "string"}, "verdict": {"type": "string"},
        "missing_evidence": {"type": "array", "maxItems": 6, "items": {"type": "string"}},
        "next_trigger": {"type": "string"},
        "source_roots": {"type": "array", "maxItems": 12, "items": SOURCE_SCHEMA},
    },
    "required": [
        "opportunity_id", "title", "should_split", "sub_opportunities", "rankings",
        "best_expression", "runner_up", "higher_risk_alternative", "avoid_or_priced_in",
        "no_clear_winner", "thesis_strength", "expectations_gap", "price_in_summary",
        "verdict", "missing_evidence", "next_trigger", "source_roots",
    ],
}

BEST_EXPRESSION_SYSTEM = """你是买方股票研究负责人。任务不是证明行业主题成立，而是判断哪只上市股票是该 Thesis 的最佳表达。

必须使用 web search 核验截至 2026-08-31 的公司一级资料、财报、订单/backlog、客户、产能、利润传导和可比估值。区分 Technology Winner 与 Stock Winner。社交媒体重复传播不能算独立证据。

逐家公司比较：收入纯度、利润弹性、竞争位置、订单/产能证据、客户集中度、供给响应、估值/市场预期、3/6/12月催化剂与失效条件。分数只用于排序，文字理由优先。若估值或收入映射不足，必须给 UNKNOWN/NEGATIVE expectations gap，不得制造 BUY 结论。

对于物理基础设施，必须判断 Cooling、Power Equipment、Transformer、Electrical Distribution、Wiring/Connectivity、Construction/Integration 是否应拆分，并至少比较 AAON、NVT、HPS.A、MOD、IESC、MTRS、JCI，以及证据显示更合适的公司。
对于 HBM→DRAM，必须直接比较 MU 与 SK hynix。
对于 CXL，必须证明产品→客户采用→收入→利润，而非只复述技术趋势。
对于 SOCAMM2，允许结论为 IMPORTANT TECHNOLOGY BUT NOT INVESTABLE EDGE。
对于 CPO/CW Laser，至少区分 LITE、COHR、Sivers、Ayar 的技术位置与股票可投资性。
对于 Wire Bonder，先判断瓶颈是设备还是 OSAT capacity，不得预设 KLIC/ASMPT 必胜。

只输出符合 schema 的 JSON。"""


def _spec_by_id() -> dict[str, dict[str, Any]]:
    return {item["candidate_id"]: item for item in SEEDED_CANDIDATES}


def _existing_chain(con: sqlite3.Connection, candidate_id: str) -> dict[str, Any] | None:
    row = con.execute("SELECT analysis_json FROM logic_chain_analyses WHERE candidate_id=?", (candidate_id,)).fetchone()
    return json.loads(row[0]) if row else None


def _analyze_missing(con: sqlite3.Connection) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    specs = _spec_by_id()
    all_claims = _claim_rows(con)
    completed: list[dict[str, Any]] = []
    errors: list[dict[str, Any]] = []
    for candidate_id in MISSING_CANDIDATE_IDS:
        if _existing_chain(con, candidate_id):
            completed.append({"candidate_id": candidate_id, "status": "REUSED_EXISTING", "cost_usd": 0.0})
            continue
        spec = specs[candidate_id]
        evidence = _candidate_evidence(con, spec, all_claims)
        digest = hashlib.sha256(_json(evidence).encode()).hexdigest()
        instruction = (
            "Close the previously mechanically truncated Candidate. Validate every causal step, use independent "
            "sources, decide whether it reaches company earnings, and explicitly reject weak or non-investable chains."
        )
        if candidate_id == "candidate_memory_architecture":
            instruction += " Compare with the existing ALAB/CXL chain and state whether this broader thesis is distinct, merged, or superseded."
        try:
            result = call_json_web(
                "logic_chain_analysis", CHAIN_SYSTEM,
                _json({"as_of": "2026-08-31", "candidate": spec, "evidence_bundle": evidence, "instruction": instruction}),
                CHAIN_SCHEMA, schema_name="signalboard_logic_chain_v121", max_output_tokens=6500,
                timeout=300, max_retries=1, prompt_version=CHAIN_PROMPT_VERSION,
                entity_type="logic_chain", entity_id=candidate_id,
            )
            data = result.data
            normalize_score_scale(data["scores"])
            data["actionability"] = _enforce_actionability(data)
            _sanitize_sources(data, result.sources, evidence["database_source_roots"])
            data["social_mention_count"] = evidence["social_mention_count"]
            data["evidence_claim_ids"] = [x["claim_id"] for x in evidence["claims"]]
            data["database_social_mentions"] = evidence["social_mention_count"]
            data["database_independent_sources"] = evidence["independent_database_sources"]
            _persist_chain(con, spec, data, result.model, "SEEDED", digest)
            record_usage(con, result, workload="logic_chain_analysis", object_type="logic_chain", object_id=candidate_id)
            con.commit()
            completed.append({
                "candidate_id": candidate_id, "status": "ANALYZED", "analysis": data,
                "model": result.model, "cost_usd": result.estimated_cost_usd,
            })
        except AIGuardrailBlocked:
            con.rollback()
            raise
        except Exception as exc:
            con.rollback()
            errors.append({"candidate_id": candidate_id, "error": f"{type(exc).__name__}: {exc}"})
    return completed, errors


def _synthesize_new(con: sqlite3.Connection, completed: list[dict[str, Any]]) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    synthesized: list[dict[str, Any]] = []
    errors: list[dict[str, Any]] = []
    for item in completed:
        data = item.get("analysis")
        if not data or int(data.get("chain_completeness", 0)) < 4 or data.get("actionability") in {"REJECTED", "THEME_ONLY", "AVOID"}:
            continue
        candidate_id = item["candidate_id"]
        opportunity_id = _stable_id("opp_", candidate_id)
        if con.execute("SELECT 1 FROM investment_opportunities WHERE opportunity_id=?", (opportunity_id,)).fetchone():
            synthesized.append({"candidate_id": candidate_id, "opportunity_id": opportunity_id, "status": "REUSED_EXISTING", "cost_usd": 0.0})
            continue
        try:
            synthesis, opportunity_id, cost = _synthesize(con, candidate_id, data, item.get("model", "gpt-5.6-terra"))
            synthesized.append({"candidate_id": candidate_id, "opportunity_id": opportunity_id, "status": "SYNTHESIZED", "synthesis": synthesis, "cost_usd": cost})
        except AIGuardrailBlocked:
            raise
        except Exception as exc:
            con.rollback()
            errors.append({"candidate_id": candidate_id, "error": f"{type(exc).__name__}: {exc}"})
    return synthesized, errors


def _coverage_status(analysis: dict[str, Any] | None) -> str:
    if not analysis:
        return "NOT_ANALYZED"
    action = analysis.get("actionability")
    if action in {"BUY_CANDIDATE", "HEDGE_CANDIDATE", "RESEARCH"}:
        return "ANALYZED_AND_PROMOTED"
    if action == "WATCH":
        return "ANALYZED_AND_WATCH"
    return "ANALYZED_AND_REJECTED"


def _build_coverage(con: sqlite3.Connection) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for spec in SEEDED_CANDIDATES:
        candidate_id = spec["candidate_id"]
        analysis = _existing_chain(con, candidate_id)
        status = _coverage_status(analysis)
        opportunity_id = _stable_id("opp_", candidate_id)
        if not con.execute("SELECT 1 FROM investment_opportunities WHERE opportunity_id=?", (opportunity_id,)).fetchone():
            opportunity_id = None
        if not analysis:
            reason = "No successful audit artifact exists; the prior attempt ended mechanically at max_output_tokens."
        elif status == "ANALYZED_AND_PROMOTED":
            reason = analysis.get("ai_verdict") or analysis.get("one_line_thesis") or "Reached company earnings and research threshold."
        elif status == "ANALYZED_AND_WATCH":
            reason = analysis.get("rejection_reason") or analysis.get("ai_verdict") or "Valid chain, but valuation/catalyst/evidence is incomplete."
        else:
            reason = analysis.get("rejection_reason") or analysis.get("ai_verdict") or "Rejected after analysis."
        item = {
            "candidate_id": candidate_id, "title": spec["title"], "final_status": status,
            "why": reason, "opportunity_id": opportunity_id,
            "analysis_source": "existing completed v1.2 audit" if candidate_id not in MISSING_CANDIDATE_IDS else "v1.2.1 coverage closure",
        }
        rows.append(item)
        con.execute(
            """INSERT INTO candidate_coverage(candidate_id,original_title,final_status,reason,mapped_candidate_id,opportunity_id,analysis_source)
               VALUES (?,?,?,?,?,?,?) ON CONFLICT(candidate_id) DO UPDATE SET
               original_title=excluded.original_title,final_status=excluded.final_status,reason=excluded.reason,
               mapped_candidate_id=excluded.mapped_candidate_id,opportunity_id=excluded.opportunity_id,
               analysis_source=excluded.analysis_source,updated_at=strftime('%Y-%m-%dT%H:%M:%fZ','now')""",
            (candidate_id, spec["title"], status, reason, None, opportunity_id, item["analysis_source"]),
        )
    con.commit()
    return rows


def _opportunity_payload(row: sqlite3.Row, chain: dict[str, Any]) -> dict[str, Any]:
    synthesis = json.loads(row[8] or "{}")
    companies = json.loads(row[7] or "[]")
    return {
        "opportunity_id": row[0], "title": row[1], "actionability": row[2],
        "opportunity_score": row[3], "primary_company": row[4],
        "market_expectations": row[5], "source_candidate_id": row[6],
        "companies": companies, "one_line_thesis": synthesis.get("one_line_thesis", row[1]),
        "why_now": synthesis.get("why_now", ""), "chain": {
            "driver": chain.get("driver", ""), "industry_change": chain.get("industry_change", ""),
            "bottleneck": chain.get("bottleneck", ""), "earnings_mechanism": chain.get("earnings_mechanism", ""),
            "valuation": chain.get("valuation", {}), "catalysts": chain.get("catalysts", [])[:5],
            "invalidation": chain.get("invalidation", [])[:5], "missing_evidence": chain.get("missing_evidence", [])[:5],
            "source_roots": chain.get("source_roots", [])[:8],
        },
    }


def _best_expression(con: sqlite3.Connection) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    rows = con.execute(
        """SELECT opportunity_id,title,actionability,opportunity_score,primary_company,market_expectations,
                  source_candidate_id,companies_json,synthesis_json
           FROM investment_opportunities
           WHERE actionability='RESEARCH' OR (actionability='WATCH' AND opportunity_score>=35)
           ORDER BY opportunity_score DESC"""
    ).fetchall()
    completed: list[dict[str, Any]] = []
    errors: list[dict[str, Any]] = []
    for row in rows:
        chain = _existing_chain(con, row[6]) or {}
        payload = _opportunity_payload(row, chain)
        digest = hashlib.sha256(_json(payload).encode()).hexdigest()
        cached = con.execute(
            "SELECT analysis_json,model FROM opportunity_best_expressions WHERE opportunity_id=? AND source_digest=? AND prompt_version=?",
            (row[0], digest, BEST_EXPRESSION_PROMPT_VERSION),
        ).fetchone()
        if cached:
            completed.append({"opportunity_id": row[0], "status": "REUSED_EXISTING", "analysis": json.loads(cached[0]), "model": cached[1], "cost_usd": 0.0})
            continue
        try:
            result = call_json_web(
                "best_expression_analysis", BEST_EXPRESSION_SYSTEM,
                _json({"as_of": "2026-08-31", "validated_opportunity": payload}),
                BEST_EXPRESSION_SCHEMA, schema_name="signalboard_best_expression_v121",
                max_output_tokens=5200, timeout=300, max_retries=1,
                prompt_version=BEST_EXPRESSION_PROMPT_VERSION,
                entity_type="investment_opportunity", entity_id=row[0],
            )
            data = result.data
            data["opportunity_id"] = row[0]
            for ranking in data["rankings"]:
                normalize_score_scale(ranking["scores"])
                ranking["best_expression_score"] = max(0.0, min(100.0, float(ranking["best_expression_score"])))
            data["rankings"].sort(key=lambda x: (x["rank"], -x["best_expression_score"]))
            _sanitize_sources(data, result.sources, chain.get("source_roots", []))
            con.execute(
                """INSERT INTO opportunity_best_expressions(opportunity_id,analysis_json,source_digest,model,prompt_version)
                   VALUES (?,?,?,?,?) ON CONFLICT(opportunity_id) DO UPDATE SET
                   analysis_json=excluded.analysis_json,source_digest=excluded.source_digest,model=excluded.model,
                   prompt_version=excluded.prompt_version,updated_at=strftime('%Y-%m-%dT%H:%M:%fZ','now')""",
                (row[0], _json(data), digest, result.model, BEST_EXPRESSION_PROMPT_VERSION),
            )
            record_usage(con, result, workload="best_expression_analysis", object_type="investment_opportunity", object_id=row[0])
            con.commit()
            completed.append({"opportunity_id": row[0], "status": "ANALYZED", "analysis": data, "model": result.model, "cost_usd": result.estimated_cost_usd})
        except AIGuardrailBlocked:
            con.rollback()
            raise
        except Exception as exc:
            con.rollback()
            errors.append({"opportunity_id": row[0], "error": f"{type(exc).__name__}: {exc}"})
    return completed, errors


def _build_funnel(con: sqlite3.Connection) -> dict[str, Any]:
    analyses = []
    for row in con.execute("SELECT candidate_id,analysis_json,status FROM logic_chain_analyses").fetchall():
        data = json.loads(row[1])
        analyses.append((row[0], data, row[2]))
    counts = {
        "raw_candidate_chains": len(SEEDED_CANDIDATES) + sum(1 for x in analyses if x[0].startswith("candidate_discovered_")),
        "verified_thesis": sum(1 for _, data, _ in analyses if data.get("actionability") not in {"REJECTED", "THEME_ONLY"}),
        "company_mapped": sum(1 for _, data, _ in analyses if int(data.get("chain_completeness", 0)) >= 3 and data.get("companies")),
        "earnings_mapped": sum(1 for _, data, _ in analyses if int(data.get("chain_completeness", 0)) >= 4 and data.get("earnings_mechanism")),
        "valuation_ready": sum(1 for _, data, _ in analyses if data.get("valuation", {}).get("status") in {"COMPLETE", "PARTIAL"} and data.get("valuation", {}).get("expectations") != "UNKNOWN"),
        "research": con.execute("SELECT COUNT(*) FROM investment_opportunities WHERE actionability='RESEARCH'").fetchone()[0],
        "buy_candidate": con.execute("SELECT COUNT(*) FROM investment_opportunities WHERE actionability='BUY_CANDIDATE'").fetchone()[0],
    }
    definitions = {
        "verified_thesis": "Analyzed and not REJECTED/THEME_ONLY",
        "company_mapped": "Completeness >=3 with named companies",
        "earnings_mapped": "Completeness >=4 with an explicit earnings mechanism",
        "valuation_ready": "Valuation COMPLETE/PARTIAL with non-UNKNOWN expectations",
    }
    con.execute(
        "INSERT OR REPLACE INTO opportunity_funnel_snapshots(snapshot_id,counts_json,definitions_json) VALUES (?,?,?)",
        ("v1.2.1-final", _json(counts), _json(definitions)),
    )
    con.commit()
    return {"counts": counts, "definitions": definitions}


def _new_candidates(con: sqlite3.Connection) -> list[dict[str, Any]]:
    out = []
    for row in con.execute(
        "SELECT candidate_id,title,analysis_json,status FROM logic_chain_analyses WHERE discovery_type='DISCOVERED' ORDER BY updated_at"
    ).fetchall():
        data = json.loads(row[2])
        out.append({"candidate_id": row[0], "title": row[1], "status": row[3], "actionability": data.get("actionability"), "why": data.get("ai_verdict") or data.get("one_line_thesis")})
    return out


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--db", default=DB_PATH)
    ap.add_argument("--output-dir", default=str(OUTPUT_DIR))
    args = ap.parse_args()
    init_db(args.db)
    out = Path(args.output_dir)
    out.mkdir(parents=True, exist_ok=True)
    con = sqlite3.connect(args.db, timeout=120)
    con.row_factory = sqlite3.Row

    missing, missing_errors = _analyze_missing(con)
    syntheses, synthesis_errors = _synthesize_new(con, missing)
    coverage = _build_coverage(con)
    best, best_errors = _best_expression(con)
    funnel = _build_funnel(con)
    new_candidates = _new_candidates(con)
    rejected = [x for x in coverage if x["final_status"] == "ANALYZED_AND_REJECTED"]
    cost = _cost_report(con)

    report = {
        "status": "COMPLETED" if not (missing_errors or synthesis_errors or best_errors) else "PARTIAL",
        "candidate_coverage": coverage, "missing_candidate_analysis": missing,
        "missing_candidate_errors": missing_errors, "new_syntheses": syntheses,
        "synthesis_errors": synthesis_errors, "best_expressions": best,
        "best_expression_errors": best_errors, "rejected_candidates": rejected,
        "new_candidates": new_candidates, "funnel": funnel, "cost": cost,
    }
    files = {
        "candidate_coverage_report.json": coverage,
        "missing_candidate_analysis.json": {"completed": missing, "errors": missing_errors},
        "rejected_candidates.json": rejected,
        "new_candidates.json": new_candidates,
        "best_expressions.json": {"completed": best, "errors": best_errors},
        "opportunity_funnel.json": funnel,
        "cost_report.json": cost,
        "run_report.json": report,
    }
    for name, payload in files.items():
        (out / name).write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    con.close()
    print(json.dumps({
        "status": report["status"], "coverage": len(coverage), "missing_completed": len(missing),
        "new_opportunities": len(syntheses), "best_expressions": len(best), "funnel": funnel["counts"],
        "cost": cost.get("total", {}),
    }, ensure_ascii=False))


if __name__ == "__main__":
    main()
