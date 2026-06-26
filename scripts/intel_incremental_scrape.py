"""大V情报系统 — 模块1: 增量抓取 + 落库 (test version)

设计原则 (用户硬规则):
- 复用现有 signalboard 管道 (scraper._call_actor / repository.upsert_raw_post / db.init_db)
- 日期用 parsedate_to_datetime → to_utc_iso, 绝对不用 createdAt[:10]
- Apify searchTerms 单字符串嵌 since/until (顶层字段会被忽略)
- post_id 去重 (upsert 幂等)
- 失败要处理: 某个大V失败不让整批崩, 记录失败 + 可重试

增量机制:
- scrape_state 表加 3 个字段: last_tweet_id, last_tweet_published_at, last_fetched_at
- 首次抓 (无 last_tweet_published_at): since = today - 7d (保险)
- 增量抓: since = last_tweet_published_at
- 抓完更新 3 个字段

数据持久化:
- DB: /workspace/data/signalboard_full.db (NFS 持久)
- 不写 /tmp, 不写本地非持久路径
"""
from __future__ import annotations

import argparse
import json
import logging
import os
import sys
from dataclasses import dataclass, field
from datetime import date, datetime, timedelta, timezone
from typing import Any, Dict, List, Optional

from email.utils import parsedate_to_datetime

# 复用现有 signalboard 管道
sys.path.insert(0, "/workspace")
from signalboard.db import get_conn, init_db
from signalboard.repository import upsert_raw_post
from signalboard.models import RawPost, Platform
from signalboard.scraper import (
    ACTOR_ID,
    _call_actor,
    build_run_input,
    default_field_map,
    _item_to_raw_post,
)

DB_PATH = "/workspace/data/signalboard_full.db"

log = logging.getLogger("intel_scrape")
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(name)s] %(message)s")

# ---------------------------------------------------------------------------
# 大V 列表 (模块1 测试: 只 Austin)
# ---------------------------------------------------------------------------
# 完整 4 人列表等用户 GitHub 配好 + 增量验证后再加
KOL_TEST = [
    {
        "handle": "jukan05",
        "source_id": "tw_jukan05",
        "platform": Platform.TWITTER.value,
    },
    {
        "handle": "aleabitoreddit",
        "source_id": "tw_aleabitoreddit",
        "platform": Platform.TWITTER.value,
    },
    {
        "handle": "zephyr_z9",
        "source_id": "tw_zephyr_z9",
        "platform": Platform.TWITTER.value,
    },
    {
        "handle": "austinsemis",
        "source_id": "tw_austinsemis",
        "platform": Platform.TWITTER.value,
    },
]

# ---------------------------------------------------------------------------
# 日期工具 (硬规则: parsedate_to_datetime, 不用 [:10])
# ---------------------------------------------------------------------------
def to_utc_iso(s: Any) -> str:
    """把 apidojo tweet-scraper 输出的 createdAt (RFC 2822) 转成 ISO 8601 UTC。

    硬规则: 不用 s[:10] (那会切成 "Sun Apr 12")。用 email.utils.parsedate_to_datetime。
    """
    if not s:
        return ""
    try:
        dt = parsedate_to_datetime(str(s))
        if dt is None:
            return ""
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        else:
            dt = dt.astimezone(timezone.utc)
        # microsecond → 去掉 + 末尾 'Z'
        return dt.replace(microsecond=0).isoformat().replace("+00:00", "Z")
    except Exception as e:
        log.warning("to_utc_iso 失败 (input=%r): %s", s, e)
        return ""


# ---------------------------------------------------------------------------
# 增量状态查询
# ---------------------------------------------------------------------------
def get_incremental_state(handle: str) -> Dict[str, Any]:
    """读 scrape_state 的 last_tweet_published_at, 用于 since 时间窗。"""
    with get_conn(DB_PATH) as conn:
        row = conn.execute(
            "SELECT last_tweet_id, last_tweet_published_at, last_fetched_at "
            "FROM scrape_state WHERE handle = ?",
            (handle,),
        ).fetchone()
        if row is None:
            return {"exists": False, "last_tweet_id": None, "last_tweet_published_at": None}
        return {
            "exists": True,
            "last_tweet_id": row[0],
            "last_tweet_published_at": row[1],
            "last_fetched_at": row[2],
        }


