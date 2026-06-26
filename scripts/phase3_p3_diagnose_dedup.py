"""Phase 3 P3-3 诊断: 去重逻辑可能误杀她最强的部分

三个诊断:
1. SIVE 全部预测的 1m excess 分布,看去重删掉的后续喊单的正超额比例
2. 去重后 3m/6m 样本的 published_at 分布(是否集中早期?)
3. 换"月度去重"口径对比(同 ticker+direction 同月内只算一次)
"""
from __future__ import annotations
import os, json, sqlite3
from datetime import datetime
from typing import Dict, List, Tuple
from collections import defaultdict, Counter
import math
import statistics

DB = "/workspace/data/signalboard_full.db"
OUT_DIR = "/workspace/outputs"
os.makedirs(OUT_DIR, exist_ok=True)

conn = sqlite3.connect(DB, timeout=30)
c = conn.cursor()

HORIZONS = ["1w", "1m", "3m", "6m"]

def wilson_lower(hit, n, z=1.96):
    if n == 0: return None
    p_hat = hit / n
    denom = 1 + z * z / n
    center = (p_hat + z * z / (2 * n)) / denom
    spread = z * math.sqrt(p_hat * (1 - p_hat) / n + z * z / (4 * n * n)) / denom
    return center - spread

# 加载 verifications
sql = """
SELECT v.prediction_id, v.ticker, v.direction, v.thesis_category, v.horizon_input,
       v.published_at, v.entry_date_actual, v.entry_price,
       v.h_1w_status, v.h_1w_raw_return, v.h_1w_benchmark_return, v.h_1w_excess_return,
       v.h_1m_status, v.h_1m_raw_return, v.h_1m_benchmark_return, v.h_1m_excess_return,
       v.h_3m_status, v.h_3m_raw_return, v.h_3m_benchmark_return, v.h_3m_excess_return,
       v.h_6m_status, v.h_6m_raw_return, v.h_6m_benchmark_return, v.h_6m_excess_return
FROM verifications v
"""
rows = c.execute(sql).fetchall()
print(f"加载 {len(rows)} verifications")

# 装载 first_pub (首次去重口径)
def get_first_pub(ticker, direction):
    sql = """
    SELECT p.prediction_id, rp.published_at FROM predictions p
    JOIN raw_posts rp ON p.post_id = rp.post_id
    WHERE p.ticker = ? AND p.direction = ? AND p.price_source_available = 1
    ORDER BY rp.published_at ASC LIMIT 1
    """
    return c.execute(sql, (ticker, direction)).fetchone()

first_pubs = {}
for r in rows:
    key = (r[1], r[2])
    if key not in first_pubs:
        r2 = get_first_pub(r[1], r[2])
        if r2:
            first_pubs[key] = r2[0]

# 装载 monthly_first (月度去重口径:同 ticker+direction 每月首次)
monthly_first = {}  # (ticker, direction, YYYY-MM) -> prediction_id
sql_m = """
SELECT p.prediction_id, p.ticker, p.direction, rp.published_at
FROM predictions p
JOIN raw_posts rp ON p.post_id = rp.post_id
WHERE p.price_source_available = 1
ORDER BY rp.published_at ASC
"""
for r in c.execute(sql_m):
    pid, t, d, pub = r
    if not pub: continue
    month = pub[:7]
    key = (t, d, month)
    if key not in monthly_first:
        monthly_first[key] = pid

print(f"first_pubs: {len(first_pubs)}")
print(f"monthly_first: {len(monthly_first)}")

# 三套集合
def is_first_pub(row): return row[0] == first_pubs.get((row[1], row[2]), row[0])
def is_monthly_first(row):
    pub = row[5]
    if not pub: return False
    key = (row[1], row[2], pub[:7])
    return row[0] == monthly_first.get(key, row[0])

full_set = rows
first_set = [r for r in rows if is_first_pub(r)]
monthly_set = [r for r in rows if is_monthly_first(r)]

