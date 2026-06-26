"""tests/test_kol_eval_pipeline.py — KOL 评估管道回归测试

测试目标:用 Serenity (aleabitoreddit) 历史数据回归,验证 kol_eval 输出与
9 轮手工核对结果一致。

关键不变量 (来自手工核对):
- tier_A 348 / tier_B 1225 / tier_C 2410
- tier_A 1m hit 54.2% / median +3.67%
- tier_A 3m hit 65.4% / median +12.90%
- tier_A 6m hit 85.5% / median +37.67%
- SIVE 26.4% 集中度 (top1)
- 5/5 核心票追高 (4 chasing + 1 early)
- confidence grade: B (outlier RED + chasing RED 扣分)
"""
import sys
from pathlib import Path
import math

ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT))

from signalboard.quality.kol_eval import evaluate_kol
from signalboard.quality.tier import classify_all, tier_summary
from signalboard.quality.outlier_audit import audit_outliers
from signalboard.quality.chasing_high import audit_chasing_high, chasing_level
from signalboard.quality.prompt_upgrade import (
    direction_classify_post,
    detect_conditional,
)


DB = "/workspace/data/signalboard_full.db"
HANDLE = "aleabitoreddit"


def _close(actual, expected, tol=1.0):
    """actual 与 expected 差不超过 tol%。"""
    return abs(actual - expected) <= tol


def test_tier_distribution():
    """tier 分层 348 / 1225 / 2410。"""
    import sqlite3
    conn = sqlite3.connect(DB, timeout=30)
    tiers = classify_all(conn)
    dist = tier_summary(tiers)
    conn.close()

    assert dist["A"] == 348, f"tier_A expected 348, got {dist['A']}"
    assert dist["B"] == 1225, f"tier_B expected 1225, got {dist['B']}"
    assert dist["C"] == 2410, f"tier_C expected 2410, got {dist['C']}"
    total = sum(dist.values())
    assert total == 3983, f"total expected 3983, got {total}"


def test_tier_a_3m_hit():
    """tier_A 3m hit_rate 65.4% ± 1%。"""
    report = evaluate_kol(handle=HANDLE, db_path=DB)
    h_3m = report.tier_stats["A"].n_resolved["3m"]
    assert h_3m.n_resolved == 191, f"3m n_resolved expected 191, got {h_3m.n_resolved}"
    assert h_3m.hit_rate is not None
    assert _close(h_3m.hit_rate * 100, 65.4, tol=1.5), \
        f"3m hit_rate expected ~65.4%, got {h_3m.hit_rate*100:.1f}%"
    assert h_3m.median_excess is not None
    assert _close(h_3m.median_excess, 12.9, tol=1.5), \
        f"3m median_excess expected ~12.9%, got {h_3m.median_excess:+.2f}%"


def test_tier_a_6m_hit():
    """tier_A 6m hit_rate 85.5% ± 2%。"""
    report = evaluate_kol(handle=HANDLE, db_path=DB)
    h_6m = report.tier_stats["A"].n_resolved["6m"]
    assert h_6m.n_resolved == 76, f"6m n_resolved expected 76, got {h_6m.n_resolved}"
    assert h_6m.hit_rate is not None
    assert _close(h_6m.hit_rate * 100, 85.5, tol=2.0), \
        f"6m hit_rate expected ~85.5%, got {h_6m.hit_rate*100:.1f}%"


def test_tier_b_hit():
    """tier_B 1m hit ~54.7%, 6m hit ~51.4% (扫描接近 50%)。"""
    report = evaluate_kol(handle=HANDLE, db_path=DB)
    h_1m = report.tier_stats["B"].n_resolved["1m"]
    h_6m = report.tier_stats["B"].n_resolved["6m"]
    assert h_1m.hit_rate is not None
    assert _close(h_1m.hit_rate * 100, 54.7, tol=2.0), \
        f"B 1m hit expected ~54.7%, got {h_1m.hit_rate*100:.1f}%"
    assert h_6m.hit_rate is not None
    assert _close(h_6m.hit_rate * 100, 51.4, tol=3.0), \
        f"B 6m hit expected ~51.4%, got {h_6m.hit_rate*100:.1f}%"


def test_outlier_concentration():
    """SIVE top1 集中度 26.4%。"""
    import sqlite3
    conn = sqlite3.connect(DB, timeout=30)
    tiers = classify_all(conn)
    tier_a = [pid for pid, t in tiers.items() if t == "A"]
    audit = audit_outliers(conn, tier_a, horizon="1m")
    conn.close()

    assert audit.top1_concentration > 0.25, \
        f"top1 concentration expected >25%, got {audit.top1_concentration*100:.1f}%"
    assert audit.top_tickers[0][0] == "SIVE", \
        f"top1 expected SIVE, got {audit.top_tickers[0][0]}"


