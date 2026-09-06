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
    assert all(x["source_terms"] for x in clues)


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


def test_preview_html_is_research_first_and_preserves_raw_intelligence(tmp_path):
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
    assert "今天有什么值得研究" in html
    assert "CLUE TIMELINE" in html
    assert "QUOTE CHAIN" in html
    assert "MEDIA EVIDENCE" in html
    assert "POSITIVE / NEGATIVE EXPOSURE" in html
    assert "AI RESEARCH VIEW" in html
    assert "/research-changes/" in html
    assert "/evidence/" in html
    assert "/posts/" in html
    assert "/tracking/" in html
    assert "/authors/" in html
    assert "/themes/" in html
    assert "/tickers/" in html
    assert "/admin/" in html
    assert "01&nbsp;&nbsp;今日线索" in html
    assert "02&nbsp;&nbsp;全部研究线" in html
    assert "05&nbsp;&nbsp;标的" in html
    assert "slice(0,7)" in html
    assert "View Original Posts" in html
    assert "View Original Post" in html
    assert "EVIDENCE VIEW" in html
    assert "ORIGINAL POST" in html
    assert "EXTRACTED CLAIMS" in html
    assert "COMPANY RESEARCH MAP" in html
    assert "href=\"/legacy/#feed-section\"" not in html
    assert "href=\"/legacy/#ai-cost\"" not in html
    assert "VALUATION UNDER AUDIT" not in html
    assert "/clues/" in html
    assert "STRICT CHRONOLOGICAL" in html
    assert "REPLY CONTEXT" in html
    assert "Recent Raw Posts" in html
    assert "TOP INVESTMENT OPPORTUNITIES" not in html
    assert "FOCUSED ODDS REVIEW" not in html
    assert "BUY_CANDIDATE" not in html
    assert "Bear Fair Value" not in html


def test_v162_product_home_and_evidence_are_integrated():
    template = (ROOT / "scripts" / "dashboard" / "research_clue_preview.template.html").read_text(encoding="utf-8")
    assert "grid-template-columns:190px minmax(0,1000px)" in template
    assert "<aside class=\"rail\"" not in template
    assert "WHY IT MATTERS" in template
    assert "EVIDENCE VIEW" in template
    assert "View Research Clue" in template
    assert "RELATED CLUE" in template
    assert "Company Research Map" not in template
    assert "COMPANY RESEARCH MAP" in template
    assert "AI COST GUARDRAILS" not in template
    assert "GOLDEN PASS" not in template
    assert "RESEARCH_CASE" not in template
    assert "DATABASE STATUS" not in template
    assert "TOP INVESTMENT OPPORTUNITIES" not in template
    audit_template = (ROOT / "scripts" / "dashboard" / "dashboard.template.html").read_text(encoding="utf-8")
    assert "LATEST RESEARCH CHANGES" not in audit_template
    assert 'href="#thesis-changes"' not in audit_template
    assert 'id="thesis-change-grid"' not in audit_template
    assert "renderLiveMeta();renderAiCostPanel();renderStance();renderFeed();renderTickers();renderKols();" in audit_template
    for section in ("market", "tracking", "feed-section", "people"):
        assert f'id="{section}"' in audit_template


def test_v163_evidence_routes_are_relevant_and_deduplicated():
    template = (ROOT / "scripts" / "dashboard" / "research_clue_preview.template.html").read_text(encoding="utf-8")
    assert "function evidenceIndex()" in template
    assert "function evidenceDetail(c,index)" in template
    assert "function sourceRelevance(c,source)" in template
    assert "const isDirectClueSource=" in template
    assert "function uniqueEvidenceRows()" in template
    assert "if(!isDirectClueSource(c,e))return" in template
    assert "Show ${omitted} Context Posts" in template
    assert "No directly related clue." in template
    assert "Evidence 回答“为什么这条证据重要”" in template
    assert "Raw Post 回答“作者实际发了什么”" in template
    assert "Research Clue Desk + Raw Intelligence" in template


