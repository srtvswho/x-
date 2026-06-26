"""P4-5b 并发跑 (thread pool) — 加快 10x"""
import os, json, time, urllib.request
from collections import Counter
from concurrent.futures import ThreadPoolExecutor, as_completed
import threading

DS_KEY = os.environ["DEEPSEEK_API_KEY"]
API_URL = "https://api.deepseek.com/chat/completions"
MODEL = "deepseek-v4-pro"

write_lock = threading.Lock()
written_count = 0


def call_deepseek(prompt):
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
    for attempt in range(3):
        try:
            with urllib.request.urlopen(req, timeout=60) as r:
                resp = json.loads(r.read())
            return json.loads(resp["choices"][0]["message"]["content"])
        except Exception as e:
            if attempt == 2:
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

results = []
results_lock = threading.Lock()
save_counter = [0]


def process(a):
    cls = classify_author(a)
    a["classification"] = cls
    with results_lock:
        results.append(a)
        save_counter[0] += 1
        if save_counter[0] % 20 == 0:
            with open("/workspace/logs/p4p5b_progress.json", "w") as f:
                json.dump({"n_done": save_counter[0], "results": results}, f, indent=2, default=str)
    return a["author"]


t0 = time.time()
with ThreadPoolExecutor(max_workers=8) as ex:
    futures = {ex.submit(process, a): a for a in authors}
    done = 0
    for f in as_completed(futures):
        a = futures[f]
        try:
            f.result()
        except Exception as e:
            print(f"err {a['author']}: {e}", flush=True)
        done += 1
        if done % 20 == 0:
            elapsed = time.time() - t0
            print(f"[{done}/{len(authors)}] {elapsed:.0f}s elapsed", flush=True)

# Final save
with open("/workspace/logs/p4p5b_llm_pro_screened.json", "w") as f:
    json.dump({
        "window": data["window"],
        "low_px": data["low_px"],
        "n_authors": len(results),
        "authors_screened": results,
    }, f, indent=2, default=str)
print(f"\nTotal time: {time.time()-t0:.0f}s", flush=True)

cats = Counter(a["classification"]["category"] for a in results)
print(f"\n分类分布:")
for c, n in cats.most_common():
    print(f"  {c}: {n}")

early_a = [a for a in results if a["pub_date"] <= "2025-05-31" and a["classification"]["category"] == "A"]
early_a.sort(key=lambda x: (x["pub_date"], -x["classification"].get("confidence", 0)))
print(f"\n=== 早期 (≤2025-05-31) + A 类 (有卡点分析): {len(early_a)} 个 ===")
for a in early_a:
    print(f"  @{a['author']:25s} {a['pub_date']:12s} +{a['pct_above_low']:5.1f}% conf={a['classification']['confidence']:.2f} | {a['classification']['key_logic']}")

early_other = [a for a in results if a["pub_date"] <= "2025-05-31" and a["classification"]["category"] in ("B", "C", "D")]
early_other.sort(key=lambda x: x["pub_date"])
print(f"\n=== 早期 + B/C/D 类: {len(early_other)} 个 ===")
for a in early_other[:15]:
    print(f"  @{a['author']:25s} {a['pub_date']:12s} +{a['pct_above_low']:5.1f}% cat={a['classification']['category']} | {a['classification'].get('reason', '')[:80]}")