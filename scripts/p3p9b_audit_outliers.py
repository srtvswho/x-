"""P3-9b tier_A 三个陷阱排除

1. 拆掉 SIVE / SIVE+NBIS,看 tier_A 真实底色
2. 6m 样本按 ticker + 月份分布,光通信 vs 非光通信
3. tier_A 核心标的首次 tier_A 论证时价 vs 起涨点
"""
import os, sqlite3, json
from datetime import datetime
from collections import Counter, defaultdict
import statistics, math

DB = "/workspace/data/signalboard_full.db"
OUT_DIR = "/workspace/outputs"
conn = sqlite3.connect(DB, timeout=30)
c = conn.cursor()

with open("/workspace/logs/p3p9_tiers.json") as f:
    tiers = json.load(f)
tier_a_pids = set(pid for pid, t in tiers.items() if t == "A")
tier_b_pids = set(pid for pid, t in tiers.items() if t == "B")
tier_c_pids = set(pid for pid, t in tiers.items() if t == "C")
print(f"tier_A: {len(tier_a_pids)}, tier_B: {len(tier_b_pids)}, tier_C: {len(tier_c_pids)}")

# 拉 tier_A 全部数据
placeholders = ",".join(["?"] * len(tier_a_pids))
sql = f"""
SELECT p.prediction_id, p.ticker, p.direction, p.published_at, p.thesis_summary,
       v.entry_date_actual, v.entry_price,
       v.h_1w_status, v.h_1w_excess_return,
       v.h_1m_status, v.h_1m_excess_return, v.h_1m_raw_return,
       v.h_3m_status, v.h_3m_excess_return, v.h_3m_raw_return,
       v.h_6m_status, v.h_6m_excess_return, v.h_6m_raw_return
FROM predictions p
JOIN verifications v ON p.prediction_id=v.prediction_id
WHERE p.prediction_id IN ({placeholders})
"""
tier_a_rows = c.execute(sql, list(tier_a_pids)).fetchall()
print(f"tier_A rows: {len(tier_a_rows)}")

def wilson(h, n, z=1.96):
    if n == 0: return None
    p = h/n
    d = 1 + z*z/n
    return ((p + z*z/(2*n))/d - z*math.sqrt(p*(1-p)/n + z*z/(4*n*n))/d)

def stats(rows, label, horizons=[("1w", 7, 8), ("1m", 9, 10), ("3m", 12, 13), ("6m", 15, 16)]):
    print(f"\n=== {label} (n={len(rows)}) ===")
    print(f"  {'horizon':6s}  {'n_resolved':10s}  {'hit_rate':8s}  {'wilson_low':10s}  {'median_exc':10s}  {'avg_exc':10s}")
    for h, st_idx, exc_idx in horizons:
        n_res, n_h = 0, 0
        exc_vals = []
        for r in rows:
            s = r[st_idx]
            e = r[exc_idx]
            if s == "resolved_hit":
                n_res += 1
                n_h += 1
                if isinstance(e, (int, float)): exc_vals.append(e)
            elif s == "resolved_miss":
                n_res += 1
                if isinstance(e, (int, float)): exc_vals.append(e)
        hr = n_h/n_res*100 if n_res else 0
        wl = wilson(n_h, n_res)
        med = statistics.median(exc_vals)*100 if exc_vals else None
        avg = statistics.mean(exc_vals)*100 if exc_vals else None
        wl_s = f"{wl*100:.1f}%" if wl is not None else "N/A"
        med_s = f"{med:+.2f}%" if med is not None else "N/A"
        avg_s = f"{avg:+.2f}%" if avg is not None else "N/A"
        print(f"  {h:6s}  {n_res:10d}  {hr:6.1f}%  {wl_s:10s}  {med_s:10s}  {avg_s:10s}")
    return rows


# 1. 三个版本对比
print("=" * 80)
print("陷阱 1: 拆掉 SIVE / SIVE+NBIS,看 tier_A 真实底色")
print("=" * 80)

# 全 tier_A
all_a = tier_a_rows
# 去 SIVE
no_sive = [r for r in tier_a_rows if r[1] != "SIVE"]
# 去 SIVE + NBIS
no_sive_nbis = [r for r in tier_a_rows if r[1] not in ("SIVE", "NBIS")]

stats(all_a, "tier_A 全样本")
stats(no_sive, "tier_A 去掉 SIVE")
stats(no_sive_nbis, "tier_A 去掉 SIVE+NBIS")

