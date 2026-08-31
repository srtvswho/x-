#!/usr/bin/env python3
"""Build the bounded Opportunity Odds MVP for the existing v1.2.1 Preview.

The script researches only seven pre-declared listed securities across the five
highest-priority opportunities.  It keeps raw sourced research in JSON, then
recomputes fair values, gaps, reward/risk, the configurable gate and the Odds
Score deterministically before persisting anything.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import sqlite3
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from signalboard.ai.guardrails import AIGuardrailBlocked
from signalboard.ai.router import call_json_web, record_usage
from signalboard.db import init_db


DB_PATH = "/workspace/data/signalboard_full.db"
OUTPUT_DIR = Path("outputs/opportunity_odds_v13")
PROMPT_VERSION = "opportunity-odds-v1.3"


@dataclass(frozen=True)
class Security:
    opportunity_id: str
    ticker: str
    company: str
    exchange: str
    currency: str


UNIVERSE = (
    Security("opp_f9ce9de1c1cd0a6af97cf684", "AAON", "AAON", "NASDAQ", "USD"),
    Security("opp_f9ce9de1c1cd0a6af97cf684", "HPS.A", "Hammond Power Solutions", "TSX", "CAD"),
    Security("opp_059a0ded5581814ea9612dc2", "TWSE:3006", "Elite Semiconductor Microelectronics Technology", "TWSE", "TWD"),
    Security("opp_a2cb1781922c965f79ff62e8", "MU", "Micron Technology", "NASDAQ", "USD"),
    Security("opp_a2cb1781922c965f79ff62e8", "000660.KS", "SK hynix", "KRX", "KRW"),
    Security("opp_10fee5b31c947c44118b429a", "COHR", "Coherent", "NYSE", "USD"),
    Security("opp_10fee5b31c947c44118b429a", "LITE", "Lumentum", "NASDAQ", "USD"),
)


NULLABLE_NUMBER = {"type": ["number", "null"]}
SOURCE_IDS = {"type": "array", "maxItems": 5, "items": {"type": "string"}}


def _metric_schema(*, currency: bool = True) -> dict[str, Any]:
    props: dict[str, Any] = {
        "value": NULLABLE_NUMBER,
        "label": {"type": "string", "enum": ["KNOWN", "CONSENSUS", "AI_ESTIMATE", "ASSUMPTION", "UNKNOWN"]},
        "fiscal_period": {"type": ["string", "null"]},
        "as_of_date": {"type": ["string", "null"]},
        "source_ids": SOURCE_IDS,
        "confidence": {"type": "string", "enum": ["LOW", "MEDIUM", "HIGH"]},
    }
    if currency:
        props["currency"] = {"type": ["string", "null"]}
    return {"type": "object", "additionalProperties": False, "properties": props, "required": list(props)}


FORECAST_SCHEMA = {
    "type": "object", "additionalProperties": False,
    "properties": {
        "fiscal_period": {"type": "string"},
        "revenue": _metric_schema(), "eps": _metric_schema(),
        "ebitda": _metric_schema(), "fcf": _metric_schema(),
        "revenue_growth": _metric_schema(currency=False),
        "eps_growth": _metric_schema(currency=False),
    },
    "required": ["fiscal_period", "revenue", "eps", "ebitda", "fcf", "revenue_growth", "eps_growth"],
}


SCENARIO_SCHEMA = {
    "type": "object", "additionalProperties": False,
    "properties": {
        "name": {"type": "string", "enum": ["BEAR", "BASE", "BULL"]},
        "fiscal_period": {"type": "string"},
        "revenue": NULLABLE_NUMBER,
        "eps": NULLABLE_NUMBER,
        "normalized_eps": NULLABLE_NUMBER,
        "fcf": NULLABLE_NUMBER,
        "valuation_method": {"type": "string", "enum": ["FORWARD_PE", "NORMALIZED_PE", "MID_CYCLE_PE", "OTHER"]},
        "valuation_basis": NULLABLE_NUMBER,
        "fair_multiple": NULLABLE_NUMBER,
        "fair_value": NULLABLE_NUMBER,
        "probability": NULLABLE_NUMBER,
        "assumptions": {"type": "array", "maxItems": 6, "items": {"type": "string"}},
        "multiple_reason": {"type": "string"},
    },
    "required": [
        "name", "fiscal_period", "revenue", "eps", "normalized_eps", "fcf",
        "valuation_method", "valuation_basis", "fair_multiple", "fair_value",
        "probability", "assumptions", "multiple_reason",
    ],
}


SOURCE_SCHEMA = {
    "type": "object", "additionalProperties": False,
    "properties": {
        "source_id": {"type": "string"}, "title": {"type": "string"},
        "url": {"type": "string"}, "publisher": {"type": "string"},
        "tier": {"type": "string", "enum": ["PRIMARY", "EXCHANGE", "CONSENSUS", "SECONDARY", "UNKNOWN"]},
        "as_of_date": {"type": ["string", "null"]},
        "fiscal_period": {"type": ["string", "null"]},
        "fields": {"type": "array", "maxItems": 10, "items": {"type": "string"}},
        "finding": {"type": "string"},
    },
    "required": ["source_id", "title", "url", "publisher", "tier", "as_of_date", "fiscal_period", "fields", "finding"],
}


ODDS_SCHEMA = {
    "type": "object", "additionalProperties": False,
    "properties": {
        "ticker": {"type": "string"}, "company": {"type": "string"},
        "exchange": {"type": "string"}, "currency": {"type": "string"},
        "as_of_date": {"type": "string"}, "fiscal_year_end": {"type": ["string", "null"]},
        "market_data": {
            "type": "object", "additionalProperties": False,
            "properties": {
                "current_price": _metric_schema(), "market_cap": _metric_schema(),
                "ttm_revenue": _metric_schema(), "ttm_eps": _metric_schema(),
                "ttm_pe": _metric_schema(currency=False), "forward_pe": _metric_schema(currency=False),
                "forecasts": {"type": "array", "minItems": 1, "maxItems": 3, "items": FORECAST_SCHEMA},
                "historical_multiple_range": {"type": "string"},
                "peer_valuation": {"type": "string"},
                "analyst_range": {"type": "string"},
                "consensus_quality": {"type": "string", "enum": ["RELIABLE", "CONSENSUS_LOW_CONFIDENCE", "UNAVAILABLE"]},
            },
            "required": [
                "current_price", "market_cap", "ttm_revenue", "ttm_eps", "ttm_pe", "forward_pe",
                "forecasts", "historical_multiple_range", "peer_valuation", "analyst_range", "consensus_quality",
            ],
        },
        "market_expectations": {
            "type": "object", "additionalProperties": False,
            "properties": {
                "level": {"type": "string", "enum": ["LOW", "MODERATE", "HIGH", "EXTREME", "UNKNOWN"]},
                "summary": {"type": "string"}, "what_market_is_pricing": {"type": "string"},
            }, "required": ["level", "summary", "what_market_is_pricing"],
        },
        "earnings_bridge": {
            "type": "object", "additionalProperties": False,
            "properties": {
                "fiscal_period": {"type": "string"}, "thesis_driver": {"type": "string"},
                "revenue_impact": {"type": "string"}, "margin_impact": {"type": "string"},
                "eps_fcf_impact": {"type": "string"},
                "consensus_revenue": _metric_schema(), "our_base_revenue": _metric_schema(),
                "consensus_margin": _metric_schema(currency=False), "our_base_margin": _metric_schema(currency=False),
                "consensus_eps": _metric_schema(), "our_base_eps": _metric_schema(),
                "consensus_fcf": _metric_schema(), "our_base_fcf": _metric_schema(),
                "revenue_gap": NULLABLE_NUMBER, "margin_gap": NULLABLE_NUMBER,
                "eps_gap": NULLABLE_NUMBER, "fcf_gap": NULLABLE_NUMBER,
            },
            "required": [
                "fiscal_period", "thesis_driver", "revenue_impact", "margin_impact", "eps_fcf_impact",
                "consensus_revenue", "our_base_revenue", "consensus_margin", "our_base_margin",
                "consensus_eps", "our_base_eps", "consensus_fcf", "our_base_fcf",
                "revenue_gap", "margin_gap", "eps_gap", "fcf_gap",
            ],
        },
        "scenarios": {"type": "array", "minItems": 3, "maxItems": 3, "items": SCENARIO_SCHEMA},
        "cyclical_risk": {
            "type": "object", "additionalProperties": False,
            "properties": {
                "is_cyclical": {"type": "boolean"}, "peak_earnings_risk": {"type": "boolean"},
                "normalization_method": {"type": "string"}, "warning": {"type": "string"},
            }, "required": ["is_cyclical", "peak_earnings_risk", "normalization_method", "warning"],
        },
        "catalyst": {"type": "string"}, "catalyst_within_18m": {"type": "boolean"},
        "invalidation": {"type": "string"}, "invalidation_clear": {"type": "boolean"},
        "why_not_buy_now": {"type": "string"}, "verdict": {"type": "string"},
        "valuation_confidence": {"type": "string", "enum": ["LOW", "MEDIUM", "HIGH"]},
        "thesis_confidence": {"type": "string", "enum": ["LOW", "MEDIUM", "HIGH"]},
        "data_gaps": {"type": "array", "maxItems": 8, "items": {"type": "string"}},
        "source_roots": {"type": "array", "maxItems": 15, "items": SOURCE_SCHEMA},
    },
    "required": [
        "ticker", "company", "exchange", "currency", "as_of_date", "fiscal_year_end",
        "market_data", "market_expectations", "earnings_bridge", "scenarios", "cyclical_risk",
        "catalyst", "catalyst_within_18m", "invalidation", "invalidation_clear",
        "why_not_buy_now", "verdict", "valuation_confidence", "thesis_confidence",
        "data_gaps", "source_roots",
    ],
}


SYSTEM_PROMPT = """你是买方研究团队的估值负责人。任务是判断当前价格的赔率，不是重复证明公司或行业很好。

