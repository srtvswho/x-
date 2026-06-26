"""zephyr Q2 2026 1000 推文 strict 重抽"""
import json, os, re, time, urllib.request, sys
from collections import Counter
from email.utils import parsedate_to_datetime
from concurrent.futures import ThreadPoolExecutor, as_completed

DEEPSEEK_API_KEY = os.environ["DEEPSEEK_API_KEY"]

tweets = json.load(open("/workspace/logs/p5_industry_judgments/raw_zephyr_2026Q2.json"))
print(f"Q2 2026 zephyr 推文: {len(tweets)}", flush=True)

def parse_date(ca):
    try: return parsedate_to_datetime(ca).strftime("%Y-%m-%d")
    except: return None

items = []
for t in tweets:
    ca = t.get("createdAt", "")
    d = parse_date(ca)
    if not d: continue
    text = t.get("text") or ""
    if not text: continue
    items.append({"id": t.get("id"), "date": d, "created_at": ca, "text": text})
print(f"可用: {len(items)}", flush=True)

ZEPHYR_PROMPT = '''你是 zephyr_z9 X 推文"产业方向判断"抽取器. 关键: zephyr 用技术黑话/行话表达判断, 你要识别出来.

zephyr 表达风格: 不用 $ticker, 写公司名 (Nvidia, Marvell, Micron, Coherent, Lumentum, Vertiv, WDC, Seagate, MongoDB, Hynix). 不用 buy/sell, 但有强烈方向感.

技术术语隐藏判断:
- HBM 紧缺/HBM 价格挤压/HBM 需求超预期 = long SK Hynix/Samsung/MU
- CoWoS 产能/先进封装 = long TSMC
- 光交换机消失/pluggable 退场/CPO 取代 = 标的导向
- AI 电力缺口/data center 电力紧缺 = long VRT
- SSD 需求/storage 紧缺 = long MU/WDC/STX
- ASIC 完蛋/custom silicon 优势 = 标的导向
- 推理算力/inference scaling = long GPU
- 管理层 pump and dump/骗局 = short
- 关闭 AI 业务/亏损 = short

4 类:
④ 明确方向押注: Nvidia 完蛋/X 公司会崩/I am long X/I am short X/X 必涨必跌
③-验证 产业趋势+标的对应+隐含方向: HBM 紧缺持续利好 SK Hynix/Samsung/MU (long)
③-模糊 产业趋势但标的模糊
② 看法/态度但非建仓 (剔除)
① 客观事实/技术评价 (剔除)

特别注意不误判: Jensen 跳 不是 short NVDA (段子). $SNAP is for sure going to 100. 100 cents that is. 是讽刺不是 short. 技术参数 (HBM 4 高 12 层) 不是判断.

输出严格 JSON — ① 或 ② 返回空:
{"judgment": "一句话核心判断", "date": "YYYY-MM-DD", "category": "④ / ③-验证 / ③-模糊", "direction": "long/short", "tickers": ["TICKER1"], "ticker_reasoning": "为什么对应到这些标的", "theme": "光通信/存储/电力/AI芯片/HBM/ASIC/CPO/其他", "time_horizon": "30d/90d/180d/365d/unknown", "original_terms": ["HBM"]}

输入:
日期: {date}
推文: {text}
'''

def extract_one(item):
    prompt = ZEPHYR_PROMPT.format(date=item["date"], text=item["text"][:1500])
    data = json.dumps({
        "model": "deepseek-v4-pro",
        "messages": [{"role": "user", "content": prompt}],
        "response_format": {"type": "json_object"},
        "temperature": 0.0,
        "max_tokens": 600,
    }).encode()
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
            time.sleep(2 * (retry + 1))
    return None

t0 = time.time()
results = []
done = 0
with ThreadPoolExecutor(max_workers=25) as pool:
    futures = {pool.submit(extract_one, it): it for it in items}
    for fut in as_completed(futures):
        try:
            r2 = fut.result()
            if r2: results.append(r2)
        except: pass
        done += 1
        if done % 50 == 0:
            print(f"  [{time.time()-t0:.0f}s] {done}/{len(items)} judgments={len(results)}", flush=True)

print(f"  [{time.time()-t0:.0f}s] done {len(results)} judgments from {done} tweets", flush=True)

seen = set()
deduped = []
for r in results:
    k = (r["date"], tuple(sorted(r.get("tickers", []))), r.get("direction", "?"), r.get("judgment", "")[:50])
    if k in seen: continue
    seen.add(k)
    deduped.append(r)
print(f"去重: {len(deduped)}", flush=True)

deduped.sort(key=lambda x: x["date"])
json.dump(deduped, open("/workspace/logs/p5_industry_judgments/zephyr_q2_strict_judgments.json", "w"), indent=2, ensure_ascii=False)
print("saved", flush=True)

cats = Counter(r["category"] for r in deduped)
print(f"4 类: {dict(cats)}", flush=True)
themes = Counter(r.get("theme", "?") for r in deduped)
print(f"主题: {dict(themes)}", flush=True)
directions = Counter(r["direction"] for r in deduped)
print(f"方向: {dict(directions)}", flush=True)
