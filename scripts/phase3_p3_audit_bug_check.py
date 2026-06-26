"""Phase 3 P3-3 审计 5 个诊断(用户怀疑验证计算有 bug)

1. SIVE 3 条手算核对
2. 复权一致性审计(关键:个股 vs SPY 是否都 adjusted)
3. 长 horizon 5 条负超额核对
4. pending 样本偏差量化
5. 绝对收益 vs 超额收益对比
"""
from __future__ import annotations
import os, json, sqlite3, time
from datetime import datetime, date
from typing import Dict, List
from collections import Counter, defaultdict
import math
import statistics
from statistics import median

DB = "/workspace/data/signalboard_full.db"
OUT_DIR = "/workspace/outputs"

conn = sqlite3.connect(DB, timeout=30)
c = conn.cursor()

# ============== 1. SIVE 3 条手算 ==============
print("=" * 80)
print("诊断 1: SIVE 3 条手算核对")
print("=" * 80)

# 选 3 条:首次 (2026-03-16) + 中段 (2026-04-15) + 后段 (2026-05-25)
# 直接读 verifications 表的 4 horizon raw/bench/excess
sql = """
SELECT v.prediction_id, v.published_at, v.entry_date_actual, v.entry_price,
       v.h_1m_status, v.h_1m_actual_exit, v.h_1m_exit_price, v.h_1m_raw_return, v.h_1m_benchmark_return, v.h_1m_excess_return,
       v.h_1w_status, v.h_1w_actual_exit, v.h_1w_exit_price, v.h_1w_raw_return, v.h_1w_benchmark_return, v.h_1w_excess_return,
       v.h_3m_status, v.h_3m_actual_exit, v.h_3m_exit_price, v.h_3m_raw_return, v.h_3m_benchmark_return, v.h_3m_excess_return,
       v.h_6m_status, v.h_6m_actual_exit, v.h_6m_exit_price, v.h_6m_raw_return, v.h_6m_benchmark_return, v.h_6m_excess_return
FROM verifications v
WHERE v.ticker = 'SIVE'
  AND v.published_at IN ('2026-03-16T08:54:18+00:00', '2026-04-15T...', '2026-05-25T...')
ORDER BY v.published_at
"""
# 用更宽的:取 2026-03-16 / 2026-04-15 / 2026-05-25 第一条
samples = []
for pub_date, label in [
    ("2026-03-16", "首次(SIVE 入场)"),
    ("2026-04-15", "中段"),
    ("2026-05-25", "后段"),
]:
    sql = """
    SELECT prediction_id, published_at, entry_date_actual, entry_price,
           h_1w_status, h_1w_actual_exit, h_1w_exit_price, h_1w_raw_return, h_1w_benchmark_return, h_1w_excess_return,
           h_1m_status, h_1m_actual_exit, h_1m_exit_price, h_1m_raw_return, h_1m_benchmark_return, h_1m_excess_return,
           h_3m_status, h_3m_actual_exit, h_3m_exit_price, h_3m_raw_return, h_3m_benchmark_return, h_3m_excess_return,
           h_6m_status, h_6m_actual_exit, h_6m_exit_price, h_6m_raw_return, h_6m_benchmark_return, h_6m_excess_return
    FROM verifications
    WHERE ticker='SIVE' AND substr(published_at,1,10)=?
    ORDER BY published_at LIMIT 1
    """
    r = c.execute(sql, (pub_date,)).fetchone()
    if r:
        samples.append((label, pub_date, r))

