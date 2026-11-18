import sqlite3
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
import intel_daily_ai as daily
import intel_resume_queue as queue
from test_ai_resume_queue import queue_fixture


def coverage(con, start, end, handles):
    con.execute('''CREATE TABLE IF NOT EXISTS twitterapi_timeline_coverage
        (coverage_start,coverage_end,handle,operation,provider,endpoint,completion_reason)''')
    con.executemany('INSERT INTO twitterapi_timeline_coverage VALUES (?,?,?,?,?,?,?)', [
        (start, end, handle, 'timeline-daily-' + start, 'twitterapi.io', 'last_tweets',
         'start_boundary_crossed') for handle in handles])


def test_ready_only_for_contiguous_verified_accounts_and_resume_without_billing():
    con = sqlite3.connect(':memory:')
    start = daily.FIRST_WINDOW
    end = '2026-11-18T02:39:16Z'
    next_end = '2026-11-19T02:39:16Z'
    day = '2026-11-18'
    coverage(con, start, end, daily.HANDLES[:-1])
    coverage(con, end, next_end, daily.HANDLES)
    assert daily.choose(con, {}, day)['action'] == 'wait'
    coverage(con, start, end, daily.HANDLES[-1:])
    assert daily.choose(con, {}, day)['end'] == end
    state = {end: {'status':'in_progress','attempt_day':day}}
    assert daily.choose(con, state, day)['end'] == next_end
    state[end]['status'] = 'ready_to_publish'
    assert daily.choose(con, state, day)['action'] == 'publish'
    state[end]['status'] = 'verified'
    state[next_end] = {'status':'verified'}
    assert daily.choose(con, state, day)['action'] == 'wait'


def test_daily_queue_does_not_reopen_historical_or_context_posts(tmp_path, monkeypatch):
    con = queue_fixture(tmp_path)
    start, end, campaign = '2026-11-19', '2026-11-21', 'daily-ai-2026-11-21'
    queue.prepare(con, campaign, start, end)
    assert con.execute('SELECT post_id FROM ai_resume_queue WHERE campaign=?', (campaign,)).fetchall() == [('future',)]
    calls = []
    def stop(post):
        calls.append(post['post_id'])
        return {'ok':False, 'error':'HTTPError: 402'}
    monkeypatch.setattr(queue.extract, 'extract_one', stop)
    assert queue.run_step(con, campaign=campaign) == 'HTTPError: 402'
    assert calls == ['future']
    assert con.execute('SELECT attempts FROM ai_resume_queue WHERE campaign=?', (queue.CAMPAIGN,)).fetchone() == (0,)
    assert queue.report(con, campaign, start, end)['pending'] == 1


def test_full_window_checkpoints_and_summary_then_publish_without_more_ai(tmp_path, monkeypatch):
    import json
    import subprocess
    con = queue_fixture(tmp_path)
    start, end = '2026-11-19', '2026-11-21'
    state = {}
    checkpointed = []
    monkeypatch.setenv('AI_CAMPAIGN_ID', '')
    monkeypatch.setenv('AI_RUN_ID', '')
    monkeypatch.setenv('DEEPSEEK_API_KEY', 'offline-placeholder')
    monkeypatch.setenv('AI_ENABLED', 'true')
    summary = tmp_path / 'summary.json'
    monkeypatch.setenv('SUMMARY_OUT_PATH', str(summary))
    monkeypatch.setattr(daily, 'REVIEW', tmp_path/'review.json')
    monkeypatch.setattr(daily, 'checkpoint', lambda state: checkpointed.append(state[end]['status']))
    monkeypatch.setattr(queue.extract, 'extract_one', lambda p: {
        'ok':True, 'extraction':{'direction':'neutral'}, 'raw_response':'{"direction":"neutral"}'})
    def offline_stage(argv, **kwargs):
        if 'scripts/intel_call_attribution.py' in argv:
            daily.REVIEW.write_text('{"pending":0}')
        else:
            summary.write_text(json.dumps({'refresh_complete':True, 'generated_at':'now'}))
        return subprocess.CompletedProcess(argv, 0)
    monkeypatch.setattr(daily.subprocess, 'run', offline_stage)
    daily.process(con, {'start':start,'end':end}, state, '2026-11-21')
    assert state[end]['status'] == 'ready_to_publish'
    assert state[end]['extraction']['counts'] == {'complete':1}
    assert state[end]['pending_directions'] == 0
    assert checkpointed[0] == 'in_progress' and checkpointed[-1] == 'ready_to_publish'
