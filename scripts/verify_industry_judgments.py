"""跑 49 产业判断验证 — 金融数据库 (恒生聚源) + 双基准 (SPX/SOX)"""
import json, os, time, urllib.request, sys
from collections import Counter
from datetime import date, datetime, timedelta
from concurrent.futures import ThreadPoolExecutor, as_completed
from email.utils import parsedate_to_datetime

API = "https://api.deepseek.com/chat/completions"
DEEPSEEK_API_KEY = os.environ["DEEPSEEK_API_KEY"]

# === 24 US ticker 内码 ===
TICKER_MAP = {
    "AAPL": "7006136", "NVDA": "7002258", "MU": "7002720", "TSLA": "7000797",
    "GOOGL": "7003901", "AMZN": "7006270", "AVGO": "7005963", "AMD": "7012998",
    "ARM": "7129132", "INTC": "7003510", "QCOM": "7001672", "MRVL": "7002853",
    "WDC": "7000164", "STX": "7001305", "VRT": "7072731", "COHR": "7003575",
    "LITE": "7007630", "KLAC": "7003170", "LRCX": "7003152", "COIN": "7114479",
    "RIOT": "7010637", "MDB": "7011242", "POET": "7120605", "INVZ": "7114491",
    "MARA": "7006648",
    "SNPS": "7000935", "DELL": "7013376", "CRWV": "7139464", "AMAT": "7006113",
}
# 3 个 index
INDEX_MAP = {
    "SPX": "3210",  # 标普500
    "SOX": "506089",  # 费城半导体
    "NDX": "3205",  # 纳斯达克100
}

# 读 49 judgments
d = json.load(open("/workspace/logs/p5_industry_judgments/judgments_3kols.json"))
ALL_J = []
for h, items in d.items():
    for j in items:
        j["handle"] = h
        ALL_J.append(j)
print(f"total: {len(ALL_J)} judgments")

# 拉 1 个 ticker 全历史 (function)
def fetch_one(code, begin, end):
    """拉 1 个 ticker (stock) 1 个时段"""
    data = json.dumps({
        "api_id": "USStockDailyQuotes",
        "params": {
            "beginDate": begin,
            "endDate": end,
            "stockObject": [code],
            "pageSize": 500,
        }
    }).encode()
    for retry in range(3):
        try:
            req = urllib.request.Request(
                "https://hsmarketwg.shenghentongzhi.com/cloudtest/apigateway/v2/rag/quote/usDailyQuote",
                data=data,
                headers={"Content-Type": "application/json"},
            )
            with urllib.request.urlopen(req, timeout=60) as r:
                resp = json.loads(r.read().decode())
            return resp.get("data", {}).get("rows", [])
        except Exception as e:
            if retry < 2:
                time.sleep(1)
    return []


def fetch_index(code, begin, end):
    data = json.dumps({
        "api_id": "IndexDailyQuote",
        "params": {
            "beginDate": begin,
            "endDate": end,
            "indexObject": [code],
            "pageSize": 500,
        }
    }).encode()
    for retry in range(3):
        try:
            req = urllib.request.Request(
                "https://hsmarketwg.shenghentongzhi.com/cloudtest/apigateway/v2/rag/quote/dailyIndexQuote",
                data=data,
                headers={"Content-Type": "application/json"},
            )
            with urllib.request.urlopen(req, timeout=60) as r:
                resp = json.loads(r.read().decode())
            return resp.get("data", {}).get("rows", [])
        except Exception as e:
            if retry < 2:
                time.sleep(1)
    return []


# Step 1: 拉所有需要的 ticker 全历史
# 时段: 2024-01-01 ~ 2026-06-25 (覆盖所有 judgment)
TICKERS_TO_FETCH = sorted(set(TICKER_MAP.values()))
print(f"\n拉 {len(TICKERS_TO_FETCH)} ticker 全历史 (2024-01 ~ 2026-06-25)...")

PRICE_CACHE = {}  # code -> {date: close}
INDEX_CACHE = {}

t0 = time.time()

def fetch_stock_job(code):
    rows = fetch_one(code, "2024-01-01", "2026-06-25")
    by_date = {}
    for r in rows:
        d = r.get("tradingday")
        if d:
            by_date[d] = r.get("close")
    return code, by_date

with ThreadPoolExecutor(max_workers=10) as pool:
    futures = {pool.submit(fetch_stock_job, c): c for c in TICKERS_TO_FETCH}
    for fut in as_completed(futures):
        try:
            code, by_date = fut.result()
            PRICE_CACHE[code] = by_date
        except Exception as e:
            sys.stderr.write(f"err: {e}\n")
        done = len(PRICE_CACHE)
        if done % 5 == 0:
            print(f"  [{time.time()-t0:.0f}s] {done}/{len(TICKERS_TO_FETCH)}", flush=True)
print(f"  [{time.time()-t0:.0f}s] stock 全部完成, {len(PRICE_CACHE)} ticker")


def fetch_index_job(code):
    rows = fetch_index(code, "2024-01-01", "2026-06-25")
    by_date = {}
    for r in rows:
        d = r.get("tradingday")
        if d:
            by_date[d] = r.get("closeprice")
    return code, by_date

with ThreadPoolExecutor(max_workers=3) as pool:
    futures = {pool.submit(fetch_index_job, c): c for c in INDEX_MAP.values()}
    for fut in as_completed(futures):
        try:
            code, by_date = fut.result()
            INDEX_CACHE[code] = by_date
        except Exception as e:
            sys.stderr.write(f"err: {e}\n")
