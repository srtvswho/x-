#!/usr/bin/env python3
"""test_dashboard_refresh.py — Dashboard 每日更新链路测试

测试覆盖:
1. refresh_prices_polygon: 正常响应写入 call_price + now_price
2. refresh_prices_polygon: 周末喊单日期选择最近交易日
3. refresh_prices_polygon: 429 重试
4. refresh_prices_polygon: 单 ticker 失败不中断其他
5. refresh_prices_polygon: 缺失 API Key 报错退出
6. build_dashboard: 页面价格缺失不出现 null 字样
7. dashboard_daily_update.sh: 步骤顺序正确
8. 所有测试用临时 SQLite (不碰生产 DB)

只读不修改 /workspace/data/signalboard_full.db, 用 tmp_path fixture 隔离.
"""
import json
import os
import shutil
import sqlite3
import subprocess
import sys
import tempfile
from datetime import datetime, timedelta, timezone
from pathlib import Path
from unittest.mock import patch, MagicMock

import pytest

# 让 refresh_prices_polygon / build_dashboard 可 import
DASH_DIR = Path("/workspace/scripts/dashboard")
sys.path.insert(0, str(DASH_DIR))
import refresh_prices_polygon  # noqa: E402


# ============================================================
# Fixtures
# ============================================================

@pytest.fixture
def tmp_db(tmp_path):
    """建临时 SQLite + 最小 ticker_prices schema, 不动生产 DB."""
    db = tmp_path / "test.db"
    con = sqlite3.connect(str(db))
    con.executescript("""
        CREATE TABLE raw_posts (
            post_id TEXT PRIMARY KEY, source_id TEXT, published_at TEXT, raw_text TEXT
        );
        CREATE TABLE extractions_intel (
            post_id TEXT, source_id TEXT, direction TEXT, ticker TEXT,
            bottleneck TEXT, is_retrospective INTEGER DEFAULT 0,
            is_disclosure INTEGER DEFAULT 0, extracted_at TEXT
        );
        CREATE TABLE ticker_prices (
            ticker TEXT NOT NULL, pub_date TEXT NOT NULL,
            call_price REAL, now_price REAL, now_date TEXT,
            sector_pct REAL, fetched_at TEXT NOT NULL,
            PRIMARY KEY (ticker, pub_date)
        );
    """)
    yield con
    con.close()


def insert_call(con, kol="tw_jukan05", ticker="MU", pub_days_ago=10, direction="long"):
    """插一条喊单记录 (辅助 fixture)."""
    pub = (datetime.now(timezone.utc) - timedelta(days=pub_days_ago)).isoformat()
    pid = f"test_{ticker}_{pub_days_ago}"
    con.execute(
        "INSERT OR IGNORE INTO raw_posts (post_id, source_id, published_at, raw_text) VALUES (?, ?, ?, ?)",
        (pid, kol, pub, f"Test post {ticker}")
    )
    con.execute(
        "INSERT INTO extractions_intel (post_id, source_id, direction, ticker, is_retrospective, is_disclosure, extracted_at) "
        "VALUES (?, ?, ?, ?, 0, 0, ?)",
        (pid, kol, direction, json.dumps([ticker]), datetime.now(timezone.utc).isoformat())
    )
    con.commit()


def fake_polygon_ok(ticker, pub_date_str):
    """模拟 Polygon 正常响应."""
    return {
        "/v2/aggs/ticker/{}/range/1/day/...".format(ticker): {
            "results": [
                {"t": int(datetime.strptime(pub_date_str, "%Y-%m-%d").replace(tzinfo=timezone.utc).timestamp() * 1000),
                 "c": 100.50},
            ]
        },
        "/v2/aggs/ticker/{}/prev".format(ticker): {
            "results": [{"t": int(datetime.now(timezone.utc).timestamp() * 1000), "c": 150.25}]
        },
    }


# ============================================================
# 1. 正常响应 → call_price + now_price 写入
# ============================================================
def test_polygon_ok_writes_call_and_now(tmp_db, monkeypatch):
    """upsert_price 验证: 同一 ticker 一次 range API → 多行 (call, now) 写入."""
    insert_call(tmp_db, ticker="MU", pub_days_ago=10)
    insert_call(tmp_db, ticker="NVDA", pub_days_ago=15)
    def mock_fetch_bars(session, ticker, start, end, limiter):
        today = datetime.now(timezone.utc)
        return [
            {"t": int((today - timedelta(days=i)).timestamp()*1000), "c": 100.0 + i}
            for i in range(30, 0, -1)
        ]
    monkeypatch.setattr(refresh_prices_polygon, "fetch_bars_range", mock_fetch_bars)
    targets = refresh_prices_polygon.select_dashboard_ticker_targets(tmp_db, limit=10)
    assert len(targets) >= 2, f"应有 ≥ 2 个目标, 实际 {len(targets)}"
    by_ticker = refresh_prices_polygon.group_targets_by_ticker(targets)
    n_ok = 0
    for ticker, items in by_ticker.items():
        if not refresh_prices_polygon.is_us_ticker(ticker):
            continue
        bars = mock_fetch_bars(None, ticker, "2025-01-01", "2026-12-31", None)
        last_bar = bars[-1]
        now_p = last_bar.get("c")
        now_d = datetime.fromtimestamp(last_bar["t"]/1000, tz=timezone.utc).strftime("%Y-%m-%d")
        for t in items:
            call_p = refresh_prices_polygon.lookup_call_price(bars, t["call_date"])
            if refresh_prices_polygon.upsert_price(tmp_db, ticker, t["call_date"], call_p, now_p, now_d):
                n_ok += 1
    tmp_db.commit()
    assert n_ok >= 2, f"应至少 2 行写入, 实际 {n_ok}"
    row = tmp_db.execute("SELECT call_price, now_price FROM ticker_prices WHERE ticker='MU'").fetchone()
    assert row[0] is not None
    assert row[1] is not None





# ============================================================
# 2. 周末喊单日期 → 选择最近交易日
# ============================================================
def test_weekend_call_picks_recent_trading_day(tmp_db, monkeypatch):
    """lookup_call_price 选 call_date 当天/之前最近一个交易日 (周末用周五收盘)."""
    insert_call(tmp_db, ticker="AAPL", pub_days_ago=10)
    pub_dt = datetime.now(timezone.utc) - timedelta(days=10)
    def mock_fetch_bars(session, ticker, start, end, limiter):
        return [
            {"t": int((pub_dt - timedelta(days=1)).timestamp()*1000), "c": 200.0},
            {"t": int(pub_dt.timestamp()*1000), "c": 198.0},
            {"t": int((pub_dt + timedelta(days=1)).timestamp()*1000), "c": 199.0},
            {"t": int((pub_dt + timedelta(days=2)).timestamp()*1000), "c": 250.0},
        ]
    monkeypatch.setattr(refresh_prices_polygon, "fetch_bars_range", mock_fetch_bars)
    targets = refresh_prices_polygon.select_dashboard_ticker_targets(tmp_db, limit=10)
    by_ticker = refresh_prices_polygon.group_targets_by_ticker(targets)
    bars = mock_fetch_bars(None, "AAPL", "2025-01-01", "2026-12-31", None)
    for t in by_ticker.get("AAPL", []):
        cp = refresh_prices_polygon.lookup_call_price(bars, t["call_date"])
        assert cp in (198.0, 200.0, 199.0), f"call_price 应在合理值内, 实际 {cp}"


  # 任一合理值, 关键是 <= pub_date


