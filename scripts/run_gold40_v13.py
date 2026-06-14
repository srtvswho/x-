"""跑金标 20 + 盲测 20(共 40 条)用 v1.3 重测。"""
import sqlite3, json, time, pickle, random
random.seed(20260614)

from signalboard.extract.caller import extract_one
from signalboard.extract.context import assemble, render_for_llm
from signalboard.extract.goldset import GOLD_V1
from signalboard.extract.evaluate import (
    LLMPostResult, LLMPrediction, evaluate, render_report,
)
from signalboard.extract.postprocess import llm_result_to_post_result
from signalboard.extract.caller import LLMCallResult

DB = "data/signalboard_full.db"

# 1) 抽盲测 20 的 post_id(从 sample_200 + goldset 拼出)
import sys
sys.path.insert(0, '/workspace')
gold_ids = [g['post_id'] for g in GOLD_V1]

# 从之前 run_sample_200.py 用的 seed(20260614)抽 200
# 但盲测 20 用了 seed=20260614(同),所以 200 里的随机子集
# 实际我之前在抽盲测时用 random.seed(20260614) 然后分桶 + 抽样
# 让我从 sample_200_raw.pkl 拿(之前的 200 实际记录)
# 但 sample_200_raw.pkl 已被沙箱清空
# 重新从 cache 拉

conn = sqlite3.connect(DB, timeout=60)
cache_rows = list(conn.execute(
    "SELECT post_id, response_json FROM extraction_cache WHERE prompt_version = 'deepseek:deepseek-v4-pro:v1.2' ORDER BY post_id"
))
all_200_pids = [r[0] for r in cache_rows if r[0] not in gold_ids]
print(f'v1.2 cache 中 200 采样: {len(all_200_pids)}')

# 复现盲测 20 抽样(同 seed + 同分桶逻辑)
import re
CASHTAG_RE = re.compile(r'\$([A-Z][A-Z0-9._-]{1,5})')
from collections import defaultdict

has_pred = []
no_pred_with_ticker = []
for r in cache_rows:
    pid = r[0]
    if pid in gold_ids: continue
    resp = json.loads(r[1])
    raw = conn.execute("SELECT raw_text FROM raw_posts WHERE post_id=?", (pid,)).fetchone()
    if not raw: continue
    text = raw[0]
    has_cashtag = bool(CASHTAG_RE.search(text))
    if resp.get('has_prediction'):
        has_pred.append((pid, resp, text))
    elif has_cashtag:
        no_pred_with_ticker.append((pid, resp, text))

# 用 seed 复现
random.seed(20260614)
buckets = defaultdict(list)
for pid, resp, text in has_pred:
    n = len(resp.get('predictions', []))
    if n <= 3: buckets['small'].append((pid, resp, text))
    elif n <= 9: buckets['medium'].append((pid, resp, text))
    else: buckets['large'].append((pid, resp, text))

sample_has = []
sample_has.extend(random.sample(buckets['small'], min(5, len(buckets['small']))))
if len(sample_has) < 10 and buckets['medium']:
    sample_has.extend(random.sample(buckets['medium'], min(3, len(buckets['medium']))))
if len(sample_has) < 10 and buckets['large']:
    sample_has.extend(random.sample(buckets['large'], min(10-len(sample_has), len(buckets['large']))))
remaining = [x for x in has_pred if x not in sample_has]
if len(sample_has) < 10:
    sample_has.extend(random.sample(remaining, min(10-len(sample_has), len(remaining))))

buckets_nopred = defaultdict(list)
for pid, resp, text in no_pred_with_ticker:
    flags = resp.get('flags', [])
    if 'victory_lap' in flags: buckets_nopred['victory_lap'].append((pid, resp, text))
    elif 'self_reported_returns' in flags: buckets_nopred['self_reported_returns'].append((pid, resp, text))
    elif 'position_disclosure' in flags: buckets_nopred['position_disclosure'].append((pid, resp, text))
    else: buckets_nopred['clean'].append((pid, resp, text))

sample_nopred = []
for k in ['victory_lap', 'self_reported_returns', 'position_disclosure', 'clean']:
    if buckets_nopred[k] and len(sample_nopred) < 10:
        take = min(3 if k != 'clean' else (10 - len(sample_nopred)), len(buckets_nopred[k]))
        sample_nopred.extend(random.sample(buckets_nopred[k], take))
remaining_nopred = [x for x in no_pred_with_ticker if x not in sample_nopred]
if len(sample_nopred) < 10:
    sample_nopred.extend(random.sample(remaining_nopred, min(10-len(sample_nopred), len(remaining_nopred))))

blind_ids = [pid for pid, _, _ in sample_has] + [pid for pid, _, _ in sample_nopred]
print(f'盲测 20 (10+10): {len(blind_ids)}')
print(f'  A 组: {[pid[-6:] for pid,_ ,_ in sample_has]}')
print(f'  B 组: {[pid[-6:] for pid,_ ,_ in sample_nopred]}')

# 2) 拼装 40 条
all_40 = gold_ids + blind_ids
print(f'\\n跑 40 条 (v1.3): {len(all_40)}')
items = []
for pid in all_40:
    raw = conn.execute("SELECT raw_json FROM raw_posts WHERE post_id=?", (pid,)).fetchone()
    if not raw: continue
    item = json.loads(raw[0])
    ctx = assemble(item, DB, source_user_id=item.get('userId'))
    items.append((pid, render_for_llm(ctx)))

# 3) 跑
t_total = time.time()
results = []
for i, (pid, assembled) in enumerate(items, 1):
    t_start = time.time()
    r = extract_one(pid, assembled, DB, use_cache=False)
    elapsed = time.time() - t_start
    results.append({
        'post_id': pid, 'elapsed': elapsed, 'prompt_version': r.prompt_version,
        'model': r.model, 'parse_error': r.parse_error,
        'response_json': r.response_json,
    })
    if r.parse_error:
        print(f'  [{i:2d}] ✗ {pid} err={r.parse_error[:60]}', flush=True)
    elif i % 10 == 0:
        print(f'  [{i:2d}/40] {elapsed:.1f}s cum {(time.time()-t_total):.0f}s', flush=True)
print(f'\\n总耗时: {time.time()-t_total:.1f}s', flush=True)

# 4) 保存
with open('/tmp/gold40_v13_results.pkl', 'wb') as f:
    pickle.dump(results, f)

# 5) 转 LLMPostResult 评测
llm_results = []
for r in results:
    if r['parse_error']:
        llm_results.append(LLMPostResult(
            post_id=r['post_id'], has_prediction=False, predictions=[],
            flags=[], extraction_notes=f"PARSE_ERROR: {r['parse_error'][:80]}",
        ))
        continue
    call_res = LLMCallResult(
        post_id=r['post_id'], prompt_version=r['prompt_version'],
        model=r['model'], response_json=r['response_json'],
        input_hash='', parse_error=None,
    )
    pr = llm_result_to_post_result(call_res, DB)
    llm_results.append(pr)

# 评测全 40
rep = evaluate(llm_results)
print(render_report(rep))
PYEOF