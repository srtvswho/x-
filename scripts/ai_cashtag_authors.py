"""美股 AI 核心标的 cashtag 讨论 → 高频发声者列表

严格按用户规则:
- 10 个标的: NVDA PLTR AMD AVGO MRVL MSFT META GOOGL TSM MU
- 抓最近 1-2 月, sort by engagement
- 提取作者, 统计频率
- 输出前 50 (handle / 出现次数 / 粉丝数 / 简介)
- 不筛选 / 不判断 / 不改规则
"""
from __future__ import annotations
import json
import os
import time
import urllib.request
from pathlib import Path
from collections import Counter
from concurrent.futures import ThreadPoolExecutor, as_completed

APIFY_TOKEN = os.environ.get("APIFY_TOKEN", "")
ACTOR_ID = "61RPP7dywgiy0JPD0"
OUT_DIR = Path("/workspace/logs/p5_cashtag_authors")
OUT_DIR.mkdir(parents=True, exist_ok=True)

# 用户给定的 10 个标的 — 严格不增不减
TICKERS = ["NVDA", "PLTR", "AMD", "AVGO", "MRVL", "MSFT", "META", "GOOGL", "TSM", "MU"]

# 时间窗: 2026-05-01 ~ 2026-06-22 (近 2 月)
SINCE = "2026-05-01"
UNTIL = "2026-06-22"


