"""P4-7 4 人后续表现 + 全部历史推文 + 整体命中率验证

Step 1: 4 人从首次发声日入场到今天的 SNDK 表现
Step 2: 抓 4 人全部历史推文 (timeline),用 LLM 抽取 ticker + direction + horizon
Step 3: 验证每条预测 (vs SPY),算整体 hit_rate / median_excess
Step 4: 排序 — 用他们在【非 SNDK】其他票上的命中率判断能力
"""
import os, json, time, urllib.request, sqlite3
from datetime import datetime
from collections import defaultdict
import statistics

DS_KEY = os.environ["DEEPSEEK_API_KEY"]
APIFY = os.environ["APIFY_TOKEN"]
PRICE_DIR = "/workspace/data/price_cache"
DB = "/workspace/data/signalboard_full.db"

# 4 个作者
AUTHORS = ["oopsguess", "jukan05", "wmhuo168", "lokoyacap"]
FIRST_PUB = {
    "oopsguess": "2025-04-15",
    "jukan05": "2025-05-12",
    "wmhuo168": "2025-07-17",
    "lokoyacap": "2025-09-05",
}
DIRECTION = {
    "oopsguess": "long",   # 看多
    "jukan05": "short",    # 看空
    "wmhuo168": "short",   # 看空
    "lokoyacap": "long",   # 隐含多
}

# ============ Step 1: 4 人 SNDK 后续表现 ============
print("=" * 80)
print("Step 1: 4 人 SNDK 后续表现 (从首次发声次日入场, 到 2026-06-12)")
print("=" * 80)

def load_bars(t):
    p = f"{PRICE_DIR}/{t}_FULL_HISTORY.json"
    if not os.path.exists(p) and t == "SIVE":
        p = f"{PRICE_DIR}/SIVEF_FULL_HISTORY.json"
    if os.path.exists(p):
        return json.load(open(p))
    return []

def find_price_on_or_after(bars, target_date):
    for b in bars:
        if b["date"] >= target_date:
            return b["c"], b["date"]
    return None, None

sndk = load_bars("SNDK")
spy = load_bars("SPY")

# 4 个 entry/exit
print(f"\n{'author':12s} {'first_pub':12s} {'dir':6s} {'entry_px':10s} {'exit_px':10s} {'raw_ret':10s} {'spy_ret':10s} {'excess':10s}")
for a in AUTHORS:
    pub = FIRST_PUB[a]
    # entry = pub + 1
    from datetime import datetime, timedelta
    entry_date = (datetime.strptime(pub, "%Y-%m-%d") + timedelta(days=1)).strftime("%Y-%m-%d")
    exit_date = "2026-06-12"  # 最后 bar

    e_px, _ = find_price_on_or_after(sndk, entry_date)
    x_px, xd = find_price_on_or_after(sndk, exit_date)

    # SPY 同期
    se_px, _ = find_price_on_or_after(spy, entry_date)
    sx_px, _ = find_price_on_or_after(spy, exit_date)

    if not e_px or not x_px or not se_px or not sx_px:
        print(f"  @{a:11s} {pub:12s} ??? data missing")
        continue

    raw_ret = (x_px - e_px) / e_px * 100
    spy_ret = (sx_px - se_px) / se_px * 100

    # long: excess = raw - spy
    # short: excess = spy - raw (做空,反着算)
    dir = DIRECTION[a]
    if dir == "long":
        excess = raw_ret - spy_ret
        correct = "✅" if excess > 0 else "❌"
    else:  # short
        excess = spy_ret - raw_ret
        correct = "✅" if excess > 0 else "❌"

    print(f"  @{a:11s} {pub:12s} {dir:6s} ${e_px:8.2f} ${x_px:8.2f} {raw_ret:+8.1f}% {spy_ret:+8.1f}% {excess:+8.1f}% {correct}")

# ============ Step 2: 抓 4 人 timeline ============
print("\n" + "=" * 80)
print("Step 2: 抓 4 人全部历史推文 (timeline)")
print("=" * 80)

from apify_client import ApifyClient
client = ApifyClient(APIFY)
ACTOR_ID = "apidojo/tweet-scraper"


