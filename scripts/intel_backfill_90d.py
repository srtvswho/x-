"""大V情报系统 — 回填 90 天历史 (模块1 准备: 基线建立)

用户硬规则:
- 复用现有 signalboard 管道 (scraper._call_actor / repository.upsert_raw_post)
- 日期: parsedate_to_datetime / ISO 8601, 绝不用 [:10]
- Apify searchTerms 嵌 since/until 单字符串
- 失败处理: 某大V失败不阻塞其他
- 增量: 走 upsert 幂等去重

回填策略:
- since = today - 90 days
- until = today
- maxItems: 跟 Serenity 全量 14 月用 3000/月, 90 天 ≈ 3 个月, 拿 5000/大V 应该够
- 4 大V 并发 (ThreadPoolExecutor), 每个 try/except 独立
"""
from __future__ import annotations

import argparse
import json
import logging
import os
import sys
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import date, datetime, timedelta, timezone
from typing import Any, Dict, List, Optional

# 复用现有 signalboard 管道
sys.path.insert(0, "/workspace")
from signalboard.db import get_conn, init_db
from signalboard.repository import upsert_raw_post
from signalboard.models import Platform
from signalboard.scraper import (
    _call_actor,
    build_run_input,
    default_field_map,
    _item_to_raw_post,
)
from email.utils import parsedate_to_datetime

DB_PATH = "/workspace/data/signalboard_full.db"

log = logging.getLogger("intel_backfill")
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(name)s] %(message)s")

# 4 大V (正式回填)
KOL_LIST = [
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


def get_incremental_state(handle: str) -> Dict[str, Any]:
    """读 scrape_state 的 last_tweet_published_at, 用于增量起点。"""
    with get_conn(DB_PATH) as conn:
        row = conn.execute(
            "SELECT last_tweet_id, last_tweet_published_at, last_fetched_at "
            "FROM scrape_state WHERE handle = ?",
            (handle,),
        ).fetchone()
        if row is None:
            return {"exists": False, "last_tweet_published_at": None}
        return {
            "exists": True,
            "last_tweet_id": row[0],
            "last_tweet_published_at": row[1],
            "last_fetched_at": row[2],
        }


def upsert_incremental_state(
    handle: str, last_tweet_id: str, last_tweet_published_at: str, new_count: int
) -> None:
    """回填后更新 scrape_state。"""
    now_iso = datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")
    with get_conn(DB_PATH) as conn:
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
                (handle, new_count, now_iso, last_tweet_id, last_tweet_published_at, now_iso),
            )
        else:
            new_total = (existing[0] or 0) + new_count
            conn.execute(
                """
                UPDATE scrape_state
                SET total_scraped = ?, last_updated = ?,
                    last_tweet_id = ?, last_tweet_published_at = ?, last_fetched_at = ?
                WHERE handle = ?
                """,
                (new_total, now_iso, last_tweet_id, last_tweet_published_at, now_iso, handle),
            )
        conn.commit()


