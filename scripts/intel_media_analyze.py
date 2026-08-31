#!/usr/bin/env python3
"""Download, hash, deduplicate and semantically analyze new Post media."""
from __future__ import annotations

import argparse
import base64
import hashlib
import json
import os
import sqlite3
import sys
import time
from pathlib import Path

import requests

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from signalboard.ai.guardrails import AIGuardrailBlocked
from signalboard.ai.router import call_json, record_usage, resolve_route, stable_input_hash
from signalboard.db import init_db

DB_PATH = "/workspace/data/signalboard_full.db"
PROMPT_VERSION = "media-v1.1.0"
MAX_DOWNLOAD_BYTES = 15 * 1024 * 1024

MEDIA_SCHEMA = {
    "type": "object",
    "additionalProperties": False,
    "properties": {
        "media_type": {"type": "string", "enum": [
            "news_screenshot", "financial_table", "earnings_slide", "supply_chain_map",
            "chart", "tweet_screenshot", "company_presentation", "research_report", "other",
        ]},
        "source_detected": {"type": "string"},
        "document_type": {"type": "string"},
        "summary": {"type": "string"},
        "important_text": {"type": "array", "items": {"type": "string"}},
        "companies": {"type": "array", "items": {"type": "string"}},
        "tickers": {"type": "array", "items": {"type": "string"}},
        "metrics": {"type": "array", "items": {"type": "string"}},
        "dates": {"type": "array", "items": {"type": "string"}},
        "themes": {"type": "array", "items": {"type": "string"}},
        "claims": {"type": "array", "items": {
            "type": "object", "additionalProperties": False,
            "properties": {
                "claim_text": {"type": "string"},
                "claim_type": {"type": "string", "enum": [
                    "FACT", "FORECAST", "OPINION", "INFERENCE", "VALUATION", "CATALYST", "RISK"
                ]},
                "claim_author": {"type": "string"},
                "companies": {"type": "array", "items": {"type": "string"}},
                "themes": {"type": "array", "items": {"type": "string"}},
                "time_horizon": {"type": "string"},
            },
            "required": ["claim_text", "claim_type", "claim_author", "companies", "themes", "time_horizon"],
        }},
        "chart_insights": {"type": "array", "items": {"type": "string"}},
        "investment_implications": {"type": "array", "items": {"type": "string"}},
        "confidence": {"type": "number", "minimum": 0, "maximum": 1},
    },
    "required": [
        "media_type", "source_detected", "document_type", "summary", "important_text",
        "companies", "tickers", "metrics", "dates", "themes", "claims", "chart_insights",
        "investment_implications", "confidence",
    ],
}

SYSTEM_PROMPT = """你是投资研究图片分析器。你必须理解图片表达的结论，而不只是OCR。
严格区分图片直接呈现的事实、来源观点和你的投资推断；claim_type 必须保留这种区别。
claim_author 是图片中真正作出该陈述的公司、媒体、研究机构或人物，不是转发图片的社交账号。
不要把图片中的预测写成已验证事实。
输出必须符合给定 JSON Schema；无法识别的字段用空字符串或空数组，不要编造。"""


def _theme_id(name: str) -> str:
    return "theme_" + hashlib.sha256(name.strip().casefold().encode()).hexdigest()[:20]


def _persist_media_claims(con: sqlite3.Connection, media_id: str, post_id: str, analysis: dict) -> int:
    point = con.execute("SELECT published_at FROM raw_posts WHERE post_id=?", (post_id,)).fetchone()
    point_in_time = point[0] if point else None
    count = 0
    for index, claim in enumerate(analysis.get("claims") or []):
        text = str(claim.get("claim_text") or "").strip()
        if not text:
            continue
        content_hash = hashlib.sha256(text.casefold().encode()).hexdigest()
        claim_id = "claim_media_" + hashlib.sha256(f"{media_id}\n{index}\n{content_hash}".encode()).hexdigest()[:24]
        themes = [str(x).strip() for x in claim.get("themes") or analysis.get("themes") or [] if str(x).strip()]
        con.execute(
            """INSERT OR REPLACE INTO claims
               (claim_id,claim_text,claim_type,author_id,companies_json,themes_json,time_horizon,
                source_post_id,source_media_id,evidence_ids_json,confidence,verification_status,point_in_time,content_hash)
               VALUES (?,?,?,?,?,?,?,?,?,'[]',?,'UNVERIFIED',?,?)""",
            (claim_id, text, claim.get("claim_type") or "OPINION", claim.get("claim_author") or None,
             json.dumps(claim.get("companies") or [], ensure_ascii=False), json.dumps(themes, ensure_ascii=False),
             claim.get("time_horizon") or None, post_id, media_id,
             max(0.0, min(1.0, float(analysis.get("confidence") or 0.5))), point_in_time, content_hash),
        )
        for name in themes:
            tid = _theme_id(name)
            con.execute("INSERT OR IGNORE INTO themes (theme_id,name) VALUES (?,?)", (tid, name))
            con.execute("INSERT OR REPLACE INTO claim_themes (claim_id,theme_id,confidence) VALUES (?,?,?)",
                        (claim_id, tid, float(analysis.get("confidence") or 0.5)))
        count += 1
    return count


