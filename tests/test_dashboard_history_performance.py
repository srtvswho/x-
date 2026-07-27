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
