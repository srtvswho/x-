"""P3-13b 增量刷新价格 + 重算 SIVE 3m

策略:
1. 用 Polygon aggs API 批量补全 SPY + 光通信 8 票 (含 SIVEF) 的最近 10 天数据
2. 写入 price_cache FULL_HISTORY.json
3. 重算 SIVE 全部 pending 3m
4. 打印新数据
"""
import os, sqlite3, json, time, requests
from datetime import date, datetime

DB = "/workspace/data/signalboard_full.db"
PRICE_DIR = "/workspace/data/price_cache"
POLY = os.environ.get("POLYGON_API_KEY")
START = "2026-06-13"
END = "2026-06-22"

# 光通信 8 票 + SPY (SIVE 用 SIVEF mirror)
TICKERS = {
    "AAOI": "AAOI",
    "AXTI": "AXTI",
    "COHR": "COHR",
    "CRDO": "CRDO",
    "IQE": "IQE",
    "LITE": "LITE",
    "POET": "POET",
    "SIVE": "SIVEF",  # mirror
    "SPY": "SPY",
}

def fetch_bars(ticker, start, end):
    url = f"https://api.polygon.io/v2/aggs/ticker/{ticker}/range/1/day/{start}/{end}?adjusted=true&apiKey={POLY}"
    r = requests.get(url, timeout=10)
    if r.status_code != 200:
        return None
    data = r.json()
    if "results" not in data:
        return []
    bars = []
    for b in data["results"]:
        # timestamp ms -> date
        from datetime import datetime
        d = datetime.utcfromtimestamp(b["t"] / 1000).strftime("%Y-%m-%d")
        bars.append({
            "date": d,
            "o": b.get("o"),
            "h": b.get("h"),
            "l": b.get("l"),
            "c": b.get("c"),
            "v": b.get("v"),
        })
    return bars


def merge_bars(ticker, new_bars):
    """merge 新 bars 到现有 FULL_HISTORY.json,dedup by date."""
    path = f"{PRICE_DIR}/{ticker}_FULL_HISTORY.json"
    existing = []
    if os.path.exists(path):
        with open(path) as f:
            existing = json.load(f)
    # dedup by date
    by_date = {b["date"]: b for b in existing}
    for b in new_bars:
        by_date[b["date"]] = b
    merged = sorted(by_date.values(), key=lambda x: x["date"])
    with open(path, "w") as f:
        json.dump(merged, f, indent=2)
    return len(new_bars), len(merged), path


# 1. 拉数据
print(f"拉 {START} ~ {END} 数据")
for display, poly_t in TICKERS.items():
    bars = fetch_bars(poly_t, START, END)
    if bars is None:
        print(f"  {display} ({poly_t}): API FAIL")
        time.sleep(12)
        continue
    if not bars:
        print(f"  {display} ({poly_t}): 无新数据")
        time.sleep(12)
        continue
    # SIVE 写到 SIVEF 文件 (display vs cache 文件名不同)
    cache_t = "SIVEF" if display == "SIVE" else display
    added, total, path = merge_bars(cache_t, bars)
    print(f"  {display} ({poly_t}): +{added} bars, total {total} → {path}")
    time.sleep(12)  # 5 req/min

print("\n✅ 价格补全完成")

# 2. 重算 SIVE 3m pending
conn = sqlite3.connect(DB, timeout=30)
c = conn.cursor()

# 拉所有 h_3m pending 且 exit_date <= today
TODAY = "2026-06-22"
rows = c.execute("""
    SELECT v.prediction_id, p.ticker, v.entry_date_actual, v.entry_price,
           v.h_3m_exit_date, p.direction
    FROM verifications v
    JOIN predictions p ON p.prediction_id=v.prediction_id
    WHERE v.h_3m_status='pending' AND v.h_3m_exit_date <= ?
""", (TODAY,)).fetchall()
print(f"\n待重算 h_3m: {len(rows)} 条")

# SIVEF bars
sivef_bars = json.load(open(f"{PRICE_DIR}/SIVEF_FULL_HISTORY.json"))
spy_bars = json.load(open(f"{PRICE_DIR}/SPY_FULL_HISTORY.json"))