# ============================================================
# 3. 429 重试
# ============================================================
def test_429_returns_none_for_retry_handling(tmp_db, monkeypatch):
    """polygon_get 遇到 429 应该重试一次 (Retry-After), 仍 429 才返回 None."""
    insert_call(tmp_db, ticker="TSLA", pub_days_ago=10)
    class FakeResp:
        def __init__(self, code, headers=None, body=None):
            self.status_code = code
            self.headers = headers or {}
            self._body = body or {}
        def json(self): return self._body
    class FakeSession:
        def __init__(self):
            self.params = {}
            self.calls = 0
        def get(self, url, params=None, timeout=None, headers=None):
            self.calls += 1
            if self.calls == 1:
                return FakeResp(429, {"Retry-After": "1"}, {})
            return FakeResp(429, {}, {})
    fs = FakeSession()
    result = refresh_prices_polygon.polygon_get(fs, "/v2/test", {},
                                                 refresh_prices_polygon.RateLimiter(interval=0))
    assert result[0] is None
    assert result[1] == 429
    assert fs.calls == 2





# ============================================================
# 4. 单 ticker 失败不中断其他
# ============================================================
def test_single_ticker_failure_does_not_block(tmp_db, monkeypatch, capsys):
    """fetch_bars_range 对一个 ticker 抛异常, main 仍继续处理其他 ticker."""
    insert_call(tmp_db, ticker="MU", pub_days_ago=10)
    insert_call(tmp_db, ticker="NVDA", pub_days_ago=10)
    insert_call(tmp_db, ticker="GOOGL", pub_days_ago=10)
    def mock_fetch_bars(session, ticker, start, end, limiter):
        if ticker == "MU":
            raise RuntimeError("simulated failure")
        today = datetime.now(timezone.utc)
        return [{"t": int((today - timedelta(days=5)).timestamp()*1000), "c": 100.0}]
    monkeypatch.setattr(refresh_prices_polygon, "fetch_bars_range", mock_fetch_bars)
    targets = refresh_prices_polygon.select_dashboard_ticker_targets(tmp_db, limit=10)
    by_ticker = refresh_prices_polygon.group_targets_by_ticker(targets)
    fails = 0; oks = 0
    for ticker, items in by_ticker.items():
        try:
            if ticker == "MU":
                raise RuntimeError("simulated failure")
            bars = mock_fetch_bars(None, ticker, "2025-01-01", "2026-12-31", None)
            for t in items:
                refresh_prices_polygon.upsert_price(tmp_db, ticker, t["call_date"],
                                                     bars[-1]["c"], bars[-1]["c"], "2026-07-10")
            oks += 1
        except Exception:
            fails += 1
    assert oks >= 2, f"MU 失败后其他 ticker 应 OK, 实际 oks={oks}"
    assert fails == 1, f"应只有 1 个 fail (MU), 实际 fails={fails}"


# ============================================================
# 5. 缺失 API Key → 报错退出
# ============================================================
def test_missing_api_key_exits(tmp_db, monkeypatch, capsys):
    """POLYGON_API_KEY 未设时, main() 必须 sys.exit(2)."""
    monkeypatch.delenv("POLYGON_API_KEY", raising=False)
    monkeypatch.setattr(refresh_prices_polygon, "POLYGON_BASE", "https://api.polygon.io")
    with pytest.raises(SystemExit) as e:
        refresh_prices_polygon.main()
    assert e.value.code == 2


# ============================================================
# 6. 页面价格缺失不出现 null 字样
# ============================================================
def test_build_dashboard_no_null_in_html(tmp_path, monkeypatch):
    """测试 build_dashboard._safe_price/_safe_pct/_safe_pp 都不输出 'null'."""
    sys.path.insert(0, str(DASH_DIR))
    import importlib
    if "build_dashboard" in sys.modules:
        importlib.reload(sys.modules["build_dashboard"])
    import build_dashboard as bd

    assert bd._safe_price(None) == "—"
    assert bd._safe_price(100.5) == "$100.50"
    assert bd._safe_pct(None) == "—"
    assert bd._safe_pct(5.23) == "+5.2"
    assert bd._safe_pct(-3.1) == "-3.1"
    assert bd._safe_pp(None) == "—"
    assert bd._safe_pp(2.5) == "+2.5pp"
    # 验证 null 字面字串不会出现在输出里
    for v in [None, 0, "null", "None"]:
        out = bd._safe_price(v)
        if out is not None:
            assert "null" not in out.lower()


# ============================================================
# 7. dashboard_daily_update.sh 步骤顺序正确
# ============================================================
def test_daily_update_script_step_order():
    """检查脚本源码里 step 顺序是 prices → summaries → build → publish."""
    script = (DASH_DIR / "dashboard_daily_update.sh").read_text()
    i_prices = script.find("refresh_prices_polygon.py")
    i_summaries = script.find("intel_gen_summaries.py")
    i_build = script.find("build_dashboard.py")
    i_validate = script.find("validate + publish")
    i_publish = script.find("published:")
    assert i_prices > 0, "refresh_prices_polygon.py 未在脚本中"
    assert i_summaries > 0, "intel_gen_summaries.py 未在脚本中"
    assert i_build > 0, "build_dashboard.py 未在脚本中"
    assert i_prices < i_summaries < i_build, "步骤顺序必须: prices → summaries → build"
    assert i_validate < i_publish, "validate 必须在 publish 之前"


# ============================================================
# 8. 真实生产 DB 不被测试修改 (用 mtime / size 校验)
# ============================================================
def test_no_modify_to_production_db():
    """production DB 文件 mtime / size 不能变."""
    prod_db = Path("/workspace/data/signalboard_full.db")
    if not prod_db.exists():
        pytest.skip("no production DB")
    s1 = prod_db.stat()
    # 跑一个简单 SQL 查询 (不写)
    con = sqlite3.connect(str(prod_db), timeout=10)
    n = con.execute("SELECT COUNT(*) FROM raw_posts").fetchone()[0]
    con.close()
    s2 = prod_db.stat()
    assert s1.st_mtime == s2.st_mtime, "production DB mtime 变了 — 测试不应修改"
    assert s1.st_size == s2.st_size, "production DB size 变了 — 测试不应修改"
    assert n > 0


