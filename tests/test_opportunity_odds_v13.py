import copy
import json
import sqlite3

from scripts.dashboard.build_dashboard import query_opportunities
from scripts.intel_opportunity_odds_v13 import gate_config, normalize_analysis
from signalboard.db import CURRENT_SCHEMA_VERSION, init_db


def metric(value, label="CONSENSUS"):
    return {
        "value": value, "label": label, "fiscal_period": "FY2027", "as_of_date": "2026-08-31",
        "source_ids": ["s1"], "confidence": "MEDIUM", "currency": "USD",
    }


def analysis_fixture():
    market_metric = metric(100, "KNOWN")
    return {
        "market_data": {"current_price": market_metric},
        "earnings_bridge": {
            "consensus_revenue": metric(1000), "our_base_revenue": metric(1200, "AI_ESTIMATE"),
            "consensus_margin": {"value": 0.20}, "our_base_margin": {"value": 0.23},
            "consensus_eps": metric(5), "our_base_eps": metric(6.5, "AI_ESTIMATE"),
            "consensus_fcf": metric(None, "UNKNOWN"), "our_base_fcf": metric(None, "UNKNOWN"),
            "revenue_gap": None, "margin_gap": None, "eps_gap": None, "fcf_gap": None,
        },
        "scenarios": [
            {"name": "BEAR", "valuation_basis": 8, "fair_multiple": 10, "fair_value": 999, "probability": 0.25},
            {"name": "BASE", "valuation_basis": 6.5, "fair_multiple": 20, "fair_value": 999, "probability": 0.50},
            {"name": "BULL", "valuation_basis": 8, "fair_multiple": 20, "fair_value": 999, "probability": 0.25},
        ],
        "valuation_confidence": "MEDIUM", "thesis_confidence": "HIGH",
        "catalyst_within_18m": True, "invalidation_clear": True,
    }


def context_fixture(**overrides):
    data = {
        "actionability": "RESEARCH", "chain_completeness": 6, "thesis_quality_score": 80,
        "evidence_quality_score": 70, "catalyst_score": 70,
    }
    data.update(overrides)
    return data


def test_v10_schema_is_idempotent(tmp_path):
    db = tmp_path / "signalboard.db"
    init_db(db)
    init_db(db)
    con = sqlite3.connect(db)
    assert con.execute("PRAGMA user_version").fetchone()[0] == CURRENT_SCHEMA_VERSION == 10
    tables = {row[0] for row in con.execute("SELECT name FROM sqlite_master WHERE type='table'")}
    assert {"opportunity_odds", "opportunity_odds_runs"} <= tables
    con.close()


def test_deterministic_math_overrides_model_fair_values_and_passes_buy_gate():
    result = normalize_analysis(analysis_fixture(), context_fixture(), gate_config())
    computed = result["computed"]
    assert [x["fair_value"] for x in result["scenarios"]] == [80.0, 130.0, 160.0]
    assert computed["earnings_gap"] == 0.3
    assert computed["base_upside"] == 0.3
    assert computed["bear_downside"] == -0.2
    assert computed["reward_risk"] == 1.5
    assert computed["odds_status"] == "BUY_CANDIDATE"


def test_good_company_bad_odds_and_good_odds_weak_evidence_are_distinct():
    bad_odds = analysis_fixture()
    bad_odds["scenarios"][1]["valuation_basis"] = 5.25
    bad_odds["scenarios"][1]["fair_multiple"] = 20
    bad_odds["scenarios"][0]["valuation_basis"] = 7
    bad_odds["scenarios"][0]["fair_multiple"] = 10
    normalized = normalize_analysis(bad_odds, context_fixture(), gate_config())
    assert normalized["computed"]["odds_status"] == "GOOD_COMPANY_BAD_ODDS"

    low_confidence = copy.deepcopy(bad_odds)
    low_confidence["valuation_confidence"] = "LOW"
    normalized = normalize_analysis(low_confidence, context_fixture(), gate_config())
    assert normalized["computed"]["odds_status"] == "GOOD_COMPANY_BAD_ODDS"

    weak = analysis_fixture()
    weak["earnings_bridge"]["our_base_eps"]["value"] = 7
    weak["scenarios"][1]["valuation_basis"] = 7
    weak["scenarios"][1]["fair_multiple"] = 20
    normalized = normalize_analysis(weak, context_fixture(evidence_quality_score=40), gate_config())
    assert normalized["computed"]["odds_status"] == "GOOD_ODDS_WEAK_EVIDENCE"


def test_missing_reliable_scenario_data_is_explicitly_incomplete():
    data = analysis_fixture()
    data["scenarios"][0]["valuation_basis"] = None
    normalized = normalize_analysis(data, context_fixture(), gate_config())
    assert normalized["computed"]["odds_status"] == "VALUATION_INCOMPLETE"
    assert normalized["computed"]["bear_fair_value"] is None
    assert normalized["computed"]["odds_score"] is None


def test_dashboard_query_exposes_best_odds(tmp_path):
    db = tmp_path / "signalboard.db"
    init_db(db)
    con = sqlite3.connect(db)
    con.execute("INSERT INTO logic_chain_analyses(candidate_id,title,analysis_json,source_digest,model,discovery_type) VALUES ('c1','Chain','{}','d','m','SEEDED')")
    con.execute(
        """INSERT INTO investment_opportunities(
           opportunity_id,title,primary_company,direction,driver,actionability,chain_completeness,
           opportunity_score,thesis_quality_score,evidence_quality_score,earnings_impact_score,
           mispricing_score,catalyst_score,risk_reward_score,one_line_thesis,ai_verdict,source_candidate_id)
           VALUES ('o1','Opportunity','AAON','LONG','AI DC','RESEARCH',6,80,80,70,70,60,70,60,'Thesis','Verdict','c1')"""
    )
    payload = {
        "market_expectations": {"level": "HIGH"}, "market_data": {}, "earnings_bridge": {},
        "scenarios": [], "computed": {"buy_gate_blockers": ["base upside"]},
        "why_not_buy_now": "Price", "verdict": "Wait", "catalyst": "Quarter", "invalidation": "Orders fall",
        "data_gaps": [],
    }
    con.execute(
        """INSERT INTO opportunity_odds(
           odds_id,opportunity_id,ticker,company,currency,analysis_json,source_digest,model,prompt_version,
           as_of_date,current_price,bear_fair_value,base_fair_value,bull_fair_value,base_upside,
           bear_downside,reward_risk,earnings_gap,expectations_gap,odds_band,odds_score,odds_status,
           valuation_confidence,thesis_confidence)
           VALUES ('d1','o1','AAON','AAON','USD',?,'s','m','v','2026-08-31',100,80,120,150,.2,-.2,1,.1,'NEUTRAL','FAIR',55,'RESEARCH','MEDIUM','HIGH')""",
        (json.dumps(payload),),
    )
    con.commit()
    row = query_opportunities(con)[0]
    assert row["best_odds"]["ticker"] == "AAON"
    assert row["best_odds"]["base_upside"] == 0.2
    con.close()
