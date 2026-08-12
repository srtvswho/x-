from __future__ import annotations

import sys
from datetime import date
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "scripts" / "dashboard"))
sys.path.insert(0, str(ROOT / "scripts"))

import common  # noqa: E402
import intel_incremental_scrape as scrape  # noqa: E402


EXPECTED = {
    "jukan", "serenity", "zephyr", "austin",
    "dgretta", "feroce", "tradex", "gsmferrari",
}


def test_production_registry_has_six_rated_and_two_role_validated():
    assert set(common.KOLS) == EXPECTED
    rated = {k for k, v in common.KOLS.items() if v["rating"] in {"A+", "B+", "B"}}
    role_validated = {k for k, v in common.KOLS.items() if v["rating"] == "专项通过"}
    assert rated == {"jukan", "serenity", "dgretta", "feroce", "tradex", "gsmferrari"}
    assert role_validated == {"zephyr", "austin"}
    assert common.KOLS["zephyr"]["shortWeight"] == 0.0
    assert common.KOLS["austin"]["consensusWeight"] < common.KOLS["austin"]["researchWeight"]


def test_scrape_registry_matches_dashboard_sources():
    scrape_sources = {row["source_id"] for row in scrape.KOL_TEST}
    assert scrape_sources == set(common.SRC2KOL)


def test_incremental_query_until_is_tomorrow_exclusive(monkeypatch):
    class FixedDate(date):
        @classmethod
        def today(cls):
            return cls(2026, 8, 11)

    monkeypatch.setattr(scrape, "date", FixedDate)
    monkeypatch.setattr(
        scrape,
        "get_incremental_state",
        lambda handle: {
            "exists": True,
            "last_tweet_id": "old",
            "last_tweet_published_at": "2026-08-10T15:42:04+00:00",
            "last_fetched_at": "2026-08-11T00:00:00Z",
        },
    )
    result = scrape.scrape_one_kol(scrape.KOL_TEST[0], "unused", dry_run=True)
    assert result["until"] == "2026-08-12"
