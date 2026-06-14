"""全量 5657 条 v1.4.1 抽取 — 两阶段。

Phase 1: 8 worker 并发 LLM call(只调,不入库,纯网络+内存)
Phase 2: 1 线程批入库(1 个 sqlite3 连接,事务包裹,避免 NFS 锁竞争)

设计原因: NFS sqlite 锁竞争让 8 worker 完全串行化。LLM call 是真
网络(不锁 sqlite),所以 8 worker 并发能省时间。落库放到最后单线程批做。
"""
import os, sys, time, json, sqlite3, traceback
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timezone
from collections import Counter

sys.path.insert(0, '/workspace')
os.environ.setdefault('DEEPSEEK_API_KEY', '')

from signalboard.extract.caller import extract_one
from signalboard.extract.context import assemble, render_for_llm
from signalboard.extract.prefilter import prefilter_post
from signalboard.extract.postprocess import (
    llm_result_to_post_result, persist_post_result,
)
from signalboard.extract.config import CACHE_KEY_PROMPT_VERSION, ACTIVE_MODEL

DB = "data/signalboard_full.db"
WORKERS = 3  # Phase 1 LLM call 并发 — 3 worker 平衡点(1 慢,2/4/8 被 DeepSeek RPM 限流)

ts = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
OUT_DIR = f"/tmp/full5657_v141_{ts}"
os.makedirs(OUT_DIR, exist_ok=True)
os.makedirs(f"{OUT_DIR}/reports", exist_ok=True)

t_start = time.time()

# ===== 加载 + 预过滤 =====
print(f"[{ts}] start. WORKERS={WORKERS}, pv={CACHE_KEY_PROMPT_VERSION}", flush=True)
conn = sqlite3.connect(DB, timeout=30)
rows = conn.execute("SELECT post_id, raw_text, raw_json FROM raw_posts").fetchall()
# 预存 published_at 映射(批入库时用)
pub_at = {r[0]: (conn.execute("SELECT published_at, captured_at FROM raw_posts WHERE post_id=?", (r[0],)).fetchone() or ("","")) for r in rows}
conn.close()
print(f"loaded {len(rows)} posts", flush=True)

t0 = time.time()
to_run = []
for pid, text, rjson in rows:
    if prefilter_post(text, db_path=DB).passed:
        to_run.append((pid, rjson))
n_skip = len(rows) - len(to_run)
print(f"prefilter: {len(to_run)}/{len(rows)} passed ({time.time()-t0:.1f}s), skip {n_skip}", flush=True)

# ===== Phase 1: 8 worker LLM call =====
llm_results = []  # list of dict (parallel to to_run order may differ)
errors = []
stats = {
    "processed": 0, "success": 0, "failed": 0, "skipped_prefilter": n_skip,
    "has_pred": 0, "no_pred": 0, "parse_error": 0,
    "records_total": 0,
    "claim_type": Counter(),
    "conviction": Counter(),
    "flag_type": Counter(),
    "ticker": Counter(),
    "market": Counter(),
    "token_in": 0, "token_out": 0,
    "elapsed_total": 0.0,
}


def phase1_call(idx_pid_rjson):
    idx, pid, rjson = idx_pid_rjson
    t0 = time.time()
    try:
        item = json.loads(rjson)
        ctx = assemble(item, DB, source_user_id=item.get('userId'))
        assembled = render_for_llm(ctx)
        r = extract_one(pid, assembled, DB, use_cache=True)  # v1.4.1 cache 已存,直接命中避免重调
        elapsed = time.time() - t0
        if r.parse_error:
            return {"idx": idx, "post_id": pid, "ok": False, "error": r.parse_error,
                    "elapsed": elapsed, "pt": r.prompt_tokens, "ct": r.completion_tokens,
                    "r": None}
        resp = r.response_json
        return {"idx": idx, "post_id": pid, "ok": True, "error": None,
                "elapsed": elapsed, "pt": r.prompt_tokens, "ct": r.completion_tokens,
                "r": r, "resp": resp}
    except Exception as e:
        tb = traceback.format_exc()
        return {"idx": idx, "post_id": pid, "ok": False, "error": str(e) + "\n" + tb[:500],
                "elapsed": time.time() - t0, "pt": 0, "ct": 0, "r": None}


