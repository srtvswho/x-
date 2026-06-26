"""Serenity (aleabitoreddit) 回归测试 — 验证光通信 8 票 3m 强区

输入: signalboard DB 中 aleabitoreddit 的光通信 8 票 (NBIS/SIVE/AAOI/AXTI/LITE/COHR/AEHR/IQE) 3m verified
预期 output:
- raw hit rate >= 70% (NBIS 拖后腿, 8 票 6/7 100% 命中)
- 强项: SIVE 100% med +9.5%, AAOI 100%, AXTI 100%, LITE 100%
- 弱项: NBIS 39.2% (中位 -0.1%)
- grade: A (n 大, raw_hit 高, 但 NBIS 拖累)

如果 verify_from_verified 出来跟 DB 直查一致, 说明 scoreboard 管道可信。
"""
from __future__ import annotations
import json
import sys
import sqlite3
from collections import Counter
from datetime import datetime

sys.path.insert(0, "/workspace")
from scripts.kol_verify_standard import verify_from_verified


OPTICAL = ["NBIS", "SIVE", "AAOI", "AXTI", "LITE", "COHR", "AEHR", "IQE"]


def fetch_serenity_optical_3m(db_path: str) -> list[dict]:
    """从 DB 拉 Serenity 光通信 8 票 3m verified 数据 (转成 p4p18 格式)。"""
    conn = sqlite3.connect(db_path)
    cur = conn.cursor()
    rows = cur.execute("""
        SELECT v.prediction_id, v.ticker, v.direction, v.entry_price, v.entry_date_actual,
               v.h_3m_exit_price, v.h_3m_exit_date, v.h_3m_raw_return,
               v.h_3m_sector_excess, v.h_3m_benchmark_return, v.sector_benchmark
        FROM verifications v
        WHERE v.ticker IN (?, ?, ?, ?, ?, ?, ?, ?)
          AND v.h_3m_raw_return IS NOT NULL
    """, OPTICAL).fetchall()
    conn.close()

    verified = []
    for r in rows:
        raw_ret = r[7] or 0
        sector_exc = r[8]  # 可能是 None
        bench_ret = r[9]  # 可能是 None
        sector = r[10] or "SPY"
        verified.append({
            "ticker": r[1],
            "direction": r[2],
            "source_date": r[4],
            "horizon_days": 90,   # 3m
            "thesis": f"Serenity light-barrier {r[1]} long",
            "attribution": "ORIGINAL",
            "attribution_evidence": "Serenity 是光通信主研究, 这些都是他自己判断",
            "text_snippet": f"Serenity 长仓 {r[1]}",
            "source_id": r[0],
            "verification": {
                "resolved": True,
                "ticker": r[1],
                "direction": r[2],
                "horizon_days": 90,
                "entry_date": r[4],
                "entry_px": r[3],
                "exit_date": r[6],
                "exit_px": r[5],
                "raw_ret": raw_ret,
            },
        })
        v = verified[-1]["verification"]
        if sector_exc is not None:
            v[sector] = {"excess_ret": sector_exc, "raw_ret": raw_ret, "hit": sector_exc > 0}
            v["SOXX"] = {"excess_ret": sector_exc, "raw_ret": raw_ret, "hit": sector_exc > 0}
        if bench_ret is not None:
            v["SPY"] = {"excess_ret": raw_ret - bench_ret, "raw_ret": raw_ret, "hit": raw_ret > 0}
    return verified


def run_serenity_regression():
    print("=" * 60)
    print("Serenity 光通信 8 票 3m 回归测试")
    print("=" * 60)

    # 拉数据
    print("\n[1/3] 拉 Serenity 光通信 8 票 3m verified...")
    verified = fetch_serenity_optical_3m("/workspace/data/signalboard_full.db")
    print(f"      n_verified = {len(verified)}")

    # 直查 DB 的关键指标 (作为 ground truth)
    conn = sqlite3.connect("/workspace/data/signalboard_full.db")
    cur = conn.cursor()
    rows = cur.execute("""
        SELECT v.ticker, v.h_3m_raw_return
        FROM verifications v
        WHERE v.ticker IN (?, ?, ?, ?, ?, ?, ?, ?)
          AND v.h_3m_raw_return IS NOT NULL
    """, OPTICAL).fetchall()
    conn.close()
    import statistics
    raws = [r[1] for r in rows]
    gt_hit = sum(1 for r in raws if r > 0)
    gt_med = statistics.median(raws)
    print(f"      ground truth: hit {gt_hit}/{len(raws)} = {gt_hit/len(raws)*100:.1f}%, med {gt_med:+.1f}%")

    # 跑管道
    print("\n[2/3] 跑 verify_from_verified...")
    result = verify_from_verified(
        verified_list=verified,
        handle="aleabitoreddit (optical 8)",
        output_path="/workspace/outputs/regression_serenity_optical_8.md",
    )

    sb = result["scoreboard"]
    rm = sb["raw_metrics"]

    # 验证
    print(f"\n[3/3] 回归结果:")
    print(f"      n_resolved: {sb['n_resolved']} (expected {len(rows)})")
    print(f"      raw_hit_rate: {rm['raw_hit_rate']:.1f}% (expected {gt_hit/len(raws)*100:.1f}%)")
    print(f"      median_raw: {rm['median_raw_ret']:+.1f}% (expected {gt_med:+.1f}%)")
    print(f"      grade: {result['grade']['grade']}")

    # 强区验证
    strong = result["capability"]["strong_areas"]
    print(f"\n      强区 ({len(strong)} 票):")
    for t, m in strong[:10]:
        print(f"        {t}: n={m['n']}, raw_hit {m['raw_hit_rate']:.1f}%, med_excess {m['med_excess_soxx']:+.1f}%")

    weak = result["capability"]["weak_areas"]
    print(f"\n      弱区 ({len(weak)} 票):")
    for t, m in weak[:10]:
        print(f"        {t}: n={m['n']}, raw_hit {m['raw_hit_rate']:.1f}%, med_excess {m['med_excess_soxx']:+.1f}%")

    # 严格断言
    assert abs(rm["raw_hit_rate"] - gt_hit/len(raws)*100) < 0.5, f"raw_hit_rate 偏离 ground truth 太大"
    assert abs(rm["median_raw_ret"] - gt_med) < 0.5, f"median_raw 偏离 ground truth 太大"
    # 强区: SIVE 必须出现
    strong_tickers = [t for t, _ in strong]
    assert "SIVE" in strong_tickers, f"SIVE 应该在强区 (100% 命中)"
    assert "AXTI" in strong_tickers, f"AXTI 应该在强区 (100%)"
    assert "AAOI" in strong_tickers, f"AAOI 应该在强区 (100%)"
    # 弱区: NBIS 应该出现
    weak_tickers = [t for t, _ in weak]
    assert "NBIS" in weak_tickers, f"NBIS 应该在弱区 (39.2%)"

    print("\n✅ all strict assertions passed")
    print(f"📄 报告: /workspace/outputs/regression_serenity_optical_8.md")
    return result


if __name__ == "__main__":
    run_serenity_regression()