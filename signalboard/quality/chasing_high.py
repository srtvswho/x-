"""追高自动检验 — Serenity 教训:

5/5 核心票 tier_A 首次论证时,票已经涨了 23%~256% (相对 60 天低点)。
她是追高者,不是预言家 — 但她选的票还在中早期。

自动检验规则:
1. 对每个核心标的 (tier_A top N),找首次 tier_A 论证的 pub
2. 计算 entry 价相对 pre_60d_low 的涨幅
3. 标记: <30% = "起涨早期", 30%~80% = "涨势中段", >80% = "明显追高"
4. 输出 "首次论证时已涨" 占比

使用:
    from signalboard.quality.chasing_high import audit_chasing_high
    report = audit_chasing_high(conn, prediction_ids, top_n=5)
"""
from __future__ import annotations
import json
import os
import sqlite3
from collections import defaultdict
from dataclasses import dataclass

PRICE_CACHE_DIR = "/workspace/data/price_cache"


def load_bars(ticker: str) -> list[dict]:
    """从 price_cache 读 bars。"""
    for path in [
        f"{PRICE_CACHE_DIR}/{ticker}_FULL_HISTORY.json",
        f"{PRICE_CACHE_DIR}/{ticker}.json",
    ]:
        if os.path.exists(path):
            with open(path) as f:
                return json.load(f)
    # SIVE 特殊:SIVE.US mirror 是 SIVEF
    if ticker == "SIVE":
        for path in [
            f"{PRICE_CACHE_DIR}/SIVEF_FULL_HISTORY.json",
            f"{PRICE_CACHE_DIR}/SIVEF.json",
        ]:
            if os.path.exists(path):
                with open(path) as f:
                    return json.load(f)
    return []


def find_pre_low(bars: list[dict], entry_date: str, window: int = 60) -> tuple[float, str] | None:
    """找 entry_date 前 window 天的最低价。"""
    if not bars:
        return None
    edate_idx = None
    for i, b in enumerate(bars):
        if b.get("date", "") >= entry_date:
            edate_idx = i
            break
    if edate_idx is None:
        return None
    pre = bars[max(0, edate_idx - window): edate_idx + 1]
    if not pre:
        return None
    low = min(b.get("l", b.get("c", 0)) for b in pre)
    low_date = next((b["date"] for b in pre if b.get("l", b.get("c", 0)) == low), "")
    return low, low_date


def chasing_level(pct_above_low: float) -> str:
    """根据 entry 相对 pre_low 的涨幅分档。

    Returns: "early" / "mid" / "chasing" / "deep_chasing"
    """
    if pct_above_low < 30:
        return "early"          # 起涨早期 (相对 pre_low +0~30%)
    elif pct_above_low < 80:
        return "mid"            # 涨势中段 (+30%~80%)
    elif pct_above_low < 200:
        return "chasing"        # 明显追高 (+80%~200%)
    else:
        return "deep_chasing"   # 深度追高 (>+200%)


@dataclass
class ChasingHighRecord:
    ticker: str
    first_tier_a_pub: str
    entry_date: str
    entry_price: float
    pre_60d_low: float
    pre_60d_low_date: str
    pct_above_pre_low: float      # entry / pre_low - 1, 正数 = 追高
    chasing_level: str            # early / mid / chasing / deep_chasing
    current_price: float | None
    pct_entry_to_now: float | None  # 从 entry 到现在


@dataclass
class ChasingHighReport:
    records: list[ChasingHighRecord]
    n_chasing: int       # >80% (含 chasing + deep_chasing)
    n_mid: int           # 30%~80%
    n_early: int         # <30%
    warning_level: str   # GREEN / YELLOW / RED


def audit_chasing_high(conn: sqlite3.Connection, prediction_ids: list[int], top_n: int = 5) -> ChasingHighReport:
    """对一组 prediction 做追高体检。

    Args:
        prediction_ids: 用于选 top_n ticker (按频次)
        top_n: 取前 top_n 个高频 ticker 做追高检验
    """
    if not prediction_ids:
        return ChasingHighReport([], 0, 0, 0, "GREEN")

    c = conn.cursor()
    placeholders = ",".join(["?"] * len(prediction_ids))
    sql = f"""
    SELECT p.prediction_id, p.ticker, p.published_at,
           v.entry_date_actual, v.entry_price
    FROM predictions p
    JOIN verifications v ON p.prediction_id=v.prediction_id
    WHERE p.prediction_id IN ({placeholders})
    """
    rows = c.execute(sql, list(prediction_ids)).fetchall()

    # ticker 频次
    ticker_count = defaultdict(int)
    for r in rows:
        ticker_count[r[1]] += 1
    top_tickers = [t for t, _ in sorted(ticker_count.items(), key=lambda x: -x[1])[:top_n]]

    records = []
    for ticker in top_tickers:
        # 找该 ticker 最早的一条 tier_A 论证
        sql2 = f"""
        SELECT p.published_at, v.entry_date_actual, v.entry_price
        FROM predictions p
        JOIN verifications v ON p.prediction_id=v.prediction_id
        WHERE p.ticker=? AND p.prediction_id IN ({placeholders})
        ORDER BY p.published_at ASC LIMIT 1
        """
        r = c.execute(sql2, [ticker] + list(prediction_ids)).fetchone()
        if not r:
            continue
        pub, edate, eprice = r
        if not isinstance(eprice, (int, float)) or eprice <= 0:
            continue
        if not edate:
            continue

        bars = load_bars(ticker)
        pre_info = find_pre_low(bars, edate, window=60)
        if not pre_info:
            continue
        pre_low, pre_low_date = pre_info
        if pre_low <= 0:
            continue

        pct_above = (eprice - pre_low) / pre_low * 100
        level = chasing_level(pct_above)

        cur = bars[-1] if bars else None
        cur_price = cur.get("c") if cur else None
        pct_to_now = (cur_price - eprice) / eprice * 100 if cur_price else None

        records.append(ChasingHighRecord(
            ticker=ticker,
            first_tier_a_pub=pub[:10] if pub else "",
            entry_date=edate,
            entry_price=eprice,
            pre_60d_low=pre_low,
            pre_60d_low_date=pre_low_date,
            pct_above_pre_low=pct_above,
            chasing_level=level,
            current_price=cur_price,
            pct_entry_to_now=pct_to_now,
        ))

    n_chasing = sum(1 for r in records if r.chasing_level in ("chasing", "deep_chasing"))
    n_mid = sum(1 for r in records if r.chasing_level == "mid")
    n_early = sum(1 for r in records if r.chasing_level == "early")

    warning = "GREEN"
    if n_chasing >= 3:
        warning = "RED"
    elif n_chasing >= 1 or n_mid >= 3:
        warning = "YELLOW"

    return ChasingHighReport(
        records=records,
        n_chasing=n_chasing,
        n_mid=n_mid,
        n_early=n_early,
        warning_level=warning,
    )