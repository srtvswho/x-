#!/usr/bin/env python3
"""
refresh_prices_polygon.py — 用 Polygon API 刷新 ticker_prices 缓存.

替代 MiniMax 恒生聚源 Connector, 适配普通 Docker/Linux 服务器.
不修改 raw_posts / extractions_intel / 其他业务表, 只 upsert ticker_prices + sector_snapshots.

刷新目标必须与 Dashboard 区块04 实际展示口径完全一致:
  - 调用 common.select_dashboard_ticker_targets(conn, limit=30) (跟 build_dashboard 共享)
  - 目标 (kol, ticker, call_date) 跟页面最终展示的 30 条完全相同
  - 按 ticker 聚合, 每 unique ticker 仅 1 次 range API 请求
  - 一个 ticker 多 (kol, ticker) 行共享 now_price

Usage:
    POLYGON_API_KEY=xxx python3 refresh_prices_polygon.py [--db PATH]
    POLYGON_API_KEY=xxx python3 refresh_prices_polygon.py --list-targets [--db PATH]

环境:
    POLYGON_API_KEY          必需. 不在日志中打印.
    POLYGON_REQUEST_INTERVAL 两次请求间隔秒数. 默认 13 (适配 Polygon 免费档 5 req/min,
                              60/5=12s + 1s buffer). 付费套餐可设 0.6 或更小.

请求量:
    N unique ticker ≤ 30 (DASHBOARD_TICKER_LIMIT)
    N 次 range API 请求 / 一次 (每个 ticker 1 次)
    不再调 /prev endpoint

特性:
- 目标 = Dashboard 区块04 展示目标 (同源共享函数)
- 一次 range API 拉 [earliest_call_date - 10d, today] 的全部 bars
- 从 bars 算每个 (kol, ticker) 行的 call_price (call_date 当天/之前最近一根)
- 最后一根 bar 给所有同 ticker 行共享 now_price + now_date
- 单 ticker 失败不阻塞其他 ticker
- 限速: POLYGON_REQUEST_INTERVAL (默认 13s)
- 429: Retry-After 头 sleep + 重试 1 次
- --list-targets: dry-run, 只输出目标, 不调网络, 不写 DB
- 日志: 展示行数 / unique ticker / unique ticker+call_date / 预计 API 请求 / 实际请求数 / 429 数

日志安全:
- apiKey 走 session.params 自动附加, 整个脚本不持有 key 字符串
- 任何 print / except 不输出 key
- 测试覆盖: 断言 URL 含 apiKey=, capsys 输出不出现 key 字面值
"""
from __future__ import annotations
import argparse
import json
import os
import re
import sqlite3
import sys
import time
from datetime import datetime, timedelta, timezone
from pathlib import Path

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

# 共享模块: 目标选择函数 + KOL 元数据 + 窗口函数
sys.path.insert(0, str(Path(__file__).parent))
from common import (  # noqa: E402
    select_dashboard_ticker_targets, group_targets_by_ticker,
    DASHBOARD_TICKER_LIMIT, DASHBOARD_MIN_DAYS,
)

POLYGON_BASE = "https://api.polygon.io"
USER_AGENT = "signalboard/1.0"

# Polygon 免费档 5 req/min → 12s/req + 1s buffer = 13s
POLYGON_REQUEST_INTERVAL_DEFAULT = 13.0

# ticker_prices schema (跟 build_dashboard.PRICE_CACHE_TABLE_DDL 一致)
TICKER_PRICES_DDL = """
CREATE TABLE IF NOT EXISTS ticker_prices (
    ticker TEXT NOT NULL,
    pub_date TEXT NOT NULL,
    call_price REAL,
    now_price REAL,
    now_date TEXT,
    sector_pct REAL,
    fetched_at TEXT NOT NULL,
    PRIMARY KEY (ticker, pub_date)
);
"""

SECTOR_SNAPSHOTS_DDL = """
CREATE TABLE IF NOT EXISTS sector_snapshots (
    sector_etf TEXT NOT NULL,
    snap_date TEXT NOT NULL,
    pct_30d REAL, pct_90d REAL, pct_180d REAL, pct_365d REAL,
    fetched_at TEXT NOT NULL,
    PRIMARY KEY (sector_etf, snap_date)
);
"""

# Polygon 美股覆盖: NYSE / NASDAQ / AMEX, 不含韩股/台股/A 股
US_TICKER_RE = re.compile(r"^[A-Z][A-Z0-9\.\-]{0,9}$")
US_TICKER_EXCLUDE = {None, "", "NULL", "NONE", "N/A", "-", "null", "none", "n/a", "."}


