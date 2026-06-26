"""4 KOL attribution 并发跑 — 25 路, 每条独立 try/except"""
import json
import os
import re
import time
import sys
import urllib.request
from concurrent.futures import ThreadPoolExecutor, as_completed
from collections import Counter
from pathlib import Path

sys.path.insert(0, "/workspace")
from signalboard.extract.directional_validator import validate_directional

OUT_DIR = Path("/workspace/logs/p5_4kol_triage")
DEEPSEEK_API_KEY = os.environ["DEEPSEEK_API_KEY"]
KOLS = ["TradexWhisperer", "StockSavvyShay", "amitisinvesting", "Sam_Badawi"]

MAX_WORKERS = 25  # 用户指定 20-30 区间

ATTRIBUTION_PROMPT = """你是内容归属判定器。给定一条 X 推文, 判定判断归属。

【内容】{text}
【日期】{date}

【3 选 1】
- ORIGINAL: 作者自己的判断 (e.g. "I think / in my view / 我认为")
- RELAYED: 转述/搬运机构 (e.g. "Goldman says / 据 Bloomberg")
- RELAYED+COMMENT: 搬运 + 加自己判断 (e.g. 转述研报后说 "However, I see it differently")

【输出 JSON】
{{
  "attribution": "ORIGINAL" / "RELAYED" / "RELAYED+COMMENT" / "news" / "commentary" / "?",
  "evidence": "一句话解释"
}}

news = 纯新闻聚合 (无个人判断)
commentary = 评价/感慨 (无明确方向)
"""


def llm_attribution(text: str, date: str) -> dict:
    """单条 attribution, 3 次 retry, 独立 try/except 不连带."""
    prompt = ATTRIBUTION_PROMPT.format(text=text[:1500], date=date)
    data = json.dumps({
        "model": "deepseek-v4-pro",
        "messages": [{"role": "user", "content": prompt}],
        "response_format": {"type": "json_object"},
        "temperature": 0.1,
        "max_tokens": 600,
    }).encode()
    last_err = "?"
    for retry in range(3):
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
                raise ValueError("empty content")
            return json.loads(cs)
        except Exception as e:
            last_err = str(e)
            if retry < 2:
                time.sleep(2 * (retry + 1))
    return {"attribution": "?", "evidence": f"err: {last_err[:50]}"}


