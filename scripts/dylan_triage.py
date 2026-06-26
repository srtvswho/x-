"""Dylan Patel (@dylan522p / SemiAnalysis) 情报源分诊

核心问题: 他的 X 内容是"领先产业情报" 还是 "已被市场消化的观点"?
预期: 大量产业事实/数据 (情报) + 少量方向性判断

策略:
1. 抓 3-6 月 X 内容 (并发)
2. LLM 分类每条推文: 产业事实 vs 方向判断 vs commentary
3. 提取"产业事实"样本 + "方向判断"样本 (供用户读)
4. 评估情报价值: 提前量 / 一手性 / 准确性
"""
from __future__ import annotations
import json
import os
import re
import time
import urllib.request
from pathlib import Path
from collections import Counter
from concurrent.futures import ThreadPoolExecutor, as_completed

APIFY_TOKEN = os.environ.get("APIFY_TOKEN", "")
DEEPSEEK_API_KEY = os.environ.get("DEEPSEEK_API_KEY", "")
ACTOR_ID = "61RPP7dywgiy0JPD0"
OUT_DIR = Path("/workspace/logs/p5_dylan")
OUT_DIR.mkdir(parents=True, exist_ok=True)
MAX_WORKERS_APIFY = 3
MAX_WORKERS_LLM = 10


def apify_fetch_period(handle: str, since: str, until: str, max_items: int = 300) -> list[dict]:
    print(f"  Apify: {handle} {since}..{until}")
    # 注意: actor 接受 since/until only if embedded right; pure from:handle sort Latest
    # 用多段单独跑以保证时间覆盖
    input_json = json.dumps({
        "searchTerms": [f"from:{handle} since:{since} until:{until}"],
        "maxItems": max_items,
        "sort": "Latest",
    })
    for retry in range(3):
        try:
            req = urllib.request.Request(
                f"https://api.apify.com/v2/acts/{ACTOR_ID}/runs?token={APIFY_TOKEN}",
                data=input_json.encode(),
                headers={"Content-Type": "application/json"},
                method="POST",
            )
            with urllib.request.urlopen(req, timeout=60) as r:
                run_info = json.loads(r.read())
            break
        except Exception as e:
            print(f"    start retry {retry+1}: {e}")
            time.sleep(5 * (retry + 1))
    run_id = run_info.get("data", {}).get("id")
    if not run_id:
        return []
    s = "?"
    for i in range(25):
        time.sleep(8)
        try:
            with urllib.request.urlopen(
                f"https://api.apify.com/v2/acts/{ACTOR_ID}/runs/{run_id}?token={APIFY_TOKEN}",
                timeout=30,
            ) as r2:
                s = json.loads(r2.read()).get("data", {}).get("status", "?")
        except Exception:
            continue
        if s in ("SUCCEEDED", "FAILED", "ABORTED"):
            break
    if s != "SUCCEEDED":
        return []
    try:
        with urllib.request.urlopen(
            f"https://api.apify.com/v2/datasets/{run_info['data']['defaultDatasetId']}/items?token={APIFY_TOKEN}&format=json&limit={max_items}",
            timeout=60,
        ) as r3:
            return json.loads(r3.read())
    except Exception:
        return []


def fetch_dylan() -> list[dict]:
    """3 段并发抓 @dylan522p。"""
    periods = [
        ("2026-04-01", "2026-06-22"),
        ("2025-12-01", "2026-03-31"),
        ("2025-08-01", "2025-11-30"),
    ]
    print(f"  并发 {len(periods)} 段 (workers={MAX_WORKERS_APIFY})...")
    all_items = []
    seen = set()
    with ThreadPoolExecutor(max_workers=MAX_WORKERS_APIFY) as pool:
        futures = {pool.submit(apify_fetch_period, "dylan522p", s, u, 300): (s, u) for s, u in periods}
        for fut in as_completed(futures):
            s, u = futures[fut]
            try:
                items = fut.result()
            except Exception as e:
                print(f"  period {s}..{u}: error {e}")
                continue
            new = 0
            for it in items:
                tid = it.get("id") or it.get("tweetId") or ""
                if tid and tid not in seen:
                    seen.add(tid)
                    all_items.append(it)
                    new += 1
            print(f"  {s}..{u}: {new} new (total {len(all_items)})")
    all_items.sort(key=lambda x: x.get("createdAt", ""), reverse=True)
    return all_items


