"""P4-16 修正 MU 6-26 direction 误抽 + 重算"""
import json
from datetime import datetime, timedelta
from collections import Counter, defaultdict
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


# === Step 1: 看 MU 6-26 原文分类 (4 个候选方向) ===
print("=" * 80)
print("MU 6-26 原文分析 — 4 个候选方向")
print("=" * 80)
print("""
原文: "The reason why Micron CEO SJ did not announce HBM sold-out for 2026 on the conference 
call is simple: Nvidia is delaying the contract. Nvidia is hoping that Samsung will pass HBM3E 
validation, allowing them to buy Micron's HBM at a lower price. That's why they're dragging 
out the negotiations. This information has been cross-verified multiple times. Most industry 
insiders probably know about it."

候选:
1. short MU 180d (原 P4-15 抽取) — ❌ 没有"做空"陈述
2. long MU 180d — ❌ 也没有"看多"陈述
3. neutral 180d — ✅ 中立产业分析, 不构成投资建议
4. 局部风险提示 (local risk) — 不是方向判断, drop

实际上: 他描述 Nvidia 的策略 + 对 Micron HBM 业务的潜在影响, 但没有"建仓"声明。
正确分类: **neutral** (产业事实, 不是投资建议)

如果改成 neutral, verify 算法不会算 (因为 neutral 不算 hit, 也不算 miss)。
所以更准确的处理: **从 his predictions 里 drop 这条**, 因为它不是投资预测。
""")

# === Step 2: 修改 verification 重新跑 ===
print("=" * 80)
print("Step 2: 修改 MU 6-26 方向后重算")
print("=" * 80)

with open("/workspace/logs/p4p13_jukan_verified.json") as f:
    d = json.load(f)

# 原始数据
his_v = d["his_predictions_verified"]
rel_v = d["relayed_predictions_verified"]

# 把 MU 6-26 改为 neutral, 然后从 verify 中排除
fixed_his = [p for p in his_v if not (p["verification"].get("ticker") == "MU" and "1938185321130430832" == str(p.get("source_id", "")))]

# QCOM 5-22 保留 (原文明确)
fixed_qcom = next((p for p in his_v if p["verification"].get("ticker") == "QCOM"), None)

print(f"\n原 30 条 → 修正后 29 条 (drop MU 6-26)")

# === Step 3: 重新算 stats ===
print("\n" + "=" * 80)
print("Step 3: 重新统计 (drop MU 6-26 后)")
print("=" * 80)


def stats(lst, bench):
    n = len(lst)
    if n == 0:
        return None
    n_hit = sum(1 for p in lst if p["verification"][bench]["hit"])
    hr = n_hit / n * 100
    raws = [p["verification"][bench]["raw_ret"] for p in lst]
    excesses = [p["verification"][bench]["excess_ret"] for p in lst]
    return {
        "n": n, "n_hit": n_hit, "hit_rate": hr,
        "med_raw": statistics.median(raws),
        "med_excess": statistics.median(excesses),
        "raw_avg": statistics.mean(raws),
        "raw_pos": sum(1 for r in raws if r > 0),
    }


for bench in ["SPY", "SOXX", "SMH"]:
    print(f"\n[{bench}]")
    # 原始 (含 MU 6-26)
    s_orig = stats(his_v, bench)
    # 修正后 (drop MU 6-26)
    s_fixed = stats(fixed_his, bench)
    # 搬运组
    s_rel = stats(rel_v, bench)
    print(f"  他原创 (原 30):        n={s_orig['n']}, hit={s_orig['n_hit']}, hr={s_orig['hit_rate']:.1f}%, med_raw={s_orig['med_raw']:+.1f}%, med_excess={s_orig['med_excess']:+.1f}%, raw_涨={s_orig['raw_pos']}/{s_orig['n']}")
    print(f"  他原创 (修正 29, drop MU short): n={s_fixed['n']}, hit={s_fixed['n_hit']}, hr={s_fixed['hit_rate']:.1f}%, med_raw={s_fixed['med_raw']:+.1f}%, med_excess={s_fixed['med_excess']:+.1f}%, raw_涨={s_fixed['raw_pos']}/{s_fixed['n']}")
    print(f"  搬运 (49):        n={s_rel['n']}, hit={s_rel['n_hit']}, hr={s_rel['hit_rate']:.1f}%, med_raw={s_rel['med_raw']:+.1f}%, med_excess={s_rel['med_excess']:+.1f}%, raw_涨={s_rel['raw_pos']}/{s_rel['n']}")
    print(f"  ** delta (修正 vs 搬运) raw_涨%: {s_fixed['raw_pos']/s_fixed['n']*100 - s_rel['raw_pos']/s_rel['n']*100:+.1f}pp")


# === Step 4: 重新分类 short 预测 ===
print("\n" + "=" * 80)
print("Step 4: 重新分类 '他做 short' 案例")
print("=" * 80)

print(f"\n原 P4-15: 4 条 short")
print(f"  MU 6-26 (-130% raw) — 误抽, drop")
print(f"  QCOM 5-22 (-14% raw) — 原文最后一句 'I still don't recommend QCOM stock', 正确")
print(f"  AAPL 12-26 (raw?)")
print(f"  QCOM 4-? (待查)")

# 列出所有 short
print("\n修正后所有 short 预测 (n=3 expected):")
for p in fixed_his:
    if p["verification"].get("direction") == "short":
        v = p["verification"]
        print(f"  {p['source_date'][:10]} {v['ticker']:6s} {v['direction']:5s} {v['horizon_days']:3d}d raw={v['SOXX']['raw_ret']:+.1f}% exc={v['SOXX']['excess_ret']:+.1f}%")
        print(f"    thesis: {p.get('thesis','')[:150]}")

# === Step 5: 保存修正版 ===
out = {
    "his_predictions_verified": fixed_his,
    "relayed_predictions_verified": rel_v,
    "dropped": [
        {
            "source_date": "2025-06-26",
            "ticker": "MU",
            "original_direction": "short",
            "corrected_classification": "neutral/drop (产业分析, 非投资建议)",
            "reason": "原文是解释 CEO 为何不宣布 HBM sold-out, 不是看空建仓声明。LLM 抽取过度解读。",
            "raw_text_evidence": "The reason why Micron CEO SJ did not announce HBM sold-out... This information has been cross-verified multiple times. Most industry insiders probably know about it.",
        }
    ],
    "his_unresolved": d["his_unresolved"],
    "rel_unresolved": d["rel_unresolved"],
}
with open("/workspace/logs/p4p16_fixed_verified.json", "w") as f:
    json.dump(out, f, indent=2)
print(f"\n✅ saved /workspace/logs/p4p16_fixed_verified.json")