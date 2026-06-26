"""ticker 解析增强 — Serenity 教训:SIVE raw 4-letter ≠ 美股

管线下沉的 4 个规则:
1. 别名表沉淀 (300+ 条资产) — LLM 不参与解析,纯 alias 表
2. 国别 vs 挂牌地识别 — SIVE 在 Nasdaq 但主体在瑞典,要看 primary listing
3. 美国 OTC 影子代码自动标记 — 大写 4-5 字母 + 非 NYSE/Nasdaq 主板 → 疑似非美股
4. 解析后入 human_review_queue — 自动标记 + 人工确认,而不是默认放过

使用:
    from signalboard.quality.ticker_resolver import resolve_and_flag
    resolved, flag = resolve_and_flag(raw_mention, conn)
"""
from __future__ import annotations
import re
import sqlite3

# 美国 OTC 影子代码特征 — 4-5 字母全大写 + 不在主要交易所
OTC_PATTERN = re.compile(r"^[A-Z]{4,5}$")

# 已知的 US 主板交易所 tickers 模式 — 1-5 字母
US_MAJOR_PATTERN = re.compile(r"^[A-Z]{1,5}$")


def is_likely_otc(ticker: str, market: str | None) -> bool:
    """判断是否疑似美国 OTC 影子代码。

    Returns: True if 4-5 letter + market 不明确 OR 标了 OTC/OTC Markets。
    """
    if not ticker:
        return False
    if not OTC_PATTERN.match(ticker):
        return False
    if market and market.upper() in ("OTC", "OTCMKTS", "PINK", "OTC PINK", "OTCQB", "OTCQX"):
        return True
    # 4 字母全大写 + 未明确 NYSE/Nasdaq 主板 → 高度疑似 OTC 影子
    return len(ticker) == 4 and ticker.isupper()


def load_alias_index(conn: sqlite3.Connection) -> dict:
    """加载 aliases 表 → {alias_raw: [(ticker, market, ...)]}。"""
    c = conn.cursor()
    rows = c.execute("""
        SELECT alias_raw, ticker, market, asset_class, confidence
        FROM aliases
    """).fetchall()
    idx = {}
    for alias, ticker, market, asset_class, conf in rows:
        idx.setdefault(alias, []).append({
            "ticker": ticker,
            "market": market,
            "asset_class": asset_class,
            "confidence": conf,
        })
    return idx


def resolve_and_flag(raw_mention: str, conn: sqlite3.Connection) -> dict:
    """解析单个别名 + 自动 flag 风险。

    Returns:
        {
            "raw_mention": str,
            "resolved_ticker": str | None,
            "market": str | None,
            "flag_otc_suspect": bool,
            "flag_uk_or_eu_listing": bool,
            "needs_human_review": bool,
            "review_reason": str | None,
        }
    """
    alias_idx = load_alias_index(conn)
    candidates = alias_idx.get(raw_mention, [])
    # 也试 lowercase
    if not candidates:
        candidates = alias_idx.get(raw_mention.lower(), [])

    flag_otc = False
    flag_foreign = False
    ticker = None
    market = None
    reason = None

    if candidates:
        # 取 confidence 最高的
        best = max(candidates, key=lambda x: x.get("confidence", 0))
        ticker = best["ticker"]
        market = best["market"]
    else:
        # 尝试按原始写法当 ticker
        ticker = raw_mention.upper().strip()
        market = None

    # OTC 检测
    if market and is_likely_otc(ticker, market):
        flag_otc = True
        reason = f"OTC 影子代码嫌疑: {ticker} market={market}"

    # 4 字母大写无市场信息 → 高度疑似 US OTC mirror
    if not market and len(ticker) == 4 and ticker.isupper():
        flag_otc = True
        flag_foreign = True
        reason = f"4 字母全大写无市场信息,疑似非美股主体 (例 SIVE 瑞典 / Sivers STO)"

    # 已知国别/挂牌地分离的标的 — 后续可扩
    FOREIGN_LISTED_ON_US_EXCHANGE = {
        "SIVE": {"primary_listing": "Stockholm (SIVE.ST)", "us_mirror": "SIVEF OTC"},
        "SIVEF": {"primary_listing": "OTC US mirror of SIVE.ST", "us_mirror": "SIVEF"},
    }
    if ticker in FOREIGN_LISTED_ON_US_EXCHANGE:
        flag_foreign = True
        info = FOREIGN_LISTED_ON_US_EXCHANGE[ticker]
        reason = f"主体非美国:{info.get('primary_listing')},US 挂牌为 {info.get('us_mirror')}"

    needs_review = bool(reason)
    return {
        "raw_mention": raw_mention,
        "resolved_ticker": ticker,
        "market": market,
        "flag_otc_suspect": flag_otc,
        "flag_uk_or_eu_listing": flag_foreign,
        "needs_human_review": needs_review,
        "review_reason": reason,
    }


def auto_queue_for_review(conn: sqlite3.Connection, extraction_id: int, ticker: str, reason: str) -> None:
    """自动入 human_review_queue 表。"""
    c = conn.cursor()
    c.execute("""
        INSERT OR IGNORE INTO human_review_queue (extraction_id, ticker, reason, status, created_at)
        VALUES (?, ?, ?, 'pending', datetime('now'))
    """, (extraction_id, ticker, reason))
    conn.commit()