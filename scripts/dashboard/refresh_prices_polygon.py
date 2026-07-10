#!/usr/bin/env python3
"""
refresh_prices_polygon.py — 用 Polygon API 刷新 ticker_prices 缓存.

替代 MiniMax 恒生聚源 Connector, 适配普通 Docker/Linux 服务器.
不修改 raw_posts / extractions_intel / 其他业务表, 只 upsert ticker_prices.

Usage:
    POLYGON_API_KEY=xxx python3 refresh_prices_polygon.py [--db PATH]

环境:
    POLYGON_API_KEY   必需. 不在日志中打印.

特性:
- 退市 / 无效 / 非美股 ticker 容错 (skip, 不报错)
- 429 / 5xx 自动重试 (urllib3 Retry)
- 单 ticker 失败不阻塞其他 ticker
- upsert ticker_prices 表 (call_price + now_price + now_date)
- 输出 ok / fail / write 计数
"""
from __future__ import annotations
import argparse
import json
import os
import sqlite3
import sys
import time
from datetime import datetime, timedelta, timezone
from pathlib import Path

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

DB_DEFAULT = "/workspace/data/signalboard_full.db"
POLYGON_BASE = "https://api.polygon.io"
USER_AGENT = "intel-dashboard/1.0"

# 美股 ticker 格式: 1-5 个字母 (允许 . / -)
# Polygon 美股覆盖: NYSE / NASDAQ / AMEX, 不含韩股/台股/A 股
import re
US_TICKER_RE = re.compile(r"^[A-Z][A-Z0-9\.\-]{0,9}$")


def get_api_key() -> str | None:
    """读 POLYGON_API_KEY 环境变量. 不打印 key."""
    k = os.environ.get("POLYGON_API_KEY", "").strip()
    if not k:
        print("  ✗ POLYGON_API_KEY 未设置", file=sys.stderr)
        return None
    return k


def make_session(api_key: str) -> requests.Session:
    """Session with auto-retry on 429 / 5xx."""
    s = requests.Session()
    retries = Retry(
        total=3, backoff_factor=1.0,
        status_forcelist=[429, 500, 502, 503, 504],
        allowed_methods=["GET"],
    )
    s.mount("https://", HTTPAdapter(max_retries=retries))
    return s


def polygon_get(session: requests.Session, path: str, params: dict, timeout: int = 10):
    """GET 一个 Polygon endpoint. 返回 dict / None. 不抛异常."""
    params = {**params, "apiKey": "[REDACTED]"} if False else {**params}  # 占位, 防止误打
    try:
        r = session.get(f"{POLYGON_BASE}{path}", params=params, timeout=timeout,
                        headers={"User-Agent": USER_AGENT})
    except requests.exceptions.RequestException as e:
        print(f"  ⚠ 网络错误 {path}: {type(e).__name__}", file=sys.stderr)
        return None
    if r.status_code == 404:
        return None  # ticker 退市/不存在
    if r.status_code == 429:
        print(f"  ⚠ 429 限流 {path}", file=sys.stderr)
        return None
    if r.status_code >= 400:
        print(f"  ⚠ HTTP {r.status_code} {path}", file=sys.stderr)
        return None
    try:
        return r.json()
    except ValueError:
        return None


def bar_date(bar: dict) -> str | None:
    """Polygon bar 的 t (ms) 转 YYYY-MM-DD."""
    t = bar.get("t")
    if isinstance(t, (int, float)):
        return datetime.fromtimestamp(t / 1000, tz=timezone.utc).strftime("%Y-%m-%d")
    return None


