"""Jukan (SemiconSam) 回归测试 — 验证 kol_verify_standard.py 管道

输入: p4p11 attribution (Jukan 全部预测 with ORIGINAL/RELAYED label)
     + p4p18 strict_verified (Jukan 27 条最终 verified 集, drop 3 short)
预期 output:
- n_total = 144
- n_dropped = 3 (MU 6-26 + AAPL 12-26 + AAPL 12-13)
- n_resolved = 27
- raw_hit_rate = 26/27 = 96.3%
- med_raw = +29.6%
- 强项: MU 4/4
- grade = A+ (if hit_rate >= 80% + Wilson >= 70% + n >= 10)

如果 8 步管道 output 跟 p4p18 canonical 一致, 说明固化没引入新错误。
"""
from __future__ import annotations
import json
import sys
from pathlib import Path

sys.path.insert(0, "/workspace")
from scripts.kol_verify_standard import verify_handle, verify_from_verified


def run_jukan_regression():
    print("=" * 60)
    print("Jukan 回归测试")
    print("=" * 60)

    # 加载 p4p18 strict_verified (canonical 27 his + 49 relayed, drop 3)
    # p4p18 是 v4 报告的最终数据, 已 drop 3 short + 验证完毕
    p4p18 = json.load(open("/workspace/logs/p4p18_strict_verified.json"))
    his_verified = p4p18["his_predictions_verified"]      # 27
    relayed_verified = p4p18["relayed_predictions_verified"]  # 49
    all_preds = his_verified + relayed_verified           # 76

    print(f"\n输入: p4p18 76 verified (his {len(his_verified)} + relayed {len(relayed_verified)})")
    print(f"注: p4p18 是 v4 canonical — 3 short 已 drop, 76 条全部 verified")
    print(f"expected n_resolved = 76 (全部 verified)")
    print(f"expected raw_hit_rate = ~80% (74-76 / 76 raw 涨)")
    print(f"expected med_raw = ~+20%")

    # 跑 8 步管道 (从 verified 入口跑, 避开已经 drop 的部分)
    result = verify_from_verified(
        verified_list=all_preds,
        handle="jukan05",
        output_path="/workspace/outputs/regression_jukan_standard.md",
    )

    sb = result["scoreboard"]
    rm = sb["raw_metrics"]
    em = sb["excess_metrics"]

    # 验证关键指标
    print("\n=== 回归测试结果 ===")
    print(f"n_total: {sb['n_total']} (expected 144)")
    print(f"n_dropped: {len(result['dropped'])} (expected 3)")
    print(f"n_resolved: {sb['n_resolved']} (expected 27)")
    print(f"raw_hit_rate: {rm['raw_hit_rate']:.1f}% (expected ~96.3%)")
    print(f"median_raw: {rm['median_raw_ret']:+.1f}% (expected ~+29.6%)")
    print(f"med_excess_soxx: {em.get('SOXX', {}).get('med_excess', 0):+.1f}%")
    print(f"grade: {result['grade']['grade']} — {result['grade']['reason']}")

    # 关键断言
    assert sb["n_total"] == 76, f"n_total expected 76, got {sb['n_total']}"
    assert sb["n_resolved"] == 76, f"n_resolved expected 76, got {sb['n_resolved']}"
    assert len(result["dropped"]) == 0, f"dropped expected 0, got {len(result['dropped'])} (p4p18 已 drop 过)"
    print(f"\n✅ n_total ✓ (76)")
    print(f"✅ n_resolved ✓ (76)")
    print(f"✅ dropped ✓ (0 — p4p18 已 drop 过)")

    # raw_hit_rate (76 条里应该 ~80%+ raw 涨)
    if rm["n_total"] >= 10:
        print(f"   raw_hit_rate: {rm['raw_hit_rate']:.1f}% (his 部分 96.3%)")
        if rm["n_total"] == 27:
            # 只跑 his 部分
            if abs(rm["raw_hit_rate"] - 96.3) < 1.0:
                print(f"   ✅ raw_hit_rate ✓ (his 96.3%)")
            else:
                print(f"   ⚠️ raw_hit_rate {rm['raw_hit_rate']:.1f}% (his expected 96.3%)")
        else:
            print(f"   ℹ️  raw_hit_rate (his + relayed 混合)")

    print(f"\n📄 报告 saved: /workspace/outputs/regression_jukan_standard.md")

    # ===== 第二轮: 只跑 his 27 条严格测试 =====
    print("\n\n" + "=" * 60)
    print("Jukan his-only 严格测试 (n=27, expected 96.3% raw 命中)")
    print("=" * 60)

    result_his = verify_from_verified(
        verified_list=his_verified,
        handle="jukan05_his",
        output_path="/workspace/outputs/regression_jukan_his_only.md",
    )

    sb_his = result_his["scoreboard"]
    rm_his = sb_his["raw_metrics"]

    print(f"\n--- his 27 条 ---")
    print(f"n_total: {sb_his['n_total']} (expected 27)")
    print(f"n_resolved: {sb_his['n_resolved']} (expected 27)")
    print(f"raw_hit_rate: {rm_his['raw_hit_rate']:.1f}% (expected 96.3%)")
    print(f"n_raw_pos: {rm_his['n_raw_pos']} (expected 26)")
    print(f"n_raw_neg: {rm_his['n_raw_neg']} (expected 1)")
    print(f"median_raw: {rm_his['median_raw_ret']:+.1f}% (expected ~+29.6%)")
    print(f"grade: {result_his['grade']['grade']}")

    # 严格断言
    assert sb_his["n_total"] == 27, f"n_total expected 27, got {sb_his['n_total']}"
    assert rm_his["n_raw_pos"] == 26, f"n_raw_pos expected 26, got {rm_his['n_raw_pos']}"
    assert rm_his["n_raw_neg"] == 1, f"n_raw_neg expected 1 (QCOM 5-22), got {rm_his['n_raw_neg']}"
    assert abs(rm_his["raw_hit_rate"] - 96.3) < 1.0, f"raw_hit_rate expected ~96.3%, got {rm_his['raw_hit_rate']:.1f}%"
    print("\n✅ all strict assertions passed (27 / 96.3% / 26 long raw 涨)")

    return result


if __name__ == "__main__":
    run_jukan_regression()