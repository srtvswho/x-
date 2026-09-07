"""A green subprocess is insufficient: the requested posts must be persisted."""
import importlib.util
import json
from pathlib import Path
import sqlite3
from types import SimpleNamespace

import pytest

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("history_runner", ROOT / "scripts/intel_history_backfill.py")
runner = importlib.util.module_from_spec(spec)
spec.loader.exec_module(runner)


@pytest.fixture
def db(tmp_path):
    path = tmp_path / "history.db"
    with sqlite3.connect(path) as con:
        con.executescript("""
            CREATE TABLE raw_posts(post_id TEXT, source_id TEXT, published_at TEXT);
            CREATE TABLE extractions_intel(post_id TEXT, prompt_version TEXT);
            INSERT INTO raw_posts VALUES
              ('old', 'tw_jukan05', '2025-01-01'),
              ('new', 'tw_jukan05', '2025-01-02');
        """)
    return path


def complete(db, *ids):
    with sqlite3.connect(db) as con:
        con.executemany("INSERT INTO extractions_intel VALUES (?, ?)",
                        [(pid, runner.PROMPT_VERSION) for pid in ids])


def test_zero_exit_with_no_persisted_posts_is_incomplete(db, tmp_path, monkeypatch):
    monkeypatch.setattr(runner.subprocess, "run", lambda *a, **kw: SimpleNamespace(returncode=0))
    output = tmp_path / "report.json"
    report = runner.run_backfill(db, 2, True, output)
    assert report["batch_status"] == "incomplete"
    assert report["resolved_this_run"] == 0
    assert report["unresolved_attempted_post_ids"] == ["old", "new"]
    assert json.loads(output.read_text()) == report


@pytest.mark.parametrize("outcome", [1, "interrupt", "unavailable"])
def test_partial_failure_keeps_report_and_resumes_only_missing(db, tmp_path, monkeypatch, outcome):
    output = tmp_path / "report.json"
    def execute(*a, **kw):
        assert json.loads(output.read_text())["batch_status"] == "running"
        complete(db, "old")
        if outcome == "interrupt":
            raise KeyboardInterrupt()
        if outcome == "unavailable":
            raise OSError("could not start")
        return SimpleNamespace(returncode=outcome)
    monkeypatch.setattr(runner.subprocess, "run", execute)
    report = runner.run_backfill(db, 2, True, output)
    assert report["batch_status"] == "incomplete"
    assert report["resolved_this_run"] == 1
    assert report["unresolved_attempted_post_ids"] == ["new"]
    assert runner.read_plan(db, 2)["selected_post_ids"] == ["new"]
    assert json.loads(output.read_text()) == report


def test_completed_batch_does_not_claim_all_history_complete(db, tmp_path, monkeypatch):
    def execute(*a, **kw):
        complete(db, "old")
        return SimpleNamespace(returncode=0)
    monkeypatch.setattr(runner.subprocess, "run", execute)
    report = runner.run_backfill(db, 1, True, tmp_path / "report.json")
    assert report["batch_status"] == "completed"
    assert report["pending_total"] == 1
    assert report["stored_history_extraction_complete"] is False
    assert report["history_complete"] is False


def test_completed_stored_extractions_do_not_prove_raw_coverage(db, tmp_path, monkeypatch):
    complete(db, "old", "new")
    monkeypatch.setattr(runner.subprocess, "run", lambda *a, **kw: pytest.fail("No API work expected"))
    report = runner.run_backfill(db, 2, True, tmp_path / "report.json")
    assert report["batch_status"] == "no_work"
    assert report["stored_history_extraction_complete"] is True
    assert report["history_complete"] is False


def test_planning_is_read_only_and_never_launches_extractor(db, tmp_path, monkeypatch):
    original = db.read_bytes()
    monkeypatch.setattr(runner.subprocess, "run", lambda *a, **kw: pytest.fail("Read-only plan"))
    report = runner.run_backfill(db, 2, False, tmp_path / "report.json")
    assert report["batch_status"] == "planned"
    assert report["attempted_post_ids"] == []
    assert report["resolved_this_run"] == 0
    assert db.read_bytes() == original
