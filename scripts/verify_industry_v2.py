"""跑 49 产业判断验证 — 用金融数据库数据"""
import json
from datetime import date, timedelta
from collections import Counter

PRICE = json.load(open("/workspace/logs/p5_industry_judgments/price_cache.json"))
INDEX = json.load(open("/workspace/logs/p5_industry_judgments/index_cache.json"))

# TICKER_MAP (注意是科学计数法存储的)
TICKER_MAP = {
    "AAPL": "7006136", "NVDA": "7002258", "MU": "7002720", "TSLA": "7000797",
    "GOOGL": "7003901", "AMZN": "7006270", "AVGO": "7005963", "AMD": "7012998",
    "ARM": "7129132", "INTC": "7003510", "QCOM": "7001672", "MRVL": "7002853",
    "WDC": "7000164", "STX": "7001305", "VRT": "7072731", "COHR": "7003575",
    "LITE": "7007630", "KLAC": "7003170", "LRCX": "7003152", "COIN": "7114479",
    "RIOT": "7010637", "MDB": "7011242", "POET": "7120605", "INVZ": "7114491",
    "MARA": "7006648", "SNPS": "7000935", "DELL": "7013376", "CRWV": "7139464",
    "AMAT": "7006113",
}

# 数字格式转换
def to_code(c):
    """'7006136' or '7.006136e+06' -> '7006136'"""
    if isinstance(c, str):
        if "e" in c.lower():
            return f"{int(float(c))}"
        return c
    return f"{c}"


# 跑
d = json.load(open("/workspace/logs/p5_industry_judgments/judgments_3kols.json"))
ALL_J = []
for h, items in d.items():
    for j in items:
        j["handle"] = h
        ALL_J.append(j)


def get_price(cache, d_str, max_lookahead=5):
    if d_str in cache:
        return d_str, cache[d_str]
    try:
        d_obj = date.fromisoformat(d_str)
    except:
        return None, None
    for i in range(1, max_lookahead + 1):
        nd = (d_obj + timedelta(days=i)).isoformat()
        if nd in cache:
            return nd, cache[nd]
    return None, None


def find_exit(cache, entry_date_str, days, max_lookahead=5):
    try:
        e = date.fromisoformat(entry_date_str)
    except:
        return None, None
    target = e + timedelta(days=days)
    for i in range(0, max_lookahead + 1):
        nd = (target + timedelta(days=i)).isoformat()
        if nd in cache:
            return nd, cache[nd]
    return None, None


def calc(j, ticker, code, idx_cache_spx, idx_cache_sox, idx_cache_ndx):
    pred_date = j["date"]
    direction = j["direction"]
    handle = j["handle"]

    code_int = to_code(code)
    code_key = code
    cache = PRICE.get(code_key, {})
    if not cache:
        return None

    entry_date, entry_px = get_price(cache, pred_date)
    if entry_px is None:
        return None

    out = {
        "handle": handle,
        "judgment_date": pred_date,
        "entry_date": entry_date,
        "entry_px": entry_px,
        "ticker": ticker,
        "direction": direction,
        "type": j.get("type"),
        "judgment": j.get("judgment", "")[:120],
        "derivation": j.get("derivation_logic", "")[:80],
    }

    for h_days in [30, 90, 180, 365]:
        exit_date, exit_px = find_exit(cache, entry_date, h_days)
        if exit_px is None:
            out[f"raw_{h_days}d"] = None
            out[f"hit_{h_days}d"] = None
            continue
        out[f"exit_{h_days}d"] = exit_date
        out[f"raw_{h_days}d"] = (exit_px - entry_px) / entry_px * 100

        # 基准 SPX / SOX / NDX
        for bench_name, bench_cache in [("SPX", idx_cache_spx), ("SOX", idx_cache_sox), ("NDX", idx_cache_ndx)]:
            bench_e_date, bench_e = get_price(bench_cache, pred_date)
            bench_x_date, bench_x = find_exit(bench_cache, entry_date, h_days)
            if bench_e and bench_x:
                bench_ret = (bench_x - bench_e) / bench_e * 100
                out[f"excess_{bench_name}_{h_days}d"] = out[f"raw_{h_days}d"] - bench_ret

        # hit
        raw = out[f"raw_{h_days}d"]
        if raw is not None:
            if direction == "long":
                out[f"hit_{h_days}d"] = raw > 0
            elif direction == "short":
                out[f"hit_{h_days}d"] = raw < 0
            else:
                out[f"hit_{h_days}d"] = None
    return out


idx_spx = INDEX.get("3210", {})
idx_sox = INDEX.get("506089", {})
idx_ndx = INDEX.get("3205", {})

results = []
for j in ALL_J:
    market = j.get("implied_market", "US")
    if market in ("KR", "TW", "DE", "HK", "US/HK"):
        continue
    for t in j.get("implied_tickers", []):
        code = TICKER_MAP.get(t)
        if not code:
            continue
        v = calc(j, t, code, idx_spx, idx_sox, idx_ndx)
        if v:
            results.append(v)

print(f"verified: {len(results)}")
json.dump(results, open("/workspace/logs/p5_industry_judgments/verifications_v2.json", "w"), indent=2, ensure_ascii=False)

# 90d 统计
print("\n=== 90d 命中率 (raw) ===")
for h in ["fi56622380", "austinsemis", "zephyr_z9"]:
    sub = [r for r in results if r["handle"] == h]
    has_90d = [r for r in sub if r.get("hit_90d") is not None]
    long_hits = [r for r in has_90d if r["direction"] == "long" and r.get("hit_90d")]
    long_tot = sum(1 for r in has_90d if r["direction"] == "long")
    short_hits = [r for r in has_90d if r["direction"] == "short" and r.get("hit_90d")]
    short_tot = sum(1 for r in has_90d if r["direction"] == "short")
    if has_90d:
        hit = sum(1 for r in has_90d if r.get("hit_90d"))
        rate = hit / len(has_90d) * 100
        print(f"  @{h}: {len(has_90d)}/90d resolved, hit={hit}/{len(has_90d)} ({rate:.1f}%) | long {len(long_hits)}/{long_tot} | short {len(short_hits)}/{short_tot}")

print("\n=== 90d median raw_ret / excess_SOX / excess_SPX ===")
for h in ["fi56622380", "austinsemis", "zephyr_z9"]:
    sub = [r for r in results if r["handle"] == h and r.get("raw_90d") is not None]
    if not sub: continue
    raw = sorted([r["raw_90d"] for r in sub])
    ex_sox = sorted([r["excess_SOX_90d"] for r in sub if "excess_SOX_90d" in r])
    ex_spx = sorted([r["excess_SPX_90d"] for r in sub if "excess_SPX_90d" in r])
    med = lambda l: l[len(l)//2] if l else 0
    print(f"  @{h}: n={len(sub)} med_raw={med(raw):.1f}% med_exSOX={med(ex_sox):.1f}pp med_exSPX={med(ex_spx):.1f}pp")

print("\n=== 180d 命中率 (raw) ===")
for h in ["fi56622380", "austinsemis", "zephyr_z9"]:
    sub = [r for r in results if r["handle"] == h]
    has_180d = [r for r in sub if r.get("hit_180d") is not None]
    if has_180d:
        hit = sum(1 for r in has_180d if r.get("hit_180d"))
        rate = hit / len(has_180d) * 100
        print(f"  @{h}: {len(has_180d)}/180d resolved, hit={hit}/{len(has_180d)} ({rate:.1f}%)")
