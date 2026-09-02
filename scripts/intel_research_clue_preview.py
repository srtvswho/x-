#!/usr/bin/env python3
"""Build the Research Clue Desk v1.6 Preview from completed research artifacts.

This is intentionally a read-only, zero-AI synthesizer.  It never imports the
OpenAI client, never mutates the database, and never reads valuation/odds data.
"""

from __future__ import annotations

import argparse
import json
import re
import sqlite3
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_DB = ROOT / "data" / "signalboard.db"
DEFAULT_OUT = ROOT / "outputs" / "research_clue_desk_v16"
OPENAI_CALLS = 0


CLUE_SPECS = [
    {
        "clue_id": "clue_ymtc_nand_wfe",
        "candidate_id": "candidate_discovered_e5ea307a08d4330cb900aca3",
        "case_id": "case_a_ymtc_nand_china_wfe",
        "title": "YMTC扩产：China WFE机会与NAND供给风险",
        "theme": "China Memory / WFE",
        "thesis": "YMTC扩产若进入设备搬入与验收阶段，将增加中国WFE需求；但同一扩产也可能在中期提高NAND供给并压低行业价格。",
        "status": "STRENGTHENING",
        "priority": 1,
    },
    {
        "clue_id": "clue_abf_copos_cowop",
        "candidate_id": "candidate_discovered_52a2b5015a466246abb141d5",
        "case_id": "case_b_abf_copos_cowop_pcb",
        "title": "Feynman封装路线：ABF、CoPoS与CoWoP谁受益",
        "theme": "Advanced Packaging / PCB",
        "thesis": "Feynman对ABF并非确定利好：CoPoS若保留ABF则需求上行，CoWoP若移除传统载板则价值池可能转向高阶PCB、CCL与RDL。",
        "status": "BUILDING",
        "priority": 2,
    },
    {
        "clue_id": "clue_datacenter_physical",
        "candidate_id": "candidate_datacenter_physical_bottlenecks",
        "title": "AI数据中心的物理瓶颈正在从GPU外溢",
        "theme": "AI Data Center Infrastructure",
        "thesis": "AI数据中心建设约束正在从芯片扩散到冷却、变压器、配电与施工交付，部分供应商的积压订单和利润表已出现验证。",
        "status": "STRENGTHENING",
        "priority": 3,
    },
    {
        "clue_id": "clue_memory_architecture",
        "candidate_id": "candidate_memory_architecture",
        "title": "Memory Wall推动分层内存与新型互连",
        "theme": "Hierarchical Memory",
        "thesis": "算力增长长期快于内存带宽，正在推动HBM、分层内存和内存互连升级，但HBF等新架构尚未形成可验证的公司盈利链。",
        "status": "BUILDING",
        "priority": 4,
    },
    {
        "clue_id": "clue_hbm_dram_crowdout",
        "candidate_id": "candidate_hbm_dram_crowdout",
        "title": "HBM晶圆强度是否继续挤压传统DRAM",
        "theme": "HBM / DRAM Supply",
        "thesis": "HBM确实消耗更多DRAM晶圆资源，但原厂会根据每片晶圆回报动态排产，不能机械推导传统DRAM将持续短缺。",
        "status": "WEAKENING",
        "priority": 5,
    },
    {
        "clue_id": "clue_legacy_dram",
        "candidate_id": "candidate_esmt_legacy_dram",
        "title": "Legacy DRAM紧缺已开始进入ESMT利润表",
        "theme": "Legacy DRAM",
        "thesis": "大厂资源转向HBM与服务器DRAM后，DDR2/DDR3供给收缩已推高ESMT收入和毛利率，但成本转嫁和高盈利持续性仍需验证。",
        "status": "STRENGTHENING",
        "priority": 6,
    },
    {
        "clue_id": "clue_cpo_cw_laser",
        "candidate_id": "candidate_cpo_laser",
        "title": "CPO与1.6T放量是否形成CW Laser瓶颈",
        "theme": "Optics / CPO",
        "thesis": "CPO和1.6T升级提高CW Laser需求的方向成立，但可插拔项目、CPO供货和Sivers公司订单目前仍被市场叙事混为一谈。",
        "status": "BUILDING",
        "priority": 7,
    },
    {
        "clue_id": "clue_socamm_lpddr",
        "candidate_id": "candidate_socamm_lpddr",
        "title": "SOCAMM2正在打开数据中心LPDDR需求池",
        "theme": "SOCAMM / LPDDR",
        "thesis": "SOCAMM2可能把LPDDR带入特定AI服务器平台，但供应商份额、单位用量和对既有产品的替代关系仍不清楚。",
        "status": "BUILDING",
        "priority": 8,
    },
    {
        "clue_id": "clue_cxl_interconnect",
        "candidate_id": "candidate_discovered_6d52ae3ca2765521c8d08cdf",
        "title": "推理瓶颈转向内存：CXL与内存互连的真实进度",
        "theme": "CXL / Memory Interconnect",
        "thesis": "推理扩张提高了内存容量、带宽和互连的重要性，但广义AI连接收入不能直接等同为CXL已经成为核心瓶颈。",
        "status": "BUILDING",
        "priority": 9,
    },
    {
        "clue_id": "clue_gpu_server_price",
        "candidate_id": "candidate_gpu_server_price",
        "title": "AI服务器涨价：内存成本转嫁还是新增利润池",
        "theme": "AI Server Economics",
        "thesis": "AI服务器涨价证明内存成本正在向系统价格传导，但尚不能判断新增价格最终留在GPU、内存还是整机厂的利润表。",
        "status": "NEW",
        "priority": 10,
    },
    {
        "clue_id": "clue_traditional_packaging",
        "candidate_id": "candidate_traditional_packaging_shortage",
        "title": "传统封装与打线机短缺：热门说法尚未成立",
        "theme": "Packaging Equipment",
        "thesis": "现有证据支持AI相关先进封装设备需求，却不足以证明传统wire-bonder已经短缺，两个设备市场不能相互替代举证。",
        "status": "CONTRADICTED",
        "priority": 11,
    },
    {
        "clue_id": "clue_cxmt_hbm3e",
        "candidate_id": "candidate_cxmt_hbm3e",
        "title": "CXMT HBM3E能否缓解中国AI GPU瓶颈",
        "theme": "China HBM",
        "thesis": "CXMT的DRAM扩张是真实研究方向，但HBM3E认证、国产GPU导入和量产收入均未获独立验证。",
        "status": "CONTRADICTED",
        "priority": 12,
    },
    {
        "clue_id": "clue_samsung_hbm4_broadcom",
        "candidate_id": "candidate_samsung_hbm4_broadcom",
        "title": "Samsung HBM4领先能否传导至Broadcom ASIC",
        "theme": "HBM4 / Custom ASIC",
        "thesis": "Samsung HBM4进展不能直接推出Broadcom ASIC执行优势，份额、认证、供货量与客户平台绑定仍缺独立证据。",
        "status": "CONTRADICTED",
        "priority": 13,
    },
]


