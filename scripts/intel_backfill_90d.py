"""大V情报系统 — 回填指定天数历史 (生产基线/缺口修复)

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
- 生产 KOL 并发 (ThreadPoolExecutor), 每个 try/except 独立
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
from signalboard.scraper import (
    _call_actor,
    build_run_input,
    default_field_map,
    _item_to_raw_post,
)
from intel_incremental_scrape import KOL_TEST
from email.utils import parsedate_to_datetime

DB_PATH = "/workspace/data/signalboard_full.db"

log = logging.getLogger("intel_backfill")
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(name)s] %(message)s")

# 与每日增量抓取共用同一份 8 人生产名单，避免新增人物只进看板、不进回填。
KOL_LIST = KOL_TEST


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
            "SELECT total_scraped, last_tweet_id, last_tweet_published_at "
            "FROM scrape_state WHERE handle = ?", (handle,)
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
            # 历史回填窗口可能早于当前增量状态；状态水位只能向前，不能回退。
            current_id = existing[1] or ""
            current_pub = existing[2] or ""
            if current_pub and current_pub >= last_tweet_published_at:
                last_tweet_id = current_id
                last_tweet_published_at = current_pub
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
    run_id: Optional[str] = None,
    since_date_override: Optional[date] = None,
    until_date_override: Optional[date] = None,
) -> Dict[str, Any]:
    """对单 KOL 做 90 天回填, 复用模块1 增量逻辑, 但 since = today - 90d (强制覆盖)。"""
    handle = kol["handle"]
    source_id = kol["source_id"]
    platform = kol["platform"]

    state = get_incremental_state(handle)
    today = date.today()
    since_date = since_date_override or (today - timedelta(days=since_days))
    # X 的 until 是排他边界；必须传明天才能覆盖今天。
    until_date = until_date_override or (today + timedelta(days=1))

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

    # 调 Apify，或复用已完成 run 的 dataset（失败续跑不重复计费）。
    try:
        if run_id:
            from apify_client import ApifyClient

            client = ApifyClient(apify_token)
            run = client.run(run_id).get()
            if isinstance(run, dict):
                dataset_id = run.get("defaultDatasetId") or run.get("default_dataset_id")
            else:
                dataset_id = getattr(run, "default_dataset_id", None)
            if not dataset_id:
                raise RuntimeError(f"Apify run {run_id} 没有 defaultDatasetId")
            items = list(client.dataset(dataset_id).iterate_items())
            log.info("[%s] 复用 Apify run %s 的 dataset", handle, run_id)
        else:
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
            # 即使是幂等命中，也用本次数据修复状态水位；但 upsert_incremental_state
            # 会再与现有状态取较新者，历史窗口不会把水位回退。
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

    # 算请求窗口内的实际覆盖；即使本轮全是幂等命中，也必须报告现有覆盖。
    with get_conn(DB_PATH) as conn:
        dates = conn.execute(
            "SELECT DISTINCT substr(published_at, 1, 10) FROM raw_posts "
            "WHERE source_id = ? AND published_at >= ? "
            "ORDER BY published_at DESC",
            (source_id, f"{since_date.isoformat()}T00:00:00+00:00"),
        ).fetchall()
        actual_days = len(dates)
        earliest = dates[-1][0] if dates else None
        latest = dates[0][0] if dates else None

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
    parser = argparse.ArgumentParser(description="大V情报 — 8 KOL 历史回填")
    parser.add_argument("--since-days", type=int, default=90, help="回填天数 (默认 90)")
    parser.add_argument(
        "--kol", default="all",
        help="单 KOL handle（必须在生产8人名单中），默认 all",
    )
    parser.add_argument("--max-per-window", type=int, default=5000, help="Apify maxItems per window")
    parser.add_argument(
        "--run-id",
        default="",
        help="复用已完成的 Apify actor run dataset，避免失败续跑时再次抓取计费",
    )
    parser.add_argument("--since-date", help="精确回填起始日 YYYY-MM-DD（覆盖 --since-days）")
    parser.add_argument("--until-date", help="精确排他结束日 YYYY-MM-DD")
    parser.add_argument("--apify-token", default=os.environ.get("APIFY_TOKEN", ""))
    parser.add_argument("--dry-run", action="store_true", help="只跑输入构建, 不真调 Apify")
    args = parser.parse_args()
    since_override = date.fromisoformat(args.since_date) if args.since_date else None
    until_override = date.fromisoformat(args.until_date) if args.until_date else None
    if (since_override is None) != (until_override is None):
        parser.error("--since-date 与 --until-date 必须同时提供")
    if since_override and since_override >= until_override:
        parser.error("--since-date 必须早于 --until-date")

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
                end=today + timedelta(days=1),
                max_per_month=args.max_per_window,
                sort="Latest",
                disable_maximization=True,
            )
            print(f"\n[{kol['handle']}] dry-run searchTerms: {run_input['searchTerms']}")
        return

    # 并发跑生产 KOL (最多4并发, 各自独立, 失败不阻塞)
    results: List[Dict[str, Any]] = []
    with ThreadPoolExecutor(max_workers=4) as pool:
        futures = {
            pool.submit(
                backfill_one_kol,
                kol,
                args.since_days,
                args.apify_token,
                args.max_per_window,
                args.run_id or None,
                since_override,
                until_override,
            ): kol
            for kol in kol_list
        }
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
    failures = [r for r in results if r.get("error")]
    if failures:
        raise SystemExit(f"{len(failures)} 个账号回填失败: {[r['handle'] for r in failures]}")


if __name__ == "__main__":
    main()