print(f"\n=== Phase 1: LLM call, {WORKERS} workers, {len(to_run)} posts ===", flush=True)
t0_phase1 = time.time()
t0 = t0_phase1
buffer = [None] * len(to_run)
with ThreadPoolExecutor(max_workers=WORKERS) as ex:
    futs = {ex.submit(phase1_call, (i, p, r)): i for i, (p, r) in enumerate(to_run)}
    for i, fut in enumerate(as_completed(futs), 1):
        result = fut.result()
        idx = result["idx"]
        buffer[idx] = result
        stats["processed"] += 1
        stats["token_in"] += result["pt"]
        stats["token_out"] += result["ct"]
        stats["elapsed_total"] += result["elapsed"]
        if not result["ok"]:
            stats["failed"] += 1
            errors.append((result["post_id"], result["error"]))
        else:
            stats["success"] += 1
            if result["r"].parse_error:
                stats["parse_error"] += 1
            resp = result["resp"]
            if resp.get('has_prediction'):
                stats["has_pred"] += 1
                preds = resp.get('predictions', [])
                stats["records_total"] += len(preds)
                for p in preds:
                    stats["claim_type"][p.get('claim_type') or 'unknown'] += 1
                    stats["conviction"][p.get('conviction') if p.get('conviction') is not None else 'null'] += 1
                    stats["ticker"][p.get('ticker') or 'null'] += 1
                    stats["market"][p.get('market') or 'null'] += 1
            else:
                stats["no_pred"] += 1
            for f in resp.get('flags', []):
                stats["flag_type"][f] += 1
        if i % 100 == 0 or i == len(to_run):
            elapsed = time.time() - t0_phase1
            rate = i / elapsed
            eta = (len(to_run) - i) / rate if rate else 0
            print(f"  [{i:4d}/{len(to_run)}] elapsed={elapsed:.0f}s rate={rate:.2f}/s ETA={eta:.0f}s "
                  f"succ={stats['success']} fail={stats['failed']} "
                  f"tok={stats['token_in']/1000:.1f}K/{stats['token_out']/1000:.1f}K", flush=True)

phase1_time = time.time() - t0_phase1
print(f"\nPhase 1 done: {phase1_time:.0f}s ({len(to_run)/phase1_time:.2f}/s)", flush=True)

# ===== Phase 2: 1 线程批入库 =====
print(f"\n=== Phase 2: 批量落库,1 线程 ===", flush=True)
t0_phase2 = time.time()
# 失败的不入库
to_persist = [b for b in buffer if b and b["ok"] and b["r"] is not None and b["r"].response_json is not None]
n_already_persisted = 0
conn = sqlite3.connect(DB, timeout=60)
conn.execute("PRAGMA journal_mode=WAL")
conn.execute("PRAGMA synchronous=NORMAL")
try:
    for i, b in enumerate(to_persist, 1):
        try:
            r = b["r"]
            post = llm_result_to_post_result(r, DB)
            persist_post_result(post, DB,
                                source_id='tw_aleabitoreddit',
                                prompt_version=r.prompt_version.replace('deepseek:deepseek-v4-pro:', ''))
        except Exception as e:
            errors.append((b["post_id"], f"persist: {e}"))
        if i % 200 == 0:
            print(f"  persist [{i}/{len(to_persist)}] elapsed={time.time()-t0_phase2:.0f}s", flush=True)
    conn.commit()
finally:
    conn.close()

phase2_time = time.time() - t0_phase2
print(f"Phase 2 done: {phase2_time:.0f}s", flush=True)

total_time = time.time() - t_start

# ===== 落库验证 + 汇总 =====
INPUT_PRICE = 0.27 / 1_000_000
OUTPUT_PRICE = 1.10 / 1_000_000
actual_cost = stats['token_in'] * INPUT_PRICE + stats['token_out'] * OUTPUT_PRICE

