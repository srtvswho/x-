"""金标评测脚本:对照 LLM 输出 vs 金标,计算各项指标。

输入:
  - LLM 输出: list of (post_id, llm_response_dict)
  - 金标: signalboard.extract.goldset.GOLD_V1

输出: 各项指标(P/R/F1/conviction/flags) + 假阳/假阴清单
"""
from __future__ import annotations

import json
from dataclasses import dataclass, field
from typing import List, Optional

from .goldset import GOLD_V1, get_gold_ids, get_gold_entry


# ---------------------------------------------------------------------------
# 评测数据结构
# ---------------------------------------------------------------------------


@dataclass
class LLMPrediction:
    """单条 LLM 输出的预测记录(后处理过的,可直接比对)。"""
    post_id: str
    ticker: str
    market: str
    direction: str
    claim_type: str
    horizon: str
    conviction: int
    thesis_summary: str = ""
    raw_asset_mention: str = ""
    # LLM 附带的帖子级标记
    flags: List[str] = field(default_factory=list)


@dataclass
class LLMPostResult:
    """LLM 对单条推文的完整输出。"""
    post_id: str
    has_prediction: bool
    predictions: List[LLMPrediction] = field(default_factory=list)
    flags: List[str] = field(default_factory=list)
    extraction_notes: str = ""


@dataclass
class EvalReport:
    """评测报告。"""
    n_posts: int = 0
    n_predictions_gold: int = 0
    n_predictions_llm: int = 0

    # 帖子级
    post_precision: float = 0.0  # has_prediction=True 中金标也 True 的比例(假阳是大敌)
    post_recall: float = 0.0     # 金标 True 中 LLM 也 True 的比例
    post_true_pos: int = 0
    post_false_pos: int = 0
    post_false_neg: int = 0

    # 记录级(post_id + ticker + direction 三元组)
    record_precision: float = 0.0
    record_recall: float = 0.0
    record_f1: float = 0.0
    record_tp: int = 0
    record_fp: int = 0
    record_fn: int = 0
    # 假阳/假阴样本
    fp_samples: list = field(default_factory=list)
    fn_samples: list = field(default_factory=list)

    # conviction 差距 ≤1 的比例
    conviction_close_rate: float = 0.0
    conviction_diff: list = field(default_factory=list)

    # flags 零漏判率(只在金标 has_flag 的帖子上检查)
    flags_recall: float = 0.0
    flags_missed: list = field(default_factory=list)

    # 胜利巡游 0 漏判(硬性):金标为 0 记录的胜利巡游帖,LLM 也必须 0
    victory_lap_clean: bool = True
    victory_lap_violations: list = field(default_factory=list)

    # 通过/未通过
    passed: bool = False
    fail_reasons: list = field(default_factory=list)


# ---------------------------------------------------------------------------
# 评测
# ---------------------------------------------------------------------------


def _record_key(post_id: str, ticker: str, direction: str) -> tuple:
    return (post_id, ticker, direction)