# 集中度
print()
print("=== tier_A ticker 集中度(SIVE+NBIS 占比) ===")
tier_a_ticker = Counter(r[1] for r in tier_a_rows)
total = len(tier_a_rows)
sive_n = tier_a_ticker.get("SIVE", 0)
nbis_n = tier_a_ticker.get("NBIS", 0)
print(f"  SIVE: {sive_n} ({sive_n/total*100:.1f}%)")
print(f"  NBIS: {nbis_n} ({nbis_n/total*100:.1f}%)")
print(f"  SIVE+NBIS: {sive_n+nbis_n} ({(sive_n+nbis_n)/total*100:.1f}%)")
print(f"  top 5 占比: {sum(n for _, n in tier_a_ticker.most_common(5))/total*100:.1f}%")


# 2. 6m 样本幸存者偏差
print()
print("=" * 80)
print("陷阱 2: 6m 样本幸存者偏差")
print("=" * 80)

# tier_A 6m resolved 的 76 条
six_m = []
for r in tier_a_rows:
    pid, ticker, direction, pub, thesis, edate, eprice, \
    s1w, e1w, s1m, e1m, r1m, s3m, e3m, r3m, s6m, e6m, r6m = r
    if s6m in ("resolved_hit", "resolved_miss"):
        six_m.append(r)

print(f"tier_A 6m resolved: {len(six_m)} 条")

# 按 ticker 分布
six_m_ticker = Counter(r[1] for r in six_m)
print(f"\n按 ticker 分布:")
for t, n in six_m_ticker.most_common():
    print(f"  {t}: {n} ({n/len(six_m)*100:.1f}%)")

# 按 published_at 月份
six_m_month = Counter(r[3][:7] for r in six_m)
print(f"\n按 published_at 月份分布:")
for m, n in sorted(six_m_month.items()):
    print(f"  {m}: {n}")

# 光通信 vs 非光通信
OPTO_TICKERS = {"AAOI", "AXTI", "LITE", "SIVE", "COHR", "CRDO", "IQE", "POET", "COHR"}
opto = [r for r in six_m if r[1] in OPTO_TICKERS]
non_opto = [r for r in six_m if r[1] not in OPTO_TICKERS]
print(f"\n光通信: {len(opto)} 条 ({len(opto)/len(six_m)*100:.1f}%)")
print(f"非光通信: {len(non_opto)} 条 ({len(non_opto)/len(six_m)*100:.1f}%)")

# 光通信 vs 非光通信 6m hit
def hit_stats(rows, label):
    n_res, n_h = 0, 0
    exc_vals = []
    for r in rows:
        s = r[15]  # s6m
        e = r[16]  # e6m
        if s == "resolved_hit":
            n_res += 1
            n_h += 1
            if isinstance(e, (int, float)): exc_vals.append(e)
        elif s == "resolved_miss":
            n_res += 1
            if isinstance(e, (int, float)): exc_vals.append(e)
    hr = n_h/n_res*100 if n_res else 0
    wl = wilson(n_h, n_res)
    med = statistics.median(exc_vals)*100 if exc_vals else None
    avg = statistics.mean(exc_vals)*100 if exc_vals else None
    print(f"  [{label}] n={n_res} hit={hr:.1f}% wilson={wl*100 if wl else 0:.1f}% med={med if med else 0:+.2f}% avg={avg if avg else 0:+.2f}%")

print(f"\n光通信 6m:")
hit_stats(opto, "光通信")
print(f"非光通信 6m:")
hit_stats(non_opto, "非光通信")


# 3. tier_A 核心标的追高检验
print()
print("=" * 80)
print("陷阱 3: tier_A 追高检验")
print("=" * 80)

CORE = ["SIVE", "NBIS", "AAOI", "AXTI", "LITE"]
price_cache_dir = "/workspace/data/price_cache"

def load_bars(t):
    path = f"{price_cache_dir}/{t}_FULL_HISTORY.json"
    if not os.path.exists(path) and t == "SIVE":
        path = f"{price_cache_dir}/SIVEF_FULL_HISTORY.json"
    if not os.path.exists(path):
        return []
    with open(path) as f:
        return json.load(f)

