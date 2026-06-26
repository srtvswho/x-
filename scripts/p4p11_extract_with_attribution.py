"""P4-11 合并 X + Substack, LLM 抽预测 + ORIGINAL/RELAYED 归属

关键: 每条内容 (推文/文章) 标 3 类:
- ORIGINAL: 他自己的判断 (I think / my view / in my opinion)
- RELAYED: 转述机构观点 (GF Securities / TrendForce / Nomura / 某研报)
- RELAYED+COMMENT: 搬运 + 加自己判断

只把 ORIGINAL + RELAYED+COMMENT 的预测计入胜率。
"""
import os, json, time, urllib.request, glob
from datetime import datetime
from collections import Counter, defaultdict

DS_KEY = os.environ["DEEPSEEK_API_KEY"]


def call_ds(prompt, max_tokens=2000, retries=2):
    data = json.dumps({
        "model": "deepseek-v4-pro",
        "messages": [{"role": "user", "content": prompt}],
        "response_format": {"type": "json_object"},
        "temperature": 0.1,
        "max_tokens": max_tokens,
    }).encode()
    req = urllib.request.Request(
        "https://api.deepseek.com/chat/completions",
        data=data,
        headers={"Authorization": f"Bearer {DS_KEY}", "Content-Type": "application/json"},
    )
    for attempt in range(retries):
        try:
            with urllib.request.urlopen(req, timeout=60) as r:
                resp = json.loads(r.read())
            return json.loads(resp["choices"][0]["message"]["content"])
        except Exception as e:
            if attempt == retries - 1:
                return None
            time.sleep(1)


# ============ 合并 X ============
print("=== 合并 X 长段时间 ===")
all_x = []
for f in sorted(glob.glob("/workspace/logs/p4p10d_x/*.json")):
    items = json.load(open(f))
    print(f"  {f.split('/')[-1]}: {len(items)}")
    all_x.extend(items)

# 去重 (按 id)
seen = set()
unique_x = []
for it in all_x:
    tid = it.get("id")
    if tid and tid not in seen:
        seen.add(tid)
        unique_x.append(it)
unique_x.sort(key=lambda x: x.get("createdAt", ""))
print(f"去重后: {len(unique_x)} X 推文")
print(f"最早: {unique_x[0].get('createdAt','')}")
print(f"最晚: {unique_x[-1].get('createdAt','')}")

# ============ 合并 Substack ============
with open("/workspace/logs/p4p10c_substack_with_bodies.json") as f:
    substack = json.load(f)
print(f"\nSubstack posts: {len(substack)}")
print(f"  公开 + 全文: {sum(1 for p in substack if p.get('body_source') == 'fetched_html')}")
print(f"  付费 + truncated: {sum(1 for p in substack if p.get('body_source') == 'paywall_partial')}")

# ============ LLM 抽取 + ORIGINAL/RELAYED 判定 ============
print("\n" + "=" * 80)
print("Step 3: LLM 抽取 + ORIGINAL/RELAYED 归属判定")
print("=" * 80)

