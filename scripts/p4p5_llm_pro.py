"""P4-5 LLM 初筛 (v4-pro) — 修复 model + 优化运行

- model = "deepseek-v4-pro"
- 批量跑 438 个作者
- 输出早期 4-5 月 + A 类的完整原文(用户要自己读)
"""
import os, json, time, urllib.request, sys
from collections import Counter

DS_KEY = os.environ["DEEPSEEK_API_KEY"]
API_URL = "https://api.deepseek.com/chat/completions"
MODEL = "deepseek-v4-pro"


def call_deepseek(prompt, max_retries=2):
    for attempt in range(max_retries + 1):
        data = json.dumps({
            "model": MODEL,
            "messages": [{"role": "user", "content": prompt}],
            "response_format": {"type": "json_object"},
            "temperature": 0.1,
            "max_tokens": 300,
        }).encode()
        req = urllib.request.Request(
            API_URL,
            data=data,
            headers={
                "Authorization": f"Bearer {DS_KEY}",
                "Content-Type": "application/json",
            },
        )
        try:
            with urllib.request.urlopen(req, timeout=60) as r:
                resp = json.loads(r.read())
            return json.loads(resp["choices"][0]["message"]["content"])
        except Exception as e:
            if attempt == max_retries:
                return {"category": "?", "confidence": 0, "key_logic": None, "reason": f"err: {e}"}
            time.sleep(1)


def classify_author(a):
    text = a["text"][:600]
    pub = a["pub_date"]
    pct = a["pct_above_low"]
    prompt = f"""你是股票信息研究员。给定一条 X 推文,判断它属于下面哪类。

【推文日期】{pub} (SNDK 此时从底部 $28 涨了 {pct:+.1f}%)
【推文作者】@{a['author']}
【推文内容】{text}

【分类定义】
A. 卡点分析: 给出结构化论点,涉及供需/产能/HBM/涨价/估值/技术瓶颈/竞争格局等具体逻辑
B. 价格/技术面: 只讨论支撑阻力/EMA/量价/形态等技术面,无基本面逻辑
C. 期权/资金流: 期权异动/大宗交易/未平仓合约变化等
D. 行业新闻: SanDisk 产品发布/技术规格/WD 分拆/财报数字等
E. 喊涨/跟风: 纯情绪 ("to the moon", "buy buy") 无具体逻辑
F. 带货/推广/不相关: Amazon 优惠/消费电子评测/媒体内容等,不是股票分析

【输出 JSON】 {{"category":"A/B/C/D/E/F","confidence":0~1,"key_logic":"A 类一句话核心论点;否则 null","reason":"一句话分类理由"}}
"""
    return call_deepseek(prompt)


with open("/workspace/logs/p4p3b_candidates.json") as f:
    data = json.load(f)

authors = data["all_authors_sorted"]
print(f"Total: {len(authors)}", flush=True)
sys.stdout.flush()

results = []
for i, a in enumerate(authors):
    if i % 10 == 0:
        print(f"[{i+1}/{len(authors)}]", flush=True)
    cls = classify_author(a)
    a["classification"] = cls
    results.append(a)

# 中途 save
with open("/workspace/logs/p4p5_llm_pro_screened.json", "w") as f:
    json.dump({
        "window": data["window"],
        "low_px": data["low_px"],
        "n_authors": len(results),
        "authors_screened": results,
    }, f, indent=2, default=str)

cats = Counter(a["classification"]["category"] for a in results)
print(f"\n分类分布:")
for c, n in cats.most_common():
    print(f"  {c}: {n}")

# 早期 (≤5月) + A 类 — 重点!
early_a = [a for a in results if a["pub_date"] <= "2025-05-31" and a["classification"]["category"] == "A"]
early_a.sort(key=lambda x: (x["pub_date"], -x["classification"].get("confidence", 0)))
print(f"\n=== 早期 (≤2025-05-31) + A 类 (有卡点分析): {len(early_a)} 个 ===")
for a in early_a:
    print(f"  @{a['author']:25s} {a['pub_date']:12s} +{a['pct_above_low']:5.1f}% conf={a['classification']['confidence']:.2f} | {a['classification']['key_logic']}")

# 早期 B/C/D 类 — 候选
early_other = [a for a in results if a["pub_date"] <= "2025-05-31" and a["classification"]["category"] in ("B", "C", "D")]
early_other.sort(key=lambda x: x["pub_date"])
print(f"\n=== 早期 + B/C/D 类: {len(early_other)} 个 (技术面/期权/行业新闻) ===")
for a in early_other[:15]:
    print(f"  @{a['author']:25s} {a['pub_date']:12s} +{a['pct_above_low']:5.1f}% cat={a['classification']['category']} | {a['classification'].get('reason', '')[:80]}")