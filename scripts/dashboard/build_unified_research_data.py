#!/usr/bin/env python3
"""Export the existing SignalBoard corpus for the unified research UI.

This is deliberately a deterministic SQLite/HTML renderer. It performs no
network requests and has no model/provider dependency.
"""

from __future__ import annotations

import argparse
import gzip
import html
import json
import re
import sqlite3
from collections import defaultdict
from pathlib import Path
from urllib.parse import urlparse


ROOT = Path(__file__).resolve().parents[2]
DEFAULT_DB = ROOT / "data" / "signalboard_full.db"
DEFAULT_LEGACY = Path(__file__).with_name("dashboard.html")
DEFAULT_CLUES = ROOT / "outputs" / "research_clue_desk_v16" / "research_clues.json"
DEFAULT_OUTPUT = ROOT / "dashboard_deploy_dist" / "data" / "raw-intelligence.json"

AUTHOR_ALIASES = {
    "tw_jukan05": "jukan",
    "tw_zephyr_z9": "zephyr",
    "tw_aleabitoreddit": "serenity",
    "tw_austinsemis": "austin",
    "tw_DGretta_Author": "dgretta",
    "tw_FeroceResearch": "feroce",
    "tw_TradexWhisperer": "tradex",
    "tw_gsmferrari": "gsmferrari",
}


def embedded_json(path: Path, element_id: str, default):
    text = path.read_text(encoding="utf-8")
    match = re.search(
        rf'<script id="{re.escape(element_id)}"[^>]*>(.*?)</script>', text, re.S
    )
    return json.loads(match.group(1)) if match else default


def safe_json(value, default):
    try:
        return json.loads(value) if value else default
    except (TypeError, ValueError):
        return default


def unique(values):
    return list(dict.fromkeys(value for value in values if value))


def post_id_from_url(url: str | None) -> str | None:
    match = re.search(r"/status/(\d+)", url or "")
    return match.group(1) if match else None


def author_payload(raw: dict, source_id: str) -> dict:
    author = raw.get("author") or {}
    handle = author.get("userName") or source_id.removeprefix("tw_").removeprefix("ctx_")
    key = AUTHOR_ALIASES.get(source_id, handle.lower())
    return {
        "key": key,
        "name": author.get("name") or handle,
        "handle": handle,
        "avatar": author.get("profilePicture") or "",
    }


def media_payload(item: dict) -> dict:
    raw = safe_json(item.get("raw_payload"), {})
    variants = ((raw.get("video_info") or {}).get("variants") or [])
    video = next(
        (v.get("url") for v in sorted(variants, key=lambda x: x.get("bitrate", 0), reverse=True)
         if str(v.get("content_type", "")).startswith("video/")),
        "",
    )
    analysis = safe_json(item.get("analysis_json"), {})
    return {
        "id": item.get("media_id"),
        "type": item.get("media_type") or raw.get("type") or "media",
        "url": item.get("storage_url") or item.get("source_url") or raw.get("media_url_https") or "",
        "video": video,
        "width": item.get("width") or ((raw.get("original_info") or {}).get("width")),
        "height": item.get("height") or ((raw.get("original_info") or {}).get("height")),
        "alt": raw.get("ext_alt_text") or "",
        "analysis": analysis,
    }


def inline_media(raw: dict) -> list[dict]:
    items = ((raw.get("extendedEntities") or {}).get("media") or [])
    out = []
    for item in items:
        variants = ((item.get("video_info") or {}).get("variants") or [])
        video = next(
            (v.get("url") for v in sorted(variants, key=lambda x: x.get("bitrate", 0), reverse=True)
             if str(v.get("content_type", "")).startswith("video/")),
            "",
        )
        info = item.get("original_info") or {}
        out.append({
            "id": item.get("media_key") or item.get("id_str"),
            "type": item.get("type") or "media",
            "url": item.get("media_url_https") or "",
            "video": video,
            "width": info.get("width"),
            "height": info.get("height"),
            "alt": item.get("ext_alt_text") or "",
            "analysis": {},
        })
    return out


def quoted_payload(raw: dict) -> dict | None:
    quote = raw.get("quote")
    if not isinstance(quote, dict):
        return None
    author = quote.get("author") or {}
    return {
        "id": str(quote.get("id") or raw.get("quoteId") or ""),
        "author": author.get("name") or author.get("userName") or "Quoted source",
        "handle": author.get("userName") or "",
        "avatar": author.get("profilePicture") or "",
        "date": quote.get("createdAt") or "",
        "text": html.unescape(quote.get("fullText") or quote.get("text") or ""),
        "url": quote.get("url") or quote.get("twitterUrl") or "",
        "media": inline_media(quote),
    }


