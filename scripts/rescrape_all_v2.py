"""全量重抓脚本 v3:用 disableMaximization=true + 单 conn 串行 upsert。

修 v1/v2 的问题:
- 单 conn 串行(NFS 不开新 conn)
- 用 ResponseCache 包装,避免重复 actor
- 跳过已成功重抓的月份(coverage 表里 persisted > 旧 persisted)
"""
import json
import os
import sys
import time
import shutil
import sqlite3
from datetime import date, datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))
from signalboard import upsert_raw_post, init_db
from signalboard.db import get_conn
from signalboard.scraper import (
    ResponseCache, _call_actor, build_run_input,
    init_scrape_state, record_coverage, default_field_map, _item_to_raw_post,
)

HANDLE = "aleabitoreddit"
DB_PATH = "data/signalboard_full.db"
CACHE_DIR = Path(".cache_full")
V1_BACKUP = Path(".cache_full_v1_backup")

if not V1_BACKUP.exists() and CACHE_DIR.exists():
    shutil.copytree(CACHE_DIR, V1_BACKUP)
    print(f"备份原 cache 到 {V1_BACKUP}", flush=True)


def month_bounds(month_str: str) -> tuple:
    y, m = map(int, month_str.split('-'))
    start = date(y, m, 1)
    end = date(y + 1, 1, 1) if m == 12 else date(y, m + 1, 1)
    return start, end


