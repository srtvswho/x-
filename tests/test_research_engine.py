from __future__ import annotations

import json
import sqlite3

from signalboard.ai import router
from signalboard.ai.router import AIResult
from signalboard.db import CURRENT_SCHEMA_VERSION, init_db
from signalboard.models import Platform, RawPost
from signalboard.repository import upsert_raw_post
from signalboard.research_graph import ingest_post_graph
from scripts.intel_extract import get_target_posts, init_extractions_table, persist_extraction
from scripts import intel_thesis_update
from scripts import intel_case_synthesis
from scripts.intel_source_dedup import build_source_map
from scripts.intel_theme_canonicalize import _apply_merges


def _root_payload():
    return {
        "id": "root",
        "text": "Root view https://t.co/a",
        "createdAt": "Sat Aug 29 20:00:00 +0000 2026",
        "author": {"userName": "zephyr_z9"},
        "isQuote": True,
        "quoteId": "q1",
        "inReplyToId": "missing-parent",
        "quote": {
            "id": "q1",
            "text": "Quoted evidence",
            "createdAt": "Sat Aug 29 19:00:00 +0000 2026",
            "author": {"userName": "jukan05"},
            "extendedEntities": {
                "media": [{
                    "media_key": "3_img1",
                    "media_url_https": "https://pbs.twimg.com/media/a.png",
                    "type": "photo",
                    "original_info": {"width": 1200, "height": 800},
                }]
            },
            "entities": {"urls": [{"expanded_url": "https://www.ft.com/story/example"}]},
        },
        "entities": {"urls": [{"expanded_url": "https://x.com/jukan05/status/q1"}]},
    }


def test_v4_schema_and_recursive_graph_are_idempotent(tmp_path):
    db = tmp_path / "graph.db"
    init_db(db)
    con = sqlite3.connect(db)
    assert con.execute("PRAGMA user_version").fetchone()[0] == CURRENT_SCHEMA_VERSION == 9
    for table in ("theme_embeddings", "underlying_sources", "source_memberships",
                  "claim_verifications", "thesis_analyses", "cross_author_theses", "research_case_analyses"):
        assert con.execute("SELECT 1 FROM sqlite_master WHERE type='table' AND name=?", (table,)).fetchone()
    payload = _root_payload()
    root = RawPost(
        post_id="root", source_id="tw_zephyr_z9", platform=Platform.TWITTER.value,
        published_at="2026-08-29T20:00:00Z", captured_at="2026-08-30T00:00:00Z",
        raw_text=payload["text"], raw_url="https://x.com/zephyr_z9/status/root",
        raw_json=json.dumps(payload),
    )
    con.close()
    upsert_raw_post(root, db)

    con = sqlite3.connect(db)
    first = ingest_post_graph(con, str(db), "root", payload)
    con.commit()
    second = ingest_post_graph(con, str(db), "root", payload)
    con.commit()
    assert first["edges"] == second["edges"] == 2
    assert con.execute("SELECT COUNT(*) FROM raw_posts").fetchone()[0] == 2
    assert con.execute("SELECT COUNT(*) FROM post_references").fetchone()[0] == 2
    assert con.execute("SELECT COUNT(*) FROM media_assets").fetchone()[0] == 1
    assert con.execute("SELECT COUNT(*) FROM external_sources").fetchone()[0] == 1
    q = con.execute(
        "SELECT depth, crawl_status FROM post_graph_memberships WHERE root_post_id='root' AND post_id='q1'"
    ).fetchone()
    assert q == (1, "complete")
    pending = con.execute(
        "SELECT crawl_status FROM post_graph_memberships WHERE root_post_id='root' AND post_id='missing-parent'"
    ).fetchone()
    assert pending == ("pending",)
    con.close()