for t in CORE:
    # 找 tier_A 首次论证
    sql = f"""
    SELECT v.prediction_id, p.published_at, v.entry_date_actual, v.entry_price, p.thesis_summary
    FROM predictions p
    JOIN verifications v ON p.prediction_id=v.prediction_id
    WHERE p.ticker=? AND p.prediction_id IN ({placeholders})
    ORDER BY p.published_at ASC LIMIT 1
    """
    r = c.execute(sql, [t] + list(tier_a_pids)).fetchone()
    if not r:
        print(f"\n{t}: 无 tier_A 数据")
        continue
    pid, pub, edate, eprice, thesis = r
    if not isinstance(eprice, (int, float)):
        print(f"\n{t}: entry_price 无效 ({eprice}), 跳过")
        continue
    print(f"\n=== {t} ===")
    print(f"  tier_A 首次论证: pub={pub[:10]} entry={edate} px=${eprice:.4f}")
    if thesis:
        print(f"  thesis: {thesis[:120]}")

    bars = load_bars(t)
    if not bars:
        print(f"  无 bars 数据,跳过起涨点计算")
        continue

    # 找 entry_date 之前的 60 天 low
    edate_idx = None
    for i, b in enumerate(bars):
        if b["date"] >= edate:
            edate_idx = i
            break
    if edate_idx is None:
        print(f"  entry_date 超出数据范围")
        continue

    # pre window (entry 前 60 天)
    pre = bars[max(0, edate_idx-60):edate_idx+1]
    if not pre:
        continue
    pre_low = min(b["l"] for b in pre)
    pre_low_date = [b["date"] for b in pre if b["l"] == pre_low][0]
    pre_high = max(b["h"] for b in pre)
    pre_high_date = [b["date"] for b in pre if b["h"] == pre_high][0]

    # 当前价
    cur = bars[-1]

    pct_above_low = (eprice - pre_low) / pre_low * 100
    pct_below_high = (pre_high - eprice) / pre_high * 100
    pct_to_cur = (cur["c"] - eprice) / eprice * 100
    pct_from_low = (cur["c"] - pre_low) / pre_low * 100

    print(f"  pre 60 天: low ${pre_low:.4f} ({pre_low_date}), high ${pre_high:.4f} ({pre_high_date})")
    print(f"  她的 entry 价相对 pre_low: +{pct_above_low:.1f}% (她是否追高)")
    print(f"  票从 entry 到当前 ({cur['date']}): {pct_to_cur:+.1f}%")
    print(f"  票从 pre_low 到当前: {pct_from_low:+.1f}%")


# 落报告
out_md = []
out_md.append("# P3-9b tier_A 三个陷阱排除")
out_md.append("")
out_md.append(f"**生成时间**: {datetime.utcnow().isoformat()}Z")
out_md.append("")
out_md.append("## 陷阱 1: 拆掉 SIVE / SIVE+NBIS 看 tier_A 真实底色")
out_md.append("")
out_md.append("**SIVE + NBIS 占 tier_A 多大比例** (这是讨论基础):")
out_md.append("")
out_md.append("| ticker | n | 占比 |")
out_md.append("|---|---|---|")
for t, n in tier_a_ticker.most_common(15):
    out_md.append(f"| {t} | {n} | {n/total*100:.1f}% |")
out_md.append("")
out_md.append("**三个版本对比**:")
out_md.append("")
out_md.append("| 口径 | n | 1m hit | 1m wilson | 1m med | 3m hit | 3m med | 6m hit | 6m med |")
out_md.append("|---|---|---|---|---|---|---|---|---|")
def fmt_row(rows, label):
    line = [label, len(rows)]
    for h, st_idx, exc_idx in [("1m", 9, 10), ("3m", 12, 13), ("6m", 15, 16)]:
        n_res, n_h = 0, 0
        exc_vals = []
        for r in rows:
            s = r[st_idx]
            e = r[exc_idx]
            if s == "resolved_hit":
                n_res += 1
                n_h += 1
                if isinstance(e, (int, float)): exc_vals.append(e)
            elif s == "resolved_miss":
                n_res += 1
                if isinstance(e, (int, float)): exc_vals.append(e)
        hr = n_h/n_res*100 if n_res else 0
        wl = wilson(n_h, n_res)
        med = statistics.median(exc_vals)*100 if exc_vals else None
        line.extend([f"{hr:.1f}%", f"{wl*100:.1f}%" if wl else "N/A", f"{med:+.2f}%" if med else "N/A"])
    out_md.append("| " + " | ".join(str(x) for x in line) + " |")
