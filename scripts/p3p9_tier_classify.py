"""P3-9 预测质量分层 (tier_A / tier_B / tier_C)

判定:
- tier_B 清单型: 同 post_id 抽出 ≥ 8 个 prediction
- tier_A 核心论证型: 同 post_id < 4 个 prediction AND thesis_summary 详细(>50 字符) AND raw_text > 400 字符
- tier_C 顺带提及: 中间地带 / 短文本 / 单 ticker 重复

输出:
1. 每档条数分布
2. tier_A 样本量 + 列表
"""
import os, sqlite3, re, json
from datetime import datetime
from collections import Counter, defaultdict
import statistics

DB = "/workspace/data/signalboard_full.db"
OUT_DIR = "/workspace/outputs"
conn = sqlite3.connect(DB, timeout=30)
c = conn.cursor()

# 拉全部 prediction
sql = """
SELECT p.prediction_id, p.ticker, p.direction, p.horizon, p.thesis_summary, p.is_repeat_call,
       p.post_id, p.published_at, p.price_source_available
FROM predictions p
WHERE p.price_source_available=1
"""
all_p = c.execute(sql).fetchall()
print(f"全部 prediction: {len(all_p)}")

# 按 post_id 分组,统计每个 post_id 抽出的 prediction 数
post_to_pids = defaultdict(list)
pid_to_post = {}
for r in all_p:
    pid, ticker, direction, horizon, thesis, repeat, post_id, pub, avail = r
    post_to_pids[post_id].append((pid, ticker, direction, horizon, thesis, repeat, pub))
    pid_to_post[pid] = post_id

# 每条 post 的 prediction 数
post_pred_count = {post: len(pids) for post, pids in post_to_pids.items()}
print(f"不同 post_id 数: {len(post_to_pids)}")
print(f"每 post 平均 prediction: {sum(post_pred_count.values())/len(post_pred_count):.1f}")

# 拉 raw_text
print("拉 raw_text...")
pid_to_text = {}
for post_id in post_to_pids:
    r = c.execute("SELECT raw_text FROM raw_posts WHERE post_id=?", (post_id,)).fetchone()
    if r:
        pid_to_text[post_id] = r[0] or ""
    else:
        pid_to_text[post_id] = ""

# 拉 verifications 1m 数据
print("拉 verifications 1m...")
v_data = {}
for r in c.execute("SELECT prediction_id, h_1m_status, h_1m_excess_return, h_1m_raw_return FROM verifications"):
    v_data[r[0]] = r

# 给每条 prediction 打 tier
tier_assignments = []  # (pid, ticker, direction, post_id, n_post_preds, thesis_len, raw_text_len, tier)
for r in all_p:
    pid, ticker, direction, horizon, thesis, repeat, post_id, pub, avail = r
    n_post_preds = post_pred_count[post_id]
    thesis_len = len(thesis) if thesis else 0
    raw_text_len = len(pid_to_text.get(post_id, ""))
    
    # 判定
    if n_post_preds >= 8:
        tier = "B"
    elif n_post_preds <= 3 and thesis_len > 50 and raw_text_len > 400:
        tier = "A"
    else:
        tier = "C"
    
    tier_assignments.append((pid, ticker, direction, post_id, n_post_preds, thesis_len, raw_text_len, tier, pub))

# 统计
tier_count = Counter(t[7] for t in tier_assignments)
print(f"\n分档结果:")
for t, n in sorted(tier_count.items()):
    print(f"  tier_{t}: {n} ({n/len(tier_assignments)*100:.1f}%)")

# tier_A 的 ticker 分布
tier_a = [t for t in tier_assignments if t[7] == "A"]
tier_b = [t for t in tier_assignments if t[7] == "B"]
tier_c = [t for t in tier_assignments if t[7] == "C"]
print(f"\ntier_A ticker 分布:")
a_ticker_count = Counter(t[1] for t in tier_a)
for t, n in sorted(a_ticker_count.items(), key=lambda x: -x[1])[:30]:
    print(f"  {t}: {n}")

# tier_B 推文数量
b_posts = set(t[3] for t in tier_b)
print(f"\ntier_B 推文数: {len(b_posts)} 篇 (含 {len(tier_b)} 个 prediction)")