def test_v163_direct_source_terms_reject_known_adjacent_theme_misroutes():
    clues = {c["clue_id"]: c for c in approved_report()["clues"]}

    def direct_ids(clue):
        terms = [x.lower() for x in clue["source_terms"]]
        result = []
        for event in clue["timeline"]:
            post = event.get("post", "")
            quoted = " ".join(x.get("text", "") for x in event.get("quoted_posts", []))
            claims = " ".join(event.get("claims", [])) if len(post) < 80 else ""
            hay = f"{post} {quoted} {claims}".lower()
            if any(term in hay for term in terms):
                result.append(event["post_url"].rsplit("/", 1)[-1])
        return result

    ymtc = direct_ids(clues["clue_ymtc_nand_wfe"])
    assert "2090779070523162841" in ymtc
    assert "2091525999666287061" in ymtc
    assert "2091327311882948875" not in ymtc  # generic AI-server / DRAM post
    assert "2094206602253570455" not in ymtc  # generic Korean DRAM export post

    legacy = direct_ids(clues["clue_legacy_dram"])
    assert "2094083798204047577" in legacy
    assert "2091707160162095210" not in legacy  # HBM4 pricing, not legacy DRAM

    assert all(direct_ids(clue) for clue in clues.values())


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
        tmp_path / "posts" / "index.html",
        tmp_path / "authors" / "index.html",
        tmp_path / "themes" / "index.html",
        tmp_path / "tickers" / "index.html",
        tmp_path / "tracking" / "index.html",
        tmp_path / "ai-usage" / "index.html",
        tmp_path / "admin" / "index.html",
    }
    assert set(outputs) == expected
    assert all(path.read_bytes() == outputs[0].read_bytes() for path in outputs)
    redirects = (tmp_path / "_redirects").read_text(encoding="utf-8")
    assert "/posts/* /posts/index.html 200" in redirects
    assert "/clues/* /index.html 200" in redirects


def test_unified_raw_exporter_is_zero_ai_and_preserves_old_features():
    source = (ROOT / "scripts" / "dashboard" / "build_unified_research_data.py").read_text(encoding="utf-8")
    assert "import openai" not in source
    assert "from openai" not in source
    assert '"openai_calls": 0' in source
    for feature in (
        "raw_posts", "author_posts", "quote_chain", "media", "research_changes",
        "tracking", "ticker_tracking", "recent_detail",
    ):
        assert f'"{feature}": True' in source
    assert "post_references" in source
    assert "media_assets" in source
    assert "raw_json" in source


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
    assert "python scripts/dashboard/build_unified_research_data.py" in workflow
    assert "dashboard_deploy_dist/data/raw-intelligence.json.gz" in workflow
    assert "dashboard_deploy_dist/posts/index.html" in workflow
    assert "dashboard_deploy_dist/tracking/index.html" in workflow
    assert "python scripts/intel_research_clue_preview.py" not in workflow
    assert 'ALLOW_EXPENSIVE_AI_JOB: "false"' in workflow


def test_original_signal_desk_remains_the_production_home():
    daily = (ROOT / ".github" / "workflows" / "signalboard-daily.yml").read_text(encoding="utf-8")
    rebuild = (ROOT / ".github" / "workflows" / "signalboard-history-rebuild.yml").read_text(encoding="utf-8")

    for workflow in (daily, rebuild):
        clue_build = workflow.index("python scripts/dashboard/build_research_clue_preview.py")
        restore_home = workflow.index(
            "cp scripts/dashboard/dashboard.html dashboard_deploy_dist/index.html",
            clue_build,
        )
        publish_home = workflow.index(
            "cp dashboard_deploy_dist/index.html dashboard.html",
            restore_home,
        )
        assert clue_build < restore_home < publish_home

    home = (ROOT / "dashboard_deploy_dist" / "index.html").read_text(encoding="utf-8")
    assert "SIGNAL DESK · 大V情报终端" in home
    assert 'id="market"' in home
    assert 'id="tracking"' in home
    assert 'id="feed-section"' in home
    assert 'id="people"' in home
    assert "综合等权方向收益" in home
    assert "SignalBoard · Unified Research Experience" not in home
