"""KOL 验证标准流程 — 主入口

输入: handle (e.g. "jukan05") + DB path
输出: 标准 scoreboard (attribution 比例 / raw 命中率 / 板块 α / 能力圈 / 可跟性 / 置信度)

使用:
    python -m scripts.kol_verify_standard --handle jukan05 --db /workspace/data/signalboard_full.db

完整流程 (8 步):
1. 从 DB 拉该 handle 的所有 predictions
2. directional_validator 校验 → drop 误抽
3. attribution classifier 分类 → ORIGINAL / RELAYED / RELAYED+COMMENT
4. 加载 benchmark 数据 (SPY/SOXX/SMH/...)
5. scoreboard 验证 → raw + excess
6. 能力圈分析 (ticker cluster)
7. 置信度分级
8. 输出标准 markdown 报告
"""
from __future__ import annotations
import json
import os
import sqlite3
import argparse
import statistics
from collections import Counter, defaultdict
from datetime import datetime

from signalboard.extract.directional_validator import validate_directional
from signalboard.extract.attribution import classify_attribution
from signalboard.quality.scoreboard import (
    build_scoreboard, load_bars, raw_hit_rate, excess_metrics,
    categorize_predictions, wilson_lower, PRICE_DIR, TODAY,
)
from signalboard.quality.outlier_audit import wilson, hit_rate_excess_median


# === Step 1: 从 DB 拉 predictions ===
def fetch_author_predictions(db_path: str, handle: str) -> list[dict]:
    """从 predictions 表拉该 handle 的所有预测。

    Returns: [{ticker, direction, source_date, horizon_days, thesis, raw_text, source_id}, ...]
    """
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()
    # raw_posts 没有 author_handle, 从 raw_json.author.userName 提取
    rows = cur.execute("""
        SELECT p.ticker, p.direction, p.published_at as source_date,
               p.horizon_days, p.thesis_summary as thesis, p.source_id,
               json_extract(rp.raw_json, '$.author.userName') as author_handle,
               rp.raw_text
        FROM predictions p
        JOIN raw_posts rp ON rp.source_id = p.source_id
        WHERE json_extract(rp.raw_json, '$.author.userName') = ?
    """, (handle,)).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def normalize_predictions(raw_preds: list[dict]) -> list[dict]:
    """把外部 json (p4p11 格式) 标准化为统一格式。

    输入 [{ticker, direction, source_date, source_id, text_snippet, thesis, ...}]
    输出 [{ticker, direction, source_date, source_id, raw_text, thesis, horizon_days, attribution}, ...]
    """
    normed = []
    for p in raw_preds:
        np = dict(p)
        # source_date → date object (verifier handles string)
        if "source_date" not in np and "published_at" in np:
            np["source_date"] = np["published_at"]
        # text_snippet → raw_text (for directional validator)
        if "raw_text" not in np:
            if "text_snippet" in np:
                np["raw_text"] = np["text_snippet"]
            elif "full_text" in np:
                np["raw_text"] = np["full_text"]
        # horizon 可能是字符串 "30d" → 30
        if isinstance(np.get("horizon"), str):
            np["horizon_days"] = int(np["horizon"].replace("d", ""))
        if "horizon_days" not in np and "horizon" in np:
            np["horizon_days"] = 30  # default
        normed.append(np)
    return normed


# === Step 2: directional validator 校验 ===
def validate_predictions(predictions: list[dict]) -> tuple[list[dict], list[dict]]:
    """对每条 prediction 跑 directional_validator。

    Returns: (kept, dropped)
    """
    kept = []
    dropped = []
    for p in predictions:
        raw_text = p.get("raw_text", "")
        ticker = p.get("ticker", "")
        v = validate_directional(raw_text, ticker, p.get("direction", "neutral"))
        if v.action in ("keep", "flip_direction"):
            # 翻方向时, 改 p 的 direction
            p2 = dict(p)
            p2["direction"] = v.final_direction
            p2["validation_action"] = v.action
            p2["validation_reason"] = v.reason
            kept.append(p2)
        else:
            dropped.append({**p, "validation_action": v.action, "validation_reason": v.reason})
    return kept, dropped


