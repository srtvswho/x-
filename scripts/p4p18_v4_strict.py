"""P4-18 最严格修正: drop 3 条 (MU 6-26, AAPL 12-26 明显误抽, AAPL 12-13 边界)"""
import json
from collections import Counter
import statistics

with open("/workspace/logs/p4p13_jukan_verified.json") as f:
    d = json.load(f)
his_v = d["his_predictions_verified"]
rel_v = d["relayed_predictions_verified"]


# 标记要 drop 的 3 条
DROP_IDS = [
    "1938185321130430832",  # MU 6-26 short (误抽, 产业 fact)
    "1872081122404045272",  # AAPL 12-26 short (误抽, product launch 不可行)
    "1999717102924747092",  # AAPL 12-13 short (边界, 消费建议不是建仓)
]

strict_his = [p for p in his_v if str(p.get("source_id", "")) not in DROP_IDS]
print(f"原 30 → 修正 {len(strict_his)} (drop 3)")
print()

# 统计
def stats(lst, bench):
    n = len(lst)
    if n == 0:
        return None
    n_hit = sum(1 for p in lst if p["verification"][bench]["hit"])
    raws = [p["verification"][bench]["raw_ret"] for p in lst]
    excesses = [p["verification"][bench]["excess_ret"] for p in lst]
    return {
        "n": n, "n_hit": n_hit,
        "hit_rate": n_hit / n * 100,
        "med_raw": statistics.median(raws),
        "med_excess": statistics.median(excesses),
        "raw_pos": sum(1 for r in raws if r > 0),
        "raw_neg": sum(1 for r in raws if r < 0),
    }


for bench in ["SPY", "SOXX", "SMH"]:
    print(f"[{bench}]")
    s_strict = stats(strict_his, bench)
    s_orig = stats(his_v, bench)
    s_rel = stats(rel_v, bench)
    print(f"  原 30:      n={s_orig['n']}, hit={s_orig['n_hit']}, hr={s_orig['hit_rate']:.1f}%, med_raw={s_orig['med_raw']:+.1f}%, med_exc={s_orig['med_excess']:+.1f}%, raw_涨={s_orig['raw_pos']}/{s_orig['n']}")
    print(f"  修正 26 (drop 3): n={s_strict['n']}, hit={s_strict['n_hit']}, hr={s_strict['hit_rate']:.1f}%, med_raw={s_strict['med_raw']:+.1f}%, med_exc={s_strict['med_excess']:+.1f}%, raw_涨={s_strict['raw_pos']}/{s_strict['n']}")
    print(f"  搬运 49:    n={s_rel['n']}, hit={s_rel['n_hit']}, hr={s_rel['hit_rate']:.1f}%, med_raw={s_rel['med_raw']:+.1f}%, med_exc={s_rel['med_excess']:+.1f}%, raw_涨={s_rel['raw_pos']}/{s_rel['n']}")
    delta = s_strict['raw_pos']/s_strict['n']*100 - s_rel['raw_pos']/s_rel['n']*100
    print(f"  ** 他 vs 搬运 raw 选股优势: {delta:+.1f}pp")
    print()

# 按方向
print("=" * 60)
print("按方向 (修正后, vs SOXX)")
print("=" * 60)
for dir in ["long", "short"]:
    sub = [p for p in strict_his if p["verification"]["direction"] == dir]
    if not sub:
        continue
    n = len(sub)
    n_hit = sum(1 for p in sub if p["verification"]["SOXX"]["hit"])
    raw = statistics.median([p["verification"]["SOXX"]["raw_ret"] for p in sub])
    exc = statistics.median([p["verification"]["SOXX"]["excess_ret"] for p in sub])
    raw_pos = sum(1 for p in sub if p["verification"]["SOXX"]["raw_ret"] > 0)
    print(f"  {dir}: n={n}, hit={n_hit}, hr={n_hit/n*100:.1f}%, med_raw={raw:+.1f}%, med_exc={exc:+.1f}%, raw_涨={raw_pos}/{n}")

# 按 ticker
print()
print("=" * 60)
print("按 ticker (修正后, vs SOXX)")
print("=" * 60)
ticker_stats = {}
for p in strict_his:
    t = p["verification"]["ticker"]
    if t not in ticker_stats:
        ticker_stats[t] = {"n": 0, "hit": 0, "excs": []}
    ticker_stats[t]["n"] += 1
    if p["verification"]["SOXX"]["hit"]:
        ticker_stats[t]["hit"] += 1
    ticker_stats[t]["excs"].append(p["verification"]["SOXX"]["excess_ret"])

for t, s in sorted(ticker_stats.items(), key=lambda x: -x[1]["n"]):
    med = statistics.median(s["excs"])
    print(f"  {t:8s} n={s['n']}, hit={s['hit']}, hr={s['hit']/s['n']*100:.1f}%, med_excess={med:+.1f}%")

# QCOM 单独 (仅存的 short)
print()
print("=" * 60)
print("唯一留下的 short: QCOM 5-22")
print("=" * 60)
for p in strict_his:
    if p["verification"]["direction"] == "short":
        v = p["verification"]
        print(f"  {p['source_date']} {v['ticker']} short {v['horizon_days']}d: raw={v['SOXX']['raw_ret']:+.1f}%, exc={v['SOXX']['excess_ret']:+.1f}%")
        print(f"    thesis: {p.get('thesis','')}")
        print()
        print("  原文最后一句: 'I still don't recommend Qualcomm stock. It's way overvalued.'")
        print("  性质: 明确的不推荐声明 (negative call) → 抽对")

# 保存
out = {
    "his_predictions_verified": strict_his,
    "relayed_predictions_verified": rel_v,
    "dropped": [
        {
            "source_id": "1938185321130430832",
            "source_date": "2025-06-26",
            "ticker": "MU",
            "original_direction": "short",
            "corrected": "drop (产业 fact-sharing, 不是建仓声明)",
            "raw_text_excerpt": "The reason why Micron CEO SJ did not announce HBM sold-out for 2026... Most industry insiders probably know about it.",
        },
        {
            "source_id": "1872081122404045272",
            "source_date": "2024-12-26",
            "ticker": "AAPL",
            "original_direction": "short",
            "corrected": "drop (product launch 不可行, 不是做空 AAPL)",
            "raw_text_excerpt": "Apple to launch a low-cost VR device by the end of 2025... Samsung Display recently placed an order for pre-mass-production research equipment.",
        },
        {
            "source_id": "1999717102924747092",
            "source_date": "2025-12-13",
            "ticker": "AAPL",
            "original_direction": "short",
            "corrected": "drop (消费建议 '现在买电子产品', 不是 AAPL stock 建仓声明)",
            "raw_text_excerpt": "if you are planning to buy electronics, buy them right now. This is the cheapest they will be. $AAPL",
        },
    ],
    "his_unresolved": d["his_unresolved"],
    "rel_unresolved": d["rel_unresolved"],
}
with open("/workspace/logs/p4p18_strict_verified.json", "w") as f:
    json.dump(out, f, indent=2)
print(f"\n✅ saved /workspace/logs/p4p18_strict_verified.json")