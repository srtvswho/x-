"""Phase 3 P3-3 记分牌聚合

处理:
1. 重复喊单去重(同 ticker+direction 取首次 published_at)
2. Wilson 95% CI 下界
3. avg + median excess(中位数抗极值)
4. 核心分层:thesis_category / market / conviction

先出去重 per-horizon 主表 + thesis_category 分层 + conviction 分层
"""
from __future__ import annotations
import os, json, sqlite3
from datetime import datetime
from typing import Dict, List, Tuple
import math
import statistics

DB = "/workspace/data/signalboard_full.db"
OUT_DIR = "/workspace/outputs"
os.makedirs(OUT_DIR, exist_ok=True)

conn = sqlite3.connect(DB, timeout=30)
c = conn.cursor()

HORIZONS = ["1w", "1m", "3m", "6m"]

# ============== 1. 加载 verifications + predictions ==============
print("=" * 80)
print("P3-3 记分牌聚合")
print("=" * 80)

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
print(f"verifications 总行数: {len(rows)}")

# Conviction 从 predictions 表读
conv_map = {r[0]: r[1] for r in c.execute("SELECT prediction_id, conviction FROM predictions")}
print(f"conviction map: {len(conv_map)} 行")

# ============== 2. 重复喊单去重 ==============
# 同 (ticker, direction) 取首次 published_at
print()
print("=" * 80)
print("重复喊单去重 (同 ticker+direction, 首次 published_at)")
print("=" * 80)

# 构造 (ticker, direction) -> 首次 published_at
def get_first_pub(ticker, direction):
    sql = """
    SELECT p.prediction_id, rp.published_at FROM predictions p
    JOIN raw_posts rp ON p.post_id = rp.post_id
    WHERE p.ticker = ? AND p.direction = ? AND p.price_source_available = 1
    ORDER BY rp.published_at ASC LIMIT 1
    """
    return c.execute(sql, (ticker, direction)).fetchone()

first_pubs = {}
for row in rows:
    pid, ticker, direction, _, _, _, _, _, *_ = row
    key = (ticker, direction)
    if key not in first_pubs:
        r = get_first_pub(ticker, direction)
        if r:
            first_pubs[key] = r[0]  # prediction_id

print(f"unique (ticker, direction) 组合: {len(first_pubs)}")
n_full = len(rows)
n_dedup = len(first_pubs)
print(f"全样本: {n_full} 条")
print(f"去重后(独立判断): {n_dedup} 条 (缩水 {n_full - n_dedup} 条)")

def is_repeat(row):
    pid = row[0]
    key = (row[1], row[2])
    return pid != first_pubs.get(key, pid)

n_repeats = sum(1 for r in rows if is_repeat(r))
print(f"其中 is_repeat_call=true: {n_repeats}")

# 拆分数据集
full_set = []
dedup_set = []
for row in rows:
    full_set.append(row)
    if not is_repeat(row):
        dedup_set.append(row)

print(f"全样本 rows: {len(full_set)}, 去重样本 rows: {len(dedup_set)}")


# ============== 3. Wilson 95% CI ==============
def wilson_lower(hit, n, z=1.96):
    """Wilson score interval 下界。n=0 返回 None。"""
    if n == 0:
        return None
    p_hat = hit / n
    denom = 1 + z * z / n
    center = (p_hat + z * z / (2 * n)) / denom
    spread = z * math.sqrt(p_hat * (1 - p_hat) / n + z * z / (4 * n * n)) / denom
    return center - spread

# ============== 4. per-horizon 主表(全样本 + 去重并列) ==============
print()
print("=" * 80)
print("Per-Horizon 主表")
print("=" * 80)