print(f"  [{time.time()-t0:.0f}s] index 全部完成, {len(INDEX_CACHE)} index")
print(f"  SPX: {len(INDEX_CACHE.get('3210', {}))} 天")
print(f"  SOX: {len(INDEX_CACHE.get('506089', {}))} 天")


# 缓存
json.dump(PRICE_CACHE, open("/workspace/logs/p5_industry_judgments/price_cache_24tickers.json", "w"), indent=2, ensure_ascii=False)
json.dump(INDEX_CACHE, open("/workspace/logs/p5_industry_judgments/index_cache_3.json", "w"), indent=2, ensure_ascii=False)
print("💾 cached")


# Step 2: 验证每个 judgment
def get_price(cache, d_str):
    """找 d_str 当日或之后 5 天内最近的 close"""
    if d_str not in cache:
        # 找之后 5 天
        try:
            d_obj = date.fromisoformat(d_str)
        except:
            return None, None
        for i in range(1, 6):
            nd = (d_obj + timedelta(days=i)).isoformat()
            if nd in cache:
                return nd, cache[nd]
        return None, None
    return d_str, cache[d_str]


def find_exit(cache, entry_date_str, days):
    """找 entry + days 之后 5 天内最近的 close"""
    try:
        e = date.fromisoformat(entry_date_str)
    except:
        return None, None
    target = e + timedelta(days=days)
    for i in range(0, 6):
        nd = (target + timedelta(days=i)).isoformat()
        if nd in cache:
            return nd, cache[nd]
    return None, None


def calc_verification(judgment, ticker, code):
    """对一个 judgment + ticker 计算 raw_ret + excess_ret"""
    pred_date = judgment["date"]
    direction = judgment["direction"]
    handle = judgment["handle"]
    market = judgment.get("implied_market", "US")

    # 拿 entry = next trading day after pred_date
    entry_date, entry_px = get_price(PRICE_CACHE[code], pred_date)
    if entry_px is None:
        return None

    # 取 90d, 180d, 365d 三个 horizon
    out = {
        "handle": handle,
        "date": pred_date,
        "entry_date": entry_date,
        "entry_px": entry_px,
        "ticker": ticker,
        "direction": direction,
        "type": judgment.get("type"),
        "judgment": judgment.get("judgment", "")[:100],
    }

    for h in [30, 90, 180, 365]:
        exit_date, exit_px = find_exit(PRICE_CACHE[code], entry_date, h)
        if exit_px is None:
            out[f"exit_{h}d"] = None
            out[f"raw_{h}d"] = None
            continue
        out[f"exit_{h}d"] = exit_date
        out[f"raw_{h}d"] = (exit_px - entry_px) / entry_px * 100
        # 基准
        for bench_name, bench_code in [("SPX", "3210"), ("SOX", "506089")]:
            bench_e_date, bench_e = get_price(INDEX_CACHE[bench_code], pred_date)
            bench_x_date, bench_x = find_exit(INDEX_CACHE[bench_code], entry_date, h)
            if bench_e and bench_x:
                bench_ret = (bench_x - bench_e) / bench_e * 100
                excess = out[f"raw_{h}d"] - bench_ret
                out[f"excess_{bench_name}_{h}d"] = excess
        # 是否兑现
        raw = out[f"raw_{h}d"]
        if raw is not None:
            if direction == "long":
                out[f"hit_{h}d"] = raw > 0
            elif direction == "short":
                out[f"hit_{h}d"] = raw < 0
            else:
                out[f"hit_{h}d"] = None
    return out


# 跑所有
results = []
for j in ALL_J:
    market = j.get("implied_market", "US")
    if market in ("KR", "TW", "DE", "HK", "US/HK"):  # 不在美股的跳过
        continue
    for t in j.get("implied_tickers", []):
        code = TICKER_MAP.get(t)
        if not code:
            continue
        v = calc_verification(j, t, code)
        if v:
            results.append(v)

print(f"\n验证完: {len(results)} 条")

# 保存
json.dump(results, open("/workspace/logs/p5_industry_judgments/verifications_v1.json", "w"), indent=2, ensure_ascii=False)
print(f"💾 verifications_v1.json")

# 快速统计
print("\n=== 90d hit rate ===")
for h in ["fi56622380", "austinsemis", "zephyr_z9"]:
    sub = [r for r in results if r["handle"] == h and r.get("hit_90d") is not None]
    n_long = sum(1 for r in sub if r["direction"] == "long" and r.get("hit_90d"))
    n_long_tot = sum(1 for r in sub if r["direction"] == "long")
    n_short = sum(1 for r in sub if r["direction"] == "short" and r.get("hit_90d"))
    n_short_tot = sum(1 for r in sub if r["direction"] == "short")
    n_total = len(sub)
    hit = sum(1 for r in sub if r.get("hit_90d"))
    print(f"  @{h}: {n_total} resolved, hit={hit}/{n_total} ({hit/n_total*100:.1f}%) | long {n_long}/{n_long_tot} | short {n_short}/{n_short_tot}")

# raw 90d
print("\n=== 90d median raw_ret ===")
for h in ["fi56622380", "austinsemis", "zephyr_z9"]:
    sub = [r for r in results if r["handle"] == h and r.get("raw_90d") is not None]
    if not sub: continue
    raws = sorted([r["raw_90d"] for r in sub])
    med = raws[len(raws)//2] if raws else 0
    print(f"  @{h}: median raw_90d = {med:.1f}%, n={len(sub)}")
