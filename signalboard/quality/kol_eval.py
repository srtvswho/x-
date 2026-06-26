"""KOL 评估标准流程 — 主入口

把 6 个模块组合成一条 pipeline:
输入: KOL handle + DB path + tier_A subset
输出: 标准记分牌 (tier 分层 + outlier 体检 + 追高标记 + 置信度分级)

使用:
    from signalboard.quality.kol_eval import evaluate_kol
    report = evaluate_kol(handle='aleabitoreddit', db_path='/workspace/data/signalboard_full.db')
    print(report.to_markdown())
"""
from __future__ import annotations
import sqlite3
import statistics
import math
from dataclasses import dataclass, field
from datetime import datetime

from .tier import classify_all, tier_summary, filter_by_tier
from .outlier_audit import audit_outliers, wilson, hit_rate_excess_median
from .chasing_high import audit_chasing_high, ChasingHighReport


@dataclass
class HorizonStats:
    horizon: str
    n_resolved: int
    n_hit: int
    hit_rate: float | None
    wilson_low: float | None
    median_excess: float | None
    avg_excess: float | None


@dataclass
class TierStats:
    tier: str
    n_total: int
    n_resolved: dict[str, HorizonStats] = field(default_factory=dict)


@dataclass
class KOLReport:
    handle: str
    generated_at: str
    db_path: str
    tier_distribution: dict[str, int]
    tier_stats: dict[str, TierStats]
    outlier_audits: dict[str, dict]   # tier_A per-horizon outlier 报告
    chasing_high: ChasingHighReport | None
    confidence_grade: str             # A+/A/B/C/D
    confidence_note: str
    summary: str

    def to_markdown(self) -> str:
        md = []
        md.append(f"# KOL 评估报告 — @{self.handle}")
        md.append("")
        md.append(f"**生成时间**: {self.generated_at}")
        md.append(f"**数据库**: {self.db_path}")
        md.append(f"**置信度等级**: **{self.confidence_grade}** — {self.confidence_note}")
        md.append("")
        md.append("## 1. Tier 分层")
        md.append("")
        md.append("| Tier | n | 占比 |")
        md.append("|---|---|---|")
        total = sum(self.tier_distribution.values())
        for t in ("A", "B", "C"):
            n = self.tier_distribution.get(t, 0)
            pct = n/total*100 if total else 0
            label = {"A": "tier_A 核心论证", "B": "tier_B 清单扫货", "C": "tier_C 顺带提及"}.get(t, t)
            md.append(f"| {label} | {n} | {pct:.1f}% |")
        md.append(f"| **总** | {total} | 100% |")
        md.append("")

        md.append("## 2. Tier × Horizon 记分牌")
        md.append("")
        for tier in ("A", "B", "C"):
            ts = self.tier_stats.get(tier)
            if not ts or not ts.n_resolved:
                continue
            label = {"A": "tier_A 核心论证", "B": "tier_B 清单扫货", "C": "tier_C 顺带提及"}.get(tier)
            md.append(f"### {label} (n_total={ts.n_total})")
            md.append("")
            md.append("| horizon | n_resolved | hit_rate | wilson_low | median_excess | avg_excess |")
            md.append("|---|---|---|---|---|---|")
            for h in ("1w", "1m", "3m", "6m"):
                s = ts.n_resolved.get(h)
                if not s:
                    continue
                hr = f"{s.hit_rate*100:.1f}%" if s.hit_rate is not None else "N/A"
                wl = f"{s.wilson_low*100:.1f}%" if s.wilson_low is not None else "N/A"
                me = f"{s.median_excess:+.2f}%" if s.median_excess is not None else "N/A"
                ae = f"{s.avg_excess:+.2f}%" if s.avg_excess is not None else "N/A"
                md.append(f"| {h} | {s.n_resolved} | {hr} | {wl} | {me} | {ae} |")
            md.append("")

        md.append("## 3. tier_A outlier 自动体检")
        md.append("")
        for h, audit in self.outlier_audits.items():
            md.append(f"### {h} horizon")
            md.append("")
            md.append(f"- 警告等级: **{audit['warning_level']}** — {audit['warning_reason']}")
            md.append(f"- n: {audit['n']}")
            md.append(f"- top1 集中度: {audit['top1_concentration']*100:.1f}% ({audit['top_tickers'][0][0] if audit['top_tickers'] else 'N/A'})")
            md.append(f"- top5 集中度: {audit['top5_concentration']*100:.1f}%")
            md.append(f"- hit_rate (with outlier): {audit['hit_rate_with_outlier']*100:.1f}%" if audit['hit_rate_with_outlier'] is not None else "- hit_rate: N/A")
            md.append(f"- hit_rate (去 top1): {audit['hit_rate_without_top1']*100:.1f}%" if audit['hit_rate_without_top1'] is not None else "- 去 top1 hit_rate: N/A")
            md.append(f"- hit_rate (去 top2): {audit['hit_rate_without_top2']*100:.1f}%" if audit['hit_rate_without_top2'] is not None else "- 去 top2 hit_rate: N/A")
            md.append(f"- hit_rate (去 top3): {audit['hit_rate_without_top3']*100:.1f}%" if audit['hit_rate_without_top3'] is not None else "- 去 top3 hit_rate: N/A")
            if audit['outlier_tickers']:
                md.append(f"- outlier ticker (median 3x+): {', '.join(audit['outlier_tickers'])}")
            md.append("")

        md.append("## 4. tier_A 追高检验")
        md.append("")
        if self.chasing_high and self.chasing_high.records:
            md.append(f"**警告等级**: {self.chasing_high.warning_level} | 追高: {self.chasing_high.n_chasing} / 中段: {self.chasing_high.n_mid} / 早期: {self.chasing_high.n_early}")
            md.append("")
            md.append("| ticker | 首次论证 | entry | pre_60d_low | 相对 low | 追高档位 | 票后涨 |")
            md.append("|---|---|---|---|---|---|---|")
            for r in self.chasing_high.records:
                ptn = f"{r.pct_entry_to_now:+.1f}%" if r.pct_entry_to_now is not None else "N/A"
                md.append(f"| {r.ticker} | {r.first_tier_a_pub} | ${r.entry_price:.4f} | ${r.pre_60d_low:.4f} ({r.pre_60d_low_date}) | **+{r.pct_above_pre_low:.1f}%** | {r.chasing_level} | {ptn} |")
            md.append("")

        md.append("## 5. 总评")
        md.append("")
        md.append(self.summary)
        return "\n".join(md)