必须使用 web search，数据截止 2026-08-31。优先公司 IR/SEC/交易所/正式财报，其次可靠 consensus 数据；不得依赖单一随机网页。所有价格、财务与 consensus 字段必须记录 source_id、as_of_date、fiscal_period、currency、confidence。Calendar Year 与 Fiscal Year 不得无说明混用；ADR、本地股与币种不得混用。找不到可靠数据时 value=null、label=UNKNOWN，并列入 data_gaps，禁止编数字。

先总结市场当前押注 LOW/MODERATE/HIGH/EXTREME，再建立 Driver→Revenue→Margin→EPS/FCF 的最小 Earnings Bridge。每个数字严格标注 KNOWN/CONSENSUS/AI_ESTIMATE/ASSUMPTION/UNKNOWN。构建 Bear/Base/Bull；每个情景给估值依据和倍数理由。对于 MU、SK hynix、ESMT 等周期股，禁止“峰值 EPS × 正常 PE”，优先 normalized/mid-cycle earnings，并明确 PEAK_EARNINGS_RISK。

fair_value 必须可由 valuation_basis × fair_multiple 复算。概率只是低精度辅助，若给出则三项和为 1。输出紧凑 JSON；每个解释最多两句话。不要在 JSON 前后输出分析过程。"""


def _json(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def _env_float(name: str, default: float) -> float:
    try:
        return float(os.getenv(name, str(default)))
    except ValueError as exc:
        raise ValueError(f"Invalid {name}") from exc


def gate_config() -> dict[str, float]:
    return {
        "strong_positive_gap": _env_float("ODDS_STRONGLY_POSITIVE_GAP", 0.35),
        "positive_gap": _env_float("ODDS_POSITIVE_GAP", 0.20),
        "neutral_gap": _env_float("ODDS_NEUTRAL_GAP", 0.10),
        "buy_min_thesis_quality": _env_float("ODDS_BUY_MIN_THESIS_QUALITY", 70),
        "buy_min_evidence_quality": _env_float("ODDS_BUY_MIN_EVIDENCE_QUALITY", 60),
        "buy_min_chain_completeness": _env_float("ODDS_BUY_MIN_CHAIN_COMPLETENESS", 5),
        "buy_min_base_upside": _env_float("ODDS_BUY_MIN_BASE_UPSIDE", 0.25),
        "buy_max_bear_downside": _env_float("ODDS_BUY_MAX_BEAR_DOWNSIDE", 0.25),
        "buy_min_reward_risk": _env_float("ODDS_BUY_MIN_REWARD_RISK", 1.5),
        "band_very_good": _env_float("ODDS_BAND_VERY_GOOD", 80),
        "band_good": _env_float("ODDS_BAND_GOOD", 65),
        "band_fair": _env_float("ODDS_BAND_FAIR", 45),
        "band_poor": _env_float("ODDS_BAND_POOR", 30),
    }


def _opportunity_context(con: sqlite3.Connection, sec: Security) -> dict[str, Any]:
    row = con.execute(
        """SELECT opportunity_id,title,actionability,chain_completeness,opportunity_score,
                  thesis_quality_score,evidence_quality_score,earnings_impact_score,catalyst_score,
                  one_line_thesis,driver,industry_change,bottleneck,earnings_mechanism,
                  valuation_question,market_expectations,catalysts_json,risks_json,
                  invalidation_conditions_json,missing_evidence_json,synthesis_json
           FROM investment_opportunities WHERE opportunity_id=?""",
        (sec.opportunity_id,),
    ).fetchone()
    if not row:
        raise RuntimeError(f"Missing opportunity {sec.opportunity_id}")
    keys = [
        "opportunity_id", "title", "actionability", "chain_completeness", "opportunity_score",
        "thesis_quality_score", "evidence_quality_score", "earnings_impact_score", "catalyst_score",
        "one_line_thesis", "driver", "industry_change", "bottleneck", "earnings_mechanism",
        "valuation_question", "market_expectations", "catalysts", "risks", "invalidation",
        "missing_evidence", "synthesis",
    ]
    payload = dict(zip(keys, row))
    for key in ("catalysts", "risks", "invalidation", "missing_evidence", "synthesis"):
        payload[key] = json.loads(payload[key] or ("{}" if key == "synthesis" else "[]"))
    best_row = con.execute(
        "SELECT analysis_json FROM opportunity_best_expressions WHERE opportunity_id=?", (sec.opportunity_id,)
    ).fetchone()
    best = json.loads(best_row[0]) if best_row else {}
    ranking = next((r for r in best.get("rankings", []) if r.get("ticker") == sec.ticker), None)
    payload["security"] = {
        "ticker": sec.ticker, "company": sec.company, "exchange": sec.exchange, "currency": sec.currency,
        "best_expression_ranking": ranking,
        "best_expression_summary": {
            "best_expression": best.get("best_expression"), "runner_up": best.get("runner_up"),
            "thesis_strength": best.get("thesis_strength"), "price_in_summary": best.get("price_in_summary"),
            "verdict": best.get("verdict"), "source_roots": best.get("source_roots", [])[:8],
        },
    }
    return payload


def _allowed_urls(result_sources: list[dict[str, Any]] | None) -> set[str]:
    return {str(x.get("url") or "").rstrip("/") for x in (result_sources or []) if x.get("url")}


def _sanitize_sources(data: dict[str, Any], result_sources: list[dict[str, Any]] | None) -> None:
    allowed = _allowed_urls(result_sources)
    retained = [x for x in data.get("source_roots", []) if str(x.get("url") or "").rstrip("/") in allowed]
    data["source_roots"] = retained
    valid_ids = {x["source_id"] for x in retained}

    def clean_metric(metric: Any) -> None:
        if not isinstance(metric, dict) or "source_ids" not in metric:
            return
        metric["source_ids"] = [x for x in metric.get("source_ids", []) if x in valid_ids]
        if metric.get("value") is not None and not metric["source_ids"]:
            metric["confidence"] = "LOW"

    market = data.get("market_data") or {}
    for key, value in market.items():
        if key == "forecasts":
            for forecast in value or []:
                for metric in forecast.values():
                    clean_metric(metric)
        else:
            clean_metric(value)
    for metric in (data.get("earnings_bridge") or {}).values():
        clean_metric(metric)
    strong_tiers = {x.get("tier") for x in retained}
    if len(retained) < 2 or not strong_tiers.intersection({"PRIMARY", "EXCHANGE", "CONSENSUS"}):
        data["valuation_confidence"] = "LOW"
        gaps = data.setdefault("data_gaps", [])
        warning = "Insufficient independently captured market/filing sources; valuation confidence forced to LOW."
        if warning not in gaps:
            gaps.append(warning)


def _value(metric: Any) -> float | None:
    value = metric.get("value") if isinstance(metric, dict) else metric
    return float(value) if isinstance(value, (int, float)) else None


def _gap(ours: float | None, consensus: float | None) -> float | None:
    if ours is None or consensus in (None, 0):
        return None
    return round(ours / consensus - 1, 6)


def _clamp(value: float, low: float = 0.0, high: float = 100.0) -> float:
    return min(high, max(low, value))


def _gap_label(gap: float | None, cfg: dict[str, float]) -> str:
    if gap is None:
        return "UNKNOWN"
    if gap > cfg["strong_positive_gap"]:
        return "STRONGLY_POSITIVE"
    if gap > cfg["positive_gap"]:
        return "POSITIVE"
    if gap >= -cfg["neutral_gap"]:
        return "NEUTRAL"
    if gap >= -cfg["strong_positive_gap"]:
        return "NEGATIVE"
    return "STRONGLY_NEGATIVE"


def _odds_score(data: dict[str, Any], context: dict[str, Any], gap: float | None, upside: float, rr: float | None) -> float | None:
    if data["valuation_confidence"] == "LOW" and gap is None:
        return None
    gap_score = 50.0 if gap is None else _clamp((gap + 0.20) / 0.60 * 100)
    upside_score = _clamp((upside + 0.20) / 0.80 * 100)
    rr_score = 0.0 if rr is None else _clamp(rr / 3.0 * 100)
    evidence = float(context["evidence_quality_score"])
    catalyst = float(context["catalyst_score"])
    valuation = {"LOW": 30.0, "MEDIUM": 65.0, "HIGH": 90.0}[data["valuation_confidence"]]
    return round(0.25 * gap_score + 0.20 * upside_score + 0.20 * rr_score + 0.15 * evidence + 0.10 * catalyst + 0.10 * valuation, 1)


def _odds_band(score: float | None, cfg: dict[str, float]) -> str:
    if score is None:
        return "INCOMPLETE"
    if score >= cfg["band_very_good"]:
        return "VERY_GOOD"
    if score >= cfg["band_good"]:
        return "GOOD"
    if score >= cfg["band_fair"]:
        return "FAIR"
    if score >= cfg["band_poor"]:
        return "POOR"
    return "VERY_POOR"


def _gate(data: dict[str, Any], context: dict[str, Any], metrics: dict[str, Any], cfg: dict[str, float]) -> tuple[str, list[str]]:
    reasons: list[str] = []
    reliable = data["valuation_confidence"] in {"MEDIUM", "HIGH"}
    evidence_ok = float(context["evidence_quality_score"]) >= cfg["buy_min_evidence_quality"]
    thesis_ok = float(context["thesis_quality_score"]) >= cfg["buy_min_thesis_quality"]
    complete = float(context["chain_completeness"]) >= cfg["buy_min_chain_completeness"]
    gap_ok = metrics["earnings_gap"] is not None and metrics["earnings_gap"] >= cfg["positive_gap"]
    upside_ok = metrics["base_upside"] >= cfg["buy_min_base_upside"]
    downside_ok = metrics["bear_downside"] >= -cfg["buy_max_bear_downside"]
    rr_ok = metrics["reward_risk"] is not None and metrics["reward_risk"] >= cfg["buy_min_reward_risk"]
    catalyst_ok = bool(data["catalyst_within_18m"])
    invalidation_ok = bool(data["invalidation_clear"])

    checks = {
        "thesis quality": thesis_ok, "evidence quality": evidence_ok, "chain completeness": complete,
        "positive earnings gap": gap_ok, "base upside": upside_ok, "bear downside": downside_ok,
        "reward/risk": rr_ok, "6–18m catalyst": catalyst_ok, "clear invalidation": invalidation_ok,
        "valuation data": reliable,
    }
    reasons = [name for name, passed in checks.items() if not passed]
    if all(checks.values()):
        return "BUY_CANDIDATE", []
    if not reliable or metrics["earnings_gap"] is None:
        return "VALUATION_INCOMPLETE", reasons
    good_odds = upside_ok and rr_ok
    strong_research = thesis_ok and evidence_ok
    if strong_research and not good_odds:
        return "GOOD_COMPANY_BAD_ODDS", reasons
    if good_odds and not strong_research:
        return "GOOD_ODDS_WEAK_EVIDENCE", reasons
    return ("RESEARCH" if context["actionability"] == "RESEARCH" and strong_research else "WATCH"), reasons


def normalize_analysis(data: dict[str, Any], context: dict[str, Any], cfg: dict[str, float]) -> dict[str, Any]:
    current = _value(data["market_data"]["current_price"])
    if current is None or current <= 0:
        raise ValueError("Current price unavailable")
    scenarios = {x["name"]: x for x in data["scenarios"]}
    if set(scenarios) != {"BEAR", "BASE", "BULL"}:
        raise ValueError("Exactly Bear/Base/Bull required")
    valuation_complete = True
    for scenario in scenarios.values():
        basis, multiple = scenario.get("valuation_basis"), scenario.get("fair_multiple")
        if basis is None or multiple is None or basis < 0 or multiple < 0:
            scenario["fair_value"] = None
            valuation_complete = False
        else:
            scenario["fair_value"] = round(float(basis) * float(multiple), 4)

    bridge = data["earnings_bridge"]
    bridge["revenue_gap"] = _gap(_value(bridge["our_base_revenue"]), _value(bridge["consensus_revenue"]))
    bridge["margin_gap"] = None if _value(bridge["our_base_margin"]) is None or _value(bridge["consensus_margin"]) is None else round(_value(bridge["our_base_margin"]) - _value(bridge["consensus_margin"]), 6)
    bridge["eps_gap"] = _gap(_value(bridge["our_base_eps"]), _value(bridge["consensus_eps"]))
    bridge["fcf_gap"] = _gap(_value(bridge["our_base_fcf"]), _value(bridge["consensus_fcf"]))
    earnings_gap = bridge["eps_gap"] if bridge["eps_gap"] is not None else bridge["fcf_gap"]

    if not valuation_complete:
        metrics = {
            "current_price": current, "bear_fair_value": None, "base_fair_value": None,
            "bull_fair_value": None, "base_upside": None, "bear_downside": None,
            "reward_risk": None, "expected_fair_value": None, "expected_return": None,
            "earnings_gap": earnings_gap,
        }
        data["valuation_confidence"] = "LOW"
        data["computed"] = {
            **metrics, "expectations_gap": _gap_label(earnings_gap, cfg), "odds_score": None,
            "odds_band": "INCOMPLETE", "odds_status": "VALUATION_INCOMPLETE",
            "buy_gate_blockers": ["valuation data"],
        }
        return data

    bear, base, bull = (float(scenarios[x]["fair_value"]) for x in ("BEAR", "BASE", "BULL"))
    if not (bear <= base <= bull):
        raise ValueError(f"Scenario order invalid: {bear}, {base}, {bull}")
    base_upside = round(base / current - 1, 6)
    bear_downside = round(bear / current - 1, 6)
    reward_risk = None if bear_downside >= 0 else round(base_upside / abs(bear_downside), 4)

    probabilities = [scenarios[x].get("probability") for x in ("BEAR", "BASE", "BULL")]
    expected_value = expected_return = None
    if all(isinstance(x, (int, float)) and x >= 0 for x in probabilities):
        total = sum(float(x) for x in probabilities)
        if total > 0:
            probs = [float(x) / total for x in probabilities]
            for name, probability in zip(("BEAR", "BASE", "BULL"), probs):
                scenarios[name]["probability"] = round(probability, 6)
            expected_value = round(sum(v * p for v, p in zip((bear, base, bull), probs)), 4)
            expected_return = round(expected_value / current - 1, 6)

    metrics = {
        "current_price": current, "bear_fair_value": bear, "base_fair_value": base,
        "bull_fair_value": bull, "base_upside": base_upside, "bear_downside": bear_downside,
        "reward_risk": reward_risk, "expected_fair_value": expected_value,
        "expected_return": expected_return, "earnings_gap": earnings_gap,
    }
    score = _odds_score(data, context, earnings_gap, base_upside, reward_risk)
    status, blockers = _gate(data, context, metrics, cfg)
    data["computed"] = {
        **metrics, "expectations_gap": _gap_label(earnings_gap, cfg),
        "odds_score": score, "odds_band": _odds_band(score, cfg),
        "odds_status": status, "buy_gate_blockers": blockers,
    }
    return data


def _rank_for_security(context: dict[str, Any]) -> int | None:
    ranking = context["security"].get("best_expression_ranking") or {}
    value = ranking.get("rank")
    return int(value) if isinstance(value, int) else None


def _persist(con: sqlite3.Connection, sec: Security, context: dict[str, Any], data: dict[str, Any], digest: str, model: str) -> None:
    c = data["computed"]
    odds_id = "odds_" + hashlib.sha256(f"{sec.opportunity_id}:{sec.ticker}:{PROMPT_VERSION}".encode()).hexdigest()[:24]
    con.execute(
        """INSERT INTO opportunity_odds(
             odds_id,opportunity_id,ticker,company,exchange,currency,best_expression_rank,
             analysis_json,source_digest,model,prompt_version,as_of_date,current_price,
             bear_fair_value,base_fair_value,bull_fair_value,base_upside,bear_downside,
             reward_risk,expected_fair_value,expected_return,earnings_gap,expectations_gap,
             odds_band,odds_score,odds_status,valuation_confidence,thesis_confidence)
           VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
           ON CONFLICT(opportunity_id,ticker,prompt_version) DO UPDATE SET
             company=excluded.company,exchange=excluded.exchange,currency=excluded.currency,
             best_expression_rank=excluded.best_expression_rank,analysis_json=excluded.analysis_json,
             source_digest=excluded.source_digest,model=excluded.model,as_of_date=excluded.as_of_date,
             current_price=excluded.current_price,bear_fair_value=excluded.bear_fair_value,
             base_fair_value=excluded.base_fair_value,bull_fair_value=excluded.bull_fair_value,
             base_upside=excluded.base_upside,bear_downside=excluded.bear_downside,
             reward_risk=excluded.reward_risk,expected_fair_value=excluded.expected_fair_value,
             expected_return=excluded.expected_return,earnings_gap=excluded.earnings_gap,
             expectations_gap=excluded.expectations_gap,odds_band=excluded.odds_band,
             odds_score=excluded.odds_score,odds_status=excluded.odds_status,
             valuation_confidence=excluded.valuation_confidence,thesis_confidence=excluded.thesis_confidence,
             updated_at=strftime('%Y-%m-%dT%H:%M:%fZ','now')""",
        (
            odds_id, sec.opportunity_id, sec.ticker, sec.company, sec.exchange, sec.currency,
            _rank_for_security(context), _json(data), digest, model, PROMPT_VERSION, data["as_of_date"],
            c["current_price"], c["bear_fair_value"], c["base_fair_value"], c["bull_fair_value"],
            c["base_upside"], c["bear_downside"], c["reward_risk"], c["expected_fair_value"],
            c["expected_return"], c["earnings_gap"], c["expectations_gap"], c["odds_band"],
            c["odds_score"], c["odds_status"], data["valuation_confidence"], data["thesis_confidence"],
        ),
    )


def _run_cost(con: sqlite3.Connection, run_id: str) -> dict[str, Any]:
    rows = con.execute(
        """SELECT status,input_tokens,cached_input_tokens,output_tokens,estimated_cost,actual_cost_if_available
           FROM ai_usage_ledger WHERE run_id=? ORDER BY request_started_at""", (run_id,)
    ).fetchall()
    attempted = [r for r in rows if r[0] in {"PENDING", "SUCCESS", "FAILED", "CANCELLED", "UNKNOWN_COST"}]
    return {
        "run_id": run_id, "attempted_calls": len(attempted),
        "successful_calls": sum(1 for r in rows if r[0] == "SUCCESS"),
        "failed_calls": sum(1 for r in rows if r[0] == "FAILED"),
        "input_tokens": sum(int(r[1] or 0) for r in rows if r[0] == "SUCCESS"),
        "cached_input_tokens": sum(int(r[2] or 0) for r in rows if r[0] == "SUCCESS"),
        "output_tokens": sum(int(r[3] or 0) for r in rows if r[0] == "SUCCESS"),
        "known_actual_cost_usd": round(sum(float(r[5] or 0) for r in rows if r[5] is not None), 8),
        "risk_cost_usd": round(sum(float(r[5] if r[5] is not None else r[4] or 0) for r in attempted), 8),
        "statuses": {status: sum(1 for r in rows if r[0] == status) for status in sorted({r[0] for r in rows})},
    }


def _report_rows(con: sqlite3.Connection) -> list[dict[str, Any]]:
    rows = []
    for row in con.execute(
        """SELECT o.opportunity_id,i.title,o.ticker,o.company,o.currency,o.best_expression_rank,
                  o.current_price,o.earnings_gap,o.bear_fair_value,o.base_fair_value,o.bull_fair_value,
                  o.base_upside,o.bear_downside,o.reward_risk,o.expected_return,o.expectations_gap,
                  o.odds_band,o.odds_score,o.odds_status,o.valuation_confidence,o.thesis_confidence,o.analysis_json
           FROM opportunity_odds o JOIN investment_opportunities i ON i.opportunity_id=o.opportunity_id
           WHERE o.prompt_version=? ORDER BY i.opportunity_score DESC,o.best_expression_rank,o.odds_score DESC""",
        (PROMPT_VERSION,),
    ).fetchall():
        data = json.loads(row[21])
        rows.append({
            "opportunity_id": row[0], "opportunity": row[1], "ticker": row[2], "company": row[3],
            "currency": row[4], "best_expression_rank": row[5], "current_price": row[6],
            "earnings_gap": row[7], "bear_fair_value": row[8], "base_fair_value": row[9],
            "bull_fair_value": row[10], "base_upside": row[11], "bear_downside": row[12],
            "reward_risk": row[13], "expected_return": row[14], "expectations_gap": row[15],
            "odds_band": row[16], "odds_score": row[17], "odds_status": row[18],
            "valuation_confidence": row[19], "thesis_confidence": row[20],
            "market_expectations": data["market_expectations"], "earnings_bridge": data["earnings_bridge"],
            "scenarios": data["scenarios"], "why_not_buy_now": data["why_not_buy_now"],
            "verdict": data["verdict"], "catalyst": data["catalyst"],
            "invalidation": data["invalidation"], "data_gaps": data["data_gaps"],
            "source_roots": data["source_roots"], "buy_gate_blockers": data["computed"]["buy_gate_blockers"],
        })
    return rows


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--db", default=DB_PATH)
    parser.add_argument("--output-dir", default=str(OUTPUT_DIR))
    args = parser.parse_args()
    init_db(args.db)
    con = sqlite3.connect(args.db, timeout=120)
    con.row_factory = sqlite3.Row
    cfg = gate_config()
    completed: list[dict[str, Any]] = []
    errors: list[dict[str, Any]] = []

    for sec in UNIVERSE:
        context = _opportunity_context(con, sec)
        digest = hashlib.sha256(_json(context).encode()).hexdigest()
        cached = con.execute(
            """SELECT analysis_json,model FROM opportunity_odds
               WHERE opportunity_id=? AND ticker=? AND source_digest=? AND prompt_version=?""",
            (sec.opportunity_id, sec.ticker, digest, PROMPT_VERSION),
        ).fetchone()
        if cached:
            completed.append({"ticker": sec.ticker, "status": "REUSED_EXISTING", "model": cached[1], "cost_usd": 0.0})
            continue
        try:
            result = call_json_web(
                "opportunity_odds_analysis", SYSTEM_PROMPT,
                _json({"as_of": "2026-08-31", "validated_opportunity": context, "gate_config": cfg}),
                ODDS_SCHEMA, schema_name="signalboard_opportunity_odds_v13", max_output_tokens=9000,
                timeout=300, max_retries=1, prompt_version=PROMPT_VERSION,
                entity_type="opportunity_security", entity_id=f"{sec.opportunity_id}:{sec.ticker}",
            )
            data = result.data
            data.update({"ticker": sec.ticker, "company": sec.company, "exchange": sec.exchange, "currency": sec.currency})
            _sanitize_sources(data, result.sources)
            data = normalize_analysis(data, context, cfg)
            _persist(con, sec, context, data, digest, result.model)
            record_usage(con, result, workload="opportunity_odds_analysis", object_type="opportunity_security", object_id=sec.ticker)
            con.commit()
            completed.append({
                "ticker": sec.ticker, "status": "ANALYZED", "model": result.model,
                "cost_usd": result.estimated_cost_usd, "odds_status": data["computed"]["odds_status"],
            })
        except AIGuardrailBlocked:
            con.rollback()
            raise
        except Exception as exc:
            con.rollback()
            errors.append({"ticker": sec.ticker, "error": f"{type(exc).__name__}: {exc}"})

    rows = _report_rows(con)
    run_id = os.getenv("AI_RUN_ID") or os.getenv("GITHUB_RUN_ID") or f"local-{os.getpid()}"
    cost = _run_cost(con, run_id)
    status = "COMPLETED" if len(rows) == len(UNIVERSE) and not errors else "PARTIAL"
    summary = {
        "status": status, "universe_size": len(UNIVERSE), "completed_rows": len(rows),
        "buy_candidates": [x["ticker"] for x in rows if x["odds_status"] == "BUY_CANDIDATE"],
        "good_company_bad_odds": [x["ticker"] for x in rows if x["odds_status"] == "GOOD_COMPANY_BAD_ODDS"],
        "good_odds_weak_evidence": [x["ticker"] for x in rows if x["odds_status"] == "GOOD_ODDS_WEAK_EVIDENCE"],
        "closest_to_buy": [x["ticker"] for x in sorted(rows, key=lambda x: x["odds_score"] or -1, reverse=True)[:3]],
    }
    con.execute(
        """INSERT OR REPLACE INTO opportunity_odds_runs
           (run_id,universe_json,config_json,summary_json,status,ai_calls,known_cost_usd,risk_cost_usd)
           VALUES (?,?,?,?,?,?,?,?)""",
        (run_id, _json([sec.__dict__ for sec in UNIVERSE]), _json(cfg), _json(summary), status,
         cost["attempted_calls"], cost["known_actual_cost_usd"], cost["risk_cost_usd"]),
    )
    con.commit()
    con.close()

    out = Path(args.output_dir)
    out.mkdir(parents=True, exist_ok=True)
    files = {
        "odds_results.json": rows,
        "top5_opportunity_odds.json": summary,
        "data_sources.json": [{"ticker": x["ticker"], "sources": x["source_roots"]} for x in rows],
        "cost_report.json": cost,
        "run_report.json": {"status": status, "completed": completed, "errors": errors, "summary": summary, "config": cfg, "cost": cost, "results": rows},
    }
    for name, payload in files.items():
        (out / name).write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({"status": status, "rows": len(rows), "errors": errors, "summary": summary, "cost": cost}, ensure_ascii=False))


if __name__ == "__main__":
    main()