# Deterministic terms used only to connect a research clue back to raw source
# posts. These deliberately favor precision over recall: the complete corpus
# remains available in /posts/, while a clue page should not claim that a
# generic adjacent-theme post is direct support for that clue.
CLUE_SOURCE_TERMS = {
    "clue_ymtc_nand_wfe": ["ymtc", "nand", "flash memory", "star market", "100k wpm"],
    "clue_abf_copos_cowop": ["feynman", "abf", "copos", "cowop", "substrate", "glass substrates", "ibiden", "innolux", "pcb", "ccl"],
    "clue_datacenter_physical": ["data center", "datacenter", "cooling", "chiller", "liquid cooling", "power delivery", "transformer", "wiring", "water"],
    "clue_memory_architecture": ["memory", "hbm", "dram", "cxl", "bandwidth", "context", "inference", "3d dram", "hbf"],
    "clue_hbm_dram_crowdout": ["hbm", "dram", "wafer input", "memory trio", "ddr4", "ddr5"],
    "clue_legacy_dram": ["legacy memory", "legacy dram", "ddr2", "ddr3", "esmt", "psmc"],
    "clue_cpo_cw_laser": ["cpo", "1.6t", "cw laser", "laser", "sive", "sivers", "pluggable", "fau", "foci", "foundry allocation"],
    "clue_socamm_lpddr": ["socamm", "lpddr", "data center lpddr", "dedicated to lpddr"],
    "clue_cxl_interconnect": ["cxl", "memory interconnect", "100 tb/s", "6.4tb/s", "hbm5", "3d dram"],
    "clue_gpu_server_price": ["server", "rack", "memory configurations", "rubin", "nvl72", "$8 million", "17%"],
    "clue_traditional_packaging": ["traditional packaging", "wire bonder", "wire-bonder", "bonder", "packaging equipment", "emib"],
    "clue_cxmt_hbm3e": ["cxmt", "hbm3e", "beijing fab", "china is still importing hbm"],
    "clue_samsung_hbm4_broadcom": ["samsung", "hbm4", "broadcom", "custom asic", "16 gbps"],
}


