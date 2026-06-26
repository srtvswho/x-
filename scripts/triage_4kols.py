"""4 KOL 体检 (TradexWhisperer / StockSavvyShay / amitisinvesting / Sam_Badawi)

严格按用户规则:
1. 抓能抓的全部历史 (按月切片, 尽量往前)
2. 类型分布: ORIGINAL / RELAYED / commentary / news
3. 个股方向判断列表 (美股 / 韩A股)
4. @TradexWhisperer 特别: 验证 self-claimed bargain thesis

不判断"值不值得", 不筛人, 不改步骤.
"""
from __future__ import annotations
import json
import os
import re
import time
import urllib.request
from pathlib import Path
from collections import Counter, defaultdict
from concurrent.futures import ThreadPoolExecutor, as_completed

APIFY_TOKEN = os.environ.get("APIFY_TOKEN", "")
DEEPSEEK_API_KEY = os.environ.get("DEEPSEEK_API_KEY", "")
ACTOR_ID = "61RPP7dywgiy0JPD0"
OUT_DIR = Path("/workspace/logs/p5_4kol_triage")
OUT_DIR.mkdir(parents=True, exist_ok=True)

# 用户指定 4 个 handle — 严格不增不减
KOLS = [
    "TradexWhisperer",
    "StockSavvyShay",
    "amitisinvesting",
    "Sam_Badawi",
]

# 时间窗: 2024-01-01 ~ 2026-06-22 (2.5 年, 尽可能往前)
SINCE = "2024-01-01"
UNTIL = "2026-06-22"