# === Step 3: attribution classifier ===
def classify_attributions(predictions: list[dict]) -> list[dict]:
    """对每条 kept 预测跑 attribution classifier。"""
    for p in predictions:
        text = p.get("raw_text", "")
        a = classify_attribution(text)
        p["attribution"] = a.attribution
        p["attribution_method"] = a.method
        p["attribution_evidence"] = a.evidence
    return predictions


# === Step 4: 加载 benchmarks ===
def load_benchmarks(tickers: set[str]) -> dict[str, list[dict]]:
    """根据用户涉及的 ticker, 加载对应基准。

    至少加载: SPY, SOXX, SMH
    韩股用户: 加载 KOSPI (如有)
    """
    benchmarks = {
        "SPY": load_bars("SPY"),
        "SOXX": load_bars("SOXX"),
        "SMH": load_bars("SMH"),
    }
    has_kr = any(t.endswith(".KS") for t in tickers if t)
    if has_kr:
        benchmarks["KOSPI"] = load_bars("KOSPI")
    has_tw = any(t.endswith(".TW") for t in tickers if t)
    if has_tw:
        benchmarks["TWSE"] = load_bars("TWSE")
    has_cn = any(t.endswith(".SS") or t.endswith(".SZ") for t in tickers if t)
    if has_cn:
        benchmarks["CSI300"] = load_bars("CSI300")
    return benchmarks


# === Step 6: 能力圈分析 ===
def analyze_capability(by_ticker: dict) -> dict:
    """根据 by_ticker 找出能力圈 (≥ 3 预测 + hit_rate ≥ 60% + 0 真亏)。

    Returns:
        {
          "strong_areas": [ticker, ...],  # 强项
          "weak_areas": [ticker, ...],    # 弱项
        }
    """
    strong = []
    weak = []
    for t, m in by_ticker.items():
        if m["n"] >= 3:
            if m["raw_hit_rate"] >= 60:
                strong.append((t, m))
            elif m["raw_hit_rate"] < 50:
                weak.append((t, m))
    return {
        "strong_areas": sorted(strong, key=lambda x: -x[1]["raw_hit_rate"]),
        "weak_areas": sorted(weak, key=lambda x: x[1]["raw_hit_rate"]),
    }


# === Step 7: 置信度分级 ===
def grade_confidence(sb: dict, attribution: dict) -> dict:
    """5 级: A+/A/B/C/D (基于 raw 命中率 + 样本量 + 显著性)。

    A+ : raw_hit ≥ 80% + n ≥ 10 + Wilson ≥ 70%
    A  : raw_hit ≥ 70% + n ≥ 5
    B  : raw_hit ≥ 60% + n ≥ 3
    C  : 50-60% 或样本不足
    D  : < 50% 或样本严重不足
    """
    rm = sb["raw_metrics"]
    n = rm["n_total"]
    rate = rm["raw_hit_rate"]
    wilson = sb["wilson_lower_raw_hit_rate"]

    if n < 3:
        grade = "D"   # 样本不足
        reason = f"样本 {n} < 3, 不可信"
    elif n < 5:
        if rate >= 70:
            grade = "C"  # 样本 3-4, 不可给 A
            reason = f"样本 {n} 较小, raw_hit {rate:.1f}%, 仅供参考"
        elif rate >= 50:
            grade = "C"
            reason = f"样本 {n} 较小, raw_hit {rate:.1f}%, 不显著"
        else:
            grade = "D"
            reason = f"样本 {n} 较小, raw_hit {rate:.1f}%, < 50% 表现差"
    elif n < 10:
        if rate >= 80 and wilson >= 60:
            grade = "A"
            reason = f"raw_hit {rate:.1f}%, Wilson {wilson:.1f}%, n={n}"
        elif rate >= 70:
            grade = "B"
            reason = f"raw_hit {rate:.1f}%, Wilson {wilson:.1f}%, n={n}"
        elif rate >= 60:
            grade = "C"
            reason = f"raw_hit {rate:.1f}%, n={n}, 较弱"
        else:
            grade = "D"
            reason = f"raw_hit {rate:.1f}%, n={n}"
    else:  # n >= 10
        if rate >= 80 and wilson >= 70:
            grade = "A+"
            reason = f"raw_hit {rate:.1f}%, Wilson {wilson:.1f}%, n={n}, 强信号"
        elif rate >= 70 and wilson >= 60:
            grade = "A"
            reason = f"raw_hit {rate:.1f}%, Wilson {wilson:.1f}%, n={n}"
        elif rate >= 60:
            grade = "B"
            reason = f"raw_hit {rate:.1f}%, Wilson {wilson:.1f}%, n={n}"
        elif rate >= 50:
            grade = "C"
            reason = f"raw_hit {rate:.1f}%, n={n}"
        else:
            grade = "D"
            reason = f"raw_hit {rate:.1f}%, n={n}, 不显著"

    return {"grade": grade, "reason": reason, "wilson": wilson}


