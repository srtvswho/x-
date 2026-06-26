"""大V情报 — 每日自检 (cron 跑完后自动执行)

4 项检查 (用 scrape_state 状态, 不是 captured_at):
1. 重复检查: raw_posts 里 4 大V 各自内部 + 之间 post_id 重复 (应永远 0)
2. cron 跑没跑: scrape_state.last_fetched_at 应该是今天 UTC
3. KOL 活跃度: last_tweet_published_at 跟 now 差 (差太大 = KOL 停发 / Apify 失败)
4. 日期检查: 全 DB 随机抽 5 条 published_at ISO 格式 (防 [:10] bug 复活)

注意: captured_at 是 import/batch 时间, 不是 published_at.
判断"今天 new 多少"用 scrape_state.total_scraped 的时间序列差 (不实际, 简化)

输出:
- 日志: /workspace/logs/intel_health_YYYYMMDD.log
- 健康总览: 末尾一行
- 异常: stderr + 显著标记 (⚠/❌)
- exit 0=健康, 1=有异常
"""
from __future__ import annotations

import os
import sqlite3
import sys
from datetime import datetime, timedelta, timezone

DB_PATH = "/workspace/data/signalboard_full.db"
LOG_DIR = "/workspace/logs"
TODAY = datetime.now(timezone.utc).date()
TODAY_ISO = TODAY.isoformat()

# 4 大V
KOLS = [
    ("jukan05", "tw_jukan05"),
    ("aleabitoreddit", "tw_aleabitoreddit"),
    ("zephyr_z9", "tw_zephyr_z9"),
    ("austinsemis", "tw_austinsemis"),
]


