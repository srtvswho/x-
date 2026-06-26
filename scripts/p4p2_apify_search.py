"""P4-2 Apify 反查 — 搜窗口内讨论 SNDK / MU 的作者

策略:
- 用 apidojo/tweet-scraper V2 actor
- 多个搜索词组合,合并去重
- 输出: authors + 首条推文 + 当时涨幅
"""
import os, json, time, re
from datetime import datetime, date
from apify_client import ApifyClient

APIFY = os.environ["APIFY_TOKEN"]
client = ApifyClient(APIFY)

WINDOWS = {
    "SNDK": ("2025-04-07", "2025-09-08"),
    "MU": ("2025-04-07", "2025-09-11"),
}

# 搜索词 (英文为主,因为 Twitter 英文 KOL 占比高)
QUERIES_SNDK = [
    "$SNDK",
    "Sandisk",
    "$WDC",  # WDC 是 SNDK 的 parent (分拆前)
    "Western Digital flash spinoff",
    "SanDisk spinoff",
]
QUERIES_MU = [
    "$MU",
    "Micron",
]

PRICE_DIR = "/workspace/data/price_cache"
def load_bars(t):
    p = f"{PRICE_DIR}/{t}_FULL_HISTORY.json"
    if not os.path.exists(p) and t == "SIVE":
        p = f"{PRICE_DIR}/SIVEF_FULL_HISTORY.json"
    if os.path.exists(p):
        return json.load(open(p))
    return []


def find_price_on_date(bars, target_date):
    """找 target_date 当天或之后第一个 bar 的 close。"""
    for b in bars:
        if b["date"] >= target_date:
            return b["c"]
    return None


def find_price_on_or_before(bars, target_date):
    """找 <= target_date 最后一个 bar 的 close。"""
    px = None
    for b in bars:
        if b["date"] <= target_date:
            px = b["c"]
        else:
            break
    return px


# Apify actor: apidojo/tweet-scraper (twitter search by advanced query)
ACTOR_ID = "apidojo/tweet-scraper"


def run_apify_search(query, since, until, max_tweets=300):
    """调 apidojo/tweet-scraper 跑一次 twitter 搜索。

    Actor input 字段 (典型):
    - query / searchTerms: 搜索表达式
    - maxTweets: 上限
    - start / end: 时间范围
    """
    # 构造 twitter advanced search query
    # since 和 until 是日期
    full_query = f"{query} since:{since} until:{until}"

    run_input = {
        "searchTerms": [query],
        "maxTweets": max_tweets,
        "since": since,
        "until": until,
        "tweetLanguage": "en",
        "includeSearchTerms": False,
        "onlyVerifiedUsers": False,
        "onlyTwitterBlue": False,
    }

    print(f"\n  [Apify] query='{query}' window={since}~{until} max={max_tweets}")
    try:
        from datetime import timedelta
        run = client.actor(ACTOR_ID).call(
            run_input=run_input,
            timeout=timedelta(seconds=180),
            memory_mbytes=1024,
        )
        # 取 dataset
        if run is None:
            print(f"    → 超时无结果")
            return []
        items = list(client.dataset(run["defaultDatasetId"]).iterate_items())
        print(f"    → 拉回 {len(items)} 条 tweets")
        return items
    except Exception as e:
        print(f"    → ERROR: {e}")
        import traceback
        traceback.print_exc()
        return []


# 主流程
all_authors = {}  # handle -> { ticker_first: SNDK/MU, first_pub_date, first_text, count }