def _json(value: Any, default: Any) -> Any:
    if value is None:
        return default
    if isinstance(value, (dict, list)):
        return value
    try:
        return json.loads(value)
    except (TypeError, json.JSONDecodeError):
        return default


def _list(value: Any) -> list[Any]:
    parsed = _json(value, value)
    if parsed is None:
        return []
    return parsed if isinstance(parsed, list) else [parsed]


def _text(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, str):
        return value.strip()
    return str(value).strip()


def _first(*values: Any) -> str:
    for value in values:
        if isinstance(value, list):
            for item in value:
                result = _text(item.get("finding") if isinstance(item, dict) else item)
                if result:
                    return result
        else:
            result = _text(value)
            if result:
                return result
    return ""


def _items(*values: Any, limit: int = 6) -> list[str]:
    result: list[str] = []
    seen: set[str] = set()
    for value in values:
        for item in _list(value):
            if isinstance(item, dict):
                text = _first(item.get("finding"), item.get("mechanism"), item.get("view"), item.get("name"), item.get("title"))
            else:
                text = _text(item)
            key = re.sub(r"\s+", " ", text).lower()
            if text and key not in seen:
                seen.add(key)
                result.append(text)
            if len(result) >= limit:
                return result
    return result


def display_author(value: str | None) -> str:
    name = _text(value)
    for prefix in ("ctx_tw_", "tw_"):
        if name.startswith(prefix):
            name = name[len(prefix):]
    return name or "Unknown"


def clean_date(value: str | None) -> str:
    return _text(value)[:10]


def sentence(value: str, limit: int = 230) -> str:
    value = re.sub(r"\s+", " ", _text(value))
    if len(value) <= limit:
        return value
    cut = value[:limit]
    for marker in ("。", "；", ";", "."):
        pos = cut.rfind(marker)
        if pos > limit * 0.55:
            return cut[: pos + 1]
    return cut.rstrip() + "…"


def research_language(value: Any) -> Any:
    """Remove obsolete opportunity/odds labels from user-facing Preview text."""
    if isinstance(value, dict):
        return {key: research_language(item) for key, item in value.items()}
    if isinstance(value, list):
        return [research_language(item) for item in value]
    if not isinstance(value, str):
        return value
    replacements = {
        "BUY_CANDIDATE": "可投资结论",
        "NOT_ACTIONABLE": "尚不可行动",
        "THEME_ONLY": "主题线索",
        "Odds Ranking": "失效的旧排序",
        "odds ranking": "失效的旧排序",
    }
    for old, new in replacements.items():
        value = value.replace(old, new)
    return value


def open_readonly(path: Path) -> sqlite3.Connection:
    con = sqlite3.connect(f"file:{path.resolve()}?mode=ro", uri=True)
    con.row_factory = sqlite3.Row
    return con


def load_analysis(con: sqlite3.Connection, candidate_id: str) -> dict[str, Any]:
    row = con.execute(
        "SELECT title,analysis_json,status,updated_at FROM logic_chain_analyses WHERE candidate_id=?",
        (candidate_id,),
    ).fetchone()
    if not row:
        raise RuntimeError(f"missing completed logic-chain analysis: {candidate_id}")
    analysis = _json(row["analysis_json"], {})
    analysis["_candidate_title"] = row["title"]
    analysis["_candidate_status"] = row["status"]
    analysis["_updated_at"] = row["updated_at"]
    return analysis


def load_case(con: sqlite3.Connection, case_id: str | None) -> dict[str, Any]:
    if not case_id:
        return {}
    row = con.execute(
        "SELECT title,analysis_json,updated_at FROM research_case_analyses WHERE case_id=?",
        (case_id,),
    ).fetchone()
    if not row:
        raise RuntimeError(f"missing completed research case: {case_id}")
    case = _json(row["analysis_json"], {})
    case["_case_title"] = row["title"]
    case["_updated_at"] = row["updated_at"]
    return case


