import importlib.util
import json
from pathlib import Path
import sqlite3
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts' / 'dashboard'))
import common
import build_dashboard


def database():
    con = sqlite3.connect(':memory:')
    con.executescript('''
        CREATE TABLE raw_posts(post_id TEXT PRIMARY KEY, source_id TEXT, published_at TEXT, raw_text TEXT, raw_url TEXT);
        CREATE TABLE extractions_intel(id INTEGER PRIMARY KEY, post_id TEXT, source_id TEXT,
            extracted_at TEXT, prompt_version TEXT, direction TEXT, ticker TEXT, bottleneck TEXT,
            is_retrospective INTEGER DEFAULT 0, is_disclosure INTEGER DEFAULT 0, attribution TEXT DEFAULT 'ORIGINAL');
        CREATE TABLE predictions(post_id TEXT, source_id TEXT, direction TEXT, ticker TEXT, published_at TEXT);
        CREATE TABLE ticker_prices(ticker TEXT, pub_date TEXT, call_price REAL, now_price REAL, now_date TEXT);
    ''')
    return con


def post(con, pid, date, *, source='tw_jukan05', text='$MU is attractive', direction='long', ticker='MU', extracted='2026-09-01T00:00:00Z'):
    con.execute('INSERT INTO raw_posts VALUES(?,?,?,?,?)', (pid, source, date, text, 'https://x.com/user/status/' + pid))
    if direction is not None:
        con.execute('INSERT INTO extractions_intel(post_id, source_id, extracted_at, prompt_version, direction,ticker) VALUES(?,?,?,?,?,?)',
                    (pid, source, extracted, 'v1', direction, json.dumps([ticker])))


def revise(con, pid, direction='neutral', **fields):
    con.execute('INSERT INTO extractions_intel(post_id,source_id,extracted_at,prompt_version,direction,ticker) SELECT post_id,source_id,?, ?, ?,ticker FROM extractions_intel WHERE post_id=? ORDER BY id LIMIT 1',
                ('2026-09-02T00:00:00+00:00', 'v2', direction, pid))
    for key, value in fields.items():
        con.execute(f'UPDATE extractions_intel SET {key}=? WHERE id=(SELECT MAX(id) FROM extractions_intel)', (value,))


def test_full_history_anchor_is_shared_with_price_targets():
    con = database()
    post(con, 'old', '2024-01-01T00:00:00Z')
    post(con, 'recent', '2026-09-05T00:00:00Z')
    con.execute("INSERT INTO ticker_prices VALUES('MU','2024-01-01',50,100,'2026-09-04')")
    row, = build_dashboard.query_call_performance(con)
    price, = common.select_call_performance_targets(con)
    assert row['post_id'] == 'old'
    assert row['call_date'] == price['call_date'] == '2024-01-01'
    assert row['directional_return'] == 100
    assert row['latest_published_at'] == '2026-09-05T00:00:00Z'
    assert row['n_mentions'] == price['n_calls'] == 2


def test_latest_interpretation_wins_before_all_filters_and_legacy():
    con = database()
    for i, flags in enumerate([{}, {'attribution': 'RELAYED'}, {'is_disclosure': 1}, {'is_retrospective': 1}]):
        pid = str(i)
        post(con, pid, f'2024-01-0{i+1}T00:00:00Z', source='tw_aleabitoreddit')
        revise(con, pid, 'long' if flags else 'neutral', **flags)
        con.execute("INSERT INTO predictions VALUES(?,'tw_aleabitoreddit','long','MU',?)", (pid, f'2024-01-0{i+1}T00:00:00Z'))
    post(con, 'valid', '2026-01-01T00:00:00Z', source='tw_aleabitoreddit')
    assert [e['post_id'] for e in common.query_call_performance_events(con)] == ['valid']


def test_equal_timestamp_revision_uses_latest_id_and_counts_once():
    con = database()
    post(con, 'p', '2025-01-01T00:00:00Z', extracted='2026-09-02T00:00:00Z')
    revise(con, 'p', 'short')
    events = common.query_call_performance_events(con)
    assert len(events) == 1
    assert events[0]['direction'] == 'short'


def test_earlier_mentions_and_missing_analysis_are_not_promoted_to_calls():
    con = database()
    post(con, 'earlier', '2024-01-01T00:00:00Z', direction=None, text='Micron HBM market share is growing')
    post(con, 'neutral', '2025-01-01T00:00:00Z', direction='neutral')
    post(con, 'call', '2026-01-01T00:00:00Z')
    row, = build_dashboard.query_call_performance(con)
    assert row['post_id'] == 'call'
    assert row['earlier_mention_count'] == 2
    assert row['earlier_mentions'][0]['post_id'] == 'earlier'
    assert row['history_coverage']['unprocessed_before_start'] == 1
    assert row['history_coverage']['status'] == 'unverified'


def test_backfill_plan_spans_all_authors_and_no_ticker_or_date_filter():
    spec = importlib.util.spec_from_file_location('history_repair', ROOT / 'scripts' / 'intel_history_backfill.py')
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    con = database()
    for i, source in enumerate(common.SRC2KOL):
        post(con, f'{i}a', '2020-01-01T00:00:00Z', source=source, text='industry discussion without a ticker', direction=None)
        post(con, f'{i}b', '2025-01-01T00:00:00Z', source=source)
    plan = mod.plan_backfill(con, 8)
    assert set(plan['selected_post_ids']) == {f'{i}a' for i in range(8)}
    assert plan['pending_total'] == 16
    assert plan['history_complete'] is False
    assert len(plan['sources']) == 8
    for pid in plan['selected_post_ids']:
        con.execute('INSERT INTO extractions_intel(post_id,prompt_version) VALUES(?,?)', (pid, mod.PROMPT_VERSION))
    resumed = mod.plan_backfill(con, 8)
    assert not set(plan['selected_post_ids']) & set(resumed['selected_post_ids'])
    assert resumed['pending_total'] == 8
