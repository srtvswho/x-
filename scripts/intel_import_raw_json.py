"""大V情报 — 导入历史 raw json 到 DB (模块1 基线 — A 部分)

用户硬规则:
- 用 parsedate_to_datetime 转 ISO 8601 (绝不用 [:10])
- 按推文 id 去重
- 走 signalboard 现有落库管道 (upsert_raw_post, 幂等)
- source_id: tw_jukan05 / tw_aleabitoreddit / tw_zephyr_z9 / tw_austinsemis

3 大V 文件清单 (按用户盘点结果):
- jukan05: 5 个 p4p10d_x 切片
- austinsemis: 2 个 raw 文件
- zephyr_z9: 5 个 raw_2024-* + 1 个 raw_2026Q2 (有 999 重复, 按 id 去重)
"""
from __future__ import annotations

import json
import os
import sys
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timezone
from email.utils import parsedate_to_datetime

# 复用现有 signalboard 管道
sys.path.insert(0, "/workspace")
from signalboard.db import get_conn, init_db
from signalboard.repository import upsert_raw_post
from signalboard.models import Platform
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
        "/workspace/logs/p5_industry_judgments/raw_zephyr_2026Q2.json",  # 999 重, 按 id 去重
    ],
}

SOURCE_ID = {
    "jukan05": "tw_jukan05",
    "austinsemis": "tw_austinsemis",
    "zephyr_z9": "tw_zephyr_z9",
}


def to_iso(created_at_str):
    """RFC 2822 → ISO 8601 (parsedate_to_datetime, 不用 [:10])"""
    if not created_at_str:
        return None
    try:
        dt = parsedate_to_datetime(created_at_str)
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        else:
            dt = dt.astimezone(timezone.utc)
        return dt.replace(microsecond=0).isoformat().replace("+00:00", "Z")
    except Exception as e:
        return None


def import_kol(handle: str, file_list: list) -> dict:
    source_id = SOURCE_ID[handle]
    field_map = default_field_map()
    captured_at = datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")

    # 1. 读所有 file, 合并, 按 id 去重
    all_tweets = {}
    file_stats = []
    for fn in file_list:
        if not os.path.exists(fn):
            file_stats.append({"file": os.path.basename(fn), "exists": False})
            continue
        try:
            with open(fn) as f:
                tweets = json.load(f)
        except Exception as e:
            file_stats.append({"file": os.path.basename(fn), "error": str(e)})
            continue
        n_added = 0
        for t in tweets:
            tid = t.get("id")
            if tid:
                if tid not in all_tweets:
                    all_tweets[tid] = t
                    n_added += 1
        file_stats.append({"file": os.path.basename(fn), "tweets": len(tweets), "new_ids": n_added})

    # 2. 转 RawPost, 调 upsert_raw_post
    new_count = 0
    existing_count = 0
    parse_errors = 0
    latest_pub = None
    latest_id = None

    for tid, item in all_tweets.items():
        try:
            post = _item_to_raw_post(item, field_map, source_id, captured_at)
        except Exception as e:
            parse_errors += 1
            continue
        if not post.published_at:
            continue
        # 注: _item_to_raw_post 内部已用 to_utc_iso 转 ISO, 不要二次 to_iso (会报 invalid)
        # 验证 ISO 格式用 fromisoformat
        try:
            s = post.published_at
            if s.endswith("Z"): s = s[:-1] + "+00:00"
            datetime.fromisoformat(s)
        except Exception:
            parse_errors += 1
            continue
        # upsert
        try:
            with get_conn(DB_PATH) as conn:
                row = conn.execute("SELECT 1 FROM raw_posts WHERE post_id=?", (post.post_id,)).fetchone()
                is_new = row is None
                upsert_raw_post(post, DB_PATH)
                if is_new:
                    new_count += 1
                else:
                    existing_count += 1
                if is_new:
                    if latest_pub is None or post.published_at > latest_pub:
                        latest_pub = post.published_at
                        latest_id = post.post_id
        except Exception as e:
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
        "file_count": len(file_list),
        "raw_unique_ids": len(all_tweets),
        "new_persisted": new_count,
        "existing_skipped": existing_count,
        "parse_errors": parse_errors,
        "latest_tweet_id": latest_id,
        "latest_tweet_published_at": latest_pub,
        "file_stats": file_stats,
    }


if __name__ == "__main__":
    init_db(DB_PATH)
    print("=== 导入 3 大V 历史 raw json → DB ===")
    print(f"DB: {DB_PATH}\n")
    results = []
    with ThreadPoolExecutor(max_workers=3) as pool:
        futs = {pool.submit(import_kol, h, f): h for h, f in KOL_FILES.items()}
        for fut in as_completed(futs):
            h = futs[fut]
            try:
                r = fut.result()
                results.append(r)
            except Exception as e:
                results.append({"handle": h, "error": str(e)})
    results.sort(key=lambda r: r["handle"])
    print(json.dumps(results, indent=2, ensure_ascii=False))