fmt_row(all_a, "tier_A 全样本")
fmt_row(no_sive, "tier_A 去掉 SIVE")
fmt_row(no_sive_nbis, "tier_A 去掉 SIVE+NBIS")
out_md.append("")
out_md.append("## 陷阱 2: 6m 样本的幸存者偏差")
out_md.append("")
out_md.append(f"**tier_A 6m resolved = {len(six_m)} 条**")
out_md.append("")
out_md.append("### 按 ticker 分布")
out_md.append("")
out_md.append("| ticker | n | 占比 |")
out_md.append("|---|---|---|")
for t, n in six_m_ticker.most_common():
    out_md.append(f"| {t} | {n} | {n/len(six_m)*100:.1f}% |")
out_md.append("")
out_md.append("### 按 published_at 月份")
out_md.append("")
out_md.append("| 月份 | n |")
out_md.append("|---|---|")
for m, n in sorted(six_m_month.items()):
    out_md.append(f"| {m} | {n} |")
out_md.append("")
out_md.append("### 光通信 vs 非光通信")
out_md.append("")
out_md.append(f"- 光通信 (SIVE/AAOI/AXTI/LITE/COHR/CRDO/IQE/POET): **{len(opto)} 条 ({len(opto)/len(six_m)*100:.1f}%)**")
out_md.append(f"- 非光通信: {len(non_opto)} 条 ({len(non_opto)/len(six_m)*100:.1f}%)")
out_md.append("")
out_md.append("| 类别 | n | 6m hit_rate | 6m wilson_low | 6m med | 6m avg |")
out_md.append("|---|---|---|---|---|---|")
for rows, lbl in [(opto, "光通信"), (non_opto, "非光通信")]:
    n_res, n_h = 0, 0
    exc_vals = []
    for r in rows:
        s = r[15]
        e = r[16]
        if s == "resolved_hit":
            n_res += 1
            n_h += 1
            if isinstance(e, (int, float)): exc_vals.append(e)
        elif s == "resolved_miss":
            n_res += 1
            if isinstance(e, (int, float)): exc_vals.append(e)
    hr = n_h/n_res*100 if n_res else 0
    wl = wilson(n_h, n_res)
    med = statistics.median(exc_vals)*100 if exc_vals else None
    avg = statistics.mean(exc_vals)*100 if exc_vals else None
    out_md.append(f"| {lbl} | {n_res} | {hr:.1f}% | {wl*100:.1f}% | {med:+.2f}% | {avg:+.2f}% |")
out_md.append("")
out_md.append("## 陷阱 3: 追高检验")
out_md.append("")
out_md.append("**核心问题: 她 tier_A 首次认真论证时,票是否已经涨了一截?**")
out_md.append("")
out_md.append("| ticker | tier_A 首次 pub | entry | entry_px | pre_60d_low | 相对 pre_low | 票后涨 |")
out_md.append("|---|---|---|---|---|---|---|")
# 重跑一遍简化版
for t in CORE:
    sql = f"""SELECT p.published_at, v.entry_date_actual, v.entry_price
    FROM predictions p JOIN verifications v ON p.prediction_id=v.prediction_id
    WHERE p.ticker=? AND p.prediction_id IN ({placeholders}) ORDER BY p.published_at ASC LIMIT 1"""
    r = c.execute(sql, [t] + list(tier_a_pids)).fetchone()
    if not r: continue
    pub, edate, eprice = r
    if not isinstance(eprice, (int, float)): continue
    bars = load_bars(t)
    if not bars: continue
    edate_idx = None
    for i, b in enumerate(bars):
        if b["date"] >= edate:
            edate_idx = i
            break
    if edate_idx is None: continue
    pre = bars[max(0, edate_idx-60):edate_idx+1]
    if not pre: continue
    pre_low = min(b["l"] for b in pre)
    cur = bars[-1]
    pct_above_low = (eprice - pre_low) / pre_low * 100
    pct_to_cur = (cur["c"] - eprice) / eprice * 100
    out_md.append(f"| {t} | {pub[:10]} | {edate} | ${eprice:.4f} | ${pre_low:.4f} | **+{pct_above_low:.1f}%** | {pct_to_cur:+.1f}% |")
out_md.append("")
out_md.append("**解读**:")
out_md.append("- 相对 pre_low +100% 以上 → 她是追高者(在票已涨 1 倍后才认真论证)")
out_md.append("- 相对 pre_low 0%~50% → 她是早期识别者(在起涨早期论证)")
out_md.append("- 相对 pre_low 负 → 她是预言家(在起涨前就建仓)")

with open(os.path.join(OUT_DIR, "phase3_p9b_outlier_audit.md"), "w", encoding="utf-8") as f:
    f.write("\n".join(out_md))
print(f"\n✅ 落 outputs/phase3_p9b_outlier_audit.md")
conn.close()
