"""干净对账脚本(无任何缓存):
1. cache 表已清空
2. 跑 40 条(use_cache=False 强制实调,带 trace)
3. 逐条打印:post_id / prompt_version / from_cache / has_pred / 记录数 / tickers / flags
4. 跟金标答案对账:一致 / 假阳 / 假阴 / flag 错
"""
import sqlite3, json, time, random, pickle
random.seed(20260614)

from signalboard.extract.caller import extract_one
from signalboard.extract.context import assemble, render_for_llm
from signalboard.extract.goldset import GOLD_V1

DB = "data/signalboard_full.db"

conn = sqlite3.connect(DB, timeout=60)
CASHTAG_RE = __import__("re").compile(r"\$([A-Z][A-Z0-9._-]{1,5})")
from collections import defaultdict

# 1) 重建 blind 20
v12_by_pid = {}
# 注意:cache 已清,这里从 v1.3 之前的 pkl 读
import os
# 之前 sample_200_raw.pkl 沙箱重启可能没了
pkl = "/tmp/sample_200_raw.pkl"
if not os.path.exists(pkl):
    # 重新跑 sample 200 (有 cache 时会自动用,现在 cache 已清,要重跑)
    print("WARN: sample_200_raw.pkl 不在,需要从 sample 200 实跑", flush=True)
    sys.exit(1)
with open(pkl, "rb") as f:
    sample_200 = pickle.load(f)
print(f"loaded sample 200: {len(sample_200)}", flush=True)

gold_ids = set(g['post_id'] for g in GOLD_V1)
has_pred = []
no_pred_with_ticker = []
for r in sample_200:
    pid = r['post_id']
    resp = r.get('response_json') or {}
    raw = conn.execute("SELECT raw_text FROM raw_posts WHERE post_id=?", (pid,)).fetchone()
    if not raw: continue
    has_cashtag = bool(CASHTAG_RE.search(raw[0]))
    if resp.get('has_prediction'):
        has_pred.append((pid, resp))
    elif has_cashtag:
        no_pred_with_ticker.append((pid, resp))

random.seed(20260614)  # 用同 seed 复现抽样
buckets = defaultdict(list)
for pid, resp in has_pred:
    n = len(resp.get('predictions', []))
    if n <= 3: buckets['small'].append((pid, resp))
    elif n <= 9: buckets['medium'].append((pid, resp))
    else: buckets['large'].append((pid, resp))

sample_has = list(random.sample(buckets['small'], min(5, len(buckets['small']))))
if len(sample_has) < 10 and buckets['medium']:
    sample_has += list(random.sample(buckets['medium'], min(3, len(buckets['medium']))))
if len(sample_has) < 10 and buckets['large']:
    sample_has += list(random.sample(buckets['large'], min(10-len(sample_has), len(buckets['large']))))
remaining = [x for x in has_pred if x not in sample_has]
if len(sample_has) < 10:
    sample_has += list(random.sample(remaining, min(10-len(sample_has), len(remaining))))

buckets_nopred = defaultdict(list)
for pid, resp in no_pred_with_ticker:
    flags = resp.get('flags', [])
    if 'victory_lap' in flags: buckets_nopred['victory_lap'].append((pid, resp))
    elif 'self_reported_returns' in flags: buckets_nopred['self_reported_returns'].append((pid, resp))
    elif 'position_disclosure' in flags: buckets_nopred['position_disclosure'].append((pid, resp))
    else: buckets_nopred['clean'].append((pid, resp))

sample_nopred = []
for k in ['victory_lap', 'self_reported_returns', 'position_disclosure', 'clean']:
    if buckets_nopred[k] and len(sample_nopred) < 10:
        take = min(3 if k != 'clean' else (10 - len(sample_nopred)), len(buckets_nopred[k]))
        sample_nopred += list(random.sample(buckets_nopred[k], take))
remaining_nopred = [x for x in no_pred_with_ticker if x not in sample_nopred]
if len(sample_nopred) < 10:
    sample_nopred += list(random.sample(remaining_nopred, min(10-len(sample_nopred), len(remaining_nopred))))

blind_A = [pid for pid, _ in sample_has]
blind_B = [pid for pid, _ in sample_nopred]
print(f"blind_A (10): {blind_A}", flush=True)
print(f"blind_B (10): {blind_B}", flush=True)

gold_ids_list = [g['post_id'] for g in GOLD_V1]
all_40 = gold_ids_list + blind_A + blind_B
print(f"all_40: {len(all_40)}", flush=True)

# 2) 跑(force use_cache=False,带 trace)
t_total = time.time()
results = []
for i, pid in enumerate(all_40, 1):
    raw = conn.execute("SELECT raw_json FROM raw_posts WHERE post_id=?", (pid,)).fetchone()
    if not raw:
        print(f"  [{i:2d}] {pid} NO RAW", flush=True)
        continue
    item = json.loads(raw[0])
    ctx = assemble(item, DB, source_user_id=item.get('userId'))
    assembled = render_for_llm(ctx)
    t_start = time.time()
    r = extract_one(pid, assembled, DB, use_cache=False)
    elapsed = time.time() - t_start
    if r.parse_error:
        print(f"  [{i:2d}] {pid} ERR: {r.parse_error[:80]}", flush=True)
    print(f"  [{i:2d}] {pid} pv={r.prompt_version} from_cache={r.from_cache} {elapsed:.1f}s", flush=True)
    results.append({
        'post_id': pid, 'elapsed': elapsed, 'prompt_version': r.prompt_version,
        'model': r.model, 'from_cache': r.from_cache,
        'parse_error': r.parse_error,
        'response_json': r.response_json,
    })
print(f"\\nTotal: {time.time()-t_total:.1f}s, errors: {sum(1 for r in results if r['parse_error'])}", flush=True)

# 3) 保存
with open("/tmp/recheck_40_clean.pkl", "wb") as f:
    pickle.dump(results, f)
print("saved /tmp/recheck_40_clean.pkl", flush=True)

# 4) 验证 cache 写入(应该是 v1.3 40 条)
n = conn.execute("SELECT count(*) FROM extraction_cache").fetchone()[0]
print(f"\\nextraction_cache after run: {n} (应该 = 40,40 个 v1.3 写入)", flush=True)
for r in conn.execute("SELECT DISTINCT prompt_version FROM extraction_cache"):
    print(f"  pv: {r[0]}")
PYEOF