def aggregate_horizon(rows_set, label):
    """对一组 rows,按 4 个 horizon 聚合统计。"""
    print(f"\n[{label}] rows={len(rows_set)}")
    results = []
    for h in HORIZONS:
        status_idx = {"1w": 8, "1m": 12, "3m": 16, "6m": 20}[h]
        excess_idx = {"1w": 11, "1m": 15, "3m": 19, "6m": 23}[h]
        
        hit = 0
        miss = 0
        pending = 0
        skipped = 0
        unver = 0
        excess_values = []  # resolved 状态的 excess_return
        raw_values = []  # resolved 状态的 raw_return
        
        for r in rows_set:
            status = r[status_idx]
            excess = r[excess_idx]
            raw = r[excess_idx - 1]
            if status == "resolved_hit":
                hit += 1
                if excess is not None:
                    excess_values.append(excess)
                if raw is not None:
                    raw_values.append(raw)
            elif status == "resolved_miss":
                miss += 1
                if excess is not None:
                    excess_values.append(excess)
                if raw is not None:
                    raw_values.append(raw)
            elif status == "pending":
                pending += 1
            elif status and status.startswith("skipped_"):
                skipped += 1
            elif status == "unverifiable_no_benchmark":
                unver += 1
        
        n_resolved = hit + miss
        hit_rate = hit / n_resolved if n_resolved else 0
        wilson_low = wilson_lower(hit, n_resolved)
        avg_excess = statistics.mean(excess_values) if excess_values else None
        median_excess = statistics.median(excess_values) if excess_values else None
        avg_raw = statistics.mean(raw_values) if raw_values else None
        median_raw = statistics.median(raw_values) if raw_values else None
        
        results.append({
            "horizon": h,
            "n_total": len(rows_set),
            "n_resolved": n_resolved,
            "hit": hit,
            "miss": miss,
            "hit_rate": hit_rate,
            "wilson_lower_95": wilson_low,
            "avg_excess": avg_excess,
            "median_excess": median_excess,
            "avg_raw": avg_raw,
            "median_raw": median_raw,
            "n_pending": pending,
            "n_skipped": skipped,
            "n_unverifiable": unver,
        })
    return results


full_h = aggregate_horizon(full_set, "全样本 (含重复)")
dedup_h = aggregate_horizon(dedup_set, "去重样本 (独立判断)")

# 打印
def print_h_rows(label, rows_list):
    print(f"\n[{label}]")
    print(f"  {'h':4s} {'n_resolved':12s} {'hit_rate':10s} {'wilson_lower':14s} {'avg_excess':12s} {'median_excess':14s} {'n_pending':10s} {'n_skipped':10s}")
    for r in rows_list:
        h = r["horizon"]
        hr = f"{r['hit_rate']*100:.1f}%"
        wl = f"{r['wilson_lower_95']*100:.1f}%" if r['wilson_lower_95'] is not None else "N/A"
        ae = f"{r['avg_excess']*100:+.2f}%" if r['avg_excess'] is not None else "N/A"
        me = f"{r['median_excess']*100:+.2f}%" if r['median_excess'] is not None else "N/A"
        print(f"  {h:4s} {r['n_resolved']:12d} {hr:10s} {wl:14s} {ae:12s} {me:14s} {r['n_pending']:10d} {r['n_skipped']:10d}")

print_h_rows("全样本", full_h)
print_h_rows("去重样本", dedup_h)


# ============== 5. thesis_category 分层 ==============
print()
print("=" * 80)
print("thesis_category 分层 (按 1m horizon, 去重样本)")
print("=" * 80)

def get_thesis_category(ticker, direction, pub_at, prediction_id):
    sql = "SELECT thesis_category FROM predictions WHERE prediction_id=?"
    r = c.execute(sql, (prediction_id,)).fetchone()
    return r[0] if r else None

def stratify(rows_set, group_key_fn, label, horizon="1m"):
    status_idx = {"1w": 8, "1m": 12, "3m": 16, "6m": 20}[horizon]
    excess_idx = {"1w": 11, "1m": 15, "3m": 19, "6m": 23}[horizon]
    
    groups = {}
    for r in rows_set:
        key = group_key_fn(r)
        if key is None:
            key = "(NULL)"
        if key not in groups:
            groups[key] = []
        groups[key].append(r)
    
    print(f"\n[{label}] horizon={horizon}")
    print(f"  {'group':25s} {'n_resolved':10s} {'hit_rate':10s} {'wilson_lower':14s} {'avg_excess':12s} {'median_excess':14s} {'n_total':8s}")
    results = []
    for key, rs in sorted(groups.items(), key=lambda x: -len(x[1])):
        hit = 0
        miss = 0
        excess_values = []
        for r in rs:
            status = r[status_idx]
            excess = r[excess_idx]
            if status == "resolved_hit":
                hit += 1
                if excess is not None:
                    excess_values.append(excess)
            elif status == "resolved_miss":
                miss += 1
                if excess is not None:
                    excess_values.append(excess)
        n_resolved = hit + miss
        hit_rate = hit / n_resolved if n_resolved else 0
        wl = wilson_lower(hit, n_resolved)
        avg = statistics.mean(excess_values) if excess_values else None
        med = statistics.median(excess_values) if excess_values else None
        hr = f"{hit_rate*100:.1f}%"
        wls = f"{wl*100:.1f}%" if wl is not None else "N/A"
        ae = f"{avg*100:+.2f}%" if avg is not None else "N/A"
        me = f"{med*100:+.2f}%" if med is not None else "N/A"
        print(f"  {str(key)[:25]:25s} {n_resolved:10d} {hr:10s} {wls:14s} {ae:12s} {me:14s} {len(rs):8d}")
        results.append({
            "group": key, "n_resolved": n_resolved, "hit": hit, "miss": miss,
            "hit_rate": hit_rate, "wilson_lower": wl,
            "avg_excess": avg, "median_excess": med, "n_total": len(rs)
        })
    return results