def main():
    token = os.environ.get("APIFY_TOKEN", "")
    if not token:
        print("ERROR: APIFY_TOKEN not set")
        sys.exit(1)

    # 单 conn, timeout 60
    db = sqlite3.connect(DB_PATH, timeout=60.0)
    db.execute("PRAGMA journal_mode=WAL")
    db.execute("PRAGMA synchronous=NORMAL")
    init_db(DB_PATH)
    init_scrape_state(DB_PATH)

    cache = ResponseCache(CACHE_DIR, enabled=True)
    fm = default_field_map()

    # 14 月(固定)
    months = [
        "2025-05", "2025-06", "2025-07", "2025-08", "2025-09", "2025-10",
        "2025-11", "2025-12", "2026-01", "2026-02", "2026-03", "2026-04",
        "2026-05", "2026-06",
    ]
    print(f"需处理 {len(months)} 月: {months[0]}..{months[-1]}", flush=True)

    # 旧 data
    old_data = {}
    for m in months:
        r = db.execute(
            "SELECT items_returned, items_persisted FROM coverage "
            "WHERE handle = ? AND window_start = ? AND depth = 0 AND subdivided = 0",
            (HANDLE, m + "-01"),
        ).fetchone()
        if r:
            old_data[m] = {"returned": r[0], "persisted": r[1]}

    # 当前 persisted(用于判断是否要重抓)
    def current_persisted(m: str) -> int:
        return db.execute(
            "SELECT count(*) FROM raw_posts WHERE substr(published_at, 1, 7) = ?",
            (m,),
        ).fetchone()[0]

    results = []
    for m_str in months:
        start, end = month_bounds(m_str)
        old = old_data.get(m_str, {"returned": 0, "persisted": 0})
        cur_p = current_persisted(m_str)

        # 不跳过:重抓所有月份,即使之前已抓过(actor 模式可能不同)

        # 调 actor
        run_input = build_run_input(HANDLE, start, end)
        key = ResponseCache._key(run_input)
        cache_file = CACHE_DIR / f"{key}.json"
        if cache_file.exists():
            with open(cache_file) as f:
                data = json.load(f)
            items = data.get("items", [])
            print(f"  ↻ {m_str}: 用 cache {cache_file.name} ({len(items)} 条)", flush=True)
        else:
            t0 = time.time()
            try:
                items = _call_actor(run_input, token)
            except Exception as e:
                print(f"  ✗ {m_str} actor 失败: {e}", flush=True)
                results.append({"month": m_str, "status": "FAILED", "error": str(e)})
                continue
            elapsed = time.time() - t0
            cache_file.write_text(json.dumps(
                {"items": items, "run_input": run_input}, ensure_ascii=False))
            print(f"  ✓ {m_str}: actor 返 {len(items)} 条, 耗时 {elapsed:.1f}s", flush=True)

        sentinels = sum(1 for it in items if isinstance(it, dict) and it.get("noResults") is True)
        real = len(items) - sentinels

        # upsert 单 conn(绕过 get_conn,避免 NFS 上反复开/关 conn)
        captured_at = datetime.utcnow().isoformat() + "Z"
        source_id = "tw_" + HANDLE
        inserted = 0
        rows_to_upsert = []
        for it in items:
            if not isinstance(it, dict) or it.get("noResults") is True:
                continue
            try:
                post = _item_to_raw_post(it, fm, source_id, captured_at)
            except Exception:
                continue
            if not post.published_at.startswith(m_str):
                continue
            rows_to_upsert.append(post.to_row())
        UPSERT_SQL = """
            INSERT INTO raw_posts (
                post_id, source_id, platform, published_at, captured_at,
                raw_text, raw_url, raw_json, content_hash, is_deleted, archive_url
            ) VALUES (
                :post_id, :source_id, :platform, :published_at, :captured_at,
                :raw_text, :raw_url, :raw_json, :content_hash, :is_deleted, :archive_url
            )
            ON CONFLICT(post_id) DO UPDATE SET
                source_id=excluded.source_id, platform=excluded.platform,
                published_at=excluded.published_at, captured_at=excluded.captured_at,
                raw_text=excluded.raw_text, raw_json=excluded.raw_json,
                raw_url=excluded.raw_url, content_hash=excluded.content_hash,
                archive_url=COALESCE(raw_posts.archive_url, excluded.archive_url)
        """
        if rows_to_upsert:
            try:
                db.execute("BEGIN IMMEDIATE")
                db.executemany(UPSERT_SQL, rows_to_upsert)
                db.commit()
                inserted = len(rows_to_upsert)
            except sqlite3.OperationalError as e:
                db.rollback()
                print(f"    批 upsert err {e}, 退回逐条", flush=True)
                for row in rows_to_upsert:
                    try:
                        db.execute("BEGIN IMMEDIATE")
                        db.execute(UPSERT_SQL, row)
                        db.commit()
                        inserted += 1
                    except Exception:
                        db.rollback()

        n_total = db.execute(
            "SELECT count(*) FROM raw_posts WHERE substr(published_at, 1, 7) = ?",
            (m_str,),
        ).fetchone()[0]

        # 记 coverage
        try:
            record_coverage(
                HANDLE, DB_PATH,
                window_start=start, window_end=end,
                items_returned=len(items), items_persisted=n_total,
                from_cache=bool(cache_file.exists()), subdivided=False, depth=0,
                sentinel_count=sentinels,
            )
        except Exception as e:
            print(f"    record_coverage 失败: {e}", flush=True)

        delta = real - old["returned"]
        pct = (delta / old["returned"] * 100) if old["returned"] else 0
        results.append({
            "month": m_str, "old_returned": old["returned"],
            "new_returned": len(items), "real": real,
            "sentinels": sentinels, "old_persisted": old["persisted"],
            "new_persisted": n_total,
            "delta_returned": delta, "pct": round(pct, 1),
        })
        print(f"  → {m_str}: returned {old['returned']}→{len(items)} (Δ {delta:+d}, {pct:+.1f}%), "
              f"persisted {old['persisted']}→{n_total} (Δ {n_total - old['persisted']:+d}), "
              f"哨兵 {sentinels}", flush=True)

    db.close()

    # 对照表
    print("\n" + "=" * 100)
    print("全量重抓对照表")
    print("=" * 100)
    print(f"{'月份':<8} {'旧 returned':>11} {'新 returned':>11} {'Δ':>6} {'%':>7} "
          f"{'哨兵':>5} {'旧入库':>7} {'新入库':>7} {'Δ':>5} {'状态':<8}")
    print("-" * 100)
    for r in results:
        if r.get("status") == "FAILED":
            print(f"  {r['month']:<6} FAILED: {r.get('error')}")
            continue
        pct = f"{r['pct']:+.1f}%"
        marker = "⚠ 截断" if r['pct'] > 10 else ("↻ 跳过" if r.get("skipped") else "✓ 完整")
        print(f"  {r['month']:<6} {r['old_returned']:>10}  {r['new_returned']:>10}  "
              f"{r['delta_returned']:>+5}  {pct:>7}  {r['sentinels']:>4}  "
              f"{r['old_persisted']:>6}  {r['new_persisted']:>6}  "
              f"{r['new_persisted'] - r['old_persisted']:>+4}  {marker}")
    total_old_ret = sum(r.get("old_returned", 0) for r in results)
    total_new_ret = sum(r.get("new_returned", 0) for r in results)
    total_old_p = sum(r.get("old_persisted", 0) for r in results)
    total_new_p = sum(r.get("new_persisted", 0) for r in results)
    total_s = sum(r.get("sentinels", 0) for r in results)
    print("-" * 100)
    print(f"  {'合计':<6} {total_old_ret:>10}  {total_new_ret:>10}  "
          f"{total_new_ret - total_old_ret:>+5}  {'':>7}  {total_s:>4}  "
          f"{total_old_p:>6}  {total_new_p:>6}  {total_new_p - total_old_p:>+4}")

    print("\n⚠ 截断月份(>10% 新增):")
    truncated = [r for r in results if r.get("pct", 0) > 10 and not r.get("skipped")]
    if not truncated:
        print("  (无)")
    for r in truncated:
        print(f"  - {r['month']}: 旧 {r['old_returned']} → 新 {r['new_returned']} "
              f"(+{r['pct']:.1f}%), 旧入库 {r['old_persisted']} → 新入库 {r['new_persisted']}")

    with open("/tmp/rescrape_diff.json", "w") as f:
        json.dump(results, f, ensure_ascii=False, indent=2)
    print(f"\n详细 JSON: /tmp/rescrape_diff.json")


if __name__ == "__main__":
    main()
