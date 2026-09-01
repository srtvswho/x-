#!/usr/bin/env python3
"""Six-security Focused Odds Sprint v1.4.1.

The paid path is deliberately bounded to two Terra web-research calls per
security: a sourced financial snapshot, followed by an odds review.  All fair
values, gaps, returns, entry prices and Good Odds gates are recomputed locally.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import sqlite3
import sys
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from signalboard.ai.router import call_json, call_json_web, record_usage
from signalboard.db import init_db


PROMPT_VERSION = "focused-odds-v1.4.1"
SNAPSHOT_VERSION = PROMPT_VERSION + "-snapshot"
OUTPUT_DIR = Path("outputs/focused_odds_v141")
DB_PATH = "/workspace/data/signalboard_full.db"
AS_OF_DATE = "2026-09-01"
CYCLICAL_PE_CEILINGS = {"KLIC": 18.0, "005930.KS": 16.0, "MU": 18.0}


@dataclass(frozen=True)
class Security:
    ticker: str
    company: str
    exchange: str
    currency: str
    group: str
    thesis: str


UNIVERSE = (
    Security("JBL", "Jabil", "NYSE", "USD", "PHYSICAL_INFRA",
             "Quantify AI/data-center exposure, AI growth, FY27/FY28 outlook, margins and customer concentration; separate legacy EMS valuation from AI rerating."),
    Security("KLIC", "Kulicke & Soffa", "NASDAQ", "USD", "PACKAGING",
             "Test whether wire-bonder demand is a valid AI/memory thesis using cycle, utilization, backlog, book-to-bill, ASP, margin and services; build downcycle/normalized/upcycle EPS."),
    Security("NVT", "nVent Electric", "NYSE", "USD", "PHYSICAL_INFRA",
             "Quantify data-center share, orders, organic growth, backlog, pricing, margins and acquisition effects; retest whether earlier ATTRACTIVE was caused by incomplete valuation."),
    Security("JCI", "Johnson Controls", "NYSE", "USD", "PHYSICAL_INFRA",
             "Quantify data-center exposure and earnings contribution, compare with AAON and NVT, and test lower-purity/lower-expectations odds."),
    Security("005930.KS", "Samsung Electronics", "KRX", "KRW", "MEMORY",
             "Cover HBM, DRAM, NAND, foundry and mobile; bridge 2026-28 memory operating profit, compare SK hynix/Micron, and test non-memory downside protection."),
    Security("MU", "Micron Technology", "NASDAQ", "USD", "MEMORY",
             "Bridge 2026-28 revenue, gross margin and EPS; test HBM price-in, DRAM tightness, wafer intensity, bit supply, CXMT and ASP; normalize cycle margin/EPS."),
)


N = {"type": ["number", "null"]}
S = {"type": ["string", "null"]}
CONF = {"type": "string", "enum": ["LOW", "MEDIUM", "HIGH"]}
LEVEL = {"type": "string", "enum": ["LOW", "MEDIUM", "HIGH"]}
SOURCE = {
    "type": "object", "additionalProperties": False,
    "properties": {
        "source_id": {"type": "string"}, "title": {"type": "string"},
        "url": {"type": "string"}, "publisher": {"type": "string"},
        "source_type": {"type": "string", "enum": ["COMPANY", "FILING", "EXCHANGE", "CONSENSUS", "MARKET_DATA", "SECONDARY"]},
        "as_of_date": S, "fiscal_period": S, "finding": {"type": "string"},
    },
    "required": ["source_id", "title", "url", "publisher", "source_type", "as_of_date", "fiscal_period", "finding"],
}
METRIC = {
    "type": "object", "additionalProperties": False,
    "properties": {
        "name": {"type": "string"}, "value": N, "unit": {"type": "string"},
        "currency": S, "fiscal_period": S, "as_of_date": S,
        "source_ids": {"type": "array", "maxItems": 5, "items": {"type": "string"}},
        "confidence": CONF, "note": {"type": "string"},
    },
    "required": ["name", "value", "unit", "currency", "fiscal_period", "as_of_date", "source_ids", "confidence", "note"],
}
YEAR = {
    "type": "object", "additionalProperties": False,
    "properties": {
        "fiscal_period": {"type": "string"}, "kind": {"type": "string", "enum": ["HISTORICAL", "CONSENSUS"]},
        "revenue": METRIC, "operating_margin": METRIC, "gross_margin": METRIC,
        "eps": METRIC, "fcf": METRIC,
    },
    "required": ["fiscal_period", "kind", "revenue", "operating_margin", "gross_margin", "eps", "fcf"],
}
SNAPSHOT_SCHEMA = {
    "type": "object", "additionalProperties": False,
    "properties": {
        "ticker": {"type": "string"}, "company": {"type": "string"},
        "exchange": {"type": "string"}, "currency": {"type": "string"},
        "as_of_date": {"type": "string"}, "fiscal_year_end": S,
        "market_metrics": {"type": "array", "minItems": 6, "maxItems": 18, "items": METRIC},
        "annual_financials": {"type": "array", "minItems": 3, "maxItems": 7, "items": YEAR},
        "thesis_exposure": {
            "type": "object", "additionalProperties": False,
            "properties": {
                "purity": LEVEL, "earnings_sensitivity": LEVEL,
                "revenue_share": METRIC, "profit_share": METRIC,
                "mechanism": {"type": "string"}, "quantification_limits": {"type": "string"},
            },
            "required": ["purity", "earnings_sensitivity", "revenue_share", "profit_share", "mechanism", "quantification_limits"],
        },
        "company_specific_findings": {"type": "array", "minItems": 5, "maxItems": 15, "items": METRIC},
        "reverse_expectations": {
            "type": "object", "additionalProperties": False,
            "properties": {"level": {"type": "string", "enum": ["LOW", "MODERATE", "HIGH", "EXTREME", "UNKNOWN"]},
                           "implied_operating_assumptions": {"type": "string"}, "priced_in_summary": {"type": "string"}},
            "required": ["level", "implied_operating_assumptions", "priced_in_summary"],
        },
        "balance_sheet_and_capital_allocation": {"type": "string"},
        "historical_and_peer_valuation": {"type": "string"},
        "data_gaps": {"type": "array", "maxItems": 10, "items": {"type": "string"}},
        "sources": {"type": "array", "minItems": 3, "maxItems": 20, "items": SOURCE},
    },
    "required": ["ticker", "company", "exchange", "currency", "as_of_date", "fiscal_year_end",
                 "market_metrics", "annual_financials", "thesis_exposure", "company_specific_findings",
                 "reverse_expectations", "balance_sheet_and_capital_allocation", "historical_and_peer_valuation",
                 "data_gaps", "sources"],
}


BRIDGE_YEAR = {
    "type": "object", "additionalProperties": False,
    "properties": {
        "fiscal_period": {"type": "string"}, "revenue_consensus": N, "revenue_base": N,
        "margin_consensus": N, "margin_base": N, "eps_consensus": N, "eps_base": N,
        "fcf_consensus": N, "fcf_base": N, "driver": {"type": "string"},
    },
    "required": ["fiscal_period", "revenue_consensus", "revenue_base", "margin_consensus", "margin_base",
                 "eps_consensus", "eps_base", "fcf_consensus", "fcf_base", "driver"],
}
SCENARIO = {
    "type": "object", "additionalProperties": False,
    "properties": {
        "name": {"type": "string", "enum": ["BEAR", "BASE", "BULL"]},
        "fiscal_period": {"type": "string"}, "revenue": N, "margin": N, "eps": N, "fcf": N,
        "valuation_method": {"type": "string", "enum": ["FORWARD_PE", "NORMALIZED_PE", "MID_CYCLE_PE", "FCF_YIELD", "SOTP"]},
        "valuation_basis": N, "fair_multiple": N, "fair_value": N, "probability": {"type": "number"},
        "multiple_reason": {"type": "string"}, "assumptions": {"type": "array", "minItems": 2, "maxItems": 6, "items": {"type": "string"}},
    },
    "required": ["name", "fiscal_period", "revenue", "margin", "eps", "fcf", "valuation_method",
                 "valuation_basis", "fair_multiple", "fair_value", "probability", "multiple_reason", "assumptions"],
}
REVIEW_SCHEMA = {
    "type": "object", "additionalProperties": False,
    "properties": {
        "ticker": {"type": "string"}, "company": {"type": "string"}, "as_of_date": {"type": "string"},
        "one_line_conclusion": {"type": "string"}, "business_quality_score": {"type": "number"},
        "thesis_quality_score": {"type": "number"}, "evidence_quality_score": {"type": "number"},
        "exposure_purity": LEVEL, "earnings_sensitivity": LEVEL,
        "exposure_quantification": {"type": "string"}, "earnings_mechanism": {"type": "string"},
        "expectations_gap": {"type": "string", "enum": ["POSITIVE", "NEUTRAL", "NEGATIVE", "UNKNOWN"]},
        "expectations_analysis": {"type": "string"},
        "earnings_bridge": {"type": "array", "minItems": 3, "maxItems": 3, "items": BRIDGE_YEAR},
        "normalized_earnings": {
            "type": "object", "additionalProperties": False,
            "properties": {"is_cyclical": {"type": "boolean"}, "normalized_eps": N,
                           "normalized_margin": N, "method": {"type": "string"}, "peak_risk": {"type": "string"}},
            "required": ["is_cyclical", "normalized_eps", "normalized_margin", "method", "peak_risk"],
        },
        "scenarios": {"type": "array", "minItems": 3, "maxItems": 3, "items": SCENARIO},
        "three_year_eps_or_fcf_cagr": N, "balance_sheet_strong": {"type": "boolean"},
        "roic_fcf_quality_strong": {"type": "boolean"}, "valuation_reasonable": {"type": "boolean"},
        "catalysts": {"type": "array", "minItems": 1, "maxItems": 5, "items": {"type": "string"}},
        "invalidation": {"type": "array", "minItems": 1, "maxItems": 5, "items": {"type": "string"}},
        "why_not_buy_now": {"type": "string"}, "what_changes_the_decision": {"type": "string"},
        "key_risks": {"type": "array", "minItems": 2, "maxItems": 7, "items": {"type": "string"}},
        "critical_data_missing": {"type": "array", "maxItems": 8, "items": {"type": "string"}},
        "valuation_confidence": CONF, "thesis_confidence": CONF,
    },
    "required": ["ticker", "company", "as_of_date", "one_line_conclusion", "business_quality_score",
                 "thesis_quality_score", "evidence_quality_score", "exposure_purity", "earnings_sensitivity",
                 "exposure_quantification", "earnings_mechanism", "expectations_gap", "expectations_analysis",
                 "earnings_bridge", "normalized_earnings", "scenarios", "three_year_eps_or_fcf_cagr",
                 "balance_sheet_strong", "roic_fcf_quality_strong", "valuation_reasonable", "catalysts",
                 "invalidation", "why_not_buy_now", "what_changes_the_decision", "key_risks",
                 "critical_data_missing", "valuation_confidence", "thesis_confidence"],
}


SNAPSHOT_SYSTEM = """You are a buy-side financial data auditor. Use web search and prioritize company IR,
filings and exchange releases, then reputable consensus/market sources. Research only the named security.
Cut off at the latest available session on or before 2026-09-01. Every numeric fact needs source_ids,
as_of_date, fiscal_period, currency/unit and confidence. Never mix fiscal/calendar years or local/ADR prices.
Use null when a reliable number is unavailable. Explicitly quantify the named thesis revenue and profit
exposure; do not substitute company-wide growth for thesis exposure. Return compact JSON only."""

REVIEW_SYSTEM = """You are the valuation lead of a buy-side team. Use only the supplied audited snapshot.
Do not browse or invent new numbers. Determine what the price implies, construct a 2026-2028
Driver→Revenue→Margin→EPS/FCF bridge, and compare consensus with Our Base. Produce Bear/Base/Bull values
with justified multiples. For cyclicals use normalized/mid-cycle earnings and never peak EPS times a normal
PE. Probabilities must sum approximately to 1. A good business is not automatically good odds. Return JSON only."""


def _json(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def _id(prefix: str, *parts: str) -> str:
    return prefix + hashlib.sha256(":".join(parts).encode()).hexdigest()[:24]


def _allowed_urls(result_sources: list[dict[str, Any]] | None) -> set[str]:
    return {str(x.get("url") or "").rstrip("/") for x in (result_sources or []) if x.get("url")}


def sanitize_snapshot(data: dict[str, Any], result_sources: list[dict[str, Any]] | None) -> None:
    allowed = _allowed_urls(result_sources)
    data["sources"] = [x for x in data.get("sources", []) if str(x.get("url") or "").rstrip("/") in allowed]
    valid = {x["source_id"] for x in data["sources"]}

    def clean(x: Any) -> None:
        if isinstance(x, dict):
            if "source_ids" in x:
                x["source_ids"] = [sid for sid in x.get("source_ids", []) if sid in valid]
                if x.get("value") is not None and not x["source_ids"]:
                    x["confidence"] = "LOW"
            for value in x.values():
                clean(value)
        elif isinstance(x, list):
            for value in x:
                clean(value)
    clean(data)
    if len(data["sources"]) < 3:
        data.setdefault("data_gaps", []).append("Fewer than three captured source roots after source validation.")


def metric(snapshot: dict[str, Any], name: str) -> float | None:
    for row in snapshot.get("market_metrics", []):
        if row.get("name", "").lower() == name.lower() and isinstance(row.get("value"), (int, float)):
            return float(row["value"])
    return None


def _gap(base: float | None, consensus: float | None) -> float | None:
    return None if base is None or consensus in (None, 0) else round(base / consensus - 1, 6)


def _entry_threshold(base: float, bear: float, normalized_value: float | None) -> tuple[float, float]:
    a = min(base / 1.30, bear / .75, (base + 1.5 * bear) / 2.5)
    b = min(base / 1.18, bear / .88, (base + 1.7 * bear) / 2.7)
    candidates = [x for x in (a, b, normalized_value) if x and x > 0]
    high = min(base, max(candidates))
    return round(max(0, min(bear, high * .90)), 4), round(high, 4)


def normalize_review(sec: Security, snapshot: dict[str, Any], review: dict[str, Any]) -> dict[str, Any]:
    current = metric(snapshot, "current_price")
    if current is None or current <= 0:
        raise ValueError(f"{sec.ticker}: current_price missing")
    by_name = {x["name"]: x for x in review["scenarios"]}
    if set(by_name) != {"BEAR", "BASE", "BULL"}:
        raise ValueError(f"{sec.ticker}: exactly Bear/Base/Bull required")
    complete = True
    for scenario in by_name.values():
        basis, multiple = scenario.get("valuation_basis"), scenario.get("fair_multiple")
        if not isinstance(basis, (int, float)) or not isinstance(multiple, (int, float)) or basis < 0 or multiple < 0:
            complete = False
            scenario["fair_value"] = None
        else:
            scenario["fair_value"] = round(float(basis) * float(multiple), 4)
    if not complete:
        review["computed"] = {"current_price": current, "odds_status": "VALUATION_INCOMPLETE", "gate_paths": {"A": False, "B": False, "C": False}}
        return review
    bear, base, bull = (float(by_name[x]["fair_value"]) for x in ("BEAR", "BASE", "BULL"))
    if not bear <= base <= bull:
        raise ValueError(f"{sec.ticker}: scenario order invalid")
    base_upside, bear_downside = base / current - 1, bear / current - 1
    rr = None if bear_downside >= 0 else base_upside / abs(bear_downside)
    probs = [max(0.0, float(by_name[x]["probability"])) for x in ("BEAR", "BASE", "BULL")]
    total = sum(probs)
    probs = [p / total for p in probs] if total else [.25, .50, .25]
    expected_value = sum(v * p for v, p in zip((bear, base, bull), probs))
    bridge = review["earnings_bridge"][-1]
    eps_gap, fcf_gap = _gap(bridge.get("eps_base"), bridge.get("eps_consensus")), _gap(bridge.get("fcf_base"), bridge.get("fcf_consensus"))
    normalized_eps = review["normalized_earnings"].get("normalized_eps")
    normalized_pe = current / normalized_eps if isinstance(normalized_eps, (int, float)) and normalized_eps > 0 else None
    ceiling = CYCLICAL_PE_CEILINGS.get(sec.ticker)
    normalized_gate = ceiling is None or (normalized_pe is not None and normalized_pe <= ceiling)
    path_a = base_upside >= .30 and bear_downside >= -.25 and rr is not None and rr >= 1.5
    path_b = base_upside >= .18 and bear_downside >= -.12 and rr is not None and rr >= 1.7
    cagr = review.get("three_year_eps_or_fcf_cagr")
    path_c = bool(isinstance(cagr, (int, float)) and .15 <= cagr <= .30 and review["valuation_reasonable"]
                  and review["balance_sheet_strong"] and review["roic_fcf_quality_strong"] and bear_downside >= -.25)
    data_ok = review["valuation_confidence"] in {"MEDIUM", "HIGH"} and review["evidence_quality_score"] >= 60
    thesis_ok = review["thesis_quality_score"] >= 65 and bool(review["catalysts"]) and bool(review["invalidation"])
    any_path = path_a or path_b or path_c
    blockers = []
    if not any_path: blockers.append("No Good Odds Path passes")
    if not normalized_gate: blockers.append(f"Normalized PE exceeds {ceiling:.0f}x gate")
    if not data_ok: blockers.append("Evidence/valuation confidence")
    if not thesis_ok: blockers.append("Thesis/catalyst/invalidation quality")
    if review["critical_data_missing"]: blockers.append("Critical data missing")
    if any_path and normalized_gate and data_ok and thesis_ok and not review["critical_data_missing"]:
        status = "BUY_CANDIDATE"
    elif review["valuation_confidence"] == "LOW":
        status = "VALUATION_INCOMPLETE"
    elif review["business_quality_score"] >= 75 and not any_path:
        status = "GOOD_COMPANY_BAD_ODDS"
    elif base_upside >= .10:
        status = "RESEARCH"
    else:
        status = "WATCH"
    normalized_value = normalized_eps * ceiling if ceiling and isinstance(normalized_eps, (int, float)) else None
    entry_low, entry_high = _entry_threshold(base, bear, normalized_value)
    score = max(0, min(100, 50 + 55 * base_upside + 12 * (rr or 0) + .12 * review["evidence_quality_score"] - 35 * max(0, -bear_downside)))
    review["computed"] = {
        "current_price": round(current, 4), "bear_fair_value": bear, "base_fair_value": base,
        "bull_fair_value": bull, "base_upside": round(base_upside, 6), "bear_downside": round(bear_downside, 6),
        "reward_risk": None if rr is None else round(rr, 4), "expected_fair_value": round(expected_value, 4),
        "expected_return": round(expected_value / current - 1, 6), "eps_gap": eps_gap, "fcf_gap": fcf_gap,
        "normalized_eps": normalized_eps, "normalized_pe": None if normalized_pe is None else round(normalized_pe, 4),
        "normalized_pe_ceiling": ceiling, "normalized_earnings_gate": normalized_gate,
        "gate_paths": {"A": path_a, "B": path_b, "C": path_c}, "odds_status": status,
        "odds_score": round(score, 1), "gate_blockers": blockers,
        "attractive_entry_low": entry_low, "attractive_entry_high": entry_high,
    }
    return review


def plan() -> dict[str, Any]:
    stages = []
    for sec in UNIVERSE:
        stages.extend([
            {"ticker": sec.ticker, "stage": "focused_financial_snapshot", "model": "gpt-5.6-terra", "reasoning": "high", "estimated_input_tokens": 9000, "estimated_output_tokens": 7000},
            {"ticker": sec.ticker, "stage": "focused_odds_analysis", "model": "gpt-5.6-terra", "reasoning": "high", "estimated_input_tokens": 16000, "estimated_output_tokens": 9000},
        ])
    # Token cost plus one web-search allowance for snapshot calls. Conservative planning figure.
    estimated = sum((x["estimated_input_tokens"] * 2 + x["estimated_output_tokens"] * 12) / 1_000_000 for x in stages) + .01 * len(UNIVERSE)
    return {
        "version": PROMPT_VERSION, "as_of_date": AS_OF_DATE, "universe": [asdict(x) for x in UNIVERSE],
        "stages": stages, "planned_calls": len(stages), "actual_api_calls": 0,
        "estimated_cost_usd": round(estimated, 4),
        "hard_gates": {"model": "gpt-5.6-terra", "run_budget_usd": 30, "daily_budget_usd": 35,
                       "call_limit": 18, "expensive_jobs": False, "retries": 0},
    }


def persist_snapshot(con: sqlite3.Connection, sec: Security, data: dict[str, Any], model: str) -> str:
    digest = hashlib.sha256(_json(data).encode()).hexdigest()
    con.execute("""INSERT INTO focused_financial_snapshots
      (snapshot_id,ticker,company,exchange,currency,as_of_date,snapshot_json,source_digest,model,prompt_version)
      VALUES (?,?,?,?,?,?,?,?,?,?) ON CONFLICT(ticker,prompt_version) DO UPDATE SET
      as_of_date=excluded.as_of_date,snapshot_json=excluded.snapshot_json,source_digest=excluded.source_digest,
      model=excluded.model,updated_at=strftime('%Y-%m-%dT%H:%M:%fZ','now')""",
      (_id("fs_", sec.ticker, SNAPSHOT_VERSION), sec.ticker, sec.company, sec.exchange, sec.currency,
       data["as_of_date"], _json(data), digest, model, SNAPSHOT_VERSION))
    return digest


def persist_review(con: sqlite3.Connection, sec: Security, data: dict[str, Any], digest: str, model: str) -> None:
    c = data["computed"]
    con.execute("""INSERT INTO focused_odds_reviews
      (review_id,ticker,company,exchange,currency,as_of_date,current_price,bear_fair_value,base_fair_value,
       bull_fair_value,base_upside,bear_downside,reward_risk,expected_return,expectations_gap,odds_status,
       actionability,attractive_entry_low,attractive_entry_high,exposure_purity,earnings_sensitivity,
       normalized_eps,normalized_pe,three_year_cagr,analysis_json,source_digest,model,prompt_version)
      VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
      ON CONFLICT(ticker,prompt_version) DO UPDATE SET
       as_of_date=excluded.as_of_date,current_price=excluded.current_price,bear_fair_value=excluded.bear_fair_value,
       base_fair_value=excluded.base_fair_value,bull_fair_value=excluded.bull_fair_value,
       base_upside=excluded.base_upside,bear_downside=excluded.bear_downside,reward_risk=excluded.reward_risk,
       expected_return=excluded.expected_return,expectations_gap=excluded.expectations_gap,
       odds_status=excluded.odds_status,actionability=excluded.actionability,
       attractive_entry_low=excluded.attractive_entry_low,attractive_entry_high=excluded.attractive_entry_high,
       exposure_purity=excluded.exposure_purity,earnings_sensitivity=excluded.earnings_sensitivity,
       normalized_eps=excluded.normalized_eps,normalized_pe=excluded.normalized_pe,
       three_year_cagr=excluded.three_year_cagr,analysis_json=excluded.analysis_json,
       source_digest=excluded.source_digest,model=excluded.model,updated_at=strftime('%Y-%m-%dT%H:%M:%fZ','now')""",
      (_id("fr_", sec.ticker, PROMPT_VERSION), sec.ticker, sec.company, sec.exchange, sec.currency,
       data["as_of_date"], c["current_price"], c["bear_fair_value"], c["base_fair_value"], c["bull_fair_value"],
       c["base_upside"], c["bear_downside"], c["reward_risk"], c["expected_return"], data["expectations_gap"],
       c["odds_status"], c["odds_status"], c["attractive_entry_low"], c["attractive_entry_high"],
       data["exposure_purity"], data["earnings_sensitivity"], c["normalized_eps"], c["normalized_pe"],
       data["three_year_eps_or_fcf_cagr"], _json(data), digest, model, PROMPT_VERSION))


def usage(con: sqlite3.Connection, run_id: str) -> dict[str, Any]:
    rows = con.execute("""SELECT entity_id,status,input_tokens,cached_input_tokens,output_tokens,
      estimated_cost,actual_cost_if_available FROM ai_usage_ledger WHERE run_id=?""", (run_id,)).fetchall()
    attempted = [x for x in rows if x[1] in {"PENDING", "SUCCESS", "FAILED", "CANCELLED", "UNKNOWN_COST"}]
    return {
        "attempted_calls": len(attempted), "successful_calls": sum(x[1] == "SUCCESS" for x in rows),
        "input_tokens": sum(int(x[2] or 0) for x in rows if x[1] == "SUCCESS"),
        "cached_input_tokens": sum(int(x[3] or 0) for x in rows if x[1] == "SUCCESS"),
        "output_tokens": sum(int(x[4] or 0) for x in rows if x[1] == "SUCCESS"),
        "known_cost_usd": round(sum(float(x[6] or 0) for x in rows if x[6] is not None), 8),
        "risk_cost_usd": round(sum(float(x[6] if x[6] is not None else x[5] or 0) for x in attempted), 8),
        "by_security": {ticker: {
            "calls": sum(1 for x in attempted if x[0] == ticker),
            "risk_cost_usd": round(sum(float(x[6] if x[6] is not None else x[5] or 0) for x in attempted if x[0] == ticker), 8),
        } for ticker in [x.ticker for x in UNIVERSE]},
    }


def rows(con: sqlite3.Connection) -> list[dict[str, Any]]:
    out = []
    for row in con.execute("SELECT ticker,company,currency,analysis_json FROM focused_odds_reviews WHERE prompt_version=?", (PROMPT_VERSION,)):
        data, c = json.loads(row[3]), json.loads(row[3])["computed"]
        out.append({"ticker": row[0], "company": row[1], "currency": row[2], "group": next(x.group for x in UNIVERSE if x.ticker == row[0]),
                    **c, "expectations_gap": data["expectations_gap"], "exposure_purity": data["exposure_purity"],
                    "earnings_sensitivity": data["earnings_sensitivity"], "one_line_conclusion": data["one_line_conclusion"],
                    "earnings_bridge": data["earnings_bridge"], "catalysts": data["catalysts"], "invalidation": data["invalidation"],
                    "why_not_buy_now": data["why_not_buy_now"], "what_changes_the_decision": data["what_changes_the_decision"],
                    "scenarios": data["scenarios"], "key_risks": data["key_risks"], "business_quality_score": data["business_quality_score"],
                    "thesis_quality_score": data["thesis_quality_score"], "evidence_quality_score": data["evidence_quality_score"],
                    "valuation_confidence": data["valuation_confidence"], "thesis_confidence": data["thesis_confidence"]})
    priority = {"BUY_CANDIDATE": 0, "RESEARCH": 1, "WATCH": 2, "GOOD_COMPANY_BAD_ODDS": 3, "VALUATION_INCOMPLETE": 4}
    return sorted(out, key=lambda x: (priority.get(x["odds_status"], 9), -(x.get("expected_return") or -9), -x["odds_score"]))


def build_report(con: sqlite3.Connection, run_id: str, errors: list[dict[str, Any]]) -> dict[str, Any]:
    review_rows, cost = rows(con), usage(con, run_id)
    groups = {}
    for group in ("PHYSICAL_INFRA", "MEMORY", "PACKAGING"):
        subset = [x for x in review_rows if x["group"] == group]
        groups[group] = {
            "best_business": max(subset, key=lambda x: x["business_quality_score"])["ticker"] if subset else None,
            "best_odds": max(subset, key=lambda x: x["odds_score"])["ticker"] if subset else None,
        }
    return {"version": PROMPT_VERSION, "as_of_date": AS_OF_DATE,
            "status": "COMPLETED" if len(review_rows) == 6 and not errors else "PARTIAL",
            "stop_state": "FOCUSED ODDS REVIEW READY", "production_changed": False,
            "universe_count": 6, "completed_count": len(review_rows), "ranking": review_rows,
            "best_business_vs_best_odds": groups, "errors": errors, "cost": cost}


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--db", default=os.getenv("SIGNALBOARD_DB", DB_PATH))
    parser.add_argument("--output-dir", default=str(OUTPUT_DIR))
    parser.add_argument("--plan-only", action="store_true")
    args = parser.parse_args()
    output = Path(args.output_dir); output.mkdir(parents=True, exist_ok=True)
    if args.plan_only:
        payload = plan()
        (output / "dry_run_plan.json").write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
        print(json.dumps(payload, ensure_ascii=False, indent=2)); return
    init_db(args.db)
    con = sqlite3.connect(args.db, timeout=120); con.row_factory = sqlite3.Row
    run_id = os.getenv("AI_RUN_ID", "focused-odds-local")
    force = os.getenv("FORCE_REANALYZE", "false").lower() in {"1", "true", "yes"}
    errors: list[dict[str, Any]] = []
    for sec in UNIVERSE:
        try:
            cached = None if force else con.execute("SELECT snapshot_json,source_digest,model FROM focused_financial_snapshots WHERE ticker=? AND prompt_version=?", (sec.ticker, SNAPSHOT_VERSION)).fetchone()
            if cached:
                snapshot, digest, snapshot_model = json.loads(cached[0]), cached[1], cached[2]
            else:
                result = call_json_web("focused_financial_snapshot", SNAPSHOT_SYSTEM,
                    _json({"security": asdict(sec), "required_as_of": AS_OF_DATE,
                           "required_market_metric_names": ["current_price", "market_cap", "enterprise_value", "ttm_revenue", "ttm_eps", "ttm_fcf", "forward_pe"]}), SNAPSHOT_SCHEMA,
                    schema_name="focused_financial_snapshot", max_output_tokens=11000, timeout=600, max_retries=0,
                    prompt_version=SNAPSHOT_VERSION, entity_type="focused_security", entity_id=sec.ticker)
                snapshot = result.data; sanitize_snapshot(snapshot, result.sources)
                digest, snapshot_model = persist_snapshot(con, sec, snapshot, result.model)
                record_usage(con, result, workload="focused_financial_snapshot", object_type="focused_security", object_id=sec.ticker)
                con.commit()
            review_cached = None if force else con.execute("SELECT analysis_json FROM focused_odds_reviews WHERE ticker=? AND prompt_version=? AND source_digest=?", (sec.ticker, PROMPT_VERSION, digest)).fetchone()
            if review_cached:
                continue
            result = call_json("focused_odds_analysis", REVIEW_SYSTEM,
                _json({"security": asdict(sec), "snapshot": snapshot, "cyclical_normalized_pe_ceiling": CYCLICAL_PE_CEILINGS.get(sec.ticker)}),
                REVIEW_SCHEMA, schema_name="focused_odds_review", max_output_tokens=13000, timeout=600, max_retries=0,
                prompt_version=PROMPT_VERSION, entity_type="focused_security", entity_id=sec.ticker)
            review = normalize_review(sec, snapshot, result.data)
            persist_review(con, sec, review, digest, result.model)
            record_usage(con, result, workload="focused_odds_analysis", object_type="focused_security", object_id=sec.ticker)
            con.commit()
        except Exception as exc:
            con.rollback(); errors.append({"ticker": sec.ticker, "error_type": type(exc).__name__, "message": str(exc)[:500]})
    report = build_report(con, run_id, errors)
    con.execute("""INSERT OR REPLACE INTO focused_odds_runs
      (run_id,status,universe_json,report_json,ai_calls,known_cost_usd,risk_cost_usd) VALUES (?,?,?,?,?,?,?)""",
      (run_id, report["status"], _json([asdict(x) for x in UNIVERSE]), _json(report),
       report["cost"]["attempted_calls"], report["cost"]["known_cost_usd"], report["cost"]["risk_cost_usd"]))
    con.commit(); con.close()
    (output / "run_report.json").write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    (output / "six_security_reviews.json").write_text(json.dumps(report["ranking"], ensure_ascii=False, indent=2), encoding="utf-8")
    (output / "cost_by_security.json").write_text(json.dumps(report["cost"], ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(report, ensure_ascii=False, indent=2))
    if report["status"] != "COMPLETED":
        raise SystemExit(2)


if __name__ == "__main__":
    main()
