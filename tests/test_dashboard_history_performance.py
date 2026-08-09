import json
import sqlite3
from pathlib import Path


ROOT = Path(__file__).parent.parent
DASH = ROOT / "scripts" / "dashboard"


def test_template_has_history_filters_pagination_and_performance():
    html = (DASH / "dashboard.template.html").read_text(encoding="utf-8")
    assert 'id="summary-date"' in html
    assert 'id="feed-kol"' in html
    assert 'id="feed-pager"' in html
    assert 'id="perf-kol"' in html
    assert 'id="perf-window"' in html
    assert 'id="stance-window"' in html
    assert "__CALL_PERFORMANCE__" in html
    assert "directional_return" in html
    assert "综合等权方向收益" in html


def test_query_call_performance_long_and_short(monkeypatch):
    import sys
    import types
    monkeypatch.setitem(sys.modules, "requests", types.SimpleNamespace())
    sys.path.insert(0, str(DASH))
    import build_dashboard as bd

    con = sqlite3.connect(":memory:")
    con.executescript("""
        CREATE TABLE raw_posts (
            post_id TEXT PRIMARY KEY, source_id TEXT, published_at TEXT
        );
        CREATE TABLE extractions_intel (
            post_id TEXT, source_id TEXT, direction TEXT, ticker TEXT,
            bottleneck TEXT, is_retrospective INTEGER, is_disclosure INTEGER
        );
        CREATE TABLE ticker_prices (
            ticker TEXT, pub_date TEXT, call_price REAL, now_price REAL,
            now_date TEXT, PRIMARY KEY(ticker, pub_date)
        );
    """)
    for pid, direction, ticker in [("p1", "long", "MU"), ("p2", "short", "NVDA")]:
        con.execute("INSERT INTO raw_posts VALUES (?, 'tw_jukan05', '2099-07-01T00:00:00+00:00')", (pid,))
        con.execute("INSERT INTO extractions_intel VALUES (?, 'tw_jukan05', ?, ?, NULL, 0, 0)",
                    (pid, direction, json.dumps([ticker])))
        con.execute("INSERT INTO ticker_prices VALUES (?, '2099-07-01', 100, 110, '2099-07-10')", (ticker,))
    out = bd.query_call_performance(con)
    by_ticker = {r["ticker"]: r for r in out}
    assert by_ticker["MU"]["directional_return"] == 10.0
    assert by_ticker["NVDA"]["directional_return"] == -10.0


def test_summary_generator_preserves_daily_history():
    src = (DASH / "intel_gen_summaries.py").read_text(encoding="utf-8")
    assert "load_daily_history()" in src
    assert 'summaries["daily_history"][archive_date]' in src


def test_performance_price_targets_include_recent_calls(monkeypatch):
    import sys
    sys.path.insert(0, str(DASH))
    import common

    con = sqlite3.connect(":memory:")
    con.executescript("""
        CREATE TABLE raw_posts (
            post_id TEXT PRIMARY KEY, source_id TEXT, published_at TEXT
        );
        CREATE TABLE extractions_intel (
            post_id TEXT, source_id TEXT, direction TEXT, ticker TEXT,
            bottleneck TEXT, is_retrospective INTEGER, is_disclosure INTEGER
        );
        INSERT INTO raw_posts VALUES
            ('p1', 'tw_jukan05', datetime('now')),
            ('p2', 'tw_jukan05', datetime('now', '-10 days'));
        INSERT INTO extractions_intel VALUES
            ('p1', 'tw_jukan05', 'long', '["MU","NVDA"]', NULL, 0, 0),
            ('p2', 'tw_jukan05', 'short', '["MU"]', NULL, 0, 0);
    """)
    targets = common.select_call_performance_targets(con)
    keys = {(row["ticker"], row["call_date"]) for row in targets}
    first_mu = con.execute("SELECT substr(datetime('now','-10 days'),1,10)").fetchone()[0]
    assert ("MU", first_mu) in keys
    assert len(keys) == 2
    mu = next(row for row in targets if row["ticker"] == "MU")
    assert mu["direction"] == "short"
    assert mu["n_calls"] == 2


def test_merge_price_targets_deduplicates_ticker_and_date():
    import sys
    sys.path.insert(0, str(DASH))
    import common

    row = {"ticker": "MU", "call_date": "2026-07-27"}
    merged = common.merge_price_targets([row], [dict(row)])
    assert merged == [row]


def test_performance_uses_first_call_once_per_person_and_ticker(monkeypatch):
    import sys
    import types
    monkeypatch.setitem(sys.modules, "requests", types.SimpleNamespace())
    sys.path.insert(0, str(DASH))
    import build_dashboard as bd

    con = sqlite3.connect(":memory:")
    con.executescript("""
        CREATE TABLE raw_posts (post_id TEXT PRIMARY KEY, source_id TEXT, published_at TEXT);
        CREATE TABLE extractions_intel (
            post_id TEXT, source_id TEXT, direction TEXT, ticker TEXT,
            bottleneck TEXT, is_retrospective INTEGER, is_disclosure INTEGER
        );
        CREATE TABLE ticker_prices (
            ticker TEXT, pub_date TEXT, call_price REAL, now_price REAL,
            now_date TEXT, PRIMARY KEY(ticker, pub_date)
        );
        INSERT INTO raw_posts VALUES
            ('p1','tw_austinsemis','2099-07-01T00:00:00+00:00'),
            ('p2','tw_austinsemis','2099-07-05T00:00:00+00:00'),
            ('p3','tw_austinsemis','2099-07-09T00:00:00+00:00');
        INSERT INTO extractions_intel VALUES
            ('p1','tw_austinsemis','long','["AMD"]',NULL,0,0),
            ('p2','tw_austinsemis','long','["AMD"]',NULL,0,0),
            ('p3','tw_austinsemis','short','["AMD"]',NULL,0,0);
        INSERT INTO ticker_prices VALUES ('AMD','2099-07-01',100,120,'2099-07-10');
    """)
    out = bd.query_call_performance(con)
    assert len(out) == 1
    assert out[0]["direction"] == "long"
    assert out[0]["call_date"] == "2099-07-01"
    assert out[0]["n_mentions"] == 3
    assert out[0]["directional_return"] == 20.0


def test_summary_generator_uses_flash_and_structured_prompts():
    src = (DASH / "intel_gen_summaries.py").read_text(encoding="utf-8")
    assert 'DEEPSEEK_MODEL = "deepseek-v4-flash"' in src
    assert "市场主线｜" in src
    assert "共识方向｜" in src
    assert "核心方向｜" in src


def test_zero_performance_price_coverage_blocks_publish(monkeypatch):
    import sys
    import types
    monkeypatch.setitem(sys.modules, "requests", types.SimpleNamespace())
    sys.path.insert(0, str(DASH))
    import build_dashboard as bd
    import pytest

    with pytest.raises(RuntimeError, match="行情覆盖为 0"):
        bd.validate_call_performance_coverage([
            {"call_price": None, "now_price": None},
            {"call_price": None, "now_price": None},
        ])
    bd.validate_call_performance_coverage([
        {"call_price": 100, "now_price": 101},
        {"call_price": None, "now_price": None},
    ])
