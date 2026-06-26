"""P4-4 LLM 初筛 — DeepSeek 批量判定 "有分析" vs "纯喊涨"

策略:
- 每个作者 first tweet 截到 600 chars
- DeepSeek prompt: 分类 + 关键论点抽取
- 输出: 每作者 (category, key_logic, confidence)
"""
import os, json, time
from datetime import datetime
from openai import OpenAI

DS_KEY = os.environ["DEEPSEEK_API_KEY"]
ds = OpenAI(api_key=DS_KEY, base_url="https://api.deepseek.com")

with open("/workspace/logs/p4p3b_candidates.json") as f:
    data = json.load(f)

authors = data["all_authors_sorted"]
print(f"Total authors: {len(authors)}")


def classify_author(author_data):
    """DeepSeek 判定单个作者的 first tweet。"""
    text = author_data["text"][:600]
    pub = author_data["pub_date"]
    pct = author_data["pct_above_low"]

    prompt = f"""你是股票信息研究员。给定一条 X 推文,判断它属于下面哪类。

【推文日期】{pub} (SNDK 此时从底部 $28 涨了 {pct:+.1f}%)
【推文作者】@{author_data['author']}
【推文内容】{text}

【分类定义】
A. 卡点分析: 给出结构化论点,涉及供需/产能/HBM/涨价/估值/技术瓶颈/竞争格局等具体逻辑
B. 价格/技术面: 只讨论支撑阻力/EMA/量价/形态等技术面,无基本面逻辑
C. 期权/资金流: 期权异动/大宗交易/未平仓合约变化等
D. 行业新闻: SanDisk 产品发布/技术规格/WD 分拆/财报数字等
E. 喊涨/跟风: 纯情绪 ("to the moon", "buy buy", "🚀🚀🚀") 无具体逻辑
F. 带货/推广/不相关: Amazon 优惠/消费电子评测/媒体内容等,不是股票分析

【输出格式 JSON】
{{
  "category": "A" 或 "B" 或 "C" 或 "D" 或 "E" 或 "F",
  "confidence": 0~1 (高=确定分类),
  "key_logic": "如果 category=A,一句话总结核心论点;否则 null",
  "reason": "一句话解释为什么这个分类"
}}
"""
    try:
        resp = ds.chat.completions.create(
            model="deepseek-v4-pro",
            messages=[{"role": "user", "content": prompt}],
            response_format={"type": "json_object"},
            temperature=0.1,
            max_tokens=300,
        )
        return json.loads(resp.choices[0].message.content)
    except Exception as e:
        return {"category": "?", "confidence": 0, "key_logic": None, "reason": f"err: {e}"}


# 批量跑
results = []
for i, a in enumerate(authors):
    print(f"[{i+1}/{len(authors)}] @{a['author']} ({a['pub_date']})... ", end="", flush=True)
    cls = classify_author(a)
    a["classification"] = cls
    results.append(a)
    print(f"{cls['category']} ({cls['confidence']:.2f})", flush=True)
    time.sleep(0.3)

# 保存
with open("/workspace/logs/p4p4_llm_screened.json", "w") as f:
    json.dump({
        "window": data["window"],
        "low_px": data["low_px"],
        "n_authors": len(results),
        "authors_screened": results,
    }, f, indent=2, default=str)
print(f"\n✅ saved /workspace/logs/p4p4_llm_screened.json")

# 汇总分类
from collections import Counter
cats = Counter(a["classification"]["category"] for a in results)
print(f"\n分类分布:")
for c, n in cats.most_common():
    print(f"  {c}: {n}")

# 早期 A 类 (有分析) — 重点!
early_a = [a for a in results if a["pub_date"] <= "2025-05-31" and a["classification"]["category"] == "A"]
early_a.sort(key=lambda x: x["pub_date"])
print(f"\n=== 早期 (≤5月) + A类 (有卡点分析): {len(early_a)} 个 ===")
for a in early_a:
    print(f"  @{a['author']:25s} {a['pub_date']:12s} +{a['pct_above_low']:5.1f}% conf={a['classification']['confidence']:.2f} | {a['classification']['key_logic']}")