"""基准: 只测 LLM call(无落库)速度,4 worker"""
import os, sys, time, json
from concurrent.futures import ThreadPoolExecutor, as_completed

sys.path.insert(0, '/workspace')
os.environ.setdefault('DEEPSEEK_API_KEY', '')

from signalboard.extract.caller import extract_one
from signalboard.extract.context import assemble, render_for_llm
from signalboard.extract.prefilter import prefilter_post
import sqlite3

DB = "data/signalboard_full.db"

conn = sqlite3.connect(DB, timeout=30)
rows = conn.execute("SELECT post_id, raw_text, raw_json FROM raw_posts").fetchall()
conn.close()

# 预过滤
to_run = []
for pid, text, rjson in rows:
    if prefilter_post(text, db_path=DB).passed:
        to_run.append((pid, rjson))
print(f"to_run: {len(to_run)}")

# 只测前 200 条,4 worker
sample = to_run[:200]

def call_only(pid, rjson):
    t0 = time.time()
    try:
        item = json.loads(rjson)
        ctx = assemble(item, DB, source_user_id=item.get('userId'))
        assembled = render_for_llm(ctx)
        r = extract_one(pid, assembled, DB, use_cache=False)
        return (time.time() - t0, r.prompt_tokens, r.completion_tokens, r.parse_error, r.response_json.get('has_prediction'))
    except Exception as e:
        return (time.time() - t0, 0, 0, str(e), None)

t0 = time.time()
for n in (1, 2, 4, 8):
    # 跳过第一次 1 worker 测 (为了对照),用 4 worker 当主测
    with ThreadPoolExecutor(max_workers=n) as ex:
        futs = [ex.submit(call_only, p, r) for p, r in sample[:80]]
        results = [f.result() for f in as_completed(futs)]
    elapsed = time.time() - t0
    succ = sum(1 for r in results if r[3] is None)
    total_tok_in = sum(r[1] for r in results)
    total_tok_out = sum(r[2] for r in results)
    print(f"  workers={n} sample={len(futs)} elapsed={elapsed:.1f}s "
          f"rate={len(futs)/elapsed:.2f}/s succ={succ} "
          f"tok={total_tok_in/1000:.1f}K/{total_tok_out/1000:.1f}K")
    t0 = time.time()
