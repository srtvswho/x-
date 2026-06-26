"""P4-3 A 路 — 修 filter bug,分析已有 500 条 Sandisk 数据

修复:
- "Fri Apr 18 2025" 格式 → 解析成 "2025-04-18" 用 datetime.strptime
- in_window 判断正确

输出:
1. 不同作者 + 首次讲 SNDK/Sandisk 日期 + 当时价 + 当时涨幅
2. DeepSeek 初筛:有分析 vs 喊涨
3. 排序清单
4. 2025-04~05 月早期 + 有分析 的账号原文完整列出
"""
import os, json, re, sqlite3, statistics
from datetime import datetime, timedelta
from collections import defaultdict
from apify_client import ApifyClient

APIFY = os.environ["APIFY_TOKEN"]
client = ApifyClient(APIFY)
PRICE_DIR = "/workspace/data/price_cache"

WINDOW_START = "2025-04-07"
WINDOW_END = "2025-09-08"
LOW_PX = 27.89  # SNDK 2025-04-07 low

def load_bars(t):
    p = f"{PRICE_DIR}/{t}_FULL_HISTORY.json"
    if os.path.exists(p):
        return json.load(open(p))
    return []


def parse_twitter_date(s):
    """解析 Twitter createdAt 格式: 'Fri Aug 08 13:45:23 +0000 2025'"""
    if not s:
        return None
    try:
        # 格式: "Mon Jun 22 07:06:25 +0000 2026"
        return datetime.strptime(s, "%a %b %d %H:%M:%S %z %Y").date()
    except ValueError:
        try:
            # 备选: "2025-08-08T13:45:23.000Z"
            return datetime.fromisoformat(s.replace("Z", "+00:00")).date()
        except Exception:
            return None


def find_price_on_or_before(bars, target_date_str):
    """bars 是 {date, o, h, l, c, v} 格式。target_date_str 是 'YYYY-MM-DD'。"""
    if not bars:
        return None
    px = None
    for b in bars:
        if b["date"] <= target_date_str:
            px = b["c"]
        else:
            break
    return px


# === Step 1: 拉 500 条 Sandisk 数据 ===
print("拉 Sandisk 500 条 dataset...")
run = client.run("mdzFDF7V").get()
items = list(client.dataset(run.default_dataset_id).iterate_items())
print(f"  → {len(items)} 条")

# 也拉 $SNDK 那 319 条
print("拉 $SNDK 319 条 dataset...")
run_sndk = client.run("tTgjb7y7").get()
items_sndk = list(client.dataset(run_sndk.default_dataset_id).iterate_items())
print(f"  → {len(items_sndk)} 条")

# 合并去重 (by tweet id)
seen_ids = set()
all_items = []
for it in items + items_sndk:
    tid = it.get("id")
    if tid and tid not in seen_ids:
        seen_ids.add(tid)
        all_items.append(it)
print(f"合并去重后: {len(all_items)} 条")

# === Step 2: parse dates + filter in window ===
bars = load_bars("SNDK")

window_items = []
date_parse_fail = 0
for it in all_items:
    cd = it.get("createdAt", "")
    d = parse_twitter_date(cd)
    if d is None:
        date_parse_fail += 1
        continue
    d_str = d.isoformat()
    if not (WINDOW_START <= d_str <= WINDOW_END):
        continue
    # 提到 SNDK / Sandisk
    text = (it.get("text") or it.get("fullText") or "").strip()
    text_lower = text.lower()
    if not any(k in text_lower for k in ["sndk", "sandisk", "闪迪"]):
        continue
    if text.startswith("RT "):
        continue
    # author
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
    px = find_price_on_or_before(bars, d_str)
    if px is None:
        continue
    pct = (px - LOW_PX) / LOW_PX * 100

    window_items.append({
        "author": author,
        "pub_date": d_str,
        "text": text,
        "px": px,
        "pct_above_low": pct,
        "like": it.get("likeCount", 0),
        "view": it.get("viewCount", 0),
        "retweet": it.get("retweetCount", 0),
        "url": it.get("url", ""),
        "tweet_id": it.get("id"),
    })

print(f"\nIn window: {len(window_items)} 条 (date_parse_fail={date_parse_fail})")
print(f"Date range: {min(it['pub_date'] for it in window_items) if window_items else 'N/A'} ~ {max(it['pub_date'] for it in window_items) if window_items else 'N/A'}")

# === Step 3: dedup author, 找 earliest ===
authors_earliest = {}
for it in window_items:
    key = it["author"]
    if key not in authors_earliest or it["pub_date"] < authors_earliest[key]["pub_date"]:
        authors_earliest[key] = it

print(f"\n不同 author: {len(authors_earliest)}")

# 排序 (earliest first)
sorted_authors = sorted(authors_earliest.values(), key=lambda x: x["pub_date"])

# 保存 candidates JSON 供 LLM 后续分析
os.makedirs("/workspace/logs", exist_ok=True)
with open("/workspace/logs/p4p3_sandisk_candidates.json", "w") as f:
    json.dump({
        "window": [WINDOW_START, WINDOW_END],
        "low_px": LOW_PX,
        "items_in_window": window_items,
        "authors_earliest": sorted_authors,
        "n_authors": len(sorted_authors),
    }, f, indent=2, default=str)
print(f"\n✅ saved /workspace/logs/p4p3_sandisk_candidates.json")
print(f"   含 {len(window_items)} 条 in-window 推文 + {len(sorted_authors)} 个 dedup 作者")

# === Step 4: 输出 top 早期 (Apr-May) 完整原文 ===
print("\n=== 早期 (2025-04-08 ~ 2025-05-31) 候选人 ===")
early = [a for a in sorted_authors if a["pub_date"] <= "2025-05-31"]
print(f"共 {len(early)} 个早期候选人")
print(f"{'author':22s} {'first_pub':12s} {'px':8s} {'%above_low':10s} {'likes':6s}")
for a in early[:30]:
    print(f"  @{a['author']:20s} {a['pub_date']:12s} ${a['px']:6.2f} {a['pct_above_low']:+8.1f}% {a['like']:6d}")