"""outlier 与集中度自动体检 — Serenity 教训:

SIVE 占 tier_A 26%,NBIS 占 16%,两个加起来 42%。
如果不主动拆开看,一个 SIVE 12 倍 outlier 就能撑起整个"85% hit"的假象。

自动体检规则:
1. 集中度 top-5 占比 (单标的占整体的比例)
2. 去掉贡献最大的 1/2/3 个 ticker 后 hit rate 变化
3. outlier 检测 (中位 3 倍以上的 ticker)
4. 自动标 warning_level: GREEN / YELLOW / RED
"""
from __future__ import annotations
import sqlite3
import math
import statistics
from collections import Counter
from dataclasses import dataclass

# WARNING 阈值
CONCENTRATION_RED = 0.4     # top1 占比 >40% → RED
CONCENTRATION_YELLOW = 0.25  # top1 占比 >25% → YELLOW
TOP5_RED = 0.7              # top5 占比 >70% → RED
TOP5_YELLOW = 0.5           # top5 占比 >50% → YELLOW


@dataclass
class OutlierReport:
    n: int
    top_tickers: list[tuple[str, int]]     # [(ticker, n)]
    top1_concentration: float              # top1 / n
    top5_concentration: float
    outlier_tickers: list[str]              # median 3x 以上的
    hit_rate_with_outlier: float | None
    hit_rate_without_top1: float | None
    hit_rate_without_top2: float | None
    hit_rate_without_top3: float | None
    warning_level: str                      # GREEN / YELLOW / RED
    warning_reason: str


def wilson(h, n, z=1.96):
    if n == 0: return None
    p = h/n
    d = 1 + z*z/n
    return ((p + z*z/(2*n))/d - z*math.sqrt(p*(1-p)/n + z*z/(4*n*n))/d)


def hit_rate_excess_median(rows: list, st_idx: int, exc_idx: int) -> tuple[int, int, float | None]:
    """算一组 row 的 hit_rate (resolved_hit / n_resolved) + median_excess。"""
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
    med = statistics.median(exc_vals)*100 if exc_vals else None
    return n_h, n_res, med


