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

from signalboard.ai.router import call_json, record_usage, stable_input_hash
from signalboard.db import init_db

DB_PATH = "/workspace/data/signalboard_full.db"
PROMPT_VERSION = "media-v1.0.0"
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
        "claims": {"type": "array", "items": {"type": "string"}},
        "chart_insights": {"type": "array", "items": {"type": "string"}},
        "investment_implications": {"type": "array", "items": {"type": "string"}},
        "confidence": {"type": "number", "minimum": 0, "maximum": 1},
    },
    "required": [
        "media_type", "source_detected", "document_type", "summary", "important_text",
        "companies", "tickers", "metrics", "dates", "claims", "chart_insights",
        "investment_implications", "confidence",
    ],
}

SYSTEM_PROMPT = """你是投资研究图片分析器。你必须理解图片表达的结论，而不只是OCR。
严格区分图片直接呈现的事实、来源观点和你的投资推断。不要把图片中的预测写成已验证事实。
输出必须符合给定 JSON Schema；无法识别的字段用空字符串或空数组，不要编造。"""


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
    parser.add_argument("--limit", type=int, default=int(os.getenv("MEDIA_AI_MAX_ITEMS", "6")))
    args = parser.parse_args()
    if args.limit < 0 or args.limit > 50:
        raise SystemExit("--limit must be between 0 and 50")

    init_db(args.db)
    con = sqlite3.connect(args.db, timeout=120)
    rows = con.execute(
        """
        SELECT m.media_id, m.post_id, m.source_url, m.content_hash, r.raw_text
        FROM media_assets m
        JOIN raw_posts r ON r.post_id=m.post_id
        LEFT JOIN media_analyses a ON a.media_id=m.media_id
        WHERE a.media_id IS NULL AND m.analysis_status IN ('pending','error')
          AND m.media_type IN ('photo','image','animated_gif')
        ORDER BY r.published_at DESC
        LIMIT ?
        """,
        (args.limit,),
    ).fetchall()
    stats = {"selected": len(rows), "analyzed": 0, "deduplicated": 0, "failed": 0, "cost_usd": 0.0}
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
            duplicate = con.execute(
                """
                SELECT a.prompt_version, a.provider, a.model, a.input_hash, a.analysis_json
                FROM media_assets m JOIN media_analyses a ON a.media_id=m.media_id
                WHERE m.content_hash=? AND a.prompt_version=? AND m.media_id<>?
                LIMIT 1
                """,
                (content_hash, PROMPT_VERSION, media_id),
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
                con.commit()
                stats["deduplicated"] += 1
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
            record_usage(con, result, workload="media_understanding", object_type="media", object_id=media_id)
            con.commit()
            stats["analyzed"] += 1
            stats["cost_usd"] = round(stats["cost_usd"] + result.estimated_cost_usd, 8)
        except Exception as exc:
            con.rollback()
            con.execute(
                "UPDATE media_assets SET analysis_status='error', updated_at=strftime('%Y-%m-%dT%H:%M:%fZ', 'now') WHERE media_id=?",
                (media_id,),
            )
            record_usage(
                con, None, workload="media_understanding", object_type="media", object_id=media_id,
                error=exc, latency_ms=int((time.monotonic() - started) * 1000),
            )
            con.commit()
            stats["failed"] += 1
            print(f"warning: media analysis failed media_id={media_id}: {type(exc).__name__}: {exc}")
    con.close()
    print(json.dumps(stats, ensure_ascii=False, sort_keys=True))
    if stats["selected"] and not (stats["analyzed"] or stats["deduplicated"]):
        raise SystemExit("all selected media analyses failed")


if __name__ == "__main__":
    main()
