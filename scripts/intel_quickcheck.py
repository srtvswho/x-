"""大V情报 — 每日健康速查 (4 项一眼看, 替代人工 cron log 翻查)

4 项检查:
1. cron 跑了没? 4 大V last_fetched_at 距今天数
2. 数据增长? raw_posts / extractions_intel 最近 24h 增量
3. 自检过了没? 4 项 (重复/cron/KOL 活跃/ISO)
4. GitHub push 成功? 远端最新 commit 时间 + 是否是 daily DB 备份

输出:
- 终端: 紧凑 4 段报告
- Markdown: /workspace/outputs/intel_quickcheck_YYYYMMDD.md (给用户存档)
- 退出码: 0 = 全绿, 1 = 异常

使用:
  python3 scripts/intel_quickcheck.py           # 检查今天
  python3 scripts/intel_quickcheck.py --days 7  # 检查最近 7 天
"""
from __future__ import annotations

import argparse
import json
import os
import sqlite3
import sys
import urllib.request
from datetime import datetime, timedelta, timezone

DB_PATH = "/workspace/data/signalboard_full.db"
GITHUB_REPO = "srtvswho/x-"

KOLS = [
    ("jukan05", "tw_jukan05"),
    ("aleabitoreddit", "tw_aleabitoreddit"),
    ("zephyr_z9", "tw_zephyr_z9"),
    ("austinsemis", "tw_austinsemis"),
]


def section_header(title: str) -> str:
    return f"\n{'='*70}\n{title}\n{'='*70}\n"


def check_cron_last_run(con: sqlite3.Connection) -> tuple[list, list]:
    """检查 1: cron 跑了没 (4 大V last_fetched_at).

    Returns: (status_lines, issues)
    """
    status = []
    issues = []
    today = datetime.now(timezone.utc).date()

    for handle, sid in KOLS:
        r = con.execute("""
            SELECT last_fetched_at, last_tweet_published_at, total_scraped
            FROM scrape_state WHERE handle=?
        """, (handle,)).fetchone()
        if not r:
            status.append(f"  ❌ {sid}: scrape_state 缺")
            issues.append(("NO_STATE", sid))
            continue
        last_fetch, last_pub, total = r
        if not last_fetch:
            status.append(f"  ⚠  {sid}: last_fetched_at 缺")
            issues.append(("FETCH_NULL", sid))
            continue
        last_fetch_date = last_fetch[:10]
        last_fetch_dt = datetime.fromisoformat(last_fetch_date).date()
        days_late = (today - last_fetch_dt).days

        if days_late == 0:
            status.append(f"  ✅ {sid}: last_fetch {last_fetch[11:16]}Z (今天)")
        elif days_late == 1:
            status.append(f"  ⚠  {sid}: last_fetch {last_fetch[11:16]}Z ({days_late} 天前, 接近 24h 边界)")
        else:
            status.append(f"  ❌ {sid}: last_fetch {last_fetch[11:16]}Z ({days_late} 天前没跑)")
            issues.append(("CRON_STALE", sid, days_late))
    return status, issues


def check_data_growth(con: sqlite3.Connection) -> tuple[list, list]:
    """检查 2: 数据增长 (raw_posts / extractions_intel).

    Returns: (status_lines, issues)
    """
    issues = []
    status = []
    now = datetime.now(timezone.utc)
    cutoff_24h = (now - timedelta(hours=24)).isoformat()
    cutoff_7d = (now - timedelta(days=7)).isoformat()

    # raw_posts 总数
    n_total = con.execute("SELECT COUNT(*) FROM raw_posts").fetchone()[0]
    n_24h = con.execute("""
        SELECT COUNT(*) FROM raw_posts
        WHERE captured_at >= ? OR published_at >= ?
    """, (cutoff_24h, cutoff_24h)).fetchone()[0]
    n_7d_new_posts = con.execute("""
        SELECT COUNT(*) FROM raw_posts
        WHERE published_at >= ?
    """, (cutoff_7d,)).fetchone()[0]

    # extractions_intel
    n_ext_total = con.execute("SELECT COUNT(*) FROM extractions_intel").fetchone()[0]
    n_ext_24h = con.execute("""
        SELECT COUNT(*) FROM extractions_intel
        WHERE extracted_at >= ?
    """, (cutoff_24h,)).fetchone()[0]

    status.append(f"  raw_posts: {n_total:,} (24h 增量: {n_24h}, 7d 推文: {n_7d_new_posts})")
    status.append(f"  extractions_intel: {n_ext_total:,} (24h 抽取: {n_ext_24h})")

    # 异常: 24h 0 new 持续 (但 cron 跑过)
    if n_24h == 0 and n_ext_24h == 0:
        status.append(f"  ⚠  24h 数据零增长 (cron 可能没真抓到推文)")
        issues.append(("NO_GROWTH", "raw_posts+extractions_intel", 0))
    elif n_24h > 500:
        status.append(f"  ⚠  24h raw_posts 增长 {n_24h} (异常暴增, 可能重复抓)")
        issues.append(("HIGH_GROWTH", "raw_posts", n_24h))

    # by source_id 增量
    status.append(f"  by source_id (24h new):")
    for sid in ['tw_jukan05', 'tw_aleabitoreddit', 'tw_zephyr_z9', 'tw_austinsemis']:
        n = con.execute("""
            SELECT COUNT(*) FROM raw_posts
            WHERE source_id=? AND (captured_at >= ? OR published_at >= ?)
        """, (sid, cutoff_24h, cutoff_24h)).fetchone()[0]
        status.append(f"    {sid:30s} {n:>3}")

    return status, issues