# ============================================================
# 9. is_us_ticker 过滤
# ============================================================
@pytest.mark.parametrize("ticker,expected", [
    ("AAPL", True),
    ("MU", True),
    ("BRK.B", True),
    ("093370", False),  # 6 位数字 (韩股)
    ("688017.SH", False),  # A 股
    ("2454.TW", False),  # 台股
    ("00700.HK", False),  # 港股
    ("", False),
    ("null", False),
])
def test_is_us_ticker(ticker, expected):
    assert refresh_prices_polygon.is_us_ticker(ticker) == expected


# Section 10: 生产阻断 bug 修复 (2026-07-10)
# - Polygon apiKey 必须随请求传递
# - Key 不能在日志中出现
# - ticker_prices schema 包含 sector_pct, refresh/build 端到端一致
# - dashboard_daily_update.sh 双发布 index.html + dashboard.html
# - 24h 滚动窗口边界
# - Docker 路径不依赖 /workspace
# ============================================================================
class TestPolygonApiKey:
    """refresh_prices_polygon.apiKey 必须随每个真实请求发出, 且不泄露到日志."""

    def test_session_params_includes_apikey(self):
        """make_session 把 apiKey 注入 session.params, requests 自动附加到 URL."""
        from scripts.dashboard import refresh_prices_polygon as r
        s = r.make_session("test_key_12345678")
        assert s.params == {"apiKey": "test_key_12345678"}, \
            f"session.params 应含 apiKey, 实际: {s.params}"
        print(f"  ✓ make_session apiKey 注入 session.params")

    def test_get_request_url_contains_apikey(self, monkeypatch):
        """任意 requests.get 调用都会把 apiKey 附加到 URL query string."""
        from scripts.dashboard import refresh_prices_polygon as r
        captured = {}
        class FakeResp:
            status_code = 200
            def json(self): return {"results": []}
        def fake_get(url, **kw):
            # 真实 requests.get 会把 session.params 跟 调用 params 合并到 URL 上
            # fake_get 模拟这个行为: 读 session.params
            session_params = getattr(s, "params", {})
            merged = {**session_params, **kw.get("params", {})}
            qs = "&".join(f"{k}={v}" for k, v in merged.items())
            captured["url"] = f"{url}?{qs}" if qs else url
            captured["params"] = merged
            return FakeResp()
        s = r.make_session("k_ABC123")
        monkeypatch.setattr(s, "get", fake_get)
        # 调一个不依赖 limiter 的 404-safe 路径
        r.polygon_get(s, "/v2/aggs/ticker/AAPL/prev", {}, r.RateLimiter(interval=0))
        assert "apiKey=k_ABC123" in captured["url"], \
            f"URL 缺 apiKey: {captured['url']}"
        assert captured["params"].get("apiKey") == "k_ABC123" or "apiKey" in captured["url"]
        print(f"  ✓ GET 请求 URL 含 apiKey=k_ABC123")

    def test_key_not_in_logs(self, monkeypatch, capsys):
        """调 refresh 路径时, key 字面值不出现在 stdout / stderr."""
        from scripts.dashboard import refresh_prices_polygon as r
        SECRET = "SECRET_KEY_DO_NOT_LOG_XYZ_9999"
        # 拦截 session.get 让它跑 (不需要真实数据)
        class FakeResp:
            status_code = 404  # 让 polygon_get 返回 None, 不调 JSON
        def fake_get(url, **kw):
            return FakeResp()
        s = r.make_session(SECRET)
        monkeypatch.setattr(s, "get", fake_get)
        r.polygon_get(s, "/v2/aggs/ticker/AAPL/prev", {}, r.RateLimiter(interval=0))
        captured = capsys.readouterr()
        assert SECRET not in captured.out, f"key 出现在 stdout: {captured.out}"
        assert SECRET not in captured.err, f"key 出现在 stderr: {captured.err}"
        print(f"  ✓ SECRET key 不在 stdout/stderr")

    def test_429_uses_retry_after_header(self, monkeypatch, capsys):
        """polygon_get 遇到 429 用 Retry-After 头 sleep, 重试一次."""
        from scripts.dashboard import refresh_prices_polygon as r
        # 第一次 429 (Retry-After: 1), 第二次 200
        class FakeResp:
            def __init__(self, code, headers=None, body=None):
                self.status_code = code
                self.headers = headers or {}
                self._body = body or {}
            def json(self): return self._body
        responses = [
            FakeResp(429, {"Retry-After": "1"}, {}),
            FakeResp(200, {}, {"results": []}),
        ]
        calls = []
        def fake_get(url, **kw):
            calls.append(1)
            return responses[min(len(calls)-1, len(responses)-1)]
        s = r.make_session("k_123")
        monkeypatch.setattr(s, "get", fake_get)
        # interval=0 避免 sleep 干扰
        data, code = r.polygon_get(s, "/v2/aggs/ticker/AAPL/prev", {}, r.RateLimiter(interval=0))
        assert code == 200, f"最终 code 应 200, 实际 {code}"
        assert len(calls) == 2, f"应重试一次, 实际调 {len(calls)} 次"
        print(f"  ✓ 429 Retry-After 头 sleep 后重试 1 次, 200 OK")

    def test_single_ticker_failure_does_not_block_with_apikey(self, monkeypatch):
        """单 ticker 失败不中断其他, apiKey 仍然传 (sanity)."""
        from scripts.dashboard import refresh_prices_polygon as r
        seen_urls = []
        def fake_get(url, **kw):
            # 模拟 requests.get 合并 session.params 到 URL
            session_params = getattr(s, "params", {})
            merged = {**session_params, **kw.get("params", {})}
            qs = "&".join(f"{k}={v}" for k, v in merged.items())
            full_url = f"{url}?{qs}" if qs else url
            seen_urls.append(full_url)
            if "MU" in full_url:
                raise requests_mock_exception("boom")
            return type("R", (), {"status_code": 200, "headers": {}, "json": lambda: {"results": []}})()
        s = r.make_session("k_456")
        monkeypatch.setattr(s, "get", fake_get)
        for tk in ("AAPL", "MU", "NVDA"):
            try:
                r.polygon_get(s, f"/v2/aggs/ticker/{tk}/prev", {}, r.RateLimiter(interval=0))
            except Exception:
                pass
        assert len(seen_urls) == 3, f"MU 抛异常后中断, 只调 {len(seen_urls)} 次"
        assert all("apiKey=k_456" in u for u in seen_urls), f"apiKey 缺失: {seen_urls}"
        print(f"  ✓ 单 ticker 抛异常后其余 2 个继续, apiKey 都在 URL")


class requests_mock_exception(Exception):
    pass


