"""Normalize Apify X payloads into an idempotent Post/Evidence graph."""
from __future__ import annotations

import hashlib
import json
import mimetypes
from datetime import datetime, timezone
from typing import Any, Iterable
from urllib.parse import urlsplit, urlunsplit

from .models import Platform, RawPost
from .scraper import to_utc_iso

MAX_GRAPH_DEPTH = 10
X_HOSTS = {"x.com", "www.x.com", "twitter.com", "www.twitter.com", "t.co", "pic.x.com"}


def _now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _author_handle(item: dict[str, Any]) -> str:
    author = item.get("author") or {}
    if isinstance(author, dict):
        return str(author.get("userName") or author.get("screen_name") or "").strip()
    return ""


def _post_url(item: dict[str, Any], post_id: str) -> str:
    direct = item.get("url") or item.get("twitterUrl") or item.get("tweetUrl")
    if direct:
        return str(direct)
    handle = _author_handle(item) or "i"
    return f"https://x.com/{handle}/status/{post_id}"


def _reference_candidates(item: dict[str, Any]) -> Iterable[tuple[str, str, dict[str, Any] | None]]:
    quote = item.get("quote") or item.get("quotedTweet") or item.get("quoted_tweet")
    quote_id = item.get("quoteId") or item.get("quotedStatusId") or item.get("quotedTweetId")
    if isinstance(quote, dict):
        quote_id = quote.get("id") or quote.get("id_str") or quote_id
    if quote_id:
        yield "quote", str(quote_id), quote if isinstance(quote, dict) else None

    reply_id = (
        item.get("inReplyToId") or item.get("inReplyToStatusId")
        or item.get("in_reply_to_status_id") or item.get("inReplyToTweetId")
    )
    if reply_id:
        yield "reply", str(reply_id), None

    repost = item.get("retweetedTweet") or item.get("retweet") or item.get("repostedTweet")
    repost_id = item.get("retweetedStatusId") or item.get("retweetId")
    if isinstance(repost, dict):
        repost_id = repost.get("id") or repost.get("id_str") or repost_id
    if repost_id:
        yield "repost", str(repost_id), repost if isinstance(repost, dict) else None


def _media_entries(item: dict[str, Any]) -> list[dict[str, Any]]:
    extended = item.get("extendedEntities") or item.get("extended_entities") or {}
    entries = extended.get("media") if isinstance(extended, dict) else None
    if isinstance(entries, list) and entries:
        return [x for x in entries if isinstance(x, dict)]
    raw_media = item.get("media")
    if not isinstance(raw_media, list):
        return []
    return [{"media_url_https": x, "type": "photo"} for x in raw_media if isinstance(x, str)]


def _canonical_url(url: str) -> str:
    parts = urlsplit(url.strip())
    return urlunsplit((parts.scheme.lower() or "https", parts.netloc.lower(), parts.path, parts.query, ""))


def _external_urls(item: dict[str, Any]) -> Iterable[str]:
    entities = item.get("entities") or {}
    urls = entities.get("urls") if isinstance(entities, dict) else None
    for entry in urls or []:
        if not isinstance(entry, dict):
            continue
        url = entry.get("expanded_url") or entry.get("expandedUrl") or entry.get("url")
        if not url:
            continue
        canonical = _canonical_url(str(url))
        if urlsplit(canonical).netloc.lower() not in X_HOSTS:
            yield canonical


def _upsert_context_post(conn: Any, item: dict[str, Any], captured_at: str) -> str | None:
    post_id = str(item.get("id") or item.get("id_str") or item.get("tweetId") or "").strip()
    text = str(item.get("text") or item.get("fullText") or item.get("rawContent") or "").strip()
    if not post_id or not text:
        return None
    handle = _author_handle(item) or "unknown"
    post = RawPost(
        post_id=post_id,
        source_id=f"ctx_tw_{handle}",
        platform=Platform.TWITTER.value,
        published_at=to_utc_iso(item.get("createdAt") or item.get("created_at") or ""),
        captured_at=captured_at,
        raw_text=text,
        raw_url=_post_url(item, post_id),
        raw_json=json.dumps(item, ensure_ascii=False),
    )
    conn.execute(
        """
        INSERT OR IGNORE INTO raw_posts (
            post_id, source_id, platform, published_at, captured_at,
            raw_text, raw_url, raw_json, content_hash, is_deleted, archive_url
        ) VALUES (
            :post_id, :source_id, :platform, :published_at, :captured_at,
            :raw_text, :raw_url, :raw_json, :content_hash, :is_deleted, :archive_url
        )
        """,
        post.to_row(),
    )
    return post_id