def is_us_ticker(t) -> bool:
    """1-5 字母 + 允许 ./-, 排除 NULL/NONE/N/A/-/空 + .SH/.SZ/.TW/.HK."""
    if t is None:
        return False
    s = str(t).strip()
    if not s or s.upper() in US_TICKER_EXCLUDE:
        return False
    if not US_TICKER_RE.match(s):
        return False
    if s.upper().endswith((".SH", ".SZ", ".TW", ".HK")):
        return False
    return True


def make_session(api_key: str) -> requests.Session:
    """Session with auto-retry on 5xx; apiKey 注入 session.params, 所有 GET 自动附加."""
    s = requests.Session()
    retries = Retry(
        total=3, backoff_factor=1.0,
        status_forcelist=[500, 502, 503, 504],  # 429 单独走 Retry-After
        allowed_methods=["GET"],
    )
    s.mount("https://", HTTPAdapter(max_retries=retries))
    s.params = {"apiKey": api_key}  # 所有 request 自动加 apiKey
    return s


class RateLimiter:
    """429 限速跟踪 + 429 退避."""

    def __init__(self, interval: float = POLYGON_REQUEST_INTERVAL_DEFAULT):
        self.interval = interval
        self.last_call = 0.0
        self.n_429 = 0

    def wait(self):
        """两次正常请求之间 sleep."""
        elapsed = time.monotonic() - self.last_call
        if elapsed < self.interval:
            time.sleep(self.interval - elapsed)
        self.last_call = time.monotonic()

    def handle_429(self, response) -> int:
        """处理 429. 返回 sleep 秒数 (>= 0)."""
        retry_after = response.headers.get("Retry-After", "60")
        try:
            sleep_s = int(retry_after)
        except ValueError:
            sleep_s = 60
        sleep_s = max(1, min(sleep_s, 300))
        self.n_429 += 1
        time.sleep(sleep_s)
        return sleep_s


def polygon_get(session: requests.Session, path: str, params: dict,
                limiter: RateLimiter, timeout: int = 10):
    """GET 一个 Polygon endpoint. 返回 (dict, status_code) 或 (None, status_code)."""
    limiter.wait()
    try:
        r = session.get(f"{POLYGON_BASE}{path}", params=params, timeout=timeout,
                        headers={"User-Agent": USER_AGENT})
    except requests.exceptions.RequestException as e:
        print(f"  ⚠ 网络错误 {path}: {type(e).__name__}", file=sys.stderr)
        return None, 0
    if r.status_code == 429:
        sleep_s = limiter.handle_429(r)
        print(f"  ⚠ 429 限流 {path} → Retry-After {sleep_s}s 后重试", file=sys.stderr)
        limiter.wait()
        try:
            r = session.get(f"{POLYGON_BASE}{path}", params=params, timeout=timeout,
                            headers={"User-Agent": USER_AGENT})
        except requests.exceptions.RequestException as e:
            print(f"  ⚠ 429 重试仍网络错误: {type(e).__name__}", file=sys.stderr)
            return None, 429
        if r.status_code == 429:
            print(f"  ⚠ 429 重试仍限速, 放弃 {path}", file=sys.stderr)
            return None, 429
    if r.status_code == 404:
        return None, 404
    if r.status_code >= 400:
        print(f"  ⚠ HTTP {r.status_code} {path}", file=sys.stderr)
        return None, r.status_code
    try:
        return r.json(), r.status_code
    except ValueError:
        return None, r.status_code


def bar_date(bar: dict) -> str | None:
    """Polygon bar 的 t (ms) 转 YYYY-MM-DD."""
    t = bar.get("t")
    if isinstance(t, (int, float)):
        return datetime.fromtimestamp(t / 1000, tz=timezone.utc).strftime("%Y-%m-%d")
    return None


def fetch_bars_range(session, ticker: str, start_date: str, end_date: str, limiter) -> list[dict]:
    """对单个 ticker 拉一次 range API, 返回所有 bars (按时间升序).

    /v2/aggs/ticker/{ticker}/range/1/day/{start}/{end}
    """
    path = f"/v2/aggs/ticker/{ticker}/range/1/day/{start_date}/{end_date}"
    data, _ = polygon_get(session, path, {"adjusted": "true", "sort": "asc", "limit": 5000}, limiter)
    if not data or "results" not in data or not data["results"]:
        return []
    return data["results"]


