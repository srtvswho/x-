#!/usr/bin/env python3
"""Map social mentions, URLs and media onto independent Underlying Sources."""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import sqlite3
import sys
from pathlib import Path
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit

import requests

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from signalboard.db import init_db

DB_PATH = "/workspace/data/signalboard_full.db"
TRACKING_KEYS = {"utm_source", "utm_medium", "utm_campaign", "utm_term", "utm_content", "ref", "source"}


def canonical_url(url: str) -> str:
    parts = urlsplit(url.strip())
    host = parts.netloc.lower().removeprefix("www.")
    path = re.sub(r"/+", "/", parts.path).rstrip("/") or "/"
    query = urlencode([(k, v) for k, v in parse_qsl(parts.query) if k.lower() not in TRACKING_KEYS])
    return urlunsplit((parts.scheme.lower() or "https", host, path, query, ""))


def _resolve(url: str) -> str:
    try:
        response = requests.get(url, timeout=15, allow_redirects=True, stream=True,
                                headers={"User-Agent": "SignalBoard/1.1"})
        return canonical_url(response.url or url)
    except Exception:
        return canonical_url(url)


def _source_class(publisher: str | None, url: str) -> str:
    host = urlsplit(url).netloc.lower()
    text = f"{publisher or ''} {host}".lower()
    if any(x in text for x in ("sec.gov", "investor.", "ir.", "hkex", "nasdaq.com/market-activity/sec-filings", ".gov")):
        return "PRIMARY"
    if any(x in text for x in ("reuters", "bloomberg", "ft.com", "wsj.com", "financial times")):
        return "SECONDARY"
    if any(x in text for x in ("trendforce", "digitimes", "semianalysis", "tomshardware", "techinsights")):
        return "INDUSTRY"
    return "UNKNOWN"


def _underlying_id(key: str) -> str:
    return "underlying_" + hashlib.sha256(key.encode()).hexdigest()[:24]


def _component_posts(con: sqlite3.Connection, seed: str) -> set[str]:
    rows = con.execute(
        """
        WITH RECURSIVE connected(post_id) AS (
          SELECT ?
          UNION
          SELECT pr.target_post_id FROM post_references pr JOIN connected c ON pr.source_post_id=c.post_id
          UNION
          SELECT pr.source_post_id FROM post_references pr JOIN connected c ON pr.target_post_id=c.post_id
        ) SELECT post_id FROM connected LIMIT 500
        """, (seed,),
    ).fetchall()
    return {r[0] for r in rows}


def build_source_map(con: sqlite3.Connection, *, resolve_redirects: bool = False,
                     post_ids: list[str] | None = None) -> dict[str, int]:
    stats = {"external_sources": 0, "media_sources": 0, "social_mentions": 0, "components": 0}
    external_rows = con.execute(
        "SELECT source_id,url,publisher,title,content_hash FROM external_sources ORDER BY source_id"
    ).fetchall()
    external_to_underlying: dict[str, str] = {}
    for source_id, url, publisher, title, content_hash in external_rows:
        resolved = _resolve(url) if resolve_redirects else canonical_url(url)
        key = f"hash:{content_hash}" if content_hash else f"url:{resolved}"
        uid = _underlying_id(key)
        con.execute(
            """INSERT INTO underlying_sources
               (underlying_source_id,canonical_url,publisher,title,source_class,content_hash)
               VALUES (?,?,?,?,?,?)
               ON CONFLICT(underlying_source_id) DO UPDATE SET
                 publisher=COALESCE(excluded.publisher,underlying_sources.publisher),
                 title=COALESCE(excluded.title,underlying_sources.title),
                 updated_at=strftime('%Y-%m-%dT%H:%M:%fZ','now')""",
            (uid, resolved, publisher, title, _source_class(publisher, resolved), content_hash),
        )
        con.execute(
            "INSERT OR IGNORE INTO source_memberships (underlying_source_id,evidence_type,evidence_id) VALUES (?,'external',?)",
            (uid, source_id),
        )
        external_to_underlying[source_id] = uid
        stats["external_sources"] += 1

    seeds = post_ids or [r[0] for r in con.execute(
        "SELECT DISTINCT post_id FROM post_external_sources UNION SELECT DISTINCT post_id FROM media_assets"
    ).fetchall()]
    seen: set[str] = set()
    for seed in seeds:
        if seed in seen:
            continue
        component = _component_posts(con, seed)
        seen.update(component)
        stats["components"] += 1
        placeholders = ",".join("?" for _ in component)
        if not placeholders:
            continue
        linked = con.execute(
            f"SELECT DISTINCT source_id FROM post_external_sources WHERE post_id IN ({placeholders})", tuple(component)
        ).fetchall()
        component_underlying = [external_to_underlying[r[0]] for r in linked if r[0] in external_to_underlying]
        media = con.execute(
            f"SELECT media_id,post_id,content_hash FROM media_assets WHERE post_id IN ({placeholders})", tuple(component)
        ).fetchall()
        for media_id, media_post_id, content_hash in media:
            # A screenshot in a component with an explicit article link is a visual representation
            # of that source; it is not an additional independent source.
            if component_underlying:
                uid = component_underlying[0]
            else:
                key = f"media:{content_hash or media_id}"
                uid = _underlying_id(key)
                con.execute(
                    """INSERT OR IGNORE INTO underlying_sources
                       (underlying_source_id,source_class,content_hash) VALUES (?,'MEDIA',?)""",
                    (uid, content_hash),
                )
                if uid not in component_underlying:
                    component_underlying.append(uid)
            con.execute(
                """INSERT OR IGNORE INTO source_memberships
                   (underlying_source_id,evidence_type,evidence_id,mention_post_id,relation_type)
                   VALUES (?,'media',?,?,?)""",
                (uid, media_id, media_post_id, "visual_representation"),
            )
            stats["media_sources"] += 1
        for uid in component_underlying:
            for post_id in component:
                con.execute(
                    """INSERT OR IGNORE INTO source_memberships
                       (underlying_source_id,evidence_type,evidence_id,mention_post_id,relation_type)
                       VALUES (?,'post',?,?, 'mentions')""", (uid, post_id, post_id),
                )
                stats["social_mentions"] += 1
    con.commit()
    return stats


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--db", default=DB_PATH)
    ap.add_argument("--resolve-redirects", action="store_true")
    ap.add_argument("--post-ids")
    args = ap.parse_args()
    init_db(args.db)
    con = sqlite3.connect(args.db, timeout=120)
    ids = [x.strip() for x in (args.post_ids or "").split(",") if x.strip()]
    stats = build_source_map(con, resolve_redirects=args.resolve_redirects, post_ids=ids or None)
    stats["independent_evidence"] = con.execute("SELECT COUNT(*) FROM underlying_sources").fetchone()[0]
    con.close()
    print(json.dumps(stats, ensure_ascii=False, sort_keys=True))


if __name__ == "__main__":
    main()
