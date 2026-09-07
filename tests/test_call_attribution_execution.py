import json
import sqlite3
import sys
from pathlib import Path
from types import SimpleNamespace

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
import intel_call_attribution as runner
from signalboard.call_attribution import SYSTEM, SCHEMA, VERSION, candidates
from test_call_attribution import fixture, payload
from test_first_call_repair import post


def test_required_contract_reaches_deepseek_messages(monkeypatch):
    from signalboard.ai import router
    bodies = []
    monkeypatch.setenv('DEEPSEEK_API_KEY', 'test-only')
    def request(url, *, headers, json, timeout):
        bodies.append(json)
        return SimpleNamespace(headers={}, raise_for_status=lambda: None,
            json=lambda: {'choices': [{'message': {'content': '{}'}}]})
    monkeypatch.setattr(router.requests, 'post', request)
    router._request_deepseek(router.resolve_route('bulk_post_processing'), SYSTEM, '{}',
        schema=SCHEMA, max_output_tokens=1600, timeout=90)
    message = bodies[0]['messages'][0]['content']
    assert json.dumps(SCHEMA) in message
    assert '"decisions"' in message and '"direction":"long"' in message
    assert bodies[0]['response_format'] == {'type': 'json_object'}


@pytest.fixture
def environment(tmp_path, monkeypatch):
    con = fixture()
    for i in range(9):
        post(con, f'comparison-{i}', f'2025-01-{i+2:02d}',
             text='AMD and NVDA are peers. Just buy TSM.')
    con.execute("UPDATE extractions_intel SET ticker=?,raw_response='{}'",
                (json.dumps(['AMD', 'NVDA', 'TSM']),))
    con.commit()
    db = tmp_path / 'review.db'
    with sqlite3.connect(db) as disk:
        con.backup(disk)
    (tmp_path / 'config').mkdir()
    (tmp_path / 'outputs').mkdir()
    config = {'campaign_id': 'stable-campaign', 'repair_revision': 'json-v2'}
    (tmp_path / 'config/history_repair_campaign.json').write_text(json.dumps(config))
    (tmp_path / 'outputs/history_repair_campaign.json').write_text(json.dumps({
        'campaign_id': 'stable-campaign', 'ledger': {'accounted_usd': 11.42}}))
    monkeypatch.chdir(tmp_path)
    monkeypatch.setenv('AI_RUN_ID', 'stable-campaign')
    monkeypatch.setattr(sys, 'argv', ['review', '--db', str(db), '--apply', '--limit', '200'])
    return db, tmp_path


def test_bad_contract_stops_after_six_and_retains_paid_responses(environment, monkeypatch):
    db, root = environment
    requests = []
    def call(*a, **kw):
        requests.append(kw)
        return SimpleNamespace(data={'TSM': 'bullish'})
    monkeypatch.setattr(runner, 'call_json', call)
    with pytest.raises(SystemExit, match='blocked'):
        runner.main()
    assert len(requests) == 6
    with sqlite3.connect(db) as con:
        assert len(candidates(con)) == 10
        assert con.execute('SELECT COUNT(*) FROM call_attribution_attempts').fetchone()[0] == 6
        assert con.execute('SELECT COUNT(*) FROM call_attribution_attempts WHERE validation_error IS NOT NULL').fetchone()[0] == 6
    campaign = json.loads((root / 'outputs/history_repair_campaign.json').read_text())
    assert campaign['campaign_status'] == 'blocked'
    assert campaign['ledger']['accounted_usd'] == 11.42
    assert campaign['campaign_id'] == 'stable-campaign'
    assert campaign['per_security_review_pending'] == 10


