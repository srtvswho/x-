from datetime import date
import importlib.util
from pathlib import Path


SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "validate_memory_startup_candidates.py"
if not SCRIPT.exists():
    SCRIPT = Path(__file__).with_name("startup_light_validation.py")
spec = importlib.util.spec_from_file_location("memory_startup_light", SCRIPT)
p = importlib.util.module_from_spec(spec); assert spec and spec.loader; spec.loader.exec_module(p)


def test_discovery_window_is_hard_excluded():
    assert p.WINDOWS[0][1] < p.DISCOVERY_EXCLUDED[0]
    assert p.WINDOWS[1][0] > p.DISCOVERY_EXCLUDED[1]


def test_event_dedup_uses_21_days():
    def sig(day):
        return {"ticker": "MU", "direction": "long",
                "post": {"handle": "x", "date": day, "published_at": day + "T00:00:00Z"}}
    kept = p.dedup_events([sig("2025-01-01"), sig("2025-01-10"), sig("2025-02-01")])
    assert [x["post"]["date"] for x in kept] == ["2025-01-01", "2025-02-01"]


def test_ambiguous_assets_are_denied():
    assert {"BTC", "ETH", "GOLD"} <= p.DENY_TICKERS