# tier_A 的 1m hit_rate
tier_a_v = []
for t in tier_a:
    v = v_data.get(t[0])
    if v:
        s1m, e1m, r1m = v[1], v[2], v[3]
        if s1m in ("resolved_hit", "resolved_miss"):
            tier_a_v.append((t, s1m, e1m, r1m))

print(f"\ntier_A 中 1m resolved: {len(tier_a_v)} / {len(tier_a)} ({len(tier_a_v)/len(tier_a)*100:.1f}%)")
hits = sum(1 for v in tier_a_v if v[1] == "resolved_hit")
print(f"tier_A 1m hit_rate: {hits/len(tier_a_v)*100 if tier_a_v else 0:.1f}%")

# 全 4 horizon hit_rate (tier_A)
sql = """
SELECT prediction_id, h_1w_status, h_1w_excess_return, h_1m_status, h_1m_excess_return,
       h_3m_status, h_3m_excess_return, h_6m_status, h_6m_excess_return
FROM verifications
"""
v_all = {r[0]: r for r in c.execute(sql)}

print(f"\n=== tier_A per-horizon 统计 ===")
for h, st_idx, exc_idx in [("1w", 1, 2), ("1m", 3, 4), ("3m", 5, 6), ("6m", 7, 8)]:
    n_res, n_h = 0, 0
    exc_vals = []
    for t in tier_a:
        v = v_all.get(t[0])
        if not v: continue
        s = v[st_idx]
        e = v[exc_idx]
        if s == "resolved_hit":
            n_res += 1
            n_h += 1
            if isinstance(e, (int, float)): exc_vals.append(e)
        elif s == "resolved_miss":
            n_res += 1
            if isinstance(e, (int, float)): exc_vals.append(e)
    hr = n_h/n_res*100 if n_res else 0
    med = statistics.median(exc_vals)*100 if exc_vals else None
    avg = statistics.mean(exc_vals)*100 if exc_vals else None
    print(f"  {h}: n_resolved={n_res} hit_rate={hr:.1f}% med_exc={med if med is not None else 0:+.2f}% avg_exc={avg if avg is not None else 0:+.2f}%")

# tier_B per-horizon
print(f"\n=== tier_B per-horizon 统计 (清单扫货,预期 ~50%) ===")
for h, st_idx, exc_idx in [("1w", 1, 2), ("1m", 3, 4), ("3m", 5, 6), ("6m", 7, 8)]:
    n_res, n_h = 0, 0
    exc_vals = []
    for t in tier_b:
        v = v_all.get(t[0])
        if not v: continue
        s = v[st_idx]
        e = v[exc_idx]
        if s == "resolved_hit":
            n_res += 1
            n_h += 1
            if isinstance(e, (int, float)): exc_vals.append(e)
        elif s == "resolved_miss":
            n_res += 1
            if isinstance(e, (int, float)): exc_vals.append(e)
    hr = n_h/n_res*100 if n_res else 0
    med = statistics.median(exc_vals)*100 if exc_vals else None
    print(f"  {h}: n_resolved={n_res} hit_rate={hr:.1f}% med_exc={med if med is not None else 0:+.2f}%")

# tier_C
print(f"\n=== tier_C per-horizon 统计 ===")
for h, st_idx, exc_idx in [("1w", 1, 2), ("1m", 3, 4), ("3m", 5, 6), ("6m", 7, 8)]:
    n_res, n_h = 0, 0
    exc_vals = []
    for t in tier_c:
        v = v_all.get(t[0])
        if not v: continue
        s = v[st_idx]
        e = v[exc_idx]
        if s == "resolved_hit":
            n_res += 1
            n_h += 1
            if isinstance(e, (int, float)): exc_vals.append(e)
        elif s == "resolved_miss":
            n_res += 1
            if isinstance(e, (int, float)): exc_vals.append(e)
    hr = n_h/n_res*100 if n_res else 0
    med = statistics.median(exc_vals)*100 if exc_vals else None
    print(f"  {h}: n_resolved={n_res} hit_rate={hr:.1f}% med_exc={med if med is not None else 0:+.2f}%")

