"""austinsemis 全部历史判断 — 严格抽 (商业洞察 + 产业判断)"""
import json, os, re, time, urllib.request, sys
from collections import Counter
from email.utils import parsedate_to_datetime
from concurrent.futures import ThreadPoolExecutor, as_completed

DEEPSEEK_API_KEY = os.environ["DEEPSEEK_API_KEY"]

tweets = json.load(open("/workspace/logs/p5_newcandidates/raw_austinsemis.json"))
print(f"austinsemis 推文总数: {len(tweets)}")

PRICE = json.load(open("/workspace/logs/p5_industry_judgments/price_cache.json"))
INDEX = json.load(open("/workspace/logs/p5_industry_judgments/index_cache.json"))

CODE_NAME = {
    "7006136": "AAPL", "7002258": "NVDA", "7002720": "MU", "7000797": "TSLA",
    "7003901": "GOOGL", "7006270": "AMZN", "7005963": "AVGO", "7012998": "AMD",
    "7129132": "ARM", "7003510": "INTC", "7001672": "QCOM", "7002853": "MRVL",
    "7000164": "WDC", "7001305": "STX", "7072731": "VRT", "7003575": "COHR",
    "7007630": "LITE", "7003170": "KLAC", "7003152": "LRCX", "7006113": "AMAT",
    "7114479": "COIN", "7010637": "RIOT", "7011242": "MDB", "7120605": "POET",
    "7114491": "INVZ", "7006648": "MARA", "7000935": "SNPS", "7013376": "DELL",
    "7139464": "CRWV",
}
NAME_CODE = {v: k for k, v in CODE_NAME.items() if k in PRICE}

def parse_date(created_at):
    try:
        return parsedate_to_datetime(created_at).strftime("%Y-%m-%d")
    except:
        return None

items = []
for t in tweets:
    ca = t.get("createdAt", "")
    d = parse_date(ca)
    if not d: continue
    text = t.get("text") or ""
    if not text: continue
    items.append({"id": t.get("id"), "date": d, "created_at": ca, "text": text})
print(f"可用推文: {len(items)}")

# 严格 prompt — 教 LLM 识别 austin 的商业洞察判断
AUSTIN_PROMPT = """你是 @austinsemis X 推文"具体可证伪判断"抽取器.

【austin 风格 — 必须识别】

Austin 是 Substack/Podcast 半导体分析师 (@creativestrat). 他输出"商业逻辑判断", 跟普通 KOL 不一样:

1. **商业逻辑/护城河判断** (重点):
   - "Nvidia CUDA 是护城河" / "CUDA moat 可破" / "switching cost 高"
   - "Nvidia 是 self-fulfilling ecosystem" / "lock-in 效应"
   - "AMD 能克服 software 劣势"
   - "Google 卖芯片能力不够" / "merchant silicon 不是 Google 的菜"

2. **公司战略/商业模式判断**:
   - "Synopsys IP 转 ARM 模式" (ongoing license)
   - "Ansys 收购整合" / "Intel 18A 路线"
   - "Broadcom hyperscaler 主导"

3. **产业方向判断** (有 long/short 隐含):
   - "AI infra 资本支出流向"
   - "推理 (inference) 取代训练" / "Rubin 架构变更"
   - "ASIC 取代 GPU" / "Custom silicon 挑战"

4. **CEO/管理层评价** (不算 4 类 — 是 ② 看法/态度)

【4 类 — 这次保留 ③ + ④ (austin 最有认知含量)】

④ **明确方向押注** (有 long/short + 标的 + 隐含时间):
   - "Bullish $NVDA" / "看多 X" / "做空 Y"
   - "X 会涨/会崩到某程度"
   - "X 严重低估/高估" (隐含 long/short)
   - "我已建仓 X" / "买 X"

③-验证 **产业趋势 + 明确标的对应 + 隐含方向**:
   - "Rubin CPX 改变 inference 经济 → 利好 NVDA" (long)
   - "Google 出 merchant silicon → 短期不会成功" (short GOOGL)
   - "AMD CUDA 护城河可破 → 利好 AMD" (long)
   - 必须: 产业趋势 + 标的 + 隐含 long/short

③-模糊 产业趋势但标的模糊 (可保留但标"无明确标的"):
   - "Inference 取代训练" (没说股)
   - "AI capex 流向供应链" (没具体股)

② 看法/态度但非建仓 (剔除):
   - "CEO Ghazi 很强" / "CEO 拉胯" 
   - "Ansys 收购看起来不错"
   - "GAA 路线比 FinFET 好"

① 客观事实/技术评价 (剔除):
   - "TSMC 用 N3 工艺" / "GAA 节点"
   - "NVDA 营收 $X" (事实)

【特别注意 — 商业逻辑判断的处理】

- "CUDA 护城河可破 → 利好 AMD" → ③-验证 (有产业逻辑 + 标的 + 方向)
- "CUDA 护城河可破" → ③-模糊 (没标的方向, 只有产业判断)
- "CUDA 是护城河" → ① (客观描述)
- "AMD 软件团队很强" → ② (态度, 非建仓)

【输出严格 JSON — 如果是 ① 或 ②, 返回空】

{{"judgment": "一句话核心判断 (保留 austin 语气, 商业洞察)",
"date": "YYYY-MM-DD",
"category": "④ / ③-验证 / ③-模糊",
"direction": "long/short",
"tickers": ["TICKER1"],
"ticker_reasoning": "为什么对应到这些标的 (austin 原话, 1 句)",
"theme": "CUDA护城河/锁定效应/ASIC/Eda/管理层/Inference/其他",
"time_horizon": "30d/90d/180d/365d/unknown",
"judgment_type": "business_logic / industry / valuation"
}}

【输入】
日期: {date}
推文: {text}
"""