def evaluate(llm_results: List[LLMPostResult]) -> EvalReport:
    """对照金标计算指标。"""
    rep = EvalReport()
    rep.n_posts = len(GOLD_V1)
    llm_by_post = {r.post_id: r for r in llm_results}

    post_tp = post_fp = post_fn = 0
    rec_tp = rec_fp = rec_fn = 0
    fp_samples = []
    fn_samples = []
    conv_close = 0
    conv_total = 0
    conv_diffs = []
    flags_missed = []

    for g in GOLD_V1:
        gp = g["post_id"]
        g_pred = g["has_prediction"]
        g_flags = set(g.get("flags", []))
        llm = llm_by_post.get(gp)
        if llm is None:
            # 缺 LLM 输出:算 1 个 post_fn
            post_fn += 1
            if g_pred:
                rec_fn += len(g["predictions"])
                for pred in g["predictions"]:
                    fn_samples.append({
                        "post_id": gp, "ticker": pred["ticker"],
                        "direction": pred["direction"], "reason": "no_llm_output",
                    })
            for f in g_flags:
                flags_missed.append({"post_id": gp, "flag": f, "reason": "no_llm_output"})
            continue
        l_pred = llm.has_prediction
        l_flags = set(llm.flags)

        # 帖子级
        if g_pred and l_pred:
            post_tp += 1
        elif not g_pred and not l_pred:
            pass  # 真负
        elif not g_pred and l_pred:
            post_fp += 1
            # 列出 LLM 在无预测帖上"硬抽"出的 ticker(假阳)
            for pred in llm.predictions:
                fp_samples.append({
                    "post_id": gp, "ticker": pred.ticker, "direction": pred.direction,
                    "reason": "no_prediction_in_gold_but_llm_made_one",
                })
        elif g_pred and not l_pred:
            post_fn += 1
            for pred in g["predictions"]:
                fn_samples.append({
                    "post_id": gp, "ticker": pred["ticker"],
                    "direction": pred["direction"], "reason": "llm_missed_has_prediction",
                })

        # 记录级
        g_keys = {_record_key(gp, p["ticker"], p["direction"]) for p in g["predictions"]}
        l_keys = {_record_key(gp, p.ticker, p.direction) for p in llm.predictions}
        for k in l_keys - g_keys:
            rec_fp += 1
            fp_samples.append({"post_id": gp, "ticker": k[1], "direction": k[2], "reason": "llm_pred_not_in_gold"})
        for k in g_keys - l_keys:
            rec_fn += 1
            fn_samples.append({"post_id": gp, "ticker": k[1], "direction": k[2], "reason": "gold_pred_missed_by_llm"})
        rec_tp += len(g_keys & l_keys)

        # conviction:仅在两者都有的记录上算
        g_by_key = {(p["ticker"], p["direction"]): p["conviction"] for p in g["predictions"]}
        for p in llm.predictions:
            k = (p.ticker, p.direction)
            if k in g_by_key:
                conv_total += 1
                diff = abs(p.conviction - g_by_key[k])
                conv_diffs.append({"post_id": gp, "ticker": p.ticker, "diff": diff})
                if diff <= 1:
                    conv_close += 1

        # flags 漏判
        for f in g_flags - l_flags:
            flags_missed.append({"post_id": gp, "flag": f})

        # 胜利巡游:金标 has_prediction=False 且 flags 含 victory_lap 时,LLM 必须 0 记录
        if not g_pred and "victory_lap" in g_flags:
            if llm.predictions:
                rep.victory_lap_clean = False
                for p in llm.predictions:
                    rep.victory_lap_violations.append({
                        "post_id": gp, "ticker": p.ticker,
                        "direction": p.direction, "reason": "victory_lap_should_be_0_records",
                    })

    # 汇总
    rep.n_predictions_gold = sum(len(g["predictions"]) for g in GOLD_V1)
    rep.n_predictions_llm = sum(len(r.predictions) for r in llm_results)
    rep.post_true_pos = post_tp
    rep.post_false_pos = post_fp
    rep.post_false_neg = post_fn
    rep.post_precision = post_tp / (post_tp + post_fp) if (post_tp + post_fp) else 1.0
    rep.post_recall = post_tp / (post_tp + post_fn) if (post_tp + post_fn) else 0.0
    rep.record_tp = rec_tp
    rep.record_fp = rec_fp
    rep.record_fn = rec_fn
    rep.record_precision = rec_tp / (rec_tp + rec_fp) if (rec_tp + rec_fp) else 0.0
    rep.record_recall = rec_tp / (rec_tp + rec_fn) if (rec_tp + rec_fn) else 0.0
    rep.record_f1 = (2 * rep.record_precision * rep.record_recall /
                     (rep.record_precision + rep.record_recall)
                     if (rep.record_precision + rep.record_recall) else 0.0)
    rep.conviction_close_rate = conv_close / conv_total if conv_total else 1.0
    rep.conviction_diff = conv_diffs
    # flags recall: 仅算"金标有 flag 的帖子"
    g_flag_posts = sum(1 for g in GOLD_V1 if g.get("flags"))
    flags_recalled = g_flag_posts - len(set((f["post_id"], f["flag"]) for f in flags_missed))
    rep.flags_recall = flags_recalled / g_flag_posts if g_flag_posts else 1.0
    rep.flags_missed = flags_missed
    rep.fp_samples = fp_samples
    rep.fn_samples = fn_samples

    # 通过线(spec 第 6 节)
    rep.passed, rep.fail_reasons = _check_pass(rep)
    return rep