def _horizon_stats(rows, horizon: str) -> HorizonStats:
    """算一组 row 在某 horizon 的 hit_rate/wilson/median/avg。

    rows 列顺序: 0=pid, 1=ticker, 2=1w_status, 3=1w_excess, 4=1m_status, 5=1m_excess,
                 6=3m_status, 7=3m_excess, 8=6m_status, 9=6m_excess
    """
    idx_map = {
        "1w": (2, 3),
        "1m": (4, 5),
        "3m": (6, 7),
        "6m": (8, 9),
    }
    st_idx, exc_idx = idx_map[horizon]
    n_res, n_h = 0, 0
    exc_vals = []
    for r in rows:
        s = r[st_idx]
        e = r[exc_idx]
        if s == "resolved_hit":
            n_res += 1
            n_h += 1
            if isinstance(e, (int, float)): exc_vals.append(e)
        elif s == "resolved_miss":
            n_res += 1
            if isinstance(e, (int, float)): exc_vals.append(e)
    hr = n_h/n_res if n_res else None
    wl = wilson(n_h, n_res)
    med = statistics.median(exc_vals)*100 if exc_vals else None
    avg = statistics.mean(exc_vals)*100 if exc_vals else None
    return HorizonStats(
        horizon=horizon,
        n_resolved=n_res,
        n_hit=n_h,
        hit_rate=hr,
        wilson_low=wl,
        median_excess=med,
        avg_excess=avg,
    )


def grade_confidence(tier_a_stats: TierStats, outlier_audits: dict, chasing: ChasingHighReport) -> tuple[str, str]:
    """根据体检结果打分: A+ / A / B / C / D。"""
    # tier_A 3m 显著 (hit ≥ 60%, wilson ≥ 55%, median ≥ +10%)
    h_3m = tier_a_stats.n_resolved.get("3m")
    h_1m = tier_a_stats.n_resolved.get("1m")
    h_6m = tier_a_stats.n_resolved.get("6m")

    score = 0
    notes = []

    if h_3m and h_3m.hit_rate and h_3m.hit_rate >= 0.6:
        score += 3
        notes.append(f"tier_A 3m hit {h_3m.hit_rate*100:.1f}% ≥ 60% (+3)")
    if h_3m and h_3m.median_excess and h_3m.median_excess >= 10:
        score += 2
        notes.append(f"tier_A 3m median excess {h_3m.median_excess:+.1f}% ≥ 10 (+2)")

    if h_6m and h_6m.hit_rate and h_6m.hit_rate >= 0.6:
        score += 2
        notes.append(f"tier_A 6m hit {h_6m.hit_rate*100:.1f}% ≥ 60% (+2)")

    # 扣分项
    if outlier_audits.get("3m", {}).get("warning_level") == "RED":
        score -= 2
        notes.append(f"tier_A 3m outlier 警告 RED (-2)")
    if outlier_audits.get("1m", {}).get("warning_level") == "RED":
        score -= 1
        notes.append(f"tier_A 1m outlier 警告 RED (-1)")

    if chasing and chasing.warning_level == "RED":
        score -= 1
        notes.append(f"追高警告 RED (-1)")

    grade_map = [(7, "A+"), (5, "A"), (3, "B"), (1, "C"), (-99, "D")]
    for threshold, g in grade_map:
        if score >= threshold:
            return g, "; ".join(notes)

    return "D", "; ".join(notes)