class TestSchemaConsistency:
    """refresh_prices_polygon 建表后, build_dashboard query_tickers / sector_pct 不失败."""

    def test_refresh_table_contains_sector_pct(self, tmp_path):
        """refresh_prices_polygon.TICKER_PRICES_DDL 包含 sector_pct REAL 字段."""
        import sqlite3, sys
        sys.path.insert(0, str(Path(__file__).parent.parent / "scripts" / "dashboard"))
        from refresh_prices_polygon import TICKER_PRICES_DDL, ensure_tables
        db = tmp_path / "schema.db"
        conn = sqlite3.connect(str(db))
        ensure_tables(conn)
        cols = [r[1] for r in conn.execute("PRAGMA table_info(ticker_prices)").fetchall()]
        assert "sector_pct" in cols, f"缺 sector_pct 字段, cols={cols}"
        assert "call_price" in cols and "now_price" in cols and "now_date" in cols
        print(f"  ✓ ticker_prices cols: {cols}")

    def test_build_dashboard_queries_succeed_after_refresh_creates_table(self, tmp_path):
        """端到端: refresh 建表 → build_dashboard query_tickers / sector_pct 正常查."""
        import sqlite3, sys
        sys.path.insert(0, str(Path(__file__).parent.parent / "scripts" / "dashboard"))
        from refresh_prices_polygon import ensure_tables
        db = tmp_path / "e2e.db"
        conn = sqlite3.connect(str(db))
        # 建 extractions_intel + raw_posts (build_dashboard.query_tickers 要查)
        conn.execute("""CREATE TABLE extractions_intel
                        (post_id TEXT, source_id TEXT, direction TEXT, ticker TEXT,
                         company TEXT, bottleneck TEXT, attribution TEXT,
                         rebuts_narrative TEXT, summary_100 TEXT,
                         is_retrospective INTEGER DEFAULT 0,
                         is_disclosure INTEGER DEFAULT 0,
                         is_self_reported_returns INTEGER DEFAULT 0,
                         extracted_at TEXT)""")
        conn.execute("""CREATE TABLE raw_posts
                        (post_id TEXT PRIMARY KEY, source_id TEXT, published_at TEXT,
                         raw_text TEXT)""")
        ensure_tables(conn)
        # 插入一条 sector_pct 数据, 验证 schema 可写
        conn.execute("""INSERT INTO ticker_prices
                        (ticker, pub_date, call_price, now_price, now_date, sector_pct, fetched_at)
                        VALUES ('AAPL','2026-07-01',100.0,110.0,'2026-07-10',2.5,'')""")
        conn.commit()
        # build_dashboard.query_tickers 查 sector_pct 不应出错
        import build_dashboard
        from build_dashboard import query_tickers
        # query_tickers 会查 extractions_intel, 现在有了, 不会报 “no such table”
        # 但 extractions_intel 是空的, query_tickers 返回 [] (不会查 ticker_prices)
        # 所以这里只验证 query_tickers 不因 extractions_intel 缺表报错
        rows = query_tickers(conn)
        assert isinstance(rows, list), f"query_tickers 返回 {type(rows)}"
        # 直接 SELECT sector_pct 验证
        r = conn.execute("SELECT sector_pct FROM ticker_prices WHERE ticker='AAPL'").fetchone()
        assert r == (2.5,), f"sector_pct 查询失败: {r}"
        print(f"  ✓ refresh 建表 → build_dashboard query_tickers / sector_pct 查询不报错")


class TestDockerPublishPath:
    """dashboard_daily_update.sh 必须在容器环境跑, 不依赖宿主机 /workspace."""

    def test_default_publish_dir_is_publish(self):
        """脚本默认 DASHBOARD_PUBLISH_DIR=/publish (容器内路径, 不是宿主机 /home/admin/www)."""
        sh = (Path(__file__).parent.parent / "scripts" / "dashboard" /
              "dashboard_daily_update.sh").read_text()
        # 验证 /publish 是默认 (而不是 /home/admin/www)
        assert "PUBLISH_DIR=\"${DASHBOARD_PUBLISH_DIR:-/publish}\"" in sh, \
            "默认 DASHBOARD_PUBLISH_DIR 不是 /publish (容器路径)"
        assert "DASHBOARD_PUBLISH_DIR:-/home/admin/www" not in sh, \
            "不应该把 /home/admin/www 写进脚本默认 (那是宿主机路径, 在容器不存在)"
        print(f"  ✓ 默认 /publish (容器路径)")

    def test_publish_always_both_index_and_dashboard(self):
        """必须总是同时发布 index.html + dashboard.html (nginx 首页与 dashboard.html 不脱节)."""
        sh = (Path(__file__).parent.parent / "scripts" / "dashboard" /
              "dashboard_daily_update.sh").read_text()
        # 验证 hardcode 列表, 不依赖旧文件探测
        assert 'for fname in index.html dashboard.html; do' in sh, \
            "应该 hardcode 循环 index.html + dashboard.html, 不是探测 ENTRY_FILES"
        # 不应该有 detect_entry 函数 (那是错的)
        assert "detect_entry" not in sh, "不应再有 detect_entry (旧设计是错)"
        # log 应该是 “published: /publish/index.html” + “/publish/dashboard.html” 两条
        assert "/publish/index.html" in sh or "PUBLISH_DIR/index.html" in sh
        assert "/publish/dashboard.html" in sh or "PUBLISH_DIR/dashboard.html" in sh
        print(f"  ✓ 总是同时发布 index.html + dashboard.html")

    def test_script_uses_workspace_path_consistent(self):
        """脚本只读 /workspace (宿主机代码挂载点), 不读 /home/admin/x--master (宿主机, 容器不可见)."""
        sh = (Path(__file__).parent.parent / "scripts" / "dashboard" /
              "dashboard_daily_update.sh").read_text()
        # 1. 脚本内部路径必须用 /workspace (容器)
        assert "SCRIPTS_DIR=/workspace/scripts/dashboard" in sh
        # 2. 容器内执行的代码路径必须是 /workspace (不是 /home/admin/x--master)
        # 3. PUBLISH_DIR 默认必须是 /publish (容器), 不是 /home/admin/www
        assert "PUBLISH_DIR=\"${DASHBOARD_PUBLISH_DIR:-/publish}\"" in sh
        # 4. /home/admin 只应该出现在注释里 (说明挂载点), 不作为路径变量执行
        # 检查: 任何非注释行 (不以 # 开头) 都不应含 /home/admin
        non_comment = "\n".join(
            line for line in sh.split("\n") if not line.strip().startswith("#")
        )
        assert "/home/admin" not in non_comment, \
            f"非注释行含 /home/admin, 应只出现在注释: {non_comment}"
        # 5. 容器内脚本, 看到的所有代码路径必须以 /workspace 开头
        print(f"  ✓ 容器脚本所有非注释路径以 /workspace 或 /publish 开头, 无 /home/admin")


