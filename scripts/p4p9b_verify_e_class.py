"""P4-9b 验证 ollie_allcaps 36 预测 + 对比 A 类"""
import os, json
from datetime import datetime, timedelta
from collections import defaultdict, Counter
import statistics

PRICE_DIR = "/workspace/data/price_cache"
TODAY = "2026-06-12"


def load_bars(t):
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
    try:
        return datetime.fromisoformat(s.replace("Z", "+00:00")).date()
    except Exception:
        return None


spy = load_bars("SPY")

with open("/workspace/logs/p4p9_e_class_predictions.json") as f:
    preds = json.load(f)


def verify(p):
    d = parse_twitter_date(p.get("createdAt", ""))
    if not d:
        return {"resolved": False, "reason": "no_date"}
    ed = (d + timedelta(days=1)).strftime("%Y-%m-%d")
    horizon = min(int(p.get("horizon_days", 30) or 30), 180)
    xd = min((d + timedelta(days=horizon + 1)).strftime("%Y-%m-%d"), TODAY)
    bars = load_bars(p["ticker"])
    if not bars:
        return {"resolved": False, "reason": f"no_bars_{p['ticker']}"}
    e_px, _ = find_price(bars, ed)
    x_px, _ = find_price(bars, xd)
    if not e_px or not x_px:
        return {"resolved": False, "reason": "no_px"}
    se_px, _ = find_price(spy, ed)
    sx_px, _ = find_price(spy, xd)
    if not se_px or not sx_px:
        return {"resolved": False, "reason": "no_spy"}
    if p["direction"] == "long":
        raw = (x_px - e_px) / e_px
    elif p["direction"] == "short":
        raw = (e_px - x_px) / e_px
    else:
        return {"resolved": False, "reason": "neutral"}
    spy_ret = (sx_px - se_px) / se_px
    excess = raw - spy_ret
    hit = (excess > 0 and p["direction"] == "long") or (excess < 0 and p["direction"] == "short")
    return {
        "resolved": True, "hit": hit,
        "raw_ret": raw * 100, "excess_ret": excess * 100,
        "entry_px": e_px, "exit_px": x_px, "entry_date": ed,
        "horizon_days": horizon, "ticker": p["ticker"],
    }


verified = []
unres = Counter()
for p in preds:
    v = verify(p)
    p["verification"] = v
    if v.get("resolved"):
        verified.append(p)
    else:
        unres[v.get("reason", "?")] += 1

print(f"\n=== @ollie_allcaps 36 预测验证 ===")
print(f"resolved: {len(verified)} / {len(preds)}")
print(f"unresolved: {dict(unres)}")
print()

print(f"{'date':12s} {'ticker':10s} {'dir':6s} {'h':4s} {'entry':8s} {'exit':8s} {'raw':8s} {'excess':8s} {'hit':4s} {'thesis':50s}")
print("-" * 130)
for p in sorted(verified, key=lambda x: x.get("createdAt", "")):
    v = p["verification"]
    hit = "✅" if v["hit"] else "❌"
    print(f"{p['createdAt'][:10]:12s} {v['ticker']:10s} {p['direction']:6s} {v['horizon_days']:3d}d ${v['entry_px']:6.2f} ${v['exit_px']:6.2f} {v['raw_ret']:+6.1f}% {v['excess_ret']:+6.1f}% {hit:4s} {p.get('thesis','')[:50]}")

# 统计
n = len(verified)
n_hit = sum(1 for p in verified if p["verification"]["hit"])
hr = n_hit/n*100 if n else 0
med_exc = statistics.median([p["verification"]["excess_ret"] for p in verified])
med_raw = statistics.median([p["verification"]["raw_ret"] for p in verified])

# 排除 SNDK
verified_no_sndk = [p for p in verified if p["ticker"] != "SNDK"]
n2 = len(verified_no_sndk)
n2_hit = sum(1 for p in verified_no_sndk if p["verification"]["hit"])
hr2 = n2_hit/n2*100 if n2 else 0
med_exc2 = statistics.median([p["verification"]["excess_ret"] for p in verified_no_sndk])
unique_t = sorted(set(p["ticker"] for p in verified_no_sndk))

print(f"\n=== @ollie_allcaps 全样本 ===")
print(f"resolved: {n}, hit: {n_hit}, hit_rate: {hr:.1f}%, med_excess: {med_exc:+.1f}%, med_raw: {med_raw:+.1f}%")
print(f"\n=== @ollie_allcaps 排除 SNDK ===")
print(f"resolved: {n2}, hit: {n2_hit}, hit_rate: {hr2:.1f}%, med_excess: {med_exc2:+.1f}%")
print(f"unique tickers: {','.join(unique_t)}")

# 保存
with open("/workspace/logs/p4p9b_e_verified.json", "w") as f:
    json.dump({
        "all_preds": preds,
        "verified": verified,
        "summary": {
            "total_resolved": n, "hit": n_hit, "hit_rate": hr,
            "med_excess": med_exc, "med_raw": med_raw,
            "no_sndk_resolved": n2, "no_sndk_hit": n2_hit, "no_sndk_hr": hr2,
            "no_sndk_med_exc": med_exc2,
        },
    }, f, indent=2)
print(f"\n✅ saved /workspace/logs/p4p9b_e_verified.json")