def test_router_openai_responses_structured_output(monkeypatch, tmp_path):
    monkeypatch.setenv("OPENAI_API_KEY", "test-only")
    monkeypatch.setenv("AI_ENABLED", "true")
    monkeypatch.setenv("AI_LEDGER_DB_PATH", str(tmp_path / "router.db"))
    monkeypatch.setenv("AI_RUN_ID", "router-structured-test")
    monkeypatch.setenv("AI_ROUTE_MEDIA_UNDERSTANDING_PROVIDER", "openai")
    monkeypatch.setenv("AI_ROUTE_MEDIA_UNDERSTANDING_MODEL", "gpt-5.6-terra")
    captured = {}

    class Response:
        headers = {"x-request-id": "req_test"}

        def raise_for_status(self):
            return None

        def json(self):
            return {
                "status": "completed",
                "output": [{"type": "message", "content": [{"type": "output_text", "text": '{"ok":true}'}]}],
                "usage": {"input_tokens": 100, "output_tokens": 10, "input_tokens_details": {"cached_tokens": 20}},
            }

    def fake_post(url, *, headers, json, timeout):
        captured.update({"url": url, "headers": headers, "body": json, "timeout": timeout})
        return Response()

    monkeypatch.setattr(router.requests, "post", fake_post)
    schema = {
        "type": "object", "additionalProperties": False,
        "properties": {"ok": {"type": "boolean"}}, "required": ["ok"],
    }
    result = router.call_json(
        "media_understanding", "system", "user", schema,
        image_urls=["data:image/png;base64,AA=="], max_retries=0,
    )
    assert result.data == {"ok": True}
    assert result.model == "gpt-5.6-terra"
    assert result.request_id == "req_test"
    assert captured["url"].endswith("/v1/responses")
    assert captured["body"]["text"]["format"]["strict"] is True
    assert captured["body"]["input"][1]["content"][1]["type"] == "input_image"
    assert result.estimated_cost_usd > 0


def test_router_web_search_captures_sources(monkeypatch, tmp_path):
    monkeypatch.setenv("OPENAI_API_KEY", "test-only")
    monkeypatch.setenv("AI_ENABLED", "true")
    monkeypatch.setenv("AI_LEDGER_DB_PATH", str(tmp_path / "router-web.db"))
    monkeypatch.setenv("AI_RUN_ID", "router-web-test")
    captured = {}

    class Response:
        headers = {"x-request-id": "req_web"}
        def raise_for_status(self): return None
        def json(self):
            return {
                "status": "completed",
                "output": [
                    {"type": "web_search_call", "action": {"sources": [
                        {"type": "url", "url": "https://www.sec.gov/test", "title": "SEC"}
                    ]}},
                    {"type": "message", "content": [{"type": "output_text", "text": '{"ok":true}'}]},
                ],
                "usage": {"input_tokens": 50, "output_tokens": 5},
            }

    def fake_post(url, *, headers, json, timeout):
        captured["body"] = json
        return Response()

    monkeypatch.setattr(router.requests, "post", fake_post)
    schema = {"type": "object", "additionalProperties": False,
              "properties": {"ok": {"type": "boolean"}}, "required": ["ok"]}
    result = router.call_json_web("claim_verification", "system", "user", schema, max_retries=0)
    assert captured["body"]["tools"] == [{"type": "web_search"}]
    assert captured["body"]["include"] == ["web_search_call.action.sources"]
    assert result.sources[0]["url"] == "https://www.sec.gov/test"


