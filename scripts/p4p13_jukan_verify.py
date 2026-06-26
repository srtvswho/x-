"""P4-13 Jukan 验证管道 — ORIGINAL/RC vs RELAYED 对照 + 三层基准"""
import os, json, time
from datetime import datetime, timedelta
from collections import Counter, defaultdict
import statistics

PRICE_DIR = "/workspace/data/price_cache"
TODAY = "2026-06-12"


def load_bars(t):
    """加载 bars。处理 .KS/.TW 无 cache 情况。"""
    p = f"{PRICE_DIR}/{t}_FULL_HISTORY.json"
    if not os.path.exists(p) and t == "SIVE":
        p = f"{PRICE_DIR}/SIVEF_FULL_HISTORY.json"
    if os.path.exists(p):
        return json.load(open(p))
    return []


def find_price(bars, target):
    for b in bars:
        if b["date"] >= target:
            return b["c"], b["date"]
    return None, None


def parse_twitter_date(s):
    if not s:
        return None
    try:
        return datetime.strptime(s, "%a %b %d %H:%M:%S %z %Y").date()
    except (ValueError, TypeError):
        pass
    # ISO
    try:
        return datetime.fromisoformat(s.replace("Z", "+00:00")).date()
    except Exception:
        pass
    # YYYY-MM-DD
    try:
        return datetime.strptime(s[:10], "%Y-%m-%d").date()
    except Exception:
        return None


# 加载基准
SPY = load_bars("SPY")
SOXX = load_bars("SOXX")
SMH = load_bars("SMH")

print(f"SPY bars: {len(SPY)}")
print(f"SOXX bars: {len(SOXX)}")
print(f"SMH bars: {len(SMH)}")


def verify_pred(p, max_horizon=180):
    """验证单条预测,返回三层基准结果。"""
    d = parse_twitter_date(p.get("source_date", ""))
    if not d:
        return {"resolved": False, "reason": "bad_date"}
    ed = (d + timedelta(days=1)).strftime("%Y-%m-%d")
    horizon = min(int(p.get("horizon_days", 30) or 30), max_horizon)
    xd = min((d + timedelta(days=horizon + 1)).strftime("%Y-%m-%d"), TODAY)

    ticker = p.get("ticker")
    if not ticker:
        return {"resolved": False, "reason": "no_ticker"}

    bars = load_bars(ticker)
    if not bars:
        return {"resolved": False, "reason": f"no_bars_{ticker}"}
    e_px, _ = find_price(bars, ed)
    x_px, _ = find_price(bars, xd)
    if not e_px or not x_px:
        return {"resolved": False, "reason": "no_px"}

    # 三层基准
    results = {}
    for name, bench in [("SPY", SPY), ("SOXX", SOXX), ("SMH", SMH)]:
        se, _ = find_price(bench, ed)
        sx, _ = find_price(bench, xd)
        if not se or not sx:
            continue
        if p["direction"] == "long":
            raw = (x_px - e_px) / e_px
            bench_ret = (sx - se) / se
        elif p["direction"] == "short":
            raw = (e_px - x_px) / e_px
            bench_ret = (sx - se) / se
        else:
            continue
        excess = raw - bench_ret
        hit = (excess > 0 and p["direction"] == "long") or (excess < 0 and p["direction"] == "short")
        results[name] = {
            "raw_ret": raw * 100,
            "excess_ret": excess * 100,
            "hit": hit,
        }

    if not results:
        return {"resolved": False, "reason": "no_bench"}

    return {
        "resolved": True,
        "ticker": ticker,
        "direction": p["direction"],
        "horizon_days": horizon,
        "entry_date": ed,
        "exit_date": xd,
        "entry_px": e_px,
        "exit_px": x_px,
        **results,
    }


# 加载 attribution 数据
with open("/workspace/logs/p4p11_attribution.json") as f:
    d = json.load(f)

his = d["his_predictions"]
rel = d["relayed_only"]

# Verify 两组
print(f"\n=== Verify Jukan ORIGINAL+RC (66) ===")
his_v = []
his_unres = Counter()
for p in his:
    v = verify_pred(p)
    p["verification"] = v
    if v.get("resolved"):
        his_v.append(p)
    else:
        his_unres[v.get("reason", "?")] += 1

print(f"resolved: {len(his_v)}/{len(his)}")
print(f"unresolved: {dict(his_unres)}")

print(f"\n=== Verify Jukan RELAYED (78) ===")
rel_v = []
rel_unres = Counter()
for p in rel:
    v = verify_pred(p)
    p["verification"] = v
    if v.get("resolved"):
        rel_v.append(p)
    else:
        rel_unres[v.get("reason", "?")] += 1

print(f"resolved: {len(rel_v)}/{len(rel)}")
print(f"unresolved: {dict(rel_unres)}")


# ============ 关键对照 ============
print("\n" + "=" * 80)
print("=== 关键对照: 他原创 (ORIGINAL+RC) vs 搬运机构 (RELAYED) ===")
print("=" * 80)


