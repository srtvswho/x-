import importlib.util
import sqlite3
from pathlib import Path


ROOT = Path(__file__).parent.parent


def load_extractor():
    spec = importlib.util.spec_from_file_location(
        "intel_extract_history_test", ROOT / "scripts" / "intel_extract.py"
    )
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def make_db():
    con = sqlite3.connect(":memory:")
    con.executescript("""
        CREATE TABLE raw_posts (
            post_id TEXT PRIMARY KEY,
            source_id TEXT,
            raw_text TEXT,
            published_at TEXT
        );
        CREATE TABLE extractions_intel (
            post_id TEXT,
            prompt_version TEXT
        );
        INSERT INTO raw_posts VALUES
            ('a1', 'tw_austinsemis', '$AMD looks attractive', '2025-09-01T00:00:00+00:00'),
            ('a2', 'tw_austinsemis', 'ordinary industry chat', '2025-10-01T00:00:00+00:00'),
            ('j1', 'tw_jukan05', 'MU supply remains tight', '2025-11-01T00:00:00+00:00'),
            ('z1', 'tw_zephyr_z9', '$NVDA update', '2026-06-01T00:00:00+00:00'),
            ('s1', 'tw_aleabitoreddit', '$AAOI long', '2025-12-01T00:00:00+00:00');
    """)
    return con


def test_ticker_clue_filter_accepts_cashtag_and_known_plain_ticker():
    mod = load_extractor()
    assert mod.has_ticker_clue("I like $CRDO here")
    assert mod.has_ticker_clue("MU supply remains tight")
    assert not mod.has_ticker_clue("ordinary industry chat")


def test_history_targets_obey_window_sources_clues_and_idempotency():
    mod = load_extractor()
    con = make_db()
    con.execute(
        "INSERT INTO extractions_intel VALUES (?, ?)",
        ("a1", mod.PROMPT_VERSION),
    )
    rows = mod.get_target_posts(
        con,
        "2025-08-11T00:00:00+00:00",
        until_iso="2026-05-28T00:00:00+00:00",
        source_ids=["tw_austinsemis", "tw_jukan05", "tw_zephyr_z9"],
        ticker_clues_only=True,
    )
    assert [row["post_id"] for row in rows] == ["j1"]


def test_workflow_backfill_is_one_time_cost_capped_and_flash_only():
    workflow = (ROOT / ".github" / "workflows" / "signalboard-daily.yml").read_text()
    extractor = (ROOT / "scripts" / "intel_extract.py").read_text()
    assert "[backfill-calls-1y]" in workflow
    assert "--sources tw_austinsemis,tw_jukan05,tw_zephyr_z9" in workflow
    assert "--ticker-clues-only" in workflow
    assert "--max-targets 650" in workflow
    assert 'DEEPSEEK_MODEL = "deepseek-v4-flash"' in extractor
    assert 'DEEPSEEK_MODEL = "deepseek-v4-pro"' not in extractor