def fetch_timeline(handle, max_tweets=2000):
    """抓单个用户全部推文。"""
    inp = {
        "searchTerms": [f"from:{handle}"],
        "maxItems": max_tweets,
        "sort": "Latest",
    }
    run = client.actor(ACTOR_ID).start(run_input=inp)
    print(f"  [start] from:{handle} → run={run.id[:8]}")
    ds = client.dataset(run.default_dataset_id)
    items = []
    t0 = time.time()
    while time.time() - t0 < 120:
        try:
            cnt = ds.get().item_count or 0
            if cnt >= 50 and time.time() - t0 > 20:
                time.sleep(8)
                items = list(ds.iterate_items())
                break
            time.sleep(3)
        except Exception as e:
            print(f"    err: {e}")
            time.sleep(3)
    else:
        items = list(ds.iterate_items())
    return items


all_tweets = {}
for a in AUTHORS:
    try:
        items = fetch_timeline(a, max_tweets=2000)
        # 排序按 createdAt ASC
        items.sort(key=lambda x: x.get("createdAt", ""))
        all_tweets[a] = items
        print(f"  → {a}: {len(items)} tweets")
    except Exception as e:
        print(f"  ✗ {a}: {e}")
        all_tweets[a] = []

# 保存 raw
with open("/workspace/logs/p4p7_timelines_raw.json", "w") as f:
    json.dump({a: [{"id": it.get("id"), "createdAt": it.get("createdAt"),
                    "text": it.get("text") or it.get("fullText", ""),
                    "like": it.get("likeCount", 0), "rt": it.get("retweetCount", 0)}
                   for it in all_tweets[a]] for a in AUTHORS}, f, indent=2)
print(f"\n✅ saved timelines")

# ============ Step 3: LLM 抽取每条推文的 ticker + direction + horizon ============
print("\n" + "=" * 80)
print("Step 3: LLM 抽取每条推文里的预测 (ticker + direction + horizon)")
print("=" * 80)


def call_deepseek(prompt, max_tokens=600):
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
                resp = json.loads(r.read())
            return json.loads(resp["choices"][0]["message"]["content"])
        except Exception as e:
            if attempt == 1:
                return {"predictions": []}
            time.sleep(1)


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


def extract_predictions(text):
    return call_deepseek(EXTRACT_PROMPT.format(text=text[:1000]))


# 抽 4 人的所有推文
all_predictions = []  # (author, tweet_id, tweet_date, text, prediction_dict)
for a in AUTHORS:
    items = all_tweets.get(a, [])
    print(f"\n  抽取 @{a} ({len(items)} tweets)...")
    for i, it in enumerate(items):
        text = it.get("text") or it.get("fullText", "")
        if not text or text.startswith("RT "):
            continue
        if i % 10 == 0:
            print(f"    [{i+1}/{len(items)}]", flush=True)
        preds = extract_predictions(text)
        for p in preds.get("predictions", []):
            ticker = p.get("ticker")
            if not ticker:
                continue
            p["ticker"] = ticker.upper().replace("$", "")
            p["author"] = a
            p["tweet_id"] = it.get("id")
            p["tweet_date"] = (it.get("createdAt") or "")[:10]
            p["text_snippet"] = text[:200]
            all_predictions.append(p)
        time.sleep(0.2)  # 限速

print(f"\n总共抽取: {len(all_predictions)} 条预测")

# 保存
with open("/workspace/logs/p4p7_predictions.json", "w") as f:
    json.dump(all_predictions, f, indent=2)
print(f"✅ saved predictions")

# ============ Step 4: 验证每条预测 ============
print("\n" + "=" * 80)
print("Step 4: 验证每条预测 (vs SPY 同期)")
print("=" * 80)


def find_price(bars, target):
    """找 >= target 的第一个 close。"""
    for b in bars:
        if b["date"] >= target:
            return b["c"], b["date"]
    return None, None


