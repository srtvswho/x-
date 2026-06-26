"""Phase 3 P3-1: Polygon.io 覆盖率测试(用户给 key 即可跑)

用法:
  POLYGON_API_KEY=xxx python scripts/phase3_p1_polygon_coverage.py
"""
import sqlite3, time, os, sys
from datetime import datetime, timezone
sys.path.insert(0, "/workspace")

POLYGON_API_KEY = os.environ.get("POLYGON_API_KEY", "").strip()
if not POLYGON_API_KEY:
    print("ERROR: set POLYGON_API_KEY environment variable", flush=True)
    sys.exit(1)

import requests

DB = "data/signalboard_full.db"
BASE = "https://api.polygon.io"

# ===== 同 phase3_p1_coverage.py 的 market_config 简化版 =====
MARKET_CONFIG = {
    "美股":   {"suffix": "",     "benchmark": "^GSPC",  "currency": "USD", "tz": "US/Eastern"},
    "SE":    {"suffix": ".ST",  "benchmark": "^OMX",   "currency": "SEK", "tz": "Europe/Stockholm"},
    "OTC":   {"suffix": "",     "benchmark": "^SP400", "currency": "USD", "tz": "US/Eastern"},
    "TW":    {"suffix": ".TW",  "benchmark": "^TWII",  "currency": "TWD", "tz": "Asia/Taipei"},
    "KR":    {"suffix": ".KS",  "benchmark": "^KS11",  "currency": "KRW", "tz": "Asia/Seoul"},
    "JP":    {"suffix": ".T",   "benchmark": "^N225",  "currency": "JPY", "tz": "Asia/Tokyo"},
    "LSE":   {"suffix": ".L",   "benchmark": "^FTSE",  "currency": "GBP", "tz": "Europe/London"},
    "CA":    {"suffix": ".TO",  "benchmark": "^GSPTSE", "currency": "CAD", "tz": "America/Toronto"},
    "ASX":   {"suffix": ".AX",  "benchmark": "^AXJO",  "currency": "AUD", "tz": "Australia/Sydney"},
    "A股":   {"suffix": ".SS",  "benchmark": "000300.SS", "currency": "CNY", "tz": "Asia/Shanghai"},
    "commodity": {"suffix": "", "benchmark": "DBC",   "currency": "USD", "tz": "US/Eastern"},
    "crypto": {"suffix": "",    "benchmark": "BTC",   "currency": "USD", "tz": "UTC"},
    "未上市": {"suffix": "NONE", "benchmark": "NONE",  "currency": "USD", "tz": "UTC"},
    "欧洲":  {"suffix": ".DE",  "benchmark": "^GDAXI", "currency": "EUR", "tz": "Europe/Berlin"},
}

def resolve_symbol(ticker, market):
    if ticker.isdigit() and 4 <= len(ticker) <= 6:
        cfg = MARKET_CONFIG.get(market, {})
        suffix = cfg.get("suffix", "")
        if suffix == "NONE":
            return None
        return f"{ticker}{suffix}" if suffix else ticker
    if "." in ticker:
        return ticker
    cfg = MARKET_CONFIG.get(market, {})
    suffix = cfg.get("suffix", "")
    if suffix == "NONE":
        return None
    return f"{ticker}{suffix}" if suffix else ticker


def check_symbol_polygon(symbol, date_from="2024-01-01", date_to="2026-06-15"):
    """Polygon aggregate bars 端点。Free tier: 5 req/min,end-of-day."""
    url = f"{BASE}/v2/aggs/ticker/{symbol}/range/1/day/{date_from}/{date_to}"
    params = {"adjusted": "true", "sort": "desc", "limit": 1, "apiKey": POLYGON_API_KEY}
    try:
        r = requests.get(url, params=params, timeout=15)
        if r.status_code == 429:
            return {"ok": False, "reason": "429_rate_limited"}
        if r.status_code == 403:
            return {"ok": False, "reason": f"403_forbidden_{r.json().get('message', '')[:40]}"}
        if r.status_code != 200:
            return {"ok": False, "reason": f"http_{r.status_code}_{r.text[:60]}"}
        data = r.json()
        if data.get("status") != "OK" or data.get("resultsCount", 0) == 0:
            return {"ok": False, "reason": f"no_results_{data.get('status', '')[:30]}"}
        last = data["results"][0]
        return {
            "ok": True,
            "last_close": last.get("c"),
            "last_date": datetime.fromtimestamp(last.get("t", 0)/1000, tz=timezone.utc).strftime("%Y-%m-%d"),
            "rows": data.get("resultsCount", 0),
        }
    except Exception as e:
        return {"ok": False, "reason": f"exc_{str(e)[:50]}"}


# ===== 主流程 =====
print("Phase 3 P3-1 (Polygon): 标的→覆盖率测试", flush=True)
conn = sqlite3.connect(DB, timeout=30)
rows = conn.execute(
    """SELECT ticker, market, count(*) as cnt FROM predictions
       WHERE ticker IS NOT NULL AND ticker != ''
       GROUP BY ticker, market ORDER BY cnt DESC""").fetchall()
print(f"unique (ticker, market): {len(rows)}", flush=True)

to_check = []
unverifiable = []
for t, m, cnt in rows:
    sym = resolve_symbol(t, m)
    if sym is None:
        unverifiable.append((t, m, cnt))
    else:
        to_check.append((t, m, cnt, sym))
print(f"  to_check: {len(to_check)} / unverifiable: {len(unverifiable)}", flush=True)


# ===== 节流跑(5 req/min = 12s/req) =====
results = []
n_ok = 0
n_fail = 0
n_429 = 0
t0 = time.time()

for i, (t, m, cnt, sym) in enumerate(to_check, 1):
    info = check_symbol_polygon(sym)
    results.append((t, m, cnt, sym, info))
    if info["ok"]:
        n_ok += 1
    else:
        n_fail += 1
        if "429" in info.get("reason", ""):
            n_429 += 1
            time.sleep(15)  # 长退避
    if i % 20 == 0:
        elapsed = time.time() - t0
        rate = i / elapsed
        print(f"  [{i}/{len(to_check)}] elapsed={elapsed:.0f}s rate={rate:.2f}/s ok={n_ok} fail={n_fail} 429={n_429}", flush=True)
    time.sleep(12.5)  # 5 req/min = 12s/req 严格

# 写 price_coverage
conn.execute("DROP TABLE IF EXISTS price_coverage")
conn.execute("""
    CREATE TABLE price_coverage (
        ticker TEXT NOT NULL,
        market TEXT NOT NULL,
        yfinance_symbol TEXT,
        n_predictions INTEGER,
        last_close REAL,
        last_date TEXT,
        rows_fetched INTEGER,
        ok INTEGER,
        reason TEXT,
        PRIMARY KEY (ticker, market)
    )
""")
for t, m, cnt, sym, info in results:
    conn.execute(
        """INSERT INTO price_coverage VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
        (t, m, sym, cnt, info.get("last_close"), info.get("last_date"),
         info.get("rows"), 1 if info["ok"] else 0, info.get("reason", ""))
    )
conn.commit()
print(f"\n写 price_coverage {len(results)} 行 (Polygon)", flush=True)
print(f"OK: {n_ok} / Fail: {n_fail} / 429: {n_429}", flush=True)
print(f"耗时: {(time.time()-t0)/60:.1f} min", flush=True)
conn.close()
