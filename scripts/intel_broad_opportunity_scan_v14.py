#!/usr/bin/env python3
"""SignalBoard v1.4 Broad Opportunity Scan.

The pipeline scans the complete local post index, discovers additional causal
chains from structured claims, maps public-equity beneficiaries, performs a
web-sourced Quick Odds screen, and spends Deep Odds budget only on the best
10–15 expressions.  Every paid request is routed through the shared fail-closed
ledger and is independently resumable.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import sqlite3
import sys
from collections import Counter
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from signalboard.ai.guardrails import AIGuardrailBlocked
from signalboard.ai.router import call_json, call_json_web, record_usage
from signalboard.db import init_db
from scripts.intel_opportunity_odds_v13 import (
    ODDS_SCHEMA,
    SYSTEM_PROMPT as ODDS_SYSTEM_PROMPT,
    _sanitize_sources as sanitize_deep_sources,
    gate_config,
    normalize_analysis,
)


DEFAULT_DB = "/workspace/data/signalboard_full.db"
OUTPUT_DIR = Path("outputs/broad_opportunity_scan_v14")
DISCOVERY_VERSION = "broad-discovery-v1.4.0"
QUICK_VERSION = "beneficiary-quick-odds-v1.4.0"
DEEP_VERSION = "broad-deep-odds-v1.4.0"
AS_OF_DATE = "2026-08-31"

NULLABLE_NUMBER = {"type": ["number", "null"]}
SOURCE_SCHEMA = {
    "type": "object", "additionalProperties": False,
    "properties": {
        "source_id": {"type": "string"}, "title": {"type": "string"},
        "url": {"type": "string"}, "publisher": {"type": "string"},
        "as_of_date": {"type": ["string", "null"]}, "finding": {"type": "string"},
    },
    "required": ["source_id", "title", "url", "publisher", "as_of_date", "finding"],
}

DISCOVERY_CHAIN_SCHEMA = {
    "type": "object", "additionalProperties": False,
    "properties": {
        "candidate_id": {"type": "string"}, "title": {"type": "string"},
        "theme": {"type": "string"}, "authors": {"type": "array", "maxItems": 8, "items": {"type": "string"}},
        "source_roots": {"type": "array", "maxItems": 10, "items": SOURCE_SCHEMA},
        "source_claim_ids": {"type": "array", "maxItems": 12, "items": {"type": "string"}},
        "social_mention_count": {"type": "integer", "minimum": 0},
        "independent_evidence_count": {"type": "integer", "minimum": 0},
        "driver": {"type": "string"}, "industry_change": {"type": "string"},
        "bottleneck": {"type": "string"},
        "companies": {
            "type": "array", "maxItems": 8,
            "items": {
                "type": "object", "additionalProperties": False,
                "properties": {
                    "company": {"type": "string"}, "ticker": {"type": "string"},
                    "mechanism": {"type": "string"},
                }, "required": ["company", "ticker", "mechanism"],
            },
        },
        "earnings_mechanism": {"type": "string"}, "time_horizon": {"type": "string"},
        "counter_case": {"type": "string"},
        "missing_evidence": {"type": "array", "maxItems": 6, "items": {"type": "string"}},
        "chain_completeness": {"type": "integer", "minimum": 0, "maximum": 6},
        "thesis_quality": {"type": "number", "minimum": 0, "maximum": 100},
        "evidence_quality": {"type": "number", "minimum": 0, "maximum": 100},
        "supported": {"type": "boolean"}, "rejection_reason": {"type": "string"},
    },
    "required": [
        "candidate_id", "title", "theme", "authors", "source_roots", "source_claim_ids",
        "social_mention_count", "independent_evidence_count", "driver", "industry_change",
        "bottleneck", "companies", "earnings_mechanism", "time_horizon", "counter_case",
        "missing_evidence", "chain_completeness", "thesis_quality", "evidence_quality",
        "supported", "rejection_reason",
    ],
}
DISCOVERY_SCHEMA = {
    "type": "object", "additionalProperties": False,
    "properties": {"chains": {"type": "array", "minItems": 4, "maxItems": 6, "items": DISCOVERY_CHAIN_SCHEMA}},
    "required": ["chains"],
}

EXPRESSION_TYPES = [
    "OBVIOUS_WINNER", "PURE_PLAY", "UNDERFOLLOWED", "CHEAPER_ALTERNATIVE", "HIGH_BETA",
    "PICKS_AND_SHOVELS", "UPSTREAM", "DOWNSTREAM", "SECOND_ORDER", "NEGATIVE_EXPOSURE",
]
EXPRESSION_SCHEMA = {
    "type": "object", "additionalProperties": False,
    "properties": {
        "ticker": {"type": "string"}, "company": {"type": "string"}, "market": {"type": "string"},
        "currency": {"type": "string"}, "accessibility": {"type": "string"},
        "listing_type": {"type": "string"}, "expression_type": {"type": "string", "enum": EXPRESSION_TYPES},
        "direction": {"type": "string", "enum": ["POSITIVE", "NEGATIVE", "MIXED"]},
        "mechanism": {"type": "string"}, "revenue_mechanism": {"type": "string"},
        "current_price": NULLABLE_NUMBER, "market_cap": NULLABLE_NUMBER,
        "forward_revenue_growth": NULLABLE_NUMBER, "forward_eps_growth": NULLABLE_NUMBER,
        "forward_pe": NULLABLE_NUMBER, "ev_ebitda": NULLABLE_NUMBER,
        "historical_multiple": {"type": "string"}, "peer_multiple": {"type": "string"},
        "expectation_level": {"type": "string", "enum": ["LOW", "MODERATE", "HIGH", "EXTREME", "UNKNOWN"]},
        "earnings_gap_estimate": NULLABLE_NUMBER,
        "valuation_level": {"type": "string", "enum": ["CHEAP", "REASONABLE", "EXPENSIVE", "VERY_EXPENSIVE", "UNKNOWN"]},
        "quick_odds": {"type": "string", "enum": ["ATTRACTIVE", "INTERESTING", "FAIR", "POOR", "UNKNOWN"]},
        "confidence": {"type": "string", "enum": ["LOW", "MEDIUM", "HIGH"]},
        "deep_research_required": {"type": "boolean"}, "why": {"type": "string"},
        "risks": {"type": "array", "maxItems": 6, "items": {"type": "string"}},
        "as_of_date": {"type": "string"}, "sources": {"type": "array", "maxItems": 8, "items": SOURCE_SCHEMA},
    },
    "required": [
        "ticker", "company", "market", "currency", "accessibility", "listing_type",
        "expression_type", "direction", "mechanism", "revenue_mechanism", "current_price",
        "market_cap", "forward_revenue_growth", "forward_eps_growth", "forward_pe", "ev_ebitda",
        "historical_multiple", "peer_multiple", "expectation_level", "earnings_gap_estimate",
        "valuation_level", "quick_odds", "confidence", "deep_research_required", "why",
        "risks", "as_of_date", "sources",
    ],
}
QUICK_SCHEMA = {
    "type": "object", "additionalProperties": False,
    "properties": {
        "coverage_gaps": {"type": "array", "maxItems": 8, "items": {"type": "string"}},
        "best_business_ticker": {"type": "string"}, "best_technology_ticker": {"type": "string"},
        "best_pure_play_ticker": {"type": "string"}, "best_odds_ticker": {"type": "string"},
        "best_us_ticker": {"type": "string"}, "best_local_ticker": {"type": "string"},
        "expressions": {"type": "array", "minItems": 2, "maxItems": 8, "items": EXPRESSION_SCHEMA},
    },
    "required": [
        "coverage_gaps", "best_business_ticker", "best_technology_ticker", "best_pure_play_ticker",
        "best_odds_ticker", "best_us_ticker", "best_local_ticker", "expressions",
    ],
}

DISCOVERY_SYSTEM = """你是 SignalBoard 的 Broad Opportunity Discovery 研究员。只根据输入数据库证据构建投资因果链，不使用作者知名度作为加分。必须区分社交共识和独立来源；同一底层来源不能重复计数。链条必须走到 Company → Revenue/Margin/EPS，否则 supported=false。不要硬编码热门主题，不要凑数量，不要重复已有链条。输出紧凑 JSON。"""

QUICK_SYSTEM = f"""你是全球股票受益者映射和 Quick Odds 负责人。必须使用 web search，数据截止 {AS_OF_DATE}。对输入 Thesis 穷尽式尝试 Obvious Winner、Pure Play、Underfollowed、Cheaper Alternative、High Beta、Picks & Shovels、Upstream、Downstream、Second-order、Negative Exposure；不存在写不进 expressions，不得编造。