print(f"\n全集: {len(full_set)}, 首次去重: {len(first_set)}, 月度去重: {len(monthly_set)}")
print(f"月度去重保留率: {len(monthly_set)/len(full_set)*100:.1f}% (vs 首次去重 {len(first_set)/len(full_set)*100:.1f}%)")


# ============== 诊断 1: SIVE 全部预测的 1m 表现 ==============
print()
print("=" * 80)
print("诊断 1: SIVE 全部预测的 1m 超额收益(按 published_at 排序)")
print("=" * 80)

sive_rows = sorted(
    [r for r in rows if r[1] == "SIVE"],
    key=lambda r: r[5] or ""
)
print(f"SIVE 总条数: {len(sive_rows)}")
print()
print(f"{'#':4s}  {'pub_date':12s}  {'1m_status':14s}  {'1m_excess':12s}  {'is_first':10s}  {'is_monthly':12s}  {'thesis':60s}")
sive_results = []
for i, r in enumerate(sive_rows, 1):
    pub = r[5][:10] if r[5] else "NULL"
    h1m_status = r[12]
    h1m_excess = r[15]
    is_f = "YES" if is_first_pub(r) else "no"
    is_m = "YES" if is_monthly_first(r) else "no"
    thesis = (r[6] or "")[:50] if len(r) > 6 else ""
    excess_s = f"{h1m_excess*100:+.2f}%" if h1m_excess is not None else "N/A"
    print(f"  {i:3d}  {pub:12s}  {h1m_status:14s}  {excess_s:12s}  {is_f:10s}  {is_m:12s}  {thesis}")

# 1m 状态分布
sive_h1m_status = [r[12] for r in sive_rows]
dist = Counter(sive_h1m_status)
print(f"\nSIVE 1m 状态分布: {dict(dist)}")

# 算正超额占比
sive_resolved_1m = [r for r in sive_rows if r[12] in ("resolved_hit", "resolved_miss")]
n_resolved = len(sive_resolved_1m)
n_hit = sum(1 for r in sive_resolved_1m if r[12] == "resolved_hit")
sive_hr = n_hit / n_resolved if n_resolved else 0
print(f"\nSIVE 1m 去重前(全样本):")
print(f"  n_resolved={n_resolved} hit_rate={sive_hr*100:.1f}% Wilson 下界={wilson_lower(n_hit,n_resolved)*100:.1f}%")

# 只看 first_only 和 monthly_only
sive_first = [r for r in sive_rows if is_first_pub(r)]
sive_monthly = [r for r in sive_rows if is_monthly_first(r)]
n_first = sum(1 for r in sive_first if r[12] in ("resolved_hit", "resolved_miss"))
n_first_hit = sum(1 for r in sive_first if r[12] == "resolved_hit")
n_monthly = sum(1 for r in sive_monthly if r[12] in ("resolved_hit", "resolved_miss"))
n_monthly_hit = sum(1 for r in sive_monthly if r[12] == "resolved_hit")

print(f"\nSIVE 1m 首次去重(只取首次):")
print(f"  n_resolved={n_first} hit_rate={n_first_hit/n_first*100:.1f}% Wilson 下界={wilson_lower(n_first_hit,n_first)*100:.1f}%")

print(f"\nSIVE 1m 月度去重:")
print(f"  n_resolved={n_monthly} hit_rate={n_monthly_hit/n_monthly*100:.1f}% Wilson 下界={wilson_lower(n_monthly_hit,n_monthly)*100:.1f}%")

# 关键诊断:被首次去重"杀掉"的后续喊单,正超额比例是多少?
removed_by_first = [r for r in sive_rows if not is_first_pub(r)]
removed_resolved = [r for r in removed_by_first if r[12] in ("resolved_hit", "resolved_miss")]
removed_hit = sum(1 for r in removed_resolved if r[12] == "resolved_hit")
print(f"\n被首次去重杀掉: {len(removed_by_first)} 条")
print(f"  其中 1m resolved: {len(removed_resolved)} 条")
print(f"  其中 hit: {removed_hit} ({removed_hit/len(removed_resolved)*100:.1f}%)")
if removed_resolved:
    removed_excess = [r[15] for r in removed_resolved if r[15] is not None]
    if removed_excess:
        print(f"  median excess: {statistics.median(removed_excess)*100:+.2f}%")
        print(f"  avg excess: {statistics.mean(removed_excess)*100:+.2f}%")