def get_call_price(session, api_key, ticker, call_date_str):
    """找 call_date 当天或之前最近一个交易日的收盘价."""
    try:
        target = datetime.strptime(call_date_str[:10], "%Y-%m-%d")
    except ValueError:
        return None
    start = target - timedelta(days=10)  # 周末/假期最多 10 天
    end = target + timedelta(days=1)
    path = f"/v2/aggs/ticker/{ticker}/range/1/day/{start.strftime('%Y-%m-%d')}/{end.strftime('%Y-%m-%d')}"
    data = polygon_get(session, path, {"adjusted": "true", "sort": "desc", "limit": 20})
    if not data or "results" not in data or not data["results"]:
        return None
    # 取 target 当天或之前的最近 bar
    for bar in data["results"]:
        bd = bar_date(bar)
        if bd and bd <= call_date_str[:10]:
            return bar.get("c")
    # 全是 target 之后 (理论上不会), fallback 取最早一根
    return data["results"][-1].get("c")


def get_now(session, api_key, ticker):
    """最新一天的收盘价 + 日期."""
    path = f"/v2/aggs/ticker/{ticker}/prev"
    data = polygon_get(session, path, {})
    if not data or "results" not in data or not data["results"]:
        return None, None
    bar = data["results"][0]
    return bar.get("c"), bar_date(bar)


def is_us_ticker(ticker: str) -> bool:
    """过滤非美股 (韩股 6 位数字 / 台股 .TW / A 股 6 位 .SH/.SZ)."""
    if not ticker:
        return False
    t = ticker.upper().strip()
    # 排除字面字符串 (LLM 抽取空值时常用)
    if t in ("NULL", "NONE", "N/A", "-", ""):
        return False
    if not US_TICKER_RE.match(t):
        return False
    if t.endswith(".SH") or t.endswith(".SZ") or t.endswith(".TW") or t.endswith(".HK"):
        return False
    # 6 位数字 (A 股 / 韩股) 已由正则过滤 (必须字母开头)
    return True


def get_dashboard_tickers(conn):
    """从 DB 模拟 build_dashboard.py 的 query_tickers 选 ticker.

    query_tickers 用 (kol, ticker) 维度去重 + MIN_DAYS=5 过滤 + in_field 排序.
    ticker_prices 需要 cache 所有 30 个展示的 ticker (无论 has_price).
    """
    rows = conn.execute("""
        SELECT e.source_id, e.ticker, e.direction, e.bottleneck, r.published_at
        FROM extractions_intel e
        JOIN raw_posts r ON r.post_id = e.post_id
        WHERE e.direction IN ('long','short')
          AND e.is_retrospective = 0 AND e.is_disclosure = 0
          AND e.ticker IS NOT NULL
        ORDER BY r.published_at DESC
    """).fetchall()

    SRC2KOL = {
        "tw_jukan05": "jukan", "tw_aleabitoreddit": "serenity",
        "tw_zephyr_z9": "zephyr", "tw_austinsemis": "austin",
    }

    by_kol_tk = {}
    for src, ticker_json, direction, bk, pub in rows:
        kol = SRC2KOL.get(src, src.replace("tw_", ""))
        # parse ticker JSON arr
        try:
            ts = json.loads(ticker_json) if ticker_json and ticker_json.startswith("[") else [ticker_json]
        except Exception:
            ts = [ticker_json]
        for tk in ts:
            if not tk or tk == "null":
                continue
            key = (kol, tk)
            if key not in by_kol_tk:
                by_kol_tk[key] = {"latest_pub": pub, "earliest_pub": pub, "n_calls": 1}
            else:
                rec = by_kol_tk[key]
                rec["n_calls"] += 1
                if pub < rec["earliest_pub"]:
                    rec["earliest_pub"] = pub

    # MIN_DAYS=5 过滤 (跟 query_tickers 一致)
    today_d = datetime.now().date()
    out = []
    skipped = 0
    for (kol, tk), rec in by_kol_tk.items():
        pub_date = rec["latest_pub"][:10]
        try:
            days = (today_d - datetime.strptime(pub_date, "%Y-%m-%d").date()).days
        except ValueError:
            continue
        if days < 5:
            skipped += 1
            continue
        # 取每个 ticker 最早一次喊单日期 (缓存覆盖最长区间)
        out.append((tk, rec["earliest_pub"][:10], kol))
    print(f"  候选 (kol, ticker): {len(by_kol_tk)}, 跳过 <5d: {skipped}, 待刷新: {len(out)}")
    return out