def find_bar(bars, target_date):
    """找 >= target_date 的第一个 bar。"""
    for b in bars:
        if b["date"] >= target_date:
            return b
    return None

def find_bar_on_or_before(bars, target_date):
    """找 <= target_date 的最后一个 bar。"""
    found = None
    for b in bars:
        if b["date"] <= target_date:
            found = b
        else:
            break
    return found

sive_updates = []
updated = 0
for pid, ticker, edate, eprice, xd3m, direction in rows:
    # 选择正确的 bars
    if ticker == "SIVE":
        bars = sivef_bars
    else:
        path = f"{PRICE_DIR}/{ticker}_FULL_HISTORY.json"
        if not os.path.exists(path):
            continue
        bars = json.load(open(path))

    if not edate or not isinstance(eprice, (int, float)) or not xd3m:
        continue

    # entry bar (entry_date 当天或之后第一个)
    entry_bar = find_bar_on_or_before(bars, edate) or find_bar(bars, edate)
    if not entry_bar:
        continue
    actual_eprice = entry_bar.get("c") or entry_bar.get("adjClose") or eprice

    # exit bar (exit_date 当天或之后第一个)
    exit_bar = find_bar(bars, xd3m)
    if not exit_bar:
        continue
    xprice = exit_bar.get("c") or exit_bar.get("adjClose")
    if not isinstance(xprice, (int, float)):
        continue

    # raw return
    if direction == "long":
        raw_ret = (xprice - actual_eprice) / actual_eprice
    elif direction == "short":
        raw_ret = (actual_eprice - xprice) / actual_eprice
    else:
        raw_ret = 0

    # SPY entry & exit
    spy_entry = find_bar_on_or_before(spy_bars, edate) or find_bar(spy_bars, edate)
    spy_exit = find_bar(spy_bars, xd3m)
    if not spy_entry or not spy_exit:
        continue
    spy_ret = (spy_exit["c"] - spy_entry["c"]) / spy_entry["c"]
    exc_ret = raw_ret - spy_ret

    # hit / miss
    if direction == "long":
        hit = exc_ret > 0
    elif direction == "short":
        hit = exc_ret < 0
    else:
        hit = False

    status = "resolved_hit" if hit else "resolved_miss"

    c.execute("""
        UPDATE verifications SET
            h_3m_status=?, h_3m_exit_date=?, h_3m_exit_price=?,
            h_3m_raw_return=?, h_3m_excess_return=?
        WHERE prediction_id=?
    """, (status, xd3m, xprice, raw_ret, exc_ret, pid))
    updated += 1

    if ticker == "SIVE":
        sive_updates.append({
            "pid": pid, "edate": edate, "eprice": actual_eprice,
            "xd3m": xd3m, "xprice": xprice, "raw": raw_ret, "exc": exc_ret, "status": status
        })

conn.commit()
print(f"\n更新 {updated} 条 h_3m 状态")

if sive_updates:
    import statistics
    print(f"\n=== SIVE 3m 已 resolve ({len(sive_updates)} 条) ===")
    print(f"{'edate':12s} {'entry':8s} {'exit_date':12s} {'exit':8s} {'raw':8s} {'exc':8s} {'status':12s}")
    for u in sive_updates[:10]:
        print(f"  {u['edate']} ${u['eprice']:.4f} {u['xd3m']} ${u['xprice']:.4f} {u['raw']*100:+6.1f}% {u['exc']*100:+6.1f}% {u['status']}")

    raws = [u['raw']*100 for u in sive_updates]
    excs = [u['exc']*100 for u in sive_updates]
    hits = sum(1 for u in sive_updates if u['status'] == 'resolved_hit')
    print(f"\nSIVE 3m: n={len(sive_updates)} hit={hits} hit_rate={hits/len(sive_updates)*100:.1f}%")
    print(f"  raw median: {statistics.median(raws):+.2f}% / avg: {statistics.mean(raws):+.2f}%")
    print(f"  excess median: {statistics.median(excs):+.2f}% / avg: {statistics.mean(excs):+.2f}%")
    print(f"  max: {max(excs):+.2f}% / min: {min(excs):+.2f}%")

conn.close()