def lookup_call_price(bars: list[dict], call_date: str) -> float | None:
    """从 bars (升序) 找 call_date 当天或之前最近一个 bar 的收盘价."""
    for bar in reversed(bars):  # 升序, 从最新往回找第一个 bd <= call_date
        bd = bar_date(bar)
        if bd and bd <= call_date:
            return bar.get("c")
    if bars:
        return bars[0].get("c")  # 全是 call_date 之后, fallback 第一根
    return None


def ensure_tables(conn):
    """建表 (跟 build_dashboard.py schema 一致)."""
    conn.executescript(TICKER_PRICES_DDL)
    conn.executescript(SECTOR_SNAPSHOTS_DDL)
    conn.commit()


def upsert_price(conn, ticker, pub_date, call_price, now_price, now_date, sector_pct=None):
    """upsert ticker_prices. call_price + now_price 都 None 时不写."""
    if call_price is None and now_price is None:
        return False
    fetched_at = datetime.now(timezone.utc).isoformat()
    conn.execute("""
        INSERT INTO ticker_prices (ticker, pub_date, call_price, now_price, now_date, sector_pct, fetched_at)
        VALUES (?, ?, ?, ?, ?, ?, ?)
        ON CONFLICT(ticker, pub_date) DO UPDATE SET
            call_price=COALESCE(excluded.call_price, ticker_prices.call_price),
            now_price=COALESCE(excluded.now_price, ticker_prices.now_price),
            now_date=COALESCE(excluded.now_date, ticker_prices.now_date),
            sector_pct=COALESCE(excluded.sector_pct, ticker_prices.sector_pct),
            fetched_at=excluded.fetched_at
    """, (ticker, pub_date, call_price, now_price, now_date, sector_pct, fetched_at))
    return True


def print_target_summary(targets: list[dict], n_unique_tickers: int, n_unique_call_dates: int,
                        expected_requests: int):
    """统一日志: 展示行数 / unique ticker / unique (ticker, call_date) / 预计 API 请求."""
    print(f"  === 目标汇总 ===", flush=True)
    print(f"  展示行数 (kol, ticker, call_date): {len(targets)}", flush=True)
    print(f"  unique ticker: {n_unique_tickers}", flush=True)
    print(f"  unique (ticker, call_date): {n_unique_call_dates}", flush=True)
    print(f"  预计 API 请求: {expected_requests}", flush=True)