def apify_fetch_cashtag(ticker: str, since: str, until: str, max_items: int = 300) -> list[dict]:
    """Apify 拉 1 个 cashtag + 时间窗 + sort=Top (按互动量)."""
    print(f"  Apify: ${ticker} since={since} until={until} max={max_items}")
    input_json = json.dumps({
        "searchTerms": [f"${ticker} since:{since} until:{until}"],
        "maxItems": max_items,
        "sort": "Top",  # 按 engagement (likes + RT + reply + view)
    })
    req = urllib.request.Request(
        f"https://api.apify.com/v2/acts/{ACTOR_ID}/runs?token={APIFY_TOKEN}",
        data=input_json.encode(),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    for retry in range(3):
        try:
            with urllib.request.urlopen(req, timeout=60) as r:
                run_info = json.loads(r.read())
            break
        except Exception as e:
            print(f"    start retry {retry+1}: {e}")
            time.sleep(5 * (retry + 1))
    run_id = run_info.get("data", {}).get("id")
    if not run_id:
        print(f"    ! no run_id")
        return []
    s = "?"
    for i in range(30):
        time.sleep(8)
        try:
            with urllib.request.urlopen(
                f"https://api.apify.com/v2/acts/{ACTOR_ID}/runs/{run_id}?token={APIFY_TOKEN}",
                timeout=30,
            ) as r2:
                s = json.loads(r2.read()).get("data", {}).get("status", "?")
        except Exception:
            continue
        if i % 4 == 0:
            print(f"    [poll {i}] {s}")
        if s in ("SUCCEEDED", "FAILED", "ABORTED"):
            break
    if s != "SUCCEEDED":
        print(f"    ! run {s}")
        return []
    try:
        with urllib.request.urlopen(
            f"https://api.apify.com/v2/datasets/{run_info['data']['defaultDatasetId']}/items?token={APIFY_TOKEN}&format=json&limit={max_items}",
            timeout=60,
        ) as r3:
            items = json.loads(r3.read())
        print(f"    → {len(items)} items")
        return items
    except Exception as e:
        print(f"    ! fetch failed: {e}")
        return []


def extract_author(item: dict) -> dict:
    """从单条推文提取作者信息 (不判断, 只提取)."""
    # apidojo/tweet-scraper 把 author 放在 author 字段
    a = item.get("author") or {}
    return {
        "handle": a.get("userName") or a.get("screen_name"),
        "name": a.get("name"),
        "user_id": a.get("id"),
        "followers_count": a.get("followersCount") or a.get("followers_count"),
        "description": a.get("description"),
        "verified": a.get("isBlueVerified") or a.get("verified"),
    }


def main():
    import time as _t
    t0 = _t.time()
    print("=" * 60)
    print("美股 AI 标的 cashtag → 高频发声者 (严格按用户规则)")
    print("=" * 60)
    print(f"标的: {TICKERS}")
    print(f"时间窗: {SINCE} ~ {UNTIL}")
    print(f"sort: Top (按互动量)")
    print()

    # Step 1: 10 个 ticker 串行拉 (避免 archon-server fetch failed)
    print(f"[Step 1/3] 抓 10 个 cashtag 推文 (串行)...")
    all_items_by_ticker: dict[str, list[dict]] = {}
    for t in TICKERS:
        try:
            items = apify_fetch_cashtag(t, SINCE, UNTIL, 300)
        except Exception as e:
            print(f"  ${t}: error {e}")
            items = []
        all_items_by_ticker[t] = items

    # 保存 raw
    for t, items in all_items_by_ticker.items():
        json.dump(items, open(OUT_DIR / f"raw_{t}.json", "w"), indent=2, ensure_ascii=False)

    total = sum(len(items) for items in all_items_by_ticker.values())
    print(f"\n  总推文: {total}")
    for t, items in all_items_by_ticker.items():
        print(f"    ${t}: {len(items)}")

    # Step 2: 提取作者, 统计频率
    print(f"\n[Step 2/3] 提取作者 + 统计频率...")
    author_count: Counter = Counter()
    author_info: dict[str, dict] = {}  # handle → {followers, description, ...}

    for t, items in all_items_by_ticker.items():
        for it in items:
            a = extract_author(it)
            h = a.get("handle")
            if not h:
                continue
            # 跳过被讨论的公司官号 (用户问的是 "谁在发表观点", 不是公司本身)
            # 严格按用户规则: 不过滤, 先收集, 让用户看
            author_count[h] += 1
            # 更新 author_info (取第一个 non-null)
            if h not in author_info:
                author_info[h] = {}
            for k, v in a.items():
                if k == "handle":
                    continue
                if v is not None and author_info[h].get(k) is None:
                    author_info[h][k] = v

    # 统计每个 ticker 上出现的作者 (用于报告)
    author_tickers: dict[str, Counter] = {}
    for t, items in all_items_by_ticker.items():
        c = Counter()
        for it in items:
            a = extract_author(it)
            h = a.get("handle")
            if h:
                c[h] += 1
        author_tickers[t] = c

    print(f"  总唯一作者: {len(author_count)}")
    print(f"  总发帖次数: {sum(author_count.values())}")

    # 排序前 50 (按出现次数降序)
    top50 = author_count.most_common(50)
    print(f"  Top 50 (出现次数):")
    for h, c in top50[:50]:
        info = author_info.get(h, {})
        fc = info.get("followers_count") or 0
        desc = (info.get("description") or "")[:50].replace("|", "/")
        print(f"    @{h:25s} {c:3d} | {fc:>8} fans | {desc}")

    # 保存 JSON
    (OUT_DIR / "authors_top50.json").write_text(json.dumps([
        {
            "handle": h,
            "count": c,
            "followers_count": author_info.get(h, {}).get("followers_count"),
            "name": author_info.get(h, {}).get("name"),
            "description": author_info.get(h, {}).get("description"),
            "verified": author_info.get(h, {}).get("verified"),
            "user_id": author_info.get(h, {}).get("user_id"),
            # 这个作者在哪几个 ticker 上出现过
            "appeared_in_tickers": [t for t, ac in author_tickers.items() if ac.get(h, 0) > 0],
            "per_ticker_count": {t: ac.get(h, 0) for t, ac in author_tickers.items() if ac.get(h, 0) > 0},
        }
        for h, c in top50
    ], indent=2, ensure_ascii=False))

    # 完整作者 (前 200, 不筛)
    top200 = author_count.most_common(200)
    (OUT_DIR / "authors_top200.json").write_text(json.dumps([
        {
            "handle": h,
            "count": c,
            "followers_count": author_info.get(h, {}).get("followers_count"),
            "name": author_info.get(h, {}).get("name"),
            "description": author_info.get(h, {}).get("description"),
        }
        for h, c in top200
    ], indent=2, ensure_ascii=False))

    # Step 3: 写报告 — 不判断不筛
    print(f"\n[Step 3/3] 写报告...")
    lines = [
        "# 美股 AI 标的 Cashtag 高频发声者 (P5-7)",
        "",
        f"**生成时间**: {time.strftime('%Y-%m-%d %H:%M')}  ",
        f"**标的**: {TICKERS} (按用户给定, 未增减)  ",
        f"**时间窗**: {SINCE} ~ {UNTIL} (近 2 月)  ",
        f"**sort**: Top (按互动量)  ",
        f"**Apify runs**: 10 个 (1 个/标的, 并发 3 路)",
        "",
        f"## 总览",
        "",
        f"- 总推文: {total}",
        f"- 总唯一作者: {len(author_count)}",
        f"- Top 50 / Top 200 (完整未筛)",
        "",
        "## Top 50 高频发声者 (按出现次数降序)",
        "",
        "**纪律**: 不做任何质量筛选, 不判断谁好谁坏, 把完整列表给你判断.",
        "",
        "| # | handle | 出现次数 | followers | verified | name | 简介 | 在哪些 ticker |",
        "|---|---|---|---|---|---|---|---|",
    ]
    for i, (h, c) in enumerate(top50, 1):
        info = author_info.get(h, {})
        fc = info.get("followers_count") or 0
        desc = (info.get("description") or "")[:80].replace("|", "/")
        name = (info.get("name") or "")[:30].replace("|", "/")
        verif = "✓" if info.get("verified") else ""
        ticks = [t for t, ac in author_tickers.items() if ac.get(h, 0) > 0]
        tick_str = ", ".join([f"${t}({author_tickers[t][h]})" for t in ticks])
        lines.append(f"| {i} | @{h} | {c} | {fc:,} | {verif} | {name} | {desc} | {tick_str} |")

    # 每个 ticker 的高频
    lines.extend([
        "",
        "## 各 ticker 高频 Top 10",
        "",
    ])
    for t in TICKERS:
        top10 = author_tickers[t].most_common(10)
        lines.append(f"### ${t}")
        lines.append("")
        lines.append("| # | handle | 次数 | 简介 |")
        lines.append("|---|---|---|---|")
        for i, (h, c) in enumerate(top10, 1):
            info = author_info.get(h, {})
            desc = (info.get("description") or "")[:60].replace("|", "/")
            lines.append(f"| {i} | @{h} | {c} | {desc} |")
        lines.append("")

    # 文件清单
    lines.extend([
        "",
        "## 文件清单",
        "",
        f"- `logs/p5_cashtag_authors/raw_*.json` (10 个, 每个 cashtag 原始推文)",
        f"- `logs/p5_cashtag_authors/authors_top50.json` (Top 50 完整 JSON)",
        f"- `logs/p5_cashtag_authors/authors_top200.json` (Top 200 完整 JSON)",
        "",
        "**等你看完 Top 50 后, 挑出像信号源的, 我再给他们做体检.**",
    ])

    out = Path("/workspace/outputs/p5_cashtag_authors.md")
    out.write_text("\n".join(lines))
    print(f"📄 {out}")

    print(f"\n⏱️  总耗时: {_t.time()-t0:.1f}s")


if __name__ == "__main__":
    main()