for ticker, (since, until) in WINDOWS.items():
    queries = QUERIES_SNDK if ticker == "SNDK" else QUERIES_MU
    bars = load_bars("SNDF" if ticker == "SNDK" else ticker)  # SNDK 用 SNDK (实际 bars 名是 SNDK)
    if ticker == "SNDK":
        bars = load_bars("SNDK")
    elif ticker == "MU":
        bars = load_bars("MU")

    low_px = min(b["l"] for b in bars if since <= b["date"] <= until)

    print(f"\n{'=' * 60}")
    print(f"{ticker}: window {since} ~ {until}, low_px=${low_px:.2f}")
    print(f"{'=' * 60}")

    for q in queries:
        items = run_apify_search(q, since, until, max_tweets=200)
        # 过滤掉 retweets / 只保留原创 / 提到 ticker
        for it in items:
            text = it.get("text") or it.get("fullText") or it.get("tweetText") or ""
            # 跳过 retweet
            if it.get("isRetweet") or text.startswith("RT "):
                continue
            # 必须真的提到 ticker / 公司
            q_lower = q.lower().replace("$", "")
            text_lower = text.lower()
            has_mention = (
                q_lower in text_lower or
                q.lower() in text_lower or
                (ticker == "SNDK" and ("sandisk" in text_lower or "闪迪" in text)) or
                (ticker == "MU" and "micron" in text_lower or "美光" in text)
            )
            if not has_mention:
                continue

            # 作者
            author = (
                it.get("author", {}).get("userName") if isinstance(it.get("author"), dict) else None
            ) or it.get("userName") or it.get("username") or it.get("author_userName")
            if not author:
                continue
            author = author.lower().lstrip("@")

            pub_date = (
                it.get("createdAt") or it.get("created_at") or it.get("date") or ""
            )[:10]

            # 价格: pub_date 当天或之后第一个 close
            px_at_tweet = find_price_on_date(bars, pub_date)
            if px_at_tweet is None:
                continue
            pct_above_low = (px_at_tweet - low_px) / low_px * 100

            # dedup: 该 author 第一次提 ticker 的时间
            key = (author, ticker)
            if key not in all_authors or pub_date < all_authors[key]["first_pub_date"]:
                all_authors[key] = {
                    "author": author,
                    "ticker": ticker,
                    "first_pub_date": pub_date,
                    "first_text": text[:500],
                    "px_at_first_tweet": px_at_tweet,
                    "pct_above_low_at_first_tweet": pct_above_low,
                    "tweet_count": 1,
                    "via_query": q,
                }
            else:
                all_authors[key]["tweet_count"] += 1

        time.sleep(5)  # 限速

# 输出汇总
print(f"\n{'=' * 60}")
print(f"汇总: 全部 author (dedup by author+ticker)")
print(f"{'=' * 60}")
print(f"不同 (author, ticker) 组合: {len(all_authors)}")
# 按 ticker 统计
from collections import Counter
by_ticker = Counter(v["ticker"] for v in all_authors.values())
print(f"按 ticker:")
for t, n in by_ticker.items():
    print(f"  {t}: {n} unique authors")

# 按 ticker 输出,按 first_pub_date 排序
for ticker in ["SNDK", "MU"]:
    rows = [v for v in all_authors.values() if v["ticker"] == ticker]
    rows.sort(key=lambda x: x["first_pub_date"])
    print(f"\n--- {ticker}: {len(rows)} authors (按首次提票日期排序) ---")
    print(f"{'author':20s} {'first_pub':12s} {'px@first':10s} {'%above_low':10s} {'count':6s} {'via_query':20s} text snippet")
    for v in rows[:50]:
        snippet = v["first_text"].replace("\n", " ")[:80]
        print(f"  @{v['author']:18s} {v['first_pub_date']:12s} ${v['px_at_first_tweet']:8.2f} {v['pct_above_low_at_first_tweet']:+8.1f}% {v['tweet_count']:6d} {v['via_query']:20s} {snippet}")

# 保存 JSON 备查
out = {
    "windows": WINDOWS,
    "queries": {"SNDK": QUERIES_SNDK, "MU": QUERIES_MU},
    "authors": list(all_authors.values()),
}
with open("/workspace/logs/p4p2_apify_results.json", "w") as f:
    json.dump(out, f, indent=2)
print(f"\n✅ saved /workspace/logs/p4p2_apify_results.json")