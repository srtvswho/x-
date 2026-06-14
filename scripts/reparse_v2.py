"""重跑后处理 — 包含 LLM ticker 兜底 (resolve_alias 未命中时检查 LLM 抽的 ticker)"""
import sqlite3, json, time, sys
sys.path.insert(0, "/workspace")

from signalboard.extract.caller import extract_one
from signalboard.extract.postprocess import llm_result_to_post_result, persist_post_result
from signalboard.extract.context import assemble, render_for_llm
from datetime import datetime, timezone

DB = "data/signalboard_full.db"
ts = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
print(f"[{ts}] 重跑 (含 LLM ticker 兜底) start", flush=True)

conn = sqlite3.connect(DB, timeout=60)
conn.execute("PRAGMA journal_mode=WAL")
conn.execute("PRAGMA synchronous=NORMAL")

for tbl in ("predictions", "post_flags", "human_review_queue"):
    conn.execute(f"DELETE FROM {tbl}")
conn.commit()
print("清空 done", flush=True)

rows = conn.execute(
    "SELECT post_id FROM extraction_cache WHERE prompt_version = ?",
    ("deepseek:deepseek-v4-pro:v1.4.1",),
).fetchall()
print(f"cached: {len(rows)} post_id", flush=True)

raw_map = {pid: r for pid, r in conn.execute("SELECT post_id, raw_json FROM raw_posts").fetchall()}

t0 = time.time()
n_p_new = 0
errors = []
for i, (pid,) in enumerate(rows, 1):
    try:
        rjson = raw_map.get(pid)
        if not rjson:
            errors.append((pid, "no raw_json"))
            continue
        item = json.loads(rjson)
        user_id = item.get("userId") or item.get("user_id")
        ctx = assemble(item, DB, source_user_id=user_id)
        assembled = render_for_llm(ctx)
        r = extract_one(pid, assembled, DB, use_cache=True)
        if r.parse_error:
            errors.append((pid, r.parse_error))
            continue
        post = llm_result_to_post_result(r, DB)
        persist_post_result(post, DB, source_id="tw_aleabitoreddit", prompt_version="v1.4.1")
        n_p_new += len(post.predictions)
    except Exception as e:
        errors.append((pid, str(e)))
    if i % 1000 == 0 or i == len(rows):
        print(f"  [{i}/{len(rows)}] elapsed={time.time()-t0:.0f}s n_p={n_p_new}", flush=True)
conn.commit()
conn.close()

print(f"\nDone {time.time()-t0:.0f}s, errors={len(errors)}", flush=True)
