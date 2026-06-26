"""P4-9 检验 E 类 33 人是否被误杀

Step 1: 算每个 E 类发声次日 → 2026-06-12 SNDK 收益 + 排序
Step 2: 抓 E 类 timeline, 看是否有"非 SNDK" 的预测, 算整体命中率
Step 3: 对比 E 类 vs A 类后续表现分布
Step 4: 诊断"早期 + 高收益" E 类 — 是真有洞察还是纯运气
"""
import os, json, time, urllib.request
from datetime import datetime, timedelta
from collections import defaultdict, Counter
import statistics

DS_KEY = os.environ["DEEPSEEK_API_KEY"]
APIFY = os.environ["APIFY_TOKEN"]
PRICE_DIR = "/workspace/data/price_cache"
TODAY = "2026-06-12"


def load_bars(t):
    p = f"{PRICE_DIR}/{t}_FULL_HISTORY.json"
    if not os.path.exists(p) and t == "SIVE":
        p = f"{PRICE_DIR}/SIVEF_FULL_HISTORY.json"
    if os.path.exists(p):
        return json.load(open(p))
    return []


def find_price(bars, target):
    for b in bars:
        if b["date"] >= target:
            return b["c"], b["date"]
    return None, None


def parse_twitter_date(s):
    if not s:
        return None
    try:
        return datetime.strptime(s, "%a %b %d %H:%M:%S %z %Y").date()
    except (ValueError, TypeError):
        pass
    try:
        return datetime.fromisoformat(s.replace("Z", "+00:00")).date()
    except Exception:
        return None


# 加载 E 类
with open("/workspace/logs/p4p5b_llm_pro_screened.json") as f:
    d = json.load(f)
e_class = [a for a in d["authors_screened"] if a.get("classification", {}).get("category") == "E"]
a_class = [a for a in d["authors_screened"] if a.get("classification", {}).get("category") == "A"]

# 加载 A+ / A (从 p4p6)
with open("/workspace/logs/p4p6_strict_filter.json") as f:
    p4p6 = json.load(f)
a_plus_a = [x for x in p4p6["graded"] if x.get("new_grade") in ("A+", "A")]

print(f"E 类: {len(e_class)}, A 类: {len(a_class)}, A+/A: {len(a_plus_a)}")

sndk = load_bars("SNDK")
spy = load_bars("SPY")
soxx = load_bars("SOXX")


def calc_returns(pub_date):
    """算 entry=pub+1 → exit=今天 的 SNDK/SPY/SOXX 收益。"""
    ed = (datetime.strptime(pub_date, "%Y-%m-%d") + timedelta(days=1)).strftime("%Y-%m-%d")
    ep, _ = find_price(sndk, ed)
    xp, _ = find_price(sndk, TODAY)
    se, _ = find_price(spy, ed)
    sx, _ = find_price(spy, TODAY)
    soxxe, _ = find_price(soxx, ed)
    soxxx, _ = find_price(soxx, TODAY)
    if not ep or not xp:
        return None
    sndk_ret = (xp - ep) / ep * 100
    spy_ret = (sx - se) / se * 100 if se and sx else 0
    soxx_ret = (soxxx - soxxe) / soxxe * 100 if soxxe and soxxx else 0
    # 各 horizon (从 entry_date 算)
    def h_exit(days):
        hx_d = (datetime.strptime(ed, "%Y-%m-%d") + timedelta(days=days)).strftime("%Y-%m-%d")
        if hx_d > TODAY:
            hx_d = TODAY
        hxp, _ = find_price(sndk, hx_d)
        hsp, _ = find_price(spy, hx_d)
        hsox, _ = find_price(soxx, hx_d)
        if not hxp or not ep:
            return None
        return {
            "sndk": (hxp - ep) / ep * 100,
            "spy": (hsp - hsp * 0 + (hsp - se) / se * 100) if se and hsp else 0,
            "excess_spy": (hxp - ep) / ep * 100 - ((hsp - se) / se * 100 if se and hsp else 0),
            "excess_soxx": (hxp - ep) / ep * 100 - ((hsox - soxxe) / soxxe * 100 if soxxe and hsox else 0),
            "exit_date": hx_d,
        }
    return {
        "entry": ep,
        "exit": xp,
        "sndk_total": sndk_ret,
        "spy_total": spy_ret,
        "soxx_total": soxx_ret,
        "excess_spy_total": sndk_ret - spy_ret,
        "excess_soxx_total": sndk_ret - soxx_ret,
        "h_1m": h_exit(30),
        "h_3m": h_exit(90),
        "h_6m": h_exit(180),
        "h_1y": h_exit(365),
    }


