import json
import sqlite3

from signalboard.ai.guardrails import STAGE_BY_WORKLOAD
from signalboard.ai.router import DEFAULT_ROUTES
from signalboard.db import CURRENT_SCHEMA_VERSION, init_db
from scripts.intel_focused_odds_v141 import (
    PROMPT_VERSION,
    UNIVERSE,
    normalize_review,
    plan,
)
from scripts.dashboard.build_dashboard import query_focused_odds


def snapshot(price=100):
    return {"market_metrics": [{"name": "current_price", "value": price}]}


def review(bear=80, base=135, bull=170, *, cyclical=False, normalized_eps=8, cagr=.18):
    def scenario(name, value, probability):
        return {"name": name, "fiscal_period": "FY2028", "valuation_basis": value / 10,
                "fair_multiple": 10, "fair_value": 999, "probability": probability}
    return {
        "scenarios": [scenario("BEAR", bear, .25), scenario("BASE", base, .5), scenario("BULL", bull, .25)],
        "earnings_bridge": [
            {"eps_base": 8, "eps_consensus": 8, "fcf_base": 100, "fcf_consensus": 100},
            {"eps_base": 9, "eps_consensus": 8.5, "fcf_base": 110, "fcf_consensus": 105},
            {"eps_base": 10, "eps_consensus": 9, "fcf_base": 120, "fcf_consensus": 110},
        ],
        "normalized_earnings": {"is_cyclical": cyclical, "normalized_eps": normalized_eps},
        "three_year_eps_or_fcf_cagr": cagr, "valuation_reasonable": True,
        "balance_sheet_strong": True, "roic_fcf_quality_strong": True,
        "valuation_confidence": "HIGH", "evidence_quality_score": 80,
        "thesis_quality_score": 80, "business_quality_score": 80,
        "catalysts": ["orders"], "invalidation": ["orders reverse"],
        "critical_data_missing": [],
    }


def test_v12_schema_and_terra_routes(tmp_path):
    db = tmp_path / "focused.sqlite"
    init_db(db); init_db(db)
    con = sqlite3.connect(db)
    assert con.execute("PRAGMA user_version").fetchone()[0] == CURRENT_SCHEMA_VERSION == 12
    tables = {x[0] for x in con.execute("SELECT name FROM sqlite_master WHERE type='table'")}
    assert {"focused_financial_snapshots", "focused_odds_reviews", "focused_odds_runs"} <= tables
    con.close()
    for workload in ("focused_financial_snapshot", "focused_odds_analysis"):
        assert DEFAULT_ROUTES[workload] == ("openai", "gpt-5.6-terra", "high")
        assert STAGE_BY_WORKLOAD[workload] == "analyst"


def test_plan_is_exactly_six_securities_twelve_calls_and_zero_ai():
    payload = plan()
    assert len(UNIVERSE) == 6
    assert payload["planned_calls"] == 12
    assert payload["actual_api_calls"] == 0
    assert payload["hard_gates"]["model"] == "gpt-5.6-terra"
    assert payload["hard_gates"]["expensive_jobs"] is False
    assert payload["hard_gates"]["run_budget_usd"] == 30


def test_path_a_passes_and_fair_values_are_recomputed():
    sec = next(x for x in UNIVERSE if x.ticker == "JBL")
    data = normalize_review(sec, snapshot(), review())
    assert data["scenarios"][1]["fair_value"] == 135
    assert data["computed"]["gate_paths"]["A"] is True
    assert data["computed"]["odds_status"] == "BUY_CANDIDATE"
    assert data["computed"]["attractive_entry_low"] <= data["computed"]["attractive_entry_high"]


def test_path_b_passes_with_tightly_controlled_bear():
    sec = next(x for x in UNIVERSE if x.ticker == "NVT")
    data = normalize_review(sec, snapshot(), review(bear=90, base=120, bull=145, cagr=.10))
    assert data["computed"]["gate_paths"] == {"A": False, "B": True, "C": False}
    assert data["computed"]["odds_status"] == "BUY_CANDIDATE"


def test_path_c_passes_compounder_but_cyclical_normalized_pe_can_block():
    jci = next(x for x in UNIVERSE if x.ticker == "JCI")
    compounder = normalize_review(jci, snapshot(), review(bear=80, base=112, bull=150, cagr=.18))
    assert compounder["computed"]["gate_paths"]["C"] is True
    mu = next(x for x in UNIVERSE if x.ticker == "MU")
    expensive_cycle = normalize_review(mu, snapshot(200), review(bear=160, base=270, bull=330, cyclical=True, normalized_eps=8))
    assert expensive_cycle["computed"]["normalized_pe"] == 25
    assert expensive_cycle["computed"]["normalized_earnings_gate"] is False
    assert expensive_cycle["computed"]["odds_status"] != "BUY_CANDIDATE"


def test_dashboard_has_focused_payload_placeholder():
    html = open("scripts/dashboard/dashboard.template.html", encoding="utf-8").read()
    assert "__FOCUSED_ODDS__" in html
    assert 'id="focused-odds-body"' in html


def test_focused_report_query_roundtrip(tmp_path):
    db = tmp_path / "focused.sqlite"; init_db(db)
    con = sqlite3.connect(db)
    report = {"status": "COMPLETED", "ranking": [{"ticker": "JBL"}]}
    con.execute("INSERT INTO focused_odds_runs(run_id,status,universe_json,report_json) VALUES ('r','COMPLETED','[]',?)", (json.dumps(report),))
    con.commit()
    assert query_focused_odds(con)["ranking"][0]["ticker"] == "JBL"
    con.close()
