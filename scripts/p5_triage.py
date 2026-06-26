"""KOL 体检脚本 — 抓最近 20-30 条内容做市场分布 + 类型分诊

不做完整验证, 只判断两件事:
1. 市场分布: 美股 / A股 / 港股 / 韩股 / 多市场
2. 类型: 信号源 (喊具体标的买卖) / 认知源 (产分析, 不喊胜率)

对每个 handle:
- X 用户: Apify `apidojo/tweet-scraper` actor `61RPP7dywgiy0JPD0`, 拉最近 30 tweets
- Substack: `/api/v1/archive` API, 拉最新 24 posts
- 知乎: 标"无现成管道"

抓完用 LLM (deepseek-v4-pro) 分类, 输出每人一行的体检表。
"""
from __future__ import annotations
import json
import os
import subprocess
import urllib.request
import time
import argparse
import re
from pathlib import Path

APIFY_TOKEN = os.environ.get("APIFY_TOKEN", "")
DEEPSEEK_API_KEY = os.environ.get("DEEPSEEK_API_KEY", "")
ACTOR_ID = "61RPP7dywgiy0JPD0"
OUT_DIR = Path("/workspace/logs/p5_triage")
OUT_DIR.mkdir(parents=True, exist_ok=True)


# 体检候选名单 — 每行 (handle, source, x_handle_or_subdomain, notes)
CANDIDATES = [
    # 信号源候选
    ("Brad Freeman", "x", "StockMarketNerd", "美股零售交易员, 1M+ followers"),
    ("DeepVan", "zhihu", "deepvan", "知乎 KOL, 需手动取链接"),

    # 认知源
    ("Dylan Patel / SemiAnalysis", "substack", "semianalysis", "半导体重磅付费 newsletter"),
    ("Citrini Research", "x", "davidcitrini", "Bear / macro 评论"),
    ("Gavin Baker", "x", "GavinSBaker", "Hedge fund manager, ATTICUS"),
    ("Doug O'Loughlin", "x", "DougOLoughlin", "Hedge fund, KOH"),
    ("Leopold Aschenbrenner", "x", "LeopoldAschenbrenner", "AI macro, Situational Awareness"),
    ("Quartr / The Transcript", "substack", "thetranscript", "earnings transcript 整理"),

    # 新加待体检
    ("@qinbafrank", "x", "qinbafrank", "新加, 待确认"),
    ("@LinQingV", "x", "LinQingV", "新加, 待确认"),
]


# === Apify fetch ===
def apify_fetch(handle: str, max_items: int = 30) -> list[dict]:
    """Apify 拉 1 个 handle 的最近 N tweets。"""
    print(f"  Apify fetch: {handle} (max {max_items})")
    input_json = json.dumps({
        "searchTerms": [f"from:{handle}"],
        "maxItems": max_items,
        "sort": "Latest",
    })

    # 1. start run
    req = urllib.request.Request(
        f"https://api.apify.com/v2/acts/{ACTOR_ID}/runs?token={APIFY_TOKEN}",
        data=input_json.encode(),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=60) as r:
        run_info = json.loads(r.read())
    run_id = run_info.get("data", {}).get("id")
    if not run_id:
        print(f"    ! start failed: {run_info}")
        return []
    print(f"    run_id: {run_id}")

    # 2. poll (max 4 min)
    for i in range(24):
        time.sleep(10)
        req2 = urllib.request.Request(
            f"https://api.apify.com/v2/acts/{ACTOR_ID}/runs/{run_id}?token={APIFY_TOKEN}"
        )
        with urllib.request.urlopen(req2, timeout=30) as r2:
            s = json.loads(r2.read()).get("data", {}).get("status", "?")
        if i % 3 == 0:
            print(f"    [poll {i}] status: {s}")
        if s in ("SUCCEEDED", "FAILED", "ABORTED"):
            break

    if s != "SUCCEEDED":
        print(f"    ! run {s}")
        return []

    # 3. get items
    req3 = urllib.request.Request(
        f"https://api.apify.com/v2/datasets/{run_info['data']['defaultDatasetId']}/items?token={APIFY_TOKEN}&format=json&limit={max_items}"
    )
    with urllib.request.urlopen(req3, timeout=60) as r3:
        items = json.loads(r3.read())
    print(f"    → {len(items)} items")
    return items


# === Substack fetch ===
def substack_fetch(subdomain: str, max_items: int = 20) -> list[dict]:
    """Substack 拉最近 N posts。"""
    print(f"  Substack fetch: {subdomain}")
    url = f"https://{subdomain}.substack.com/api/v1/archive?sort=new&limit={max_items}"
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=30) as r:
            data = json.loads(r.read())
        print(f"    → {len(data)} posts")
        return data
    except Exception as e:
        print(f"    ! failed: {e}")
        return []