def evaluate_kol(handle: str, db_path: str, output_path: str | None = None) -> KOLReport:
    """KOL 评估主入口。"""
    conn = sqlite3.connect(db_path, timeout=30)
    c = conn.cursor()

    # 1. tier 分层
    tiers = classify_all(conn)
    tier_dist = tier_summary(tiers)

    tier_a_pids = filter_by_tier(list(tiers.keys()), tiers, "A")
    tier_b_pids = filter_by_tier(list(tiers.keys()), tiers, "B")
    tier_c_pids = filter_by_tier(list(tiers.keys()), tiers, "C")

    # 2. 拉 verifications 数据
    def fetch_verif(pids):
        if not pids:
            return []
        placeholders = ",".join(["?"] * len(pids))
        sql = f"""
        SELECT p.prediction_id, p.ticker,
               v.h_1w_status, v.h_1w_excess_return,
               v.h_1m_status, v.h_1m_excess_return,
               v.h_3m_status, v.h_3m_excess_return,
               v.h_6m_status, v.h_6m_excess_return
        FROM predictions p
        JOIN verifications v ON p.prediction_id=v.prediction_id
        WHERE p.prediction_id IN ({placeholders})
        """
        return c.execute(sql, list(pids)).fetchall()

    rows_a = fetch_verif(tier_a_pids)
    rows_b = fetch_verif(tier_b_pids)
    rows_c = fetch_verif(tier_c_pids)

    # 3. tier × horizon 记分牌
    tier_stats = {}
    for tier, rows in (("A", rows_a), ("B", rows_b), ("C", rows_c)):
        ts = TierStats(tier=tier, n_total=len(rows))
        for h in ("1w", "1m", "3m", "6m"):
            ts.n_resolved[h] = _horizon_stats(rows, h)
        tier_stats[tier] = ts

    # 4. outlier 体检 (tier_A per-horizon)
    outlier_audits = {}
    for h in ("1w", "1m", "3m", "6m"):
        report = audit_outliers(conn, tier_a_pids, horizon=h)
        outlier_audits[h] = {
            "warning_level": report.warning_level,
            "warning_reason": report.warning_reason,
            "n": report.n,
            "top_tickers": report.top_tickers,
            "top1_concentration": report.top1_concentration,
            "top5_concentration": report.top5_concentration,
            "outlier_tickers": report.outlier_tickers,
            "hit_rate_with_outlier": report.hit_rate_with_outlier,
            "hit_rate_without_top1": report.hit_rate_without_top1,
            "hit_rate_without_top2": report.hit_rate_without_top2,
            "hit_rate_without_top3": report.hit_rate_without_top3,
        }

    # 5. 追高检验
    chasing = audit_chasing_high(conn, tier_a_pids, top_n=5)

    # 6. 置信度分级
    ts_a = tier_stats.get("A", TierStats("A", 0))
    grade, note = grade_confidence(ts_a, outlier_audits, chasing)

    # 7. 总评 summary
    h_3m = ts_a.n_resolved.get("3m")
    summary_lines = []
    if h_3m and h_3m.hit_rate and h_3m.median_excess is not None:
        summary_lines.append(f"tier_A 3m hit {h_3m.hit_rate*100:.1f}% / median excess {h_3m.median_excess:+.2f}%")
    if outlier_audits.get("3m", {}).get("warning_level") == "RED":
        summary_lines.append(f"⚠ 3m outlier 警告 RED — {outlier_audits['3m']['warning_reason']}")
    if chasing:
        summary_lines.append(f"追高检验: {chasing.n_chasing}/{chasing.n_mid}/{chasing.n_early} = 追高/中段/早期")

    report = KOLReport(
        handle=handle,
        generated_at=datetime.utcnow().isoformat() + "Z",
        db_path=db_path,
        tier_distribution=tier_dist,
        tier_stats=tier_stats,
        outlier_audits=outlier_audits,
        chasing_high=chasing,
        confidence_grade=grade,
        confidence_note=note,
        summary=" / ".join(summary_lines) if summary_lines else "N/A",
    )

    if output_path:
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(report.to_markdown())

    conn.close()
    return report