# === Step 8: 输出 markdown 报告 ===
def render_markdown(handle: str, sb: dict, attribution: dict, capability: dict,
                    grade: dict, dropped: list[dict], kept_count: int) -> str:
    """生成标准 scoreboard markdown 报告。"""
    rm = sb["raw_metrics"]
    em_soxx = sb["excess_metrics"].get("SOXX", {})

    # 关键指标卡
    lines = [
        f"# {handle} — KOL Standard Scoreboard",
        "",
        f"**生成时间**: {datetime.now().isoformat()[:19]}  ",
        f"**置信度**: **{grade['grade']}** — {grade['reason']}  ",
        f"**入参**: n_total={sb['n_total']} | n_resolved={sb['n_resolved']} | dropped={len(dropped)}",
        "",
        "## 1. 核心指标 (raw 选股命中率 — 不依赖任何基准)",
        "",
        f"| 指标 | 值 |",
        f"|---|---|",
        f"| n_resolved | {rm['n_total']} |",
        f"| raw 涨 | {rm['n_raw_pos']} |",
        f"| raw 跌 | {rm['n_raw_neg']} |",
        f"| **raw 选股命中率** | **{rm['raw_hit_rate']:.1f}%** |",
        f"| raw 中位 | {rm['median_raw_ret']:+.1f}% |",
        f"| Wilson 95% 下界 | {grade['wilson']:.1f}% |",
        "",
        "## 2. Excess vs Benchmarks",
        "",
        "| Bench | n | med_excess | hit_rate |",
        "|---|---|---|---|",
    ]
    for bench, m in sb["excess_metrics"].items():
        lines.append(f"| {bench} | {m.get('n', '-')} | {m.get('med_excess', 0):+.1f}% | {m.get('hit_rate', 0):.1f}% |")

    # attribution 分布
    lines.extend([
        "",
        "## 3. Attribution 分布 (铁律 3: 区分判断归属)",
        "",
        "| 类型 | 计数 | 比例 |",
        "|---|---|---|",
    ])
    n = max(kept_count, 1)
    for attr, cnt in attribution.items():
        lines.append(f"| {attr} | {cnt} | {cnt/n*100:.1f}% |")

    # 4 分类
    cat = sb["categorized"]
    lines.extend([
        "",
        "## 4. 4 分类 (铁律 6: 禁止 '5 大赢/5 大输' 模糊说法)",
        "",
        f"### 4.1 raw 真赢 ({len(cat['raw_win'])} 条, 选 5 大)",
        "| ticker | direction | horizon | raw_ret | excess_vs_soxx |",
        "|---|---|---|---|---|",
    ])
    for v in cat["raw_win"][:5]:
        ex = v["excess"].get("SOXX", {}).get("excess_ret", 0)
        lines.append(f"| {v['ticker']} | {v['direction']} | {v['horizon_days']}d | {v['raw_ret']:+.1f}% | {ex:+.1f}% |")

    lines.extend([
        "",
        f"### 4.2 raw 真输 ({len(cat['raw_loss'])} 条)",
        "| ticker | direction | horizon | raw_ret | excess_vs_soxx |",
        "|---|---|---|---|---|",
    ])
    for v in cat["raw_loss"][:5]:
        ex = v["excess"].get("SOXX", {}).get("excess_ret", 0)
        lines.append(f"| {v['ticker']} | {v['direction']} | {v['horizon_days']}d | {v['raw_ret']:+.1f}% | {ex:+.1f}% |")

    lines.extend([
        "",
        f"### 4.3 跑赢板块 ({len(cat['excess_win'])} 条, 选 5 大)",
        "| ticker | direction | horizon | raw_ret | excess_vs_soxx |",
        "|---|---|---|---|---|",
    ])
    for v in cat["excess_win"][:5]:
        ex = v["excess"].get("SOXX", {}).get("excess_ret", 0)
        lines.append(f"| {v['ticker']} | {v['direction']} | {v['horizon_days']}d | {v['raw_ret']:+.1f}% | {ex:+.1f}% |")

    lines.extend([
        "",
        f"### 4.4 跑输板块 ({len(cat['excess_loss'])} 条, 含 raw 涨的)",
        "| ticker | direction | horizon | raw_ret | excess_vs_soxx |",
        "|---|---|---|---|---|",
    ])
    for v in cat["excess_loss"][:5]:
        ex = v["excess"].get("SOXX", {}).get("excess_ret", 0)
        lines.append(f"| {v['ticker']} | {v['direction']} | {v['horizon_days']}d | {v['raw_ret']:+.1f}% | {ex:+.1f}% |")

    # 能力圈
    lines.extend([
        "",
        "## 5. 能力圈 (ticker cluster)",
        "",
        f"### 5.1 强项 (raw_hit ≥ 60% + n ≥ 3)",
        "| ticker | n | raw_hit | med_excess_soxx |",
        "|---|---|---|---|",
    ])
    for t, m in capability["strong_areas"][:10]:
        lines.append(f"| {t} | {m['n']} | {m['raw_hit_rate']:.1f}% | {m['med_excess_soxx']:+.1f}% |")

    lines.extend([
        "",
        f"### 5.2 弱项 (raw_hit < 50% + n ≥ 3)",
        "| ticker | n | raw_hit | med_excess_soxx |",
        "|---|---|---|---|",
    ])
    for t, m in capability["weak_areas"][:10]:
        lines.append(f"| {t} | {m['n']} | {m['raw_hit_rate']:.1f}% | {m['med_excess_soxx']:+.1f}% |")

    # dropped
    lines.extend([
        "",
        f"## 6. Dropped 误抽 ({len(dropped)} 条 — 铁律 1+2 自动拦截)",
        "",
        "| source_id | source_date | ticker | original_dir | action | reason |",
        "|---|---|---|---|---|---|",
    ])
    for d in dropped[:20]:
        lines.append(f"| {d['source_id']} | {d['source_date']} | {d['ticker']} | {d['direction']} | {d['validation_action']} | {d['validation_reason'][:60]} |")

    # 跟单建议
    lines.extend([
        "",
        "## 7. 跟单建议",
        "",
    ])
    if grade["grade"] in ("A+", "A"):
        lines.append(f"✅ **可跟单** — 跟 {grade['grade']} 信号")
        if capability["strong_areas"]:
            tickers = ", ".join([t for t, _ in capability["strong_areas"][:5]])
            lines.append(f"- **能力圈**: {tickers}")
        if capability["weak_areas"]:
            tickers = ", ".join([t for t, _ in capability["weak_areas"][:5]])
            lines.append(f"- **避开**: {tickers}")
        if rm["n_total"] < 10:
            lines.append(f"- ⚠️ 样本 {rm['n_total']} < 10, 建议加观察期")
    elif grade["grade"] in ("B", "C"):
        lines.append(f"🟡 **谨慎跟单** — {grade['grade']} 信号, raw_hit {rm['raw_hit_rate']:.1f}%, Wilson {grade['wilson']:.1f}%")
    else:
        lines.append(f"❌ **不跟** — {grade['grade']} 信号, raw_hit {rm['raw_hit_rate']:.1f}% 不显著")

    return "\n".join(lines)


