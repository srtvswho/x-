import json
import sqlite3
from pathlib import Path

from signalboard.db import CURRENT_SCHEMA_VERSION, init_db
from scripts.dashboard.build_dashboard import query_opportunities
from scripts.intel_opportunity_engine_v12 import _enforce_actionability


ROOT = Path(__file__).resolve().parents[1]


def _insert_candidate_and_opportunity(con: sqlite3.Connection) -> None:
    con.execute(
        "INSERT INTO logic_chain_analyses(candidate_id,title,analysis_json,source_digest,model,discovery_type) VALUES ('c1','Chain','{}','d','gpt-5.6-terra','SEEDED')"
    )
    con.execute(
        """INSERT INTO investment_opportunities(
           opportunity_id,title,primary_company,direction,time_horizon,driver,industry_change,bottleneck,
           earnings_mechanism,valuation_question,market_expectations,mispricing_hypothesis,actionability,
           chain_completeness,opportunity_score,thesis_quality_score,evidence_quality_score,
           earnings_impact_score,mispricing_score,catalyst_score,risk_reward_score,one_line_thesis,
           why_now,ai_verdict,next_trigger,social_mention_count,independent_evidence_count,source_candidate_id)
           VALUES ('o1','Memory Opportunity','MU','LONG','12m','AI demand','HBM mix','wafer','ASP to margin',
           'price in?','high','maybe','RESEARCH',5,77,80,70,85,55,65,60,'one line','now','research','filing',8,3,'c1')"""
    )
    con.commit()


def test_v8_schema_is_idempotent(tmp_path):
    db = tmp_path / "signalboard.db"
    init_db(db)
    init_db(db)
    con = sqlite3.connect(db)
    assert con.execute("PRAGMA user_version").fetchone()[0] == CURRENT_SCHEMA_VERSION == 8
    tables = {r[0] for r in con.execute("SELECT name FROM sqlite_master WHERE type='table'")}
    assert {"logic_chain_analyses", "investment_opportunities", "opportunity_evidence", "opportunity_versions"} <= tables
    con.close()


def test_query_opportunities_exposes_score_components(tmp_path):
    db = tmp_path / "signalboard.db"
    init_db(db)
    con = sqlite3.connect(db)
    _insert_candidate_and_opportunity(con)
    rows = query_opportunities(con)
    assert rows[0]["title"] == "Memory Opportunity"
    assert rows[0]["actionability"] == "RESEARCH"
    assert rows[0]["score_components"]["Earnings"] == 85
    con.close()


def test_actionability_cannot_outrun_completeness_or_valuation():
    row = {"chain_completeness": 4, "actionability": "BUY_CANDIDATE", "valuation": {"status": "COMPLETE"}}
    assert _enforce_actionability(row) == "WATCH"
    row = {"chain_completeness": 5, "actionability": "BUY_CANDIDATE", "valuation": {"status": "COMPLETE"}}
    assert _enforce_actionability(row) == "RESEARCH"
    row = {"chain_completeness": 6, "actionability": "BUY_CANDIDATE", "valuation": {"status": "VALUATION_INCOMPLETE"}}
    assert _enforce_actionability(row) == "RESEARCH"
    row = {"chain_completeness": 3, "actionability": "WATCH", "valuation": {"status": "PARTIAL"}}
    assert _enforce_actionability(row) == "THEME_ONLY"


def test_home_is_conclusion_first_and_single_column():
    html = (ROOT / "scripts/dashboard/dashboard.template.html").read_text(encoding="utf-8")
    assert html.index('id="opportunities"') < html.index('id="thesis-changes"') < html.index('id="alerts"')
    assert ".opportunity-stack{display:grid;grid-template-columns:1fr" in html
    assert ".thesis-change-grid{display:grid;grid-template-columns:1fr" in html
    assert "Admin · AI Cost Guardrails" in html
    assert "renderOpportunities()" in html
    assert "__OPPORTUNITIES__" in html


def test_completed_one_time_preview_workflows_are_removed():
    workflows = ROOT / ".github/workflows"
    assert not (workflows / "opportunity-engine-v12-preview.yml").exists()
    assert not (workflows / "opportunity-score-normalization-zero-ai.yml").exists()


def test_prompt_outputs_preserve_source_and_decision_fields():
    from scripts.intel_opportunity_engine_v12 import CHAIN_SCHEMA

    required = set(CHAIN_SCHEMA["required"])
    assert {"source_roots", "social_mention_count", "independent_evidence_count"} <= required
    assert {"earnings_mechanism", "valuation", "invalidation", "missing_evidence"} <= required
    assert CHAIN_SCHEMA["properties"]["chain_completeness"]["maximum"] == 6