def check_health(con: sqlite3.Connection) -> tuple[list, list]:
    """检查 3: 自检 4 项 (重复/cron/KOL 活跃/ISO).

    Returns: (status_lines, issues)
    """
    issues = []
    status = []

    # 重复
    dup_total = 0
    for sid in ['tw_jukan05', 'tw_aleabitoreddit', 'tw_zephyr_z9', 'tw_austinsemis']:
        r = con.execute("""
            SELECT COUNT(*), COUNT(DISTINCT post_id) FROM raw_posts WHERE source_id=?
        """, (sid,)).fetchone()
        dup = r[0] - r[1]
        if dup > 0:
            status.append(f"  ❌ {sid}: {dup} 重复 (race condition!)")
            issues.append(("DUP", sid, dup))
            dup_total += dup
    if dup_total == 0:
        status.append(f"  ✅ 4 大V 内部 0 重复")

    # KOL 活跃
    today = datetime.now(timezone.utc).date()
    for handle, sid in KOLS:
        r = con.execute("""
            SELECT last_tweet_published_at FROM scrape_state WHERE handle=?
        """, (handle,)).fetchone()
        if r and r[0]:
            last_pub_dt = datetime.fromisoformat(r[0].replace("Z", "+00:00"))
            days_ago = (datetime.now(timezone.utc) - last_pub_dt).days
            if days_ago > 30:
                status.append(f"  ❌ {sid}: {days_ago} 天没推文 (KOL 停发/失效)")
                issues.append(("INACTIVE", sid, days_ago))
            elif days_ago > 7:
                status.append(f"  ⚠  {sid}: {days_ago} 天没推文")

    # ISO 格式
    bad = con.execute("""
        SELECT COUNT(*) FROM raw_posts
        WHERE published_at IS NULL OR length(published_at) < 20
           OR instr(substr(published_at, 11), 'T') = 0
    """).fetchone()[0]
    if bad > 0:
        status.append(f"  ❌ raw_posts: {bad} 条 published_at 非 ISO 格式")
        issues.append(("ISO_BAD", "raw_posts", bad))
    else:
        status.append(f"  ✅ 全 DB published_at ISO 格式")

    return status, issues


def check_github_push() -> tuple[list, list]:
    """检查 4: GitHub push 成功? 远端最新 commit.

    Returns: (status_lines, issues)
    """
    issues = []
    status = []
    token = os.environ.get("GH_TOKEN", "")
    if not token:
        status.append(f"  ❌ GH_TOKEN 未设置 (无法查 GitHub)")
        issues.append(("NO_TOKEN", "github", 0))
        return status, issues
    try:
        req = urllib.request.Request(
            f"https://api.github.com/repos/{GITHUB_REPO}/commits?per_page=3",
            headers={"Authorization": f"token {token}"}
        )
        with urllib.request.urlopen(req, timeout=15) as r:
            d = json.load(r)
        # 远端最新
        remote_head = d[0]
        remote_sha = remote_head["sha"][:8]
        remote_msg = remote_head["commit"]["message"].split("\n")[0]
        remote_date = remote_head["commit"]["committer"]["date"]
        # 本地 HEAD
        import subprocess
        local = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            capture_output=True, text=True, cwd="/workspace"
        )
        local_sha = local.stdout.strip()[:8]
        # sync?
        if local_sha == remote_sha:
            status.append(f"  ✅ Local HEAD = Remote HEAD: {remote_sha} | {remote_msg}")
        else:
            status.append(f"  ⚠  Local {local_sha} != Remote {remote_sha}")
            issues.append(("DIVERGED", "git", 0))
        # 远端 commit 时间
        commit_dt = datetime.fromisoformat(remote_date.replace("Z", "+00:00"))
        now = datetime.now(timezone.utc)
        age = (now - commit_dt).total_seconds() / 3600  # hours
        if age < 24:
            status.append(f"  ✅ 远端最新 commit: {age:.1f}h 前 (今天)")
        elif age < 48:
            status.append(f"  ⚠  远端最新 commit: {age:.1f}h 前 (昨天)")
        else:
            status.append(f"  ❌ 远端最新 commit: {age/24:.1f}d 前 (超 48h)")
            issues.append(("PUSH_STALE", "github", age))
        # 是否 daily DB 备份
        if "Daily DB backup" in remote_msg:
            status.append(f"  ✅ 最新 commit 是 Daily DB backup")
        else:
            status.append(f"  ⚠  最新 commit 不是 Daily DB backup: {remote_msg}")
    except Exception as e:
        status.append(f"  ❌ GitHub API ERR: {e}")
        issues.append(("API_ERR", "github", str(e)))
    return status, issues