def _check_pass(rep: EvalReport) -> tuple:
    """spec 第 6 节验收。"""
    fail = []
    if rep.post_precision < 0.95:
        fail.append(f"post_precision={rep.post_precision:.3f} < 0.95 (假阳是大敌)")
    if rep.post_recall < 0.85:
        fail.append(f"post_recall={rep.post_recall:.3f} < 0.85")
    if rep.record_f1 < 0.85:
        fail.append(f"record_f1={rep.record_f1:.3f} < 0.85")
    if rep.conviction_close_rate < 0.80:
        fail.append(f"conviction_close_rate={rep.conviction_close_rate:.3f} < 0.80")
    if rep.flags_recall < 1.0:
        fail.append(f"flags_recall={rep.flags_recall:.3f} < 1.0 (零漏判)")
    if not rep.victory_lap_clean:
        fail.append(f"victory_lap_violations={rep.victory_lap_violations[:3]}... (硬性)")
    return (len(fail) == 0, fail)


# ---------------------------------------------------------------------------
# 报告渲染
# ---------------------------------------------------------------------------


def render_report(rep: EvalReport) -> str:
    lines = []
    lines.append("=" * 80)
    lines.append("金标评测报告 v1(20 条)")
    lines.append("=" * 80)
    lines.append(f"帖子数: {rep.n_posts}")
    lines.append(f"金标预测总数: {rep.n_predictions_gold}, LLM 抽出: {rep.n_predictions_llm}")
    lines.append("")
    lines.append("## 帖子级 has_prediction 判定")
    lines.append(f"  precision: {rep.post_precision:.3f}  (要求 ≥ 0.95)")
    lines.append(f"  recall   : {rep.post_recall:.3f}  (要求 ≥ 0.85)")
    lines.append(f"  TP/FP/FN : {rep.post_true_pos} / {rep.post_false_pos} / {rep.post_false_neg}")
    lines.append("")
    lines.append("## 记录级(post_id + ticker + direction)")
    lines.append(f"  precision: {rep.record_precision:.3f}")
    lines.append(f"  recall   : {rep.record_recall:.3f}")
    lines.append(f"  F1       : {rep.record_f1:.3f}  (要求 ≥ 0.85)")
    lines.append(f"  TP/FP/FN : {rep.record_tp} / {rep.record_fp} / {rep.record_fn}")
    lines.append("")
    lines.append("## conviction(差距 ≤1 的比例)")
    lines.append(f"  close_rate: {rep.conviction_close_rate:.3f}  (要求 ≥ 0.80)")
    if rep.conviction_diff:
        big_diffs = [d for d in rep.conviction_diff if d["diff"] > 1]
        if big_diffs:
            lines.append(f"  大差距(>1)样本: {len(big_diffs)}")
            for d in big_diffs[:5]:
                lines.append(f"    {d['post_id'][-6:]}  {d['ticker']:<10}  diff={d['diff']}")
    lines.append("")
    lines.append("## flags 召回")
    lines.append(f"  recall: {rep.flags_recall:.3f}  (要求 = 1.0,零漏判)")
    if rep.flags_missed:
        lines.append(f"  漏判: {rep.flags_missed}")
    lines.append("")
    lines.append("## 胜利巡游 0 漏判(硬性)")
    lines.append(f"  clean: {rep.victory_lap_clean}")
    if not rep.victory_lap_clean:
        lines.append(f"  violations: {rep.victory_lap_violations}")
    lines.append("")
    lines.append("## 假阳样本(LLM 多抽 / 多标的)")
    if not rep.fp_samples:
        lines.append("  (无)")
    else:
        for s in rep.fp_samples[:10]:
            lines.append(f"  {s['post_id'][-6:]}  {s.get('ticker', ''):<12}  {s.get('direction', ''):<6}  {s.get('reason', '')}")
        if len(rep.fp_samples) > 10:
            lines.append(f"  ... 共 {len(rep.fp_samples)} 个")
    lines.append("")
    lines.append("## 假阴样本(LLM 漏抽)")
    if not rep.fn_samples:
        lines.append("  (无)")
    else:
        for s in rep.fn_samples[:10]:
            lines.append(f"  {s['post_id'][-6:]}  {s.get('ticker', ''):<12}  {s.get('direction', ''):<6}  {s.get('reason', '')}")
        if len(rep.fn_samples) > 10:
            lines.append(f"  ... 共 {len(rep.fn_samples)} 个")
    lines.append("")
    lines.append("=" * 80)
    if rep.passed:
        lines.append("✅ 全部通过")
    else:
        lines.append("❌ 未通过:")
        for f in rep.fail_reasons:
            lines.append(f"  - {f}")
    lines.append("=" * 80)
    return "\n".join(lines)