def _download(url: str) -> tuple[bytes, str]:
    response = requests.get(url, timeout=30, stream=True, headers={"User-Agent": "SignalBoard/1.0"})
    response.raise_for_status()
    chunks: list[bytes] = []
    size = 0
    for chunk in response.iter_content(64 * 1024):
        if not chunk:
            continue
        size += len(chunk)
        if size > MAX_DOWNLOAD_BYTES:
            raise ValueError(f"media exceeds {MAX_DOWNLOAD_BYTES} bytes")
        chunks.append(chunk)
    mime = (response.headers.get("content-type") or "image/jpeg").split(";", 1)[0].strip()
    return b"".join(chunks), mime


def _data_url(content: bytes, mime_type: str) -> str:
    return f"data:{mime_type};base64,{base64.b64encode(content).decode('ascii')}"


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--db", default=DB_PATH)
    parser.add_argument(
        "--limit", type=int,
        default=int(os.getenv("MEDIA_BACKFILL_BATCH_SIZE", os.getenv("MEDIA_AI_MAX_ITEMS", "6"))),
    )
    parser.add_argument("--post-ids", help="逗号分隔的精确 post_id；Golden media 优先")
    parser.add_argument("--estimate-only", action="store_true", help="只下载/hash/估算，不调用 Vision")
    args = parser.parse_args()
    if args.limit < 0 or args.limit > 50:
        raise SystemExit("--limit must be between 0 and 50")
    if args.limit > int(os.getenv("MEDIA_AI_MAX_ITEMS", "6")):
        os.environ.setdefault("AI_JOB_KIND", "historical_media_backfill")

    init_db(args.db)
    con = sqlite3.connect(args.db, timeout=120)
    post_ids = [x.strip() for x in (args.post_ids or "").split(",") if x.strip()]
    post_filter = ""
    params: list[object] = []
    if post_ids:
        post_filter = f"AND m.post_id IN ({','.join('?' for _ in post_ids)})"
        params.extend(post_ids)
    params.append(args.limit)
    rows = con.execute(
        f"""
        SELECT m.media_id, m.post_id, m.source_url, m.content_hash, r.raw_text
        FROM media_assets m
        JOIN raw_posts r ON r.post_id=m.post_id
        LEFT JOIN media_analyses a ON a.media_id=m.media_id
        WHERE a.media_id IS NULL AND m.analysis_status IN ('pending','error','FAILED_RETRYABLE')
          AND m.media_type IN ('photo','image','animated_gif')
          {post_filter}
        ORDER BY
          CASE
            WHEN lower(r.raw_text) GLOB '*chart*' OR lower(r.raw_text) GLOB '*table*'
              OR lower(r.raw_text) GLOB '*earnings*' OR lower(r.raw_text) GLOB '*report*'
              OR lower(r.raw_text) GLOB '*slide*' OR lower(r.raw_text) GLOB '*supply chain*'
              OR lower(r.raw_text) GLOB '*研报*' OR lower(r.raw_text) GLOB '*财报*'
              OR lower(r.raw_text) GLOB '*产能*' OR lower(r.raw_text) GLOB '*架构*' THEN 0
            WHEN lower(r.raw_text) GLOB '*meme*' OR lower(r.raw_text) GLOB '*avatar*' THEN 2
            ELSE 1
          END,
          r.published_at DESC
        LIMIT ?
        """,
        params,
    ).fetchall()
    stats = {
        "selected": len(rows), "analyzed": 0, "deduplicated": 0, "hashed_only": 0,
        "media_claims": 0, "failed_retryable": 0, "cost_usd": 0.0,
    }
    configured_model = resolve_route("media_understanding").model
    force_reanalyze = os.getenv("FORCE_REANALYZE", "false").strip().lower() in {"1", "true", "yes", "on"}
    for media_id, post_id, source_url, old_hash, post_text in rows:
        started = time.monotonic()
        try:
            content, mime_type = _download(source_url)
            content_hash = hashlib.sha256(content).hexdigest()
            input_hash = stable_input_hash(PROMPT_VERSION, content_hash, post_text or "")
            con.execute(
                """
                UPDATE media_assets
                SET content_hash=?, mime_type=?, storage_url=COALESCE(storage_url, source_url),
                    download_status='complete', updated_at=strftime('%Y-%m-%dT%H:%M:%fZ', 'now')
                WHERE media_id=?
                """,
                (content_hash, mime_type, media_id),
            )
            duplicate = None if force_reanalyze else con.execute(
                """
                SELECT a.prompt_version, a.provider, a.model, a.input_hash, a.analysis_json
                FROM media_assets m JOIN media_analyses a ON a.media_id=m.media_id
                WHERE m.content_hash=? AND a.prompt_version=? AND a.model=? AND m.media_id<>?
                LIMIT 1
                """,
                (content_hash, PROMPT_VERSION, configured_model, media_id),
            ).fetchone()
            if duplicate:
                con.execute(
                    """
                    INSERT OR REPLACE INTO media_analyses
                    (media_id, prompt_version, provider, model, input_hash, analysis_json)
                    VALUES (?, ?, ?, ?, ?, ?)
                    """,
                    (media_id, *duplicate),
                )
                con.execute("UPDATE media_assets SET analysis_status='complete' WHERE media_id=?", (media_id,))
                stats["media_claims"] += _persist_media_claims(con, media_id, post_id, json.loads(duplicate[4]))
                con.commit()
                stats["deduplicated"] += 1
                continue

            if args.estimate_only:
                con.commit()
                stats["hashed_only"] += 1
                continue

            user = (
                "分析这张帖子图片。帖子文字仅用于语境，不代表图片内容已经被证实。\n"
                f"post_id: {post_id}\n帖子文字: {(post_text or '')[:1200]}"
            )
            result = call_json(
                "media_understanding", SYSTEM_PROMPT, user, MEDIA_SCHEMA,
                schema_name="signalboard_media_analysis",
                image_urls=[_data_url(content, mime_type)],
                max_output_tokens=2200,
                timeout=120,
                prompt_version=PROMPT_VERSION, entity_type="media", entity_id=media_id,
            )
            con.execute(
                """
                INSERT OR REPLACE INTO media_analyses
                (media_id, prompt_version, provider, model, input_hash, analysis_json)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (media_id, PROMPT_VERSION, result.provider, result.model, input_hash, json.dumps(result.data, ensure_ascii=False)),
            )
            con.execute("UPDATE media_assets SET analysis_status='complete' WHERE media_id=?", (media_id,))
            stats["media_claims"] += _persist_media_claims(con, media_id, post_id, result.data)
            record_usage(con, result, workload="media_understanding", object_type="media", object_id=media_id)
            con.commit()
            stats["analyzed"] += 1
            stats["cost_usd"] = round(stats["cost_usd"] + result.estimated_cost_usd, 8)
        except AIGuardrailBlocked as exc:
            con.rollback()
            stats["budget_blocked"] = stats.get("budget_blocked", 0) + 1
            stats["stop_reason"] = exc.reason
            print(f"AI_GUARDRAIL_STOP media_id={media_id} reason={exc.reason}")
            break
        except Exception as exc:
            con.rollback()
            con.execute(
                "UPDATE media_assets SET analysis_status='FAILED_RETRYABLE', updated_at=strftime('%Y-%m-%dT%H:%M:%fZ', 'now') WHERE media_id=?",
                (media_id,),
            )
            record_usage(
                con, None, workload="media_understanding", object_type="media", object_id=media_id,
                error=exc, latency_ms=int((time.monotonic() - started) * 1000),
            )
            con.commit()
            stats["failed_retryable"] += 1
            print(f"warning: media analysis failed media_id={media_id}: {type(exc).__name__}: {exc}")
    con.close()
    print(json.dumps(stats, ensure_ascii=False, sort_keys=True))
    # 单张 Vision/下载失败永远不能阻塞 daily pipeline；状态会在后续批次自动重试。


if __name__ == "__main__":
    main()
