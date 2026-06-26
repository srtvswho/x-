"""P4-10 抓 @jukan05 长段时间 (X) + 试 Substack URL"""
import os, json, time
import urllib.request

APIFY = os.environ["APIFY_TOKEN"]


def fetch_long_timeline(handle, since_str, until_str, max_tweets=2000):
    """since/until 嵌入 searchTerms 字符串,拉长段时间。"""
    from apify_client import ApifyClient
    client = ApifyClient(APIFY)
    inp = {
        "searchTerms": [f"from:{handle} since:{since_str} until:{until_str}"],
        "maxItems": max_tweets,
        "sort": "Latest",
    }
    run = client.actor("apidojo/tweet-scraper").start(run_input=inp)
    print(f"  [start] from:{handle} since:{since_str} → run={run.id[:8]}")
    ds = client.dataset(run.default_dataset_id)
    items = []
    t0 = time.time()
    while time.time() - t0 < 180:
        try:
            cnt = ds.get().item_count or 0
            if cnt >= 50 and time.time() - t0 > 20:
                time.sleep(10)
                items = list(ds.iterate_items())
                break
            time.sleep(3)
        except Exception as e:
            print(f"    err: {e}")
            time.sleep(3)
    else:
        items = list(ds.iterate_items())
    items.sort(key=lambda x: x.get("createdAt", ""))
    return items


# 试 Substack URL 变体
print("=== 试 Substack URL 变体 (curl) ===")
candidates = [
    "https://semiconsam.substack.com",
    "https://semiconsam.substack.com/archive",
    "https://jukan.substack.com",
    "https://jukan05.substack.com",
    "https://jukan05.substack.com/archive",
    "https://www.semiconsam.com",
    "https://medium.com/@semiconsam",
    "https://semiconsam.medium.com",
]
import subprocess
for url in candidates:
    try:
        out = subprocess.check_output(["curl", "-sIL", "--max-time", "8", "-A", "Mozilla/5.0", url], stderr=subprocess.STDOUT, timeout=10).decode()
        first_line = [l for l in out.split("\n") if l][0] if out else "no response"
        print(f"  {url}: {first_line[:100]}")
    except subprocess.TimeoutExpired:
        print(f"  {url}: timeout")
    except Exception as e:
        print(f"  {url}: {type(e).__name__}")


# 拉 @jukan05 长段时间 (多段拼接, Apify 限制单次)
print("\n=== 抓 @jukan05 长段时间 X ===")
all_items = []
periods = [
    ("2024-01-01", "2024-12-31"),
    ("2025-01-01", "2025-08-31"),
    ("2025-09-01", "2026-03-31"),
    ("2026-04-01", "2026-06-22"),
]
for since, until in periods:
    try:
        items = fetch_long_timeline("jukan05", since, until, max_tweets=2000)
        print(f"  → {since} ~ {until}: {len(items)} tweets")
        all_items.extend(items)
    except Exception as e:
        print(f"  ✗ {since} ~ {until}: {e}")
        time.sleep(5)

# 去重 (按 id)
seen = set()
unique = []
for it in all_items:
    tid = it.get("id")
    if tid and tid not in seen:
        seen.add(tid)
        unique.append(it)
unique.sort(key=lambda x: x.get("createdAt", ""))

print(f"\n去重后: {len(unique)} 条")
print(f"最早: {unique[0].get('createdAt','') if unique else 'N/A'}")
print(f"最晚: {unique[-1].get('createdAt','') if unique else 'N/A'}")

# 保存
with open("/workspace/logs/p4p10_jukan05_long_x.json", "w") as f:
    json.dump([{
        "id": it.get("id"),
        "createdAt": it.get("createdAt"),
        "text": it.get("text") or it.get("fullText", ""),
        "like": it.get("likeCount", 0),
        "rt": it.get("retweetCount", 0),
        "reply": it.get("replyCount", 0),
        "view": it.get("viewCount", 0),
        "is_rt": it.get("isRetweet", False),
        "is_quote": it.get("isQuote", False),
        "is_reply": it.get("isReply", False),
        "url": it.get("url", ""),
    } for it in unique], f, indent=2)
print(f"\n✅ saved /workspace/logs/p4p10_jukan05_long_x.json")