def test_claim_backfill_upgrades_existing_extraction_in_place(tmp_path):
    db = tmp_path / "claims.db"
    init_db(db)
    post = RawPost(
        post_id="p1", source_id="tw_jukan05", platform=Platform.TWITTER.value,
        published_at="2026-08-29T00:00:00Z", captured_at="2026-08-29T00:01:00Z",
        raw_text="NAND supply may tighten", raw_url="https://x.com/jukan05/status/p1",
    )
    upsert_raw_post(post, db)
    con = sqlite3.connect(db)
    init_extractions_table(con)
    base = {
        "ticker": ["SNDK"], "company": ["SanDisk"], "direction": "long",
        "short_skeptical": 0, "bottleneck": "存储", "attribution": "ORIGINAL",
        "rebuts_narrative": None, "summary_100": "old", "is_retrospective": 0,
        "is_disclosure": 0, "is_self_reported_returns": 0,
    }
    assert persist_extraction(con, "p1", "tw_jukan05", json.dumps(base), base)
    assert get_target_posts(con, "2026-08-28T00:00:00Z") == []
    assert [x["post_id"] for x in get_target_posts(
        con, "2026-08-28T00:00:00Z", claims_missing=True,
    )] == ["p1"]

    upgraded = dict(base)
    upgraded.update({
        "summary_100": "new", "themes": ["NAND"],
        "claims": [{
            "claim_text": "作者预计 NAND 供应趋紧", "claim_type": "FORECAST",
            "claim_author": "Jukan", "companies": ["SanDisk"], "themes": ["NAND"],
            "time_horizon": "2027", "confidence": 0.8,
        }],
    })
    assert persist_extraction(con, "p1", "tw_jukan05", json.dumps(upgraded), upgraded)
    assert con.execute("SELECT COUNT(*) FROM extractions_intel WHERE post_id='p1'").fetchone()[0] == 1
    assert con.execute("SELECT summary_100 FROM extractions_intel WHERE post_id='p1'").fetchone()[0] == "new"
    assert con.execute("SELECT verification_status FROM claims").fetchone()[0] == "UNVERIFIED"
    assert get_target_posts(con, "2026-08-28T00:00:00Z", claims_missing=True) == []
    con.close()


def test_thesis_versions_only_on_material_change(tmp_path, monkeypatch):
    db = tmp_path / "thesis.db"
    init_db(db)
    post = RawPost(
        post_id="p1", source_id="tw_jukan05", platform=Platform.TWITTER.value,
        published_at="2026-08-29T00:00:00Z", captured_at="2026-08-29T00:01:00Z",
        raw_text="NAND", raw_url="https://x.com/jukan05/status/p1",
    )
    upsert_raw_post(post, db)
    con = sqlite3.connect(db)
    init_extractions_table(con)
    extraction = {
        "ticker": ["SNDK"], "company": ["SanDisk"], "direction": "long",
        "short_skeptical": 0, "bottleneck": "存储", "attribution": "ORIGINAL",
        "rebuts_narrative": None, "summary_100": "NAND", "is_retrospective": 0,
        "is_disclosure": 0, "is_self_reported_returns": 0, "themes": ["NAND"],
        "claims": [{
            "claim_text": "NAND supply tightens", "claim_type": "FORECAST",
            "claim_author": "Jukan", "companies": ["SanDisk"], "themes": ["NAND"],
            "time_horizon": "2027", "confidence": 0.8,
        }],
    }
    assert persist_extraction(con, "p1", "tw_jukan05", json.dumps(extraction), extraction)

    change_type = {"value": "THESIS_EXPANSION"}

    def fake_call(*args, **kwargs):
        payload = {
            "current_thesis": "NAND supply is tightening", "thesis_summary": "tight supply",
            "bull_case": "pricing", "bear_case": "new capacity", "key_drivers": ["demand"],
            "key_risks": ["supply"], "companies_positive": ["SNDK"], "companies_negative": [],
            "time_horizon": "2027", "confidence": 0.8, "change_type": change_type["value"],
            "thesis_change_score": 70 if change_type["value"] != "NO_CHANGE" else 0,
            "change_summary": "expanded", "facts": [],
            "author_opinions": ["supply tightens"], "ai_inferences": [], "missing_evidence": ["pricing"],
        }
        return AIResult(
            text=json.dumps(payload), data=payload, workload="thesis_update",
            provider="openai", model="gpt-5.6-terra", input_tokens=100,
            output_tokens=20, estimated_cost_usd=0.0002, latency_ms=10,
        )

    monkeypatch.setattr(intel_thesis_update, "call_json", fake_call)
    first = intel_thesis_update.update_pending_theses(con, 4)
    assert first["versioned"] == 1
    assert con.execute("SELECT COUNT(*) FROM thesis_versions").fetchone()[0] == 1

    con.execute("UPDATE claims SET point_in_time='2099-08-30T00:00:00Z'")
    con.commit()
    change_type["value"] = "NO_CHANGE"
    second = intel_thesis_update.update_pending_theses(con, 4)
    assert second["no_change"] == 1
    assert con.execute("SELECT COUNT(*) FROM thesis_versions").fetchone()[0] == 1
    con.close()