def stats_block(name, lst, bench):
    if not lst:
        return f"  {name}: n=0"
    n = len(lst)
    n_hit = sum(1 for p in lst if p["verification"][bench]["hit"])
    hr = n_hit / n * 100
    med_exc = statistics.median([p["verification"][bench]["excess_ret"] for p in lst])
    med_raw = statistics.median([p["verification"][bench]["raw_ret"] for p in lst])
    return f"  {name}: n={n}, hit={n_hit}, hit_rate={hr:.1f}%, med_excess={med_exc:+.1f}%, med_raw={med_raw:+.1f}%"


for bench_name in ["SPY", "SOXX", "SMH"]:
    print(f"\n[{bench_name}]")
    print(stats_block("他原创 (his)", his_v, bench_name))
    print(stats_block("搬运机构 (rel)", rel_v, bench_name))


# ============ Wilson 下界 ============
print("\n" + "=" * 80)
print("=== Wilson 下界 (95% CI) ===")
print("=" * 80)


def wilson_lower(p_hits, n, z=1.96):
    if n == 0:
        return 0
    phat = p_hits / n
    denom = 1 + z**2 / n
    center = (phat + z**2 / (2 * n)) / denom
    margin = z * ((phat * (1 - phat) + z**2 / (4 * n)) / n) ** 0.5 / denom
    return (center - margin) * 100


for bench in ["SPY", "SOXX", "SMH"]:
    his_hits = sum(1 for p in his_v if p["verification"][bench]["hit"])
    rel_hits = sum(1 for p in rel_v if p["verification"][bench]["hit"])
    his_n = len(his_v)
    rel_n = len(rel_v)
    print(f"\n[{bench}]")
    print(f"  他原创: hit={his_hits}/{his_n}, wilson_lower={wilson_lower(his_hits, his_n):.1f}%")
    print(f"  搬运:   hit={rel_hits}/{rel_n}, wilson_lower={wilson_lower(rel_hits, rel_n):.1f}%")
    if wilson_lower(his_hits, his_n) > 50:
        print(f"  ✅ 他原创 wilson_lower > 50% (true alpha candidate)")
    else:
        print(f"  ❌ 他原创 wilson_lower < 50% (random)")


# ============ 能力圈分析 ============
print("\n" + "=" * 80)
print("=== 能力圈 — 细分领域他原创命中率 (vs SOXX, 半导体板块基准) ===")
print("=" * 80)

# 分组: 韩股 / 美股大票 / 中国半导体相关
GROUPS = {
    "韩股 (Samsung + SK Hynix)": ["005930.KS", "000660.KS", "009150.KS"],
    "美股大票 (NVDA/MU/AMD/INTC/AAPL)": ["NVDA", "MU", "AMD", "INTC", "AAPL"],
    "代工/设备 (TSM/ASML/LRCX/AVGO)": ["TSM", "ASML", "LRCX", "AVGO"],
    "SNDK (Sandisk)": ["SNDK"],
    "中国相关 (无 ticker 但主题)": [],  # None ticker
}

for bench in ["SPY", "SOXX"]:
    print(f"\n[{bench}]")
    for gname, gtickers in GROUPS.items():
        if not gtickers:
            continue
        his_g = [p for p in his_v if p["verification"]["ticker"] in gtickers]
        if not his_g:
            print(f"  {gname}: n=0 (无可 verify)")
            continue
        n = len(his_g)
        n_hit = sum(1 for p in his_g if p["verification"][bench]["hit"])
        hr = n_hit / n * 100
        med_exc = statistics.median([p["verification"][bench]["excess_ret"] for p in his_g])
        wl = wilson_lower(n_hit, n)
        print(f"  {gname}: n={n}, hit={n_hit}, hit_rate={hr:.1f}%, wilson_lower={wl:.1f}%, med_excess={med_exc:+.1f}%")


# ============ 详细每条列表 ============
print("\n" + "=" * 80)
print("=== 他原创 resolved 逐条 (vs SOXX) ===")
print("=" * 80)
print(f"{'date':12s} {'ticker':10s} {'dir':6s} {'h':4s} {'entry':8s} {'exit':8s} {'raw':7s} {'vs_spy':7s} {'vs_soxx':7s} {'vs_smh':7s} {'hit_soxx':8s} {'thesis':50s}")
print("-" * 145)
for p in sorted(his_v, key=lambda x: x["source_date"]):
    v = p["verification"]
    hit = "✅" if v["SOXX"]["hit"] else "❌"
    print(f"{p['source_date'][:10]:12s} {v['ticker']:10s} {v['direction']:6s} {v['horizon_days']:3d}d ${v['entry_px']:6.2f} ${v['exit_px']:6.2f} {v['SOXX']['raw_ret']:+6.1f}% {v['SPY']['excess_ret']:+6.1f}% {v['SOXX']['excess_ret']:+6.1f}% {v['SMH']['excess_ret']:+6.1f}% {hit:8s} {p.get('thesis','')[:50]}")

# 保存
with open("/workspace/logs/p4p13_jukan_verified.json", "w") as f:
    json.dump({
        "his_predictions_verified": his_v,
        "relayed_predictions_verified": rel_v,
        "his_unresolved": dict(his_unres),
        "rel_unresolved": dict(rel_unres),
    }, f, indent=2)
print(f"\n✅ saved /workspace/logs/p4p13_jukan_verified.json")