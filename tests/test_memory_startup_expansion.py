from datetime import date
import importlib.util
from pathlib import Path


SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "expand_memory_startup_discovery.py"
if not SCRIPT.exists():
    SCRIPT = Path(__file__).with_name("expand_memory_startup_discovery.py")
spec = importlib.util.spec_from_file_location("memory_startup_expansion", SCRIPT)
e = importlib.util.module_from_spec(spec)
assert spec and spec.loader
spec.loader.exec_module(e)


def test_timing_tiers_do_not_treat_late_calls_as_pioneers():
    assert e.timing_tier(date(2025, 6, 30)) == ("startup_discoverer", 1.0)
    assert e.timing_tier(date(2025, 7, 1)) == ("early_confirmer", 0.7)
    assert e.timing_tier(date(2025, 9, 11)) == ("early_confirmer", 0.7)
    assert e.timing_tier(date(2025, 9, 12)) == ("trend_confirmer", 0.4)


def test_search_slices_cover_gaps_but_skip_august():
    covered = {d.month for start, end in e.SEARCH_SLICES
               for d in (start, end)}
    assert {3, 4, 5, 6, 7, 9, 10} <= covered
    assert 8 not in covered
    assert len(e.SEARCH_SLICES) * len(e.QUERY_FAMILIES) * e.MAX_ITEMS_SLICE \
        + len(e.TARGET_HANDLES) * e.MAX_ITEMS_TARGET <= 2000


def test_timing_adjustment_preserves_eligibility_but_downweights_late():
    candidates = [
        {"handle": "early", "passes_evidence_gate": True, "discovery_score": 10,
         "first_evidence_date": "2025-05-01"},
        {"handle": "late", "passes_evidence_gate": True, "discovery_score": 20,
         "first_evidence_date": "2025-10-01"},
    ]
    adjusted = {c["handle"]: c for c in e.add_timing(candidates)}
    assert adjusted["late"]["passes_evidence_gate"] is True
    assert adjusted["late"]["timing_adjusted_score"] == 8.0
    assert adjusted["early"]["timing_adjusted_score"] == 10.0