def test_good_canary_then_drain_without_repeating_successes(environment, monkeypatch):
    db, root = environment
    requests = []
    def call(*a, **kw):
        requests.append(kw['entity_id'])
        return SimpleNamespace(data=payload())
    monkeypatch.setattr(runner, 'call_json', call)
    runner.main()
    report = json.loads((root / 'outputs/call_attribution_review.json').read_text())
    assert report['pending'] == 4 and report['canary_passed']
    runner.main()
    report = json.loads((root / 'outputs/call_attribution_review.json').read_text())
    assert report['pending'] == 0 and report['status'] == 'completed'
    assert len(requests) == len(set(requests)) == 10
    with sqlite3.connect(db) as con:
        assert con.execute('SELECT COUNT(*) FROM extractions_intel').fetchone()[0] == 10
    report['failed_attempts']={'comparison':2}
    (root / 'outputs/call_attribution_review.json').write_text(json.dumps(report))
    runner.main()
    report=json.loads((root / 'outputs/call_attribution_review.json').read_text())
    assert report['failed_attempts']=={} and len(requests)==10


def test_final_manual_evidence_hashes_quotes_and_security_scope():
    from signalboard.history_reuse import raw_hash
    config=Path(__file__).resolve().parents[1]/'config/first_call_evidence_reviews.json'
    rows={r['post_id']:r for r in json.loads(config.read_text())['reviews']}
    expected={
        '1993327956585070661':{'NBIS'},
        '2016725956002537717':set(),
        '2054266085889982497':{'MU','SNDK'},
        '2055007237207453843':{'MU','SNDK'},
        '1945263024098697624':{'000660.KS','005930.KS'},
        '1951089623234650248':{'005930.KS'},
        '1965681856214696110':{'TSM'},
        '1966185091467718795':{'TSM'},
    }
    for pid,tickers in expected.items():
        row=rows[pid]
        assert raw_hash(row)==row['raw_hash']
        assert len(row['reviewed_extraction_hash'])==64
        assert {e['ticker'] for e in row['events']}==tickers
        for event in row['events']:
            if 'quote' in event:assert event['quote'] in row['raw_text']


def test_new_contract_keeps_accepted_old_reviews(environment, monkeypatch):
    from signalboard.call_attribution import save
    db, root = environment
    with sqlite3.connect(db) as con:
        save(con, candidates(con)[0], payload())
        con.execute("UPDATE historical_call_reviews SET origin_version='per-security-calls-v1'")
        assert len(candidates(con)) == 9
    # The broken contract's retry debt may reset; paid accounting and accepted
    # evidence must not reset. No raw interpretation is re-extracted.
    (root / 'outputs/call_attribution_review.json').write_text(json.dumps({
        'version': 'per-security-calls-v1', 'canary_passed': True,
        'failed_attempts': {f'comparison-{i}': 2 for i in range(9)}}))
    monkeypatch.setattr(runner, 'call_json', lambda *a, **kw: SimpleNamespace(data=payload()))
    runner.main()
    report = json.loads((root / 'outputs/call_attribution_review.json').read_text())
    assert report['version'] == VERSION
    assert report['selected_count'] == 6 and report['pending'] == 3


def test_semantic_retry_has_new_request_input():
    con = fixture()
    candidate = candidates(con)[0]
    first = runner.review_prompt(candidate)
    retry = runner.review_prompt(candidate, 'Missing per-security decisions')
    assert first != retry
    assert json.loads(retry)['raw_post'] == candidate['raw_text']


@pytest.mark.parametrize('previous,count,successes,remaining,blocked', [
    ({}, 6, 1, 100, True), ({}, 6, 5, 100, False),
    ({'canary_passed': True}, 200, 1, 100, True),
    ({'canary_passed': True}, 10, 8, 2, False),
    ({'canary_passed': True}, 0, 0, 1, True),
    ({}, 0, 0, 0, False),
])
def test_failure_circuit(previous, count, successes, remaining, blocked):
    assert runner.batch_status(previous, count, successes, remaining)[1] is blocked


def test_evidence_debt_does_not_block_unattempted_records():
    assert runner.batch_status({},6,4,36,evidence_failures=2)==(True,False)
    assert runner.batch_status({'canary_passed':True},2,0,2,evidence_failures=2)==(True,False)
    assert runner.batch_status({'canary_passed':True},0,0,2)==(True,True)