def extract_one(item):
    prompt = AUSTIN_PROMPT.format(date=item["date"], text=item["text"][:1500])
    data = json.dumps({
        "model": "deepseek-v4-pro",
        "messages": [{"role": "user", "content": prompt}],
        "response_format": {"type": "json_object"},
        "temperature": 0.0,
        "max_tokens": 600,
    }).encode()
    last_err = "?"
    for retry in range(4):
        try:
            req = urllib.request.Request(
                "https://api.deepseek.com/chat/completions",
                data=data,
                headers={"Authorization": f"Bearer {DEEPSEEK_API_KEY}", "Content-Type": "application/json"},
            )
            with urllib.request.urlopen(req, timeout=60) as r:
                resp = json.loads(r.read().decode())
            cs = resp["choices"][0]["message"]["content"]
            if not cs: raise ValueError("empty")
            r2 = json.loads(cs)
            if r2.get("category") in ("④", "③-验证", "③-模糊"):
                r2["source_id"] = item["id"]
                r2["original_text"] = item["text"]
                r2["date"] = item["date"]
                return r2
            return None
        except Exception as ex:
            last_err = str(ex)
            time.sleep(2 * (retry + 1))
    sys.stderr.write(f"  err {item['id']}: {last_err}\n")
    return None


t0 = time.time()
results = []
done = 0
with ThreadPoolExecutor(max_workers=20) as pool:
    futures = {pool.submit(extract_one, it): it for it in items}
    for fut in as_completed(futures):
        try:
            r2 = fut.result()
            if r2: results.append(r2)
        except Exception as e:
            sys.stderr.write(f"err: {e}\n")
        done += 1
        if done % 50 == 0:
            print(f"  [{time.time()-t0:.0f}s] {done}/{len(items)} judgments={len(results)}", flush=True)
print(f"  [{time.time()-t0:.0f}s] done {len(results)} judgments")

# 去重
seen = set()
deduped = []
for r in results:
    k = (r["date"], tuple(sorted(r.get("tickers", []))), r.get("direction", "?"), r.get("judgment", "")[:50])
    if k in seen: continue
    seen.add(k)
    deduped.append(r)
print(f"去重后: {len(deduped)}")

deduped.sort(key=lambda x: x["date"])
json.dump(deduped, open("/workspace/logs/p5_industry_judgments/austin_strict_judgments.json", "w"), indent=2, ensure_ascii=False)
print("💾 saved")

cats = Counter(r["category"] for r in deduped)
print(f"\n=== 4 类 ===")
for k in ["④", "③-验证", "③-模糊"]:
    print(f"  {k}: {cats.get(k, 0)}")
directions = Counter(r["direction"] for r in deduped)
print(f"方向: {dict(directions)}")
themes = Counter(r.get("theme", "?") for r in deduped)
print(f"主题 top 20: {dict(themes.most_common(20))}")
jt = Counter(r.get("judgment_type", "?") for r in deduped)
print(f"judgment_type: {dict(jt)}")