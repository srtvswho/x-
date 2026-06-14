"""重跑后处理 v3 — 修 bug 后让 20 个 post 的合法 ticker 入库"""
import sqlite3, json, time, sys
sys.path.insert(0, "/workspace")

from signalboard.extract.caller import extract_one
from signalboard.extract.postprocess import llm_result_to_post_result, persist_post_result
from signalboard.extract.context import assemble, render_for_llm
from datetime import datetime, timezone

DB = "data/signalboard_full.db"
ts = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
print(f"[{ts}] 重跑 v3 (修 persist try/except) start", flush=True)

conn = sqlite3.connect(DB, timeout=60)
conn.execute("PRAGMA journal_mode=WAL")
conn.execute("PRAGMA synchronous=NORMAL")

# 只重跑 26 个 unresolved post(其它不动,避免 4463 已经正确的被破坏)
unresolved_pids = [r[0] for r in conn.execute(
    """SELECT DISTINCT post_id FROM human_review_queue WHERE reason='unresolved_ticker'""").fetchall()]
print(f"重跑 {len(unresolved_pids)} 个 post", flush=True)

# 先把现有 predictions 行保留(避免重复 upsert 行为改变)
# 不需要,persist_post_result 用 ON CONFLICT upsert 是幂等的

raw_map = {pid: r for pid, r in conn.execute("SELECT post_id, raw_json FROM raw_posts").fetchall()}

t0 = time.time()
n_added = 0
errors = []
for i, pid in enumerate(unresolved_pids, 1):
    try:
        rjson = raw_map.get(pid)
        if not rjson:
            errors.append((pid, "no raw_json"))
            continue
        item = json.loads(rjson)
        user_id = item.get("userId") or item.get("user_id")
        ctx = assemble(item, DB, source_user_id=user_id)
        assembled = render_for_llm(ctx)
        r = extract_one(pid, assembled, DB, use_cache=True)  # cache 命中
        if r.parse_error:
            errors.append((pid, r.parse_error))
            continue
        # 删除旧 predictions (让新跑重新入)
        n_before = conn.execute("SELECT count(*) FROM predictions WHERE post_id=?", (pid,)).fetchone()[0]
        post = llm_result_to_post_result(r, DB)
        # 删除 post 现有 predictions (re-persist 会 UPSERT,但旧的 ticker=None 已不会存在,因为现在有 try/except)
        # 实际之前 20 个 post 是 0 入表,所以没旧行;6 个有旧行的 post 重跑会 upsert 覆盖
        persist_post_result(post, DB, source_id="tw_aleabitoreddit", prompt_version="v1.4.1")
        n_after = conn.execute("SELECT count(*) FROM predictions WHERE post_id=?", (pid,)).fetchone()[0]
        n_added += (n_after - n_before)
    except Exception as e:
        errors.append((pid, str(e)))
    if i % 10 == 0 or i == len(unresolved_pids):
        print(f"  [{i}/{len(unresolved_pids)}] elapsed={time.time()-t0:.0f}s added={n_added}", flush=True)
conn.commit()
conn.close()

print(f"\nDone {time.time()-t0:.0f}s, errors={len(errors)}, new predictions added: {n_added}", flush=True)
