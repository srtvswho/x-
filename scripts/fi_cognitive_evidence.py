"""fi56622380 全部历史判断 — 严格抽"具体可证伪"判断, 不下结论"""
import json, os, re, time, urllib.request, sys
from collections import Counter
from email.utils import parsedate_to_datetime
from concurrent.futures import ThreadPoolExecutor, as_completed

DEEPSEEK_API_KEY = os.environ["DEEPSEEK_API_KEY"]

# 读 1098 fi 推文
tweets = json.load(open("/workspace/logs/p5_industry_judgments/raw_fi56622380.json"))
print(f"fi56622380 推文总数: {len(tweets)}")

# 加载价格 cache
PRICE = json.load(open("/workspace/logs/p5_industry_judgments/price_cache.json"))
INDEX = json.load(open("/workspace/logs/p5_industry_judgments/index_cache.json"))

# 内码 (reversed lookup)
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

# 日期
def parse_date(created_at):
    try:
        return parsedate_to_datetime(created_at).strftime("%Y-%m-%d")
    except:
        return None

# 整理推文
items = []
for t in tweets:
    ca = t.get("createdAt", "")
    d = parse_date(ca)
    if not d: continue
    text = t.get("text") or ""
    if not text: continue
    items.append({"id": t.get("id"), "date": d, "created_at": ca, "text": text})

print(f"可用推文: {len(items)}")

# 严格 prompt — 找"具体可证伪"判断
STRICT_PROMPT = """你是 X 推文"具体可证伪判断"抽取器. **极严格**: 只接受真·有方向 + 真·有具体对象 + 真·可证伪的判断.

【4 类 — 你只能输出 A 或 B, 其他不算"具体可证伪判断"】

A. **④ 明确方向押注** (有 long/short + 标的 + 隐含时间):
   - "看多 X / 看空 X" + 标的
   - "X 会涨到 Y" / "X 会崩盘"
   - "X 严重低估 / X 严重高估"
   - "我买 X / 我建仓 X" / "我加仓 X"
   - "我会买 / 我不打算买" + 标的
   - "X 必涨/必跌"

B. **③-验证 产业趋势 + 明确标的 + 明确方向**:
   - "AI 电力缺口爆发 → 利好 VRT"
   - "HBM 紧缺持续 → MU 受益"
   - 必须有: 产业趋势 (有方向) + 受益/受损标的 + 隐含 long/short
   - 如果只说"产业趋势"但没说标的或没说方向 → **不算** (这是 ③-模糊)

【不算 (剔除)】

① 客观事实/技术评价:
   - "美光技术比海力士差" (技术比较, 不验)
   - "HBM 容量最稀缺" (事实)
   - "AMD 发布了新 GPU" (事实)
   - "CUDA 护城河" (技术评价)
   - "Apple 在 AI 时代是 Microsoft 在云时代" (类比, 不明确 long/short 哪个)

② 看法/态度但非建仓:
   - "不看好谷歌" (= 不 long, 不是做空)
   - "CEO 拉胯" (主观评价)
   - "我会绕着走" (个人行为)
   - "我不认为 X 值得买" (= 弱不 long)
   - "可以买但我不会" (倾向)
   - "以后碰到 X 都绕着走" (态度)

③-模糊 产业趋势无明确标的/方向:
   - "AI 电力缺口会爆发" (没说股)
   - "crypto 周期牛尾" (没具体股)
   - "明年存储紧缺" (没说股)
   - "端侧 AI 发展" (产业趋势, 标的模糊)

【特别警告】— 之前 2 次误抽的 3 类

1. **技术比较 ≠ short**: "美光技术比海力士差" 永远不算判断, 只是技术比较
2. **不看好 ≠ short**: "不看好谷歌" 永远不算 short, 是态度
3. **类比 ≠ 标的判断**: "Apple 在 AI 时代是 Microsoft 在云时代" 是 commentary, 没有 long/short 哪个

【输出严格 JSON — 如果这条不算, 返回空】

{{"judgment": "一句话核心判断 (不改原意, 不夸不贬)",
"date": "YYYY-MM-DD",
"category": "A 或 B",
"direction": "long/short",
"tickers": ["TICKER1", "TICKER2"],
"ticker_reasoning": "为什么对应到这些标的 (1 句, 不夸张不牵强)",
"time_horizon": "推断的时间窗口 (30d/90d/180d/365d/unknown)",
"confidence": "high/medium/low (从语气判断)"}}

【输入】
日期: {date}
推文: {text}
"""


def extract_one(item):
    prompt = STRICT_PROMPT.format(date=item["date"], text=item["text"][:1500])
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
            if not cs:
                raise ValueError("empty")
            r2 = json.loads(cs)
            if r2.get("category") in ("A", "B"):
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
            if r2:
                results.append(r2)
        except Exception as e:
            sys.stderr.write(f"err: {e}\n")
        done += 1
        if done % 50 == 0:
            print(f"  [{time.time()-t0:.0f}s] {done}/{len(items)} judgments={len(results)}", flush=True)
print(f"  [{time.time()-t0:.0f}s] done {len(results)} judgments from {done} tweets")


# 去重: 同一 (date + tickers + direction) 只留 1
seen = set()
deduped = []
for r in results:
    k = (r["date"], tuple(sorted(r.get("tickers", []))), r.get("direction", "?"))
    if k in seen: continue
    seen.add(k)
    deduped.append(r)
print(f"去重后: {len(deduped)}")

# 排序
deduped.sort(key=lambda x: x["date"])

# 保存
json.dump(deduped, open("/workspace/logs/p5_industry_judgments/fi_strict_judgments.json", "w"), indent=2, ensure_ascii=False)
print("💾 saved fi_strict_judgments.json")

# 统计
print("\n=== 4 类 (A=④ B=③-验证) 统计 ===")
cats = Counter(r["category"] for r in deduped)
print(f"  A (④ 明确方向押注): {cats.get('A', 0)}")
print(f"  B (③-验证 产业+标的): {cats.get('B', 0)}")
directions = Counter(r["direction"] for r in deduped)
print(f"  方向: {dict(directions)}")
tickers_all = []
for r in deduped:
    tickers_all.extend(r.get("tickers", []))
print(f"  标的 top 20: {Counter(tickers_all).most_common(20)}")
