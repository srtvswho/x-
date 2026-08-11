from datetime import date

from scripts import discover_memory_top_kols as mod


def test_parse_datetime_supports_x_and_iso_formats():
    assert mod.parse_datetime("Wed Jun 10 08:30:00 +0000 2026").date() == date(2026, 6, 10)
    assert mod.parse_datetime("2026-06-10T08:30:00Z").date() == date(2026, 6, 10)


def test_normalize_post_uses_full_date_parser_and_stable_id():
    item = {
        "text": "$MU trimming here",
        "createdAt": "Wed Jun 10 08:30:00 +0000 2026",
        "author": {"userName": "Example", "followersCount": "1,234"},
        "likeCount": "25",
    }
    first = mod.normalize_post(item, "$MU trim")
    second = mod.normalize_post(item, "$MU trim")
    assert first["published_date"] == "2026-06-10"
    assert first["post_id"] == second["post_id"]
    assert first["followers"] == 1234


def test_event_uses_high_and_first_drawdown_confirmation():
    bars = [
        {"date": date(2026, 6, 1), "high": 100, "close": 99},
        {"date": date(2026, 6, 8), "high": 120, "close": 117},
        {"date": date(2026, 6, 9), "high": 119, "close": 110},
        {"date": date(2026, 6, 10), "high": 110, "close": 101},
    ]
    event = mod.define_event("MU", bars)
    assert event["peak_date"] == "2026-06-08"
    assert event["confirmation_date"] == "2026-06-10"


def test_apify_v3_run_object_and_v2_dict_are_supported():
    class Run:
        default_dataset_id = "dataset-v3"

    assert mod.dataset_id_from_run(Run()) == "dataset-v3"
    assert mod.dataset_id_from_run({"defaultDatasetId": "dataset-v2"}) == "dataset-v2"


def test_candidate_score_rewards_repeated_independent_evidence():
    row = {
        "post": {"published_date": "2026-06-01", "likes": 10, "reposts": 2},
        "classification": {
            "category": "advance_exit",
            "reasoning_quality": 2,
            "explicitness": 3,
        },
    }
    one = mod.candidate_score([row], [date(2026, 6, 20)])
    two = mod.candidate_score([row, row], [date(2026, 6, 20)])
    assert two > 2 * one
