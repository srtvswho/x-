"""盲查 30 条(分层抽样 + 删缓存实跑)
- 15 条 has_pred=True(验假阳)
- 15 条 has_pred=False + 原文含 cashtag(验假阴)
"""
import sqlite3, json, random, sys, os
sys.path.insert(0, '/workspace')
os.environ.setdefault('DEEPSEEK_API_KEY', '')

from signalboard.extract.caller import extract_one
from signalboard.extract.context import assemble, render_for_llm
from signalboard.extract.config import CACHE_KEY_PROMPT_VERSION

DB = "data/signalboard_full.db"
N_TRUE = 15
N_FALSE = 15
RANDOM_SEED = 20260615

random.seed(RANDOM_SEED)
c = sqlite3.connect(DB, timeout=30)

# 1) 收集分层候选
true_cands = []  # has_pred=True
false_cands = []  # has_pred=False + 原文含 cashtag
import re
CASHTAG = re.compile(r'\$([A-Z][A-Z0-9._-]{1,5})')

print("收集分层候选...", flush=True)
for r in c.execute(
    """SELECT post_id, response_json FROM extraction_cache
       WHERE prompt_version='deepseek:deepseek-v4-pro:v1.4.1'""").fetchall():
    pid, rjs = r
    rj = json.loads(rjs)
    raw = c.execute("SELECT raw_text FROM raw_posts WHERE post_id=?", (pid,)).fetchone()
    if not raw:
        continue
    text = raw[0]
    if rj.get('has_prediction'):
        true_cands.append((pid, text, rj))
    elif CASHTAG.findall(text):
        false_cands.append((pid, text, rj, CASHTAG.findall(text)))

print(f"  has_pred=True 候选: {len(true_cands)}", flush=True)
print(f"  has_pred=False + cashtag 候选: {len(false_cands)}", flush=True)

# 2) 抽 15+15
sample_true = random.sample(true_cands, N_TRUE)
sample_false = random.sample(false_cands, N_FALSE)

# 3) 删 extraction_cache(本批抽样 30 条) → 强制 use_cache=False 实跑
#    只删这 30 条的 cache,保留其它(避免破坏其它)
sample_pids = set([pid for pid, _, _ in sample_true] + [pid for pid, _, _, _ in sample_false])
print(f"\n删 {len(sample_pids)} 条 cache(只删抽到的,其它保留)...", flush=True)
deleted = 0
for pid in sample_pids:
    cur = c.execute("DELETE FROM extraction_cache WHERE post_id=? AND prompt_version='deepseek:deepseek-v4-pro:v1.4.1'", (pid,))
    deleted += cur.rowcount
c.commit()
print(f"  deleted {deleted} rows", flush=True)

# 4) 实跑(use_cache=False 强制实调)
import time
t0 = time.time()
results = []
for i, item in enumerate(sample_true + sample_false, 1):
    if len(item) == 3:
        pid, text, _ = item
    else:
        pid, text, _, _ = item
    try:
        rjson = c.execute("SELECT raw_json FROM raw_posts WHERE post_id=?", (pid,)).fetchone()[0]
        item_obj = json.loads(rjson)
        user_id = item_obj.get('userId') or item_obj.get('user_id')
        ctx = assemble(item_obj, DB, source_user_id=user_id)
        assembled = render_for_llm(ctx)
        r = extract_one(pid, assembled, DB, use_cache=False)  # 实调
        results.append({
            'idx': i, 'post_id': pid, 'has_pred_cached': True if len(item)==3 else False,
            'text': text, 'r': r,
        })
    except Exception as e:
        results.append({
            'idx': i, 'post_id': pid, 'error': str(e),
            'text': text, 'r': None,
        })
    if i % 5 == 0 or i == len(sample_true) + len(sample_false):
        print(f"  [{i}/30] elapsed={time.time()-t0:.0f}s", flush=True)

# 5) 逐条打印
print("\n" + "="*80, flush=True)
print("盲查 30 条逐条打印", flush=True)
print("="*80, flush=True)
for result in results:
    i = result['idx']
    pid = result['post_id']
    text = result['text']
    is_true = result.get('has_pred_cached', False)
    section = "TRUE 类(LLM 原 has_pred=True,验假阳)" if is_true else "FALSE 类(LLM 原 has_pred=False,验假阴)"
    print(f"\n{'='*80}")
    print(f"### #{i:2d} [{section}]  post_id: {pid}")
    print(f"="*80)
    print(f"--- 原文 (raw_text,可能截断) ---")
    print(text[:1500] + ('...' if len(text) > 1500 else ''))
    if result.get('error'):
        print(f"\n--- ERROR: {result['error']} ---")
        continue
    r = result['r']
    print(f"\n--- 真实输出 (pv={r.prompt_version}, from_cache={r.from_cache}, pt={r.prompt_tokens}, ct={r.completion_tokens}) ---")
    resp = r.response_json
    print(f"has_prediction: {resp.get('has_prediction')}")
    print(f"flags: {resp.get('flags', [])}")
    preds = resp.get('predictions', [])
    print(f"predictions 数: {len(preds)}")
    for j, p in enumerate(preds, 1):
        print(f"  {j}. ticker={p.get('ticker')!r}  raw={p.get('raw_asset_mention')!r}")
        print(f"     market={p.get('market')!r}  direction={p.get('direction')!r}  conv={p.get('conviction')}  claim={p.get('claim_type')}")
        print(f"     thesis: {p.get('thesis_summary', '')[:200]}")
    print(f"\nextraction_notes: {resp.get('extraction_notes', '')[:500]}")

# 6) 总结
n_total_pred = sum(len(r['r'].response_json.get('predictions', [])) for r in results if r.get('r') and not r.get('error'))
n_consistent_true = sum(1 for r in results if r.get('has_pred_cached') and r.get('r') and r['r'].response_json.get('has_prediction') == True)
n_consistent_false = sum(1 for r in results if not r.get('has_pred_cached') and r.get('r') and r['r'].response_json.get('has_prediction') == False)
n_flipped = sum(1 for r in results if r.get('r') and r['r'].response_json.get('has_prediction') != r.get('has_pred_cached'))
print(f"\n\n{'='*80}")
print(f"统计: 实跑 30/30, 用时 {time.time()-t0:.0f}s, token 累加见每条 pt/ct")
print(f"  True 类(15): LLM 重判 True {n_consistent_true} / False {15 - n_consistent_true}")
print(f"  False 类(15): LLM 重判 False {n_consistent_false} / True {15 - n_consistent_false}")
print(f"  总翻转(对比原 cache): {n_flipped} (deterministic=0 应是最理想)")
print(f"="*80)