def verify_prediction(p, max_horizon=180):
    """验证单条预测,返回 (resolved, hit, raw_ret, excess_ret, exit_date)。"""
    ticker = p["ticker"]
    pub_date = p["tweet_date"]
    direction = p["direction"]
    horizon = min(p.get("horizon_days", 30), max_horizon)

    # entry = pub + 1
    from datetime import datetime, timedelta
    entry_date = (datetime.strptime(pub_date, "%Y-%m-%d") + timedelta(days=1)).strftime("%Y-%m-%d")
    exit_date = (datetime.strptime(entry_date, "%Y-%m-%d") + timedelta(days=horizon)).strftime("%Y-%m-%d")
    # 不能晚于今天
    today = "2026-06-12"
    exit_date = min(exit_date, today)

    # 拉 bars
    bars = load_bars(ticker)
    if not bars:
        return {"resolved": False, "reason": f"no_bars_{ticker}"}

    e_px, _ = find_price(bars, entry_date)
    x_px, xd = find_price(bars, exit_date)
    if not e_px or not x_px:
        return {"resolved": False, "reason": "no_px"}

    if direction == "long":
        raw_ret = (x_px - e_px) / e_px
    elif direction == "short":
        raw_ret = (e_px - x_px) / e_px
    else:
        return {"resolved": False, "reason": "neutral"}

    # SPY 同期
    se_px, _ = find_price(spy, entry_date)
    sx_px, _ = find_price(spy, exit_date)
    if not se_px or not sx_px:
        return {"resolved": False, "reason": "no_spy"}
    spy_ret = (sx_px - se_px) / se_px
    excess = raw_ret - spy_ret

    # hit?
    if direction == "long":
        hit = excess > 0
    else:
        hit = excess < 0  # short,excess 负数(price 跌赢 spy)算 hit

    return {
        "resolved": True,
        "hit": hit,
        "raw_ret": raw_ret * 100,
        "excess_ret": excess * 100,
        "entry_px": e_px,
        "exit_px": x_px,
        "entry_date": entry_date,
        "exit_date": exit_date,
        "horizon_days": horizon,
    }


verified = []
for p in all_predictions:
    v = verify_prediction(p)
    p["verification"] = v
    if v.get("resolved"):
        verified.append(p)

print(f"已验证 (resolved): {len(verified)} / {len(all_predictions)}")

# 统计每个作者
print(f"\n{'author':12s} {'#pred':6s} {'#resolved':10s} {'#hit':6s} {'hit_rate':10s} {'med_exc':10s} {'med_raw':10s}")
by_author = defaultdict(list)
for p in verified:
    by_author[p["author"]].append(p)

for a in AUTHORS:
    ps = by_author.get(a, [])
    n = len(ps)
    n_hit = sum(1 for p in ps if p["verification"]["hit"])
    hr = n_hit/n*100 if n else 0
    med_exc = statistics.median([p["verification"]["excess_ret"] for p in ps]) if ps else 0
    med_raw = statistics.median([p["verification"]["raw_ret"] for p in ps]) if ps else 0
    print(f"  @{a:11s} {len(all_predictions) if a in [p['author'] for p in all_predictions] else 0:6d} {n:10d} {n_hit:6d} {hr:8.1f}% {med_exc:+8.1f}% {med_raw:+8.1f}%")

# 关键: 排除 SNDK 后 (survivorship bias fix)
print(f"\n\n=== 关键: 排除 SNDK 后的命中率 (其他票才是真能力证据) ===")
print(f"{'author':12s} {'#pred':6s} {'#resolved':10s} {'#hit':6s} {'hit_rate':10s} {'med_exc':10s} {'unique_tickers':30s}")
for a in AUTHORS:
    ps_no_sndk = [p for p in verified if p["author"] == a and p["ticker"] != "SNDK"]
    n = len(ps_no_sndk)
    n_hit = sum(1 for p in ps_no_sndk if p["verification"]["hit"])
    hr = n_hit/n*100 if n else 0
    med_exc = statistics.median([p["verification"]["excess_ret"] for p in ps_no_sndk]) if ps_no_sndk else 0
    unique_t = sorted(set(p["ticker"] for p in ps_no_sndk))
    print(f"  @{a:11s} {len([p for p in all_predictions if p['author']==a and p['ticker']!='SNDK']):6d} {n:10d} {n_hit:6d} {hr:8.1f}% {med_exc:+8.1f}% {','.join(unique_t[:8])}")

# 保存
with open("/workspace/logs/p4p7_verified.json", "w") as f:
    json.dump({
        "verified": verified,
        "all_predictions": all_predictions,
        "by_author": {a: [p for p in verified if p["author"] == a] for a in AUTHORS},
    }, f, indent=2)
print(f"\n✅ saved verified")