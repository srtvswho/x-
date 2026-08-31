#!/usr/bin/env python3
"""Bounded Investment Opportunity discovery and synthesis for SignalBoard v1.2.

The script analyzes ten deterministic candidates, discovers at most five more,
and promotes only chains that reach company earnings into the independent
``investment_opportunities`` layer.  Every model request goes through the
shared pre-call ledger and budget guardrails.
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
from signalboard.ai.router import call_json_web, record_usage
from signalboard.db import init_db


DB_PATH = "/workspace/data/signalboard_full.db"
OUTPUT_DIR = Path("outputs/opportunity_engine_v12")
CHAIN_PROMPT_VERSION = "logic-chain-v1.2.0"
DISCOVERY_PROMPT_VERSION = "opportunity-discovery-v1.2.0"
SYNTHESIS_PROMPT_VERSION = "opportunity-synthesis-v1.2.0"

SEEDED_CANDIDATES = [
    {
        "candidate_id": "candidate_esmt_legacy_dram",
        "title": "Legacy DRAM tightness → ESMT earnings leverage",
        "themes": ["Legacy Memory", "DRAM Pricing", "Supply Tightness", "Cost Pass-through", "Earnings", "BOM Cost"],
        "keywords": ["ESMT", "DDR3", "DDR2", "晶圆成本", "净利润", "ASP"],
        "hypothesis": "legacy DRAM tightness → ASP increase → wafer-cost pass-through → ESMT revenue/margin leverage",
    },
    {
        "candidate_id": "candidate_hbm_dram_crowdout",
        "title": "HBM wafer intensity → conventional DRAM supply squeeze",
        "themes": ["HBM", "DRAM", "Memory Shortage", "存储"],
        "keywords": ["30%的DRAM晶圆", "HBM需求", "长期协议", "出口价格", "wafer"],
        "hypothesis": "GPU/ASIC demand → HBM wafer intensity → conventional DRAM crowd-out → ASP → MU/SK Hynix earnings",
    },
    {
        "candidate_id": "candidate_socamm_lpddr",
        "title": "SOCAMM2 → data-center LPDDR demand pool",
        "themes": ["SOCAMM", "SOCAMM2", "LPDDR", "LPDDR5X", "数据中心内存", "AI 推理"],
        "keywords": ["SOCAMM", "LPDDR", "Vera Rubin", "Verano"],
        "hypothesis": "SOCAMM adoption → LPDDR demand → supplier mix/ASP → MU/SK Hynix earnings",
    },
    {
        "candidate_id": "candidate_cpo_laser",
        "title": "CPO / 1.6T ramp → CW laser and optical bottlenecks",
        "themes": ["CPO", "1.6T", "Optics", "光通信", "Laser Supply", "CW laser", "Optical I/O", "Pluggables"],
        "keywords": ["Sivers", "Ayar", "激光", "laser", "CPO", "FAU", "1.6T"],
        "hypothesis": "AI bandwidth → CPO/1.6T → CW laser/FAU bottleneck → orders → revenue/earnings",
    },
    {
        "candidate_id": "candidate_datacenter_physical_bottlenecks",
        "title": "AI data-center buildout → cooling / transformer / wiring constraints",
        "themes": ["电力", "液冷", "散热", "变压器", "变压器短缺", "布线", "Data Center Cooling"],
        "keywords": ["HPS", "AAON", "NVT", "MOD", "IESC", "MTRS", "JCI", "cooling", "transformer"],
        "hypothesis": "AI capex → data-center build → physical bottlenecks → backlog/pricing → company earnings",
    },
    {
        "candidate_id": "candidate_samsung_hbm4_broadcom",
        "title": "Samsung HBM4 lead → Broadcom ASIC execution advantage",
        "themes": ["HBM", "ASIC"],
        "keywords": ["Samsung", "三星", "HBM4", "Broadcom", "ASIC"],
        "hypothesis": "Samsung HBM4 execution → Broadcom ASIC supply match → shipments/performance → AVGO earnings",
    },
    {
        "candidate_id": "candidate_traditional_packaging_shortage",
        "title": "AI server growth → traditional packaging / wire-bonder shortage",
        "themes": ["Advanced Packaging", "先进封装", "半导体"],
        "keywords": ["wire bonder", "wire-bonder", "打线机", "KLIC", "ASMPT", "Amkor", "Powertech", "OSAT"],
        "hypothesis": "AI servers → OSAT bottleneck → wire-bonder shortage → equipment orders/backlog → earnings",
    },
    {
        "candidate_id": "candidate_cxmt_hbm3e",
        "title": "CXMT HBM3E ramp → China AI GPU bottleneck relief",
        "themes": ["HBM", "AI GPU", "China", "China Memory", "DRAM"],
        "keywords": ["CXMT", "长鑫", "HBM3E", "中国AI", "国产GPU"],
        "hypothesis": "CXMT capability → HBM3E qualification → domestic AI GPU supply → listed beneficiary if supported",
    },
    {
        "candidate_id": "candidate_gpu_server_price",
        "title": "AI server price increases → memory and GPU revenue pass-through",
        "themes": ["AI服务器", "GPU", "存储", "涨价", "AI 算力"],
        "keywords": ["价格将上涨", "GPU 价格", "Rubin NVL72", "memory configuration", "涨价"],
        "hypothesis": "AI demand/scarcity → server price increase → GPU/memory revenue and margin versus demand elasticity",
    },
    {
        "candidate_id": "candidate_memory_architecture",
        "title": "HBM limits → hierarchical memory / high-bandwidth NAND",
        "themes": ["HBM", "Memory architecture", "CXL", "AI inference", "AI agents", "Agent Memory"],
        "keywords": ["hierarchical", "hybrid memory", "HBF", "memory wall", "long-context", "长期memory"],
        "hypothesis": "long-context inference → HBM cost/capacity limit → tiered memory → DRAM/NAND/CXL value migration",
    },
]

MEDIA_IDS = [
    "3_2008639280902795266", "3_2094076428841291776", "3_2093052991620448256",
    "3_2092404709323845632", "3_2092782336635273216", "3_2034136443397017600",
    "3_2092500329921384448", "3_2092710847550537728", "3_2091953822445047808",
    "3_2093252422579945472",
]

CLAIM_IDS = [
    "claim_9284983de2954fd11a4c3bd3", "claim_062439d4b2895487e02937b6",
    "claim_09dd726c51fdb508a6984cd7", "claim_1854bf7262952de8005d0569",
    "claim_19d31fcbb2e5dc475b12abf4", "claim_89f485bcaa4da71b4f1e9389",
    "claim_90c4a91adf57907d654720f1", "claim_c9fbb96de104a7e30800eb25",
    "claim_0dba5938397cea7965d5dc8d", "claim_134a5af4d73768b672e1523d",
    "claim_54d28989cd802c853962ae7b", "claim_dbe7e2d1c2c1f6302555cbd0",
    "claim_f786b9b75a8d71a51071a2ea", "claim_f1f1fffa68a7e5fa8b462208",
    "claim_da591b56a1e8bfad24a571ed",
]


SOURCE_SCHEMA = {
    "type": "object", "additionalProperties": False,
    "properties": {
        "title": {"type": "string"}, "url": {"type": "string"},
        "publisher": {"type": "string"},
        "tier": {"type": "string", "enum": ["PRIMARY", "SECONDARY", "INDUSTRY", "SOCIAL", "UNKNOWN"]},
        "finding": {"type": "string"},
    },
    "required": ["title", "url", "publisher", "tier", "finding"],
}

COMPANY_SCHEMA = {
    "type": "object", "additionalProperties": False,
    "properties": {
        "name": {"type": "string"}, "ticker": {"type": "string"},
        "exposure": {"type": "string", "enum": ["POSITIVE", "NEGATIVE", "MIXED", "UNKNOWN"]},
        "mechanism": {"type": "string"},
    },
    "required": ["name", "ticker", "exposure", "mechanism"],
}

SCORES_SCHEMA = {
    "type": "object", "additionalProperties": False,
    "properties": {name: {"type": "number", "minimum": 0, "maximum": 100} for name in (
        "opportunity", "thesis_quality", "evidence_quality", "earnings_impact",
        "mispricing", "catalyst", "risk_reward"
    )},
    "required": ["opportunity", "thesis_quality", "evidence_quality", "earnings_impact", "mispricing", "catalyst", "risk_reward"],
}

VALUATION_SCHEMA = {
    "type": "object", "additionalProperties": False,
    "properties": {
        "status": {"type": "string", "enum": ["COMPLETE", "PARTIAL", "VALUATION_INCOMPLETE"]},
        "as_of": {"type": "string"}, "current_price": {"type": "string"},
        "market_cap": {"type": "string"}, "ttm_or_forward_pe": {"type": "string"},
        "revenue_growth": {"type": "string"}, "eps_growth": {"type": "string"},
        "consensus": {"type": "string"}, "historical_multiple": {"type": "string"},
        "peer_multiple": {"type": "string"},
        "expectations": {"type": "string", "enum": ["LOW_EXPECTATIONS", "FAIRLY_PRICED", "HIGH_EXPECTATIONS", "EXTREME_EXPECTATIONS", "UNKNOWN"]},
    },
    "required": ["status", "as_of", "current_price", "market_cap", "ttm_or_forward_pe", "revenue_growth", "eps_growth", "consensus", "historical_multiple", "peer_multiple", "expectations"],
}

CHAIN_SCHEMA = {
    "type": "object", "additionalProperties": False,
    "properties": {
        "title": {"type": "string"},
        "authors": {"type": "array", "maxItems": 8, "items": {"type": "string"}},
        "source_roots": {"type": "array", "maxItems": 12, "items": SOURCE_SCHEMA},
        "social_mention_count": {"type": "integer", "minimum": 0},
        "independent_evidence_count": {"type": "integer", "minimum": 0},
        "themes": {"type": "array", "items": {"type": "string"}},
        "driver": {"type": "string"}, "industry_change": {"type": "string"},
        "bottleneck": {"type": "string"},
        "causal_chain": {"type": "array", "items": {"type": "string"}},
        "companies": {"type": "array", "maxItems": 8, "items": COMPANY_SCHEMA},
        "primary_beneficiary": COMPANY_SCHEMA,
        "secondary_beneficiaries": {"type": "array", "maxItems": 5, "items": COMPANY_SCHEMA},
        "negative_exposure": {"type": "array", "maxItems": 5, "items": COMPANY_SCHEMA},
        "earnings_mechanism": {"type": "string"}, "time_horizon": {"type": "string"},
        "catalysts": {"type": "array", "maxItems": 6, "items": {"type": "string"}},
        "counter_case": {"type": "string"},
        "invalidation": {"type": "array", "maxItems": 6, "items": {"type": "string"}},
        "missing_evidence": {"type": "array", "maxItems": 6, "items": {"type": "string"}},
        "valuation_question": {"type": "string"}, "valuation": VALUATION_SCHEMA,
        "chain_completeness": {"type": "integer", "minimum": 0, "maximum": 6},
        "actionability": {"type": "string", "enum": ["THEME_ONLY", "WATCH", "RESEARCH", "BUY_CANDIDATE", "HEDGE_CANDIDATE", "AVOID", "REJECTED"]},
        "scores": SCORES_SCHEMA,
        "one_line_thesis": {"type": "string"}, "why_now": {"type": "string"},
        "ai_verdict": {"type": "string"}, "next_trigger": {"type": "string"},
        "rejection_reason": {"type": "string"},
    },
    "required": [
        "title", "authors", "source_roots", "social_mention_count", "independent_evidence_count",
        "themes", "driver", "industry_change", "bottleneck", "causal_chain", "companies",
        "primary_beneficiary", "secondary_beneficiaries", "negative_exposure", "earnings_mechanism",
        "time_horizon", "catalysts", "counter_case", "invalidation", "missing_evidence",
        "valuation_question", "valuation", "chain_completeness", "actionability", "scores",
        "one_line_thesis", "why_now", "ai_verdict", "next_trigger", "rejection_reason",
    ],
}

DISCOVERY_ITEM_SCHEMA = {
    "type": "object", "additionalProperties": False,
    "properties": {
        "candidate_id": {"type": "string"}, "title": {"type": "string"},
        "themes": {"type": "array", "items": {"type": "string"}},
        "keywords": {"type": "array", "items": {"type": "string"}},
        "hypothesis": {"type": "string"}, "why_novel": {"type": "string"},
    },
    "required": ["candidate_id", "title", "themes", "keywords", "hypothesis", "why_novel"],
}
DISCOVERY_SCHEMA = {
    "type": "object", "additionalProperties": False,
    "properties": {"candidates": {"type": "array", "maxItems": 5, "items": DISCOVERY_ITEM_SCHEMA}},
    "required": ["candidates"],
}

SYNTHESIS_SCHEMA = {
    "type": "object", "additionalProperties": False,
    "properties": {
        "opportunity_title": {"type": "string"},
        "direction": {"type": "string", "enum": ["LONG", "SHORT", "HEDGE", "MIXED", "UNRESOLVED"]},
        "actionability": {"type": "string", "enum": ["NOT_ACTIONABLE", "WATCH", "RESEARCH", "BUY_CANDIDATE", "HEDGE_CANDIDATE", "AVOID"]},
        "scores": SCORES_SCHEMA,
        "industry_change_real": {"type": "string"}, "key_evidence": {"type": "string"},
        "revenue_bridge": {"type": "string"}, "profit_bridge": {"type": "string"},
        "purest_beneficiary": COMPANY_SCHEMA,
        "cheaper_alternatives": {"type": "array", "items": COMPANY_SCHEMA},
        "largest_counter_case": {"type": "string"}, "price_in_assessment": {"type": "string"},
        "missing_data": {"type": "array", "items": {"type": "string"}},
        "next_research": {"type": "array", "items": {"type": "string"}},
        "next_trigger": {"type": "string"},
        "invalidation": {"type": "array", "items": {"type": "string"}},
        "market_expectations": {"type": "string"}, "mispricing_hypothesis": {"type": "string"},
        "one_line_thesis": {"type": "string"}, "why_now": {"type": "string"},
        "ai_verdict": {"type": "string"},
    },
    "required": [
        "opportunity_title", "direction", "actionability", "scores", "industry_change_real",
        "key_evidence", "revenue_bridge", "profit_bridge", "purest_beneficiary",
        "cheaper_alternatives", "largest_counter_case", "price_in_assessment", "missing_data",
        "next_research", "next_trigger", "invalidation", "market_expectations",
        "mispricing_hypothesis", "one_line_thesis", "why_now", "ai_verdict",
    ],
}

CHAIN_SYSTEM = """你是严谨的半导体与AI基础设施投资研究员。你必须验证而不是迎合候选逻辑。
使用 web search 时优先公司文件/IR/SEC/政府数据，其次 Reuters/Bloomberg/FT/WSJ，再次行业媒体。
社交账号重复转述同一根来源，只能算一个 independent evidence。作者观点不能自动成为事实。
逻辑必须明确走到 company revenue、margin/EPS/FCF；走不到就降为 THEME_ONLY 或 REJECTED。
估值数字必须有可靠且注明时点的来源；拿不到就写 VALUATION_INCOMPLETE，绝不编造。
Completeness: 0观点；1 Driver；2 Industry；3 Company；4 Revenue/Earnings；5 Valuation/Expectations；6 Catalyst+Invalidation。
Completeness 4 最高 WATCH；5 最高 RESEARCH；只有6且九项投资条件完整才可能 BUY_CANDIDATE。
Opportunity score 只用于排序，必须由子分数解释，不能因作者看多而加分。
输出中文，专有名词和 ticker 可保留英文。"""

DISCOVERY_SYSTEM = """你从真实数据库聚合中发现此前未人工指定的新投资逻辑链。不要围绕预设行业硬编。
候选必须至少有多个相关 Post、一个可追溯根来源、产业机制、公司映射和潜在 earnings mechanism。
排除仅有情绪、技术图形、价格目标或不能映射公司盈利的主题。最多返回5条；没有就返回空数组。"""

SYNTHESIS_SYSTEM = """你负责把已经验证过的逻辑链压缩成投资机会，而不是重复摘要。
必须回答产业变化真假、证据、收入和利润传导、最纯受益者、便宜替代、counter case、price-in、缺口、下一步、触发和证伪。
没有可靠 valuation/mispricing/catalyst/invalidation 时禁止 BUY_CANDIDATE。成本不是排序因子。输出中文。"""


def _stable_id(prefix: str, text: str) -> str:
    return prefix + hashlib.sha256(text.encode("utf-8")).hexdigest()[:24]


def _json(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True)


def _claim_rows(con: sqlite3.Connection) -> list[dict[str, Any]]:
    rows = con.execute(
        """SELECT c.claim_id,c.claim_text,c.claim_type,c.author_id,c.companies_json,c.themes_json,
                  c.time_horizon,c.source_post_id,c.source_media_id,c.confidence,c.verification_status,
                  rp.published_at,rp.raw_url
           FROM claims c LEFT JOIN raw_posts rp ON rp.post_id=c.source_post_id"""
    ).fetchall()
    return [{
        "claim_id": r[0], "claim_text": r[1], "claim_type": r[2], "author": r[3],
        "companies": json.loads(r[4] or "[]"), "themes": json.loads(r[5] or "[]"),
        "time_horizon": r[6], "post_id": r[7], "media_id": r[8], "confidence": r[9],
        "verification_status": r[10], "published_at": r[11], "post_url": r[12],
    } for r in rows]


def _candidate_evidence(con: sqlite3.Connection, spec: dict[str, Any], all_claims: list[dict[str, Any]]) -> dict[str, Any]:
    themes = {x.casefold() for x in spec.get("themes", [])}
    keywords = [x.casefold() for x in spec.get("keywords", [])]
    ranked: list[tuple[float, dict[str, Any]]] = []
    for claim in all_claims:
        text = claim["claim_text"].casefold()
        claim_themes = {str(x).casefold() for x in claim["themes"]}
        score = 6 * len(themes & claim_themes) + 3 * sum(key in text for key in keywords)
        score += 2 if claim["verification_status"] != "UNVERIFIED" else 0
        score += float(claim["confidence"] or 0)
        if score >= 3:
            ranked.append((score, claim))
    ranked.sort(key=lambda x: (-x[0], -(x[1]["confidence"] or 0), x[1]["claim_id"]))
    claims = [x[1] for x in ranked[:12]]
    post_ids = sorted({x["post_id"] for x in claims if x["post_id"]})
    authors = sorted({x["author"] for x in claims if x["author"]})

    verification: list[dict[str, Any]] = []
    claim_ids = [x["claim_id"] for x in claims]
    if claim_ids:
        placeholders = ",".join("?" for _ in claim_ids)
        for row in con.execute(
            f"""SELECT claim_id,status,rationale,corrected_claim,sources_json
                FROM claim_verifications WHERE claim_id IN ({placeholders})""", claim_ids
        ).fetchall():
            verification.append({"claim_id": row[0], "status": row[1], "rationale": row[2],
                                 "corrected_claim": row[3], "sources": json.loads(row[4] or "[]")[:2]})
        verification = verification[:6]

    source_roots: list[dict[str, Any]] = []
    if post_ids:
        placeholders = ",".join("?" for _ in post_ids)
        rows = con.execute(
            f"""SELECT DISTINCT u.underlying_source_id,u.canonical_url,u.publisher,u.title,u.source_class
                FROM source_memberships sm JOIN underlying_sources u
                  ON u.underlying_source_id=sm.underlying_source_id
                WHERE sm.mention_post_id IN ({placeholders})""", post_ids
        ).fetchall()
        tier_order = {"PRIMARY": 0, "SECONDARY": 1, "INDUSTRY": 2, "SOCIAL": 3, "UNKNOWN": 4}
        source_roots = [{"source_id": r[0], "url": r[1], "publisher": r[2], "title": r[3], "tier": r[4]} for r in rows]
        source_roots.sort(key=lambda item: (tier_order.get(item["tier"], 4), item["source_id"]))
        source_roots = source_roots[:12]

    media: list[dict[str, Any]] = []
    if post_ids:
        placeholders = ",".join("?" for _ in post_ids)
        rows = con.execute(
            f"""SELECT m.media_id,a.analysis_json FROM media_assets m JOIN media_analyses a ON a.media_id=m.media_id
                WHERE m.post_id IN ({placeholders}) LIMIT 8""", post_ids
        ).fetchall()
        media = [{"media_id": r[0], "analysis": json.loads(r[1])} for r in rows[:3]]

    return {
        "candidate": spec,
        "claims": claims,
        "claim_verifications": verification,
        "database_source_roots": source_roots,
        "media_analyses": media,
        "authors_observed": authors,
        "social_mention_count": len(post_ids),
        "independent_database_sources": len({x["source_id"] for x in source_roots if x["tier"] in {"PRIMARY", "SECONDARY", "INDUSTRY"}}),
    }


def _sanitize_sources(
    data: dict[str, Any],
    returned_sources: list[dict[str, Any]] | None,
    database_roots: list[dict[str, Any]] | None = None,
) -> None:
    allowed = {str(x.get("url") or "").rstrip("/") for x in (returned_sources or []) if x.get("url")}
    retained = [x for x in data.get("source_roots", []) if str(x.get("url") or "").rstrip("/") in allowed]
    seen = {str(x.get("url") or "").rstrip("/") for x in retained}
    for root in (database_roots or [])[:12]:
        url = str(root.get("url") or "").rstrip("/")
        if not url or url in seen:
            continue
        tier = root.get("tier") if root.get("tier") in {"PRIMARY", "SECONDARY", "INDUSTRY", "SOCIAL", "UNKNOWN"} else "UNKNOWN"
        retained.append({"title": root.get("title") or root.get("publisher") or url, "url": url,
                         "publisher": root.get("publisher") or "", "tier": tier,
                         "finding": "Existing deduplicated database source root."})
        seen.add(url)
    data["source_roots"] = retained[:12]
    independent = {x["url"].rstrip("/") for x in data["source_roots"] if x["tier"] in {"PRIMARY", "SECONDARY", "INDUSTRY"}}
    data["independent_evidence_count"] = len(independent)


def _enforce_actionability(data: dict[str, Any]) -> str:
    completeness = int(data.get("chain_completeness") or 0)
    action = data.get("actionability") or "THEME_ONLY"
    valuation_status = (data.get("valuation") or {}).get("status")
    if completeness < 4:
        action = "REJECTED" if action == "REJECTED" else "THEME_ONLY"
    elif completeness == 4 and action in {"RESEARCH", "BUY_CANDIDATE", "HEDGE_CANDIDATE"}:
        action = "WATCH"
    elif completeness == 5 and action in {"BUY_CANDIDATE", "HEDGE_CANDIDATE"}:
        action = "RESEARCH"
    elif action in {"BUY_CANDIDATE", "HEDGE_CANDIDATE"} and valuation_status != "COMPLETE":
        action = "RESEARCH"
    data["actionability"] = action
    return action


def normalize_score_scale(scores: dict[str, Any]) -> bool:
    """Normalize an obvious 0-10 model response onto the required 0-100 scale."""
    values = [float(value) for value in scores.values() if isinstance(value, (int, float))]
    if not values or max(values) > 10 or not any(not value.is_integer() for value in values):
        return False
    for key, value in list(scores.items()):
        if isinstance(value, (int, float)):
            scores[key] = round(min(100.0, max(0.0, float(value) * 10)), 1)
    return True


def _discovery_inventory(con: sqlite3.Connection) -> dict[str, Any]:
    themes = []
    for row in con.execute(
        """SELECT t.name,COUNT(DISTINCT ct.claim_id),COUNT(DISTINCT c.author_id),COUNT(DISTINCT c.source_post_id)
           FROM themes t LEFT JOIN claim_themes ct ON ct.theme_id=t.theme_id
           LEFT JOIN claims c ON c.claim_id=ct.claim_id WHERE t.parent_theme_id IS NULL
           GROUP BY t.theme_id ORDER BY COUNT(DISTINCT ct.claim_id) DESC LIMIT 60"""
    ).fetchall():
        examples = [x[0] for x in con.execute(
            """SELECT c.claim_text FROM claims c JOIN claim_themes ct ON ct.claim_id=c.claim_id
               JOIN themes t ON t.theme_id=ct.theme_id WHERE t.name=? ORDER BY c.confidence DESC LIMIT 3""", (row[0],)
        ).fetchall()]
        themes.append({"theme": row[0], "claims": row[1], "authors": row[2], "posts": row[3], "examples": examples})
    return {"theme_aggregates": themes, "excluded_seeded_titles": [x["title"] for x in SEEDED_CANDIDATES]}


def _persist_chain(con: sqlite3.Connection, candidate: dict[str, Any], data: dict[str, Any], model: str, discovery_type: str, digest: str) -> None:
    action = _enforce_actionability(data)
    status = "REJECTED" if action == "REJECTED" else ("THEME_ONLY" if action == "THEME_ONLY" else "ACTIVE")
    con.execute(
        """INSERT INTO logic_chain_analyses(candidate_id,title,analysis_json,source_digest,model,discovery_type,status)
           VALUES (?,?,?,?,?,?,?) ON CONFLICT(candidate_id) DO UPDATE SET
             title=excluded.title,analysis_json=excluded.analysis_json,source_digest=excluded.source_digest,
             model=excluded.model,discovery_type=excluded.discovery_type,status=excluded.status,
             updated_at=strftime('%Y-%m-%dT%H:%M:%fZ','now')""",
        (candidate["candidate_id"], data["title"], _json(data), digest, model, discovery_type, status),
    )


def _synthesize(con: sqlite3.Connection, candidate_id: str, chain: dict[str, Any], model_fallback: str) -> tuple[dict[str, Any], str, float]:
    result = call_json_web(
        "opportunity_synthesis", SYNTHESIS_SYSTEM,
        _json({"validated_logic_chain": chain, "as_of": "2026-08-31", "questions": "Answer all twelve synthesis questions."}),
        SYNTHESIS_SCHEMA, schema_name="signalboard_opportunity_synthesis", max_output_tokens=4500, timeout=240,
        max_retries=1,
        prompt_version=SYNTHESIS_PROMPT_VERSION, entity_type="opportunity_candidate", entity_id=candidate_id,
    )
    synthesis = result.data
    normalize_score_scale(synthesis["scores"])
    completeness = int(chain["chain_completeness"])
    action = synthesis["actionability"]
    if completeness == 4 and action in {"RESEARCH", "BUY_CANDIDATE", "HEDGE_CANDIDATE"}:
        action = "WATCH"
    if completeness == 5 and action in {"BUY_CANDIDATE", "HEDGE_CANDIDATE"}:
        action = "RESEARCH"
    if chain["valuation"]["status"] != "COMPLETE" and action in {"BUY_CANDIDATE", "HEDGE_CANDIDATE"}:
        action = "RESEARCH"
    synthesis["actionability"] = action
    opportunity_id = _stable_id("opp_", candidate_id)
    scores = synthesis["scores"]
    primary = synthesis["purest_beneficiary"]
    companies = chain["companies"]
    positive = [x for x in companies if x["exposure"] == "POSITIVE"]
    negative = [x for x in companies if x["exposure"] == "NEGATIVE"]
    now = "strftime('%Y-%m-%dT%H:%M:%fZ','now')"
    con.execute(
        f"""INSERT INTO investment_opportunities(
          opportunity_id,title,theme_ids_json,thesis_ids_json,companies_json,primary_company,direction,time_horizon,
          driver,industry_change,bottleneck,earnings_mechanism,valuation_question,market_expectations,
          mispricing_hypothesis,catalysts_json,risks_json,invalidation_conditions_json,missing_evidence_json,
          actionability,chain_completeness,opportunity_score,thesis_quality_score,evidence_quality_score,
          earnings_impact_score,mispricing_score,catalyst_score,risk_reward_score,one_line_thesis,why_now,
          ai_verdict,next_trigger,positive_exposure_json,negative_exposure_json,authors_json,source_roots_json,
          social_mention_count,independent_evidence_count,valuation_json,synthesis_json,source_candidate_id)
        VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
        ON CONFLICT(opportunity_id) DO UPDATE SET
          title=excluded.title,theme_ids_json=excluded.theme_ids_json,companies_json=excluded.companies_json,
          primary_company=excluded.primary_company,direction=excluded.direction,time_horizon=excluded.time_horizon,
          driver=excluded.driver,industry_change=excluded.industry_change,bottleneck=excluded.bottleneck,
          earnings_mechanism=excluded.earnings_mechanism,valuation_question=excluded.valuation_question,
          market_expectations=excluded.market_expectations,mispricing_hypothesis=excluded.mispricing_hypothesis,
          catalysts_json=excluded.catalysts_json,risks_json=excluded.risks_json,
          invalidation_conditions_json=excluded.invalidation_conditions_json,
          missing_evidence_json=excluded.missing_evidence_json,actionability=excluded.actionability,
          chain_completeness=excluded.chain_completeness,opportunity_score=excluded.opportunity_score,
          thesis_quality_score=excluded.thesis_quality_score,evidence_quality_score=excluded.evidence_quality_score,
          earnings_impact_score=excluded.earnings_impact_score,mispricing_score=excluded.mispricing_score,
          catalyst_score=excluded.catalyst_score,risk_reward_score=excluded.risk_reward_score,
          one_line_thesis=excluded.one_line_thesis,why_now=excluded.why_now,ai_verdict=excluded.ai_verdict,
          next_trigger=excluded.next_trigger,positive_exposure_json=excluded.positive_exposure_json,
          negative_exposure_json=excluded.negative_exposure_json,authors_json=excluded.authors_json,
          source_roots_json=excluded.source_roots_json,social_mention_count=excluded.social_mention_count,
          independent_evidence_count=excluded.independent_evidence_count,valuation_json=excluded.valuation_json,
          synthesis_json=excluded.synthesis_json,updated_at={now}""",
        (
            opportunity_id, synthesis["opportunity_title"], _json(chain["themes"]), "[]", _json(companies),
            primary["ticker"] or primary["name"], synthesis["direction"], chain["time_horizon"], chain["driver"],
            chain["industry_change"], chain["bottleneck"], chain["earnings_mechanism"], chain["valuation_question"],
            synthesis["market_expectations"], synthesis["mispricing_hypothesis"], _json(chain["catalysts"]),
            _json([chain["counter_case"]]), _json(synthesis["invalidation"]), _json(synthesis["missing_data"]),
            action, completeness, scores["opportunity"], scores["thesis_quality"], scores["evidence_quality"],
            scores["earnings_impact"], scores["mispricing"], scores["catalyst"], scores["risk_reward"],
            synthesis["one_line_thesis"], synthesis["why_now"], synthesis["ai_verdict"], synthesis["next_trigger"],
            _json(positive), _json(negative), _json(chain["authors"]), _json(chain["source_roots"]),
            chain["social_mention_count"], chain["independent_evidence_count"], _json(chain["valuation"]),
            _json(synthesis), candidate_id,
        ),
    )
    snapshot = {"chain": chain, "synthesis": synthesis}
    digest = hashlib.sha256(_json(snapshot).encode()).hexdigest()
    existing = con.execute(
        "SELECT version_number,source_digest FROM opportunity_versions WHERE opportunity_id=? ORDER BY version_number DESC LIMIT 1",
        (opportunity_id,),
    ).fetchone()
    if not existing or existing[1] != digest:
        version = 1 if not existing else int(existing[0]) + 1
        con.execute(
            "INSERT INTO opportunity_versions(opportunity_id,version_number,snapshot_json,source_digest,model) VALUES (?,?,?,?,?)",
            (opportunity_id, version, _json(snapshot), digest, result.model or model_fallback),
        )
    con.execute("DELETE FROM opportunity_evidence WHERE opportunity_id=?", (opportunity_id,))
    for claim_id in chain.get("evidence_claim_ids", []):
        con.execute(
            "INSERT OR IGNORE INTO opportunity_evidence(opportunity_id,evidence_type,evidence_id) VALUES (?,'claim',?)",
            (opportunity_id, claim_id),
        )
    record_usage(con, result, workload="opportunity_synthesis", object_type="opportunity", object_id=opportunity_id)
    con.commit()
    return synthesis, opportunity_id, result.estimated_cost_usd


def _cost_report(con: sqlite3.Connection) -> dict[str, Any]:
    run_id = os.getenv("AI_RUN_ID", "")
    rows = con.execute(
        """SELECT stage,status,COUNT(*),SUM(input_tokens),SUM(output_tokens),SUM(estimated_cost),
                  SUM(COALESCE(actual_cost_if_available,0)),
                  SUM(COALESCE(actual_cost_if_available,estimated_cost,0)),
                  SUM(CASE WHEN actual_cost_if_available IS NULL THEN 1 ELSE 0 END)
           FROM ai_usage_ledger WHERE run_id=? GROUP BY stage,status ORDER BY stage,status""", (run_id,)
    ).fetchall()
    by_stage: dict[str, dict[str, Any]] = {}
    for stage, status, calls, input_tokens, output_tokens, estimated, actual, risk, unknown_actual in rows:
        bucket = by_stage.setdefault(stage, {"calls": 0, "input_tokens": 0, "output_tokens": 0,
                                             "estimated_cost": 0.0, "known_actual_cost": 0.0,
                                             "risk_cost": 0.0, "unknown_actual_cost_calls": 0,
                                             "statuses": {}})
        bucket["statuses"][status] = calls
        if status in {"PENDING", "SUCCESS", "FAILED", "CANCELLED", "UNKNOWN_COST"}:
            bucket["calls"] += calls
            bucket["input_tokens"] += input_tokens or 0
            bucket["output_tokens"] += output_tokens or 0
            bucket["estimated_cost"] += estimated or 0
            bucket["known_actual_cost"] += actual or 0
            bucket["risk_cost"] += risk or 0
            bucket["unknown_actual_cost_calls"] += unknown_actual or 0
    total = {key: sum(float(x[key]) for x in by_stage.values()) for key in
             ("calls", "input_tokens", "output_tokens", "estimated_cost", "known_actual_cost", "risk_cost",
              "unknown_actual_cost_calls")}
    total["calls"] = int(total["calls"]); total["input_tokens"] = int(total["input_tokens"]); total["output_tokens"] = int(total["output_tokens"])
    total["unknown_actual_cost_calls"] = int(total["unknown_actual_cost_calls"])
    blocked = con.execute(
        "SELECT COUNT(*) FROM ai_usage_ledger WHERE run_id=? AND status IN ('BUDGET_BLOCKED','DAILY_BUDGET_EXCEEDED')",
        (run_id,),
    ).fetchone()[0]
    return {"run_id": run_id, "by_stage": by_stage, "total": total, "budget_blocked_calls": blocked}


def _write_supporting_outputs(con: sqlite3.Connection, out: Path) -> None:
    media = []
    placeholders = ",".join("?" for _ in MEDIA_IDS)
    for row in con.execute(
        f"""SELECT m.media_id,m.post_id,m.analysis_status,a.analysis_json FROM media_assets m
            LEFT JOIN media_analyses a ON a.media_id=m.media_id WHERE m.media_id IN ({placeholders})""", MEDIA_IDS
    ).fetchall():
        media.append({"media_id": row[0], "post_id": row[1], "status": row[2],
                      "analysis": json.loads(row[3]) if row[3] else None})
    claims = []
    placeholders = ",".join("?" for _ in CLAIM_IDS)
    for row in con.execute(
        f"""SELECT c.claim_id,c.claim_text,c.verification_status,cv.rationale,cv.corrected_claim,cv.sources_json
            FROM claims c LEFT JOIN claim_verifications cv ON cv.claim_id=c.claim_id
            WHERE c.claim_id IN ({placeholders})""", CLAIM_IDS
    ).fetchall():
        claims.append({"claim_id": row[0], "claim": row[1], "status": row[2], "rationale": row[3],
                       "corrected_claim": row[4], "sources": json.loads(row[5] or "[]")})
    (out / "media_analysis_summary.json").write_text(_json(media), encoding="utf-8")
    (out / "claim_verification_summary.json").write_text(_json(claims), encoding="utf-8")


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--db", default=DB_PATH)
    ap.add_argument("--output-dir", default=str(OUTPUT_DIR))
    ap.add_argument("--max-new", type=int, default=5)
    ap.add_argument("--max-synthesis", type=int, default=5)
    ap.add_argument("--skip-discovery", action="store_true")
    ap.add_argument("--candidate-ids", help="Comma-separated exact candidate IDs for a bounded corrective run")
    args = ap.parse_args()
    if not 0 <= args.max_new <= 5 or not 3 <= args.max_synthesis <= 5:
        raise SystemExit("--max-new must be 0..5 and --max-synthesis must be 3..5")
    init_db(args.db)
    con = sqlite3.connect(args.db, timeout=120)
    con.row_factory = sqlite3.Row
    out = Path(args.output_dir); out.mkdir(parents=True, exist_ok=True)
    requested_ids = [x.strip() for x in (args.candidate_ids or "").split(",") if x.strip()]
    all_claims = _claim_rows(con)
    analyzed: list[dict[str, Any]] = []
    stopped_reason = None

    discovered: list[dict[str, Any]] = []
    if args.skip_discovery:
        previous_report = out / "run_report.json"
        if previous_report.exists():
            discovered = json.loads(previous_report.read_text(encoding="utf-8")).get("discovered_candidates", [])
    else:
        try:
            discovery_result = call_json_web(
                "opportunity_discovery", DISCOVERY_SYSTEM, _json(_discovery_inventory(con)), DISCOVERY_SCHEMA,
                schema_name="signalboard_opportunity_discovery", max_output_tokens=2500, timeout=240,
                prompt_version=DISCOVERY_PROMPT_VERSION, entity_type="opportunity_discovery", entity_id="history-v12",
            )
            discovered = discovery_result.data["candidates"][:args.max_new]
            for item in discovered:
                item["candidate_id"] = _stable_id("candidate_discovered_", item["title"])
            record_usage(con, discovery_result, workload="opportunity_discovery", object_type="discovery_run", object_id="history-v12")
            con.commit()
        except AIGuardrailBlocked as exc:
            discovered = []
            stopped_reason = exc.reason
    candidates = [(x, "SEEDED") for x in SEEDED_CANDIDATES] + [(x, "DISCOVERED") for x in discovered]
    if requested_ids:
        requested = set(requested_ids)
        candidates = [item for item in candidates if item[0]["candidate_id"] in requested]
        found = {item[0]["candidate_id"] for item in candidates}
        missing = [candidate_id for candidate_id in requested_ids if candidate_id not in found]
        if missing:
            raise SystemExit(f"Unknown candidate IDs: {','.join(missing)}")

    for spec, discovery_type in candidates:
        if stopped_reason:
            break
        evidence = _candidate_evidence(con, spec, all_claims)
        digest = hashlib.sha256(_json(evidence).encode()).hexdigest()
        try:
            result = call_json_web(
                "logic_chain_analysis", CHAIN_SYSTEM,
                _json({"as_of": "2026-08-31", "evidence_bundle": evidence,
                       "instruction": "Validate every step, find independent sources and reject the chain when necessary."}),
                CHAIN_SCHEMA, schema_name="signalboard_logic_chain", max_output_tokens=6000, timeout=300,
                max_retries=1,
                prompt_version=CHAIN_PROMPT_VERSION, entity_type="logic_chain", entity_id=spec["candidate_id"],
            )
            data = result.data
            normalize_score_scale(data["scores"])
            _sanitize_sources(data, result.sources, evidence["database_source_roots"])
            data["social_mention_count"] = evidence["social_mention_count"]
            data["evidence_claim_ids"] = [x["claim_id"] for x in evidence["claims"]]
            data["database_social_mentions"] = evidence["social_mention_count"]
            data["database_independent_sources"] = evidence["independent_database_sources"]
            _persist_chain(con, spec, data, result.model, discovery_type, digest)
            record_usage(con, result, workload="logic_chain_analysis", object_type="logic_chain", object_id=spec["candidate_id"])
            con.commit()
            analyzed.append({"candidate_id": spec["candidate_id"], "discovery_type": discovery_type, "analysis": data,
                             "model": result.model, "cost_usd": result.estimated_cost_usd})
        except AIGuardrailBlocked as exc:
            con.rollback(); stopped_reason = exc.reason; break
        except Exception as exc:
            con.rollback()
            analyzed.append({"candidate_id": spec["candidate_id"], "discovery_type": discovery_type,
                             "error": f"{type(exc).__name__}: {exc}"})

    eligible = [x for x in analyzed if "analysis" in x and int(x["analysis"]["chain_completeness"]) >= 4
                and x["analysis"]["actionability"] not in {"REJECTED", "THEME_ONLY"}]
    eligible.sort(key=lambda x: (-float(x["analysis"]["scores"]["opportunity"]), x["candidate_id"]))
    syntheses = []
    for item in eligible[:args.max_synthesis]:
        if stopped_reason:
            break
        try:
            synthesis, opportunity_id, cost = _synthesize(con, item["candidate_id"], item["analysis"], item["model"])
            syntheses.append({"opportunity_id": opportunity_id, "candidate_id": item["candidate_id"],
                              "chain": item["analysis"], "synthesis": synthesis, "cost_usd": cost})
        except AIGuardrailBlocked as exc:
            con.rollback(); stopped_reason = exc.reason; break

    _write_supporting_outputs(con, out)
    cost = _cost_report(con)
    theme_calls = int((cost.get("by_stage", {}).get("theme") or {}).get("calls", 0))
    calls_planned = theme_calls + len(candidates) + min(args.max_synthesis, len(eligible)) + (0 if args.skip_discovery else 1)
    report = {
        "status": "BUDGET_STOPPED" if stopped_reason else "COMPLETED",
        "stop_reason": stopped_reason,
        "seeded_candidates": sum(1 for _, discovery_type in candidates if discovery_type == "SEEDED"),
        "discovered_candidates": discovered,
        "analyzed": analyzed, "synthesized_opportunities": syntheses,
        "research_count": sum(1 for x in analyzed if x.get("analysis", {}).get("actionability") == "RESEARCH"),
        "watch_count": sum(1 for x in analyzed if x.get("analysis", {}).get("actionability") == "WATCH"),
        "rejected_or_theme_only_count": sum(1 for x in analyzed if x.get("analysis", {}).get("actionability") in {"REJECTED", "THEME_ONLY"}),
        "calls_planned": calls_planned,
        "why_extra_calls_were_used": [
            {"candidate_id": x["candidate_id"], "title": x["title"], "reason": x.get("why_novel", "New database-grounded chain")}
            for x in discovered
        ],
        "cost_by_logic_chain": {x["candidate_id"]: x.get("cost_usd", 0.0) for x in analyzed},
        "cost_by_opportunity": {x["opportunity_id"]: x.get("cost_usd", 0.0) for x in syntheses},
        "cost": cost,
    }
    (out / "candidate_logic_chains.json").write_text(_json(analyzed), encoding="utf-8")
    (out / "top_opportunities.json").write_text(_json(syntheses), encoding="utf-8")
    (out / "cost_report.json").write_text(_json(cost), encoding="utf-8")
    (out / "run_report.json").write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    con.close()
    print(json.dumps({"status": report["status"], "analyzed": len(analyzed), "opportunities": len(syntheses),
                      "research": report["research_count"], "watch": report["watch_count"],
                      "rejected_or_theme_only": report["rejected_or_theme_only_count"], "cost": cost}, ensure_ascii=False))


if __name__ == "__main__":
    main()
