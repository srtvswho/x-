#!/usr/bin/env python3
"""Build Post/Media/External Source graph from newly captured X payloads."""
from __future__ import annotations

import argparse
import json
import sqlite3
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from signalboard.db import init_db
from signalboard.research_graph import ingest_post_graph

DB_PATH = "/workspace/data/signalboard_full.db"


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--db", default=DB_PATH)
    parser.add_argument("--since", required=True)
    parser.add_argument("--limit", type=int, default=0)
    args = parser.parse_args()

    init_db(args.db)
    con = sqlite3.connect(args.db, timeout=120)
    sql = """
        SELECT rp.post_id, rp.raw_json
        FROM raw_posts rp
        WHERE rp.published_at >= ?
          AND rp.raw_json IS NOT NULL
          AND rp.source_id NOT LIKE 'ctx_%'
          AND NOT EXISTS (
              SELECT 1 FROM post_graph_memberships pg
              WHERE pg.root_post_id=rp.post_id AND pg.post_id=rp.post_id
          )
        ORDER BY rp.published_at ASC
    """
    params: list[object] = [args.since if "T" in args.since else f"{args.since}T00:00:00+00:00"]
    if args.limit:
        sql += " LIMIT ?"
        params.append(args.limit)
    rows = con.execute(sql, params).fetchall()
    totals = {"roots": 0, "invalid": 0, "nodes": 0, "edges": 0, "pending": 0, "media": 0, "external_urls": 0}
    for post_id, raw in rows:
        try:
            payload = json.loads(raw)
            if not isinstance(payload, dict):
                raise ValueError("raw_json is not an object")
            stats = ingest_post_graph(con, args.db, post_id, payload)
            totals["roots"] += 1
            for key, value in stats.items():
                totals[key] += value
            con.commit()
        except Exception as exc:
            con.rollback()
            totals["invalid"] += 1
            print(f"warning: graph ingest failed post_id={post_id}: {type(exc).__name__}: {exc}")
    con.close()
    print(json.dumps(totals, ensure_ascii=False, sort_keys=True))


if __name__ == "__main__":
    main()