conn = sqlite3.connect(DB, timeout=30)
pred_n = conn.execute("SELECT count(*) FROM predictions").fetchone()[0]
pred_distinct = conn.execute("SELECT count(DISTINCT post_id) FROM predictions").fetchone()[0]
flag_n = conn.execute("SELECT count(*) FROM post_flags").fetchone()[0]
unresolved_n = conn.execute("SELECT count(*) FROM human_review_queue WHERE reason='unresolved_ticker'").fetchone()[0]
unresolved_full = conn.execute("SELECT count(*) FROM human_review_queue").fetchone()[0]
cache_n = conn.execute("SELECT count(*) FROM extraction_cache").fetchone()[0]
cache_pv = list(conn.execute("SELECT DISTINCT prompt_version FROM extraction_cache"))
repeat_n = conn.execute("SELECT count(*) FROM predictions WHERE is_repeat_call=1").fetchone()[0]
unresolved_raw = conn.execute(
    """SELECT json_extract(payload, '$.raw_mention') as rm, count(*) as c
       FROM human_review_queue WHERE reason='unresolved_ticker'
       GROUP BY rm ORDER BY c DESC LIMIT 50""").fetchall()
unresolved_distinct_posts = conn.execute(
    """SELECT count(DISTINCT post_id) FROM human_review_queue WHERE reason='unresolved_ticker'""").fetchone()[0]
conn.close()

# trace.jsonl
with open(f"{OUT_DIR}/trace.jsonl", "w") as f:
    for b in buffer:
        if b is None: continue
        if b["ok"]:
            resp = b["r"].response_json
            preds = resp.get('predictions', [])
            tickers = [p.get('ticker') for p in preds]
            flags = resp.get('flags', [])
            has_pred = resp.get('has_prediction')
        else:
            tickers = []; flags = []; has_pred = None
        f.write(json.dumps({
            "post_id": b["post_id"], "ok": b["ok"],
            "elapsed": round(b["elapsed"], 2), "pt": b["pt"], "ct": b["ct"],
            "has_pred": has_pred,
            "n_records": len(tickers), "tickers": tickers, "flags": flags,
            "error": b["error"][:200] if b["error"] else None,
        }, ensure_ascii=False) + "\n")

# summary
report = f"""# 全量 5657 条 v1.4.1 抽取汇总报告

**运行时间**: {ts}  
**总耗时**: {total_time:.0f}s ({total_time/60:.1f}min)  
  - Phase 1 (LLM call, {WORKERS} workers): {phase1_time:.0f}s
  - Phase 2 (1 线程批入库): {phase2_time:.0f}s
**Prompt Version**: {CACHE_KEY_PROMPT_VERSION}  
**Model**: {ACTIVE_MODEL}

## 1. 处理统计

| 项 | 值 |
|---|---|
| raw_posts 总数 | {len(rows)} |
| 预过滤通过 | {len(to_run)} ({len(to_run)/len(rows)*100:.1f}%) |
| 预过滤跳过 | {stats['skipped_prefilter']} |
| 实际处理 | {stats['processed']} |
| 成功 (LLM OK) | {stats['success']} |
| 失败 (parse/exception) | {stats['failed']} |
| parse_error (LLM 返但 JSON 错) | {stats['parse_error']} |
| LLM 实际吞吐 | {len(to_run)/phase1_time:.2f} 条/s |

## 2. 预测统计

| 项 | 值 |
|---|---|
| has_prediction=true | {stats['has_pred']} ({stats['has_pred']/max(stats['processed'],1)*100:.1f}%) |
| has_prediction=false | {stats['no_pred']} ({stats['no_pred']/max(stats['processed'],1)*100:.1f}%) |
| 总 PredictionRecord (LLM 抽) | {stats['records_total']} |
| 平均 records/post (有预测) | {stats['records_total']/max(stats['has_pred'],1):.2f} |
| 落库 is_repeat_call | {repeat_n} |

### Claim Type 分布
"""
for k, v in stats['claim_type'].most_common():
    report += f"- `{k}`: {v}\n"
report += "\n### Conviction 分布\n"
for k, v in sorted(stats['conviction'].items(), key=lambda x: str(x[0])):
    report += f"- `{k}`: {v}\n"
report += "\n### Flag 类型计数\n"
for k, v in stats['flag_type'].most_common():
    report += f"- `{k}`: {v}\n"
report += "\n### Ticker Top 30\n"
for k, v in stats['ticker'].most_common(30):
    report += f"- `{k}`: {v}\n"
if len(stats['ticker']) > 30:
    report += f"\n(还有 {len(stats['ticker'])-30} 个 ticker)\n"
