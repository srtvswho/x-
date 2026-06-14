"""抽 200 条预过滤通过的推文,跑真实 LLM 抽取,统计费用/延迟/预测密度。

读 v3 db,跑 DeepSeek-v4-pro。
"""
import sqlite3, random, json, time, pickle
random.seed(20260614)

from signalboard.extract.prefilter import prefilter_post
from signalboard.extract.caller import extract_one
from signalboard.extract.context import assemble, render_for_llm

DB = "data/signalboard_full.db"

conn = sqlite3.connect(DB, timeout=60)
all_rows = list(conn.execute('SELECT post_id, raw_text FROM raw_posts'))
print(f"total posts: {len(all_rows)}", flush=True)

# 预过滤
t0 = time.time()
passed_ids = []
for pid, txt in all_rows:
    res = prefilter_post(txt, db_path=DB)
    if res.passed:
        passed_ids.append(pid)
print(f"passed prefilter: {len(passed_ids)} ({time.time()-t0:.1f}s)", flush=True)

# 抽 200
sample_ids = random.sample(passed_ids, 200)
print(f"sampled 200", flush=True)

# 拼装
items = []
for pid in sample_ids:
    r = conn.execute("SELECT raw_json FROM raw_posts WHERE post_id=?", (pid,)).fetchone()
    item = json.loads(r[0])
    ctx = assemble(item, DB, source_user_id=item.get("userId"))
    items.append((pid, render_for_llm(ctx)))

# 跑
t_total = time.time()
results = []
errors = 0
for i, (pid, assembled) in enumerate(items, 1):
    t_start = time.time()
    r = extract_one(pid, assembled, DB, use_cache=False)
    elapsed = time.time() - t_start
    results.append({
        "post_id": pid, "elapsed": elapsed, "prompt_version": r.prompt_version,
        "model": r.model, "parse_error": r.parse_error,
        "response_json": r.response_json,
    })
    if r.parse_error:
        errors += 1
    if i % 25 == 0:
        print(f"  [{i}/200] {elapsed:.1f}s cum {(time.time()-t_total):.0f}s, err={errors}", flush=True)
elapsed_total = time.time() - t_total
print(f"\nTotal: {elapsed_total:.1f}s, errors: {errors}", flush=True)

# 保存
with open("/tmp/sample_200_raw.pkl", "wb") as f:
    pickle.dump(results, f)
print("saved to /tmp/sample_200_raw.pkl", flush=True)