def write_markdown_report(today: str, all_status: dict, all_issues: list) -> str:
    """写 markdown 报告 (用户存档/速查)."""
    md = []
    md.append(f"# 大V情报 — 每日健康速查 ({today} UTC)")
    md.append("")
    md.append(f"_生成时间: {datetime.now(timezone.utc).isoformat()}_")
    md.append("")

    if all_issues:
        md.append(f"## ❌ 状态: {len(all_issues)} 类异常")
    else:
        md.append(f"## ✅ 状态: 全绿")
    md.append("")

    for sec, lines in all_status.items():
        md.append(f"## {sec}")
        md.append("")
        for line in lines:
            md.append(line)
        md.append("")

    md.append("## 异常详情")
    md.append("")
    if all_issues:
        for typ, sid, n in all_issues:
            md.append(f"- **{typ}** {sid} ({n})")
    else:
        md.append("- 无")

    md.append("")
    md.append("---")
    md.append("")
    md.append("**用法**: `python3 scripts/intel_quickcheck.py` (每早跑一次, 一眼看完)")
    return "\n".join(md)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--days", type=int, default=0, help="检查最近 N 天 (0=只看今天)")
    ap.add_argument("--no-md", action="store_true", help="不写 markdown 文件, 只打印")
    ap.add_argument("--quiet", action="store_true", help="只打印 summary, 不打印详情")
    args = ap.parse_args()

    con = sqlite3.connect(DB_PATH, timeout=30)
    today = datetime.now(timezone.utc).date()
    today_iso = today.isoformat()

    all_status = {}
    all_issues = []

    # 检查 1: cron
    s, i = check_cron_last_run(con)
    all_status["1️⃣ Cron 跑没跑 (4 大V last_fetched_at)"] = s
    all_issues.extend(i)

    # 检查 2: 数据增长
    s, i = check_data_growth(con)
    all_status["2️⃣ 数据增长 (raw_posts + extractions_intel)"] = s
    all_issues.extend(i)

    # 检查 3: 自检
    s, i = check_health(con)
    all_status["3️⃣ 自检 (重复/KOL 活跃/ISO 格式)"] = s
    all_issues.extend(i)

    # 检查 4: GitHub push
    s, i = check_github_push()
    all_status["4️⃣ GitHub push 状态 (远端最新 commit)"] = s
    all_issues.extend(i)

    con.close()

    # 打印
    print(f"\n{'#'*70}")
    print(f"# 大V情报 — 每日健康速查 ({today_iso} UTC)")
    print(f"{'#'*70}")

    if not args.quiet:
        for sec, lines in all_status.items():
            print(section_header(sec))
            for line in lines:
                print(line)
    else:
        # Quiet 模式: 一行
        if all_issues:
            print(f"\n  ❌ 异常: {len(all_issues)} 项")
            for typ, sid, n in all_issues:
                print(f"     - {typ} {sid} ({n})")
        else:
            print(f"\n  ✅ 全绿 (4 大V 健康, 数据在增长, push 成功)")

    # 总结
    print(f"\n{'='*70}")
    if all_issues:
        print(f"❌ 速查: {len(all_issues)} 类异常 — 看上面详情")
        exit_code = 1
    else:
        print(f"✅ 速查: 全绿 — 系统昨天正常跑了")
        exit_code = 0
    print(f"{'='*70}\n")

    # 写 markdown
    if not args.no_md:
        out_dir = "/workspace/outputs"
        os.makedirs(out_dir, exist_ok=True)
        md_file = f"{out_dir}/intel_quickcheck_{today_iso}.md"
        with open(md_file, "w") as f:
            f.write(write_markdown_report(today_iso, all_status, all_issues))
        print(f"📁 Markdown 报告: {md_file}")

    return exit_code


if __name__ == "__main__":
    sys.exit(main())