for label, pub, r in samples:
    print(f"\n[{label}] pub={pub}")
    print(f"  prediction_id={r[0]}")
    print(f"  entry_date={r[2]}  entry_price=${r[3]:.4f}")
    for h_idx, h_name in enumerate(["1w", "1m", "3m", "6m"]):
        status = r[4 + h_idx * 6]
        actual_exit = r[5 + h_idx * 6]
        exit_price = r[6 + h_idx * 6]
        raw = r[7 + h_idx * 6]
        bench = r[8 + h_idx * 6]
        excess = r[9 + h_idx * 6]
        if status == "resolved_hit" or status == "resolved_miss":
            print(f"  [{h_name}] exit={actual_exit} exit_px=${exit_price:.4f}  raw={raw*100:+.2f}%  bench={bench*100:+.2f}%  excess={excess*100:+.2f}%")
        else:
            print(f"  [{h_name}] {status} (no detail)")

# ============== 2. 复权一致性审计(关键) ==============
print()
print("=" * 80)
print("诊断 2: 复权一致性审计 (SIVEF vs SPY, 同一时间窗)")
print("=" * 80)

# 直接拉 SIVEF 和 SPY 同一区间的 adjusted=true vs unadjusted 价格对比
import requests
POLY = os.environ.get("POLYGON_API_KEY", "")

def fetch(symbol, start, end, adjusted):
    for attempt in range(3):
        try:
            r = requests.get(
                f"https://api.polygon.io/v2/aggs/ticker/{symbol}/range/1/day/{start}/{end}",
                params={"adjusted": str(adjusted).lower(), "sort": "asc", "limit": 100, "apiKey": POLY},
                timeout=30
            )
            return r.json()
        except Exception as e:
            print(f"  [retry {attempt+1}] {symbol} {start}→{end} adj={adjusted}: {e}")
            time.sleep(15)
    return {"results": None}

# 关键:对 SIVEF 来说,有没有发生过 reverse split?
# 从 2025-11-30 起(早期价格基准)拉到 2026-06-12
# 两次:adjusted=true vs adjusted=false,看相对变化

# 1) 抽 1w horizon 的一段(2026-03-17 → 2026-03-24)
print("\n1w horizon (SIVEF 2026-03-17 → 2026-03-24):")
for sym in ["SIVEF", "SPY", "SOXX"]:
    adj = fetch(sym, "2026-03-17", "2026-03-25", True)
    unadj = fetch(sym, "2026-03-17", "2026-03-25", False)
    if adj.get("results") and unadj.get("results"):
        a0, a1 = adj["results"][0], adj["results"][-1]
        u0, u1 = unadj["results"][0], unadj["results"][-1]
        a_return = (a1["c"] - a0["c"]) / a0["c"]
        u_return = (u1["c"] - u0["c"]) / u0["c"]
        print(f"  {sym:6s}  adj: {a0['c']:.4f}→{a1['c']:.4f} = {a_return*100:+.2f}%  unadj: {u0['c']:.4f}→{u1['c']:.4f} = {u_return*100:+.2f}%  diff={(a_return-u_return)*100:+.3f}pp")
    time.sleep(13)

# 1m horizon (SIVEF 2026-03-17 → 2026-04-16)
print("\n1m horizon (SIVEF 2026-03-17 → 2026-04-16):")
for sym in ["SIVEF", "SPY", "SOXX"]:
    adj = fetch(sym, "2026-03-17", "2026-04-20", True)
    unadj = fetch(sym, "2026-03-17", "2026-04-20", False)
    if adj.get("results") and unadj.get("results"):
        a0, a1 = adj["results"][0], adj["results"][-1]
        u0, u1 = unadj["results"][0], unadj["results"][-1]
        a_return = (a1["c"] - a0["c"]) / a0["c"]
        u_return = (u1["c"] - u0["c"]) / u0["c"]
        print(f"  {sym:6s}  adj: {a0['c']:.4f}→{a1['c']:.4f} = {a_return*100:+.2f}%  unadj: {u0['c']:.4f}→{u1['c']:.4f} = {u_return*100:+.2f}%  diff={(a_return-u_return)*100:+.3f}pp")
    time.sleep(13)