# === 主流程 ===
def verify_handle(handle: str, db_path: str | None = None, output_path: str | None = None,
                  external_predictions: list[dict] | None = None) -> dict:
    """主流程: 输入 handle, 输出标准 scoreboard。

    Args:
        handle: 作者 handle
        db_path: signalboard DB 路径 (如果 external_predictions 给出, 可不传)
        output_path: markdown 输出路径 (None = 仅返回 dict)
        external_predictions: 外部传入的预测列表 (json 格式, for 回归测试)

    Returns:
        {scoreboard: dict, attribution: dict, capability: dict, grade: dict, markdown: str}
    """
    # Step 1
    print(f"[1/7] 拉 {handle} 的 predictions...")
    if external_predictions is not None:
        raw_preds = normalize_predictions(external_predictions)
        print(f"      (外部) raw n = {len(raw_preds)}")
    elif db_path is not None:
        raw_preds = fetch_author_predictions(db_path, handle)
        print(f"      (DB) raw n = {len(raw_preds)}")
    else:
        raise ValueError("必须传 db_path 或 external_predictions")

    # Step 2
    print(f"[2/7] directional_validator 校验...")
    kept, dropped = validate_predictions(raw_preds)
    print(f"      kept = {len(kept)}, dropped = {len(dropped)}")

    # Step 3
    print(f"[3/7] attribution classifier...")
    kept = classify_attributions(kept)
    attribution_count = Counter(p["attribution"] for p in kept)
    print(f"      attribution = {dict(attribution_count)}")

    # Step 4
    print(f"[4/7] 加载 benchmarks...")
    tickers = set(p.get("ticker") for p in kept if p.get("ticker"))
    benchmarks = load_benchmarks(tickers)
    print(f"      benchmarks = {list(benchmarks.keys())}")

    # Step 5
    print(f"[5/7] scoreboard 验证...")
    sb = build_scoreboard(kept, benchmarks)
    print(f"      resolved = {sb['n_resolved']}/{sb['n_total']}")
    print(f"      raw_hit_rate = {sb['raw_metrics']['raw_hit_rate']:.1f}%")

    # Step 6
    print(f"[6/7] 能力圈分析...")
    capability = analyze_capability(sb["by_ticker"])

    # Step 7
    print(f"[7/7] 置信度分级...")
    grade = grade_confidence(sb, attribution_count)
    print(f"      grade = {grade['grade']} — {grade['reason']}")

    # Step 8
    md = render_markdown(handle, sb, attribution_count, capability, grade, dropped, len(kept))
    if output_path:
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        with open(output_path, "w") as f:
            f.write(md)
        print(f"      report saved to {output_path}")

    return {
        "scoreboard": sb,
        "attribution": dict(attribution_count),
        "capability": capability,
        "grade": grade,
        "dropped": dropped,
        "markdown": md,
    }


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--handle", required=True)
    parser.add_argument("--db", default="/workspace/data/signalboard_full.db")
    parser.add_argument("--out", default=None)
    args = parser.parse_args()
    verify_handle(args.handle, args.db, args.out)