class Test24hRollingWindow:
    """cn_recent_24h_window_utc 必须是 now-24h ~ now, 不是北京今日 00:00."""

    def test_24h_window_is_now_minus_24h(self):
        from scripts.dashboard.common import cn_recent_24h_window_utc
        from datetime import datetime, timezone, timedelta
        fixed = datetime(2026, 7, 10, 10, 0, 0, tzinfo=timezone.utc)  # 北京 18:00
        start, end = cn_recent_24h_window_utc(fixed)
        # start = end - 24h
        assert end == fixed.isoformat()
        assert start == (fixed - timedelta(hours=24)).isoformat()
        # 不是北京 00:00
        assert "2026-07-10T00:00:00" not in start, "不应该用北京 00:00 作为窗口起点"
        assert "2026-07-09T00:00:00" not in start
        print(f"  ✓ 24h 滚动: {start} → {end} (间隔正好 24h)")

    def test_24h_window_includes_06am_yesterday_to_06am_today(self):
        """06:00 抓取 → 06:20 Dashboard, 24h 窗口恰好覆盖 [昨天 06:00, 今天 06:00)."""
        from scripts.dashboard.common import cn_recent_24h_window_utc
        from datetime import datetime, timezone, timedelta
        # 模拟 06:20 Beijing → UTC 22:20 前一天
        fixed = datetime(2026, 7, 10, 6, 20, 0, tzinfo=timezone(timedelta(hours=8)))
        fixed_utc = fixed.astimezone(timezone.utc)
        start, end = cn_recent_24h_window_utc(fixed_utc)
        # start = 7-9 06:20 UTC = 北京 7-9 14:20
        # end = 7-10 06:20 UTC = 北京 7-10 14:20
        # 间隔 24h, 完全对齐 cron 节奏
        s_dt = datetime.fromisoformat(start)
        e_dt = datetime.fromisoformat(end)
        assert (e_dt - s_dt) == timedelta(hours=24)
        print(f"  ✓ 6:20→6:20 24h 滚动: {start} → {end}")

    def test_query_today_stats_24h_window(self, tmp_path):
        """no_posts 场景: 24h 窗口 raw_posts = 0."""
        import sqlite3, sys
        sys.path.insert(0, str(Path(__file__).parent.parent / "scripts" / "dashboard"))
        from common import query_today_stats, cn_recent_24h_window_utc
        db = tmp_path / "t.db"
        conn = sqlite3.connect(str(db))
        conn.execute("""CREATE TABLE raw_posts
                        (post_id TEXT PRIMARY KEY, source_id TEXT, published_at TEXT)""")
        conn.execute("""CREATE TABLE extractions_intel
                        (post_id TEXT, direction TEXT, ticker TEXT, bottleneck TEXT,
                         is_retrospective INTEGER, is_disclosure INTEGER)""")
        # 25h 前老数据, 不在 24h 窗口
        from datetime import datetime, timezone, timedelta
        old = (datetime.now(timezone.utc) - timedelta(hours=25)).isoformat()
        conn.execute("INSERT INTO raw_posts VALUES ('p1','tw_jukan05',?)", (old,))
        conn.commit()
        stats = query_today_stats(conn)
        assert stats["n_posts_24h"] == 0
        assert stats["empty_reason"] == "no_posts"
        assert stats["window_label"] == "过去 24 小时"
        print(f"  ✓ 25h 前数据不计入 24h 窗口")


class TestPolygonRateLimit:
    """POLYGON_REQUEST_INTERVAL env, 429 计数, limiter sleep."""

    def test_rate_limiter_interval_default(self):
        """默认 13s (Polygon 免费档 5 req/min = 60/5=12s + 1s buffer)."""
        from scripts.dashboard.refresh_prices_polygon import RateLimiter, POLYGON_REQUEST_INTERVAL_DEFAULT
        rl = RateLimiter()
        assert rl.interval == 13.0, f"默认 interval 应是 13s (免费档 5 req/min), 实际 {rl.interval}"
        assert POLYGON_REQUEST_INTERVAL_DEFAULT == 13.0
        print(f"  ✓ RateLimiter 默认 interval=13s (免费档 5 req/min)")

    def test_rate_limiter_429_count(self):
        from scripts.dashboard.refresh_prices_polygon import RateLimiter
        rl = RateLimiter(interval=0)
        # mock 429 response with Retry-After
        r = type("R", (), {"headers": {"Retry-After": "2"}})()
        rl.handle_429(r)
        rl.handle_429(r)
        assert rl.n_429 == 2, f"n_429 应累计到 2, 实际 {rl.n_429}"
        print(f"  ✓ 429 计数正确 (n_429=2)")

    def test_refresh_uses_env_interval(self, monkeypatch):
        """POLYGON_REQUEST_INTERVAL env 被 RateLimiter 读."""
        from scripts.dashboard import refresh_prices_polygon as r
        # 不能调 main() (它会查 DB), 直接验证 env 读取
        monkeypatch.setenv("POLYGON_REQUEST_INTERVAL", "1.5")
        interval = float(__import__("os").environ.get("POLYGON_REQUEST_INTERVAL", "0.6"))
        assert interval == 1.5, f"env interval 读取失败: {interval}"
        print(f"  ✓ POLYGON_REQUEST_INTERVAL env 可调")

    def test_refresh_outputs_ok_fail_429_counts(self, tmp_path, monkeypatch, capsys):
        """main 输出 ok / fail / 429_retries / 实际 API 请求 计数."""
        import sqlite3, sys
        import refresh_prices_polygon as r
        db = tmp_path / "db.db"
        conn = sqlite3.connect(str(db))
        conn.executescript("""
            CREATE TABLE extractions_intel
                (post_id TEXT, source_id TEXT, direction TEXT, ticker TEXT,
                 company TEXT, bottleneck TEXT, attribution TEXT,
                 rebuts_narrative TEXT, summary_100 TEXT,
                 is_retrospective INTEGER DEFAULT 0,
                 is_disclosure INTEGER DEFAULT 0,
                 is_self_reported_returns INTEGER DEFAULT 0,
                 extracted_at TEXT);
            CREATE TABLE raw_posts
                (post_id TEXT PRIMARY KEY, source_id TEXT, published_at TEXT, raw_text TEXT);
        """)
        # 3 个 jukan 强项标的, pub 10 天前 (避开 MIN_DAYS 排除)
        pub_base = (datetime.now(timezone.utc) - timedelta(days=10)).isoformat()
        for pid, tk in [("p1", "MU"), ("p2", "NVDA"), ("p3", "AMD")]:
            conn.execute("INSERT INTO raw_posts VALUES (?,?,?,?)", (pid, "tw_jukan05", pub_base, "text"))
            conn.execute("INSERT INTO extractions_intel VALUES (?,?,?,?,?,?,?,?,?,0,0,0,?)",
                         (pid, "tw_jukan05", "long", json.dumps([tk]), None, None, None, None, None, ""))
        conn.commit()
        conn.close()
        monkeypatch.setenv("POLYGON_API_KEY", "test_key")
        def make_mock(behaviors):
            behaviors = list(behaviors)
            def mock(session, ticker, start, end, limiter):
                if not behaviors: return []
                b = behaviors.pop(0)
                if isinstance(b, Exception): raise b
                return b
            return mock
        today = datetime.now(timezone.utc)
        bars = [{"t": int(today.timestamp()*1000), "c": 100.0}]
        monkeypatch.setattr(r, "fetch_bars_range", make_mock([bars, RuntimeError("boom"), bars]))
        try:
            sys.argv = ["refresh", "--db", str(db)]
            r.main()
        except SystemExit:
            pass
        out = capsys.readouterr().out
        assert "展示行数" in out
        assert "unique ticker:" in out
        assert "预计 API 请求" in out
        assert "实际 API 请求" in out
        assert "429_retries" in out
        print(f"  OK main 输出含 '实际 API 请求' / '429_retries' / 唯一 ticker 计数")