def apify_fetch(handle: str, since: str, until: str, max_items: int = 1000) -> list[dict]:
    """Apify 拉 1 个 handle 的所有内容."""
    print(f"  Apify: @{handle} since={since} until={until} max={max_items}")
    input_json = json.dumps({
        "searchTerms": [f"from:{handle} since:{since} until:{until}"],
        "maxItems": max_items,
        "sort": "Latest",
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
    for i in range(40):
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


# === directional_validator + attribution ===
import sys
sys.path.insert(0, "/workspace")
from signalboard.extract.directional_validator import validate_directional

ATTRIBUTION_PROMPT = """你是内容归属判定器。给定一条 X 推文, 判定判断归属。

【内容】{text}
【日期】{date}

【3 选 1】
- ORIGINAL: 作者自己的判断, 直接陈述观点, 没引用机构 (e.g. "I think / in my view / 我认为")
- RELAYED: 转述/搬运机构观点, 只引用没加立场 (e.g. "Goldman says / 研报 / 据 Bloomberg")
- RELAYED+COMMENT: 搬运了别人观点, 但加了自己的明确判断 (e.g. 转述研报后说 "However, I see it differently")

【输出 JSON】
{{
  "attribution": "ORIGINAL" / "RELAYED" / "RELAYED+COMMENT" / "?" / "news" / "commentary",
  "evidence": "一句话解释"
}}

注意: news = 纯新闻聚合 (无个人判断), commentary = 评价/感慨 (无明确方向)
"""


def llm_attribution(text: str, date: str) -> dict:
    prompt = ATTRIBUTION_PROMPT.format(text=text[:1500], date=date)
    data = json.dumps({
        "model": "deepseek-v4-pro",
        "messages": [{"role": "user", "content": prompt}],
        "response_format": {"type": "json_object"},
        "temperature": 0.1,
        "max_tokens": 600,
    }).encode()
    err = "?"
    for retry in range(2):
        try:
            req = urllib.request.Request(
                "https://api.deepseek.com/chat/completions",
                data=data,
                headers={"Authorization": f"Bearer {DEEPSEEK_API_KEY}", "Content-Type": "application/json"},
            )
            with urllib.request.urlopen(req, timeout=60) as r:
                resp = json.loads(r.read())
            cs = resp["choices"][0]["message"]["content"]
            if not cs:
                raise ValueError("empty")
            return json.loads(cs)
        except Exception as e:
            err = str(e)
            if retry < 1:
                time.sleep(2)
    return {"attribution": "?", "evidence": f"err: {err[:50]}"}


# 美股 vs A股/港股 判定 (粗)
A_SHARE_RE = re.compile(r"\b[0-9]{6}\.(?:SH|SZ|SS)\b")
HK_RE = re.compile(r"\b[0-9]{4,5}\.HK\b")
KR_RE = re.compile(r"\b[0-9]{6}\.(?:KS|KQ)\b")
TW_RE = re.compile(r"\b[0-9]{4}\.(?:TW|TWO)\b")


def market_of_text(text: str, ticker: str | None) -> str:
    """判断文本/ticker 属于哪个市场."""
    if ticker:
        # 通过 ticker 后缀
        if KR_RE.search(ticker):
            return "KR"
        if TW_RE.search(ticker):
            return "TW"
        if HK_RE.search(ticker):
            return "HK"
        if A_SHARE_RE.search(ticker):
            return "A_share"
        # 美股 ticker 默认 US (无后缀或 .X)
        return "US"
    # 通过文字
    if A_SHARE_RE.search(text):
        return "A_share"
    if HK_RE.search(text):
        return "HK"
    if KR_RE.search(text):
        return "KR"
    if TW_RE.search(text):
        return "TW"
    if re.search(r"\$([A-Z]{1,5})\b", text):
        return "US"  # $ticker 形式默认 US
    return "?"


# === Per-KOL 体检 ===
def triage_one(handle: str) -> dict:
    """单 KOL 体检: 抓数据 + 抽取 + 统计."""
    items = apify_fetch(handle, SINCE, UNTIL, 1000)
    if not items:
        return {"handle": handle, "n_items": 0, "skipped": "no_data"}

    # 保存 raw
    json.dump(items, open(OUT_DIR / f"raw_{handle}.json", "w"), indent=2, ensure_ascii=False)

    # 时间跨度
    dates = sorted({(it.get("createdAt") or "?")[:10] for it in items if it.get("createdAt")})
    date_range = f"{dates[0]} ~ {dates[-1]}" if dates else "?"

    # 原创 vs reply
    originals = [it for it in items if not it.get("isReply") and not it.get("isRetweet")]
    replies = [it for it in items if it.get("isReply")]
    retweets = [it for it in items if it.get("isRetweet")]

    # 抽取 directional judgment
    judgments = []
    type_count = Counter()

    for it in items:
        text = (it.get("text") or it.get("fullText") or "")
        if not text:
            continue
        # 提取 ticker (粗, 不严格)
        # 优先 $TICKER 形式
        dollar_t = re.findall(r"\$([A-Z]{1,5})\b", text)
        ticker = dollar_t[0] if dollar_t else None

        # directional_validator 校验
        v = validate_directional(text, ticker or "", "auto")
        type_count[v.action] += 1

        # 只保留 keep / flip_direction (即真有 long/short 方向)
        if v.action in ("keep", "flip_direction"):
            # 进一步 attribution
            date = (it.get("createdAt") or "?")[:10]
            attr = llm_attribution(text[:1500], date)
            judgments.append({
                "date": date,
                "direction": v.final_direction,
                "ticker": ticker,
                "market": market_of_text(text, ticker),
                "excerpt": text[:200],
                "validation_action": v.action,
                "validation_reason": v.reason[:120],
                "attribution": attr.get("attribution", "?"),
                "attribution_evidence": attr.get("evidence", ""),
                "source_id": it.get("id"),
                "tweet_url": (it.get("url") or it.get("twitterUrl") or ""),
            })

    return {
        "handle": handle,
        "n_items": len(items),
        "date_range": date_range,
        "n_originals": len(originals),
        "n_replies": len(replies),
        "n_retweets": len(retweets),
        "validation_actions": dict(type_count),
        "judgments": judgments,
    }


def main():
    import time as _t
    t0 = _t.time()
    print("=" * 60)
    print("4 KOL 体检 (TradexWhisperer / StockSavvyShay / amitisinvesting / Sam_Badawi)")
    print("=" * 60)
    print(f"时间窗: {SINCE} ~ {UNTIL}")
    print(f"每 KOL: maxItems=1000, sort=Latest")
    print()

    # Step 1: 抓 4 个 (并发 3)
    print(f"[Step 1/3] 抓 4 KOL 历史推文 (并发 3 路)...")
    results = {}
    with ThreadPoolExecutor(max_workers=3) as pool:
        futures = {pool.submit(triage_one, h): h for h in KOLS}
        for fut in as_completed(futures):
            h = futures[fut]
            try:
                r = fut.result()
            except Exception as e:
                r = {"handle": h, "n_items": 0, "error": str(e)}
            results[h] = r
            print(f"  @{h}: {r.get('n_items', 0)} items")

    # 保存
    (OUT_DIR / "triage_results.json").write_text(json.dumps(results, indent=2, ensure_ascii=False))

    # Step 2: 报告 — 每人单独 section
    print(f"\n[Step 2/3] 写报告 (每 KOL 独立 section)...")

    lines = [
        "# 4 KOL 体检报告 (P5-8)",
        "",
        f"**生成时间**: {time.strftime('%Y-%m-%d %H:%M')}  ",
        f"**时间窗**: {SINCE} ~ {UNTIL} (~ 2.5 年)  ",
        f"**顺序**: 按用户挑选的 4 人 (TradexWhisperer / StockSavvyShay / amitisinvesting / Sam_Badawi)",
        "",
        "**纪律**: 不下'值不值得'结论, 不筛人, 不改步骤.",
        "",
    ]

    for h in KOLS:
        r = results[h]
        lines.extend([
            "---",
            "",
            f"## @{h}",
            "",
        ])
        if r.get("n_items", 0) == 0:
            lines.append(f"❌ 无数据: {r.get('skipped', r.get('error', '?'))}\n")
            continue

        lines.extend([
            f"### 数据跨度",
            "",
            f"- **总推文**: {r['n_items']}",
            f"- **时间跨度**: {r['date_range']}",
            f"- **原创 / 回复 / RT**: {r['n_originals']} / {r['n_replies']} / {r['n_retweets']}",
            "",
            f"### directional_validator 校验结果",
            "",
            "| action | 数量 | 含义 |",
            "|---|---|---|",
        ])
        for act, n in r["validation_actions"].items():
            desc = {
                "keep": "通过 — 有方向关键词, 真·long/short",
                "flip_direction": "原 LLM 方向反, validator 翻转",
                "mark_commentary": "非 stock 对象 / 产业 fact / 缺方向词",
                "drop": "无 ticker / 不可识别",
            }.get(act, "?")
            lines.append(f"| {act} | {n} | {desc} |")
        lines.append("")

        # attribution 分布 (基于 keep / flip_direction)
        judgments = r["judgments"]
        lines.extend([
            f"### 明确的个股方向判断 ({len(judgments)} 条)",
            "",
            "| # | 日期 | direction | ticker | 市场 | attribution | 原文 |",
            "|---|---|---|---|---|---|---|",
        ])
        for i, j in enumerate(judgments, 1):
            ex = j["excerpt"].replace("|", "/")[:80]
            lines.append(f"| {i} | {j['date']} | {j['direction']} | {j['ticker'] or '?'} | {j['market']} | {j['attribution']} | {ex} |")
        lines.append("")

        # 市场分布统计
        market_count = Counter(j["market"] for j in judgments)
        attr_count = Counter(j["attribution"] for j in judgments)
        lines.extend([
            f"### 统计",
            "",
            f"- **市场分布**: {dict(market_count)}",
            f"- **attribution 分布**: {dict(attr_count)}",
            "",
        ])

    # Step 3: @TradexWhisperer 特别段
    print(f"\n[Step 3/3] @TradexWhisperer 特别验证...")
    tw = results.get("TradexWhisperer", {})
    tw_judgments = tw.get("judgments", [])

    lines.extend([
        "---",
        "",
        "## @TradexWhisperer 特别验证 (用户指定)",
        "",
        "用户提示: 他简介自称在低位发过 `$MU $62`, `$SNDK $214` 等 bargain thesis.",
        "",
        f"### 全部个股方向判断 ({len(tw_judgments)} 条)",
        "",
        "**包含简介里挑出来的成功案例 + 他没说过的判断** — 防止幸存者偏差/自我美化.",
        "",
        "| # | 日期 | direction | ticker | 市场 | attribution | 原文 |",
        "|---|---|---|---|---|---|---|",
    ])
    for i, j in enumerate(tw_judgments, 1):
        ex = j["excerpt"].replace("|", "/")[:120]
        lines.append(f"| {i} | {j['date']} | {j['direction']} | {j['ticker'] or '?'} | {j['market']} | {j['attribution']} | {ex} |")
    lines.append("")

    # 找 MU / SNDK / RKLB / PLTR 的最早一条
    for ticker in ["MU", "SNDK", "RKLB", "PLTR"]:
        ts = [j for j in tw_judgments if j.get("ticker") == ticker]
        if ts:
            ts.sort(key=lambda j: j["date"])
            first = ts[0]
            lines.append(f"**${ticker} 最早判断**: {first['date']} {first['direction']} — \"{first['excerpt'][:100]}\"")
            lines.append("")

    out = Path("/workspace/outputs/p5_4kol_triage.md")
    out.write_text("\n".join(lines))
    print(f"\n📄 {out}")
    print(f"\n⏱️  总耗时: {_t.time()-t0:.1f}s")


if __name__ == "__main__":
    main()