def upsert_price(conn, ticker, pub_date, call_price, now_price, now_date):
    """upsert ticker_prices 表. 不写业务表."""
    if call_price is None and now_price is None:
        return False  # 都没拿到, 不污染 cache
    now_iso = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
    conn.execute("""
        INSERT INTO ticker_prices
            (ticker, pub_date, call_price, now_price, now_date, fetched_at)
        VALUES (?, ?, ?, ?, ?, ?)
        ON CONFLICT(ticker, pub_date) DO UPDATE SET
            call_price=COALESCE(excluded.call_price, ticker_prices.call_price),
            now_price=COALESCE(excluded.now_price, ticker_prices.now_price),
            now_date=COALESCE(excluded.now_date, ticker_prices.now_date),
            fetched_at=excluded.fetched_at
    """, (ticker, pub_date, call_price, now_price, now_date, now_iso))
    return True


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--db", default=DB_DEFAULT)
    parser.add_argument("--rate-sleep", type=float, default=0.15,
                        help="每个 ticker 之间 sleep 秒数 (Polygon 5 req/min 免费档)")
    args = parser.parse_args()

    api_key = get_api_key()
    if not api_key:
        sys.exit(2)

    session = make_session(api_key)

    db_path = Path(args.db)
    if not db_path.exists():
        print(f"  ✗ DB 不存在: {db_path}", file=sys.stderr)
        sys.exit(2)

    print(f"===== refresh_prices_polygon =====")
    print(f"  DB: {db_path}")
    print(f"  Polygon: {POLYGON_BASE}")

    conn = sqlite3.connect(str(db_path), timeout=30)

    # ticker_prices 表 schema (兜底创建, 兼容没有 connector cache 的环境)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS ticker_prices (
            ticker TEXT NOT NULL,
            pub_date TEXT NOT NULL,
            call_price REAL,
            now_price REAL,
            now_date TEXT,
            fetched_at TEXT NOT NULL,
            PRIMARY KEY (ticker, pub_date)
        )
    """)
    conn.commit()

    candidates = get_dashboard_tickers(conn)
    print(f"  待刷新 ticker: {len(candidates)}")

    ok = 0
    fail = 0
    written = 0
    skipped_non_us = 0
    skipped_empty = 0

    for ticker, pub_date, kol in candidates:
        if not is_us_ticker(ticker):
            print(f"  ⏭ {ticker} (KOL={kol}, pub={pub_date}): skip (非美股)")
            skipped_non_us += 1
            continue
        try:
            cp = get_call_price(session, api_key, ticker, pub_date)
            np_, nd = get_now(session, api_key, ticker)
            if cp is None and np_ is None:
                print(f"  ✗ {ticker}: 无数据 (可能退市/无效)")
                skipped_empty += 1
                continue
            if upsert_price(conn, ticker, pub_date, cp, np_, nd):
                written += 1
            ok += 1
            cp_s = f"${cp:.2f}" if cp is not None else "—"
            np_s = f"${np_:.2f}" if np_ is not None else "—"
            print(f"  ✓ {ticker} (KOL={kol}, pub={pub_date}): call={cp_s} now={np_s} ({nd})")
        except Exception as e:
            print(f"  ✗ {ticker}: 异常 {type(e).__name__}: {e}")
            fail += 1
        time.sleep(args.rate_sleep)

    conn.commit()
    conn.close()

    total = len(candidates)
    print()
    print(f"  ===== 汇总 =====")
    print(f"  候选总数:      {total}")
    print(f"  ok (有数据):   {ok}")
    print(f"  fail (异常):   {fail}")
    print(f"  written:       {written}")
    print(f"  非美股 skip:   {skipped_non_us}")
    print(f"  无数据 skip:   {skipped_empty}")


if __name__ == "__main__":
    main()