# === Step 1: E 类排序 ===
print("\n" + "=" * 100)
print("Step 1: E 类 33 人 — SNDK 后续表现排序 (按 excess vs SPY 总)")
print("=" * 100)

e_with_returns = []
for a in e_class:
    pub = a["pub_date"]
    r = calc_returns(pub)
    if not r:
        continue
    e_with_returns.append({
        "author": a["author"],
        "pub_date": pub,
        "pct_above_low": a["pct_above_low"],
        "text": a["text"],
        "reason": a["classification"]["reason"],
        "returns": r,
    })

# 按 excess_spy_total 排序(应该都 + 几千 %,因为 SNDK 涨 60x)
e_with_returns.sort(key=lambda x: x["returns"]["entry"], reverse=True)  # 早入价高 → 排前

print(f"\n{'rank':4s} {'author':18s} {'pub_date':10s} {'pct_low':8s} {'entry':8s} {'h_1m':12s} {'h_3m':12s} {'h_6m':12s} {'total':10s} {'excess_spy':12s}")
print("-" * 130)
for i, e in enumerate(e_with_returns, 1):
    r = e["returns"]
    h1 = f"{r['h_1m']['sndk']:+.0f}%/{r['h_1m']['excess_spy']:+.0f}%" if r.get("h_1m") else "n/a"
    h3 = f"{r['h_3m']['sndk']:+.0f}%/{r['h_3m']['excess_spy']:+.0f}%" if r.get("h_3m") else "n/a"
    h6 = f"{r['h_6m']['sndk']:+.0f}%/{r['h_6m']['excess_spy']:+.0f}%" if r.get("h_6m") else "n/a"
    print(f"{i:4d} @{e['author']:17s} {e['pub_date']:10s} {e['pct_above_low']:6.1f}% ${r['entry']:6.2f} {h1:12s} {h3:12s} {h6:12s} {r['sndk_total']:+8.0f}% {r['excess_spy_total']:+10.0f}%")

# === Step 1b: 重点 — 入价最低的几个 (即"早期") ===
print("\n" + "=" * 100)
print("Step 1b: E 类按 entry 价排序 (最便宜的几个 = 真正的早期发现者)")
print("=" * 100)
e_with_returns.sort(key=lambda x: x["returns"]["entry"])
print(f"\n{'rank':4s} {'author':18s} {'pub_date':10s} {'pct_low':8s} {'entry':8s} {'total_sndk':12s} {'excess_spy':12s} {'文本前 80 字'}")
print("-" * 130)
for i, e in enumerate(e_with_returns[:10], 1):
    r = e["returns"]
    print(f"{i:4d} @{e['author']:17s} {e['pub_date']:10s} {e['pct_above_low']:6.1f}% ${r['entry']:6.2f} {r['sndk_total']:+10.0f}% {r['excess_spy_total']:+10.0f}% {e['text'][:80]}")

# 保存
with open("/workspace/logs/p4p9_e_class_returns.json", "w") as f:
    json.dump(e_with_returns, f, indent=2)
print(f"\n✅ saved /workspace/logs/p4p9_e_class_returns.json")

# === Step 2: 抓 E 类 timeline + LLM 抽取 ===
print("\n" + "=" * 100)
print("Step 2: 抓 E 类 33 人 timeline + LLM 抽取预测 (按 [非 SNDK 命中率] 评估能力)")
print("=" * 100)


