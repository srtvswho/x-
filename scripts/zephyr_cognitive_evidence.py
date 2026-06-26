"""zephyr_z9 全部历史判断 — 严格抽 (技术语言识别) + 保留 ③④ 产业+标的 押注"""
import json, os, re, time, urllib.request, sys
from collections import Counter
from email.utils import parsedate_to_datetime
from concurrent.futures import ThreadPoolExecutor, as_completed

DEEPSEEK_API_KEY = os.environ["DEEPSEEK_API_KEY"]

# zephyr 全 4000 推文
tweets = json.load(open("/workspace/logs/p5_zephyr/raw_all.json"))
print(f"zephyr_z9 推文总数: {len(tweets)}")

# 价格 cache + index
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
NAME_CODE = {v: k for k, v in CODE_NAME.items()}

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

# 严格 prompt — 专门教 LLM 识别 zephyr 的技术黑话式判断
ZEPHYR_PROMPT = """你是 zephyr_z9 X 推文"产业方向判断"抽取器. **关键**: zephyr 用技术黑话/行话表达判断, 你要识别出来.

【zephyr 表达风格 — 必须识别】
- 不用 $ticker, 写公司名 (Nvidia, Marvell, Micron, Coherent, Lumentum, Vertiv, WDC, Seagate, MongoDB, Hynix)
- 不用 buy/sell, 但有强烈方向感 (用产业语言)
- 技术术语隐藏判断:
  - "HBM 紧缺" / "HBM 价格挤压" / "HBM 需求超预期" = long SK Hynix / Samsung / MU
  - "CoWoS 产能" / "先进封装" = long TSMC
  - "光交换机消失" / "pluggable 退场" / "CPO 取代" = short LITE/COHR (或 CPO 相关)
  - "AI 电力缺口" / "data center 电力紧缺" = long VRT
  - "SSD 需求" / "storage 紧缺" = long MU/WDC/STX
  - "ASIC 完蛋" / "custom silicon 优势" = 标的导向
  - "推理算力" / "inference scaling" = long GPU/加速器供应商
  - "管理层 pump and dump" / "骗局" = short 标的
  - "高端制造" / "先进制程" / "纳米" = 标的导向

【4 类 — 这次 ③ 类也要保留, 因为是 zephyr 最有认知含量的判断】

④ **明确方向押注** (有 long/short + 标的 + 隐含时间):
   - "Nvidia 完蛋" / "X 公司会崩" = short X
   - "Marvell 是 pump and dump" = short MRVL
   - "MongoDB LMAO" = short MDB
   - "世界没这么高 AI 需求" = short NVDA
   - "I am long X" / "I am short X"
   - "X 必涨/必跌"

③-验证 **产业趋势 + 标的对应 + 隐含方向**:
   - "HBM 紧缺持续 → 利好 SK Hynix/Samsung/MU" (long)
   - "AI 电力缺口明年爆发 → 利好 VRT" (long)
   - "SSD 需求爆 → 利好 MU/WDC" (long)
   - "光交换机消失 → 拖累 LITE" (short)
   - "CPO 取代 pluggable → long CPO 供应链" (long)
   - 必须: 产业趋势 + 标的 (明说或可推导) + 隐含 long/short

③-模糊 产业趋势但标的模糊 (可保留但标"无明确标的"):
   - "AI 算力需求未来 5 年 100x" (没说股)

② 看法/态度但非建仓 (剔除, 不算判断):
   - "Jensen 跳" (段子)
   - "美国 AI 主导" (立场)
   - "AGI 5 年内" (大判断, 没标的)

① 客观事实/技术评价 (剔除):
   - "HBM 4 高 16 high stack" (技术描述)
   - "CoWoS-L 良率" (技术参数)

【特别注意 — 不能误判】
- "Jensen 跳" 不是 short NVDA (段子/玩笑)
- "$SNAP is for sure going to 100. 100 cents that is." 是讽刺不是 short
- 技术参数 (HBM 4 高 12 层) 不是判断
- "BTC 周期牛尾" 是 ③-模糊 产业趋势但没具体股

【输出严格 JSON — 如果是 ① 或 ②, 返回空】

{{"judgment": "一句话核心判断 (不改原意, 不夸不贬, 保留 zephyr 语气)",
"date": "YYYY-MM-DD",
"category": "④ / ③-验证 / ③-模糊",
"direction": "long/short",
"tickers": ["TICKER1"],
"ticker_reasoning": "为什么对应到这些标的 (zephyr 原话, 1 句, 不夸张不牵强)",
"theme": "光通信/存储/电力/AI芯片/HBM/ASIC/CPO/其他",
"time_horizon": "30d/90d/180d/365d/unknown",
"original_terms": ["HBM", "CoWoS", "CPO"] (技术关键词, 让用户理解背景)
}}

【输入】
日期: {date}
推文: {text}
"""


def extract_one(item):
    prompt = ZEPHYR_PROMPT.format(date=item["date"], text=item["text"][:1500])
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
with ThreadPoolExecutor(max_workers=25) as pool:
    futures = {pool.submit(extract_one, it): it for it in items}
    for fut in as_completed(futures):
        try:
            r2 = fut.result()
            if r2:
                results.append(r2)
        except Exception as e:
            sys.stderr.write(f"err: {e}\n")
        done += 1
        if done % 100 == 0:
            print(f"  [{time.time()-t0:.0f}s] {done}/{len(items)} judgments={len(results)}", flush=True)
print(f"  [{time.time()-t0:.0f}s] done {len(results)} judgments from {done} tweets")

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
json.dump(deduped, open("/workspace/logs/p5_industry_judgments/zephyr_strict_judgments.json", "w"), indent=2, ensure_ascii=False)
print("💾 saved")

cats = Counter(r["category"] for r in deduped)
print(f"\n=== 4 类 (保留 ③④) ===")
for k in ["④", "③-验证", "③-模糊"]:
    print(f"  {k}: {cats.get(k, 0)}")
directions = Counter(r["direction"] for r in deduped)
print(f"  方向: {dict(directions)}")
themes = Counter(r.get("theme", "?") for r in deduped)
print(f"  主题: {dict(themes)}")

# 特别检查 6 条标志性判断
print("\n=== 6 条标志性判断检查 ===")
markers = [
    "光交换机", "pluggable", "CPO", "光模块",
    "SSD", "storage-pilled", "存储",
    "AI 电力", "power demand", "VRT",
    "HBM 需求", "HBM 紧缺", "HBM price", "price squeeze",
    "Marvell", "pump and dump", "MRVL",
    "世界没有", "world does not have", "high AI demand",
]
for marker in markers:
    matched = [r for r in deduped if marker.lower() in r.get("original_text", "").lower() or marker.lower() in r.get("judgment", "").lower()]
    if matched:
        print(f"  ✓ '{marker}' — {len(matched)} 条匹配")
        for m in matched[:2]:
            print(f"    [{m['date']}] {m['direction']} {m.get('tickers', [])} — {m.get('judgment', '')[:100]}")
    else:
        print(f"  ✗ '{marker}' — 0 匹配")