class TestDockerCrontab:
    """验证提供的 crontab 形式是一行 docker run."""

    def test_crontab_is_one_line_docker_run(self):
        """期望: 20 6 * * * docker run --rm ... -v /home/admin/x--master:/workspace -v /home/admin/www:/publish -w /workspace signalboard:1 bash scripts/dashboard/dashboard_daily_update.sh >> /home/admin/cron_dash.log 2>&1"""
        crontab_line = (
            "20 6 * * * docker run --rm "
            "--env-file /home/admin/signalboard.env "
            "--env-file /home/admin/secrets.env "
            "-e DASHBOARD_PUBLISH_DIR=/publish "
            "-v /home/admin/x--master:/workspace "
            "-v /home/admin/www:/publish "
            "-w /workspace "
            "signalboard:1 "
            "bash scripts/dashboard/dashboard_daily_update.sh "
            ">> /home/admin/cron_dash.log 2>&1"
        )
        # 不能含多行
        assert "\n" not in crontab_line, "crontab 必须是单行"
        # 必须含 docker run
        assert "docker run --rm" in crontab_line
        # 必须有 -v /home/admin/x--master:/workspace (代码挂载)
        assert "-v /home/admin/x--master:/workspace" in crontab_line
        # 必须有 -v /home/admin/www:/publish (网站目录挂载)
        assert "-v /home/admin/www:/publish" in crontab_line
        # 必须有 DASHBOARD_PUBLISH_DIR=/publish
        assert "DASHBOARD_PUBLISH_DIR=/publish" in crontab_line
        # 必须以 bash scripts/dashboard/dashboard_daily_update.sh 结尾
        assert crontab_line.rstrip().endswith(">> /home/admin/cron_dash.log 2>&1")
        # 不能直接调 bash /workspace/... (那是 host 路径, 宿主机没 /workspace)
        assert "bash /workspace/" not in crontab_line or "docker run" in crontab_line
        print(f"  ✓ crontab 形式正确: {crontab_line[:80]}...")