# tier_A 详细列表
print()
print("=== tier_A 详细列表 (前 30 条) ===")
for i, t in enumerate(tier_a[:30]):
    pid, ticker, direction, post_id, n_post_preds, thesis_len, raw_text_len, tier, pub = t
    v = v_all.get(pid)
    s1m = v[3] if v else "?"
    e1m = v[4] if v and isinstance(v[4], (int, float)) else 0
    print(f"  [{i+1}] {ticker:6s} {direction:6s} pub={pub[:10]} post_preds={n_post_preds} thesis_len={thesis_len} raw_len={raw_text_len} 1m: {s1m} exc={e1m*100:+.1f}%")

# 落报告
out_md = []
out_md.append("# P3-9 预测质量分层 (tier_A / tier_B / tier_C)")
out_md.append("")
out_md.append(f"**生成时间**: {datetime.utcnow().isoformat()}Z")
out_md.append("")
out_md.append("## 0. 判定规则")
out_md.append("")
out_md.append("- **tier_A 核心论证型**: 同 post_id 抽出 ≤ 3 个 prediction **AND** thesis_summary > 50 字符 **AND** raw_text > 400 字符")
out_md.append("- **tier_B 清单扫货型**: 同 post_id 抽出 ≥ 8 个 prediction (典型 'Strong Buy/Buy/Hold/Sell/Strong Sell' 评级)")
out_md.append("- **tier_C 顺带提及**: 中间地带 (post 4-7 个 prediction, 或 thesis 短)")
out_md.append("")
out_md.append("## 1. 总体分档")
out_md.append("")
out_md.append("| Tier | n | 占比 |")
out_md.append("|---|---|---|")
out_md.append(f"| **tier_A 核心论证** | {len(tier_a)} | {len(tier_a)/len(tier_assignments)*100:.1f}% |")
out_md.append(f"| tier_B 清单扫货 | {len(tier_b)} | {len(tier_b)/len(tier_assignments)*100:.1f}% |")
out_md.append(f"| tier_C 顺带提及 | {len(tier_c)} | {len(tier_c)/len(tier_assignments)*100:.1f}% |")
out_md.append(f"| 总 | {len(tier_assignments)} | 100% |")
out_md.append("")
out_md.append(f"**注**: tier_B 来自 {len(b_posts)} 篇推文(批量扫货)")
out_md.append("")
out_md.append("## 2. tier_A ticker 分布 (top 30)")
out_md.append("")
out_md.append("| ticker | n |")
out_md.append("|---|---|")
for t, n in sorted(a_ticker_count.items(), key=lambda x: -x[1])[:30]:
    out_md.append(f"| {t} | {n} |")
out_md.append("")

# tier_A per horizon
out_md.append("## 3. tier_A per-horizon 统计 (核心论证,真研究能力)")
out_md.append("")
out_md.append("| horizon | n_resolved | hit_rate | median_exc | avg_exc |")
out_md.append("|---|---|---|---|---|")
for h, st_idx, exc_idx in [("1w", 1, 2), ("1m", 3, 4), ("3m", 5, 6), ("6m", 7, 8)]:
    n_res, n_h = 0, 0
    exc_vals = []
    for t in tier_a:
        v = v_all.get(t[0])
        if not v: continue
        s = v[st_idx]
        e = v[exc_idx]
        if s == "resolved_hit":
            n_res += 1
            n_h += 1
            if isinstance(e, (int, float)): exc_vals.append(e)
        elif s == "resolved_miss":
            n_res += 1
            if isinstance(e, (int, float)): exc_vals.append(e)
    hr = n_h/n_res*100 if n_res else 0
    med = statistics.median(exc_vals)*100 if exc_vals else None
    avg = statistics.mean(exc_vals)*100 if exc_vals else None
    med_s = f"{med:+.2f}%" if med is not None else "N/A"
    avg_s = f"{avg:+.2f}%" if avg is not None else "N/A"
    out_md.append(f"| {h} | {n_res} | {hr:.1f}% | {med_s} | {avg_s} |")
out_md.append("")

