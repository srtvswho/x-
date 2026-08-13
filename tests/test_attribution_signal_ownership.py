import json
import sqlite3
import sys
from pathlib import Path


DASH = Path(__file__).parent.parent / "scripts" / "dashboard"
sys.path.insert(0, str(DASH))

import common  # noqa: E402


def _db():
    con = sqlite3.connect(":memory:")
    con.executescript("""
        CREATE TABLE raw_posts (
            post_id TEXT PRIMARY KEY, source_id TEXT, published_at TEXT,
            raw_text TEXT, raw_url TEXT
        );
        CREATE TABLE extractions_intel (
            post_id TEXT, source_id TEXT, direction TEXT, ticker TEXT,
            company TEXT, bottleneck TEXT, attribution TEXT,
            is_retrospective INTEGER DEFAULT 0,
            is_disclosure INTEGER DEFAULT 0
        );
    """)
    return con


def test_attribution_multiplier_separates_author_from_external_source():
    assert common.attribution_signal_multiplier("ORIGINAL") == 1.0
    assert common.attribution_signal_multiplier("ENDORSED") == 0.5
    assert common.attribution_signal_multiplier("DISAGREED") == 1.0
    assert common.attribution_signal_multiplier("RELAYED") == 0.0
    assert common.attribution_signal_multiplier("RC") == 0.0


def test_relayed_report_is_excluded_from_performance_events():
    con = _db()
    posts = [
        ("report", "RELAYED", ["CRWV", "NBIS", "LITE", "NV"], "Nvidia"),
        ("original", "ORIGINAL", ["MU"], "Micron"),
    ]
    for post_id, attribution, tickers, company in posts:
        con.execute(
            "INSERT INTO raw_posts VALUES (?, 'tw_jukan05', datetime('now','-10 days'), ?, '')",
            (post_id, f"{company} report"),
        )
        con.execute(
            "INSERT INTO extractions_intel VALUES (?, 'tw_jukan05', 'long', ?, ?, '存储', ?, 0, 0)",
            (post_id, json.dumps(tickers), company, attribution),
        )

    events = common.query_call_performance_events(con)
    assert {(row["post_id"], row["ticker"]) for row in events} == {("original", "MU")}


def test_endorsed_external_view_is_discounted_but_kept():
    con = _db()
    con.execute(
        "INSERT INTO raw_posts VALUES ('p1','tw_jukan05',datetime('now','-10 days'),'I agree: Nvidia bullish','')"
    )
    con.execute(
        "INSERT INTO extractions_intel VALUES ('p1','tw_jukan05','long','[\"NV\"]','Nvidia',NULL,'ENDORSED',0,0)"
    )
    events = common.query_call_performance_events(con)
    assert len(events) == 1
    assert events[0]["ticker"] == "NVDA"
    assert common.attribution_signal_multiplier("ENDORSED") == 0.5


def test_template_does_not_turn_relayed_direction_into_author_stance():
    html = (DASH / "dashboard.template.html").read_text(encoding="utf-8")
    assert "function attributionMultiplier" in html
    assert "function effectiveDirection" in html
    assert "if(attributionMultiplier(r)===0)return [];" in html
    assert "外部观点·不计作者方向" in html


def test_prompt_has_unambiguous_attribution_and_nvda_alias():
    prompt = (Path(__file__).parent.parent / "signalboard" / "extract" / "prompts_intel.py").read_text(encoding="utf-8")
    assert '"ENDORSED"' in prompt
    assert '"DISAGREED"' in prompt
    assert "Nvidia / NV 一律标准化为 NVDA" in prompt
