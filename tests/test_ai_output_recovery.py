import json
import sqlite3
import pytest
from signalboard.ai import router


@pytest.fixture
def api(monkeypatch, tmp_path):
    monkeypatch.setenv('DEEPSEEK_API_KEY', 'test-only')
    monkeypatch.setenv('AI_ENABLED', 'true')
    monkeypatch.setenv('AI_LEDGER_DB_PATH', str(tmp_path / 'ledger.db'))
    monkeypatch.setenv('AI_RUN_ID', 'output-recovery-test')
    monkeypatch.setenv('AI_ROUTE_BULK_POST_PROCESSING_PROVIDER', 'deepseek')
    monkeypatch.setenv('AI_ROUTE_BULK_POST_PROCESSING_MODEL', 'deepseek-v4-flash')
    monkeypatch.setattr(router.time, 'sleep', lambda _: None)
    calls = []
    responses = []
    class Response:
        headers = {}
        def raise_for_status(self): pass
        def json(self): return responses.pop(0)
    def post(url, *, headers, json, timeout):
        calls.append(json['max_tokens'])
        return Response()
    monkeypatch.setattr(router.requests, 'post', post)
    return calls, responses, tmp_path / 'ledger.db'


def response(text, reason='stop'):
    return {'choices': [{'finish_reason': reason, 'message': {'content': text}}],
            'usage': {'prompt_tokens': 10, 'completion_tokens': 20}}


def call(**kwargs):
    return router.call_json('bulk_post_processing', 'Return JSON', 'long post',
        {'type': 'object'}, max_output_tokens=1500, **kwargs)


@pytest.mark.parametrize('broken', [response('{"x":"unfinished'), response('{"x":1}', 'length')])
def test_truncated_output_grows_and_each_attempt_is_accounted(api, broken):
    calls, responses, db = api
    responses.extend([broken, response('{"ok":true}')])
    assert call(max_output_tokens_ceiling=6000).data == {'ok': True}
    assert calls == [1500, 3000]
    with sqlite3.connect(db) as con:
        rows = con.execute('SELECT status, input_hash FROM ai_usage_ledger ORDER BY rowid').fetchall()
    assert [r[0] for r in rows] == ['FAILED', 'SUCCESS']
    assert rows[0][1] != rows[1][1]


def test_growth_is_bounded_and_default_other_calls_unchanged(api):
    calls, responses, _ = api
    responses.extend([response('{')] * 3)
    with pytest.raises(json.JSONDecodeError):
        call(max_output_tokens_ceiling=6000)
    assert calls == [1500, 3000, 6000]


def test_no_growth_without_opt_in(api):
    calls, responses, _ = api
    responses.extend([response('{'), response('{}')])
    call()
    assert calls == [1500, 1500]


def test_larger_retry_still_requires_guardrail_permit(api, monkeypatch):
    calls, responses, _ = api
    responses.append(response('{'))
    monkeypatch.setenv('AI_MAX_CALLS_PER_RUN', '1')
    with pytest.raises(router.AIGuardrailBlocked):
        call(max_output_tokens_ceiling=6000)
    assert calls == [1500]