def test_chasing_high():
    """5/5 核心票 tier_A 首次论证追高 (≥4 chasing + 1 early)。"""
    import sqlite3
    conn = sqlite3.connect(DB, timeout=30)
    tiers = classify_all(conn)
    tier_a = [pid for pid, t in tiers.items() if t == "A"]
    chase = audit_chasing_high(conn, tier_a, top_n=5)
    conn.close()

    assert chase.n_chasing >= 4, f"chasing expected ≥4, got {chase.n_chasing}"
    assert chase.warning_level == "RED", f"chasing warning expected RED, got {chase.warning_level}"

    # AXTI 应该 deep_chasing (>200%)
    axi = next((r for r in chase.records if r.ticker == "AXTI"), None)
    assert axi is not None, "AXTI record missing"
    assert axi.chasing_level == "deep_chasing", \
        f"AXTI expected deep_chasing, got {axi.chasing_level}"
    assert axi.pct_above_pre_low > 200, \
        f"AXTI expected >200% above pre_low, got {axi.pct_above_pre_low:.1f}%"


def test_direction_classify_b_class():
    """B 类 'Strong Sell' 评级应改 neutral。"""
    raw_text = "Adding RGTI to my Strong Sell list. Risks include dilution and weak demand."
    result = direction_classify_post(llm_direction="short", raw_text=raw_text, ticker="RGTI")
    assert result.classified_class == "B", f"expected B, got {result.classified_class}"
    assert result.final_direction == "neutral", f"expected neutral, got {result.final_direction}"


def test_direction_classify_c_class_dip_buy():
    """C 类 'dip buying opportunity' 反向指标,short 改 long。"""
    raw_text = "$XYZ is a dip buying opportunity here, big support at $50."
    result = direction_classify_post(llm_direction="short", raw_text=raw_text, ticker="XYZ")
    assert result.classified_class == "C", f"expected C, got {result.classified_class}"
    assert result.final_direction == "long", f"expected long, got {result.final_direction}"


def test_direction_classify_a_class():
    """A 类真·反向持仓应保留 short。"""
    raw_text = "I'm short $IREN at $50 with stop at $60, target $30. Big position, 5% of portfolio."
    result = direction_classify_post(llm_direction="short", raw_text=raw_text, ticker="IREN")
    assert result.classified_class == "A", f"expected A, got {result.classified_class}"
    assert result.final_direction == "short", f"expected short, got {result.final_direction}"


def test_detect_conditional_true():
    """真条件: 'if SIVE breaks $1.20' 应被检测到。"""
    raw = "I'm bullish on $SIVE. if SIVE breaks $1.20, target is $1.80. otherwise stay patient."
    result = detect_conditional(raw)
    assert result["conditional"], f"expected conditional=True, got {result}"
    assert len(result["triggers"]) > 0, f"expected triggers, got {result}"


def test_detect_conditional_rhetorical():
    """伪条件: 'after SIVE breaks $1.20' (时间修饰) 不应算条件。"""
    raw = "After SIVE breaks $1.20, we'll see momentum. patient accumulation."
    result = detect_conditional(raw)
    assert not result["conditional"], f"expected conditional=False, got {result}"
    assert result["is_rhetorical"], f"expected is_rhetorical=True, got {result}"


def test_confidence_grade():
    """置信度应为 B (outlier RED + chasing RED 扣分)。"""
    report = evaluate_kol(handle=HANDLE, db_path=DB)
    assert report.confidence_grade in ("B", "C"), \
        f"expected grade B or C, got {report.confidence_grade}"


def test_full_report_markdown():
    """完整 markdown 报告应包含 5 个章节。"""
    import tempfile
    with tempfile.NamedTemporaryFile(suffix=".md", delete=False, mode="w") as f:
        out = f.name
    try:
        report = evaluate_kol(handle=HANDLE, db_path=DB, output_path=out)
        with open(out) as f:
            md = f.read()
        assert "# KOL 评估报告" in md
        assert "## 1. Tier 分层" in md
        assert "## 2. Tier × Horizon 记分牌" in md
        assert "## 3. tier_A outlier 自动体检" in md
        assert "## 4. tier_A 追高检验" in md
        assert "## 5. 总评" in md
    finally:
        Path(out).unlink(missing_ok=True)


if __name__ == "__main__":
    import pytest
    pytest.main([__file__, "-v"])