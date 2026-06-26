"""4 KOL 体检 v2 — 独立脚本, 后台跑"""
import json
import os
import re
import time
import sys
from collections import Counter
from pathlib import Path
import urllib.request

sys.path.insert(0, "/workspace")
from signalboard.extract.directional_validator import validate_directional

OUT_DIR = Path("/workspace/logs/p5_4kol_triage")
DEEPSEEK_API_KEY = os.environ["DEEPSEEK_API_KEY"]

KOLS = ["TradexWhisperer", "StockSavvyShay", "amitisinvesting", "Sam_Badawi"]
SINCE = "2024-01-01"
UNTIL = "2026-06-22"

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


A_SHARE_RE = re.compile(r"\b[0-9]{6}\.(?:SH|SZ|SS)\b")
HK_RE = re.compile(r"\b[0-9]{4,5}\.HK\b")
KR_RE = re.compile(r"\b[0-9]{6}\.(?:KS|KQ)\b")
TW_RE = re.compile(r"\b[0-9]{4}\.(?:TW|TWO)\b")


def market_of_text(text: str, ticker):
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


def triage(handle):
    items = json.load(open(OUT_DIR / f"raw_{handle}.json"))
    if not items:
        return {"handle": handle, "n_items": 0}
    dates = sorted({(it.get("createdAt") or "?")[:10] for it in items if it.get("createdAt")})
    date_range = f"{dates[0]} ~ {dates[-1]}" if dates else "?"
    originals = [it for it in items if not it.get("isReply") and not it.get("isRetweet")]
    replies = [it for it in items if it.get("isReply")]
    retweets = [it for it in items if it.get("isRetweet")]

    judgments = []
    type_count = Counter()
    for it in items:
        text = (it.get("text") or it.get("fullText") or "")
        if not text:
            continue
        dollar_t = re.findall(r"\$([A-Z]{1,5})\b", text)
        ticker = dollar_t[0] if dollar_t else None
        v = validate_directional(text, ticker or "", "auto")
        type_count[v.action] += 1
        if v.action in ("keep", "flip_direction"):
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
    print(f"[{_t.time()-t0:.0f}s] 开始 4 KOL 体检", flush=True)

    results = {}
    for h in KOLS:
        print(f"[{_t.time()-t0:.0f}s] 处理 @{h}...", flush=True)
        r = triage(h)
        results[h] = r
        n_j = len(r.get("judgments", []))
        print(f"  items={r['n_items']} judgments={n_j}", flush=True)

    (OUT_DIR / "triage_results.json").write_text(json.dumps(results, indent=2, ensure_ascii=False))
    print(f"[{_t.time()-t0:.0f}s] saved triage_results.json", flush=True)

    # 报告
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
            lines.append(f"❌ 无数据\n")
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

        market_count = Counter(j["market"] for j in judgments)
        attr_count = Counter(j["attribution"] for j in judgments)
        lines.extend([
            f"### 统计",
            "",
            f"- **市场分布**: {dict(market_count)}",
            f"- **attribution 分布**: {dict(attr_count)}",
            "",
        ])

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


if __name__ == "__main__":
    main()