def audit_outliers(conn: sqlite3.Connection, prediction_ids: list[int], horizon: str = "1m") -> OutlierReport:
    """对一组 prediction 做 outlier 体检。

    Args:
        conn: sqlite connection
        prediction_ids: 要体检的 prediction_id 列表
        horizon: "1w" / "1m" / "3m" / "6m"

    Returns:
        OutlierReport
    """
    if not prediction_ids:
        return OutlierReport(0, [], 0, 0, [], None, None, None, None, "GREEN", "empty")

    horizon_col_map = {
        "1w": ("h_1w_status", "h_1w_excess_return"),
        "1m": ("h_1m_status", "h_1m_excess_return"),
        "3m": ("h_3m_status", "h_3m_excess_return"),
        "6m": ("h_6m_status", "h_6m_excess_return"),
    }
    st_col, exc_col = horizon_col_map[horizon]
    st_idx_map = {"1w": 1, "1m": 3, "3m": 5, "6m": 7}
    exc_idx_map = {"1w": 2, "1m": 4, "3m": 6, "6m": 8}
    st_idx = st_idx_map[horizon]
    exc_idx = exc_idx_map[horizon]

    placeholders = ",".join(["?"] * len(prediction_ids))
    sql = f"""
    SELECT p.prediction_id, p.ticker,
           v.{st_col}, v.{exc_col}
    FROM predictions p
    JOIN verifications v ON p.prediction_id=v.prediction_id
    WHERE p.prediction_id IN ({placeholders})
    """
    rows = c.execute(sql, list(prediction_ids)) if False else conn.execute(sql, list(prediction_ids)).fetchall()
    n = len(rows)

    # ticker 分布
    ticker_count = Counter(r[1] for r in rows)
    top_tickers = ticker_count.most_common(5)
    top1 = top_tickers[0] if top_tickers else (None, 0)
    top1_concentration = top1[1] / n if n else 0
    top5_concentration = sum(t[1] for t in top_tickers) / n if n else 0

    # outlier 检测: median excess 3x
    per_ticker_excess = {}
    for tk in ticker_count:
        tk_rows = [r for r in rows if r[1] == tk]
        _, _, med = hit_rate_excess_median(tk_rows, st_idx=2, exc_idx=3)
        if med is not None:
            per_ticker_excess[tk] = med

    all_med = [m for m in per_ticker_excess.values() if m is not None]
    overall_med = statistics.median(all_med) if all_med else 0
    outliers = [tk for tk, m in per_ticker_excess.items() if m and overall_med and m > 3 * abs(overall_med) and m > 30]

    # hit rate with / without top1/2/3
    n_h_full, n_res_full, _ = hit_rate_excess_median(rows, st_idx=2, exc_idx=3)
    hr_full = n_h_full/n_res_full if n_res_full else None

    rows_no1 = [r for r in rows if r[1] != top_tickers[0][0]] if top_tickers else rows
    n_h_no1, n_res_no1, _ = hit_rate_excess_median(rows_no1, st_idx=2, exc_idx=3)
    hr_no1 = n_h_no1/n_res_no1 if n_res_no1 else None

    rows_no2 = [r for r in rows if r[1] not in {t[0] for t in top_tickers[:2]}] if len(top_tickers) >= 2 else rows_no1
    n_h_no2, n_res_no2, _ = hit_rate_excess_median(rows_no2, st_idx=2, exc_idx=3)
    hr_no2 = n_h_no2/n_res_no2 if n_res_no2 else None

    rows_no3 = [r for r in rows if r[1] not in {t[0] for t in top_tickers[:3]}] if len(top_tickers) >= 3 else rows_no2
    n_h_no3, n_res_no3, _ = hit_rate_excess_median(rows_no3, st_idx=2, exc_idx=3)
    hr_no3 = n_h_no3/n_res_no3 if n_res_no3 else None

    # warning level
    warning = "GREEN"
    reasons = []
    if top1_concentration > CONCENTRATION_RED:
        warning = "RED"
        reasons.append(f"top1 ({top1[0]}) 占 {top1_concentration*100:.1f}% > {CONCENTRATION_RED*100}%")
    elif top1_concentration > CONCENTRATION_YELLOW:
        warning = max(warning, "YELLOW", key=["GREEN", "YELLOW", "RED"].index)
        reasons.append(f"top1 ({top1[0]}) 占 {top1_concentration*100:.1f}% > {CONCENTRATION_YELLOW*100}%")

    if top5_concentration > TOP5_RED:
        warning = "RED"
        reasons.append(f"top5 占 {top5_concentration*100:.1f}% > {TOP5_RED*100}%")
    elif top5_concentration > TOP5_YELLOW:
        warning = max(warning, "YELLOW", key=["GREEN", "YELLOW", "RED"].index)
        reasons.append(f"top5 占 {top5_concentration*100:.1f}% > {TOP5_YELLOW*100}%")

    if outliers:
        warning = "RED"
        reasons.append(f"outlier ticker: {','.join(outliers[:3])} (median excess 3x overall)")

    # hit rate 塌方检测 (去掉 top1 后 hit 跌 >15pp)
    if hr_full and hr_no1 and (hr_full - hr_no1) > 0.15:
        warning = "RED"
        reasons.append(f"去掉 {top_tickers[0][0]} 后 hit_rate 跌 {hr_full-hr_no1:.1%}")

    return OutlierReport(
        n=n,
        top_tickers=top_tickers,
        top1_concentration=top1_concentration,
        top5_concentration=top5_concentration,
        outlier_tickers=outliers,
        hit_rate_with_outlier=hr_full,
        hit_rate_without_top1=hr_no1,
        hit_rate_without_top2=hr_no2,
        hit_rate_without_top3=hr_no3,
        warning_level=warning,
        warning_reason="; ".join(reasons) if reasons else "OK",
    )