def main():
    import time as _t
    t0 = _t.time()
    print(f"[{_t.time()-t0:.0f}s] 开始 4 KOL attribution 并发 (workers={MAX_WORKERS})", flush=True)

    # 加载之前 quick_triage 的 judgments (有 date/direction/ticker/excerpt)
    quick = json.load(open(OUT_DIR / "quick_triage.json"))

    # 重新加载 raw, 拿到完整 items (我们需要 text_snippet)
    # 因为 quick_triage 的 excerpt 是 truncate 200 字符, 但 LLM 用 1500 字符
    # 所以我们用原始 raw_*.json 重新跑 directional_validator
    A_SHARE_RE = re.compile(r"\b[0-9]{6}\.(?:SH|SZ|SS)\b")
    HK_RE = re.compile(r"\b[0-9]{4,5}\.HK\b")
    KR_RE = re.compile(r"\b[0-9]{6}\.(?:KS|KQ)\b")
    TW_RE = re.compile(r"\b[0-9]{4}\.(?:TW|TWO)\b")

    def market_of_text(text, ticker):
        if ticker:
            if KR_RE.search(ticker): return "KR"
            if TW_RE.search(ticker): return "TW"
            if HK_RE.search(ticker): return "HK"
            if A_SHARE_RE.search(ticker): return "A_share"
            return "US"
        if A_SHARE_RE.search(text): return "A_share"
        if HK_RE.search(text): return "HK"
        if KR_RE.search(text): return "KR"
        if TW_RE.search(text): return "TW"
        if re.search(r"\$([A-Z]{1,5})\b", text): return "US"
        return "?"

    results = {}
    for h in KOLS:
        print(f"[{_t.time()-t0:.0f}s] 处理 @{h}...", flush=True)
        items = json.load(open(OUT_DIR / f"raw_{h}.json"))

        # 先 directional + market (无 LLM, 快)
        judgments = []
        for it in items:
            text = it.get("text") or it.get("fullText") or ""
            if not text:
                continue
            dollar_t = re.findall(r"\$([A-Z]{1,5})\b", text)
            ticker = dollar_t[0] if dollar_t else None
            v = validate_directional(text, ticker or "", "auto")
            if v.action in ("keep", "flip_direction"):
                judgments.append({
                    "date": (it.get("createdAt") or "?")[:10],
                    "direction": v.final_direction,
                    "ticker": ticker,
                    "market": market_of_text(text, ticker),
                    "excerpt": text[:200],
                    "text_full": text[:1500],  # 用于 LLM attribution
                    "source_id": it.get("id"),
                    "_attr": None,  # 后面并发填
                })
        print(f"  judgments={len(judgments)}", flush=True)

        # 并发 attribution
        def attr_one(j):
            return j, llm_attribution(j["text_full"], j["date"])

        n_done = 0
        n_err = 0
        with ThreadPoolExecutor(max_workers=MAX_WORKERS) as pool:
            futures = {pool.submit(attr_one, j): i for i, j in enumerate(judgments)}
            for fut in as_completed(futures):
                try:
                    j, attr = fut.result()
                    j["_attr"] = attr
                    if attr.get("attribution") == "?":
                        n_err += 1
                    n_done += 1
                    if n_done % 50 == 0:
                        print(f"  [{_t.time()-t0:.0f}s]   attribution {n_done}/{len(judgments)} (err={n_err})", flush=True)
                except Exception as e:
                    n_err += 1
                    n_done += 1
                    print(f"  attr error: {e}", flush=True)

        # 把 attribution 提到顶层
        for j in judgments:
            j["attribution"] = j["_attr"].get("attribution", "?") if j["_attr"] else "?"
            j["attribution_evidence"] = j["_attr"].get("evidence", "") if j["_attr"] else ""

        results[h] = {
            "n_items": len(items),
            "n_judgments": len(judgments),
            "n_attr_err": n_err,
            "judgments": judgments,
        }

        # 统计
        attr_count = Counter(j["attribution"] for j in judgments)
        market_count = Counter(j["market"] for j in judgments)
        results[h]["attribution_count"] = dict(attr_count)
        results[h]["market_count"] = dict(market_count)

        print(f"  attribution: {dict(attr_count)}", flush=True)
        print(f"  market: {dict(market_count)}", flush=True)
        print(f"  [{_t.time()-t0:.0f}s] saved", flush=True)

    # 保存
    (OUT_DIR / "attribution_results.json").write_text(json.dumps(results, indent=2, ensure_ascii=False))

    # 报告
    lines = [
        "# 4 KOL 体检 — 完整版 (P5-8)",
        "",
        f"**生成时间**: {time.strftime('%Y-%m-%d %H:%M')}  ",
        f"**并发**: {MAX_WORKERS} workers",
        "",
        "**纪律**: 不下'值不值得'结论, 不筛人, 不改步骤 (仅串行→并发).",
        "",
    ]

    for h in KOLS:
        r = results[h]
        judgments = r["judgments"]
        attr_count = Counter(j["attribution"] for j in judgments)
        market_count = Counter(j["market"] for j in judgments)

        lines.extend([
            "---",
            "",
            f"## @{h}",
            "",
            f"### 数据",
            "",
            f"- 抓取条数: {r['n_items']}",
            f"- 个股方向判断 (keep+flip): {r['n_judgments']}",
            f"- attribution 失败: {r['n_attr_err']}",
            "",
            "### 类型分布 (attribution)",
            "",
            "| 类型 | 数量 | 占比 | 含义 |",
            "|---|---|---|---|",
        ])
        total = sum(attr_count.values()) or 1
        desc = {
            "ORIGINAL": "作者自己的判断 (I think / in my view)",
            "RELAYED": "搬运机构观点 (Goldman says / 据 Bloomberg)",
            "RELAYED+COMMENT": "搬运 + 加自己判断",
            "news": "纯新闻聚合",
            "commentary": "评价/感慨, 无明确方向",
            "?": "LLM 失败/未识别",
        }
        for t, c in attr_count.most_common():
            lines.append(f"| {t} | {c} | {c/total*100:.1f}% | {desc.get(t, '?')} |")
        lines.append("")

        # 市场分布
        lines.extend([
            "### 市场分布",
            "",
            "| 市场 | 数量 | 占比 |",
            "|---|---|---|",
        ])
        for m, c in market_count.most_common():
            lines.append(f"| {m} | {c} | {c/total*100:.1f}% |")
        lines.append("")

        # 个股判断完整列表
        lines.extend([
            f"### 个股方向判断完整列表 ({len(judgments)} 条)",
            "",
            "| # | 日期 | direction | ticker | 市场 | attribution | 原文 |",
            "|---|---|---|---|---|---|---|",
        ])
        for i, j in enumerate(judgments, 1):
            ex = j["excerpt"].replace("|", "/")[:80]
            lines.append(f"| {i} | {j['date']} | {j['direction']} | {j['ticker'] or '?'} | {j['market']} | {j['attribution']} | {ex} |")
        lines.append("")

    # TradexWhisperer 特别段
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

    for ticker in ["MU", "SNDK", "RKLB", "PLTR"]:
        ts = [j for j in tw_judgments if j.get("ticker") == ticker]
        if ts:
            ts.sort(key=lambda j: j["date"])
            first = ts[0]
            lines.append(f"**${ticker} 最早判断**: {first['date']} {first['direction']} — \"{first['excerpt'][:100]}\"")
            lines.append("")

    out = Path("/workspace/outputs/p5_4kol_triage.md")
    out.write_text("\n".join(lines))
    print(f"[{_t.time()-t0:.0f}s] 📄 {out}", flush=True)
    print(f"[{_t.time()-t0:.0f}s] ⏱️  总耗时: {_t.time()-t0:.1f}s", flush=True)


if __name__ == "__main__":
    main()