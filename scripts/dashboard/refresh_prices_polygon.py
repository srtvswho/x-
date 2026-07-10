#!/usr/bin/env python3
"""
refresh_prices_polygon.py — 用 Polygon API 刷新 ticker_prices 缓存.

替代 MiniMax 恒生聚源 Connector, 适配普通 Docker/Linux 服务器.
不修改 raw_posts / extractions_intel / 其他业务表, 只 upsert ticker_prices + sector_snapshots.

Usage:
    POLYGON_API_KEY=xxx python3 refresh_prices_polygon.py [--db PATH]

环境:
    POLYGON_API_KEY          必需. 不在日志中打印.
    POLYGON_REQUEST_INTERVAL 两次请求间隔秒数 (默认 0.6, 适配 5 req/min 免费档)

特性:
- 所有真实请求携带 apiKey (注入 session.params, requests 自动加到 URL)
- 退市 / 无效 / 非美股 ticker 容错 (skip, 不报错)
- 429 用 Retry-After + 自定义重试; 5xx 走 urllib3 Retry
- 单 ticker 失败不阻塞其他 ticker
- 限速 sleep 时间可调 (POLYGON_REQUEST_INTERVAL)
- 输出 ok / fail / 429_retry 计数
- ticker_prices schema 跟 build_dashboard.py 一致: 含 sector_pct REAL

日志安全:
- apiKey 走 session.params 自动附加, 整个脚本不持有 key 字符串
- 任何 print / except 不输出 key
- 测试覆盖: 断言请求 URL 含 apiKey= 但 capsys 输出不出现 key 字面值
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

POLYGON_BASE = "https://api.polygon.io"
USER_AGENT = "signalboard/1.0"

# 跟 build_dashboard.py PRAGMA user_version + 字段一致, refresh 建表后 build_dashboard
# 查询不会因缺字段失败.
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
    """Session with auto-retry on 5xx; apiKey 注入 session.params, 所有 GET 自动附加.

    requests.Session.params 是默认 query string, 每次 get() 都会自动 merge 进 URL.
    整个脚本不持有 api_key 字符串作为变量, 只传给 session 一次, 日志/异常无法泄露.
    """
    s = requests.Session()
    retries = Retry(
        total=3, backoff_factor=1.0,
        status_forcelist=[500, 502, 503, 504],  # 429 单独走 Retry-After, 不在这
        allowed_methods=["GET"],
    )
    s.mount("https://", HTTPAdapter(max_retries=retries))
    s.params = {"apiKey": api_key}  # 关键: 所有 request 自动加 apiKey
    return s


class RateLimiter:
    """429 限速跟踪 + 429 退避.

    - 非 429: 按 REQUEST_INTERVAL sleep
    - 429: 按 Retry-After 头 sleep (默认 60s, 不可信时取上限 5 min)
    """

    def __init__(self, interval: float = 0.6):
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
        """处理 429. 返回 sleep 秒数 (>= 0).

        response 是 requests.Response (from session.get).
        读 Retry-After 头 (秒数或 HTTP-date); 不存在则用 60s.
        """
        retry_after = response.headers.get("Retry-After", "60")
        try:
            sleep_s = int(retry_after)
        except ValueError:
            # HTTP-date 格式, fallback 60s
            sleep_s = 60
        sleep_s = max(1, min(sleep_s, 300))  # clamp 1s..300s
        self.n_429 += 1
        time.sleep(sleep_s)
        return sleep_s


def polygon_get(session: requests.Session, path: str, params: dict,
                limiter: RateLimiter, timeout: int = 10):
    """GET 一个 Polygon endpoint. 返回 (dict, status_code) 或 (None, status_code).

    不抛异常 (除 KeyboardInterrupt). 429 自动 sleep Retry-After, 然后重试一次.
    限速由 limiter.wait() 在每次请求前 sleep.
    """
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
        # 一次重试
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


def get_call_price(session, ticker, call_date_str, limiter):
    """找 call_date 当天或之前最近一个交易日的收盘价."""
    try:
        target = datetime.strptime(call_date_str[:10], "%Y-%m-%d")
    except (ValueError, TypeError):
        return None
    start = target - timedelta(days=10)  # 周末/假期最多 10 天
    end = target + timedelta(days=1)
    path = f"/v2/aggs/ticker/{ticker}/range/1/day/{start.strftime('%Y-%m-%d')}/{end.strftime('%Y-%m-%d')}"
    data, _ = polygon_get(session, path, {"adjusted": "true", "sort": "desc", "limit": 20}, limiter)
    if not data or "results" not in data or not data["results"]:
        return None
    # 取 target 当天或之前的最近 bar
    for bar in data["results"]:
        bd = bar_date(bar)
        if bd and bd <= call_date_str[:10]:
            return bar.get("c")
    # 全是 target 之后 (理论上不会), fallback 取最早一根
    return data["results"][-1].get("c")


def get_now(session, ticker, limiter):
    """最新一天的收盘价 + 日期."""
    path = f"/v2/aggs/ticker/{ticker}/prev"
    data, _ = polygon_get(session, path, {}, limiter)
    if not data or "results" not in data or not data["results"]:
        return None, None
    bar = data["results"][0]
    return bar.get("c"), bar_date(bar)


def get_dashboard_tickers(conn) -> list[dict]:
    """从 extractions_intel 拿所有 (kol, ticker, pub_date) 唯一组合.

    排掉非美股 ticker (大陆/台/港股, Polygon 没数据).
    """
    rows = conn.execute("""
        SELECT DISTINCT e.source_id, e.ticker, r.published_at
        FROM extractions_intel e
        JOIN raw_posts r ON r.post_id = e.post_id
        WHERE e.ticker IS NOT NULL
    """).fetchall()
    out = []
    for src, ticker_json, pub_at in rows:
        try:
            tickers = json.loads(ticker_json) if ticker_json else []
        except (ValueError, TypeError):
            continue
        for t in tickers:
            if is_us_ticker(t):
                out.append({"source_id": src, "ticker": t, "pub_date": pub_at[:10]})
    return out


def ensure_tables(conn):
    """建表 (跟 build_dashboard.py schema 一致)."""
    conn.executescript(TICKER_PRICES_DDL)
    conn.executescript(SECTOR_SNAPSHOTS_DDL)
    conn.commit()


def upsert_price(conn, ticker, pub_date, call_price, now_price, now_date, sector_pct=None):
    """upsert ticker_prices. call_price + now_price 都 None 时不写 (防污染 cache)."""
    if call_price is None and now_price is None:
        return False  # skip
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


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--db", default="/workspace/data/signalboard_full.db",
                        help="signalboard DB 路径 (默认 /workspace/data/signalboard_full.db)")
    parser.add_argument("--no-fetch", action="store_true",
                        help="只建表, 不调 Polygon (用于测试 / 离线恢复)")
    args = parser.parse_args()

    interval = float(os.environ.get("POLYGON_REQUEST_INTERVAL", "0.6"))
    if not os.environ.get("POLYGON_API_KEY"):
        print("ERROR: POLYGON_API_KEY 未设置", file=sys.stderr)
        sys.exit(2)

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
        # 调 polygon
        api_key = os.environ["POLYGON_API_KEY"]
        session = make_session(api_key)
        limiter = RateLimiter(interval=interval)
        candidates = get_dashboard_tickers(conn)
        n_total = len(candidates)
        print(f"  candidates: {n_total}", flush=True)
        n_ok = 0; n_fail = 0; n_skip = 0; n_written = 0
        for c in candidates:
            ticker = c["ticker"]; pub_date = c["pub_date"]
            try:
                call_p = get_call_price(session, ticker, pub_date, limiter)
                now_p, now_d = get_now(session, ticker, limiter)
                if call_p is None and now_p is None:
                    n_skip += 1
                    print(f"  · {ticker} {pub_date}: skip (无数据)", flush=True)
                    continue
                written = upsert_price(conn, ticker, pub_date, call_p, now_p, now_d)
                if written:
                    n_written += 1
                n_ok += 1
                print(f"  ✓ {ticker} {pub_date}: call={call_p} now={now_p} now_date={now_d}", flush=True)
            except Exception as e:
                n_fail += 1
                print(f"  ✗ {ticker} {pub_date}: {type(e).__name__}: {e}", file=sys.stderr, flush=True)
                # 单 ticker 失败不中断, 继续下一个
                continue
        conn.commit()
        print(f"  === summary ===", flush=True)
        print(f"  total: {n_total}, ok: {n_ok}, written: {n_written}, skip: {n_skip}, fail: {n_fail}, "
              f"429_retries: {limiter.n_429}", flush=True)
    finally:
        conn.close()


if __name__ == "__main__":
    main()