def test_theme_merge_requires_semantic_judgment_and_preserves_alias(tmp_path):
    db = tmp_path / "themes.db"
    init_db(db)
    con = sqlite3.connect(db)
    con.execute("INSERT INTO themes(theme_id,name) VALUES ('nand','NAND'),('flash','Flash Memory'),('agent','Agent Memory')")
    con.execute("""INSERT INTO claims
        (claim_id,claim_text,claim_type,themes_json,evidence_ids_json,confidence,content_hash)
        VALUES ('c1','NAND supply','FACT','[\"Flash Memory\"]','[]',0.8,'h1')""")
    con.execute("INSERT INTO claim_themes(claim_id,theme_id,confidence) VALUES ('c1','flash',0.8)")
    merged = _apply_merges(con, [{
        "decision": "MERGE_ALIAS", "confidence": 0.95, "canonical_name": "NAND",
        "left_theme_id": "nand", "left_name": "NAND", "right_theme_id": "flash", "right_name": "Flash Memory",
    }])
    assert merged == 1
    assert con.execute("SELECT parent_theme_id FROM themes WHERE theme_id='flash'").fetchone()[0] == "nand"
    assert json.loads(con.execute("SELECT aliases_json FROM themes WHERE theme_id='nand'").fetchone()[0]) == ["Flash Memory"]
    assert con.execute("SELECT theme_id FROM claim_themes WHERE claim_id='c1'").fetchone()[0] == "nand"
    assert con.execute("SELECT parent_theme_id FROM themes WHERE theme_id='agent'").fetchone()[0] is None
    assert _apply_merges(con, [{
        "decision": "MERGE_ALIAS", "confidence": 0.95, "canonical_name": "NAND",
        "left_theme_id": "nand", "left_name": "NAND", "right_theme_id": "flash", "right_name": "Flash Memory",
    }]) == 0
    assert con.execute("SELECT parent_theme_id FROM themes WHERE theme_id='flash'").fetchone()[0] == "nand"
    con.close()


def test_theme_constraint_is_not_merged_into_product(tmp_path):
    db = tmp_path / "theme-guard.db"
    init_db(db)
    con = sqlite3.connect(db)
    con.execute("INSERT INTO themes(theme_id,name) VALUES ('memory','内存'),('memory_limit','内存瓶颈')")
    merged = _apply_merges(con, [{
        "decision": "MERGE_ALIAS", "confidence": 0.95, "canonical_name": "内存",
        "left_theme_id": "memory", "left_name": "内存",
        "right_theme_id": "memory_limit", "right_name": "内存瓶颈",
    }])
    assert merged == 0
    assert con.execute("SELECT parent_theme_id FROM themes WHERE theme_id='memory_limit'").fetchone()[0] is None
    con.close()


