import gzip
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


def preview_db(tmp_path: Path) -> Path:
    target = tmp_path / "signalboard.db"
    with gzip.open(ROOT / "data" / "signalboard.db.gz", "rb") as src:
        target.write_bytes(src.read())
    return target


def test_research_clue_contract_and_zero_ai(tmp_path):
    module = load_module(ROOT / "scripts" / "intel_research_clue_preview.py", "clue_preview")
    report = module.build(preview_db(tmp_path))
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


def test_clue_timeline_preserves_evidence_layers_and_author_evolution(tmp_path):
    module = load_module(ROOT / "scripts" / "intel_research_clue_preview.py", "clue_preview_layers")
    clues = module.build(preview_db(tmp_path))["clues"]
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
    clue_module = load_module(ROOT / "scripts" / "intel_research_clue_preview.py", "clue_preview_html_data")
    build_module = load_module(ROOT / "scripts" / "dashboard" / "build_research_clue_preview.py", "clue_preview_html")
    out_dir = tmp_path / "outputs"
    report = clue_module.build(preview_db(tmp_path))
    clue_module.validate(report)
    data_path = out_dir / "research_clues.json"
    out_dir.mkdir()
    data_path.write_text(json.dumps(report, ensure_ascii=False), encoding="utf-8")
    output = tmp_path / "index.html"
    build_module.render(
        data_path,
        ROOT / "scripts" / "dashboard" / "research_clue_preview.template.html",
        output,
    )
    html = output.read_text(encoding="utf-8")
    assert "Today's Research Clues" in html
    assert "CLUE TIMELINE" in html
    assert "AUTHOR THESIS EVOLUTION" in html
    assert "AI RESEARCH VIEW" in html
    assert "#clue/" in html
    assert "#author/" in html
    assert "#theme/" in html
    assert "TOP INVESTMENT OPPORTUNITIES" not in html
    assert "FOCUSED ODDS REVIEW" not in html
    assert "BUY_CANDIDATE" not in html
    assert "Bear Fair Value" not in html


def test_synthesizer_has_no_openai_dependency():
    source = (ROOT / "scripts" / "intel_research_clue_preview.py").read_text(encoding="utf-8")
    assert "from openai" not in source
    assert "import openai" not in source
    assert "call_json(" not in source
    assert "OPENAI_CALLS = 0" in source