def upsert_incremental_state(
    handle: str,
    last_tweet_id: str,
    last_tweet_published_at: str,
    fetched_count: int,
) -> None:
    """抓完后更新 scrape_state 的增量字段 + last_updated + total_scraped 增量。"""
    now_iso = datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")
    with get_conn(DB_PATH) as conn:
        # 先看是否存在
        existing = conn.execute(
            "SELECT total_scraped FROM scrape_state WHERE handle = ?", (handle,)
        ).fetchone()
        if existing is None:
            conn.execute(
                """
                INSERT INTO scrape_state (
                    handle, last_run_id, months_done, total_scraped, last_updated,
                    last_tweet_id, last_tweet_published_at, last_fetched_at
                ) VALUES (?, NULL, '[]', ?, ?, ?, ?, ?)
                """,
                (
                    handle,
                    fetched_count,
                    now_iso,
                    last_tweet_id,
                    last_tweet_published_at,
                    now_iso,
                ),
            )
        else:
            new_total = (existing[0] or 0) + fetched_count
            conn.execute(
                """
                UPDATE scrape_state
                SET total_scraped = ?,
                    last_updated = ?,
                    last_tweet_id = ?,
                    last_tweet_published_at = ?,
                    last_fetched_at = ?
                WHERE handle = ?
                """,
                (
                    new_total,
                    now_iso,
                    last_tweet_id,
                    last_tweet_published_at,
                    now_iso,
                    handle,
                ),
            )
        conn.commit()


