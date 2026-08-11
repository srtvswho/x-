from datetime import date
import importlib.util
from pathlib import Path


SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "validate_memory_startup_expansion_candidates.py"
if not SCRIPT.exists():
    SCRIPT = Path(__file__).with_name("validate_memory_startup_expansion_candidates.py")
spec = importlib.util.spec_from_file_location("expansion_validation", SCRIPT)
v = importlib.util.module_from_spec(spec)
assert spec and spec.loader
spec.loader.exec_module(v)


def test_discovery_window_is_fully_excluded():
    assert v.DISCOVERY_EXCLUDED == (date(2025, 3, 1), date(2025, 10, 31))
    assert v.WINDOWS[0][1] < v.DISCOVERY_EXCLUDED[0]
    assert v.WINDOWS[1][0] > v.DISCOVERY_EXCLUDED[1]


def test_validation_is_capped_and_contains_only_new_candidates():
    assert len(v.CANDIDATES) == 6
    assert len(set(v.CANDIDATES)) == 6
    assert v.MAX_PER_AUTHOR_WINDOW == 180
    assert not ({"dgretta_author", "sam_badawi", "tradexwhisperer", "thevalueist"}
                & set(v.CANDIDATES))


def test_configure_changes_base_runtime_constants():
    v.configure()
    assert v.base.CANDIDATES == v.CANDIDATES
    assert v.base.WINDOWS == v.WINDOWS
    assert v.base.DISCOVERY_EXCLUDED == v.DISCOVERY_EXCLUDED