def load_opportunity(con: sqlite3.Connection, candidate_id: str) -> dict[str, Any]:
    row = con.execute(
        "SELECT * FROM investment_opportunities WHERE source_candidate_id=? ORDER BY updated_at DESC LIMIT 1",
        (candidate_id,),
    ).fetchone()
    if not row:
        return {}
    data = dict(row)
    for key in (
        "theme_ids_json", "thesis_ids_json", "companies_json", "catalysts_json", "risks_json",
        "invalidation_conditions_json", "missing_evidence_json", "positive_exposure_json",
        "negative_exposure_json", "authors_json", "source_roots_json", "synthesis_json",
    ):
        data[key.removesuffix("_json")] = _json(data.get(key), [] if key != "synthesis_json" else {})
    return data


def source_roots(analysis: dict[str, Any], opportunity: dict[str, Any]) -> list[dict[str, Any]]:
    roots = analysis.get("source_roots") or opportunity.get("source_roots") or []
    output: list[dict[str, Any]] = []
    seen: set[str] = set()
    for root in roots:
        if not isinstance(root, dict):
            root = {"title": _text(root)}
        url = _text(root.get("url"))
        title = _text(root.get("title")) or _text(root.get("publisher")) or url or "Untitled evidence"
        key = (url.rstrip("/").lower() if url else title.lower())
        if key in seen:
            continue
        seen.add(key)
        tier = _text(root.get("tier") or root.get("source_tier") or root.get("primary_or_secondary")).upper()
        if "PRIMARY" in tier or tier in {"一级", "COMPANY", "REGULATORY"}:
            layer = "PRIMARY_EVIDENCE"
        elif "AUTHOR" in tier or "SOCIAL" in tier:
            layer = "AUTHOR_INTERPRETATION"
        else:
            layer = "SECONDARY_EVIDENCE"
        output.append({
            "title": title,
            "url": url,
            "publisher": _text(root.get("publisher")),
            "layer": layer,
            "finding": sentence(_text(root.get("finding")), 300),
        })
    return output[:12]