def external_links(raw: dict, raw_url: str) -> list[str]:
    links = []
    entities = raw.get("entities") or {}
    for item in entities.get("urls") or []:
        links.append(item.get("expanded_url") or item.get("url"))
    card = raw.get("card") or {}
    binding = card.get("binding_values") or card.get("bindingValues") or []
    if isinstance(binding, dict):
        binding = [{"value": value} for value in binding.values()]
    for item in binding:
        value = item.get("value") if isinstance(item, dict) else None
        if isinstance(value, dict):
            links.append(value.get("string_value") or value.get("stringValue"))
    clean = []
    for link in unique(links):
        if not link or link == raw_url:
            continue
        try:
            if urlparse(link).netloc in {"x.com", "twitter.com"}:
                continue
        except ValueError:
            pass
        clean.append(link)
    return clean


def build(database: Path, legacy_dashboard: Path, clues_path: Path) -> dict:
    clues_doc = json.loads(clues_path.read_text(encoding="utf-8"))
    if clues_doc.get("openai_calls") != 0:
        raise RuntimeError("Unified export requires the approved zero-AI clue artifact")

    clue_posts: dict[str, list[str]] = defaultdict(list)
    for clue in clues_doc.get("clues", []):
        for event in clue.get("timeline", []):
            post_id = post_id_from_url(event.get("post_url"))
            if post_id:
                clue_posts[post_id].append(clue["clue_id"])
            for quote in event.get("quoted_posts", []):
                quote_id = post_id_from_url(quote.get("url"))
                if quote_id:
                    clue_posts[quote_id].append(clue["clue_id"])

    con = sqlite3.connect(database)
    con.row_factory = sqlite3.Row

    extracted: dict[str, dict] = {}
    for row in con.execute(
        """SELECT post_id,ticker,company,bottleneck,attribution,summary_100,
                  is_retrospective,is_disclosure,is_self_reported_returns
             FROM extractions_intel ORDER BY id"""
    ):
        item = extracted.setdefault(str(row["post_id"]), {
            "tickers": [], "companies": [], "themes": [], "summary": "",
            "attribution": "", "important": False,
        })
        for key, column in (("tickers", "ticker"), ("companies", "company")):
            value = row[column]
            parsed = safe_json(value, None)
            item[key].extend(parsed if isinstance(parsed, list) else ([value] if value else []))
        if row["bottleneck"]:
            item["themes"].append(row["bottleneck"])
        item["summary"] = item["summary"] or row["summary_100"] or ""
        item["attribution"] = item["attribution"] or row["attribution"] or ""
        item["important"] = item["important"] or any(
            row[name] for name in ("is_retrospective", "is_disclosure", "is_self_reported_returns")
        )
    for item in extracted.values():
        for key in ("tickers", "companies", "themes"):
            item[key] = unique(item[key])

    claims: dict[str, list[str]] = defaultdict(list)
    for row in con.execute("SELECT source_post_id,claim_text FROM claims WHERE source_post_id IS NOT NULL"):
        claims[str(row["source_post_id"])].append(row["claim_text"])

    media: dict[str, list[dict]] = defaultdict(list)
    for row in con.execute(
        """SELECT m.*,a.analysis_json FROM media_assets m
             LEFT JOIN media_analyses a ON a.media_id=m.media_id
             ORDER BY m.post_id,m.media_id"""
    ):
        media[str(row["post_id"])].append(media_payload(dict(row)))

    reference_map: dict[str, list[dict]] = defaultdict(list)
    for row in con.execute("SELECT * FROM post_references ORDER BY discovered_at"):
        reference_map[str(row["source_post_id"])].append(dict(row))

    rows = list(con.execute(
        """SELECT post_id,source_id,published_at,raw_text,raw_url,raw_json
             FROM raw_posts
            WHERE is_deleted=0 AND source_id LIKE 'tw_%'
            ORDER BY published_at DESC,post_id DESC"""
    ))
    raw_by_id = {str(row["post_id"]): row for row in rows}
    authors: dict[str, dict] = {}
    posts = []
    for row in rows:
        post_id = str(row["post_id"])
        raw = safe_json(row["raw_json"], {})
        author = author_payload(raw, row["source_id"])
        authors[author["key"]] = author
        meta = extracted.get(post_id, {})
        post_media = media.get(post_id) or inline_media(raw)
        reply_id = str(raw.get("inReplyToId") or "")
        for reference in reference_map.get(post_id, []):
            if reference.get("reference_type") == "reply":
                reply_id = str(reference.get("target_post_id") or reply_id)
        reply = None
        if reply_id:
            parent = raw_by_id.get(reply_id)
            if parent:
                parent_raw = safe_json(parent["raw_json"], {})
                parent_author = author_payload(parent_raw, parent["source_id"])
                reply = {
                    "id": reply_id,
                    "author": parent_author["name"],
                    "handle": parent_author["handle"],
                    "date": parent["published_at"],
                    "text": html.unescape(parent["raw_text"] or ""),
                    "url": parent["raw_url"],
                }
            else:
                reply = {
                    "id": reply_id,
                    "author": raw.get("inReplyToUsername") or "Reply parent",
                    "handle": raw.get("inReplyToUsername") or "",
                    "date": "", "text": "", "url": f"https://x.com/i/status/{reply_id}",
                }
        posts.append({
            "id": post_id,
            "author": author["key"],
            "author_name": author["name"],
            "handle": author["handle"],
            "avatar": author["avatar"],
            "date": row["published_at"],
            "text": html.unescape(row["raw_text"] or ""),
            "url": row["raw_url"],
            "tickers": meta.get("tickers", []),
            "companies": meta.get("companies", []),
            "themes": meta.get("themes", []),
            "summary": meta.get("summary", ""),
            "attribution": meta.get("attribution", ""),
            "media": post_media,
            "quote": quoted_payload(raw),
            "reply": reply,
            "repost": bool(raw.get("isRetweet")),
            "links": external_links(raw, row["raw_url"]),
            "claims": unique(claims.get(post_id, [])),
            "clue_ids": unique(clue_posts.get(post_id, [])),
            "important": bool(meta.get("important") or clue_posts.get(post_id)),
        })

    legacy_kols = embedded_json(legacy_dashboard, "KOLS", {})
    for key, value in legacy_kols.items():
        author = authors.setdefault(key, {"key": key, "name": value.get("name", key), "handle": value.get("handle", "").lstrip("@"), "avatar": ""})
        author.update({
            "rating": value.get("rating", ""),
            "type": value.get("typeLabel") or value.get("type") or "",
            "description": value.get("desc", ""),
        })

    latest = posts[0]["date"] if posts else clues_doc.get("generated_at")
    return {
        "version": "unified-research-experience-v1.6.3",
        "generated_at": latest,
        "openai_calls": 0,
        "openai_cost_usd": 0,
        "posts": posts,
        "authors": sorted(authors.values(), key=lambda x: x["name"].lower()),
        "tracking": {
            "tickers": embedded_json(legacy_dashboard, "TICKERS", []),
            "call_performance": embedded_json(legacy_dashboard, "CALL_PERFORMANCE", []),
            "people": legacy_kols,
        },
        "research_changes": embedded_json(legacy_dashboard, "THESIS_CHANGES", []),
        "ai_usage": embedded_json(legacy_dashboard, "AI_COST_PANEL", {}),
        "preservation": {
            "raw_posts": True,
            "author_posts": True,
            "quote_chain": True,
            "media": True,
            "research_changes": True,
            "tracking": True,
            "ticker_tracking": True,
            "recent_detail": True,
        },
    }


def render(database: Path, legacy_dashboard: Path, clues_path: Path, output: Path) -> Path:
    payload = build(database, legacy_dashboard, clues_path)
    output.parent.mkdir(parents=True, exist_ok=True)
    encoded = json.dumps(payload, ensure_ascii=False, separators=(",", ":")).replace("</", "<\\/").encode("utf-8")
    if output.suffix == ".gz":
        output.write_bytes(gzip.compress(encoded, compresslevel=9, mtime=0))
    else:
        output.write_bytes(encoded)
    return output


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--database", type=Path, default=DEFAULT_DB)
    parser.add_argument("--legacy-dashboard", type=Path, default=DEFAULT_LEGACY)
    parser.add_argument("--clues", type=Path, default=DEFAULT_CLUES)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    args = parser.parse_args()
    print(render(args.database, args.legacy_dashboard, args.clues, args.output))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