# 哪些被"月度去重"杀掉(同月内重复的)?
removed_by_monthly = [r for r in sive_rows if not is_monthly_first(r)]
removed_m_resolved = [r for r in removed_by_monthly if r[12] in ("resolved_hit", "resolved_miss")]
removed_m_hit = sum(1 for r in removed_m_resolved if r[12] == "resolved_hit")
print(f"\n被月度去重杀掉(同 ticker+dir 同月内重复): {len(removed_by_monthly)} 条")
print(f"  其中 1m resolved: {len(removed_m_resolved)} 条")
print(f"  其中 hit: {removed_m_hit} ({removed_m_hit/len(removed_m_resolved)*100:.1f}%)")


# ============== 诊断 2: 去重后 3m/6m 样本的 published_at 分布 ==============
print()
print("=" * 80)
print("诊断 2: 去重后 3m/6m 样本的 published_at 分布")
print("=" * 80)

# 首次去重后 3m 已到期的样本 published_at 月份
def get_status(rows, h):
    idx = {"1w": 8, "1m": 12, "3m": 16, "6m": 20}[h]
    return [r[idx] for r in rows]

def pub_month(rows):
    pubs = []
    for r in rows:
        if r[5]:
            pubs.append(r[5][:7])
    return pubs

for h in ["3m", "6m"]:
    print(f"\n[{h}] 首次去重后 resolved 的 published_at 月份分布:")
    h_resolved = [r for r in first_set if r[{"1w":8,"1m":12,"3m":16,"6m":20}[h]] in ("resolved_hit", "resolved_miss")]
    pubs = pub_month(h_resolved)
    counter = Counter(pubs)
    for m in sorted(counter):
        print(f"  {m}  {counter[m]}")