def verify_from_verified(verified_list: list[dict], handle: str = "unknown",
                         output_path: str | None = None) -> dict:
    """接受 pre-verified 格式 (p4p18 canonical) 直接转 scoreboard。

    Args:
        verified_list: [{ticker, direction, source_date, horizon_days, verification: {resolved, raw_ret, excess: {SOXX: {excess_ret, hit}}}, ...}, ...]
        handle: handle 名字 (报告用)
        output_path: 输出 markdown 路径

    Returns:
        {scoreboard, attribution, capability, grade, markdown}
    """
    # 转换为统一 verified 格式
    flat_verified = []
    for p in verified_list:
        v = p.get("verification", {})
        if not v.get("resolved"):
            continue
        # raw_ret 优先取 v 顶层 scalar, fallback 从 excess dict 拿
        raw_ret = v.get("raw_ret", 0)
        # 重塑 excess 结构
        excess = {}
        for bench, data in v.items():
            if isinstance(data, dict) and "excess_ret" in data:
                excess[bench] = data
                # raw_ret 顶层优先, 否则从 excess dict 拿
                if raw_ret == 0 and "raw_ret" in data:
                    raw_ret = data["raw_ret"]
        flat_verified.append({
            "resolved": True,
            "ticker": v.get("ticker", p.get("ticker")),
            "direction": v.get("direction", p.get("direction")),
            "horizon_days": v.get("horizon_days", p.get("horizon_days", 30)),
            "entry_date": v.get("entry_date"),
            "exit_date": v.get("exit_date"),
            "entry_px": v.get("entry_px"),
            "exit_px": v.get("exit_px"),
            "raw_ret": raw_ret,
            "excess": excess,
            "is_raw_loss": raw_ret < 0,
            "reason": "ok",
        })

    # 重新走 scoreboard (但跳过 verify step)
    rm = raw_hit_rate(flat_verified)
    em_soxx = excess_metrics(flat_verified, "SOXX")
    em_spy = excess_metrics(flat_verified, "SPY")
    em_smh = excess_metrics(flat_verified, "SMH")

    cat = categorize_predictions(flat_verified)
    by_t = defaultdict(list)
    for v in flat_verified:
        by_t[v["ticker"]].append(v)
    by_ticker = {}
    for t, lst in by_t.items():
        n = len(lst)
        n_hit = sum(1 for v in lst if v["excess"].get("SOXX", {}).get("hit", False))
        n_raw_pos = sum(1 for v in lst if v["raw_ret"] > 0)
        med_excess = statistics.median([
            v["excess"].get("SOXX", {}).get("excess_ret", 0)
            for v in lst if "SOXX" in v["excess"]
        ]) if any("SOXX" in v["excess"] for v in lst) else 0
        by_ticker[t] = {
            "n": n,
            "hit_rate_soxx": n_hit / n * 100 if n else 0,
            "raw_hit_rate": n_raw_pos / n * 100 if n else 0,
            "med_excess_soxx": med_excess,
        }

    attribution_count = Counter(p.get("attribution", "?") for p in verified_list)
    capability = analyze_capability(by_ticker)

    sb = {
        "n_total": len(flat_verified),
        "n_resolved": len(flat_verified),
        "n_unresolved": {},
        "raw_metrics": rm,
        "excess_metrics": {"SPY": em_spy, "SOXX": em_soxx, "SMH": em_smh},
        "categorized": cat,
        "by_horizon": {},
        "by_direction": {},
        "by_ticker": dict(by_ticker),
        "wilson_lower_raw_hit_rate": wilson_lower(rm["n_raw_pos"], rm["n_total"]),
    }
    grade = grade_confidence(sb, attribution_count)
    md = render_markdown(handle, sb, attribution_count, capability, grade, [], len(flat_verified))

    if output_path:
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        with open(output_path, "w") as f:
            f.write(md)

    return {
        "scoreboard": sb,
        "attribution": dict(attribution_count),
        "capability": capability,
        "grade": grade,
        "dropped": [],
        "markdown": md,
    }