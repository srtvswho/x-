"""Quick build_dashboard test - 5 ticker, 验证 logic."""
import sys, sqlite3, json, pathlib, time
sys.path.insert(0, '/workspace/scripts/dashboard')
from build_dashboard import get_call_price, get_now_price, get_sector_pct
import build_dashboard as bd

print("Step 1: SOXX sector pct (1 call)", flush=True)
sector = get_sector_pct('2026-01-01', '2026-06-28')
print(f"  SOXX YTD: {sector}%", flush=True)

# 单 ticker 测时间
print("\nStep 2: 单 ticker 测 (看每次 API 耗时)", flush=True)
for tk in ['MU', 'NVDA']:
    t0 = time.time()
    cp = get_call_price(tk, '2026-05-15')
    np, nd = get_now_price(tk)
    elapsed = time.time() - t0
    print(f"  {tk}: call={cp} now={np} on={nd} ({elapsed:.1f}s)", flush=True)
    time.sleep(4)  # 5 req/min = 12s, 但 2 call → 4s

# 5 ticker 测总时间
print("\nStep 3: 5 ticker 完整 (call + now + cache, 3 req/ticker × 5 = 15 req)", flush=True)
t0 = time.time()
for tk in ['MU', 'NVDA', 'AMD', 'AVGO', 'SNDK']:
    cp, np, nd = get_call_price(tk, '2026-05-15'), *get_now_price(tk)
    print(f"  {tk}: call={cp} now={np} on={nd}", flush=True)
    time.sleep(4)
elapsed = time.time() - t0
print(f"\n  5 ticker 总耗时: {elapsed:.1f}s (avg {elapsed/5:.1f}s/ticker)", flush=True)

# 写 dashboard.html (5 ticker + placeholder)
print("\nStep 4: 写 dashboard.html (5 ticker, placeholder summaries)", flush=True)
con = sqlite3.connect('/workspace/data/signalboard_full.db', timeout=30)
data = bd.query_extractions(con)
all_tickers = bd.query_tickers(con)
con.close()
print(f"  extractions: {len(data)}, all_tickers: {len(all_tickers)}", flush=True)

# 用前 5 ticker
sample = all_tickers[:5]
for t in sample:
    cp, np, raw, exc = bd.get_prices(t['ticker'], t['called_at'][:10])
    t['call_price'], t['now_price'], t['raw_pct'], t['excess_pct'] = cp, np, raw, exc

template = pathlib.Path('/workspace/scripts/dashboard/dashboard.template.html').read_text(encoding='utf-8')
out = template.replace('__RECORDS__', json.dumps(data, ensure_ascii=False))
out = out.replace('__KOLS__', json.dumps(bd.KOLS, ensure_ascii=False))
out = out.replace('__TICKERS__', json.dumps(sample, ensure_ascii=False))
out = out.replace('__SUMMARIES__', json.dumps(bd.load_summaries(), ensure_ascii=False))
pathlib.Path('/workspace/scripts/dashboard/dashboard.html').write_text(out, encoding='utf-8')
print(f"\n✓ dashboard.html: {len(out):,} chars", flush=True)
print(f"  占位符剩余: __RECORDS__={out.count('__RECORDS__')} __SUMMARIES__={out.count('__SUMMARIES__')}", flush=True)