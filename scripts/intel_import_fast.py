"""大V情报 — 快速导入 (INSERT OR IGNORE + 批量 commit)

为什么之前慢:
- upsert_raw_post 用 ON CONFLICT DO UPDATE, 每次重写 12 列 (raw_text 12KB) → IO 大
- ThreadPoolExecutor(3) + SQLite WAL 在 NFS 上 race → dup (jukan 翻 5 倍)

修法:
- 串行 (无 race)
- INSERT OR IGNORE (PRIMARY KEY 冲突时静默跳过, 不重写)
- 50/批 commit (减少 fsync 次数)
"""
from __future__ import annotations

import json
import os
import sqlite3
import sys
import time
from datetime import datetime, timezone
from email.utils import parsedate_to_datetime

sys.path.insert(0, "/workspace")
from signalboard.db import init_db
from signalboard.scraper import _item_to_raw_post, default_field_map

DB_PATH = "/workspace/data/signalboard_full.db"
BATCH_SIZE = 50

KOL_FILES = {
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
    "austinsemis": "tw_austinsemis",
    "zephyr_z9": "tw_zephyr_z9",
}


def import_kol_fast(handle: str, file_list: list) -> dict:
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
    print(f"  [{handle}] 合并 {len(file_list)} 文件 → {len(all_tweets)} unique id")

    # 2. 转 RawPost, 收集
    parse_errors = 0
    latest_pub = None
    latest_id = None
    posts_to_insert = []
    for tid, item in all_tweets.items():
        try:
            post = _item_to_raw_post(item, field_map, source_id, captured_at)
        except Exception:
            parse_errors += 1
            continue
        if not post.published_at:
            parse_errors += 1
            continue
        try:
            s = post.published_at
            if s.endswith("Z"): s = s[:-1] + "+00:00"
            datetime.fromisoformat(s)
        except Exception:
            parse_errors += 1
            continue

        posts_to_insert.append(post.to_row())
        if latest_pub is None or post.published_at > latest_pub:
            latest_pub = post.published_at
            latest_id = post.post_id

    print(f"  [{handle}] 待插 {len(posts_to_insert)} 条, parse_errors {parse_errors}")

    # 3. INSERT OR IGNORE, 批量 commit
    t0 = time.time()
    inserted = 0
    skipped = 0
    con = sqlite3.connect(DB_PATH, timeout=60)
    try:
        cur = con.cursor()
        cur.execute("BEGIN IMMEDIATE")
        for i, row in enumerate(posts_to_insert):
            try:
                cur.execute(
                    """INSERT OR IGNORE INTO raw_posts
                       (post_id, source_id, platform, published_at, captured_at,
                        raw_text, raw_url, raw_json, content_hash, is_deleted, archive_url)
                       VALUES (:post_id, :source_id, :platform, :published_at, :captured_at,
                               :raw_text, :raw_url, :raw_json, :content_hash, :is_deleted, :archive_url)""",
                    row,
                )
                if cur.rowcount > 0:
                    inserted += 1
                else:
                    skipped += 1
            except Exception as e:
                parse_errors += 1
            if (i + 1) % BATCH_SIZE == 0:
                con.commit()
                cur.execute("BEGIN IMMEDIATE")
        con.commit()
    finally:
        con.close()
    elapsed = time.time() - t0
    print(f"  [{handle}] 完成: inserted {inserted}, skipped {skipped}, errors {parse_errors}, {elapsed:.0f}s")

    # 4. 更新 scrape_state
    with sqlite3.connect(DB_PATH, timeout=30) as con:
        existing = con.execute(
            "SELECT total_scraped FROM scrape_state WHERE handle=?", (handle,)
        ).fetchone()
        if existing is None:
            con.execute(
                """INSERT INTO scrape_state
                   (handle, last_run_id, months_done, total_scraped, last_updated,
                    last_tweet_id, last_tweet_published_at, last_fetched_at)
                   VALUES (?, NULL, '[]', ?, ?, ?, ?, ?)""",
                (handle, inserted, captured_at, latest_id, latest_pub, captured_at),
            )
        else:
            new_total = (existing[0] or 0) + inserted
            con.execute(
                """UPDATE scrape_state
                   SET total_scraped=?, last_updated=?,
                       last_tweet_id=?, last_tweet_published_at=?, last_fetched_at=?
                   WHERE handle=?""",
                (new_total, captured_at, latest_id, latest_pub, captured_at, handle),
            )
        con.commit()

    return {
        "handle": handle,
        "source_id": source_id,
        "unique_ids": len(all_tweets),
        "inserted": inserted,
        "skipped_existing": skipped,
        "parse_errors": parse_errors,
        "elapsed_s": round(elapsed, 1),
        "latest_tweet_published_at": latest_pub,
    }


if __name__ == "__main__":
    init_db(DB_PATH)
    print(f"=== 快速导入 (INSERT OR IGNORE + 批量) → {DB_PATH} ===\n")
    results = []
    for handle, file_list in KOL_FILES.items():
        r = import_kol_fast(handle, file_list)
        results.append(r)
        print()
    print("=== 总结 ===")
    print(json.dumps(results, indent=2, ensure_ascii=False))