def fetch_timeline(handle, max_tweets=500):
    from apify_client import ApifyClient
    client = ApifyClient(APIFY)
    inp = {"searchTerms": [f"from:{handle}"], "maxItems": max_tweets, "sort": "Latest"}
    run = client.actor("apidojo/tweet-scraper").start(run_input=inp)
    ds = client.dataset(run.default_dataset_id)
    items = []
    t0 = time.time()
    while time.time() - t0 < 60:
        cnt = ds.get().item_count or 0
        if cnt >= 50 and time.time() - t0 > 12:
            time.sleep(5)
            items = list(ds.iterate_items())
            break
        time.sleep(2)
    else:
        items = list(ds.iterate_items())
    items.sort(key=lambda x: x.get("createdAt", ""))
    return items


EXTRACT_PROMPT = """你是一个股票推文预测抽取器。给定一条 X 推文,识别其中关于具体股票/标的的【预测性陈述】。

【推文】{text}

【判定规则】
- 只抽取【明确的方向性预测】(看多/看空/有目标价),不抽取纯新闻/纯情绪/纯产品评测
- 多个标的就返回多个 prediction
- direction: "long" / "short" / "neutral"
- horizon_days: 数字(看多/看空的天数窗口,默认 30 = 1m,90 = 3m,180 = 6m)
- thesis: 一句话总结预测理由
- 纯转发、纯提问、纯评论: predictions=[]

【输出 JSON】
{{
  "predictions": [
    {{
      "ticker": "SNDK" 或 "MU" 或公司名映射的代码 或 null(无法判断),
      "direction": "long" / "short" / "neutral",
      "horizon_days": 30,
      "thesis": "理由一句话"
    }}
  ]
}}
"""


def call_ds(prompt, max_tokens=600):
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
    for attempt in range(2):
        try:
            with urllib.request.urlopen(req, timeout=60) as r:
                return json.loads(json.loads(r.read())["choices"][0]["message"]["content"])
        except Exception as e:
            if attempt == 1:
                return {"predictions": []}
            time.sleep(1)


# 先只抓早期 5 人 timeline (top 5 by 早期度) — 看是否有非 SNDK 的真判断
TOP_E = e_with_returns[:5]  # 最早的 5 人

print(f"\n先抓 top 5 早期 E 类 timeline: {[e['author'] for e in TOP_E]}")

timelines = {}
for e in TOP_E:
    try:
        items = fetch_timeline(e["author"], max_tweets=500)
        timelines[e["author"]] = items
        print(f"  → @{e['author']}: {len(items)} tweets")
    except Exception as ex:
        print(f"  ✗ @{e['author']}: {ex}")
        timelines[e["author"]] = []

# 保存
with open("/workspace/logs/p4p9_e_class_timelines.json", "w") as f:
    json.dump({a: [{"id": it.get("id"), "createdAt": it.get("createdAt"),
                    "text": it.get("text") or it.get("fullText", "")}
                   for it in items] for a, items in timelines.items()}, f, indent=2)

# LLM 抽取预测
print(f"\nLLM 抽取 top 5 E 类的预测...")
all_preds = []
for a, items in timelines.items():
    for it in items:
        text = it.get("text") or ""
        if not text or text.startswith("RT "):
            continue
        r = call_ds(EXTRACT_PROMPT.format(text=text[:1000]))
        for p in r.get("predictions", []):
            ticker = p.get("ticker")
            if not ticker:
                continue
            p["ticker"] = ticker.upper().replace("$", "")
            p["author"] = a
            p["tweet_id"] = it.get("id")
            p["createdAt"] = it.get("createdAt", "")
            p["text_snippet"] = text[:200]
            all_preds.append(p)
        time.sleep(0.15)

print(f"\ntop 5 E 类共抽出预测: {len(all_preds)}")

# 按 author 统计
ca = Counter(p["author"] for p in all_preds)
for a in [e["author"] for e in TOP_E]:
    n = ca.get(a, 0)
    n_sndk = sum(1 for p in all_preds if p["author"] == a and p["ticker"] == "SNDK")
    n_other = n - n_sndk
    print(f"  @{a:18s} total={n}, SNDK={n_sndk}, 其他={n_other}")

# 保存
with open("/workspace/logs/p4p9_e_class_predictions.json", "w") as f:
    json.dump(all_preds, f, indent=2)
print(f"\n✅ saved predictions")