def test_underlying_source_counts_mentions_not_reposts_as_evidence(tmp_path):
    db = tmp_path / "sources.db"
    init_db(db)
    for pid, source in (("p1", "tw_ft"), ("p2", "tw_jukan"), ("p3", "tw_zephyr")):
        upsert_raw_post(RawPost(
            post_id=pid, source_id=source, platform=Platform.TWITTER.value,
            published_at="2026-08-29T00:00:00Z", captured_at="2026-08-29T00:01:00Z",
            raw_text="same FT story", raw_url=f"https://x.com/x/status/{pid}",
        ), db)
    con = sqlite3.connect(db)
    con.execute("INSERT INTO external_sources(source_id,url,publisher) VALUES ('ext1','https://www.ft.com/content/story?utm_source=x','FT')")
    con.execute("INSERT INTO post_external_sources(post_id,source_id) VALUES ('p1','ext1')")
    con.execute("INSERT INTO post_references(source_post_id,target_post_id,reference_type,fetch_status) VALUES ('p2','p1','quote','complete')")
    con.execute("INSERT INTO post_references(source_post_id,target_post_id,reference_type,fetch_status) VALUES ('p3','p2','quote','complete')")
    stats = build_source_map(con, post_ids=["p1", "p2", "p3"])
    assert stats["external_sources"] == 1
    assert con.execute("SELECT COUNT(*) FROM underlying_sources").fetchone()[0] == 1
    assert con.execute("SELECT COUNT(DISTINCT mention_post_id) FROM source_memberships").fetchone()[0] == 3
    con.close()


def test_research_case_synthesis_is_incremental_and_bounded(tmp_path, monkeypatch):
    db = tmp_path / "case.db"
    init_db(db)
    upsert_raw_post(RawPost(
        post_id="p1", source_id="tw_zephyr", platform=Platform.TWITTER.value,
        published_at="2026-08-29T00:00:00Z", captured_at="2026-08-29T00:01:00Z",
        raw_text="YMTC capacity can support China WFE but raises NAND supply risk",
        raw_url="https://x.com/zephyr/status/p1",
    ), db)
    con = sqlite3.connect(db)
    con.execute("INSERT INTO post_graph_memberships(root_post_id,post_id,depth,crawl_status) VALUES ('p1','p1',0,'complete')")
    con.commit()

    payload = {
        "author_views": [{"author": "Zephyr", "view": "China WFE upside"}],
        "facts": ["YMTC expansion is planned"], "verified_evidence": [],
        "logic_chain": ["profit -> CapEx -> WFE"], "corrections": [], "contradictions": [],
        "ai_assessment": "Research further", "counter_case": ["NAND oversupply"],
        "second_order_effects": ["SNDK pricing risk"], "beneficiaries": ["NAURA"],
        "negative_exposure": ["SNDK"], "risks": ["oversupply"],
        "valuation_questions": ["WFE order conversion"], "catalysts": ["IPO filing"],
        "invalidation_conditions": ["CapEx is delayed"], "unknowns": ["fab count wording"],
        "actionability": "RESEARCH", "scores": {
            "thesis_quality": 7, "evidence_quality": 5, "novelty": 6,
            "mispricing_potential": 5, "actionability": 4,
        },
    }
    calls = {"n": 0}
    def fake_call(*args, **kwargs):
        calls["n"] += 1
        return AIResult(text=json.dumps(payload), data=payload, workload="research_case_synthesis",
                        provider="openai", model="gpt-5.6-terra", input_tokens=100,
                        output_tokens=50, estimated_cost_usd=0.0008, latency_ms=10)
    monkeypatch.setattr(intel_case_synthesis, "call_json", fake_call)
    cases = {"A": {"title": "YMTC / NAND / China WFE", "seed_post_ids": ["p1"],
                   "audit_questions": ["five total or five additional?"]}}
    assert intel_case_synthesis.synthesize(con, cases)["synthesized"] == 1
    assert intel_case_synthesis.synthesize(con, cases)["synthesized"] == 0
    assert calls["n"] == 1
    saved = json.loads(con.execute("SELECT analysis_json FROM research_case_analyses WHERE case_id='A'").fetchone()[0])
    assert saved["actionability"] == "RESEARCH"
    assert saved["scores"]["thesis_quality"] == 70
    con.close()