# 算中位月份
def median_month(pubs):
    if not pubs: return None
    months = sorted(pubs)
    return months[len(months)//2]

print()
for h in ["1m", "3m", "6m"]:
    h_resolved_first = [r for r in first_set if r[{"1w":8,"1m":12,"3m":16,"6m":20}[h]] in ("resolved_hit", "resolved_miss")]
    h_resolved_monthly = [r for r in monthly_set if r[{"1w":8,"1m":12,"3m":16,"6m":20}[h]] in ("resolved_hit", "resolved_miss")]
    pubs_first = pub_month(h_resolved_first)
    pubs_monthly = pub_month(h_resolved_monthly)
    print(f"  [{h}] 首次去重 resolved={len(h_resolved_first)} 中位月份={median_month(pubs_first)}")
    print(f"  [{h}] 月度去重 resolved={len(h_resolved_monthly)} 中位月份={median_month(pubs_monthly)}")


# ============== 诊断 3: 三套口径 per-horizon 胜率对比 ==============
print()
print("=" * 80)
print("诊断 3: 三套口径 per-horizon hit_rate 对比")
print("=" * 80)

def per_horizon_table(rows_set, label):
    print(f"\n[{label}] rows={len(rows_set)}")
    print(f"  {'h':4s} {'n_resolved':10s} {'hit_rate':10s} {'wilson_low':10s} {'median_excess':14s} {'avg_excess':12s}")
    for h in HORIZONS:
        idx = {"1w":8,"1m":12,"3m":16,"6m":20}[h]
        exc_idx = {"1w":11,"1m":15,"3m":19,"6m":23}[h]
        hits, misses, excess_vals = 0, 0, []
        for r in rows_set:
            s = r[idx]
            e = r[exc_idx]
            if s == "resolved_hit":
                hits += 1
                if e is not None: excess_vals.append(e)
            elif s == "resolved_miss":
                misses += 1
                if e is not None: excess_vals.append(e)
        n = hits + misses
        hr = hits/n if n else 0
        wl = wilson_lower(hits, n)
        med = statistics.median(excess_vals) if excess_vals else None
        avg = statistics.mean(excess_vals) if excess_vals else None
        hr_s = f"{hr*100:.1f}%"
        wl_s = f"{wl*100:.1f}%" if wl is not None else "N/A"
        med_s = f"{med*100:+.2f}%" if med is not None else "N/A"
        avg_s = f"{avg*100:+.2f}%" if avg is not None else "N/A"
        print(f"  {h:4s} {n:10d} {hr_s:10s} {wl_s:10s} {med_s:14s} {avg_s:12s}")

per_horizon_table(full_set, "全集 (无去重)")
per_horizon_table(first_set, "首次去重 (口径 1)")
per_horizon_table(monthly_set, "月度去重 (口径 2)")


# ============== 落报告 ==============
print()
print("=" * 80)
print("落报告")
print("=" * 80)

md = []
md.append("# Phase 3 P3-3 诊断: 去重逻辑可能误杀她最强的部分")
md.append("")
md.append(f"**运行时间**: {datetime.utcnow().isoformat()}Z")
md.append("")
md.append("## 0. 三套口径样本量对比")
md.append("")
md.append("| 口径 | rows | 保留率 |")
md.append("|---|---|---|")
md.append(f"| 全集(无去重) | {len(full_set)} | 100.0% |")
md.append(f"| 首次去重(同 ticker+direction 全部时间) | {len(first_set)} | {len(first_set)/len(full_set)*100:.1f}% |")
md.append(f"| 月度去重(同 ticker+direction 同月内) | {len(monthly_set)} | {len(monthly_set)/len(full_set)*100:.1f}% |")
md.append("")
md.append("## 1. SIVE 案例: 1m 全部预测明细")
md.append("")
md.append(f"**SIVE 总条数**: {len(sive_rows)}")
md.append("")
md.append("| # | pub_date | 1m_status | 1m_excess | is_first | is_monthly | thesis |")
md.append("|---|---|---|---|---|---|---|")
for i, r in enumerate(sive_rows, 1):
    pub = r[5][:10] if r[5] else "NULL"
    h1m_status = r[12]
    h1m_excess = r[15]
    is_f = "✓" if is_first_pub(r) else "✗"
    is_m = "✓" if is_monthly_first(r) else "✗"
    thesis = (r[6] or "")[:50] if len(r) > 6 else ""
    excess_s = f"{h1m_excess*100:+.2f}%" if h1m_excess is not None else "N/A"
    md.append(f"| {i} | {pub} | {h1m_status} | {excess_s} | {is_f} | {is_m} | {thesis} |")
md.append("")

md.append("### 1.1 SIVE 1m 三套口径对比")
md.append("")
md.append("| 口径 | n_resolved | hit_rate | Wilson 95% 下界 | median_excess | avg_excess |")
md.append("|---|---|---|---|---|---|")
md.append(f"| 全样本 | {n_resolved} | {sive_hr*100:.1f}% | {wilson_lower(n_hit,n_resolved)*100:.1f}% | {statistics.median([r[15] for r in sive_resolved_1m if r[15] is not None])*100:+.2f}% | {statistics.mean([r[15] for r in sive_resolved_1m if r[15] is not None])*100:+.2f}% |")
md.append(f"| 首次去重 | {n_first} | {n_first_hit/n_first*100:.1f}% | {wilson_lower(n_first_hit,n_first)*100:.1f}% | {statistics.median([r[15] for r in sive_first if r[15] is not None and r[12] in ('resolved_hit','resolved_miss')])*100:+.2f}% | {statistics.mean([r[15] for r in sive_first if r[15] is not None and r[12] in ('resolved_hit','resolved_miss')])*100:+.2f}% |")
md.append(f"| 月度去重 | {n_monthly} | {n_monthly_hit/n_monthly*100:.1f}% | {wilson_lower(n_monthly_hit,n_monthly)*100:.1f}% | {statistics.median([r[15] for r in sive_monthly if r[15] is not None and r[12] in ('resolved_hit','resolved_miss')])*100:+.2f}% | {statistics.mean([r[15] for r in sive_monthly if r[15] is not None and r[12] in ('resolved_hit','resolved_miss')])*100:+.2f}% |")
md.append("")

md.append("### 1.2 被首次去重'杀掉'的后续喊单")
md.append("")
md.append(f"- 被删除: **{len(removed_by_first)}** 条")
md.append(f"- 1m resolved: {len(removed_resolved)} 条")
if removed_resolved:
    md.append(f"- 其中 hit: {removed_hit} ({removed_hit/len(removed_resolved)*100:.1f}%)")
    md.append(f"- median excess: {statistics.median(removed_excess)*100:+.2f}%")
    md.append(f"- avg excess: {statistics.mean(removed_excess)*100:+.2f}%")
md.append("")

md.append("### 1.3 被月度去重'杀掉'的(同 ticker+dir 同月内重复)")
md.append("")
md.append(f"- 被删除: **{len(removed_by_monthly)}** 条")
md.append(f"- 1m resolved: {len(removed_m_resolved)} 条")
if removed_m_resolved:
    md.append(f"- 其中 hit: {removed_m_hit} ({removed_m_hit/len(removed_m_resolved)*100:.1f}%)")
md.append("")

md.append("## 2. 去重后 3m/6m 样本的 published_at 分布")
md.append("")
md.append("### 首次去重后,3m/6m resolved 样本的 published_at 月份分布")
md.append("")
for h in ["3m", "6m"]:
    md.append(f"**[{h}]**")
    md.append("")
    h_resolved = [r for r in first_set if r[{"1w":8,"1m":12,"3m":16,"6m":20}[h]] in ("resolved_hit", "resolved_miss")]
    pubs = pub_month(h_resolved)
    counter = Counter(pubs)
    md.append("| 月份 | n_resolved |")
    md.append("|---|---|")
    for m in sorted(counter):
        md.append(f"| {m} | {counter[m]} |")
    md.append(f"| **中位月份** | **{median_month(pubs)}** |")
    md.append("")

md.append("## 3. 三套口径 per-horizon 胜率对比")
md.append("")
for label, rs in [("全集", full_set), ("首次去重", first_set), ("月度去重", monthly_set)]:
    md.append(f"### {label} (rows={len(rs)})")
    md.append("")
    md.append("| horizon | n_resolved | hit_rate | Wilson 95% 下界 | median_excess | avg_excess |")
    md.append("|---|---|---|---|---|---|")
    for h in HORIZONS:
        idx = {"1w":8,"1m":12,"3m":16,"6m":20}[h]
        exc_idx = {"1w":11,"1m":15,"3m":19,"6m":23}[h]
        hits, misses, excess_vals = 0, 0, []
        for r in rs:
            s = r[idx]
            e = r[exc_idx]
            if s == "resolved_hit":
                hits += 1
                if e is not None: excess_vals.append(e)
            elif s == "resolved_miss":
                misses += 1
                if e is not None: excess_vals.append(e)
        n = hits + misses
        hr = hits/n if n else 0
        wl = wilson_lower(hits, n)
        med = statistics.median(excess_vals) if excess_vals else None
        avg = statistics.mean(excess_vals) if excess_vals else None
        hr_s = f"{hr*100:.1f}%"
        wl_s = f"{wl*100:.1f}%" if wl is not None else "N/A"
        med_s = f"{med*100:+.2f}%" if med is not None else "N/A"
        avg_s = f"{avg*100:+.2f}%" if avg is not None else "N/A"
        md.append(f"| {h} | {n} | {hr_s} | {wl_s} | {med_s} | {avg_s} |")
    md.append("")

content = "\n".join(md)
with open(os.path.join(OUT_DIR, "phase3_p3_dedup_diagnose.md"), "w", encoding="utf-8") as f:
    f.write(content)
print(f"✅ 落 outputs/phase3_p3_dedup_diagnose.md ({len(content)} chars)")
conn.close()
print("=== DONE ===")