# thesis_category 取自 predictions 表(已存于 verifications.thesis_category)
def get_cat(row):
    return row[3]  # thesis_category

# 全样本 + 去重 两套都出
th_full = stratify(full_set, get_cat, "thesis_category [全样本]", horizon="1m")
print()
th_dedup = stratify(dedup_set, get_cat, "thesis_category [去重]", horizon="1m")


# ============== 6. conviction 分层 ==============
print()
print("=" * 80)
print("conviction 分层 (1m horizon, 去重样本)")
print("=" * 80)

def get_conv(row):
    pid = row[0]
    return conv_map.get(pid)

cv_full = stratify(full_set, get_conv, "conviction [全样本]", horizon="1m")
print()
cv_dedup = stratify(dedup_set, get_conv, "conviction [去重]", horizon="1m")


# ============== 7. 落 markdown 报告 ==============
print()
print("=" * 80)
print("落 markdown 报告")
print("=" * 80)

md = []
md.append("# Phase 3 P3-3 记分牌聚合")
md.append("")
md.append(f"**运行时间**: {datetime.utcnow().isoformat()}Z")
md.append("")
md.append("## 1. 重复喊单去重")
md.append("")
md.append(f"- 全样本(含重复喊单): **{n_full} 行**")
md.append(f"- 去重样本(同 ticker+direction 首次 published_at): **{n_dedup} 行**")
md.append(f"- 缩水: {n_full - n_dedup} 条重复喊单")
md.append(f"- 缩水比例: {(n_full - n_dedup) / n_full * 100:.1f}%")
md.append("")
md.append("**关键洞察**:alexwo 大量重复喊单(同一 ticker 一段时间内反复看多/看空),")
md.append("**全样本会把她的'重复发声'算作独立判断,胜率会虚高**。")
md.append("**看下去重后的胜率,才是'独立判断 α'的真实信号**。")
md.append("")

md.append("## 2. Per-Horizon 主表(去重 + 全样本)")
md.append("")
for label, rs in [("全样本(含重复)", full_h), ("去重样本(独立判断)", dedup_h)]:
    md.append(f"### {label}")
    md.append("")
    md.append("| horizon | n_resolved | hit | miss | hit_rate | Wilson 95% 下界 | avg_excess | median_excess | n_pending | n_skipped |")
    md.append("|---|---|---|---|---|---|---|---|---|---|")
    for r in rs:
        hr_s = f"{r['hit_rate']*100:.1f}%"
        wl_s = f"{r['wilson_lower_95']*100:.1f}%" if r['wilson_lower_95'] is not None else "N/A"
        ae = f"{r['avg_excess']*100:+.2f}%" if r['avg_excess'] is not None else "N/A"
        me = f"{r['median_excess']*100:+.2f}%" if r['median_excess'] is not None else "N/A"
        md.append(f"| {r['horizon']} | {r['n_resolved']} | {r['hit']} | {r['miss']} | {hr_s} | {wl_s} | {ae} | {me} | {r['n_pending']} | {r['n_skipped']} |")
    md.append("")

md.append("## 3. thesis_category 分层(1m horizon)")
md.append("")
for label, rs in [("全样本(含重复)", th_full), ("去重样本(独立判断)", th_dedup)]:
    md.append(f"### {label}")
    md.append("")
    md.append("| thesis_category | n_resolved | hit_rate | Wilson 下界 | avg_excess | median_excess | n_total |")
    md.append("|---|---|---|---|---|---|---|")
    for r in rs:
        cat = r['group'] if r['group'] is not None else '(NULL)'
        hr_s = f"{r['hit_rate']*100:.1f}%"
        wl_s = f"{r['wilson_lower']*100:.1f}%" if r['wilson_lower'] is not None else "N/A"
        ae = f"{r['avg_excess']*100:+.2f}%" if r['avg_excess'] is not None else "N/A"
        me = f"{r['median_excess']*100:+.2f}%" if r['median_excess'] is not None else "N/A"
        md.append(f"| {cat} | {r['n_resolved']} | {hr_s} | {wl_s} | {ae} | {me} | {r['n_total']} |")
    md.append("")

