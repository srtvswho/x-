"""run_kol_eval_tests.py — 不依赖 pytest 的回归测试

每个测试独立 try/except,失败不影响其他测试。
"""
import sys
import traceback
from pathlib import Path

ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT))

from signalboard.quality.kol_eval import evaluate_kol
from signalboard.quality.tier import classify_all, tier_summary
from signalboard.quality.outlier_audit import audit_outliers
from signalboard.quality.chasing_high import audit_chasing_high
from signalboard.quality.prompt_upgrade import (
    direction_classify_post,
    detect_conditional,
)

DB = "/workspace/data/signalboard_full.db"
HANDLE = "aleabitoreddit"


def _close(a, b, tol=1.0):
    return abs(a - b) <= tol


def run_test(name, fn):
    print(f"\n[TEST] {name}")
    try:
        fn()
        print(f"  ✅ PASS")
        return True
    except AssertionError as e:
        print(f"  ❌ FAIL: {e}")
        return False
    except Exception as e:
        print(f"  💥 ERROR: {e}")
        traceback.print_exc()
        return False


def t1_tier_distribution():
    import sqlite3
    conn = sqlite3.connect(DB, timeout=30)
    tiers = classify_all(conn)
    dist = tier_summary(tiers)
    conn.close()
    assert dist["A"] == 348, f"tier_A expected 348, got {dist['A']}"
    assert dist["B"] == 1225, f"tier_B expected 1225, got {dist['B']}"
    assert dist["C"] == 2410, f"tier_C expected 2410, got {dist['C']}"
    assert sum(dist.values()) == 3983


def t2_tier_a_3m():
    report = evaluate_kol(handle=HANDLE, db_path=DB)
    h_3m = report.tier_stats["A"].n_resolved["3m"]
    assert h_3m.n_resolved == 191
    assert h_3m.hit_rate is not None
    assert _close(h_3m.hit_rate * 100, 65.4, tol=1.5)
    assert h_3m.median_excess is not None
    assert _close(h_3m.median_excess, 12.9, tol=1.5)


def t3_tier_a_6m():
    report = evaluate_kol(handle=HANDLE, db_path=DB)
    h_6m = report.tier_stats["A"].n_resolved["6m"]
    assert h_6m.n_resolved == 76
    assert h_6m.hit_rate is not None
    assert _close(h_6m.hit_rate * 100, 85.5, tol=2.0)


def t4_tier_b_6m():
    report = evaluate_kol(handle=HANDLE, db_path=DB)
    h_6m = report.tier_stats["B"].n_resolved["6m"]
    assert h_6m.hit_rate is not None
    assert _close(h_6m.hit_rate * 100, 51.4, tol=3.0), \
        f"B 6m hit expected ~51.4%, got {h_6m.hit_rate*100:.1f}%"


def t5_outlier_sive():
    import sqlite3
    conn = sqlite3.connect(DB, timeout=30)
    tiers = classify_all(conn)
    tier_a = [pid for pid, t in tiers.items() if t == "A"]
    audit = audit_outliers(conn, tier_a, horizon="1m")
    conn.close()
    assert audit.top1_concentration > 0.25
    assert audit.top_tickers[0][0] == "SIVE"


def t6_chasing_high():
    import sqlite3
    conn = sqlite3.connect(DB, timeout=30)
    tiers = classify_all(conn)
    tier_a = [pid for pid, t in tiers.items() if t == "A"]
    chase = audit_chasing_high(conn, tier_a, top_n=5)
    conn.close()
    assert chase.n_chasing >= 4
    assert chase.warning_level == "RED"
    axi = next((r for r in chase.records if r.ticker == "AXTI"), None)
    assert axi is not None
    assert axi.chasing_level == "deep_chasing"
    assert axi.pct_above_pre_low > 200


def t7_direction_b():
    raw = "Adding RGTI to my Strong Sell list. Risks include dilution."
    r = direction_classify_post(llm_direction="short", raw_text=raw, ticker="RGTI")
    assert r.classified_class == "B"
    assert r.final_direction == "neutral"


def t8_direction_c_dip_buy():
    raw = "$XYZ is a dip buying opportunity here, big support at $50."
    r = direction_classify_post(llm_direction="short", raw_text=raw, ticker="XYZ")
    assert r.classified_class == "C"
    assert r.final_direction == "long"


def t9_direction_a():
    raw = "I'm short $IREN at $50 with stop at $60, target $30."
    r = direction_classify_post(llm_direction="short", raw_text=raw, ticker="IREN")
    assert r.classified_class == "A"
    assert r.final_direction == "short"


def t10_detect_conditional_true():
    raw = "I'm bullish on $SIVE. if SIVE breaks $1.20, target is $1.80."
    r = detect_conditional(raw)
    assert r["conditional"]
    assert len(r["triggers"]) > 0


def t11_detect_conditional_rhetorical():
    raw = "After SIVE breaks $1.20, we'll see momentum."
    r = detect_conditional(raw)
    assert not r["conditional"]
    assert r["is_rhetorical"]


def t12_confidence_grade():
    report = evaluate_kol(handle=HANDLE, db_path=DB)
    assert report.confidence_grade in ("B", "C")


def t13_full_report():
    out = "/tmp/test_kol_report.md"
    Path(out).parent.mkdir(parents=True, exist_ok=True)
    report = evaluate_kol(handle=HANDLE, db_path=DB, output_path=out)
    md = Path(out).read_text()
    assert "# KOL 评估报告" in md
    assert "## 1. Tier 分层" in md
    assert "## 2. Tier × Horizon 记分牌" in md
    assert "## 3. tier_A outlier 自动体检" in md
    assert "## 4. tier_A 追高检验" in md
    assert "## 5. 总评" in md
    Path(out).unlink(missing_ok=True)


tests = [
    ("tier 分层 348/1225/2410", t1_tier_distribution),
    ("tier_A 3m hit 65.4% / med +12.9%", t2_tier_a_3m),
    ("tier_A 6m hit 85.5%", t3_tier_a_6m),
    ("tier_B 6m hit 51.4% (扫货无 α)", t4_tier_b_6m),
    ("SIVE top1 集中度 26.4%", t5_outlier_sive),
    ("追高 5/5 (AXTI deep_chasing)", t6_chasing_high),
    ("direction B 类 (Strong Sell → neutral)", t7_direction_b),
    ("direction C 类 (dip buy 反向 → long)", t8_direction_c_dip_buy),
    ("direction A 类 (持仓 short 保留)", t9_direction_a),
    ("detect conditional 真条件", t10_detect_conditional_true),
    ("detect conditional 修辞不识别", t11_detect_conditional_rhetorical),
    ("confidence grade B/C", t12_confidence_grade),
    ("完整 markdown 5 章节", t13_full_report),
]


def main():
    print("=" * 60)
    print("KOL 评估管道回归测试 (Serenity)")
    print("=" * 60)
    passed = 0
    for name, fn in tests:
        if run_test(name, fn):
            passed += 1
    print(f"\n{'=' * 60}")
    print(f"结果: {passed}/{len(tests)} 通过")
    print(f"{'=' * 60}")
    return 0 if passed == len(tests) else 1


if __name__ == "__main__":
    sys.exit(main())