EXTRACT_PROMPT = """你是股票预测内容分析器。给定一条内容 (X 推文 或 Substack 摘要),识别其中关于具体股票/标的的【预测性陈述】,并判定【判断归属】。

【内容来源】{source} (X = Twitter 推文, Substack = 长文)

【内容】{text}

【判定规则】

1. 【判断归属】3 选 1:
   - ORIGINAL: 他自己的判断 (e.g. "I think", "in my view", "我认为", "我的判断", 直接陈述自己对未来股价/事件的看法, 没有引用其他机构)
   - RELAYED: 搬运/转述机构观点 (e.g. "GF Securities 报告", "TrendForce 数据", "Nomura 分析", "某券商指出", "根据研报", 引述别人观点但没加自己立场)
   - RELAYED+COMMENT: 搬运了别人观点, 但加了自己的明确判断 (e.g. 转述研报后说"我的看法是..." / "我认为研报漏了..." / 加了自己的 buy/sell/short 立场)

2. 【预测内容】抽取关于具体股票/标的的【方向性预测】(看多/看空/有目标价)。多个标的就返回多个。
   - ticker: 用 ticker 代码 (如 SNDK / MU / SK Hynix → 000660.KS, Samsung → 005930.KS, Micron → MU, NVIDIA → NVDA), 不能识别就 null
   - direction: "long" / "short" / "neutral"
   - horizon_days: 30=1m, 90=3m, 180=6m
   - thesis: 一句话

3. 只抽取明确预测, 不抽取纯新闻/纯情绪/纯产品评测

【输出 JSON】
{{
  "attribution": "ORIGINAL" | "RELAYED" | "RELAYED+COMMENT",
  "attribution_evidence": "为什么这么判定 (一句话, 引用原文片段)",
  "predictions": [
    {{
      "ticker": "...",
      "direction": "long/short/neutral",
      "horizon_days": 30,
      "thesis": "..."
    }}
  ]
}}
"""


def process_content(text, source, max_chars=3000):
    """对一条内容做 LLM 抽取 + 归属判定。"""
    truncated = text[:max_chars] if len(text) > max_chars else text
    prompt = EXTRACT_PROMPT.format(source=source, text=truncated)
    r = call_ds(prompt, max_tokens=1500)
    if not r:
        return {"attribution": "?", "attribution_evidence": "API failed", "predictions": []}
    r.setdefault("attribution", "?")
    r.setdefault("attribution_evidence", "")
    r.setdefault("predictions", [])
    return r


# 抽 X (限速 1.5s/条, 682 条要 ~17 分钟)
print(f"\n开始抽 X ({len(unique_x)} 条)...")
x_results = []
save_every = 25
for i, it in enumerate(unique_x):
    text = (it.get("text") or it.get("fullText") or "")
    if not text:
        continue
    r = process_content(text, "X")
    r["x_id"] = it.get("id")
    r["x_createdAt"] = it.get("createdAt")
    r["x_text"] = text[:300]
    x_results.append(r)
    if (i + 1) % save_every == 0:
        with open("/workspace/logs/p4p11_x_partial.json", "w") as f:
            json.dump(x_results, f)
        print(f"  [{i+1}/{len(unique_x)}] saved partial, attribution: {Counter(x['attribution'] for x in x_results).most_common()}", flush=True)
    if (i + 1) % 50 == 0:
        print(f"  [{i+1}/{len(unique_x)}] attribution: {Counter(x['attribution'] for x in x_results).most_common()}", flush=True)
    time.sleep(0.2)

# 抽 Substack
print(f"\n开始抽 Substack ({len(substack)} 篇)...")
ss_results = []
for i, p in enumerate(substack):
    text = p.get("full_body", "") or p.get("truncated_body", "")
    if not text:
        continue
    r = process_content(text, "Substack")
    r["ss_slug"] = p.get("slug")
    r["ss_post_date"] = p.get("post_date")
    r["ss_title"] = p.get("title")
    r["ss_audience"] = p.get("audience")
    r["ss_body_source"] = p.get("body_source")
    r["ss_text_snippet"] = text[:300]
    ss_results.append(r)
    print(f"  [{i+1}/{len(substack)}] {p.get('title','')[:50]} → attribution: {r['attribution']}")
    time.sleep(0.3)

# 统计
print("\n" + "=" * 80)
print("Step 4: ORIGINAL/RELAYED 分布")
print("=" * 80)

# X
x_attr = Counter(r["attribution"] for r in x_results)
x_pred = [r for r in x_results if r.get("predictions")]
print(f"\nX 推文 ({len(x_results)} 条) attribution:")
for k, n in x_attr.most_common():
    pct = n/len(x_results)*100 if x_results else 0
    print(f"  {k}: {n} ({pct:.1f}%)")
