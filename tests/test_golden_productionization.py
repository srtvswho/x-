from __future__ import annotations

import json
import sqlite3
from pathlib import Path

from scripts.intel_golden_revalidate_existing import revalidate
from scripts.intel_seed_existing_golden import seed


ROOT = Path(__file__).resolve().parent.parent


def test_archived_golden_seed_is_zero_ai_and_idempotent(tmp_path, monkeypatch):
    db = tmp_path / "golden.db"
    monkeypatch.setenv("AI_ENABLED", "false")
    monkeypatch.setenv("SEED_EXISTING_RESULTS_ONLY", "true")
    monkeypatch.setenv("AI_RUN_ID", "golden-productionization-test")

    first = seed(db)
    second = seed(db)
    assert first["openai_calls"] == 0
    assert first["openai_cost_usd"] == 0
    assert all(value == 0 for value in second["delta"].values())

    report = revalidate(db, timestamp="2026-08-31T00:00:00.000Z")
    assert report["summary"] == {"PASS": 2, "PARTIAL": 0, "FAIL": 0}
    case_a = next(row for row in report["results"] if row["case_id"].startswith("case_a_"))
    assert case_a["original_status"] == "PARTIAL"
    assert case_a["original_discrepancy"]["resolution"] == "validator now accepts CapEx | 资本开支"

    con = sqlite3.connect(db)
    assert con.execute("SELECT COUNT(*) FROM golden_validations WHERE status='PASS'").fetchone()[0] == 2
    assert con.execute("SELECT COUNT(*) FROM theses WHERE author_id='golden_case_consensus'").fetchone()[0] == 2
    assert con.execute("SELECT COUNT(*) FROM research_case_analyses").fetchone()[0] == 2
    assert con.execute("SELECT COUNT(*) FROM ai_usage_ledger WHERE provider='openai' AND status='SUCCESS'").fetchone()[0] == 0
    case_a_analysis = json.loads(con.execute(
        "SELECT analysis_json FROM research_case_analyses WHERE case_id='case_a_ymtc_nand_china_wfe'"
    ).fetchone()[0])
    assert any("5座新厂" in text for text in case_a_analysis["corrections"])
    case_b_analysis = json.loads(con.execute(
        "SELECT analysis_json FROM research_case_analyses WHERE case_id='case_b_abf_copos_cowop_pcb'"
    ).fetchone()[0])
    assert "条件性命题" in case_b_analysis["logic_chain"][2]
    con.close()
