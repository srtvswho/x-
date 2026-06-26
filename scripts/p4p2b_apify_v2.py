"""P4-2b 简化 Apify 反查 — 手动启动 + 轮询 dataset

策略:
- 启动 actor 后立即返回 run_id,不阻塞等
- 轮询 dataset.items() 拿数据
- timeout 短 (maxTweets=50)
"""
import os, json, time, re
from datetime import datetime, date, timedelta
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


def start_search(query, since, until, max_tweets=80):
    """启动 actor,返回 (run_id, dataset_id) 不阻塞。"""
    inp = {
        "searchTerms": [query],
        "maxItems": max_tweets,
        "since": since,
        "until": until,
        "sort": "Latest",
        "tweetLanguage": "en",
        "includeSearchTerms": False,
    }
    run = client.actor(ACTOR_ID).start(run_input=inp)
    print(f"  [start] {query} → run={run.id}")
    return run.id, run.default_dataset_id


def poll_dataset(dataset_id, max_wait_sec=120):
    """轮询 dataset 等有数据。"""
    print(f"  [poll] dataset={dataset_id[:8]}")
    ds = client.dataset(dataset_id)
    start_t = time.time()
    last_count = 0
    while time.time() - start_t < max_wait_sec:
        try:
            cnt = ds.get().item_count or 0
            if cnt != last_count:
                print(f"    items so far: {cnt} (waited {time.time()-start_t:.0f}s)")
                last_count = cnt
            if cnt > 0 and time.time() - start_t > 15:
                # 拿到第一批数据后,再等 10s 收集后续
                time.sleep(10)
                return list(ds.iterate_items())
            time.sleep(3)
        except Exception as e:
            print(f"    poll err: {e}")
            time.sleep(5)
    # 超时返回已有
    return list(ds.iterate_items())


# 主流程
results = []  # {ticker, query, run_id, items_count}
for ticker, (since, until) in WINDOWS.items():
    print(f"\n{'=' * 60}")
    print(f"{ticker}: window {since} ~ {until}")
    print(f"{'=' * 60}")

    bars = load_bars(ticker)
    low_px = min(b["l"] for b in bars if since <= b["date"] <= until)
    print(f"low_px=${low_px:.2f}")

    for q in QUERIES[ticker]:
        try:
            run_id, ds_id = start_search(q, since, until, max_tweets=80)
            items = poll_dataset(ds_id, max_wait_sec=90)
            results.append({
                "ticker": ticker, "query": q, "run_id": run_id,
                "ds_id": ds_id, "items_count": len(items), "items": items
            })
            print(f"  ✓ got {len(items)} items for '{q}'")
        except Exception as e:
            print(f"  ✗ error: {e}")
            import traceback; traceback.print_exc()

# 解析结果
print(f"\n{'=' * 60}")
print(f"汇总")
print(f"{'=' * 60}")

all_authors = {}  # (handle, ticker) -> info
for r in results:
    ticker = r["ticker"]
    query = r["query"]
    bars = load_bars(ticker)
    low_px = min(b["l"] for b in bars if WINDOWS[ticker][0] <= b["date"] <= WINDOWS[ticker][1])

    for it in r.get("items", []):
        text = (it.get("text") or it.get("fullText") or "").strip()
        if not text or text.startswith("RT "):
            continue
        # 必须提到 ticker 或公司名
        text_lower = text.lower()
        if ticker == "SNDK":
            if not any(k in text_lower for k in ["sndk", "sandisk", "闪迪", "$wdc", "western digital"]):
                continue
        elif ticker == "MU":
            if not any(k in text_lower for k in ["micron", "美光", " $mu ", "$mu.", "$mu,", "$mu!", "$mu?", "$mu)", "$mu:", "mu stock", "$mu "]):
                continue

        # author
        author = None
        if isinstance(it.get("author"), dict):
            author = it["author"].get("userName") or it["author"].get("username")
        if not author:
            author = it.get("userName") or it.get("username") or it.get("author_userName")
        if not author:
            # 从 url 提
            url = it.get("url", "")
            m = re.search(r"x\.com/([^/]+)/", url)
            if m:
                author = m.group(1)
        if not author:
            continue
        author = author.lower().lstrip("@")

        # pub date
        pub_date = (it.get("createdAt") or it.get("date") or "")[:10]
        if not pub_date or len(pub_date) < 10:
            continue

        px = find_price_on_or_before(bars, pub_date)
        if px is None:
            continue
        pct = (px - low_px) / low_px * 100

        key = (author, ticker)
        if key not in all_authors or pub_date < all_authors[key]["first_pub_date"]:
            all_authors[key] = {
                "author": author,
                "ticker": ticker,
                "first_pub_date": pub_date,
                "first_text": text[:600],
                "px_at_first_tweet": px,
                "pct_above_low": pct,
                "via_query": query,
                "tweet_count": 1,
                "like_count": it.get("likeCount", 0),
                "view_count": it.get("viewCount", 0),
            }
        else:
            all_authors[key]["tweet_count"] += 1


# 输出
print(f"\n不同 (author, ticker): {len(all_authors)}")
from collections import Counter
by_ticker = Counter(v["ticker"] for v in all_authors.values())
print(f"按 ticker: {dict(by_ticker)}")

for ticker in ["SNDK", "MU"]:
    rows = [v for v in all_authors.values() if v["ticker"] == ticker]
    rows.sort(key=lambda x: x["first_pub_date"])
    print(f"\n--- {ticker}: {len(rows)} authors (按首次提票日期) ---")
    print(f"{'author':22s} {'first_pub':12s} {'px@first':10s} {'%above_low':10s} {'count':6s} {'likes':6s} text snippet")
    for v in rows[:50]:
        snippet = v["first_text"].replace("\n", " ")[:80]
        print(f"  @{v['author']:20s} {v['first_pub_date']:12s} ${v['px_at_first_tweet']:8.2f} {v['pct_above_low']:+8.1f}% {v['tweet_count']:6d} {v['like_count']:6d} {snippet}")

# 保存
with open("/workspace/logs/p4p2b_results.json", "w") as f:
    json.dump({
        "windows": WINDOWS,
        "queries": QUERIES,
        "results_meta": [{"ticker": r["ticker"], "query": r["query"], "run_id": r["run_id"], "items_count": r["items_count"]} for r in results],
        "authors": list(all_authors.values()),
    }, f, indent=2)
print(f"\n✅ saved /workspace/logs/p4p2b_results.json")