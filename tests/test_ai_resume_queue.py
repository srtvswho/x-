import json
import sqlite3
import sys
from pathlib import Path
from types import SimpleNamespace
import pytest
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
import intel_resume_queue as queue
from signalboard.ai import router
from signalboard.ai.guardrails import preflight, finish_success, AIGuardrailBlocked


def test_campaign_budget_survives_new_batch_id(tmp_path, monkeypatch):
    monkeypatch.setenv('AI_ENABLED','true')
    monkeypatch.setenv('AI_LEDGER_DB_PATH',str(tmp_path/'ledger.db'))
    monkeypatch.setenv('AI_CAMPAIGN_ID','recovery')
    monkeypatch.setenv('AI_CAMPAIGN_MAX_COST_USD','0.0015')
    monkeypatch.setenv('AI_RUN_ID','recovery/first')
    def reserve(key):
        return preflight(workload='bulk_post_processing',provider='deepseek',model='test',
            system='',user='',image_count=0,max_output_tokens=999,
            prices_per_million=(1,0,1),input_hash=key,prompt_version='test')
    p=reserve('one')
    finish_success(p,input_tokens=1,cached_input_tokens=0,output_tokens=999,actual_cost=.001)
    monkeypatch.setenv('AI_RUN_ID','recovery/second')
    with pytest.raises(AIGuardrailBlocked, match='CAMPAIGN_BUDGET_EXCEEDED'):
        reserve('two')


def test_permanent_http_failure_not_retried(tmp_path, monkeypatch):
    monkeypatch.setenv('AI_ENABLED','true')
    monkeypatch.setenv('AI_LEDGER_DB_PATH',str(tmp_path/'ledger.db'))
    calls=[]
    def fail(*a, **kw):
        calls.append(1)
        raise router.requests.HTTPError('balance unavailable', response=SimpleNamespace(status_code=402))
    monkeypatch.setattr(router,'_request_deepseek',fail)
    with pytest.raises(router.requests.HTTPError):
        router.call_text('bulk_post_processing','system','input',max_retries=2)
    assert len(calls)==1


def queue_fixture(tmp_path):
    db=tmp_path/'queue.db'
    queue.extract.init_db(db)
    c=sqlite3.connect(db)
    queue.extract.init_extractions_table(c)
    # Insert through the actual raw schema, without depending on unused columns.
    columns={r[1]:r for r in c.execute('pragma table_info(raw_posts)')}
    for pid, source, date in [('new','tw_jukan05','2026-11-10'),('old','tw_jukan05','2026-11-10'),('ctx','ctx_tw_jukan05','2026-11-10'),('future','tw_jukan05','2026-11-20')]:
        values={'post_id':pid,'source_id':source,'raw_text':'text','published_at':date,'fetched_at':date,'raw_json':'{}'}
        for name,r in columns.items():
            if r[3] and r[4] is None and name not in values: values[name]='test'
        names=[k for k in values if k in columns]
        c.execute(f"INSERT INTO raw_posts ({','.join(names)}) VALUES ({','.join('?' for _ in names)})",[values[k] for k in names])
    c.execute("INSERT INTO extractions_intel(post_id,source_id,extracted_at,model_version,prompt_version,raw_response,direction) VALUES('old','tw_jukan05','now','old','old','{}','neutral')")
    c.commit()
    queue.prepare(c);queue.prepare(c)
    assert c.execute('select post_id from ai_resume_queue').fetchall()==[('new',)]
    return c


def test_outage_stops_after_canary_and_keeps_pending(tmp_path,monkeypatch):
    c=queue_fixture(tmp_path)
    calls=[]
    def fail(post):
        calls.append(post['post_id'])
        return {'ok':False,'error':'HTTPError: 402'}
    monkeypatch.setattr(queue.extract,'extract_one',fail)
    assert queue.run_step(c)=='HTTPError: 402'
    assert calls==['new']
    assert c.execute('select status,error from ai_resume_queue').fetchone()==('pending','HTTPError: 402')


def test_missing_queue_preserves_old_versions_and_scope(tmp_path):
    queue_fixture(tmp_path).close()


def test_deferred_retry_grows_only_failed_output_once(tmp_path,monkeypatch):
    c=queue_fixture(tmp_path)
    c.execute("update ai_resume_queue set status='deferred',attempts=1,error='AIOutputTruncatedError'")
    c.commit()
    calls=[]
    def fail(pid,text,**kw):
        calls.append((pid,kw))
        return {'ok':False,'error':'AIOutputTruncatedError: still too long'}
    monkeypatch.setattr(queue.extract,'call_deepseek',fail)
    queue.run_step(c,retry_deferred=True)
    queue.run_step(c,retry_deferred=True)
    assert calls==[('new',{'max_output_tokens':3000,'max_retries':1})]
    assert c.execute('select status,attempts from ai_resume_queue').fetchone()==('deferred',2)
