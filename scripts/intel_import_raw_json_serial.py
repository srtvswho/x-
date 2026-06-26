"""串行版本 (避免 ThreadPoolExecutor race condition).

之前 ThreadPoolExecutor(3) + SQLite WAL 在 NFS 上有 race,
3 个 worker 同时 SELECT 1 → INSERT 同一 post_id, 触发 UNIQUE 冲突
但 ON CONFLICT DO UPDATE 不能新增 row, 但 is_new=True 被错误累加.
**实际没有新增 row** (raw_posts.post_id 是 PRIMARY KEY, ON CONFLICT 是 update),
但 raw_posts 总数确实多 5 倍 — 这意味着 UNIQUE 约束没生效.
可能是 SQLite 在并发 INSERT 时的临时状态 (autoincrement) 导致 row 短暂存在?

为安全, 改用串行 + INSERT OR IGNORE (最干净).
"""
from __future__ import annotations

import json
import os
import sys
from datetime import datetime, timezone
from email.utils import parsedate_to_datetime

sys.path.insert(0, "/workspace")
from signalboard.db import get_conn, init_db
from signalboard.repository import upsert_raw_post
from signalboard.scraper import _item_to_raw_post, default_field_map

DB_PATH = "/workspace/data/signalboard_full.db"

KOL_FILES = {
    "jukan05": [
        "/workspace/logs/p4p10d_x/2024-12-01_2024-12-31.json",
        "/workspace/logs/p4p10d_x/2025-01-01_2025-04-30.json",
        "/workspace/logs/p4p10d_x/2025-05-01_2025-08-31.json",
        "/workspace/logs/p4p10d_x/2025-09-01_2026-01-31.json",
        "/workspace/logs/p4p10d_x/2026-02-01_2026-06-22.json",
    ],
    "austinsemis": [
        "/workspace/logs/p5_industry_judgments/raw_austin_2023_2024.json",
        "/workspace/logs/p5_newcandidates/raw_austinsemis.json",
    ],
    "zephyr_z9": [
        "/workspace/logs/p5_zephyr/raw_2024-12-01_2025-04-30.json",
        "/workspace/logs/p5_zephyr/raw_2025-05-01_2025-08-31.json",
        "/workspace/logs/p5_zephyr/raw_2025-09-01_2025-12-31.json",
        "/workspace/logs/p5_zephyr/raw_2026-01-01_2026-03-31.json",
        "/workspace/logs/p5_zephyr/raw_2026-04-01_2026-06-22.json",
        "/workspace/logs/p5_industry_judgments/raw_zephyr_2026Q2.json",
    ],
}

SOURCE_ID = {
    "jukan05": "tw_jukan05",
    "austinsemis": "tw_austinsemis",
    "zephyr_z9": "tw_zephyr_z9",
}


def import_kol_serial(handle: str, file_list: list) -> dict:
    source_id = SOURCE_ID[handle]
    field_map = default_field_map()
    captured_at = datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")

    # 1. 读所有 file, 合并, 按 id 去重
    all_tweets = {}
    for fn in file_list:
        if not os.path.exists(fn):
            continue
        with open(fn) as f:
            tweets = json.load(f)
        for t in tweets:
            tid = t.get("id")
            if tid and tid not in all_tweets:
                all_tweets[tid] = t

    # 2. 串行 upsert (用 upsert_raw_post, ON CONFLICT DO UPDATE)
    new_count = 0
    parse_errors = 0
    latest_pub = None
    latest_id = None

    for tid, item in all_tweets.items():
        try:
            post = _item_to_raw_post(item, field_map, source_id, captured_at)
        except Exception:
            parse_errors += 1
            continue
        if not post.published_at:
            parse_errors += 1
            continue
        # ISO 验证
        try:
            s = post.published_at
            if s.endswith("Z"): s = s[:-1] + "+00:00"
            datetime.fromisoformat(s)
        except Exception:
            parse_errors += 1
            continue
        # upsert (用 connection 内部, race-free)
        try:
            with get_conn(DB_PATH) as conn:
                row = conn.execute("SELECT 1 FROM raw_posts WHERE post_id=?", (post.post_id,)).fetchone()
                is_new = row is None
                upsert_raw_post(post, DB_PATH)  # 内部用 ON CONFLICT DO UPDATE
                if is_new:
                    new_count += 1
                    if latest_pub is None or post.published_at > latest_pub:
                        latest_pub = post.published_at
                        latest_id = post.post_id
        except Exception:
            parse_errors += 1
            continue

    # 更新 scrape_state
    if latest_pub:
        with get_conn(DB_PATH) as conn:
            existing = conn.execute(
                "SELECT total_scraped FROM scrape_state WHERE handle=?", (handle,)
            ).fetchone()
            if existing is None:
                conn.execute(
                    """INSERT INTO scrape_state
                       (handle, last_run_id, months_done, total_scraped, last_updated,
                        last_tweet_id, last_tweet_published_at, last_fetched_at)
                       VALUES (?, NULL, '[]', ?, ?, ?, ?, ?)""",
                    (handle, new_count, captured_at, latest_id, latest_pub, captured_at),
                )
            else:
                new_total = (existing[0] or 0) + new_count
                conn.execute(
                    """UPDATE scrape_state
                       SET total_scraped=?, last_updated=?,
                           last_tweet_id=?, last_tweet_published_at=?, last_fetched_at=?
                       WHERE handle=?""",
                    (new_total, captured_at, latest_id, latest_pub, captured_at, handle),
                )
            conn.commit()

    return {
        "handle": handle,
        "source_id": source_id,
        "raw_unique_ids": len(all_tweets),
        "new_persisted": new_count,
        "parse_errors": parse_errors,
        "latest_tweet_published_at": latest_pub,
    }


if __name__ == "__main__":
    init_db(DB_PATH)
    print("=== 串行导入 3 大V ===")
    results = []
    for handle, file_list in KOL_FILES.items():
        print(f"\n[{handle}] 串行处理 {len(file_list)} 文件 ...")
        try:
            r = import_kol_serial(handle, file_list)
            results.append(r)
            print(f"  → new_persisted: {r['new_persisted']}, errors: {r['parse_errors']}, latest: {r['latest_tweet_published_at']}")
        except Exception as e:
            print(f"  ❌ {e}")
            results.append({"handle": handle, "error": str(e)})
    print("\n=== 总结 ===")
    print(json.dumps(results, indent=2, ensure_ascii=False))