# === LLM classify ===
CLASSIFY_PROMPT = """你是 KOL 内容分诊器。给定一批最近的内容 (X 推文 / Substack 文章), 判断两件事:

【内容】{content}

【输出 JSON】
{{
  "market": "US" / "A_share" / "HK" / "KR" / "TW" / "CN_US_mixed" / "non_stock" / "?",
  "kol_type": "signal" / "knowledge" / "mixed" / "?",
  "confidence": 0-1,
  "evidence": "一句话解释 (引用原文片段 / ticker 数)"
}}

【判定规则】

market (主要市场):
- US: 多数 ticker 是美股 (NVDA, AAPL, TSLA, etc.) 或美股 ETF (SPY, SOXX, SMH)
- A_share: 多数 ticker 是 A 股 (贵州茅台 600519, 宁德 300750, .SZ, .SS 等)
- HK: 港股 (.HK, 00700 腾讯, 09988 阿里)
- KR: 韩股 (.KS, 000660 SK Hynix, 005930 三星)
- TW: 台股 (.TW, 2330 TSMC, 2455 联发科)
- CN_US_mixed: 中美混合
- non_stock: 几乎不涉及股票 (纯产业 / 政治 / 加密 commentary)
- ?: 内容太少看不出

kol_type (类型):
- signal: 喊具体标的买卖方向 (有 $TICKER + buy/sell/long/short/推荐/不推荐)
  e.g. "I'm buying NVDA", "$MU 推荐加仓", "AVGO 看空"
- knowledge: 产分析 / 趋势 / 框架, 不喊具体买卖 (像分析师报告 / 产业研究)
  e.g. "中国 EV 产业链分析", "AI infra 投资逻辑", "GAAFET vs FinFET"
- mixed: 两者都有 (e.g. Dylan Patel 偶尔喊 TSMC long 但主要是 analysis)
- ?: 内容太少看不出

【置信度】
- 0.9+: 30+ 条内容, market/type 明显
- 0.7: 10-30 条, 大体清晰
- 0.5: 5-10 条, 弱判断
- 0.3: < 5 条, 纯 guess
"""


def llm_classify(content_summary: str) -> dict:
    """LLM classify 一批内容。"""
    prompt = CLASSIFY_PROMPT.format(content=content_summary[:6000])  # 限 6K
    data = json.dumps({
        "model": "deepseek-v4-pro",
        "messages": [{"role": "user", "content": prompt}],
        "response_format": {"type": "json_object"},
        "temperature": 0.1,
        "max_tokens": 1500,  # 给 LLM 充足空间 (reasoning_content 占 token)
    }).encode()
    req = urllib.request.Request(
        "https://api.deepseek.com/chat/completions",
        data=data,
        headers={"Authorization": f"Bearer {DEEPSEEK_API_KEY}", "Content-Type": "application/json"},
    )
    try:
        with urllib.request.urlopen(req, timeout=60) as r:
            resp = json.loads(r.read())
        return json.loads(resp["choices"][0]["message"]["content"])
    except Exception as e:
        return {"market": "?", "kol_type": "?", "confidence": 0, "evidence": f"LLM failed: {e}"}


def triage_x_handle(name: str, handle: str) -> dict:
    """体检 1 个 X handle。"""
    items = apify_fetch(handle, max_items=30)
    if not items:
        return {"name": name, "handle": handle, "platform": "x", "n_items": 0, "skipped": "no_data"}
    # 保存 raw
    out_path = OUT_DIR / f"x_{handle}.json"
    out_path.write_text(json.dumps(items, indent=2, ensure_ascii=False))
    # 抽 ticker + text
    snippets = []
    ticker_count: dict[str, int] = {}
    for it in items:
        text = it.get("text") or it.get("fullText") or ""
        # 抓 $TICKER 或裸 ticker (大写 1-5 字母)
        tickers = re.findall(r"\$([A-Z]{1,5})\b", text) + re.findall(r"\b([A-Z]{2,5})\b", text[:500])
        for t in tickers:
            ticker_count[t] = ticker_count.get(t, 0) + 1
        snippets.append(f"[{it.get('createdAt', '?')[:10]}] {text[:200]}")
    content_summary = "\n".join(snippets[:25])  # 限 25 条
    top_tickers = sorted(ticker_count.items(), key=lambda x: -x[1])[:15]
    # LLM classify
    cls = llm_classify(content_summary)
    return {
        "name": name,
        "handle": handle,
        "platform": "x",
        "n_items": len(items),
        "top_tickers": top_tickers,
        "classification": cls,
    }


