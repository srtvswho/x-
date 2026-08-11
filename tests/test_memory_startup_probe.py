from datetime import timezone

import startup_probe as p


def test_parse_datetime_rfc_and_iso():
    assert p.parse_datetime("Wed Jun 25 12:00:00 +0000 2025").tzinfo == timezone.utc
    assert p.parse_datetime("2025-06-25T12:00:00Z").date().isoformat() == "2025-06-25"


def test_normalize_enforces_window_memory_and_retweet():
    base = {"id": "1", "author": {"userName": "Alpha"},
            "createdAt": "2025-06-25T12:00:00Z", "text": "$MU memory cycle is starting"}
    assert p.normalize_post(base, "q", "apify")["handle"] == "alpha"
    assert p.normalize_post({**base, "createdAt": "2026-06-25T12:00:00Z"}, "q", "apify") is None
    assert p.normalize_post({**base, "text": "RT @x $MU memory cycle", "isRetweet": True}, "q", "apify") is None


def test_candidate_gate_is_author_event_level():
    def row(pid, day, category, mechanism):
        return {"post": {"post_id": pid, "handle": "alpha", "published_at": day + "T00:00:00+00:00",
                         "date": day, "text": "x", "url": "u"},
                "classification": {"category": category, "original_judgment": True,
                                   "actionable": category == "early_long_action",
                                   "mechanism_present": mechanism, "explicitness": 2,
                                   "reasoning_quality": 2}}
    one_day = p.build_candidates([row("1", "2025-05-01", "early_cycle_call", True),
                                  row("2", "2025-05-01", "early_long_action", False)])
    assert one_day[0]["passes_evidence_gate"] is False
    two_days = p.build_candidates([row("1", "2025-05-01", "early_cycle_call", True),
                                   row("3", "2025-05-08", "early_long_action", False)])
    assert two_days[0]["passes_evidence_gate"] is True


def test_bearish_never_passes():
    rows = [{"post": {"handle": "bear", "published_at": "2025-05-01T00:00:00+00:00",
                      "date": "2025-05-01"},
             "classification": {"category": "bearish", "original_judgment": True,
                                "actionable": True, "mechanism_present": True}}]
    assert p.build_candidates(rows) == []