def list_targets(args):
    """Dry-run: 输出目标 / unique ticker / 预计请求. 不调网络, 不写 DB."""
    db_path = Path(args.db)
    if not db_path.exists():
        print(f"ERROR: DB 不存在: {db_path}", file=sys.stderr)
        sys.exit(1)
    conn = sqlite3.connect(str(db_path), timeout=30)
    try:
        targets = select_dashboard_ticker_targets(conn, limit=DASHBOARD_TICKER_LIMIT)
        by_ticker = group_targets_by_ticker(targets)
        n_unique_tickers = len(by_ticker)
        n_unique_call_dates = sum(len(v) for v in by_ticker.values())
        print_target_summary(targets, n_unique_tickers, n_unique_call_dates, n_unique_tickers)

        print(f"\n  === 详细目标 ===", flush=True)
        for i, t in enumerate(targets, 1):
            in_field = "✓ 强项" if t["in_field"] else "⚠ 圈外"
            print(f"    {i:2d}. {in_field:5s} {t['kol']:10s} {t['ticker']:8s} {t['direction']:5s} "
                  f"call_date={t['call_date']} ({t['days_since']}d ago) "
                  f"n_calls={t['n_calls']}", flush=True)
        print(f"\n  === unique ticker 范围 (每个 ticker 1 次 range API) ===", flush=True)
        for tk, items in by_ticker.items():
            call_dates = ", ".join(t["call_date"] for t in items)
            print(f"    {tk:8s} ({len(items)} rows): {call_dates}", flush=True)

        print(f"\n  --list-targets: dry-run 完成, 未调网络, 未写 DB", flush=True)
    finally:
        conn.close()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--db", default="/workspace/data/signalboard_full.db",
                        help="signalboard DB 路径 (默认 /workspace/data/signalboard_full.db)")
    parser.add_argument("--no-fetch", action="store_true",
                        help="只建表, 不调 Polygon (用于测试 / 离线恢复)")
    parser.add_argument("--list-targets", action="store_true",
                        help="Dry-run: 输出目标, 不调网络, 不写 DB")
    args = parser.parse_args()

    if args.list_targets:
        list_targets(args)
        return

    interval = float(os.environ.get("POLYGON_REQUEST_INTERVAL", str(POLYGON_REQUEST_INTERVAL_DEFAULT)))
    if not os.environ.get("POLYGON_API_KEY"):
        print("ERROR: POLYGON_API_KEY 未设置", file=sys.stderr)
        sys.exit(2)

    print(f"  POLYGON_REQUEST_INTERVAL: {interval}s (默认 {POLYGON_REQUEST_INTERVAL_DEFAULT}s 适配免费档 5 req/min)", flush=True)
    # 不打印 API Key

    db_path = Path(args.db)
    if not db_path.exists():
        print(f"ERROR: DB 不存在: {db_path}", file=sys.stderr)
        sys.exit(1)

    conn = sqlite3.connect(str(db_path), timeout=30)
    try:
        ensure_tables(conn)
        if args.no_fetch:
            print(f"  ✓ 建表完成 (no-fetch 模式): {db_path}")
            return

        # 1. 取目标 (跟 Dashboard 区块04 同源)
        targets = select_dashboard_ticker_targets(conn, limit=DASHBOARD_TICKER_LIMIT)
        by_ticker = group_targets_by_ticker(targets)
        n_unique_tickers = len(by_ticker)
        n_unique_call_dates = sum(len(v) for v in by_ticker.values())
        print_target_summary(targets, n_unique_tickers, n_unique_call_dates, n_unique_tickers)

        # 过滤非美股 ticker (跨境的 Polygon 没数据)
        for tk in list(by_ticker.keys()):
            if not is_us_ticker(tk):
                print(f"  · skip 非美股: {tk}", flush=True)
                del by_ticker[tk]
        n_after_filter = len(by_ticker)
        print(f"  非美股过滤后 unique ticker: {n_after_filter}", flush=True)

        if n_after_filter == 0:
            print(f"  (无美股目标, 跳过 fetch)", flush=True)
            return

        # 2. 每个 unique ticker 一次 range API
        api_key = os.environ["POLYGON_API_KEY"]
        session = make_session(api_key)
        limiter = RateLimiter(interval=interval)
        today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
        n_ok = 0; n_fail = 0; n_skip = 0; n_written = 0; n_404 = 0
        actual_requests = 0
        for ticker, items in by_ticker.items():
            # earliest_call_date - 10d
            try:
                earliest = min(t["call_date"] for t in items)
                start_dt = datetime.fromisoformat(earliest) - timedelta(days=10)
                start_str = start_dt.strftime("%Y-%m-%d")
            except Exception:
                start_str = "2025-01-01"
            try:
                actual_requests += 1
                bars = fetch_bars_range(session, ticker, start_str, today, limiter)
                if not bars:
                    n_404 += 1
                    print(f"  · {ticker}: 无数据 (404 或空)", flush=True)
                    continue

                # 最后一根 = now
                last_bar = bars[-1]
                now_p = last_bar.get("c")
                now_d = bar_date(last_bar)

                # 每个 (kol, ticker) 行的 call_price
                row_written = 0
                for t in items:
                    call_p = lookup_call_price(bars, t["call_date"])
                    written = upsert_price(conn, ticker, t["call_date"], call_p, now_p, now_d)
                    if written:
                        row_written += 1
                        n_written += 1
                n_ok += 1
                call_dates_str = ", ".join(t["call_date"] for t in items)
                print(f"  ✓ {ticker} [{len(items)} rows: {call_dates_str}]: "
                      f"now={now_p} @ {now_d}, rows_written={row_written}", flush=True)
            except Exception as e:
                n_fail += 1
                print(f"  ✗ {ticker}: {type(e).__name__}: {e}", file=sys.stderr, flush=True)
                continue
        conn.commit()
        print(f"  === summary ===", flush=True)
        print(f"  unique ticker: {n_after_filter}, ok: {n_ok}, fail: {n_fail}, 404/empty: {n_404}", flush=True)
        print(f"  实际 API 请求: {actual_requests} (≤ unique ticker {n_after_filter})", flush=True)
        print(f"  rows written to ticker_prices: {n_written}", flush=True)
        print(f"  429_retries: {limiter.n_429}", flush=True)
    finally:
        conn.close()


if __name__ == "__main__":
    main()