def _upsert_media(conn: Any, post_id: str, item: dict[str, Any]) -> int:
    count = 0
    for media in _media_entries(item):
        source_url = media.get("media_url_https") or media.get("media_url") or media.get("url")
        if not source_url:
            continue
        source_url = str(source_url)
        media_id = str(media.get("media_key") or media.get("id_str") or "").strip()
        if not media_id:
            media_id = "media_" + hashlib.sha256(f"{post_id}\n{source_url}".encode()).hexdigest()[:24]
        original = media.get("original_info") or {}
        width = original.get("width") if isinstance(original, dict) else None
        height = original.get("height") if isinstance(original, dict) else None
        media_type = str(media.get("type") or "image")
        mime_type = mimetypes.guess_type(urlsplit(source_url).path)[0]
        conn.execute(
            """
            INSERT INTO media_assets (
                media_id, post_id, source_url, media_type, mime_type, width, height, raw_payload
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(media_id) DO UPDATE SET
                source_url=excluded.source_url,
                width=COALESCE(excluded.width, media_assets.width),
                height=COALESCE(excluded.height, media_assets.height),
                raw_payload=excluded.raw_payload,
                updated_at=strftime('%Y-%m-%dT%H:%M:%fZ', 'now')
            """,
            (media_id, post_id, source_url, media_type, mime_type, width, height, json.dumps(media, ensure_ascii=False)),
        )
        count += 1
    return count


def _upsert_external_sources(conn: Any, post_id: str, item: dict[str, Any]) -> int:
    count = 0
    for url in _external_urls(item):
        source_id = "ext_" + hashlib.sha256(url.encode()).hexdigest()[:24]
        conn.execute(
            """
            INSERT INTO external_sources (source_id, url)
            VALUES (?, ?)
            ON CONFLICT(url) DO UPDATE SET updated_at=strftime('%Y-%m-%dT%H:%M:%fZ', 'now')
            """,
            (source_id, url),
        )
        actual = conn.execute("SELECT source_id FROM external_sources WHERE url=?", (url,)).fetchone()[0]
        conn.execute(
            "INSERT OR IGNORE INTO post_external_sources (post_id, source_id) VALUES (?, ?)",
            (post_id, actual),
        )
        count += 1
    return count


def ingest_post_graph(conn: Any, db_path: str, root_post_id: str, raw_payload: dict[str, Any]) -> dict[str, int]:
    """Normalize one root and every embedded reference, stopping safely at depth 10."""
    captured_at = _now_iso()
    stats = {"nodes": 0, "edges": 0, "pending": 0, "media": 0, "external_urls": 0}
    visited: set[str] = set()

    def walk(item: dict[str, Any], post_id: str, parent_id: str | None, depth: int, relation: str) -> None:
        if depth > MAX_GRAPH_DEPTH or post_id in visited:
            return
        visited.add(post_id)
        conn.execute(
            """
            INSERT INTO post_graph_memberships (
                root_post_id, post_id, parent_post_id, depth, reference_type, crawl_status
            ) VALUES (?, ?, ?, ?, ?, 'complete')
            ON CONFLICT(root_post_id, post_id) DO UPDATE SET
                parent_post_id=excluded.parent_post_id,
                depth=MIN(post_graph_memberships.depth, excluded.depth),
                reference_type=excluded.reference_type,
                crawl_status='complete',
                crawled_at=strftime('%Y-%m-%dT%H:%M:%fZ', 'now'),
                last_error=NULL
            """,
            (root_post_id, post_id, parent_id, depth, relation),
        )
        stats["nodes"] += 1
        stats["media"] += _upsert_media(conn, post_id, item)
        stats["external_urls"] += _upsert_external_sources(conn, post_id, item)
        if depth == MAX_GRAPH_DEPTH:
            return
        for ref_type, target_id, embedded in _reference_candidates(item):
            target_url = _post_url(embedded, target_id) if embedded else f"https://x.com/i/status/{target_id}"
            complete = embedded is not None
            if not complete:
                row = conn.execute("SELECT raw_json FROM raw_posts WHERE post_id=?", (target_id,)).fetchone()
                if row and row[0]:
                    try:
                        embedded = json.loads(row[0])
                        complete = isinstance(embedded, dict)
                    except json.JSONDecodeError:
                        complete = False
            conn.execute(
                """
                INSERT INTO post_references (
                    source_post_id, target_post_id, reference_type, target_url, fetch_status
                ) VALUES (?, ?, ?, ?, ?)
                ON CONFLICT(source_post_id, target_post_id, reference_type) DO UPDATE SET
                    target_url=excluded.target_url,
                    fetch_status=excluded.fetch_status,
                    last_error=NULL
                """,
                (post_id, target_id, ref_type, target_url, "complete" if complete else "pending"),
            )
            stats["edges"] += 1
            if complete and embedded is not None:
                exists = conn.execute("SELECT 1 FROM raw_posts WHERE post_id=?", (target_id,)).fetchone()
                if not exists:
                    _upsert_context_post(conn, embedded, captured_at)
                walk(embedded, target_id, post_id, depth + 1, ref_type)
            else:
                conn.execute(
                    """
                    INSERT INTO post_graph_memberships (
                        root_post_id, post_id, parent_post_id, depth, reference_type, crawl_status
                    ) VALUES (?, ?, ?, ?, ?, 'pending')
                    ON CONFLICT(root_post_id, post_id) DO UPDATE SET
                        depth=MIN(post_graph_memberships.depth, excluded.depth),
                        crawl_status=CASE WHEN post_graph_memberships.crawl_status='complete' THEN 'complete' ELSE 'pending' END
                    """,
                    (root_post_id, target_id, post_id, depth + 1, ref_type),
                )
                stats["pending"] += 1

    walk(raw_payload, root_post_id, None, 0, "original")
    return stats