每个股票必须是真实上市证券、有明确收入/利润机制，并至少保留一个真实来源。覆盖美国、台湾、A股、港股、日本、韩国等市场；标注交易市场、币种、ADR/Local 和普通国际零售投资者可交易性。Quick Odds 只做必要筛选，不生成目标价。获取同日价格、市值、forward growth、PE/EV EBITDA、历史/同业估值、市场预期和粗略 earnings gap。找不到可靠数据填 null/UNKNOWN。官方 IR、SEC/交易所/正式财报优先；不能依赖单一行情网站。

不要因为公司热门或业务好就给高赔率。Strong Thesis + Extreme Expectations 可以是 POOR。对周期股警惕 peak earnings。输出紧凑 JSON。"""


def jdump(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def digest(*parts: str) -> str:
    return hashlib.sha256("\n\x1f\n".join(parts).encode("utf-8")).hexdigest()


def db_connect(path: str) -> sqlite3.Connection:
    init_db(path)
    con = sqlite3.connect(path, timeout=30)
    con.row_factory = sqlite3.Row
    con.execute("PRAGMA foreign_keys=ON")
    con.execute("PRAGMA busy_timeout=30000")
    return con


def database_counts(con: sqlite3.Connection) -> dict[str, int]:
    out = {}
    for key, table in (("posts", "raw_posts"), ("media", "media_assets"), ("claims", "claims"), ("themes", "themes")):
        out[key] = int(con.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0])
    return out


def evidence_packets(con: sqlite3.Connection, batches: int = 5, per_batch: int = 52) -> list[list[dict[str, Any]]]:
    rows = con.execute(
        """SELECT c.claim_id,c.claim_text,c.claim_type,c.author_id,c.companies_json,c.confidence,
                  c.source_post_id,p.raw_url,p.published_at,
                  group_concat(DISTINCT t.name) AS themes
           FROM claims c
           LEFT JOIN raw_posts p ON p.post_id=c.source_post_id
           LEFT JOIN claim_themes ct ON ct.claim_id=c.claim_id
           LEFT JOIN themes t ON t.theme_id=ct.theme_id
           WHERE c.claim_type NOT IN ('POSITION','QUESTION')
           GROUP BY c.claim_id"""
    ).fetchall()
    scored = []
    for row in rows:
        d = dict(row)
        companies = json.loads(d.get("companies_json") or "[]")
        score = float(d.get("confidence") or 0) + min(len(companies), 3) * 0.18 + (0.25 if d.get("raw_url") else 0)
        score += 0.2 if d.get("themes") else 0
        d["companies"] = companies
        d.pop("companies_json", None)
        scored.append((score, d))
    scored.sort(key=lambda x: (-x[0], x[1]["claim_id"]))
    packets: list[list[dict[str, Any]]] = [[] for _ in range(batches)]
    for idx, (_, row) in enumerate(scored[: batches * per_batch]):
        packets[idx % batches].append(row)
    return packets


def existing_chains(con: sqlite3.Connection) -> list[dict[str, Any]]:
    out = []
    for row in con.execute("SELECT candidate_id,title,analysis_json,status FROM logic_chain_analyses ORDER BY candidate_id"):
        data = json.loads(row[2])
        data.setdefault("candidate_id", row[0])
        data.setdefault("title", row[1])
        data.setdefault("supported", row[3] == "ACTIVE")
        data.setdefault("rejection_reason", "")
        out.append(data)
    return out


def discover_chains(con: sqlite3.Connection, plan_only: bool) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    current = existing_chains(con)
    if plan_only:
        return current, []
    titles = [str(x.get("title") or "") for x in current]
    rejected: list[dict[str, Any]] = []
    for batch_no, packet in enumerate(evidence_packets(con), 1):
        user = jdump({
            "batch": batch_no,
            "all_database_counts": database_counts(con),
            "existing_chain_titles_to_avoid": titles[-50:],
            "evidence_claims": packet,
            "instruction": "Find 4–6 distinct investable causal chains. Prefer overlooked cross-theme and second-order mechanisms. Reject unsupported chains explicitly.",
        })
        try:
            result = call_json(
                "broad_candidate_discovery", DISCOVERY_SYSTEM, user, DISCOVERY_SCHEMA,
                schema_name="signalboard_broad_discovery_v14", max_output_tokens=7000,
                timeout=300, max_retries=0, prompt_version=DISCOVERY_VERSION,
                entity_type="claim_batch", entity_id=f"broad-batch-{batch_no}",
            )
            record_usage(con, result, workload="broad_candidate_discovery", object_type="claim_batch", object_id=str(batch_no))
            for raw in result.data["chains"]:
                raw["candidate_id"] = "broad_" + digest(raw["title"], raw["theme"])[:24]
                if raw["title"].casefold() in {x.casefold() for x in titles}:
                    raw["supported"] = False
                    raw["rejection_reason"] = "Duplicate chain title"
                if raw["supported"] and raw["chain_completeness"] >= 3 and raw["companies"]:
                    con.execute(
                        """INSERT INTO logic_chain_analyses(candidate_id,title,analysis_json,source_digest,model,discovery_type,status)
                           VALUES (?,?,?,?,?,'DISCOVERED','ACTIVE')
                           ON CONFLICT(candidate_id) DO UPDATE SET analysis_json=excluded.analysis_json,
                             source_digest=excluded.source_digest,model=excluded.model,status='ACTIVE',
                             updated_at=strftime('%Y-%m-%dT%H:%M:%fZ','now')""",
                        (raw["candidate_id"], raw["title"], jdump(raw), digest(user), result.model),
                    )
                    current.append(raw); titles.append(raw["title"])
                else:
                    rejected.append(raw)
            con.commit()
        except AIGuardrailBlocked:
            raise
        except Exception as exc:
            record_usage(con, None, workload="broad_candidate_discovery", object_type="claim_batch", object_id=str(batch_no), error=exc)
            rejected.append({"batch": batch_no, "rejection_reason": f"{type(exc).__name__}: {exc}"})
            con.commit()
    return existing_chains(con), rejected


def chain_companies(chain: dict[str, Any]) -> list[dict[str, Any]]:
    companies = chain.get("companies") or []
    if not companies and chain.get("primary_beneficiary"):
        companies = [chain["primary_beneficiary"], *(chain.get("secondary_beneficiaries") or [])]
    return [x for x in companies if isinstance(x, dict) and (x.get("ticker") or x.get("company") or x.get("name"))]


def ensure_opportunity(con: sqlite3.Connection, chain: dict[str, Any]) -> str | None:
    candidate_id = str(chain.get("candidate_id") or "")
    row = con.execute("SELECT opportunity_id FROM investment_opportunities WHERE source_candidate_id=?", (candidate_id,)).fetchone()
    if row:
        return str(row[0])
    companies = chain_companies(chain)
    completeness = int(chain.get("chain_completeness") or 0)
    if completeness < 3 or not companies:
        return None
    opportunity_id = "opp_" + digest(candidate_id)[:24]
    themes = chain.get("themes") or [chain.get("theme") or "Unclassified"]
    source_roots = chain.get("source_roots") or []
    thesis_quality = float(chain.get("thesis_quality") or (chain.get("scores") or {}).get("thesis_quality") or 55)
    evidence_quality = float(chain.get("evidence_quality") or (chain.get("scores") or {}).get("evidence_quality") or 50)
    title = str(chain.get("title") or candidate_id)
    primary = companies[0].get("ticker") or companies[0].get("company") or companies[0].get("name")
    columns = (
        "opportunity_id", "title", "theme_ids_json", "companies_json", "primary_company", "direction",
        "time_horizon", "driver", "industry_change", "bottleneck", "earnings_mechanism",
        "valuation_question", "market_expectations", "mispricing_hypothesis", "catalysts_json", "risks_json",
        "invalidation_conditions_json", "missing_evidence_json", "actionability", "chain_completeness",
        "opportunity_score", "thesis_quality_score", "evidence_quality_score", "earnings_impact_score",
        "mispricing_score", "catalyst_score", "risk_reward_score", "one_line_thesis", "why_now", "ai_verdict",
        "next_trigger", "positive_exposure_json", "negative_exposure_json", "authors_json", "source_roots_json",
        "social_mention_count", "independent_evidence_count", "valuation_json", "synthesis_json", "source_candidate_id",
    )
    values = (
        opportunity_id, title, jdump(themes), jdump(companies), primary, "LONG",
        chain.get("time_horizon") or "12–24m", chain.get("driver") or "",
        chain.get("industry_change") or "", chain.get("bottleneck") or "",
        chain.get("earnings_mechanism") or "", "What expectations are already priced?", "UNKNOWN",
        chain.get("counter_case") or "", "[]", jdump([chain.get("counter_case") or ""]), "[]",
        jdump(chain.get("missing_evidence") or []), "RESEARCH" if completeness >= 5 else "WATCH", completeness,
        round((thesis_quality + evidence_quality) / 2, 1), thesis_quality, evidence_quality,
        max(40.0, thesis_quality - 5), 45.0, 50.0, 50.0,
        chain.get("one_line_thesis") or f"{chain.get('driver','')} → {chain.get('earnings_mechanism','')}",
        chain.get("why_now") or "Broad historical evidence scan candidate.",
        "Broad scan candidate; odds not yet established.", "Complete beneficiary and expectations scan.",
        jdump(companies), "[]", jdump(chain.get("authors") or []), jdump(source_roots),
        int(chain.get("social_mention_count") or len(chain.get("source_claim_ids") or [])),
        int(chain.get("independent_evidence_count") or len(source_roots)), "{}", jdump(chain), candidate_id,
    )
    con.execute(
        f"INSERT INTO investment_opportunities({','.join(columns)}) VALUES ({','.join('?' for _ in columns)})",
        values,
    )
    con.commit()
    return opportunity_id


def allowed_urls(result_sources: list[dict[str, Any]] | None) -> set[str]:
    return {str(x.get("url") or "").rstrip("/") for x in (result_sources or []) if x.get("url")}


def coverage_confidence(expressions: list[dict[str, Any]]) -> str:
    types = {x["expression_type"] for x in expressions}
    if len(expressions) >= 6 and len(types) >= 4:
        return "HIGH"
    if len(expressions) >= 3 and len(types) >= 2:
        return "MEDIUM"
    return "LOW"


def quick_category(chain: dict[str, Any], expr: dict[str, Any]) -> str:
    strong = float(chain.get("thesis_quality") or (chain.get("scores") or {}).get("thesis_quality") or 50) >= 65
    valuation = expr["valuation_level"]
    if expr["confidence"] == "LOW" or valuation == "UNKNOWN":
        return "F_INSUFFICIENT_DATA"
    if strong and valuation == "CHEAP": return "A_STRONG_CHEAP"
    if strong and valuation == "REASONABLE": return "B_STRONG_FAIR"
    if strong: return "C_STRONG_EXPENSIVE"
    if valuation in {"CHEAP", "REASONABLE"}: return "D_WEAK_CHEAP"
    return "E_WEAK_EXPENSIVE"


def persist_quick_map(con: sqlite3.Connection, opportunity_id: str, chain: dict[str, Any], data: dict[str, Any], result: Any, prompt_digest: str) -> tuple[int, list[dict[str, Any]]]:
    allowed = allowed_urls(result.sources)
    retained: list[dict[str, Any]] = []
    rejected: list[dict[str, Any]] = []
    seen: set[tuple[str, str]] = set()
    for expr in data["expressions"]:
        expr["sources"] = [s for s in expr["sources"] if str(s.get("url") or "").rstrip("/") in allowed]
        ticker = str(expr["ticker"]).strip().upper()
        key = (ticker, expr["expression_type"])
        reason = ""
        if not ticker or ticker in {"NONE", "PRIVATE", "N/A"}: reason = "No public equity"
        elif key in seen: reason = "Duplicate expression"
        elif not expr["revenue_mechanism"].strip(): reason = "No earnings link"
        elif not expr["sources"]: reason = "No captured evidence root"
        seen.add(key)
        if reason:
            rejected.append({**expr, "rejection_reason": reason}); continue
        if expr["current_price"] is None or expr["current_price"] <= 0:
            expr["confidence"] = "LOW"; expr["quick_odds"] = "UNKNOWN"
        expr["category"] = quick_category(chain, expr)
        expression_id = "expr_" + digest(opportunity_id, ticker, expr["expression_type"])[:24]
        evidence = expr["sources"][0]
        con.execute(
            """INSERT INTO security_expressions(expression_id,opportunity_id,ticker,company,market,currency,
                 accessibility,listing_type,expression_type,direction,mechanism,revenue_mechanism,
                 evidence_root_json,risks_json,source_digest,status,rejection_reason)
               VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,'ACTIVE',NULL)
               ON CONFLICT(opportunity_id,ticker,expression_type) DO UPDATE SET
                 company=excluded.company,market=excluded.market,currency=excluded.currency,
                 accessibility=excluded.accessibility,listing_type=excluded.listing_type,direction=excluded.direction,
                 mechanism=excluded.mechanism,revenue_mechanism=excluded.revenue_mechanism,
                 evidence_root_json=excluded.evidence_root_json,risks_json=excluded.risks_json,
                 source_digest=excluded.source_digest,status='ACTIVE',rejection_reason=NULL,
                 updated_at=strftime('%Y-%m-%dT%H:%M:%fZ','now')""",
            (expression_id, opportunity_id, ticker, expr["company"], expr["market"], expr["currency"],
             expr["accessibility"], expr["listing_type"], expr["expression_type"], expr["direction"],
             expr["mechanism"], expr["revenue_mechanism"], jdump(evidence), jdump(expr["risks"]), prompt_digest),
        )
        # Resolve the canonical id if the uniqueness constraint matched an older row.
        expression_id = con.execute(
            "SELECT expression_id FROM security_expressions WHERE opportunity_id=? AND ticker=? AND expression_type=?",
            (opportunity_id, ticker, expr["expression_type"]),
        ).fetchone()[0]
        quick_id = "quick_" + digest(expression_id, QUICK_VERSION)[:24]
        con.execute(
            """INSERT INTO quick_odds(quick_odds_id,expression_id,current_price,market_cap,forward_revenue_growth,
                 forward_eps_growth,forward_pe,ev_ebitda,historical_multiple,peer_multiple,expectation_level,
                 earnings_gap_estimate,valuation_level,quick_odds,confidence,deep_research_required,category,
                 as_of_date,sources_json,analysis_json,source_digest,model,prompt_version)
               VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
               ON CONFLICT(expression_id) DO UPDATE SET current_price=excluded.current_price,
                 market_cap=excluded.market_cap,forward_revenue_growth=excluded.forward_revenue_growth,
                 forward_eps_growth=excluded.forward_eps_growth,forward_pe=excluded.forward_pe,
                 ev_ebitda=excluded.ev_ebitda,historical_multiple=excluded.historical_multiple,
                 peer_multiple=excluded.peer_multiple,expectation_level=excluded.expectation_level,
                 earnings_gap_estimate=excluded.earnings_gap_estimate,valuation_level=excluded.valuation_level,
                 quick_odds=excluded.quick_odds,confidence=excluded.confidence,
                 deep_research_required=excluded.deep_research_required,category=excluded.category,
                 as_of_date=excluded.as_of_date,sources_json=excluded.sources_json,
                 analysis_json=excluded.analysis_json,source_digest=excluded.source_digest,model=excluded.model,
                 prompt_version=excluded.prompt_version,updated_at=strftime('%Y-%m-%dT%H:%M:%fZ','now')""",
            (quick_id, expression_id, expr["current_price"], expr["market_cap"], expr["forward_revenue_growth"],
             expr["forward_eps_growth"], expr["forward_pe"], expr["ev_ebitda"], expr["historical_multiple"],
             expr["peer_multiple"], expr["expectation_level"], expr["earnings_gap_estimate"],
             expr["valuation_level"], expr["quick_odds"], expr["confidence"],
             int(expr["deep_research_required"]), expr["category"], expr["as_of_date"],
             jdump(expr["sources"]), jdump(expr), prompt_digest, result.model, QUICK_VERSION),
        )
        retained.append(expr)
    confidence = coverage_confidence(retained)
    value = lambda k: None if str(data[k]).upper() in {"NONE", "N/A", "UNKNOWN", ""} else data[k]
    con.execute(
        """INSERT INTO beneficiary_maps(opportunity_id,coverage_confidence,thesis_pricing_status,
             best_business_ticker,best_technology_ticker,best_pure_play_ticker,best_odds_ticker,best_us_ticker,
             best_local_ticker,analysis_json,source_digest,model,prompt_version)
           VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)
           ON CONFLICT(opportunity_id) DO UPDATE SET coverage_confidence=excluded.coverage_confidence,
             best_business_ticker=excluded.best_business_ticker,best_technology_ticker=excluded.best_technology_ticker,
             best_pure_play_ticker=excluded.best_pure_play_ticker,best_odds_ticker=excluded.best_odds_ticker,
             best_us_ticker=excluded.best_us_ticker,best_local_ticker=excluded.best_local_ticker,
             analysis_json=excluded.analysis_json,source_digest=excluded.source_digest,model=excluded.model,
             prompt_version=excluded.prompt_version,updated_at=strftime('%Y-%m-%dT%H:%M:%fZ','now')""",
        (opportunity_id, confidence, "NOT_EXHAUSTED", value("best_business_ticker"), value("best_technology_ticker"),
         value("best_pure_play_ticker"), value("best_odds_ticker"), value("best_us_ticker"),
         value("best_local_ticker"), jdump(data), prompt_digest, result.model, QUICK_VERSION),
    )
    con.commit()
    return len(retained), rejected


def run_quick_maps(con: sqlite3.Connection, chains: list[dict[str, Any]], plan_only: bool) -> list[dict[str, Any]]:
    rejected: list[dict[str, Any]] = []
    if plan_only: return rejected
    for chain in chains:
        opportunity_id = ensure_opportunity(con, chain)
        if not opportunity_id: continue
        already = con.execute("SELECT COUNT(*) FROM quick_odds q JOIN security_expressions e ON e.expression_id=q.expression_id WHERE e.opportunity_id=?", (opportunity_id,)).fetchone()[0]
        if already >= 2: continue
        user = jdump({
            "opportunity_id": opportunity_id, "chain": chain,
            "requirements": {
                "public_equities_only": True, "minimum_expressions_if_real": 2, "maximum_expressions": 8,
                "global_markets": True, "same_date_market_data": AS_OF_DATE,
                "best_business_may_differ_from_best_odds": True,
            },
        })
        try:
            result = call_json_web(
                "beneficiary_quick_odds", QUICK_SYSTEM, user, QUICK_SCHEMA,
                schema_name="signalboard_beneficiary_quick_v14", max_output_tokens=8500,
                timeout=360, max_retries=0, prompt_version=QUICK_VERSION,
                entity_type="opportunity", entity_id=opportunity_id,
            )
            record_usage(con, result, workload="beneficiary_quick_odds", object_type="opportunity", object_id=opportunity_id)
            _, bad = persist_quick_map(con, opportunity_id, chain, result.data, result, digest(user))
            rejected.extend({"opportunity_id": opportunity_id, **x} for x in bad)
        except AIGuardrailBlocked:
            raise
        except Exception as exc:
            record_usage(con, None, workload="beneficiary_quick_odds", object_type="opportunity", object_id=opportunity_id, error=exc)
            rejected.append({"opportunity_id": opportunity_id, "rejection_reason": f"{type(exc).__name__}: {exc}"})
            con.commit()
    return rejected


def deep_candidates(con: sqlite3.Connection, limit: int) -> list[sqlite3.Row]:
    return con.execute(
        """SELECT e.*,q.*,i.title,i.driver,i.industry_change,i.bottleneck,i.earnings_mechanism,
                  i.actionability,i.chain_completeness,i.thesis_quality_score,i.evidence_quality_score,
                  i.catalyst_score,i.source_candidate_id,l.analysis_json AS chain_json
           FROM security_expressions e JOIN quick_odds q ON q.expression_id=e.expression_id
           JOIN investment_opportunities i ON i.opportunity_id=e.opportunity_id
           JOIN logic_chain_analyses l ON l.candidate_id=i.source_candidate_id
           LEFT JOIN deep_odds d ON d.expression_id=e.expression_id
           WHERE e.status='ACTIVE' AND d.expression_id IS NULL AND e.direction!='NEGATIVE'
           ORDER BY
             CASE q.quick_odds WHEN 'ATTRACTIVE' THEN 5 WHEN 'INTERESTING' THEN 4 WHEN 'FAIR' THEN 3 WHEN 'UNKNOWN' THEN 2 ELSE 1 END DESC,
             CASE e.expression_type WHEN 'UNDERFOLLOWED' THEN 5 WHEN 'CHEAPER_ALTERNATIVE' THEN 4 WHEN 'PURE_PLAY' THEN 3 ELSE 2 END DESC,
             CASE q.confidence WHEN 'HIGH' THEN 3 WHEN 'MEDIUM' THEN 2 ELSE 1 END DESC,
             COALESCE(q.earnings_gap_estimate,-9) DESC,i.thesis_quality_score DESC
           LIMIT ?""", (limit,)
    ).fetchall()


def persist_deep(con: sqlite3.Connection, row: sqlite3.Row, data: dict[str, Any], result: Any, prompt_digest: str) -> None:
    c = data["computed"]
    deep_id = "deep_" + digest(row["expression_id"], DEEP_VERSION)[:24]
    con.execute(
        """INSERT INTO deep_odds(deep_odds_id,expression_id,analysis_json,odds_score,odds_band,odds_status,
             expectations_gap,earnings_gap,base_upside,bear_downside,reward_risk,valuation_confidence,
             thesis_confidence,as_of_date,source_digest,model,prompt_version)
           VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
           ON CONFLICT(expression_id) DO UPDATE SET analysis_json=excluded.analysis_json,odds_score=excluded.odds_score,
             odds_band=excluded.odds_band,odds_status=excluded.odds_status,expectations_gap=excluded.expectations_gap,
             earnings_gap=excluded.earnings_gap,base_upside=excluded.base_upside,bear_downside=excluded.bear_downside,
             reward_risk=excluded.reward_risk,valuation_confidence=excluded.valuation_confidence,
             thesis_confidence=excluded.thesis_confidence,as_of_date=excluded.as_of_date,
             source_digest=excluded.source_digest,model=excluded.model,prompt_version=excluded.prompt_version,
             updated_at=strftime('%Y-%m-%dT%H:%M:%fZ','now')""",
        (deep_id, row["expression_id"], jdump(data), c["odds_score"], c["odds_band"], c["odds_status"],
         c["expectations_gap"], c["earnings_gap"], c["base_upside"], c["bear_downside"], c["reward_risk"],
         data["valuation_confidence"], data["thesis_confidence"], data["as_of_date"], prompt_digest,
         result.model, DEEP_VERSION),
    )
    con.commit()


def run_deep(con: sqlite3.Connection, limit: int, plan_only: bool) -> list[dict[str, Any]]:
    errors = []
    if plan_only: return errors
    for row in deep_candidates(con, limit):
        chain = json.loads(row["chain_json"])
        quick = json.loads(row["analysis_json"])
        context = {
            "opportunity_id": row["opportunity_id"], "title": row["title"],
            "driver": row["driver"], "industry_change": row["industry_change"],
            "bottleneck": row["bottleneck"], "earnings_mechanism": row["earnings_mechanism"],
            "actionability": row["actionability"], "chain_completeness": row["chain_completeness"],
            "thesis_quality_score": row["thesis_quality_score"],
            "evidence_quality_score": row["evidence_quality_score"], "catalyst_score": row["catalyst_score"],
            "chain": chain, "quick_odds": quick,
            "security": {"ticker": row["ticker"], "company": row["company"], "exchange": row["market"], "currency": row["currency"]},
        }
        system = ODDS_SYSTEM_PROMPT + "\n这是 Broad Scan 入选的 Deep Odds。不得因为入选而放宽 BUY gate；Best Business 与 Best Odds 可不同。"
        user = jdump(context)
        try:
            result = call_json_web(
                "broad_deep_odds", system, user, ODDS_SCHEMA,
                schema_name="signalboard_broad_deep_odds_v14", max_output_tokens=9000,
                timeout=360, max_retries=0, prompt_version=DEEP_VERSION,
                entity_type="security_expression", entity_id=row["expression_id"],
            )
            record_usage(con, result, workload="broad_deep_odds", object_type="security_expression", object_id=row["expression_id"])
            sanitize_deep_sources(result.data, result.sources)
            normalized = normalize_analysis(result.data, context, gate_config())
            persist_deep(con, row, normalized, result, digest(user))
        except AIGuardrailBlocked:
            raise
        except Exception as exc:
            record_usage(con, None, workload="broad_deep_odds", object_type="security_expression", object_id=row["expression_id"], error=exc)
            errors.append({"expression_id": row["expression_id"], "ticker": row["ticker"], "error": f"{type(exc).__name__}: {exc}"})
            con.commit()
    return errors


def run_cost(con: sqlite3.Connection, run_id: str) -> dict[str, Any]:
    rows = con.execute(
        """SELECT status,input_tokens,cached_input_tokens,output_tokens,estimated_cost,actual_cost_if_available
           FROM ai_usage_ledger WHERE run_id=?""", (run_id,)
    ).fetchall()
    attempted_status = {"PENDING", "SUCCESS", "FAILED", "CANCELLED", "UNKNOWN_COST"}
    attempted = [r for r in rows if r[0] in attempted_status]
    return {
        "run_id": run_id, "attempted_calls": len(attempted),
        "successful_calls": sum(r[0] == "SUCCESS" for r in rows), "failed_calls": sum(r[0] == "FAILED" for r in rows),
        "input_tokens": sum(int(r[1] or 0) for r in rows if r[0] == "SUCCESS"),
        "cached_input_tokens": sum(int(r[2] or 0) for r in rows if r[0] == "SUCCESS"),
        "output_tokens": sum(int(r[3] or 0) for r in rows if r[0] == "SUCCESS"),
        "known_actual_cost_usd": round(sum(float(r[5] or 0) for r in rows if r[5] is not None), 8),
        "risk_cost_usd": round(sum(float(r[5] if r[5] is not None else r[4] or 0) for r in attempted), 8),
        "statuses": dict(Counter(r[0] for r in rows)),
    }


def update_pricing_status(con: sqlite3.Connection) -> None:
    for row in con.execute("SELECT opportunity_id,coverage_confidence FROM beneficiary_maps"):
        quick = con.execute(
            """SELECT q.quick_odds,q.valuation_level,q.confidence FROM quick_odds q JOIN security_expressions e
               ON e.expression_id=q.expression_id WHERE e.opportunity_id=? AND e.status='ACTIVE'""", (row[0],)
        ).fetchall()
        deep = con.execute(
            """SELECT d.odds_status FROM deep_odds d JOIN security_expressions e ON e.expression_id=d.expression_id
               WHERE e.opportunity_id=?""", (row[0],)
        ).fetchall()
        attractive = any(q[0] in {"ATTRACTIVE", "INTERESTING"} for q in quick) or any(d[0] in {"BUY_CANDIDATE", "RESEARCH"} for d in deep)
        valuation_ready = sum(q[1] != "UNKNOWN" and q[2] in {"MEDIUM", "HIGH"} for q in quick)
        if attractive: status = "ATTRACTIVE_REMAINING"
        elif row[1] == "HIGH" and len(quick) >= 6 and valuation_ready >= 4 and len(deep) >= 2: status = "THESIS_FULLY_PRICED"
        elif quick: status = "MIXED"
        else: status = "NOT_EXHAUSTED"
        con.execute("UPDATE beneficiary_maps SET thesis_pricing_status=? WHERE opportunity_id=?", (status, row[0]))
    con.commit()


def coverage_report(con: sqlite3.Connection) -> dict[str, Any]:
    counts = database_counts(con)
    scalar = lambda sql: int(con.execute(sql).fetchone()[0])
    counts.update({
        "candidate_logic_chains": scalar("SELECT COUNT(*) FROM logic_chain_analyses"),
        "verified_thesis": scalar("SELECT COUNT(*) FROM logic_chain_analyses WHERE status='ACTIVE'"),
        "company_mapped_opportunities": scalar("SELECT COUNT(*) FROM beneficiary_maps"),
        "security_expressions": scalar("SELECT COUNT(*) FROM security_expressions WHERE status='ACTIVE'"),
        "quick_odds_completed": scalar("SELECT COUNT(*) FROM quick_odds"),
        "attractive_quick_odds": scalar("SELECT COUNT(*) FROM quick_odds WHERE quick_odds IN ('ATTRACTIVE','INTERESTING')"),
        "deep_odds_completed": scalar("SELECT COUNT(*) FROM deep_odds"),
        "valuation_ready": scalar("SELECT COUNT(*) FROM deep_odds WHERE valuation_confidence IN ('MEDIUM','HIGH')"),
        "buy_candidates": scalar("SELECT COUNT(*) FROM deep_odds WHERE odds_status='BUY_CANDIDATE'"),
    })
    gates = [counts["candidate_logic_chains"] >= 30, counts["company_mapped_opportunities"] >= 20,
             counts["security_expressions"] >= 50, counts["quick_odds_completed"] >= 30,
             counts["deep_odds_completed"] >= 10, counts["valuation_ready"] >= 10]
    counts["coverage_confidence"] = "HIGH" if all(gates) else ("MEDIUM" if sum(gates) >= 4 else "LOW")
    return counts


def top_expressions(con: sqlite3.Connection, limit: int = 20) -> list[dict[str, Any]]:
    rows = con.execute(
        """SELECT e.ticker,e.company,e.market,e.currency,e.expression_type,e.mechanism,e.revenue_mechanism,
                  i.title AS theme,i.thesis_quality_score,i.evidence_quality_score,q.expectation_level,
                  q.valuation_level,q.earnings_gap_estimate,q.quick_odds,q.confidence,q.category,
                  d.odds_status,d.odds_score,d.earnings_gap,d.base_upside,d.bear_downside,d.reward_risk,
                  d.valuation_confidence,d.thesis_confidence
           FROM security_expressions e JOIN quick_odds q ON q.expression_id=e.expression_id
           JOIN investment_opportunities i ON i.opportunity_id=e.opportunity_id
           LEFT JOIN deep_odds d ON d.expression_id=e.expression_id
           WHERE e.status='ACTIVE'
           ORDER BY CASE d.odds_status WHEN 'BUY_CANDIDATE' THEN 9 WHEN 'RESEARCH' THEN 8 WHEN 'WATCH' THEN 7
                    WHEN 'GOOD_ODDS_WEAK_EVIDENCE' THEN 6 WHEN 'GOOD_COMPANY_BAD_ODDS' THEN 3 WHEN 'VALUATION_INCOMPLETE' THEN 2 ELSE 1 END DESC,
                    COALESCE(d.odds_score,CASE q.quick_odds WHEN 'ATTRACTIVE' THEN 80 WHEN 'INTERESTING' THEN 65 WHEN 'FAIR' THEN 45 WHEN 'POOR' THEN 20 ELSE 0 END) DESC,
                    i.thesis_quality_score DESC LIMIT ?""", (limit,)
    ).fetchall()
    return [dict(r) for r in rows]


def final_report(con: sqlite3.Connection, rejected_chains: list[dict[str, Any]], rejected_expressions: list[dict[str, Any]], deep_errors: list[dict[str, Any]]) -> dict[str, Any]:
    update_pricing_status(con)
    coverage = coverage_report(con)
    top20 = top_expressions(con)
    new_discoveries = [dict(r) for r in con.execute(
        """SELECT i.title,i.primary_company,i.thesis_quality_score,i.evidence_quality_score,b.best_odds_ticker,
                  b.coverage_confidence,b.analysis_json FROM investment_opportunities i JOIN beneficiary_maps b
                  ON b.opportunity_id=i.opportunity_id WHERE i.source_candidate_id LIKE 'broad_%'
                  ORDER BY i.thesis_quality_score+i.evidence_quality_score DESC LIMIT 5"""
    )]
    cheap = [dict(r) for r in con.execute(
        """SELECT i.title,e1.ticker popular,e2.ticker alternative,q1.quick_odds popular_odds,q2.quick_odds alternative_odds,
                  e2.revenue_mechanism why
           FROM investment_opportunities i JOIN security_expressions e1 ON e1.opportunity_id=i.opportunity_id
           JOIN quick_odds q1 ON q1.expression_id=e1.expression_id
           JOIN security_expressions e2 ON e2.opportunity_id=i.opportunity_id
           JOIN quick_odds q2 ON q2.expression_id=e2.expression_id
           WHERE e1.expression_type='OBVIOUS_WINNER' AND e2.expression_type IN ('CHEAPER_ALTERNATIVE','UNDERFOLLOWED')
             AND q1.quick_odds IN ('POOR','FAIR') AND q2.quick_odds IN ('ATTRACTIVE','INTERESTING') LIMIT 20"""
    )]
    fully_priced = [dict(r) for r in con.execute(
        """SELECT i.title,b.coverage_confidence,b.thesis_pricing_status,b.best_odds_ticker,
                  (SELECT COUNT(*) FROM security_expressions e WHERE e.opportunity_id=i.opportunity_id AND e.status='ACTIVE') securities_scanned
           FROM beneficiary_maps b JOIN investment_opportunities i ON i.opportunity_id=b.opportunity_id
           WHERE b.thesis_pricing_status='THESIS_FULLY_PRICED'"""
    )]
    near_buy = []
    for row in con.execute(
        """SELECT e.ticker,e.company,i.title,d.analysis_json,d.odds_score,d.odds_status,d.base_upside,d.bear_downside,d.reward_risk
           FROM deep_odds d JOIN security_expressions e ON e.expression_id=d.expression_id
           JOIN investment_opportunities i ON i.opportunity_id=e.opportunity_id
           WHERE d.odds_status!='BUY_CANDIDATE' ORDER BY d.odds_score DESC LIMIT 5"""
    ):
        item = dict(row); analysis = json.loads(item.pop("analysis_json")); item["missing_gates"] = analysis.get("computed", {}).get("buy_gate_blockers", []); near_buy.append(item)
    run_id = os.getenv("AI_RUN_ID") or os.getenv("GITHUB_RUN_ID") or "local"
    cost = run_cost(con, run_id)
    useful = coverage["attractive_quick_odds"] + sum(1 for x in top20 if x.get("odds_status") in {"BUY_CANDIDATE", "RESEARCH", "WATCH"})
    cost_efficiency = {
        "per_candidate_chain": round(cost["risk_cost_usd"] / max(coverage["candidate_logic_chains"], 1), 6),
        "per_company_opportunity": round(cost["risk_cost_usd"] / max(coverage["company_mapped_opportunities"], 1), 6),
        "per_security_scanned": round(cost["risk_cost_usd"] / max(coverage["security_expressions"], 1), 6),
        "per_quick_odds": round(cost["risk_cost_usd"] / max(coverage["quick_odds_completed"], 1), 6),
        "per_deep_odds": round(cost["risk_cost_usd"] / max(coverage["deep_odds_completed"], 1), 6),
        "per_useful_candidate": round(cost["risk_cost_usd"] / max(useful, 1), 6),
    }
    return {
        "status": "COMPLETED" if coverage["coverage_confidence"] == "HIGH" else "PARTIAL",
        "coverage": coverage, "top_20_expressions": top20, "best_new_discoveries": new_discoveries,
        "cheap_alternatives": cheap, "fully_priced_themes": fully_priced,
        "rejected": {"candidate_chains": rejected_chains, "security_expressions": rejected_expressions, "deep_errors": deep_errors},
        "buy_candidates": [x for x in top20 if x.get("odds_status") == "BUY_CANDIDATE"],
        "near_buy": near_buy, "cost": cost, "cost_efficiency": cost_efficiency,
        "as_of_date": AS_OF_DATE,
    }


def write_outputs(report: dict[str, Any]) -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    files = {
        "run_report.json": report,
        "coverage_report.json": report["coverage"],
        "top20_expressions.json": report["top_20_expressions"],
        "new_discoveries.json": report["best_new_discoveries"],
        "cheap_alternatives.json": report["cheap_alternatives"],
        "fully_priced_themes.json": report["fully_priced_themes"],
        "rejected.json": report["rejected"],
        "buy_near_buy.json": {"buy_candidates": report["buy_candidates"], "near_buy": report["near_buy"]},
        "cost_report.json": {"cost": report["cost"], "cost_efficiency": report["cost_efficiency"]},
    }
    for name, payload in files.items():
        (OUTPUT_DIR / name).write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def plan(con: sqlite3.Connection, deep_limit: int) -> dict[str, Any]:
    counts = database_counts(con)
    current = len(existing_chains(con))
    return {
        "mode": "ZERO_AI_PLAN", "database": counts, "existing_candidate_chains": current,
        "discovery_batches": 5, "expected_new_chains": "20–30",
        "expected_company_mapped_opportunities": "20–35", "expected_security_expressions": "50–100+",
        "quick_odds_calls": "one per company-mapped opportunity", "deep_odds_limit": deep_limit,
        "expected_total_calls": f"{5 + 20 + deep_limit}–{5 + 35 + deep_limit}",
        "hard_gates": {"run_budget_usd": 50, "daily_budget_usd": 75, "calls": 400, "expensive_jobs": False},
        "actual_api_calls": 0,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--db", default=os.getenv("SIGNALBOARD_DB", DEFAULT_DB))
    parser.add_argument("--plan-only", action="store_true")
    parser.add_argument("--deep-limit", type=int, default=int(os.getenv("BROAD_DEEP_LIMIT", "15")))
    args = parser.parse_args()
    if not 10 <= args.deep_limit <= 15:
        raise SystemExit("--deep-limit must be 10–15")
    con = db_connect(args.db)
    try:
        if args.plan_only:
            payload = plan(con, args.deep_limit)
            OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
            (OUTPUT_DIR / "dry_plan.json").write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
            print(json.dumps(payload, ensure_ascii=False, indent=2)); return
        chains, rejected_chains = discover_chains(con, False)
        rejected_expressions = run_quick_maps(con, chains, False)
        deep_errors = run_deep(con, args.deep_limit, False)
        report = final_report(con, rejected_chains, rejected_expressions, deep_errors)
        write_outputs(report)
        run_id = os.getenv("AI_RUN_ID") or os.getenv("GITHUB_RUN_ID") or "local"
        con.execute(
            """INSERT OR REPLACE INTO broad_opportunity_scan_runs(run_id,status,coverage_json,report_json,
                 ai_calls,known_cost_usd,risk_cost_usd,why_extra_calls_json) VALUES (?,?,?,?,?,?,?,'[]')""",
            (run_id, report["status"], jdump(report["coverage"]), jdump(report), report["cost"]["attempted_calls"],
             report["cost"]["known_actual_cost_usd"], report["cost"]["risk_cost_usd"]),
        )
        con.commit()
        print(json.dumps({"status": report["status"], "coverage": report["coverage"], "cost": report["cost"]}, ensure_ascii=False, indent=2))
    finally:
        con.close()


if __name__ == "__main__":
    main()
