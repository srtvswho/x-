"""P4-3b 分析已有 dataset (已保存本地)"""
import os, json, re, statistics
from datetime import datetime
from collections import Counter, defaultdict

PRICE_DIR = "/workspace/data/price_cache"
WINDOW_START = "2025-04-07"
WINDOW_END = "2025-09-08"
LOW_PX = 27.89


def load_bars(t):
    p = f"{PRICE_DIR}/{t}_FULL_HISTORY.json"
    if os.path.exists(p):
        return json.load(open(p))
    return []


def parse_twitter_date(s):
    """解析 'Fri Aug 08 13:45:23 +0000 2025' → '2025-08-08'"""
    if not s:
        return None
    try:
        d = datetime.strptime(s, "%a %b %d %H:%M:%S %z %Y").date()
        return d.isoformat()
    except ValueError:
        try:
            return datetime.fromisoformat(s.replace("Z", "+00:00")).date().isoformat()
        except Exception:
            return None


def find_price_on_or_before(bars, target_date_str):
    px = None
    for b in bars:
        if b["date"] <= target_date_str:
            px = b["c"]
        else:
            break
    return px


def get_author(it):
    if isinstance(it.get("author"), dict):
        return (it["author"].get("userName") or it["author"].get("username"))
    a = it.get("userName") or it.get("username") or it.get("author_userName")
    if a: return a
    url = it.get("url", "")
    m = re.search(r"x\.com/([^/]+)/", url)
    return m.group(1) if m else None


def parse_items(items, ticker):
    out = []
    pf = 0
    for it in items:
        text = (it.get("text") or it.get("fullText") or "").strip()
        if not text or text.startswith("RT "):
            continue
        cd = it.get("createdAt", "")
        d = parse_twitter_date(cd)
        if not d:
            pf += 1
            continue
        if not (WINDOW_START <= d <= WINDOW_END):
            continue
        # 提到 SNDK / Sandisk
        text_lower = text.lower()
        if ticker == "SNDK" and not any(k in text_lower for k in ["sndk", "sandisk", "闪迪"]):
            continue
        a = get_author(it)
        if not a:
            continue
        a = a.lower().lstrip("@")
        out.append({"author": a, "pub_date": d, "text": text, "tweet_id": it.get("id"),
                    "like": it.get("likeCount", 0), "view": it.get("viewCount", 0),
                    "retweet": it.get("retweetCount", 0), "url": it.get("url", "")})
    return out, pf


# 拉两份 dataset
with open("/workspace/logs/sandisk_500.json") as f:
    sandisk = json.load(f)
with open("/workspace/logs/sndk_319.json") as f:
    sndk = json.load(f)

print(f"Sandisk dataset: {len(sandisk)} 条")
print(f"$SNDK dataset: {len(sndk)} 条")

# dedup by tweet_id
seen = set()
all_tweets = []
for it in sandisk + sndk:
    tid = it.get("id")
    if tid and tid not in seen:
        seen.add(tid)
        all_tweets.append(it)
print(f"合并去重: {len(all_tweets)} 条")

# parse + filter
parsed, pf = parse_items(all_tweets, "SNDK")
print(f"in-window + 提到 SNDK: {len(parsed)} 条 (date_parse_fail={pf})")

# date range
if parsed:
    print(f"date range: {min(p['pub_date'] for p in parsed)} ~ {max(p['pub_date'] for p in parsed)}")

# per author earliest
bars = load_bars("SNDK")
authors = {}
for p in parsed:
    a = p["author"]
    px = find_price_on_or_before(bars, p["pub_date"])
    if px is None:
        continue
    pct = (px - LOW_PX) / LOW_PX * 100
    p["px"] = px
    p["pct_above_low"] = pct
    if a not in authors or p["pub_date"] < authors[a]["pub_date"]:
        authors[a] = p

sorted_authors = sorted(authors.values(), key=lambda x: x["pub_date"])
print(f"\n不同 author: {len(sorted_authors)}")

# 输出按时间排序
print("\n=== 按 first_pub 排序 (所有 in-window 作者) ===")
print(f"{'author':22s} {'first_pub':12s} {'px':8s} {'%above_low':10s} {'likes':6s} text snippet")
for a in sorted_authors[:80]:
    snippet = a["text"].replace("\n", " ")[:80]
    print(f"  @{a['author']:20s} {a['pub_date']:12s} ${a['px']:6.2f} {a['pct_above_low']:+8.1f}% {a['like']:6d} {snippet}")

# 早期 (Apr + May) — 关键候选
early = [a for a in sorted_authors if a["pub_date"] <= "2025-05-31"]
print(f"\n=== 早期 (≤ 2025-05-31) 候选人: {len(early)} 个 ===")
for a in early:
    snippet = a["text"].replace("\n", " ")[:100]
    print(f"  @{a['author']:20s} {a['pub_date']:12s} ${a['px']:6.2f} {a['pct_above_low']:+8.1f}% likes={a['like']} | {snippet}")

# 按月分布
months = Counter(a["pub_date"][:7] for a in sorted_authors)
print(f"\n作者首次提及月份分布:")
for m, n in sorted(months.items()):
    print(f"  {m}: {n}")

# 保存
with open("/workspace/logs/p4p3b_candidates.json", "w") as f:
    json.dump({
        "window": [WINDOW_START, WINDOW_END],
        "low_px": LOW_PX,
        "n_in_window_tweets": len(parsed),
        "n_authors": len(sorted_authors),
        "n_early_authors": len(early),
        "all_authors_sorted": sorted_authors,
    }, f, indent=2, default=str)
print(f"\n✅ saved /workspace/logs/p4p3b_candidates.json")