md.append("## 4. conviction 分层(1m horizon)")
md.append("")
for label, rs in [("全样本(含重复)", cv_full), ("去重样本(独立判断)", cv_dedup)]:
    md.append(f"### {label}")
    md.append("")
    md.append("| conviction | n_resolved | hit_rate | Wilson 下界 | avg_excess | median_excess | n_total |")
    md.append("|---|---|---|---|---|---|---|")
    for r in rs:
        cv = r['group'] if r['group'] is not None else '(NULL)'
        hr_s = f"{r['hit_rate']*100:.1f}%"
        wl_s = f"{r['wilson_lower']*100:.1f}%" if r['wilson_lower'] is not None else "N/A"
        ae = f"{r['avg_excess']*100:+.2f}%" if r['avg_excess'] is not None else "N/A"
        me = f"{r['median_excess']*100:+.2f}%" if r['median_excess'] is not None else "N/A"
        md.append(f"| {cv} | {r['n_resolved']} | {hr_s} | {wl_s} | {ae} | {me} | {r['n_total']} |")
    md.append("")

# 关键发现文字解读
md.append("## 5. 关键发现")
md.append("")

# 计算去重 hit rate 与 50% 基准的偏离
dedup_1m_hit_rate = next(r['hit_rate'] for r in dedup_h if r['horizon'] == '1m')
dedup_1m_wilson = next(r['wilson_lower_95'] for r in dedup_h if r['horizon'] == '1m')

md.append(f"### 5.1 独立判断 hit_rate(去重后)")
md.append("")
md.append(f"- **1m horizon hit_rate**: {dedup_1m_hit_rate*100:.1f}%,Wilson 95% 下界 {dedup_1m_wilson*100:.1f}%")
md.append(f"- 50% 基准偏离: {(dedup_1m_hit_rate - 0.5)*100:+.1f} pp")
md.append(f"- 中位数 excess(抗极值): {next(r['median_excess'] for r in dedup_h if r['horizon'] == '1m')*100:+.2f}%")
md.append("")
md.append("### 5.2 conviction vs 准确性")
md.append("")

# 检查 conviction 高低 hit_rate 差异(不要求 n>=30 门槛,因为去重后小分组常见)
def get_cv_hitrate(rs):
    h5 = [r for r in rs if r['group'] in (4, 5)]
    l2 = [r for r in rs if r['group'] == 2]
    h5_hr = sum(r['hit'] for r in h5) / sum(r['n_resolved'] for r in h5) if h5 and sum(r['n_resolved'] for r in h5) > 0 else 0
    l2_hr = sum(r['hit'] for r in l2) / sum(r['n_resolved'] for r in l2) if l2 and sum(r['n_resolved'] for r in l2) > 0 else 0
    h5_n = sum(r['n_resolved'] for r in h5)
    l2_n = sum(r['n_resolved'] for r in l2)
    return h5_hr, h5_n, l2_hr, l2_n

hr5, n5, hr2, n2 = get_cv_hitrate(cv_dedup)
md.append(f"- **高 conviction (4-5) hit_rate**: {hr5*100:.1f}% (n_resolved={n5})")
md.append(f"- **低 conviction (2) hit_rate**: {hr2*100:.1f}% (n_resolved={n2})")
md.append(f"- 差异: {(hr5-hr2)*100:+.1f} pp")
md.append("")
if n5 < 30:
    md.append(f"**注**:高 conviction n_resolved={n5} 偏小,Wilson 下界宽,读作'初步信号'而非定论")
md.append("")
if hr5 > hr2 + 0.05:
    md.append("**结论**:高 conviction 胜率显著高于低 conviction → **她'知道自己什么时候更有把握'(强 α 信号)**")
elif hr5 < hr2 - 0.05:
    md.append("**结论**:高 conviction 胜率反而低 → **她的信心和准确度反相关,过度自信**")
else:
    md.append("**结论**:高/低 conviction 胜率接近(差<5pp) → **她的信心和准确度无关,信号弱**")
md.append("")

content = "\n".join(md)
with open(os.path.join(OUT_DIR, "phase3_p3_scoreboard_v1.md"), "w", encoding="utf-8") as f:
    f.write(content)
print(f"✅ 落 outputs/phase3_p3_scoreboard_v1.md ({len(content)} chars)")
conn.close()
print("=== DONE ===")
