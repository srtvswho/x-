import importlib.util
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def load_module(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader
    spec.loader.exec_module(module)
    return module


def approved_report() -> dict:
    return json.loads(
        (ROOT / "outputs" / "research_clue_desk_v16" / "research_clues.json")
        .read_text(encoding="utf-8")
    )


def test_research_clue_contract_and_zero_ai():
    module = load_module(ROOT / "scripts" / "intel_research_clue_preview.py", "clue_preview")
    report = approved_report()
    checks = module.validate(report)
    clues = report["clues"]

    assert all(checks.values())
    assert report["openai_calls"] == 0
    assert report["openai_cost_usd"] == 0
    assert report["production_changed"] is False
    assert 8 <= len(clues) <= 15
    assert sum(x["timeline_completeness"] == "COMPLETE" for x in clues) >= 5
    assert sum(len(x["authors"]) >= 2 for x in clues) >= 3
    assert sum(x["media_evidence_count"] > 0 for x in clues) >= 3
    assert sum(x["independent_evidence_roots"] >= 2 for x in clues) >= 3
    assert any(x["status"] == "CONTRADICTED" for x in clues)
    assert all(x["additional_openai_calls"] == 0 for x in clues)


def test_clue_timeline_preserves_evidence_layers_and_author_evolution():
    clues = approved_report()["clues"]
    for clue in clues:
        assert clue["one_line_thesis"]
        assert clue["first_seen"] <= clue["last_updated"]
        assert clue["timeline"]
        assert clue["author_evolution"]
        assert clue["evidence_roots"]
        assert clue["what_to_research_next"]
        assert clue["clue_completeness"]["total"] == 6
        assert all(event["event_type"] in {
            "THESIS_ORIGIN", "NEW_EVIDENCE", "THESIS_EXPANSION", "CONFIDENCE_UP",
            "CONFIDENCE_DOWN", "NEW_RISK", "NEW_COMPANY", "CATALYST",
            "CONTRADICTION", "THESIS_UPDATE",
        } for event in clue["timeline"])
    assert any(any(event["media"] for event in clue["timeline"]) for clue in clues)
    assert any(any(event["quoted_posts"] for event in clue["timeline"]) for clue in clues)


def test_preview_html_is_research_first_and_has_hash_routes(tmp_path):
    build_module = load_module(ROOT / "scripts" / "dashboard" / "build_research_clue_preview.py", "clue_preview_html")
    data_path = ROOT / "outputs" / "research_clue_desk_v16" / "research_clues.json"
    output = tmp_path / "index.html"
    build_module.render(
        data_path,
        ROOT / "scripts" / "dashboard" / "research_clue_preview.template.html",
        output,
    )
    html = output.read_text(encoding="utf-8")
    assert "TODAY'S RESEARCH CLUES" in html
    assert "今日研究线索" in html
    assert "CLUE TIMELINE" in html
    assert "QUOTE CHAIN" in html
    assert "MEDIA EVIDENCE" in html
    assert "POSITIVE / NEGATIVE EXPOSURE" in html
    assert "AUTHOR THESIS EVOLUTION" in html
    assert "AI RESEARCH VIEW" in html
    assert "/research-changes/" in html
    assert "/evidence/" in html
    assert "/companies/" in html
    assert "/admin/" in html
    assert "01&nbsp;&nbsp;今日线索" in html
    assert "02&nbsp;&nbsp;全部研究线" in html
    assert "05&nbsp;&nbsp;标的" in html
    assert "function recommendedClues()" in html
    assert "return rows.slice(0,7)" in html
    assert "View Evidence" in html
    assert "View Timeline" in html
    assert "EVIDENCE DETAIL" in html
    assert "ORIGINAL CONTENT" in html
    assert "EXTRACTED FACTS" in html
    assert "COMPANY RESEARCH MAP" in html
    assert "href=\"/legacy/#feed-section\"" not in html
    assert "href=\"/legacy/#ai-cost\"" not in html
    assert "VALUATION UNDER AUDIT" not in html
    assert "#clue/" in html
    assert "#author/" in html
    assert "#theme/" in html
    assert "TOP INVESTMENT OPPORTUNITIES" not in html
    assert "FOCUSED ODDS REVIEW" not in html
    assert "BUY_CANDIDATE" not in html
    assert "Bear Fair Value" not in html


def test_v162_product_home_and_evidence_are_integrated():
    template = (ROOT / "scripts" / "dashboard" / "research_clue_preview.template.html").read_text(encoding="utf-8")
    assert "grid-template-columns:176px minmax(0,980px)" in template
    assert "<aside class=\"rail\"" not in template
    assert "WHY RECOMMENDED" in template
    assert "Evidence Detail" not in template
    assert "EVIDENCE DETAIL" in template
    assert "Back to Clue Detail" in template
    assert "RELATED CLUE" in template
    assert "Company Research Map" not in template
    assert "COMPANY RESEARCH MAP" in template
    assert "AI COST GUARDRAILS" not in template
    assert "GOLDEN PASS" not in template
    assert "RESEARCH_CASE" not in template
    assert "DATABASE STATUS" not in template
    assert "TOP INVESTMENT OPPORTUNITIES" not in template
    audit_template = (ROOT / "scripts" / "dashboard" / "dashboard.template.html").read_text(encoding="utf-8")
    assert "LATEST RESEARCH CHANGES" in audit_template


def test_v162_builds_all_product_routes(tmp_path):
    build_module = load_module(ROOT / "scripts" / "dashboard" / "build_research_clue_preview.py", "clue_routes")
    outputs = build_module.render_product_routes(
        ROOT / "outputs" / "research_clue_desk_v16" / "research_clues.json",
        ROOT / "scripts" / "dashboard" / "research_clue_preview.template.html",
        tmp_path,
    )
    expected = {
        tmp_path / "index.html",
        tmp_path / "research-clues" / "index.html",
        tmp_path / "research-changes" / "index.html",
        tmp_path / "evidence" / "index.html",
        tmp_path / "companies" / "index.html",
    }
    assert set(outputs) == expected
    assert all(path.read_bytes() == outputs[0].read_bytes() for path in outputs)


def test_synthesizer_has_no_openai_dependency():
    source = (ROOT / "scripts" / "intel_research_clue_preview.py").read_text(encoding="utf-8")
    assert "from openai" not in source
    assert "import openai" not in source
    assert "call_json(" not in source
    assert "OPENAI_CALLS = 0" in source


def test_daily_production_build_reuses_approved_artifact_only():
    workflow = (ROOT / ".github" / "workflows" / "signalboard-daily.yml").read_text(encoding="utf-8")
    assert "python scripts/dashboard/build_research_clue_preview.py" in workflow
    assert "dashboard_deploy_dist/legacy/index.html" in workflow
    assert "dashboard_deploy_dist/admin/index.html" in workflow
    assert "--deploy-root dashboard_deploy_dist" in workflow
    assert "dashboard_deploy_dist/evidence/index.html" in workflow
    assert "dashboard_deploy_dist/companies/index.html" in workflow
    assert "dashboard_deploy_dist/research-changes/index.html" in workflow
    assert "python scripts/intel_research_clue_preview.py" not in workflow
    assert 'ALLOW_EXPENSIVE_AI_JOB: "false"' in workflow
