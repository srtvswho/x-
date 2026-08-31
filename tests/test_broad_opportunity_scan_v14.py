import json
import sqlite3
from types import SimpleNamespace

from signalboard.ai.guardrails import STAGE_BY_WORKLOAD
from signalboard.ai.router import DEFAULT_ROUTES
from signalboard.db import CURRENT_SCHEMA_VERSION, init_db
from scripts.intel_broad_opportunity_scan_v14 import (
    coverage_confidence,
    ensure_opportunity,
    persist_quick_map,
    plan,
    quick_category,
    update_pricing_status,
)
from scripts.dashboard.build_dashboard import query_broad_opportunity_scan


def chain_fixture():
    return {
        "candidate_id": "broad_test", "title": "AI power components",
        "theme": "AI Power", "authors": ["a"],
        "source_roots": [{"source_id": "r1", "title": "IR", "url": "https://example.com/ir", "publisher": "Company", "as_of_date": "2026-08-31", "finding": "Orders"}],
        "source_claim_ids": ["c1"], "social_mention_count": 2, "independent_evidence_count": 1,
        "driver": "AI capex", "industry_change": "power demand", "bottleneck": "components",
        "companies": [{"company": "Example", "ticker": "EXM", "mechanism": "orders"}],
        "earnings_mechanism": "orders to revenue and margin", "time_horizon": "12m",
        "counter_case": "capacity normalizes", "missing_evidence": ["backlog"],
        "chain_completeness": 5, "thesis_quality": 75, "evidence_quality": 68,
        "supported": True, "rejection_reason": "",
    }


def expression_fixture():
    source = {"source_id": "s1", "title": "IR", "url": "https://example.com/ir", "publisher": "Example", "as_of_date": "2026-08-31", "finding": "Guidance"}
    return {
        "ticker": "EXM", "company": "Example", "market": "NASDAQ", "currency": "USD",
        "accessibility": "US listed", "listing_type": "LOCAL", "expression_type": "UNDERFOLLOWED",
        "direction": "POSITIVE", "mechanism": "AI power orders", "revenue_mechanism": "orders convert to revenue",
        "current_price": 20, "market_cap": 1000, "forward_revenue_growth": .12, "forward_eps_growth": .2,
        "forward_pe": 15, "ev_ebitda": 10, "historical_multiple": "12–20x", "peer_multiple": "18x",
        "expectation_level": "MODERATE", "earnings_gap_estimate": .25, "valuation_level": "CHEAP",
        "quick_odds": "ATTRACTIVE", "confidence": "MEDIUM", "deep_research_required": True,
        "why": "Gap", "risks": ["customer concentration"], "as_of_date": "2026-08-31", "sources": [source],
    }


def test_v11_schema_and_routes_are_available(tmp_path):
    db = tmp_path / "db.sqlite"
    init_db(db); init_db(db)
    con = sqlite3.connect(db)
    assert con.execute("PRAGMA user_version").fetchone()[0] == CURRENT_SCHEMA_VERSION == 11
    tables = {r[0] for r in con.execute("SELECT name FROM sqlite_master WHERE type='table'")}
    assert {"beneficiary_maps", "security_expressions", "quick_odds", "deep_odds", "broad_opportunity_scan_runs"} <= tables
    con.close()
    for workload in ("broad_candidate_discovery", "beneficiary_quick_odds", "broad_deep_odds"):
        assert DEFAULT_ROUTES[workload][0:2] == ("openai", "gpt-5.6-terra")
        assert STAGE_BY_WORKLOAD[workload] == "analyst"


def test_coverage_confidence_requires_expression_type_breadth():
    assert coverage_confidence([{"expression_type": "PURE_PLAY"}] * 8) == "LOW"
    assert coverage_confidence([{"expression_type": "PURE_PLAY"}, {"expression_type": "UNDERFOLLOWED"}, {"expression_type": "UPSTREAM"}]) == "MEDIUM"
    rows = [{"expression_type": x} for x in ["PURE_PLAY", "UNDERFOLLOWED", "UPSTREAM", "SECOND_ORDER", "CHEAPER_ALTERNATIVE", "OBVIOUS_WINNER"]]
    assert coverage_confidence(rows) == "HIGH"