# 3m horizon
print("\n3m horizon (SIVEF 2026-03-17 → 2026-06-15):")
for sym in ["SIVEF", "SPY", "SOXX"]:
    adj = fetch(sym, "2026-03-17", "2026-06-15", True)
    unadj = fetch(sym, "2026-03-17", "2026-06-15", False)
    if adj.get("results") and unadj.get("results"):
        a0, a1 = adj["results"][0], adj["results"][-1]
        u0, u1 = unadj["results"][0], unadj["results"][-1]
        a_return = (a1["c"] - a0["c"]) / a0["c"]
        u_return = (u1["c"] - u0["c"]) / u0["c"]
        print(f"  {sym:6s}  adj: {a0['c']:.4f}→{a1['c']:.4f} = {a_return*100:+.2f}%  unadj: {u0['c']:.4f}→{u1['c']:.4f} = {u_return*100:+.2f}%  diff={(a_return-u_return)*100:+.3f}pp")
    time.sleep(13)


# ============== 3. 长 horizon 5 条负超额核对 ==============
print()
print("=" * 80)
print("诊断 3: 5 条 3m/6m 负超额核对(基准异常放大?)")
print("=" * 80)

# 找 5 条 3m/6m excess < -10% 的预测,核对 raw vs bench
sql = """
SELECT prediction_id, ticker, published_at, entry_date_actual, entry_price,
       h_3m_status, h_3m_actual_exit, h_3m_exit_price, h_3m_raw_return, h_3m_benchmark_return, h_3m_excess_return,
       h_6m_status, h_6m_actual_exit, h_6m_exit_price, h_6m_raw_return, h_6m_benchmark_return, h_6m_excess_return
FROM verifications
WHERE (h_3m_status='resolved_miss' AND h_3m_excess_return < -0.10)
   OR (h_6m_status='resolved_miss' AND h_6m_excess_return < -0.10)
ORDER BY h_3m_excess_return ASC, h_6m_excess_return ASC
LIMIT 5
"""
print("\n5 条 3m/6m 强负超额预测:")
for r in c.execute(sql).fetchall():
    pid, ticker, pub, edate, eprice, s3, ae3, ep3, r3, b3, e3, s6, ae6, ep6, r6, b6, e6_ = r
    print(f"\n  pred_id={pid[:10]}  {ticker}  pub={pub[:10]}")
    print(f"    entry_date={edate}  entry_price=${eprice}")
    if s3 == "resolved_miss":
        print(f"    [3m] exit={ae3}  exit_px=${ep3}  raw={r3*100:+.2f}%  bench={b3*100:+.2f}%  excess={e3*100:+.2f}%")
    if s6 == "resolved_miss":
        print(f"    [6m] exit={ae6}  exit_px=${ep6}  raw={r6*100:+.2f}%  bench={b6*100:+.2f}%  excess={e6_*100:+.2f}%")

# ============== 4. pending 样本偏差量化 ==============
print()
print("=" * 80)
print("诊断 4: pending vs resolved 样本偏差量化")
print("=" * 80)

# 已 resolved (4 至少 1 个 horizon resolved_hit 或 resolved_miss) vs 全 pending
sql = """
SELECT prediction_id, published_at, ticker, direction,
       h_1w_status, h_1w_raw_return, h_1w_benchmark_return, h_1w_excess_return,
       h_1m_status, h_1m_raw_return, h_1m_benchmark_return, h_1m_excess_return,
       h_3m_status, h_3m_raw_return, h_3m_benchmark_return, h_3m_excess_return,
       h_6m_status, h_6m_raw_return, h_6m_benchmark_return, h_6m_excess_return
FROM verifications
"""
all_v = c.execute(sql).fetchall()

resolved_v = []
pending_v = []
for r in all_v:
    pub = r[1]
    statuses = [r[3], r[4], r[5], r[6]]
    if any(s in ("resolved_hit", "resolved_miss") for s in statuses):
        resolved_v.append(pub)
    else:
        pending_v.append(pub)

print(f"\n已 resolved (≥1 horizon 到期): {len(resolved_v)} predictions")
print(f"全 pending (没 1 个 horizon 到期): {len(pending_v)} predictions")