report += "\n### Market 分布\n"
for k, v in stats['market'].most_common():
    report += f"- `{k}`: {v}\n"

report += f"\n## 3. 错误明细\n\n失败数: {stats['failed']}\n\n"
if errors:
    for i, (pid, err) in enumerate(errors[:30], 1):
        report += f"{i}. `{pid}`: {err[:200]}\n"
    if len(errors) > 30:
        report += f"\n(还有 {len(errors)-30} 条,见 errors.json)\n"
else:
    report += "无错误\n"

report += f"\n## 4. 未解析 ticker(unresolved)\n\n"
report += f"human_review_queue `unresolved_ticker` 总条数: **{unresolved_n}**\n\n"
report += f"涉及 distinct post_id: **{unresolved_distinct_posts}**\n\n"
if unresolved_raw:
    report += "### 按 raw_mention 分布(Top 50)\n"
    for rm, c in unresolved_raw:
        report += f"- `{rm}`: {c}\n"

report += f"\n## 5. Token 用量 & 实际费用\n\n"
report += f"| 项 | 值 |\n|---|---|\n"
report += f"| 累计 prompt_tokens | {stats['token_in']:,} |\n"
report += f"| 累计 completion_tokens | {stats['token_out']:,} |\n"
report += f"| 累计 total_tokens | {stats['token_in']+stats['token_out']:,} |\n"
report += f"| 输入价 (per 1M) | $0.27 |\n"
report += f"| 输出价 (per 1M) | $1.10 |\n"
report += f"| **实际总费用** | **${actual_cost:.4f}** |\n"
report += f"| 之前 200-sample 估算 | $5.18 |\n"
report += f"| 实际 vs 估算 | {actual_cost/5.18*100:.1f}% |\n"
report += f"| 平均每条费用 | ${actual_cost/max(stats['processed'],1)*1000:.4f}¢ |\n"

report += f"\n## 6. 落库验证\n\n"
report += f"| 表 | 行数 |\n|---|---|\n"
report += f"| predictions | {pred_n} ({pred_distinct} distinct post_id) |\n"
report += f"| post_flags | {flag_n} |\n"
report += f"| human_review_queue (unresolved_ticker) | {unresolved_n} |\n"
report += f"| human_review_queue (all) | {unresolved_full} |\n"
report += f"| extraction_cache | {cache_n} |\n"
report += f"| 唯一 prompt_version | {[r[0] for r in cache_pv]} |\n"

with open(f"{OUT_DIR}/reports/summary.md", "w", encoding="utf-8") as f:
    f.write(report)

if errors:
    with open(f"{OUT_DIR}/reports/errors.json", "w", encoding="utf-8") as f:
        json.dump([{"post_id": p, "error": e} for p, e in errors], f, ensure_ascii=False, indent=2)

status = {
    "ts": ts, "phase1_s": round(phase1_time, 1), "phase2_s": round(phase2_time, 1),
    "total_s": round(total_time, 1),
    "processed": stats["processed"], "success": stats["success"],
    "failed": stats["failed"], "parse_error": stats["parse_error"],
    "skipped_prefilter": stats["skipped_prefilter"],
    "has_pred": stats["has_pred"], "no_pred": stats["no_pred"],
    "records_total": stats["records_total"],
    "unresolved_n": unresolved_n,
    "pred_n": pred_n, "pred_distinct": pred_distinct,
    "flag_n": flag_n, "cache_n": cache_n, "repeat_n": repeat_n,
    "token_in": stats["token_in"], "token_out": stats["token_out"],
    "actual_cost_usd": round(actual_cost, 4),
    "out_dir": OUT_DIR,
}
with open(f"{OUT_DIR}/reports/status.json", "w") as f:
    json.dump(status, f, indent=2)

print(f"\nDONE.", flush=True)
print(f"  {stats['success']} success / {stats['failed']} failed / {stats['skipped_prefilter']} prefilter-skipped", flush=True)
print(f"  has_pred: {stats['has_pred']} ({stats['has_pred']/max(stats['processed'],1)*100:.1f}%)", flush=True)
print(f"  records: {stats['records_total']}", flush=True)
print(f"  cost: ${actual_cost:.4f}  vs  估算 $5.18", flush=True)
print(f"  out: {OUT_DIR}/reports/summary.md", flush=True)