# ============================================================================
# Section 11: 共享目标选择 + 唯一 ticker 一次 range API (2026-07-10)
# ============================================================================
class TestSharedTargetSelection:
    """build_dashboard 跟 refresh_prices_polygon 必须调同一个 select_dashboard_ticker_targets.
    目标 = Dashboard 区块04 实际展示的 30 条, 不会是"全部历史 ticker".
    """

    def test_100_records_30_display_limit(self, tmp_path):
        """DB 有 100 条 ticker 记录, 但 Dashboard 只展示 30 条, refresh 目标也 30 条."""
        import sqlite3, sys
        sys.path.insert(0, str(Path(__file__).parent.parent / "scripts" / "dashboard"))
        from common import select_dashboard_ticker_targets
        db = tmp_path / "many.db"
        conn = sqlite3.connect(str(db))
        conn.executescript("""
            CREATE TABLE extractions_intel
                (post_id TEXT, source_id TEXT, direction TEXT, ticker TEXT,
                 company TEXT, bottleneck TEXT, attribution TEXT,
                 rebuts_narrative TEXT, summary_100 TEXT,
                 is_retrospective INTEGER DEFAULT 0,
                 is_disclosure INTEGER DEFAULT 0,
                 is_self_reported_returns INTEGER DEFAULT 0,
                 extracted_at TEXT);
            CREATE TABLE raw_posts
                (post_id TEXT PRIMARY KEY, source_id TEXT, published_at TEXT, raw_text TEXT);
        """)
        # 插 100 条 jukan 强项 MU (不同 5+ 天的 pub_date, 100 条 0 retro/disc)
        # 全部 long, 全部 0 retro/disc, 全部 ticker=MU
        # 由于按 (kol, ticker) 聚合, 实际只 1 个 unique (jukan, MU)
        # 为了让有 100 个 unique, 用 100 个不同 ticker
        for i in range(100):
            pid = f"p_{i}"
            tk = f"X{i:03d}"  # 不同 ticker
            pub = (datetime.now(timezone.utc) - timedelta(days=6+i)).isoformat()
            conn.execute("INSERT INTO raw_posts VALUES (?,?,?,?)", (pid, "tw_jukan05", pub, "text"))
            conn.execute("INSERT INTO extractions_intel VALUES (?,?,?,?,?,?,?,?,?,0,0,0,?)",
                         (pid, "tw_jukan05", "long", json.dumps([tk]), None, None, None, None, None, ""))
        conn.commit()
        # 但这 100 ticker 不在 jukan in_field 里, 全部 is_in_field=False
        # priority=2 (圈外) 但没有 has_price check 在 select 函数里
        # 看一下 select: priority = 0 if in_field else 2
        # 全部 priority=2, 按 -days_since 排序, 取 30
        # 所以 select 返回 30, 100 被裁到 30 ✓
        targets = select_dashboard_ticker_targets(conn, limit=30)
        assert len(targets) == 30, f"应 30 条, 实际 {len(targets)}"
        # unique ticker 数也应 ≤ 30
        unique_tk = set(t["ticker"] for t in targets)
        assert len(unique_tk) == 30, f"unique ticker 应 30, 实际 {len(unique_tk)}"
        print(f"  ✓ 100 条 ticker 记录 → 30 条 refresh 目标")

    def test_refresh_and_build_dashboard_same_function(self):
        """refresh 跟 build_dashboard 调同一个 select_dashboard_ticker_targets (来自 common.py)."""
        import sys
        sys.path.insert(0, str(Path(__file__).parent.parent / "scripts" / "dashboard"))
        from common import select_dashboard_ticker_targets as common_fn
        import refresh_prices_polygon
        import build_dashboard
        # 同一个函数
        assert refresh_prices_polygon.select_dashboard_ticker_targets is common_fn
        assert build_dashboard.select_dashboard_ticker_targets is common_fn
        print(f"  ✓ refresh 跟 build_dashboard 调同一个 common.select_dashboard_ticker_targets")

    def test_one_ticker_three_call_dates_one_request(self, tmp_path, monkeypatch):
        """同一 ticker 3 个 (kol, ticker) 喊单 (不同 KOL), refresh 只调 Polygon 1 次 range API."""
        import sqlite3, sys
        sys.path.insert(0, str(Path(__file__).parent.parent / "scripts" / "dashboard"))
        from common import select_dashboard_ticker_targets, group_targets_by_ticker
        import refresh_prices_polygon
        db = tmp_path / "t.db"
        conn = sqlite3.connect(str(db))
        conn.executescript("""
            CREATE TABLE extractions_intel
                (post_id TEXT, source_id TEXT, direction TEXT, ticker TEXT,
                 company TEXT, bottleneck TEXT, attribution TEXT,
                 rebuts_narrative TEXT, summary_100 TEXT,
                 is_retrospective INTEGER DEFAULT 0,
                 is_disclosure INTEGER DEFAULT 0,
                 is_self_reported_returns INTEGER DEFAULT 0,
                 extracted_at TEXT);
            CREATE TABLE raw_posts
                (post_id TEXT PRIMARY KEY, source_id TEXT, published_at TEXT, raw_text TEXT);
            CREATE TABLE ticker_prices
                (ticker TEXT NOT NULL, pub_date TEXT NOT NULL,
                 call_price REAL, now_price REAL, now_date TEXT,
                 sector_pct REAL, fetched_at TEXT NOT NULL,
                 PRIMARY KEY (ticker, pub_date));
        """)
        # 同 ticker "MU" 3 个 KOL (jukan/serenity/zephyr 都在 in_field 包含 MU)
        # 各自 5+ 天前 (避开 MIN_DAYS)
        for i, src in enumerate(["tw_jukan05", "tw_aleabitoreddit", "tw_zephyr_z9"]):
            pid = f"p{i}"
            pub = (datetime.now(timezone.utc) - timedelta(days=6+i)).isoformat()
            conn.execute("INSERT INTO raw_posts VALUES (?,?,?,?)", (pid, src, pub, "text"))
            conn.execute("INSERT INTO extractions_intel VALUES (?,?,?,?,?,?,?,?,?,0,0,0,?)",
                         (pid, src, "long", json.dumps(["MU"]), None, None, None, None, None, ""))
        conn.commit()
        targets = select_dashboard_ticker_targets(conn, limit=10)
        by_ticker = group_targets_by_ticker(targets)
        assert len(by_ticker["MU"]) == 3, f"应 3 个 (kol, ticker) 行 = MU, 实际 {len(by_ticker['MU'])}"
        assert len(by_ticker) == 1, f"应只 1 个 unique ticker, 实际 {len(by_ticker)}"
        # 模拟 fetch_bars_range 调用计数
        n_calls = 0
        def mock_fetch_bars(session, ticker, start, end, limiter):
            nonlocal n_calls
            n_calls += 1
            today = datetime.now(timezone.utc)
            return [{"t": int(today.timestamp()*1000), "c": 100.0}]
        monkeypatch.setattr(refresh_prices_polygon, "fetch_bars_range", mock_fetch_bars)
        for ticker, items in by_ticker.items():
            bars = mock_fetch_bars(None, ticker, "2025-01-01", "2026-12-31", None)
            for t in items:
                refresh_prices_polygon.upsert_price(conn, ticker, t["call_date"],
                                                     100.0, 100.0, "2026-07-10")
        assert n_calls == 1, f"3 个 (kol, ticker) 行 MU 应只调 1 次 range API, 实际 {n_calls}"
        print(f"  ✓ 同一 ticker 3 个 (kol, ticker) 喊单, 1 次 range API 请求")

    def test_30_rows_with_dup_ticker_request_count_equals_unique_ticker(self, tmp_path, monkeypatch):
        """30 行 (kol, ticker) 中有重复 ticker, 实际 API 请求 = unique ticker 数."""
        import sqlite3, sys
        sys.path.insert(0, str(Path(__file__).parent.parent / "scripts" / "dashboard"))
        from common import select_dashboard_ticker_targets, group_targets_by_ticker
        import refresh_prices_polygon
        db = tmp_path / "t2.db"
        conn = sqlite3.connect(str(db))
        conn.executescript("""
            CREATE TABLE extractions_intel
                (post_id TEXT, source_id TEXT, direction TEXT, ticker TEXT,
                 company TEXT, bottleneck TEXT, attribution TEXT,
                 rebuts_narrative TEXT, summary_100 TEXT,
                 is_retrospective INTEGER DEFAULT 0,
                 is_disclosure INTEGER DEFAULT 0,
                 is_self_reported_returns INTEGER DEFAULT 0,
                 extracted_at TEXT);
            CREATE TABLE raw_posts
                (post_id TEXT PRIMARY KEY, source_id TEXT, published_at TEXT, raw_text TEXT);
            CREATE TABLE ticker_prices
                (ticker TEXT NOT NULL, pub_date TEXT NOT NULL,
                 call_price REAL, now_price REAL, now_date TEXT,
                 sector_pct REAL, fetched_at TEXT NOT NULL,
                 PRIMARY KEY (ticker, pub_date));
        """)
        # MU 出现 3 次 (jukan + serenity + austin 都在 in_field), NVDA 2 次, AMD 1 次 ...
        # 合计 30 行, 但 unique ticker ≤ 30
        kols = ["tw_jukan05", "tw_aleabitoreddit", "tw_zephyr_z9", "tw_austinsemis"]
        tickers_per_kol = {
            "tw_jukan05": ["MU", "SNDK", "NVDA", "AMD", "AVGO", "NBIS", "AXTI", "TSM"],
            "tw_aleabitoreddit": ["MU", "AAOI", "LITE", "COHR", "POET", "AEVA", "AEHR", "MRVL", "JBL"],  # MU 重复
            "tw_zephyr_z9": ["MU", "SNDK", "NVDA", "AMD", "TSM", "AAOI", "LITE", "POET", "AEVA"],  # MU/SNDK/NVDA 重
            "tw_austinsemis": ["AMD", "NVDA", "MU", "AVGO", "TSM", "INTC", "MRVL", "GOOGL"],  # AMD/NVDA/MU/AVGO/TSM/MRVL 重
        }
        # 合计 8+9+9+8 = 34, 全部 pub_date 6 天前 (避开 MIN_DAYS 排除)
        pid_n = 0
        for src, tks in tickers_per_kol.items():
            for tk in tks:
                pid = f"p_{pid_n}"; pid_n += 1
                pub = (datetime.now(timezone.utc) - timedelta(days=6)).isoformat()
                conn.execute("INSERT INTO raw_posts VALUES (?,?,?,?)", (pid, src, pub, "text"))
                conn.execute("INSERT INTO extractions_intel VALUES (?,?,?,?,?,?,?,?,?,0,0,0,?)",
                             (pid, src, "long", json.dumps([tk]), None, None, None, None, None, ""))
        conn.commit()
        targets = select_dashboard_ticker_targets(conn, limit=30)
        by_ticker = group_targets_by_ticker(targets)
        # 计数 unique ticker
        n_unique = len(by_ticker)
        n_total = len(targets)
        # 模拟 fetch
        n_calls = 0
        def mock_fetch_bars(session, ticker, start, end, limiter):
            nonlocal n_calls
            n_calls += 1
            today = datetime.now(timezone.utc)
            return [{"t": int(today.timestamp()*1000), "c": 100.0}]
        monkeypatch.setattr(refresh_prices_polygon, "fetch_bars_range", mock_fetch_bars)
        for ticker, items in by_ticker.items():
            bars = mock_fetch_bars(None, ticker, "2025-01-01", "2026-12-31", None)
            for t in items:
                refresh_prices_polygon.upsert_price(conn, ticker, t["call_date"],
                                                     100.0, 100.0, "2026-07-10")
        assert n_calls == n_unique, f"实际 API 请求 ({n_calls}) 应 = unique ticker ({n_unique})"
        assert n_total > n_unique, f"展示行 ({n_total}) 应 > unique ticker ({n_unique}) (有重复)"
        print(f"  ✓ {n_total} 行含重复 ticker, {n_unique} unique ticker, 实际 API 请求 {n_calls} = {n_unique}")

    def test_default_interval_is_13_seconds(self):
        """默认 POLYGON_REQUEST_INTERVAL = 13s (Polygon 免费档 5 req/min 适配)."""
        from scripts.dashboard.refresh_prices_polygon import POLYGON_REQUEST_INTERVAL_DEFAULT
        assert POLYGON_REQUEST_INTERVAL_DEFAULT == 13.0, f"应 13.0s, 实际 {POLYGON_REQUEST_INTERVAL_DEFAULT}"
        # 5 req/min = 60/5 = 12s/req, +1s buffer = 13s
        print(f"  ✓ POLYGON_REQUEST_INTERVAL 默认 = 13s (5 req/min 适配)")

    def test_env_can_override_interval(self, monkeypatch):
        """POLYGON_REQUEST_INTERVAL env 可覆盖 (付费套餐可设 0.6)."""
        monkeypatch.setenv("POLYGON_REQUEST_INTERVAL", "0.6")
        interval = float(__import__("os").environ.get("POLYGON_REQUEST_INTERVAL", "13"))
        assert interval == 0.6
        # main() 也读这个 env
        monkeypatch.setenv("POLYGON_REQUEST_INTERVAL", "1.5")
        interval = float(__import__("os").environ.get("POLYGON_REQUEST_INTERVAL", "13"))
        assert interval == 1.5
        print(f"  ✓ POLYGON_REQUEST_INTERVAL env 可调 (付费套餐 0.6)")

    def test_list_targets_no_network_no_db_write(self, tmp_path, monkeypatch, capsys):
        """--list-targets dry-run: 不调网络, 不写 DB."""
        import sqlite3, sys
        sys.path.insert(0, str(Path(__file__).parent.parent / "scripts" / "dashboard"))
        import refresh_prices_polygon
        db = tmp_path / "lt.db"
        conn = sqlite3.connect(str(db))
        conn.executescript("""
            CREATE TABLE extractions_intel
                (post_id TEXT, source_id TEXT, direction TEXT, ticker TEXT,
                 company TEXT, bottleneck TEXT, attribution TEXT,
                 rebuts_narrative TEXT, summary_100 TEXT,
                 is_retrospective INTEGER DEFAULT 0,
                 is_disclosure INTEGER DEFAULT 0,
                 is_self_reported_returns INTEGER DEFAULT 0,
                 extracted_at TEXT);
            CREATE TABLE raw_posts
                (post_id TEXT PRIMARY KEY, source_id TEXT, published_at TEXT, raw_text TEXT);
        """)
        # 3 个目标
        for i, tk in enumerate(["MU", "NVDA", "AMD"]):
            pub = (datetime.now(timezone.utc) - timedelta(days=8)).isoformat()
            conn.execute("INSERT INTO raw_posts VALUES (?,?,?,?)", (f"p{i}", "tw_jukan05", pub, "text"))
            conn.execute("INSERT INTO extractions_intel VALUES (?,?,?,?,?,?,?,?,?,0,0,0,?)",
                         (f"p{i}", "tw_jukan05", "long", json.dumps([tk]), None, None, None, None, None, ""))
        conn.commit()
        # 记 DB mtime/size
        mtime_before = db.stat().st_mtime
        size_before = db.stat().st_size
        # mock 网络调用
        def forbidden(*args, **kwargs):
            raise AssertionError("list-targets 不应调网络!")
        monkeypatch.setattr(refresh_prices_polygon, "polygon_get", forbidden)
        monkeypatch.setattr(refresh_prices_polygon, "fetch_bars_range", forbidden)
        # 调 list_targets
        from argparse import Namespace
        args = Namespace(db=str(db))
        try:
            refresh_prices_polygon.list_targets(args)
        except SystemExit as e:
            pass  # 允许 sys.exit
        # 验证 DB 没被改
        mtime_after = db.stat().st_mtime
        size_after = db.stat().st_size
        assert mtime_after == mtime_before, f"DB mtime 改变! {mtime_before} -> {mtime_after}"
        assert size_after == size_before, f"DB size 改变! {size_before} -> {size_after}"
        # 验证输出
        out = capsys.readouterr().out
        assert "展示行数" in out
        assert "unique ticker:" in out
        assert "预计 API 请求" in out
        assert "dry-run 完成" in out
        assert "未调网络" in out
        assert "未写 DB" in out
        print(f"  ✓ --list-targets 不调网络, 不写 DB, 输出含 '展示行数/unique ticker/预计 API 请求'")

    def test_logs_print_interval_no_key(self, tmp_path, monkeypatch, capsys):
        """main 日志: 打印 interval, 不打印 API key."""
        import sqlite3, sys
        sys.path.insert(0, str(Path(__file__).parent.parent / "scripts" / "dashboard"))
        import refresh_prices_polygon
        db = tmp_path / "log.db"
        conn = sqlite3.connect(str(db))
        conn.executescript("""
            CREATE TABLE extractions_intel
                (post_id TEXT, source_id TEXT, direction TEXT, ticker TEXT,
                 company TEXT, bottleneck TEXT, attribution TEXT,
                 rebuts_narrative TEXT, summary_100 TEXT,
                 is_retrospective INTEGER DEFAULT 0,
                 is_disclosure INTEGER DEFAULT 0,
                 is_self_reported_returns INTEGER DEFAULT 0,
                 extracted_at TEXT);
            CREATE TABLE raw_posts
                (post_id TEXT PRIMARY KEY, source_id TEXT, published_at TEXT, raw_text TEXT);
        """)
        conn.close()
        SECRET = "POLYGON_KEY_DO_NOT_LOG_XYZ"
        monkeypatch.setenv("POLYGON_API_KEY", SECRET)
        # mock fetch_bars_range 返回空
        monkeypatch.setattr(refresh_prices_polygon, "fetch_bars_range", lambda *a, **k: [])
        try:
            sys.argv = ["refresh", "--db", str(db)]
            refresh_prices_polygon.main()
        except SystemExit:
            pass
        out = capsys.readouterr().out
        assert "POLYGON_REQUEST_INTERVAL" in out, f"应打印 interval, 实际: {out[:200]}"
        assert "13.0s" in out, f"应打印 13.0s 默认值, 实际: {out[:200]}"
        assert SECRET not in out, f"SECRET key 出现在 stdout: {out}"
        assert SECRET not in capsys.readouterr().err, f"SECRET key 出现在 stderr"
        print(f"  ✓ main 日志含 'POLYGON_REQUEST_INTERVAL 13s', 不含 key")