def triage_substack(name: str, subdomain: str) -> dict:
    """体检 1 个 Substack。"""
    items = substack_fetch(subdomain, max_items=20)
    if not items:
        return {"name": name, "subdomain": subdomain, "platform": "substack", "n_items": 0, "skipped": "no_data"}
    out_path = OUT_DIR / f"ss_{subdomain}.json"
    out_path.write_text(json.dumps(items, indent=2, ensure_ascii=False))
    snippets = []
    for p in items[:15]:
        title = p.get("title", "")
        body_excerpt = (p.get("body") or "")[:300]
        date = p.get("post_date", "?")[:10]
        snippets.append(f"[{date}] {title}\n{body_excerpt}")
    content_summary = "\n\n---\n\n".join(snippets)
    cls = llm_classify(content_summary)
    return {
        "name": name,
        "subdomain": subdomain,
        "platform": "substack",
        "n_items": len(items),
        "classification": cls,
    }


# === 报告渲染 ===
def render_triage_report(results: list[dict]) -> str:
    """生成体检 markdown 表。"""
    lines = [
        "# KOL 体检分诊报告 (P5-1)",
        "",
        f"**生成时间**: {time.strftime('%Y-%m-%d %H:%M')}  ",
        f"**候选总数**: {len(results)}  ",
        f"**判定维度**: 市场分布 (US/A/HK/KR/TW/mixed) + 类型 (signal/knowledge/mixed)",
        "",
        "| KOL | Platform | n | 市场 | 类型 | 置信度 | 备注 |",
        "|---|---|---|---|---|---|---|",
    ]
    for r in results:
        name = r["name"]
        plat = r["platform"]
        n = r.get("n_items", 0)
        if "skipped" in r:
            lines.append(f"| {name} | {plat} | 0 | ? | ? | 0 | ⚠️ {r['skipped']} |")
            continue
        cls = r.get("classification", {})
        market = cls.get("market", "?")
        ktype = cls.get("kol_type", "?")
        conf = cls.get("confidence", 0)
        ev = (cls.get("evidence", "") or "")[:60]
        # 候选可执行性
        if market == "US" and ktype == "signal":
            verdict = "✅ 美股信号源, 跑胜率管道"
        elif market == "US" and ktype in ("knowledge", "mixed"):
            verdict = "🟡 美股认知源, 走主题/卡点提炼"
        elif market in ("A_share", "HK"):
            verdict = "❌ A/H 股, Polygon 验不了, 暂缓"
        elif market in ("KR", "TW"):
            verdict = "❌ 韩国/台股, Polygon 验不了, 暂缓"
        elif market == "non_stock":
            verdict = "❌ 非股票, 跳过胜率管道"
        else:
            verdict = "❓ 待定"
        # 加 top_tickers
        top_t = r.get("top_tickers", [])[:5]
        if top_t:
            ticker_str = ", ".join([f"{t[0]}({t[1]})" for t in top_t])
            ev = f"{ev} | top: {ticker_str}"
        lines.append(f"| {name} | {plat} | {n} | {market} | {ktype} | {conf:.1f} | {verdict} |")

    lines.extend([
        "",
        "## 详细 Evidence",
        "",
    ])
    for r in results:
        name = r["name"]
        cls = r.get("classification", {})
        ev = cls.get("evidence", "")
        if ev:
            lines.append(f"### {name}")
            lines.append(f"> {ev}")
            if r.get("top_tickers"):
                lines.append(f"> top tickers: {r['top_tickers'][:10]}")
            lines.append("")

    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--only", nargs="*", help="只跑这些 (name 模糊匹配)")
    args = parser.parse_args()

    results = []
    for name, source, handle, notes in CANDIDATES:
        if args.only and not any(o in name for o in args.only):
            continue
        print(f"\n=== {name} ({source}) ===")
        if source == "x":
            r = triage_x_handle(name, handle)
        elif source == "substack":
            r = triage_substack(name, handle)
        elif source == "zhihu":
            r = {"name": name, "platform": "zhihu", "n_items": 0, "skipped": "无现成管道, 待手动"}
        else:
            r = {"name": name, "platform": source, "n_items": 0, "skipped": f"未知 source: {source}"}
        r["notes"] = notes
        results.append(r)

    # 保存 + 报告
    (OUT_DIR / "triage_results.json").write_text(json.dumps(results, indent=2, ensure_ascii=False))
    report = render_triage_report(results)
    out = Path("/workspace/outputs/p5_triage_report.md")
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(report)
    print(f"\n📄 报告: {out}")


if __name__ == "__main__":
    main()