# ---------------------------------------------------------------------------
# 增量抓取单 KOL
# ---------------------------------------------------------------------------
def scrape_one_kol(kol: Dict[str, str], apify_token: str, dry_run: bool = False) -> Dict[str, Any]:
    """对单 KOL 做增量抓取, 返回 {fetched, persisted, since, until, error, sample}。"""
    handle = kol["handle"]
    source_id = kol["source_id"]
    platform = kol["platform"]

    state = get_incremental_state(handle)
    today = date.today()

    if state["last_tweet_published_at"]:
        # 增量: since = last_tweet_published_at (精确到秒, 不切天 — 否则会重抓同一天的)
        try:
            s = state["last_tweet_published_at"]
            if s.endswith("Z"):
                s = s[:-1] + "+00:00"
            since_dt = datetime.fromisoformat(s)
            since_date = since_dt.date()
            # 精确 since 时间戳 (用于秒级去重判断, 不传给 Apify)
            since_iso = s
            log.info("[%s] 增量 since=%s (last_tweet_published_at=%s)", handle, since_date, state["last_tweet_published_at"])
        except Exception as e:
            log.warning("[%s] 解析 last_tweet_published_at=%r 失败 (%s), 退到 today-7d",
                        handle, state["last_tweet_published_at"], e)
            since_date = today - timedelta(days=7)
            since_iso = None
    else:
        # 首次: since = today - 7d
        since_date = today - timedelta(days=7)
        since_iso = None
        log.info("[%s] 首次 since=%s (无 last_tweet_published_at)", handle, since_date)

    until_date = today

    # 用现有 build_run_input — searchTerms 嵌 since/until 在单字符串
    run_input = build_run_input(
        handle=handle,
        start=since_date,
        end=until_date,
        max_per_month=500,
        sort="Latest",
        disable_maximization=True,
    )

    log.info("[%s] searchTerms = %s", handle, run_input["searchTerms"])
    log.info("[%s] maxItems = %d, sort = %s, disableMaximization = %s",
             handle, run_input["maxItems"], run_input["sort"], run_input["disableMaximization"])

    if dry_run:
        return {
            "handle": handle,
            "fetched": 0,
            "persisted": 0,
            "since": since_date.isoformat(),
            "until": until_date.isoformat(),
            "error": None,
            "sample": [],
            "dry_run": True,
        }

    # 调 Apify
    captured_at = datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")
    field_map = default_field_map()

    try:
        items = _call_actor(run_input, apify_token)
    except Exception as e:
        log.error("[%s] Apify 调用失败: %s", handle, e)
        return {
            "handle": handle,
            "fetched": 0,
            "persisted": 0,
            "since": since_date.isoformat(),
            "until": until_date.isoformat(),
            "error": str(e),
            "sample": [],
        }

    log.info("[%s] actor 返 %d items", handle, len(items))

    # item → RawPost → upsert
    # 增量核心: 如果 last_tweet_published_at 已存在, 用 published_at 严格 > 那个时间戳过滤
    # (避免 since_date 切天后的 "同一天重抓" 问题)
    new_persisted = 0
    existing_skipped = 0
    skipped_sentinel = 0
    parse_errors = []
    sample: List[Dict[str, Any]] = []

    # 找最新 (按 published_at 排序, 拿最大)
    latest_id: Optional[str] = None
    latest_pub: Optional[str] = None

    for item in items:
        if not isinstance(item, dict) or item.get("noResults") is True:
            skipped_sentinel += 1
            continue
        try:
            post = _item_to_raw_post(item, field_map, source_id, captured_at)
        except Exception as e:
            parse_errors.append({"item_id": item.get("id"), "err": str(e)})
            continue
        if not post.published_at:
            log.warning("[%s] post_id=%s 缺 published_at, 跳过", handle, post.post_id)
            continue

        # 增量过滤: 跳过 published_at <= last_tweet_published_at 的 (已经落库)
        if since_iso and post.published_at <= since_iso:
            existing_skipped += 1
            continue

        # 落库 (幂等 — 如果 post_id 已存在, UPDATE 不算 "new")
        # 用 "新插入 vs 已存在" 区分
        try:
            with get_conn(DB_PATH) as conn:
                row = conn.execute(
                    "SELECT 1 FROM raw_posts WHERE post_id = ?", (post.post_id,)
                ).fetchone()
                is_new = row is None
                upsert_raw_post(post, DB_PATH)
                if is_new:
                    new_persisted += 1
                else:
                    existing_skipped += 1
        except Exception as e:
            log.error("[%s] upsert 失败 post_id=%s: %s", handle, post.post_id, e)
            continue

        # 收集最新 (只算 new, 不算 existing)
        if is_new:
            if latest_pub is None or post.published_at > latest_pub:
                latest_pub = post.published_at
                latest_id = post.post_id

        # 收集样本 (前 3 条 new)
        if is_new and len(sample) < 3:
            sample.append({
                "post_id": post.post_id,
                "published_at": post.published_at,
                "raw_text_excerpt": post.raw_text[:120] if post.raw_text else "",
            })

    log.info("[%s] 新增 %d 条, 已存在跳过 %d, 哨兵跳过 %d, 解析错 %d",
             handle, new_persisted, existing_skipped, skipped_sentinel, len(parse_errors))

    # 更新 scrape_state (不管有没有 new, 都要更新 last_fetched_at — cron 跑过的证据)
    # 但 last_tweet_published_at 只有 new > 0 才覆盖 (避免后退)
    if new_persisted > 0 and latest_pub:
        upsert_incremental_state(handle, latest_id or "", latest_pub, new_persisted)
    elif new_persisted == 0:
        # 只更新 last_fetched_at, 不动 last_tweet_published_at
        now_iso = datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")
        with get_conn(DB_PATH) as conn:
            existing = conn.execute(
                "SELECT total_scraped FROM scrape_state WHERE handle=?", (handle,)
            ).fetchone()
            if existing is None:
                # scrape_state 还没建 — 用 INSERT
                conn.execute(
                    """INSERT INTO scrape_state
                       (handle, last_run_id, months_done, total_scraped, last_updated,
                        last_tweet_id, last_tweet_published_at, last_fetched_at)
                       VALUES (?, NULL, '[]', 0, ?, NULL, NULL, ?)""",
                    (handle, now_iso, now_iso),
                )
            else:
                conn.execute(
                    """UPDATE scrape_state
                       SET last_updated=?, last_fetched_at=?
                       WHERE handle=?""",
                    (now_iso, now_iso, handle),
                )
            conn.commit()

    return {
        "handle": handle,
        "fetched": len(items),
        "new_persisted": new_persisted,
        "existing_skipped": existing_skipped,
        "skipped_sentinel": skipped_sentinel,
        "parse_errors": len(parse_errors),
        "since": since_date.isoformat(),
        "since_iso": since_iso,
        "until": until_date.isoformat(),
        "last_tweet_id": latest_id,
        "last_tweet_published_at": latest_pub,
        "error": None,
        "sample": sample,
        "first_parse_errors": parse_errors[:3],
    }


# ---------------------------------------------------------------------------
# main
# ---------------------------------------------------------------------------
def main():
    parser = argparse.ArgumentParser(description="大V情报 — 模块1: 增量抓取 + 落库")
    parser.add_argument(
        "--kol", default="austinsemis",
        help="handle (默认 austinsemis, 模块1 测试)",
    )
    parser.add_argument("--dry-run", action="store_true", help="只跑输入构建, 不真调 Apify")
    parser.add_argument("--apify-token", default=os.environ.get("APIFY_TOKEN", ""))
    args = parser.parse_args()

    if not args.apify_token and not args.dry_run:
        log.error("需要 APIFY_TOKEN (env 或 --apify-token)")
        sys.exit(1)

    # 找大V 配置
    kol = next((k for k in KOL_TEST if k["handle"] == args.kol), None)
    if kol is None:
        log.error("KOL '%s' 不在 KOL_TEST (模块1 测试列表)", args.kol)
        sys.exit(1)

    # 确保 DB schema 最新
    init_db(DB_PATH)

    # 抓
    result = scrape_one_kol(kol, args.apify_token, dry_run=args.dry_run)

    print("\n=== 结果 ===")
    print(json.dumps(result, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()