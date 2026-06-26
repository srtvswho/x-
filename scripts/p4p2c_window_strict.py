"""P4-2c 修正:拉 maxItems=300 + Python 端严格 since/until 过滤 + 按 createdAt 排序找早期发现者"""
import os, json, time, re
from apify_client import ApifyClient

APIFY = os.environ["APIFY_TOKEN"]
client = ApifyClient(APIFY)
ACTOR_ID = "apidojo/tweet-scraper"

WINDOWS = {
    "SNDK": ("2025-04-07", "2025-09-08"),
    "MU": ("2025-04-07", "2025-09-11"),
}
QUERIES = {
    "SNDK": ["$SNDK", "Sandisk", "$WDC"],
    "MU": ["$MU", "Micron"],
}

PRICE_DIR = "/workspace/data/price_cache"
def load_bars(t):
    p = f"{PRICE_DIR}/{t}_FULL_HISTORY.json"
    if os.path.exists(p):
        return json.load(open(p))
    return []


def find_price_on_or_before(bars, target_date):
    px = None
    for b in bars:
        if b["date"] <= target_date:
            px = b["c"]
        else:
            break
    return px


def start_search(query, since, until, max_items=300):
    inp = {
        "searchTerms": [query],
        "maxItems": max_items,
        "since": since,
        "until": until,
        "sort": "Latest",
        "tweetLanguage": "en",
        "includeSearchTerms": False,
    }
    run = client.actor(ACTOR_ID).start(run_input=inp)
    print(f"  [start] {query} → run={run.id[:8]}")
    return run.id, run.default_dataset_id


def poll_dataset(dataset_id, max_wait=60):
    ds = client.dataset(dataset_id)
    t0 = time.time()
    last = 0
    while time.time() - t0 < max_wait:
        try:
            cnt = ds.get().item_count or 0
            if cnt != last:
                print(f"    items: {cnt}")
                last = cnt
            if cnt >= 80 and time.time() - t0 > 25:
                time.sleep(8)
                return list(ds.iterate_items())
            time.sleep(3)
        except Exception as e:
            print(f"    err: {e}")
            time.sleep(3)
    return list(ds.iterate_items())


# 跑
results = []
for ticker, (since, until) in WINDOWS.items():
    print(f"\n{'=' * 60}")
    print(f"{ticker}: window {since} ~ {until}")
    for q in QUERIES[ticker]:
        try:
            run_id, ds_id = start_search(q, since, until, max_items=300)
            items = poll_dataset(ds_id, max_wait=70)
            # STRICT filter: pub_date 在 [since, until]
            valid = []
            for it in items:
                cd = (it.get("createdAt") or it.get("date") or "")[:10]
                if since <= cd <= until:
                    valid.append(it)
            print(f"  → {len(items)} total, {len(valid)} in window")
            results.append({
                "ticker": ticker, "query": q, "run_id": run_id,
                "ds_id": ds_id, "items": valid
            })
        except Exception as e:
            print(f"  ✗ {e}")
            import traceback; traceback.print_exc()


# 解析 (按 createdAt ASC 排序找最早)
print(f"\n{'=' * 60}")
print(f"汇总")
print(f"{'=' * 60}")

all_tweets = []  # {ticker, query, author, pub_date, text, px, pct_above_low}
for r in results:
    ticker = r["ticker"]
    query = r["query"]
    bars = load_bars(ticker)
    low_px = min(b["l"] for b in bars if WINDOWS[ticker][0] <= b["date"] <= WINDOWS[ticker][1])

    for it in r["items"]:
        text = (it.get("text") or it.get("fullText") or "").strip()
        if not text or text.startswith("RT "):
            continue
        text_lower = text.lower()
        if ticker == "SNDK":
            if not any(k in text_lower for k in ["sndk", "sandisk", "闪迪", "$wdc", "western digital"]):
                continue
        elif ticker == "MU":
            if not any(k in text_lower for k in ["micron", "美光"]):
                continue

        author = None
        if isinstance(it.get("author"), dict):
            author = it["author"].get("userName") or it["author"].get("username")
        if not author:
            author = it.get("userName") or it.get("username") or it.get("author_userName")
        if not author:
            url = it.get("url", "")
            m = re.search(r"x\.com/([^/]+)/", url)
            if m: author = m.group(1)
        if not author:
            continue
        author = author.lower().lstrip("@")

        pub_date = (it.get("createdAt") or it.get("date") or "")[:10]
        if not pub_date or len(pub_date) < 10:
            continue

        px = find_price_on_or_before(bars, pub_date)
        if px is None:
            continue
        pct = (px - low_px) / low_px * 100

        all_tweets.append({
            "ticker": ticker, "query": query, "author": author,
            "pub_date": pub_date, "text": text, "px": px,
            "pct_above_low": pct, "like": it.get("likeCount", 0),
            "view": it.get("viewCount", 0),
        })

# 按 (author, ticker) 找最早一条
authors_earliest = {}
for t in all_tweets:
    key = (t["author"], t["ticker"])
    if key not in authors_earliest or t["pub_date"] < authors_earliest[key]["pub_date"]:
        authors_earliest[key] = t

# 排序输出
print(f"\n不同 (author, ticker): {len(authors_earliest)}")
from collections import Counter
by_ticker = Counter(v["ticker"] for v in authors_earliest.values())
print(f"按 ticker: {dict(by_ticker)}")

for ticker in ["SNDK", "MU"]:
    rows = [v for v in authors_earliest.values() if v["ticker"] == ticker]
    rows.sort(key=lambda x: x["pub_date"])
    print(f"\n--- {ticker}: {len(rows)} authors (按 first_pub 排序) ---")
    print(f"{'author':24s} {'first_pub':12s} {'px@first':10s} {'%above_low':10s} {'likes':6s} text snippet")
    for v in rows[:80]:
        snippet = v["text"].replace("\n", " ")[:90]
        print(f"  @{v['author']:22s} {v['pub_date']:12s} ${v['px']:8.2f} {v['pct_above_low']:+8.1f}% {v['like']:6d} {snippet}")

# 保存
with open("/workspace/logs/p4p2c_results.json", "w") as f:
    json.dump({
        "windows": WINDOWS,
        "queries": QUERIES,
        "authors_earliest": list(authors_earliest.values()),
        "all_tweets": all_tweets,
    }, f, indent=2)
print(f"\n✅ saved /workspace/logs/p4p2c_results.json")