def test_quick_category_separates_thesis_strength_and_price():
    chain = chain_fixture()
    assert quick_category(chain, {"confidence": "MEDIUM", "valuation_level": "CHEAP"}) == "A_STRONG_CHEAP"
    assert quick_category(chain, {"confidence": "MEDIUM", "valuation_level": "EXPENSIVE"}) == "C_STRONG_EXPENSIVE"
    assert quick_category(chain, {"confidence": "LOW", "valuation_level": "CHEAP"}) == "F_INSUFFICIENT_DATA"


def test_opportunity_and_quick_map_persistence_is_idempotent(tmp_path):
    db = tmp_path / "db.sqlite"; init_db(db)
    con = sqlite3.connect(db); con.row_factory = sqlite3.Row; con.execute("PRAGMA foreign_keys=ON")
    chain = chain_fixture()
    con.execute("INSERT INTO logic_chain_analyses(candidate_id,title,analysis_json,source_digest,model,discovery_type) VALUES (?,?,?,?,?,'DISCOVERED')", (chain["candidate_id"], chain["title"], json.dumps(chain), "d", "m"))
    oid = ensure_opportunity(con, chain)
    assert oid == ensure_opportunity(con, chain)
    data = {
        "coverage_gaps": [], "best_business_ticker": "EXM", "best_technology_ticker": "EXM",
        "best_pure_play_ticker": "NONE", "best_odds_ticker": "EXM", "best_us_ticker": "EXM",
        "best_local_ticker": "EXM", "expressions": [expression_fixture()],
    }
    result = SimpleNamespace(model="gpt-5.6-terra", sources=[{"url": "https://example.com/ir"}])
    assert persist_quick_map(con, oid, chain, data, result, "pd")[0] == 1
    assert persist_quick_map(con, oid, chain, data, result, "pd")[0] == 1
    assert con.execute("SELECT COUNT(*) FROM security_expressions").fetchone()[0] == 1
    assert con.execute("SELECT COUNT(*) FROM quick_odds").fetchone()[0] == 1
    con.close()


def test_fully_priced_requires_high_coverage_and_exhaustion(tmp_path):
    db = tmp_path / "db.sqlite"; init_db(db)
    con = sqlite3.connect(db); con.row_factory = sqlite3.Row; con.execute("PRAGMA foreign_keys=ON")
    chain = chain_fixture(); con.execute("INSERT INTO logic_chain_analyses(candidate_id,title,analysis_json,source_digest,model,discovery_type) VALUES (?,?,?,?,?,'DISCOVERED')", (chain["candidate_id"], chain["title"], json.dumps(chain), "d", "m"))
    oid = ensure_opportunity(con, chain)
    con.execute("INSERT INTO beneficiary_maps(opportunity_id,coverage_confidence,analysis_json,source_digest,model,prompt_version) VALUES (?,'LOW','{}','d','m','v')", (oid,))
    con.commit(); update_pricing_status(con)
    assert con.execute("SELECT thesis_pricing_status FROM beneficiary_maps").fetchone()[0] == "NOT_EXHAUSTED"
    con.close()


def test_plan_is_zero_ai_and_bounded(tmp_path):
    db = tmp_path / "db.sqlite"; init_db(db)
    con = sqlite3.connect(db); con.row_factory = sqlite3.Row
    payload = plan(con, 15)
    assert payload["actual_api_calls"] == 0
    assert payload["hard_gates"] == {"run_budget_usd": 50, "daily_budget_usd": 75, "calls": 400, "expensive_jobs": False}
    con.close()


def test_dashboard_is_top_odds_first_and_exposes_coverage(tmp_path):
    html = open("scripts/dashboard/dashboard.template.html", encoding="utf-8").read()
    assert html.index("TOP ODDS") < html.index("RESEARCH CONTEXT")
    assert 'id="coverage-summary"' in html
    assert 'id="top-odds-body"' in html
    assert "__BROAD_SCAN__" in html
    db = tmp_path / "db.sqlite"; init_db(db)
    con = sqlite3.connect(db)
    report = {"coverage": {"security_expressions": 55}, "top_20_expressions": []}
    con.execute("INSERT INTO broad_opportunity_scan_runs(run_id,status,coverage_json,report_json) VALUES ('r','COMPLETED','{}',?)", (json.dumps(report),))
    con.commit()
    assert query_broad_opportunity_scan(con)["coverage"]["security_expressions"] == 55
    con.close()