def health_check():
    issues = []
    today_str = TODAY.strftime("%Y%m%d")
    log_file = os.path.join(LOG_DIR, f"intel_health_{today_str}.log")
    log_lines = []

    def log(msg):
        line = f"[{datetime.now(timezone.utc).isoformat()}] {msg}"
        log_lines.append(line)
        print(line)

    log("=" * 70)
    log(f"📊 大V情报 — 每日自检 ({TODAY_ISO} UTC)")
    log("=" * 70)

    con = sqlite3.connect(DB_PATH, timeout=30)
    cur = con.cursor()

    # ===== 检查 1: 重复 (4 大V 内部 + 之间) =====
    log("\n[1/4] 🔍 重复检查 (raw_posts post_id 重复)")
    log("-" * 70)

    for handle, sid in KOLS:
        r = cur.execute("""
            SELECT COUNT(*), COUNT(DISTINCT post_id)
            FROM raw_posts WHERE source_id=?
        """, (sid,)).fetchone()
        total, distinct = r
        dup = total - distinct
        if dup == 0:
            log(f"  ✅ {sid}: {total} 条, 0 重复")
        else:
            msg = f"❌ {sid}: {total} 条, {dup} 重复! (race condition 复发)"
            log(msg)
            issues.append(("DUP", sid, dup))
            dup_ids = cur.execute("""
                SELECT post_id, COUNT(*) c FROM raw_posts
                WHERE source_id=? GROUP BY post_id HAVING c > 1 LIMIT 3
            """, (sid,)).fetchall()
            for pid, c in dup_ids:
                log(f"      dup id={pid} x{c}")

    cross = cur.execute("""
        SELECT post_id, COUNT(*) c, GROUP_CONCAT(source_id) sources
        FROM raw_posts
        WHERE source_id IN ('tw_jukan05', 'tw_aleabitoreddit', 'tw_zephyr_z9', 'tw_austinsemis')
        GROUP BY post_id HAVING c > 1 LIMIT 3
    """).fetchall()
    if not cross:
        log(f"  ✅ 4 大V 之间 0 冲突")
    else:
        msg = f"❌ 4 大V 之间 {len(cross)} 个 post_id 冲突"
        log(msg)
        issues.append(("CROSS", "", len(cross)))

    # ===== 检查 2: cron 跑没跑 =====
    log("\n[2/4] ⏰ cron 跑没跑 (scrape_state.last_fetched_at)")
    log("-" * 70)

    for handle, sid in KOLS:
        r = cur.execute("""
            SELECT last_fetched_at, last_tweet_published_at, total_scraped
            FROM scrape_state WHERE handle=?
        """, (handle,)).fetchone()
        if not r:
            msg = f"❌ {sid}: scrape_state 缺 (cron 还没跑过 / 初始化失败)"
            log(msg)
            issues.append(("NO_STATE", sid, 0))
            continue
        last_fetch, last_pub, total = r
        # last_fetched_at 是不是今天
        if last_fetch:
            last_fetch_date = last_fetch[:10]  # YYYY-MM-DD
            if last_fetch_date == TODAY_ISO:
                log(f"  ✅ {sid}: last_fetched_at={last_fetch} (今天跑过)")
            else:
                days_late = (TODAY - datetime.fromisoformat(last_fetch_date).date()).days
                if days_late <= 1:
                    log(f"  ⚠  {sid}: last_fetched_at={last_fetch} ({days_late} 天前, 接近 24h 边界)")
                else:
                    msg = f"❌ {sid}: last_fetched_at={last_fetch} ({days_late} 天前没跑)"
                    log(msg)
                    issues.append(("CRON_STALE", sid, days_late))
        else:
            log(f"  ⚠  {sid}: last_fetched_at 缺")

    # ===== 检查 3: KOL 活跃度 (last_tweet_published_at 跟 now 差多少) =====
    log("\n[3/4] 📈 KOL 活跃度 (last_tweet_published_at 距今)")
    log("-" * 70)

    for handle, sid in KOLS:
        r = cur.execute("""
            SELECT last_tweet_published_at FROM scrape_state WHERE handle=?
        """, (handle,)).fetchone()
        if not r or not r[0]:
            log(f"  ⚠  {sid}: last_tweet_published_at 缺")
            continue
        last_pub = r[0]
        try:
            last_pub_dt = datetime.fromisoformat(last_pub.replace("Z", "+00:00"))
            days_ago = (datetime.now(timezone.utc) - last_pub_dt).days
        except Exception:
            log(f"  ⚠  {sid}: last_tweet_published_at={last_pub} 解析失败")
            continue
        if days_ago <= 7:
            log(f"  ✅ {sid}: 最新推文 {days_ago} 天前 ({last_pub}) — 正常活跃")
        elif days_ago <= 30:
            log(f"  ⚠  {sid}: 最新推文 {days_ago} 天前 ({last_pub}) — KOL 可能停发")
            issues.append(("INACTIVE", sid, days_ago))
        else:
            msg = f"❌ {sid}: 最新推文 {days_ago} 天前 ({last_pub}) — 长期停发 / 抓取失败"
            log(msg)
            issues.append(("INACTIVE", sid, days_ago))

    # ===== 检查 4: 日期格式 (全 DB 随机抽 5 条 published_at ISO) =====
    log("\n[4/4] 📅 日期格式检查 (raw_posts published_at 必须 ISO)")
    log("-" * 70)

    bad_count = 0
    for handle, sid in KOLS:
        bad = cur.execute("""
            SELECT post_id, published_at FROM raw_posts
            WHERE source_id=?
              AND (
                published_at IS NULL OR published_at = ''
                OR length(published_at) < 20
                OR instr(substr(published_at, 11), 'T') = 0
              )
            LIMIT 5
        """, (sid,)).fetchall()
        if not bad:
            n = cur.execute("SELECT COUNT(*) FROM raw_posts WHERE source_id=?", (sid,)).fetchone()[0]
            log(f"  ✅ {sid}: 全部 {n} 条 published_at ISO 格式")
        else:
            msg = f"❌ {sid}: {len(bad)} 条 published_at 非 ISO ([:10] bug 复活?)"
            log(msg)
            issues.append(("ISO_BAD", sid, len(bad)))
            bad_count += len(bad)
            for pid, pub in bad[:3]:
                log(f"      id={pid} published_at={pub!r}")

    # ===== 总览 =====
    log("\n" + "=" * 70)
    if issues:
        log(f"❌ 自检不通过 — {len(issues)} 类异常")
        for typ, sid, n in issues:
            log(f"   - {typ}  {sid}  ({n})")
        log("")
        log("⚠ 自检失败的可能原因:")
        log("   - DUP/REPLAY: race condition 复发, 看上次 race fix")
        log("   - CRON_STALE: cron 没跑 / Apify 失败, 看 cron log")
        log("   - INACTIVE: KOL 停发 / handle 失效 / 抓取逻辑失败")
        log("   - ISO_BAD: [:10] bug 复活, 立刻 disable cron, debug")
        log("   - NO_STATE: 初始化失败, 跑 init_db + 手动 trigger")
        exit_code = 1
    else:
        log(f"✅ 自检通过 — 4 大V 健康")
        exit_code = 0

    con.close()

    # 写日志
    with open(log_file, "w") as f:
        f.write("\n".join(log_lines))
    print(f"\n📁 日志: {log_file}")

    return exit_code


if __name__ == "__main__":
    sys.exit(health_check())