# === 类型分类 LLM ===
TYPE_PROMPT = """你是半导体/AI 产业推文分类器。给定一条推文, 判断类型:

【推文】{text}
【日期】{date}

【3 类选 1】
- **情报 (intel)**: 产业事实/数据/一手信息陈述 — 涉及产能、客户、技术细节、供应链、人事变动、财报具体数字等可证事实
  e.g. "TSMC CoWoS-S capacity 30k/月到 2026 Q3", "Samsung HBM3E 良率达 70%", "某客户 capex 翻倍"
- **判断 (judgment)**: 作者方向性表态 — "我认为 X 会怎样 / 我看多 / 我看空 / 我预期"
  e.g. "I think NVDA will outperform in 2026", "我们认为 AI infra 仍是主线"
- **观点/评论 (commentary)**: 既有事实也有判断, 偏向评论 — "这是一次非常糟糕的财报", "这对市场意味着..."

【输出 JSON】
{{
  "type": "intel" / "judgment" / "commentary",
  "industry_tags": ["HBM" / "CoWoS" / "光刻机" / "AI infra" / "数据中心" / "晶圆" / "..."],
  "claim_verifiability": "high" / "medium" / "low" (高=具体数字/可证, 低=模糊/不可证),
  "key_fact": "一句话提取关键事实 (如果是 intel 或 commentary)",
  "key_judgment": "一句话提取判断 (如果是 judgment 或 commentary)"
}}
"""


def llm_classify_one(text: str, date: str) -> dict:
    prompt = TYPE_PROMPT.format(text=text[:1500], date=date)
    data = json.dumps({
        "model": "deepseek-v4-pro",
        "messages": [{"role": "user", "content": prompt}],
        "response_format": {"type": "json_object"},
        "temperature": 0.1,
        "max_tokens": 1500,
    }).encode()
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
                raise ValueError("empty")
            return json.loads(cs)
        except Exception as e:
            if retry < 2:
                time.sleep(2 * (retry + 1))
    return {"type": "?", "key_fact": "?", "key_judgment": "?"}


def classify_batch(items: list[dict]) -> list[dict]:
    """并发分类一批推文。"""
    print(f"  并发分类 {len(items)} 条 (workers={MAX_WORKERS_LLM})...")
    results = [None] * len(items)
    with ThreadPoolExecutor(max_workers=MAX_WORKERS_LLM) as pool:
        futures = {i: pool.submit(llm_classify_one, it.get("text", "") or it.get("fullText", ""), it.get("createdAt", "?")[:10]) for i, it in enumerate(items)}
        for i, fut in futures.items():
            try:
                results[i] = fut.result()
            except Exception as e:
                results[i] = {"type": "?", "error": str(e)}
            if (i + 1) % 50 == 0:
                print(f"    {i+1}/{len(items)} done")
    return results


def main():
    import time as _t
    t0 = _t.time()
    print("=" * 60)
    print("Dylan Patel (@dylan522p) — 情报源分诊")
    print("=" * 60)

    # Step 1: 抓
    print("\n[1/3] 抓 @dylan522p X 内容 (3-6 月)...")
    items = fetch_dylan()
    print(f"  total: {len(items)}")
    # 过滤 2025-12-01 之后
    from datetime import datetime
    cutoff = datetime(2025, 12, 1).timestamp()
    filtered = []
    for it in items:
        ca = it.get("createdAt", "")
        try:
            dt = datetime.strptime(ca, "%a %b %d %H:%M:%S %z %Y")
            if dt.timestamp() >= cutoff:
                filtered.append(it)
        except Exception:
            pass
    print(f"  过滤后 (>=2025-12-01): {len(filtered)} 条")
    (OUT_DIR / "tweets_filtered.json").write_text(json.dumps(filtered, indent=2, ensure_ascii=False))
    items = filtered

    # Step 2: 过滤原创 + 分类
    print("\n[2/3] 过滤原创 + 并发分类...")
    originals = [it for it in items if not it.get("isReply") and not it.get("isRetweet")]
    reply = len(items) - len(originals)
    print(f"  原创 {len(originals)} / 回复+转发 {reply}")
    classified = classify_batch(originals)
    # merge
    enriched = []
    for it, cls in zip(originals, classified):
        merged = dict(it)
        merged["_type"] = cls.get("type", "?")
        merged["_tags"] = cls.get("industry_tags", [])
        merged["_claim_verifiability"] = cls.get("claim_verifiability", "?")
        merged["_key_fact"] = cls.get("key_fact", "")
        merged["_key_judgment"] = cls.get("key_judgment", "")
        enriched.append(merged)
    (OUT_DIR / "classified.json").write_text(json.dumps(enriched, indent=2, ensure_ascii=False))

    # Step 3: 统计 + 抽样
    print("\n[3/3] 类型统计 + 情报/判断 抽样...")
    type_count = Counter(e["_type"] for e in enriched)
    n = len(enriched)
    print(f"  类型分布: {dict(type_count)}")
    for t, c in type_count.most_common():
        print(f"    {t}: {c} ({c/n*100:.1f}%)")

    # 情报样本 (按 verifiability high 优先)
    intel = [e for e in enriched if e["_type"] == "intel"]
    intel.sort(key=lambda e: (e["_claim_verifiability"] == "high", e["_claim_verifiability"] == "medium"), reverse=True)
    print(f"\n  情报型 (intel) 样本: {len(intel)} 条, 选 top 10:")
    samples_intel = intel[:10]

    # 判断样本
    judgment = [e for e in enriched if e["_type"] == "judgment"]
    print(f"  判断型 (judgment) 样本: {len(judgment)} 条, 选 top 10:")
    samples_judgment = judgment[:10]

    # commentary
    commentary = [e for e in enriched if e["_type"] == "commentary"]
    samples_commentary = commentary[:5]

    # tag 分布
    all_tags: Counter = Counter()
    for e in enriched:
        for t in e.get("_tags", []):
            all_tags[t] += 1
    print(f"\n  产业标签 Top 15:")
    for t, c in all_tags.most_common(15):
        print(f"    {t}: {c}")

    # 报告
    report = render_report(enriched, type_count, all_tags, samples_intel, samples_judgment, samples_commentary)
    out_md = Path("/workspace/outputs/p5_dylan_intel_triage.md")
    out_md.write_text(report)
    print(f"\n📄 报告: {out_md}")
    print(f"\n⏱️  总耗时: {_t.time()-t0:.1f}s")


