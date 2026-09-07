import json
import sqlite3
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from unittest.mock import patch

from signalboard.history_reuse import DDL, intel_decision, load_reviews, save_review, apply_evidence_reviews, cache_decision
from test_first_call_repair import database, post, revise
from common import query_call_performance_events
from intel_history_backfill import plan_backfill


def review(con, pid, events):
    con.executescript(DDL)
    row = con.execute('SELECT post_id,source_id,published_at,raw_text FROM raw_posts WHERE post_id=?', (pid,)).fetchone()
    obj = dict(zip(('post_id','source_id','published_at','raw_text'), row))
    eid = con.execute('SELECT id FROM extractions_intel WHERE post_id=? ORDER BY id DESC', (pid,)).fetchone()
    save_review(con, obj, events, origin='extraction_cache', version='v1.4.1', payload='{}',
                extraction_id=eid[0] if eid else None, reason='saved_per_ticker_predictions')


def test_reused_cache_no_call_overrides_legacy_and_never_calls_api():
    con = database()
    post(con, 'old', '2024-01-01T00:00:00Z', source='tw_aleabitoreddit', direction=None)
    post(con, 'new', '2026-01-01T00:00:00Z', source='tw_aleabitoreddit')
    con.execute("INSERT INTO predictions VALUES('old','tw_aleabitoreddit','long','MU','2024-01-01')")
    review(con, 'old', [])
    with patch('signalboard.ai.router.call_json', side_effect=AssertionError('must not call AI')):
        assert [r['post_id'] for r in query_call_performance_events(con)] == ['new']
        assert plan_backfill(con)['pending_total'] == 1


def test_cache_preserves_per_ticker_directions_and_price_start():
    con = database()
    post(con, 'p', '2024-01-01T00:00:00Z', direction=None)
    review(con, 'p', [{'ticker':'MU','direction':'long'}, {'ticker':'SNDK','direction':'short'}])
    assert {(r['ticker'],r['direction']) for r in query_call_performance_events(con)} == {('MU','long'),('SNDK','short')}
    plan = plan_backfill(con)
    assert plan['pending_total'] == 0
    assert plan['stored_history_call_review_complete'] is True
    assert plan['stored_history_extraction_complete'] is False


def test_newer_neutral_wins_over_reused_old_direction():
    con = database()
    post(con, 'p', '2024-01-01T00:00:00Z')
    review(con, 'p', [{'ticker':'MU','direction':'long'}])
    assert len(load_reviews(con)) == 1
    revise(con, 'p', 'neutral')
    assert not load_reviews(con)
    assert not query_call_performance_events(con)


def test_changed_raw_post_invalidates_reuse():
    con = database()
    post(con, 'p', '2024-01-01T00:00:00Z', direction=None)
    review(con, 'p', [])
    con.execute("UPDATE raw_posts SET raw_text='Buy $SNDK' WHERE post_id='p'")
    assert not load_reviews(con)
    assert plan_backfill(con)['pending_total'] == 1


def test_old_neutral_does_not_need_missing_trade_flags_but_long_does():
    p = {'ticker':['MU'], 'direction':'neutral', 'attribution':'ORIGINAL', 'summary_100':'Micron revenue increased.'}
    raw = {'raw_text':'Micron revenue increased.'}
    assert intel_decision({'raw_response':json.dumps(p)}, raw)[0] == []
    p['direction'] = 'long'
    assert intel_decision({'raw_response':json.dumps(p)}, raw)[0] is None


def test_empty_content_and_institutional_we_believe_are_not_reused_as_calls():
    p = {'ticker':['MU'], 'direction':'long', 'attribution':'ORIGINAL', 'summary_100':'We believe Micron is attractive.',
         'is_retrospective':0, 'is_disclosure':0, 'is_self_reported_returns':0}
    assert intel_decision({'raw_response':json.dumps(p)}, {'raw_text':'Morgan Stanley: We believe MU is attractive.'})[0] is None
    p.update(direction='neutral', summary_100='无法获取推文内容')
    assert intel_decision({'raw_response':json.dumps(p)}, {'raw_text':'Buy MU'})[0] is None


def test_reviewed_jukan_evidence_moves_both_anchors_and_is_idempotent(tmp_path):
    path = Path(__file__).resolve().parents[1] / 'config/first_call_evidence_reviews.json'
    evidence = json.loads(path.read_text())
    con = database()
    for r in evidence['reviews']:
        post(con, r['post_id'], r['published_at'], text=r['raw_text'], direction=None)
    con.commit()
    db = tmp_path / 'evidence.db'
    with sqlite3.connect(db) as out:
        con.backup(out)
    assert apply_evidence_reviews(db, path) == 4
    assert apply_evidence_reviews(db, path) == 0
    with sqlite3.connect(db) as out:
        from common import select_call_performance_targets
        anchors = {r['ticker']:r['call_date'] for r in select_call_performance_targets(out)}
        assert anchors['MU'] == '2025-09-05'
        assert anchors['SNDK'] == '2025-09-30'
        assert '1938183627545973006' not in {r['post_id'] for r in query_call_performance_events(out)}


def test_cache_with_changed_context_is_not_reused():
    cache = {'response_json':json.dumps({'post_id':'p','has_prediction':False,'predictions':[],'flags':[]}),
             'prompt_version':'v1.4.1','input_hash':'stale'}
    raw = {'post_id':'p','raw_json':json.dumps({'id':'p','text':'Buy MU'}),'raw_text':'Buy MU'}
    with patch('signalboard.extract.context.assemble', return_value=object()), patch('signalboard.extract.context.render_for_llm', return_value='new context'):
        assert cache_decision(cache, raw, 'unused') == (None, 'cache_context_changed')


def test_focus_prices_are_prioritized_without_changing_default_order(monkeypatch):
    from refresh_prices_polygon import prioritize_price_targets
    con = database()
    con.execute('ALTER TABLE ticker_prices ADD COLUMN fetched_at TEXT')
    targets = {ticker:[{'ticker':ticker,'call_date':'2025-09-05'}] for ticker in ('AAPL','MU','SNDK')}
    assert list(prioritize_price_targets(con, targets, targets['AAPL'], 2)) == ['AAPL','MU']
    monkeypatch.setenv('POLYGON_PRIORITY_TICKERS', 'MU,SNDK')
    assert list(prioritize_price_targets(con, targets, targets['AAPL'], 2)) == ['MU','SNDK']