print(f"X 含预测数: {len(x_pred)} 条 (有 predictions array 非空)")

# Substack
ss_attr = Counter(r["attribution"] for r in ss_results)
print(f"\nSubstack 文章 ({len(ss_results)} 篇) attribution:")
for k, n in ss_attr.most_common():
    pct = n/len(ss_results)*100 if ss_results else 0
    print(f"  {k}: {n} ({pct:.1f}%)")

# 合并预测 (从所有 ORIGINAL + RELAYED+COMMENT)
all_content = x_results + ss_results
his_predictions = []  # ORIGINAL + RELAYED+COMMENT
relayed_only = []  # RELAYED
for r in all_content:
    if r["attribution"] in ("ORIGINAL", "RELAYED+COMMENT"):
        for p in r.get("predictions", []):
            p["source"] = "x" if "x_id" in r else "substack"
            p["source_id"] = r.get("x_id") or r.get("ss_slug")
            p["source_date"] = r.get("x_createdAt") or r.get("ss_post_date")
            p["attribution"] = r["attribution"]
            p["attribution_evidence"] = r.get("attribution_evidence", "")
            p["text_snippet"] = r.get("x_text") or r.get("ss_text_snippet", "")
            his_predictions.append(p)
    elif r["attribution"] == "RELAYED":
        for p in r.get("predictions", []):
            p["source"] = "x" if "x_id" in r else "substack"
            p["source_id"] = r.get("x_id") or r.get("ss_slug")
            p["source_date"] = r.get("x_createdAt") or r.get("ss_post_date")
            p["attribution"] = "RELAYED"
            p["text_snippet"] = r.get("x_text") or r.get("ss_text_snippet", "")
            relayed_only.append(p)

print(f"\n=== 关键结论 ===")
print(f"他的内容 ({len(all_content)} 条) 中:")
print(f"  ORIGINAL 或 RELAYED+COMMENT (他的真判断): {sum(1 for r in all_content if r['attribution'] in ('ORIGINAL','RELAYED+COMMENT'))}")
print(f"  纯 RELAYED (搬运工模式): {sum(1 for r in all_content if r['attribution'] == 'RELAYED')}")
print(f"\n他发出的预测总数: {len(his_predictions) + len(relayed_only)}")
print(f"  其中他自己判断: {len(his_predictions)}")
print(f"  其中纯搬运: {len(relayed_only)}")
print(f"\nORIGINAL/RELAYED+COMMENT 比例: {len(his_predictions) / (len(his_predictions) + len(relayed_only)) * 100:.1f}%")

# 按 ticker 看他自己判断的标的
his_tickers = Counter(p.get("ticker") for p in his_predictions if p.get("ticker"))
print(f"\n他自己判断的 ticker 分布 (top 20):")
for t, n in his_tickers.most_common(20):
    print(f"  {t}: {n}")

# 按 ticker 搬运标的
relayed_tickers = Counter(p.get("ticker") for p in relayed_only if p.get("ticker"))
print(f"\n他纯搬运的 ticker 分布 (top 20):")
for t, n in relayed_tickers.most_common(20):
    print(f"  {t}: {n}")

# 保存
with open("/workspace/logs/p4p11_attribution.json", "w") as f:
    json.dump({
        "x_results": x_results,
        "ss_results": ss_results,
        "his_predictions": his_predictions,
        "relayed_only": relayed_only,
        "summary": {
            "x_total": len(x_results),
            "ss_total": len(ss_results),
            "x_attr": dict(x_attr),
            "ss_attr": dict(ss_attr),
            "his_count": len(his_predictions),
            "relayed_count": len(relayed_only),
            "his_pct": len(his_predictions) / (len(his_predictions) + len(relayed_only)) * 100 if (his_predictions or relayed_only) else 0,
        },
    }, f, indent=2)
print(f"\n✅ saved /workspace/logs/p4p11_attribution.json")