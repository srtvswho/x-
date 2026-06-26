"""P4-13b 详细分析 - 按 horizon 拆 + 按方向拆 + ticker 拆分"""
import os, json
from collections import Counter, defaultdict
import statistics

with open("/workspace/logs/p4p13_jukan_verified.json") as f:
    d = json.load(f)
his_v = d["his_predictions_verified"]
rel_v = d["relayed_predictions_verified"]

# === Horizon 拆 ===
print("=" * 80)
print("按 horizon 拆 (30d / 90d / 180d)")
print("=" * 80)


def horizon_stats(lst, bench, h_filter):
    sub = [p for p in lst if p["verification"]["horizon_days"] == h_filter]
    if not sub:
        return None
    n = len(sub)
    n_hit = sum(1 for p in sub if p["verification"][bench]["hit"])
    hr = n_hit / n * 100 if n else 0
    med_exc = statistics.median([p["verification"][bench]["excess_ret"] for p in sub])
    med_raw = statistics.median([p["verification"][bench]["raw_ret"] for p in sub])
    return n, n_hit, hr, med_exc, med_raw


for bench in ["SPY", "SOXX", "SMH"]:
    print(f"\n[{bench}]")
    for h in [30, 90, 180]:
        his_s = horizon_stats(his_v, bench, h)
        rel_s = horizon_stats(rel_v, bench, h)
        if his_s:
            n, h_, hr, me, mr = his_s
            print(f"  30/90/180={h:3d}d 他原创: n={n}, hit={h_}, hr={hr:.1f}%, med_exc={me:+.1f}%, med_raw={mr:+.1f}%")
        if rel_s:
            n, h_, hr, me, mr = rel_s
            print(f"  30/90/180={h:3d}d 搬运:   n={n}, hit={h_}, hr={hr:.1f}%, med_exc={me:+.1f}%, med_raw={mr:+.1f}%")

# === Direction 拆 ===
print("\n" + "=" * 80)
print("按方向拆 (long / short)")
print("=" * 80)
for bench in ["SPY", "SOXX"]:
    print(f"\n[{bench}]")
    for dir in ["long", "short"]:
        his_d = [p for p in his_v if p["verification"]["direction"] == dir]
        rel_d = [p for p in rel_v if p["verification"]["direction"] == dir]
        if his_d:
            n = len(his_d)
            n_hit = sum(1 for p in his_d if p["verification"][bench]["hit"])
            me = statistics.median([p["verification"][bench]["excess_ret"] for p in his_d])
            print(f"  {dir:6s} 他原创: n={n}, hit={n_hit}, hr={n_hit/n*100:.1f}%, med_exc={me:+.1f}%")
        if rel_d:
            n = len(rel_d)
            n_hit = sum(1 for p in rel_d if p["verification"][bench]["hit"])
            me = statistics.median([p["verification"][bench]["excess_ret"] for p in rel_d])
            print(f"  {dir:6s} 搬运:   n={n}, hit={n_hit}, hr={n_hit/n*100:.1f}%, med_exc={me:+.1f}%")

# === Ticker 集中度分析 ===
print("\n" + "=" * 80)
print("按 ticker 拆 (他原创)")
print("=" * 80)

his_by_ticker = defaultdict(list)
for p in his_v:
    his_by_ticker[p["verification"]["ticker"]].append(p)

print(f"\n{'ticker':10s} {'n':4s} {'hit_soxx':8s} {'hr':6s} {'med_exc_soxx':14s} {'consensus':50s}")
for ticker, ps in sorted(his_by_ticker.items(), key=lambda x: -len(x[1])):
    n = len(ps)
    n_hit = sum(1 for p in ps if p["verification"]["SOXX"]["hit"])
    hr = n_hit / n * 100 if n else 0
    me = statistics.median([p["verification"]["SOXX"]["excess_ret"] for p in ps])
    consensus = " / ".join(set(p["verification"]["direction"] for p in ps))
    print(f"  {ticker:10s} {n:4d} {n_hit:8d} {hr:5.1f}% {me:+10.1f}%  {consensus:20s}")


# === 大输 vs 大赢 ===
print("\n" + "=" * 80)
print("他原创 5 大赢 vs 5 大输 (vs SOXX)")
print("=" * 80)
his_sorted = sorted(his_v, key=lambda p: p["verification"]["SOXX"]["excess_ret"], reverse=True)
print("\n=== 5 大赢 (vs SOXX excess 最高) ===")
for p in his_sorted[:5]:
    v = p["verification"]
    print(f"  {p['source_date'][:10]} {v['ticker']:10s} {v['direction']:6s} {v['horizon_days']:3d}d  excess={v['SOXX']['excess_ret']:+.1f}% raw={v['SOXX']['raw_ret']:+.1f}%")
    print(f"    {p.get('thesis','')[:120]}")

print("\n=== 5 大输 (vs SOXX excess 最低) ===")
for p in his_sorted[-5:]:
    v = p["verification"]
    print(f"  {p['source_date'][:10]} {v['ticker']:10s} {v['direction']:6s} {v['horizon_days']:3d}d  excess={v['SOXX']['excess_ret']:+.1f}% raw={v['SOXX']['raw_ret']:+.1f}%")
    print(f"    {p.get('thesis','')[:120]}")

# === 搬运 vs 他 — 同 ticker 同时间 ===
print("\n" + "=" * 80)
print("关键对照 — 他原创 vs 搬运 vs SOXX excess (按 ticker)")
print("=" * 80)
print(f"{'ticker':10s} {'his_n':6s} {'his_avg_exc':14s} {'rel_n':6s} {'rel_avg_exc':14s} {'delta':10s}")
for ticker in set([p["verification"]["ticker"] for p in his_v]):
    his_t = [p for p in his_v if p["verification"]["ticker"] == ticker]
    rel_t = [p for p in rel_v if p["verification"]["ticker"] == ticker]
    his_n = len(his_t)
    rel_n = len(rel_t)
    if his_n == 0 and rel_n == 0:
        continue
    his_avg = statistics.mean([p["verification"]["SOXX"]["excess_ret"] for p in his_t]) if his_t else 0
    rel_avg = statistics.mean([p["verification"]["SOXX"]["excess_ret"] for p in rel_t]) if rel_t else 0
    delta = his_avg - rel_avg
    print(f"  {ticker:10s} {his_n:6d} {his_avg:+12.1f}%  {rel_n:6d} {rel_avg:+12.1f}%  {delta:+8.1f}%")