def render_report(enriched, type_count, all_tags, intel_samples, judgment_samples, commentary_samples):
    n = len(enriched)
    lines = [
        "# Dylan Patel (@dylan522p / SemiAnalysis) — 情报源分诊",
        "",
        "**核心问题**: 他的 X 免费内容 = 领先产业情报 vs 已被市场消化的观点?",
        "",
        f"**总推文**: {n} 条 (原创)  ",
        f"**生成时间**: {time.strftime('%Y-%m-%d %H:%M')}",
        "",
        "## 1. 类型分布",
        "",
        "| 类型 | n | 占比 | 含义 |",
        "|---|---|---|---|",
    ]
    type_desc = {
        "intel": "产业事实/数据 (一手情报)",
        "judgment": "方向性判断 (预测/观点)",
        "commentary": "混合评论 (事实+判断)",
    }
    for t, c in type_count.most_common():
        lines.append(f"| **{t}** | {c} | {c/n*100:.1f}% | {type_desc.get(t, '?')} |")

    # 关键结论
    intel_pct = type_count.get("intel", 0) / n * 100
    judgment_pct = type_count.get("judgment", 0) / n * 100
    if intel_pct >= 60:
        verdict = f"**情报型 (intel {intel_pct:.0f}%) 主导** — 他的免费 X 主要是产业情报, 不是喊单"
    elif judgment_pct >= 60:
        verdict = f"**判断型 (judgment {judgment_pct:.0f}%) 主导** — 他的免费 X 是观点/预测"
    else:
        verdict = f"**混合型** — 情报 {intel_pct:.0f}% / 判断 {judgment_pct:.0f}% / 评论 {type_count.get('commentary',0)/n*100:.0f}%"
    lines.extend([
        "",
        f"### 结论: {verdict}",
        "",
    ])

    # 产业标签
    lines.extend([
        "## 2. 产业标签 Top 15",
        "",
        "| 标签 | 推文数 |",
        "|---|---|",
    ])
    for t, c in all_tags.most_common(15):
        lines.append(f"| {t} | {c} |")

    # 情报样本 (重点)
    lines.extend([
        "",
        "## 3. 情报型 (intel) 样本 Top 10",
        "",
        "**这一节最重要** — 看你读他原文, 判断情报价值",
        "",
    ])
    for i, e in enumerate(intel_samples, 1):
        date = (e.get("createdAt") or "?")[:10]
        text = (e.get("text") or e.get("fullText") or "")[:280]
        tags = ", ".join(e.get("_tags", []))[:50]
        fact = e.get("_key_fact", "")[:80]
        verif = e.get("_claim_verifiability", "?")
        lines.extend([
            f"### #{i} [{date}] verifiability={verif}",
            f"**Tags**: {tags}",
            f"**Key fact**: {fact}",
            f"**原文**: {text}",
            "",
        ])

    # 判断样本
    lines.extend([
        "## 4. 判断型 (judgment) 样本 Top 10",
        "",
    ])
    if judgment_samples:
        for i, e in enumerate(judgment_samples, 1):
            date = (e.get("createdAt") or "?")[:10]
            text = (e.get("text") or e.get("fullText") or "")[:280]
            judgment = e.get("_key_judgment", "")[:80]
            lines.extend([
                f"### #{i} [{date}]",
                f"**Judgment**: {judgment}",
                f"**原文**: {text}",
                "",
            ])
    else:
        lines.append("⚠️ 几乎没有纯判断型推文 (他不做方向预测)\n")

    # Commentary 样本
    lines.extend([
        "## 5. 混合评论 (commentary) 样本 Top 5",
        "",
    ])
    for i, e in enumerate(commentary_samples, 1):
        date = (e.get("createdAt") or "?")[:10]
        text = (e.get("text") or e.get("fullText") or "")[:250]
        lines.append(f"### #{i} [{date}]\n> {text}\n")

    return "\n".join(lines)


if __name__ == "__main__":
    main()