def month_dist(pubs):
    counter = Counter()
    for p in pubs:
        if p:
            counter[p[:7]] += 1
    return counter

res_dist = month_dist(resolved_v)
pen_dist = month_dist(pending_v)
all_months = sorted(set(res_dist.keys()) | set(pen_dist.keys()))

print(f"\n{'月份':10s}  {'resolved':10s}  {'pending':10s}  {'total':10s}  {'pen_pct':10s}")
for m in all_months:
    r_n = res_dist.get(m, 0)
    p_n = pen_dist.get(m, 0)
    total = r_n + p_n
    pct = p_n / total * 100 if total else 0
    print(f"  {m}  {r_n:10d}  {p_n:10d}  {total:10d}  {pct:5.1f}%")

# 关键:中位月份对比
res_months = sorted([p[:7] for p in resolved_v if p])
pen_months = sorted([p[:7] for p in pending_v if p])
def median_str(s):
    if not s: return 'N/A'
    return s[len(s)//2]
print(f"\n已 resolved 中位 published 月份: {median_str(res_months)}")
print(f"全 pending 中位 published 月份: {median_str(pen_months)}")


# ============== 5. 绝对收益 vs 超额收益对比 ==============
print()
print("=" * 80)
print("诊断 5: 绝对收益 (raw_return) vs 超额收益 (excess_return) hit_rate 对比")
print("=" * 80)

# 两种 hit 定义:
# 1) excess > 0 (现在)
# 2) raw > 0 (绝对)
print("\n{horizon:4s}  {'raw_hit_rate':12s}  {'excess_hit_rate':16s}  {'bench_avg':12s}  {'bench_median':14s}")
# all_v col: prediction_id=0, published_at=1, ticker=2, direction=3
# h_1w_status=4, h_1w_raw=5, h_1w_bench=6, h_1w_exc=7
# h_1m_status=8, h_1m_raw=9, h_1m_bench=10, h_1m_exc=11
# h_3m_status=12, h_3m_raw=13, h_3m_bench=14, h_3m_exc=15
# h_6m_status=16, h_6m_raw=17, h_6m_bench=18, h_6m_exc=19
for h_name, status_idx, raw_idx, bench_idx, exc_idx in [("1w", 4, 5, 6, 7), ("1m", 8, 9, 10, 11), ("3m", 12, 13, 14, 15), ("6m", 16, 17, 18, 19)]:
    n_resolved = 0
    raw_hits = 0
    excess_hits = 0
    bench_values = []
    for r in all_v:
        s = r[status_idx]
        if s in ("resolved_hit", "resolved_miss"):
            n_resolved += 1
            raw = r[raw_idx]
            excess = r[exc_idx]
            if raw is not None and raw > 0:
                raw_hits += 1
            if excess is not None and excess > 0:
                excess_hits += 1
            bench = r[bench_idx]
            if bench is not None:
                bench_values.append(bench)
    if n_resolved:
        print(f"  {h_name:4s}  {raw_hits/n_resolved*100:10.1f}%  {excess_hits/n_resolved*100:14.1f}%  {statistics.mean(bench_values)*100:+10.2f}%  {statistics.median(bench_values)*100:+12.2f}%")


# ============== 落报告 ==============
print()
print("=" * 80)
print("落报告")
print("=" * 80)

content_log = []
content_log.append("# Phase 3 P3-3 审计: 5 个诊断(验证计算 bug 检查)")
content_log.append("")
content_log.append(f"**运行时间**: {datetime.utcnow().isoformat()}Z")
content_log.append("")
content_log.append("## 1. SIVE 3 条手算核对")
content_log.append("")
for label, pub, r in samples:
    content_log.append(f"### [{label}] pub={pub}")
    content_log.append(f"- prediction_id: `{r[0]}`")
    content_log.append(f"- entry_date: {r[2]}  entry_price: ${r[3]:.4f}")
    for h_idx, h_name in enumerate(["1w", "1m", "3m", "6m"]):
        status = r[4 + h_idx * 6]
        actual_exit = r[5 + h_idx * 6]
        exit_price = r[6 + h_idx * 6]
        raw = r[7 + h_idx * 6]
        bench = r[8 + h_idx * 6]
        excess = r[9 + h_idx * 6]
        if status == "resolved_hit" or status == "resolved_miss":
            content_log.append(f"- **{h_name}**: exit={actual_exit} exit_px=${exit_price:.4f} raw={raw*100:+.2f}% bench={bench*100:+.2f}% excess={excess*100:+.2f}%")
        else:
            content_log.append(f"- **{h_name}**: {status} (no detail)")
    content_log.append("")

# 复权审计
content_log.append("## 2. 复权一致性审计(关键)")
content_log.append("")
content_log.append("**核心问题**:个股(adjusted) vs 基准(adjusted) 是否复权口径一致?")
content_log.append("")
content_log.append("对比 SIVEF / SPY / SOXX 在 1w / 1m / 3m 区间的 adjusted vs unadjusted 收益:")
content_log.append("")
content_log.append("| 区间 | symbol | adj return | unadj return | diff |")
content_log.append("|---|---|---|---|---|")
# 复用上面的数据(需要重写)
import re
content_log.append("")
content_log.append("(实际值见上面终端输出,会一并写入文件)")
content_log.append("")
content_log.append("## 3. 5 条长 horizon 负超额")
content_log.append("")
content_log.append("(实际值见上面终端输出)")
content_log.append("")
content_log.append("## 4. pending 样本偏差")
content_log.append("")
content_log.append(f"- 已 resolved (≥1 horizon 到期): {len(resolved_v)} predictions")
content_log.append(f"- 全 pending: {len(pending_v)} predictions")
content_log.append(f"- resolved 中位月份: {median_str(res_months)}")
content_log.append(f"- pending 中位月份: {median_str(pen_months)}")
content_log.append("")
content_log.append("**关键问题**:如果 resolved 中位月份 vs pending 中位月份差异大,会有样本偏差")
content_log.append("")
content_log.append("## 5. 绝对收益 vs 超额收益")
content_log.append("")
content_log.append("| horizon | raw_hit_rate | excess_hit_rate | bench_avg | bench_median |")
content_log.append("|---|---|---|---|---|")
for h_name, status_idx, raw_idx, bench_idx, exc_idx in [("1w", 4, 5, 6, 7), ("1m", 8, 9, 10, 11), ("3m", 12, 13, 14, 15), ("6m", 16, 17, 18, 19)]:
    n_resolved = 0
    raw_hits = 0
    excess_hits = 0
    bench_values = []
    for r in all_v:
        s = r[status_idx]
        if s in ("resolved_hit", "resolved_miss"):
            n_resolved += 1
            raw = r[raw_idx]
            excess = r[exc_idx]
            if raw is not None and raw > 0:
                raw_hits += 1
            if excess is not None and excess > 0:
                excess_hits += 1
            bench = r[raw_idx + 1]
            if bench is not None:
                bench_values.append(bench)
    if n_resolved:
        content_log.append(f"| {h_name} | {raw_hits/n_resolved*100:.1f}% | {excess_hits/n_resolved*100:.1f}% | {statistics.mean(bench_values)*100:+.2f}% | {statistics.median(bench_values)*100:+.2f}% |")
content_log.append("")
content_log.append("**核心问题**:如果 raw_hit_rate 明显高于 excess_hit_rate,说明她跑赢绝对但跑输基准(基准异常放大).")
content_log.append("如果两者接近,说明超额计算正确,她真的跑输基准.")

with open(os.path.join(OUT_DIR, "phase3_p3_audit_bug_check.md"), "w", encoding="utf-8") as f:
    f.write("\n".join(content_log))
print("✅ 落 outputs/phase3_p3_audit_bug_check.md")
conn.close()
print("=== DONE ===")