# tier_B per horizon
out_md.append("## 4. tier_B per-horizon 统计 (清单扫货,预期 ~50% 接近 beta)")
out_md.append("")
out_md.append("| horizon | n_resolved | hit_rate | median_exc |")
out_md.append("|---|---|---|---|")
for h, st_idx, exc_idx in [("1w", 1, 2), ("1m", 3, 4), ("3m", 5, 6), ("6m", 7, 8)]:
    n_res, n_h = 0, 0
    exc_vals = []
    for t in tier_b:
        v = v_all.get(t[0])
        if not v: continue
        s = v[st_idx]
        e = v[exc_idx]
        if s == "resolved_hit":
            n_res += 1
            n_h += 1
            if isinstance(e, (int, float)): exc_vals.append(e)
        elif s == "resolved_miss":
            n_res += 1
            if isinstance(e, (int, float)): exc_vals.append(e)
    hr = n_h/n_res*100 if n_res else 0
    med = statistics.median(exc_vals)*100 if exc_vals else None
    med_s = f"{med:+.2f}%" if med is not None else "N/A"
    out_md.append(f"| {h} | {n_res} | {hr:.1f}% | {med_s} |")
out_md.append("")

# tier_C
out_md.append("## 5. tier_C per-horizon 统计")
out_md.append("")
out_md.append("| horizon | n_resolved | hit_rate | median_exc |")
out_md.append("|---|---|---|---|")
for h, st_idx, exc_idx in [("1w", 1, 2), ("1m", 3, 4), ("3m", 5, 6), ("6m", 7, 8)]:
    n_res, n_h = 0, 0
    exc_vals = []
    for t in tier_c:
        v = v_all.get(t[0])
        if not v: continue
        s = v[st_idx]
        e = v[exc_idx]
        if s == "resolved_hit":
            n_res += 1
            n_h += 1
            if isinstance(e, (int, float)): exc_vals.append(e)
        elif s == "resolved_miss":
            n_res += 1
            if isinstance(e, (int, float)): exc_vals.append(e)
    hr = n_h/n_res*100 if n_res else 0
    med = statistics.median(exc_vals)*100 if exc_vals else None
    med_s = f"{med:+.2f}%" if med is not None else "N/A"
    out_md.append(f"| {h} | {n_res} | {hr:.1f}% | {med_s} |")
out_md.append("")

# tier_A 详细列表
out_md.append("## 6. tier_A 详细列表 (前 50 条,按 published_at 排序)")
out_md.append("")
out_md.append("| # | ticker | dir | pub | entry | n_post_preds | thesis_len | raw_text_len | 1m | 1m_excess |")
out_md.append("|---|---|---|---|---|---|---|---|---|---|")
sorted_tier_a = sorted(tier_a, key=lambda x: x[8])
for i, t in enumerate(sorted_tier_a[:50]):
    pid, ticker, direction, post_id, n_post_preds, thesis_len, raw_text_len, tier, pub = t
    v = v_all.get(pid)
    s1m = v[3] if v else "?"
    e1m = v[4] if v and isinstance(v[4], (int, float)) else 0
    out_md.append(f"| {i+1} | {ticker} | {direction} | {pub[:10]} | {t[4]} | {n_post_preds} | {thesis_len} | {raw_text_len} | {s1m} | {e1m*100:+.1f}% |")
out_md.append("")

# tier_A 时间分布(2025 vs 2026)
out_md.append("## 7. tier_A 时间分布")
out_md.append("")
out_md.append("| 时期 | n |")
out_md.append("|---|---|")
early_2025 = sum(1 for t in tier_a if t[8] and t[8] < "2026-01-01")
late_2026 = sum(1 for t in tier_a if t[8] and t[8] >= "2026-01-01")
out_md.append(f"| 2025 (前期) | {early_2025} |")
out_md.append(f"| 2026 (后期) | {late_2026} |")
out_md.append("")

with open(os.path.join(OUT_DIR, "phase3_p9_tier_classify.md"), "w", encoding="utf-8") as f:
    f.write("\n".join(out_md))
print(f"\n✅ 落 outputs/phase3_p9_tier_classify.md")

# 保存 tier 分类到文件
tiers = {t[0]: t[7] for t in tier_assignments}
with open("/workspace/logs/p3p9_tiers.json", "w") as f:
    json.dump(tiers, f, indent=2)
print(f"✅ 落 p3p9_tiers.json")

conn.close()
