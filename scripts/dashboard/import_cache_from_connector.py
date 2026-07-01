"""
import_cache_from_connector.py — 把 connector 下载的 JSON 写 ticker_prices cache.
agent 跑: 收集 /tmp/us_q_p*.json → 解析 → 写 cache.
"""
import json, sqlite3, sys, datetime
from pathlib import Path

DB = "/workspace/data/signalboard_full.db"

# 找所有 /tmp/us_q_p*.json
files = sorted(Path("/tmp").glob("us_q_p*.json"))
if not files:
    print("未找到 /tmp/us_q_p*.json, 退出")
    sys.exit(1)

print(f"加载 {len(files)} 个 JSON:")
all_rows = []
for f in files:
    print(f"  {f.name}: ", end="", flush=True)
    d = json.loads(f.read_text())
    rows = d['rows']
    print(f"{len(rows)} rows", flush=True)
    all_rows.extend(rows)

print(f"\n总 rows: {len(all_rows)}", flush=True)
tickers = sorted(set(r['secucode'] for r in all_rows))
print(f"unique tickers: {len(tickers)}", flush=True)

# 按 (ticker, pub_date) 聚合
by_kd = {}
for r in all_rows:
    k = (r['secucode'], r['tradingday'])
    by_kd[k] = r

print(f"unique (ticker, date): {len(by_kd)}", flush=True)

# 写 cache
con = sqlite3.connect(DB, timeout=30)
fa = datetime.datetime.now(datetime.timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")
# 拉 now_price = 每个 ticker 最新一天
now_by_ticker = {}
for r in all_rows:
    tk = r['secucode']
    if tk not in now_by_ticker or r['tradingday'] > now_by_ticker[tk][0]:
        now_by_ticker[tk] = (r['tradingday'], r['close'])
print(f"now_price: {len(now_by_ticker)} ticker")

inserted = 0
for (tk, pub_date), r in sorted(by_kd.items()):
    call_p = r['close']
    now_p = now_by_ticker[tk][1]
    now_d = now_by_ticker[tk][0]
    con.execute("""
        INSERT OR REPLACE INTO ticker_prices
        (ticker, pub_date, call_price, now_price, now_date, sector_pct, fetched_at)
        VALUES (?, ?, ?, ?, ?, NULL, ?)
    """, (tk, pub_date, call_p, now_p, now_d, fa))
    inserted += 1

con.commit()
print(f"\n✓ 写 {inserted} 行 ticker_prices cache", flush=True)

# 验证
n = con.execute("SELECT COUNT(*) FROM ticker_prices").fetchone()[0]
print(f"  ticker_prices 总行数: {n}")
con.close()