def backfill_one_kol(
    kol: Dict[str, str],
    since_days: int,
    apify_token: str,
    max_per_window: int,
) -> Dict[str, Any]:
    """对单 KOL 做 90 天回填, 复用模块1 增量逻辑, 但 since = today - 90d (强制覆盖)。"""
    handle = kol["handle"]
    source_id = kol["source_id"]
    platform = kol["platform"]

    state = get_incremental_state(handle)
    today = date.today()
    since_date = today - timedelta(days=since_days)
    until_date = today

    log.info("[%s] 回填 %d 天 since=%s until=%s (DB 已 last_tweet_published_at=%s)",
             handle, since_days, since_date, until_date, state.get("last_tweet_published_at"))

    # 用 build_run_input 构造 (searchTerms 嵌 since/until)
    run_input = build_run_input(
        handle=handle,
        start=since_date,
        end=until_date,
        max_per_month=max_per_window,
        sort="Latest",
        disable_maximization=True,
    )
    log.info("[%s] searchTerms = %s", handle, run_input["searchTerms"])
    log.info("[%s] maxItems = %d", handle, run_input["maxItems"])

    captured_at = datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")
    field_map = default_field_map()

    # 调 Apify
    try:
        items = _call_actor(run_input, apify_token)
    except Exception as e:
        log.error("[%s] Apify 调用失败: %s", handle, e)
        return {"handle": handle, "fetched": 0, "new_persisted": 0, "error": str(e)}

    log.info("[%s] actor 返 %d items", handle, len(items))

    new_persisted = 0
    existing_skipped = 0
    skipped_sentinel = 0
    parse_errors = []
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
            continue
        # 严格 since_days 过滤 (用 today - since_days 作 cutoff, 不切天)
        cutoff_iso = datetime.combine(since_date, datetime.min.time(), tzinfo=timezone.utc) \
            .replace(microsecond=0).isoformat().replace("+00:00", "Z")
        if post.published_at < cutoff_iso:
            continue

        # upsert (幂等), 区分新插入 vs 已存在
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
            if is_new:
                if latest_pub is None or post.published_at > latest_pub:
                    latest_pub = post.published_at
                    latest_id = post.post_id
        except Exception as e:
            log.error("[%s] upsert 失败 post_id=%s: %s", handle, post.post_id, e)
            continue

    log.info("[%s] 新增 %d, 已存在 %d, 哨兵 %d, 解析错 %d",
             handle, new_persisted, existing_skipped, skipped_sentinel, len(parse_errors))

    # 更新 scrape_state (即使没新增, 也更新 last_tweet_published_at, 因为这次回填拿到了新数据)
    if latest_pub:
        upsert_incremental_state(handle, latest_id or "", latest_pub, new_persisted)

    # 算实际回填覆盖天数
    if new_persisted > 0:
        with get_conn(DB_PATH) as conn:
            dates = conn.execute(
                "SELECT DISTINCT substr(published_at, 1, 10) FROM raw_posts "
                "WHERE source_id = ? ORDER BY published_at DESC LIMIT 90",
                (source_id,),
            ).fetchall()
            actual_days = len(dates)
            earliest = dates[-1][0] if dates else None
            latest = dates[0][0] if dates else None
    else:
        actual_days = 0
        earliest = None
        latest = None

    return {
        "handle": handle,
        "source_id": source_id,
        "fetched": len(items),
        "new_persisted": new_persisted,
        "existing_skipped": existing_skipped,
        "skipped_sentinel": skipped_sentinel,
        "parse_errors": len(parse_errors),
        "since": since_date.isoformat(),
        "until": until_date.isoformat(),
        "latest_tweet_id": latest_id,
        "latest_tweet_published_at": latest_pub,
        "actual_days_covered": actual_days,
        "earliest_date": earliest,
        "latest_date": latest,
        "error": None,
    }


def main():
    parser = argparse.ArgumentParser(description="大V情报 — 4 KOL × 90 天回填")
    parser.add_argument("--since-days", type=int, default=90, help="回填天数 (默认 90)")
    parser.add_argument(
        "--kol", default="all",
        help="单 KOL handle (jukan05 / aleabitoreddit / zephyr_z9 / austinsemis), 默认 all",
    )
    parser.add_argument("--max-per-window", type=int, default=5000, help="Apify maxItems per window")
    parser.add_argument("--apify-token", default=os.environ.get("APIFY_TOKEN", ""))
    parser.add_argument("--dry-run", action="store_true", help="只跑输入构建, 不真调 Apify")
    args = parser.parse_args()

    if not args.apify_token and not args.dry_run:
        log.error("需要 APIFY_TOKEN (env 或 --apify-token)")
        sys.exit(1)

    # 选 KOL
    if args.kol == "all":
        kol_list = KOL_LIST
    else:
        kol_list = [k for k in KOL_LIST if k["handle"] == args.kol]
        if not kol_list:
            log.error("KOL '%s' 不在 KOL_LIST", args.kol)
            sys.exit(1)

    init_db(DB_PATH)

    if args.dry_run:
        for kol in kol_list:
            today = date.today()
            since_date = today - timedelta(days=args.since_days)
            run_input = build_run_input(
                handle=kol["handle"],
                start=since_date,
                end=today,
                max_per_month=args.max_per_window,
                sort="Latest",
                disable_maximization=True,
            )
            print(f"\n[{kol['handle']}] dry-run searchTerms: {run_input['searchTerms']}")
        return

    # 并发跑 4 大V (max_workers=4, 各自独立, 失败不阻塞)
    results: List[Dict[str, Any]] = []
    with ThreadPoolExecutor(max_workers=4) as pool:
        futures = {pool.submit(backfill_one_kol, kol, args.since_days, args.apify_token, args.max_per_window): kol for kol in kol_list}
        for fut in as_completed(futures):
            kol = futures[fut]
            try:
                r = fut.result()
                results.append(r)
            except Exception as e:
                log.error("[%s] 任务异常: %s", kol["handle"], e)
                results.append({
                    "handle": kol["handle"],
                    "error": str(e),
                    "new_persisted": 0,
                })

    # 按 handle 排序输出
    results.sort(key=lambda r: r["handle"])
    print("\n=== 回填结果 ===")
    print(json.dumps(results, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()