def claim_rows(con: sqlite3.Connection, claim_ids: list[str]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for claim_id in claim_ids:
        row = con.execute(
            """SELECT c.*,rp.source_id AS post_author,rp.published_at,rp.raw_text,rp.raw_url
               FROM claims c LEFT JOIN raw_posts rp ON rp.post_id=c.source_post_id
               WHERE c.claim_id=?""",
            (claim_id,),
        ).fetchone()
        if not row:
            continue
        item = dict(row)
        item["companies"] = _json(item.get("companies_json"), [])
        item["themes"] = _json(item.get("themes_json"), [])
        rows.append(item)
    return rows


def media_item(con: sqlite3.Connection, media_id: str | None) -> dict[str, Any] | None:
    if not media_id:
        return None
    row = con.execute(
        """SELECT ma.media_id,ma.source_url,ma.storage_url,ma.media_type,ma.width,ma.height,
                  an.analysis_json
           FROM media_assets ma LEFT JOIN media_analyses an ON an.media_id=ma.media_id
           WHERE ma.media_id=? ORDER BY an.created_at DESC LIMIT 1""",
        (media_id,),
    ).fetchone()
    if not row:
        return None
    analysis = _json(row["analysis_json"], {})
    return {
        "media_id": row["media_id"],
        "thumbnail_url": row["storage_url"] or row["source_url"],
        "media_type": row["media_type"],
        "width": row["width"],
        "height": row["height"],
        "summary": sentence(_text(analysis.get("summary")), 320),
        "important_numbers": _items(analysis.get("metrics"), analysis.get("important_text"), limit=5),
        "detected_source": _text(analysis.get("source_detected")),
    }


def quoted_posts(con: sqlite3.Connection, post_id: str | None) -> list[dict[str, Any]]:
    if not post_id:
        return []
    rows = con.execute(
        """SELECT pr.reference_type,pr.target_url,rp.post_id,rp.source_id,rp.published_at,
                  rp.raw_text,rp.raw_url
           FROM post_references pr LEFT JOIN raw_posts rp ON rp.post_id=pr.target_post_id
           WHERE pr.source_post_id=? ORDER BY rp.published_at LIMIT 3""",
        (post_id,),
    ).fetchall()
    return [
        {
            "reference_type": row["reference_type"],
            "author": display_author(row["source_id"]),
            "date": clean_date(row["published_at"]),
            "text": sentence(_text(row["raw_text"]), 260),
            "url": row["raw_url"] or row["target_url"] or "",
        }
        for row in rows
    ]


def classify_event(group: dict[str, Any], index: int, total: int) -> tuple[str, str, str]:
    text = " ".join(group["claims"]).lower()
    claim_types = {x.upper() for x in group["claim_types"]}
    verification = {x.upper() for x in group["verification"]}
    if index == 0:
        return "THESIS_ORIGIN", "首次形成可追踪的研究线", "这是起点，不代表结论已经成立。"
    risk_words = ("风险", "不足", "未验证", "无法确认", "延迟", "放缓", "下降", "替代", "短缺未", "不支持")
    contradiction_words = ("错误", "否定", "不一致", "contradict", "不能证明", "并非", "未获独立验证")
    if any(word in text for word in contradiction_words) or "REFUTED" in verification:
        return "CONTRADICTION", "关键前提受到反证或证据约束", "需要降低置信度，并把作者说法与已验证事实分开。"
    if any(word in text for word in risk_words):
        return "NEW_RISK", "出现新的反向约束或不确定性", "这缩窄了原 Thesis 的成立条件。"
    if group["media_ids"]:
        return "NEW_EVIDENCE", "新增图片、图表或公司材料", "Media 是证据节点，仍需核对来源与口径。"
    if group["companies"]:
        return "NEW_COMPANY", "研究线延伸到具体公司", "公司映射已出现，但不等于可买入。"
    if index == total - 1:
        return "THESIS_UPDATE", "最新信息更新了当前判断", "应以本节点后的 Thesis 作为当前版本。"
    if "FACT" in claim_types:
        return "NEW_EVIDENCE", "新增事实或数据支持", "事实层增强，但其独立来源仍需去重。"
    return "THESIS_EXPANSION", "作者扩展了原有逻辑", "属于 Thesis 扩展，需继续寻找独立证据。"


def build_timeline(con: sqlite3.Connection, claims: list[dict[str, Any]]) -> tuple[list[dict[str, Any]], int]:
    grouped: dict[tuple[str, str, str], dict[str, Any]] = {}
    for claim in claims:
        date = clean_date(claim.get("published_at") or claim.get("point_in_time") or claim.get("created_at"))
        post_id = _text(claim.get("source_post_id"))
        author = display_author(claim.get("post_author") or claim.get("author_id"))
        key = (date, post_id or claim["claim_id"], author)
        group = grouped.setdefault(key, {
            "date": date or "Undated", "post_id": post_id, "author": author,
            "post_url": _text(claim.get("raw_url")), "post_text": sentence(_text(claim.get("raw_text")), 360),
            "claims": [], "claim_types": [], "verification": [], "companies": [], "media_ids": [],
        })
        group["claims"].append(_text(claim.get("claim_text")))
        group["claim_types"].append(_text(claim.get("claim_type")))
        group["verification"].append(_text(claim.get("verification_status")))
        group["companies"].extend(_list(claim.get("companies")))
        if claim.get("source_media_id"):
            group["media_ids"].append(claim["source_media_id"])

    groups = sorted(grouped.values(), key=lambda x: (x["date"] == "Undated", x["date"], x["post_id"]))
    selected = groups
    if len(groups) > 7:
        must = {0, len(groups) - 1}
        must.update(i for i, g in enumerate(groups) if g["media_ids"])
        must.update(i for i, g in enumerate(groups) if any(w in " ".join(g["claims"]) for w in ("风险", "未验证", "不支持", "下降", "替代")))
        for i in range(1, len(groups) - 1):
            if len(must) >= 7:
                break
            must.add(i)
        selected = [groups[i] for i in sorted(must)[:7]]

    events: list[dict[str, Any]] = []
    for index, group in enumerate(selected):
        event_type, changed, interpretation = classify_event(group, index, len(selected))
        media = [media_item(con, media_id) for media_id in dict.fromkeys(group["media_ids"])]
        events.append({
            "date": group["date"],
            "author": group["author"],
            "event_type": event_type,
            "post": group["post_text"],
            "post_url": group["post_url"],
            "claims": [sentence(x, 330) for x in group["claims"][:3]],
            "what_changed": changed,
            "ai_interpretation": interpretation,
            "quoted_posts": quoted_posts(con, group["post_id"]),
            "media": [x for x in media if x],
        })
    return events, max(0, len(groups) - len(selected))


def author_evolution(claims: list[dict[str, Any]]) -> list[dict[str, Any]]:
    by_author: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for claim in claims:
        author = display_author(claim.get("post_author") or claim.get("author_id"))
        by_author[author].append(claim)
    rows: list[dict[str, Any]] = []
    for author, items in by_author.items():
        items.sort(key=lambda x: _text(x.get("published_at") or x.get("point_in_time") or x.get("created_at")))
        confidences = [float(x["confidence"]) for x in items if isinstance(x.get("confidence"), (int, float))]
        avg = sum(confidences) / len(confidences) if confidences else 0.5
        rows.append({
            "author": author,
            "initial_view": sentence(_text(items[0].get("claim_text")), 300),
            "current_view": sentence(_text(items[-1].get("claim_text")), 300),
            "difference": "观点得到后续证据扩展" if len(items) > 1 else "当前仅有一个有效节点",
            "current_confidence": "HIGH" if avg >= 0.78 else "MEDIUM" if avg >= 0.5 else "LOW",
            "first_seen": clean_date(items[0].get("published_at") or items[0].get("point_in_time")),
            "last_updated": clean_date(items[-1].get("published_at") or items[-1].get("point_in_time")),
            "claim_count": len(items),
        })
    rows.sort(key=lambda x: (not re.match(r"^[A-Za-z0-9_]+$", x["author"]), -x["claim_count"], x["author"]))
    return rows[:6]


def company_rows(analysis: dict[str, Any], case: dict[str, Any], opportunity: dict[str, Any]) -> list[dict[str, str]]:
    raw = analysis.get("companies") or opportunity.get("companies") or []
    rows: list[dict[str, str]] = []
    seen: set[str] = set()
    for item in raw:
        if isinstance(item, str):
            item = {"name": item}
        name = _text(item.get("name") or item.get("company") or item.get("ticker"))
        ticker = _text(item.get("ticker"))
        key = (ticker or name).upper()
        if not key or key in seen:
            continue
        seen.add(key)
        rows.append({
            "name": name or ticker,
            "ticker": ticker,
            "exposure": _text(item.get("exposure") or item.get("direction") or "WATCH"),
            "mechanism": sentence(_text(item.get("mechanism")), 280),
        })
    if not rows:
        for text in _items(case.get("beneficiaries"), limit=4):
            rows.append({"name": text, "ticker": "", "exposure": "CONDITIONAL", "mechanism": text})
    return rows[:8]


def confidence_label(status: str, independent_count: int, roots: list[dict[str, Any]]) -> str:
    if status == "CONTRADICTED":
        return "LOW"
    primary = sum(root["layer"] == "PRIMARY_EVIDENCE" for root in roots)
    if independent_count >= 4 and primary:
        return "HIGH"
    if independent_count >= 2 or len(roots) >= 3:
        return "MEDIUM"
    return "LOW"


def build_clue(con: sqlite3.Connection, spec: dict[str, Any]) -> dict[str, Any]:
    analysis = load_analysis(con, spec["candidate_id"])
    case = load_case(con, spec.get("case_id"))
    opportunity = load_opportunity(con, spec["candidate_id"])
    claim_ids = list(dict.fromkeys(_list(analysis.get("evidence_claim_ids"))))
    claims = claim_rows(con, claim_ids)
    timeline, repeats = build_timeline(con, claims)
    roots = source_roots(analysis, opportunity)
    companies = company_rows(analysis, case, opportunity)
    authors = [x["author"] for x in author_evolution(claims)]
    for view in _list(case.get("author_views")):
        if isinstance(view, dict):
            author = display_author(view.get("author"))
            if author and author not in authors:
                authors.append(author)
    authors = authors[:6]
    post_ids = {row.get("source_post_id") for row in claims if row.get("source_post_id")}
    independent_count = int(
        analysis.get("independent_evidence_count")
        or analysis.get("database_independent_sources")
        or opportunity.get("independent_evidence_count")
        or len(roots)
    )
    social_count = int(
        analysis.get("social_mention_count")
        or analysis.get("database_social_mentions")
        or opportunity.get("social_mention_count")
        or len(post_ids)
    )
    thesis = _first(spec.get("thesis"), case.get("ai_assessment"), analysis.get("ai_verdict"), analysis.get("why"), opportunity.get("one_line_thesis"), analysis.get("industry_change"))
    why_matters = _first(analysis.get("earnings_mechanism"), opportunity.get("earnings_mechanism"), analysis.get("industry_change"), analysis.get("driver"))
    causal_chain = _items(case.get("logic_chain"), analysis.get("causal_chain"), opportunity.get("causal_chain"), limit=6)
    counter_case = _items(case.get("counter_case"), case.get("contradictions"), analysis.get("counter_case"), analysis.get("risks"), opportunity.get("risks"), limit=6)
    unknowns = _items(case.get("unknowns"), analysis.get("missing_data"), analysis.get("missing_evidence"), opportunity.get("missing_evidence"), limit=6)
    second_order = _items(case.get("second_order_effects"), analysis.get("second_order_effects"), limit=5)
    research_next = _items(case.get("unknowns"), case.get("valuation_questions"), analysis.get("missing_data"), analysis.get("missing_evidence"), analysis.get("invalidation"), opportunity.get("missing_evidence"), limit=6)
    if not research_next:
        research_next = ["找到一级来源确认核心 Claim", "确认公司收入与利润的直接传导机制"]
    first_seen = min((e["date"] for e in timeline if e["date"] != "Undated"), default=clean_date(case.get("_updated_at") or analysis.get("_updated_at")))
    last_updated = max((e["date"] for e in timeline if e["date"] != "Undated"), default=clean_date(case.get("_updated_at") or analysis.get("_updated_at")))
    latest_change = timeline[-1]["what_changed"] if timeline else "完成既有研究结果整理"
    media_count = sum(len(event["media"]) for event in timeline)
    completeness_flags = {
        "SOURCE": bool(roots or claims),
        "TIMELINE": len(timeline) >= 3,
        "THESIS": bool(thesis),
        "EVIDENCE": bool(roots or media_count),
        "COUNTER_CASE": bool(counter_case),
        "COMPANY_MAPPING": bool(companies),
    }
    completeness = sum(completeness_flags.values())
    recommendation_reasons = []
    if independent_count >= 3:
        recommendation_reasons.append(f"{independent_count}个独立证据根")
    if len(authors) >= 2:
        recommendation_reasons.append("多位作者共同推进")
    if media_count:
        recommendation_reasons.append("包含可审计Media Evidence")
    if spec["status"] == "CONTRADICTED":
        recommendation_reasons.append("热门叙事的关键前提未获验证")
    if spec["status"] in {"STRENGTHENING", "WEAKENING"}:
        recommendation_reasons.append("Thesis强度发生实质变化")
    if not recommendation_reasons:
        recommendation_reasons.append("新逻辑链值得继续验证")

    primary_findings = [root["finding"] for root in roots if root["layer"] == "PRIMARY_EVIDENCE" and root["finding"]]
    verified = _items(case.get("verified_evidence"), analysis.get("verified_evidence"), primary_findings, limit=4)
    what_looks_right = verified or _items(analysis.get("driver"), analysis.get("industry_change"), limit=3)
    ai_view = {
        "what_looks_right": what_looks_right,
        "what_may_be_wrong": counter_case[:4],
        "what_is_still_unknown": unknowns[:4],
        "second_order_effects": second_order,
        "what_to_research_next": research_next,
    }
    positive = [x for x in companies if x["exposure"].upper() in {"POSITIVE", "BENEFICIARY"}]
    negative = [x for x in companies if x["exposure"].upper() in {"NEGATIVE", "RISK"}]
    if not negative:
        negative = [{"name": x, "ticker": "", "exposure": "NEGATIVE", "mechanism": x} for x in _items(case.get("negative_exposure"), analysis.get("negative_exposure"), limit=4)]

    return research_language({
        "clue_id": spec["clue_id"],
        "priority": spec["priority"],
        "title": spec["title"],
        "theme": spec["theme"],
        "source_terms": CLUE_SOURCE_TERMS[spec["clue_id"]],
        "status": spec["status"],
        "current_state": "VALID THESIS" if spec["status"] not in {"CONTRADICTED", "NEW"} else "INVALID / UNPROVEN THESIS" if spec["status"] == "CONTRADICTED" else "INTERESTING CLUE",
        "first_seen": first_seen,
        "last_updated": last_updated,
        "authors": authors,
        "one_line_thesis": sentence(thesis, 300),
        "why_this_matters": sentence(why_matters, 420),
        "what_changed": latest_change,
        "short_logic_chain": causal_chain[:4],
        "full_logic_chain": causal_chain,
        "recommendation_reasons": recommendation_reasons[:3],
        "confidence": confidence_label(spec["status"], independent_count, roots),
        "social_mentions": social_count,
        "independent_evidence_roots": independent_count,
        "evidence_roots": roots,
        "timeline": timeline,
        "collapsed_repeat_count": repeats,
        "timeline_completeness": "COMPLETE" if len(timeline) >= 4 and bool(roots) else "PARTIAL",
        "author_evolution": author_evolution(claims),
        "where_they_agree": _items(analysis.get("agreement"), case.get("verified_evidence"), analysis.get("driver"), limit=3),
        "where_they_disagree": _items(analysis.get("disagreement"), case.get("contradictions"), analysis.get("counter_case"), limit=3),
        "related_companies": companies,
        "positive_exposure": positive[:5],
        "negative_exposure": negative[:5],
        "no_clear_public_equity_expression": not bool(companies),
        "ai_initial_view": sentence(_first(case.get("ai_assessment"), analysis.get("ai_verdict"), thesis), 380),
        "ai_research_view": ai_view,
        "what_to_research_next": research_next,
        "clue_completeness": {"completed": completeness, "total": 6, "layers": completeness_flags},
        "media_evidence_count": media_count,
        "source_candidate_id": spec["candidate_id"],
        "source_case_id": spec.get("case_id"),
        "analysis_source": "existing completed Golden / Opportunity / Media artifacts",
        "additional_openai_calls": 0,
    })


def build(db_path: Path) -> dict[str, Any]:
    con = open_readonly(db_path)
    try:
        clues = [build_clue(con, spec) for spec in CLUE_SPECS]
    finally:
        con.close()
    clues.sort(key=lambda x: x["priority"])
    return {
        "version": "research-clue-desk-v1.6",
        "generated_at": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        "positioning": "AI Research Clue Desk",
        "valuation_engine_status": "FAIL_UNDER_AUDIT",
        "odds_ranking_status": "INVALID_UNTIL_REVALIDATED",
        "openai_calls": OPENAI_CALLS,
        "openai_cost_usd": 0,
        "production_changed": False,
        "clues": clues,
    }


def validate(report: dict[str, Any]) -> dict[str, Any]:
    clues = report["clues"]
    checks = {
        "clue_count_8_to_15": 8 <= len(clues) <= 15,
        "five_complete_timelines": sum(x["timeline_completeness"] == "COMPLETE" for x in clues) >= 5,
        "three_multi_author": sum(len(x["authors"]) >= 2 for x in clues) >= 3,
        "three_with_media": sum(x["media_evidence_count"] > 0 for x in clues) >= 3,
        "three_with_source_dedup": sum(x["independent_evidence_roots"] >= 2 for x in clues) >= 3,
        "all_required_fields": all(
            all(x.get(k) not in (None, "", []) for k in (
                "title", "theme", "status", "one_line_thesis", "first_seen", "last_updated",
                "authors", "timeline", "ai_research_view", "what_to_research_next",
            )) for x in clues
        ),
        "zero_openai_calls": report["openai_calls"] == 0,
        "zero_openai_cost": report["openai_cost_usd"] == 0,
        "production_unchanged": report["production_changed"] is False,
    }
    if not all(checks.values()):
        raise RuntimeError(f"Research Clue Preview validation failed: {checks}")
    return checks


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--db", type=Path, default=DEFAULT_DB)
    parser.add_argument("--out-dir", type=Path, default=DEFAULT_OUT)
    args = parser.parse_args()
    report = build(args.db)
    checks = validate(report)
    args.out_dir.mkdir(parents=True, exist_ok=True)
    (args.out_dir / "research_clues.json").write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    summary = {
        "status": "RESEARCH CLUE DESK PREVIEW READY",
        "generated_at": report["generated_at"],
        "clue_count": len(report["clues"]),
        "complete_timeline_count": sum(x["timeline_completeness"] == "COMPLETE" for x in report["clues"]),
        "multi_author_count": sum(len(x["authors"]) >= 2 for x in report["clues"]),
        "media_clue_count": sum(x["media_evidence_count"] > 0 for x in report["clues"]),
        "source_dedup_count": sum(x["independent_evidence_roots"] >= 2 for x in report["clues"]),
        "openai_calls": 0,
        "openai_cost_usd": 0,
        "production_changed": False,
        "checks": checks,
    }
    (args.out_dir / "run_report.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(summary, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
