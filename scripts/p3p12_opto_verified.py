"""P3-12 光通信 8 票 — 已验证 vs 待验证,严格拆开"""
import os, sqlite3, json
from datetime import datetime
from collections import defaultdict
import statistics

DB = "/workspace/data/signalboard_full.db"
OUT = "/workspace/outputs/phase3_p12_opto_verified.md"

conn = sqlite3.connect(DB, timeout=30)
c = conn.cursor()

with open("/workspace/logs/p3p9_tiers.json") as f:
    tiers = json.load(f)
tier_a_pids = set(pid for pid, t in tiers.items() if t == "A")

# 光通信 8 票
OPTO = ["AAOI", "AXTI", "COHR", "CRDO", "IQE", "LITE", "POET", "SIVE"]
today = "2026-06-22"

# 拉每只票的 tier_A 全部 + verifications
placeholders = ",".join(["?"] * len(tier_a_pids))
sql = f"""
SELECT p.ticker, p.prediction_id, p.direction, p.published_at,
       v.entry_date_actual, v.entry_price,
       v.h_1w_status, v.h_1w_excess_return,
       v.h_1m_status, v.h_1m_excess_return,
       v.h_3m_status, v.h_3m_excess_return,
       v.h_6m_status, v.h_6m_excess_return
FROM predictions p
JOIN verifications v ON p.prediction_id=v.prediction_id
WHERE p.ticker IN ({",".join(["?"] * len(OPTO))})
  AND p.prediction_id IN ({placeholders})
ORDER BY p.ticker, p.published_at
"""
rows = c.execute(sql, OPTO + list(tier_a_pids)).fetchall()
print(f"光通信 8 票 tier_A 总数: {len(rows)} 条")

# 按 ticker 分组
by_ticker = defaultdict(list)
for r in rows:
    by_ticker[r[0]].append(r)

# 每只票详细分析
def horizon_stats(rows, h_idx, e_idx):
    n_res, n_pend, n_hit = 0, 0, 0
    exc_vals = []
    for r in rows:
        s = r[h_idx]
        e = r[e_idx]
        if s in ("resolved_hit", "resolved_miss"):
            n_res += 1
            if s == "resolved_hit":
                n_hit += 1
            if isinstance(e, (int, float)):
                exc_vals.append(e * 100)
        elif s == "pending":
            n_pend += 1
    return n_res, n_pend, n_hit, exc_vals

md = []
md.append("# P3-12 光通信 8 票 — 已验证 vs 待验证,严格拆开")
md.append("")
md.append(f"**生成时间**: {datetime.utcnow().isoformat()}Z")
md.append(f"**当前日期**: {today}")
md.append("")
md.append("**铁律**: 3m horizon = entry + 90 天,所以:")
md.append("- 3m 已 resolved: entry_date + 90 天 ≤ 今天")
md.append("- 3m pending: entry_date + 90 天 > 今天 (还在等待)")
md.append("")
md.append("---")
md.append("")

# 总体概览
md.append("## 0. 光通信 8 票总览")
md.append("")
md.append("| ticker | tier_A 总数 | 3m resolved | 3m pending | 6m resolved | 6m pending |")
md.append("|---|---|---|---|---|---|")
total_a = 0
total_3m_res = 0
total_3m_pend = 0
for t in OPTO:
    trs = by_ticker[t]
    total_a += len(trs)
    n3r, n3p, _, _ = horizon_stats(trs, 10, 11)
    n6r, n6p, _, _ = horizon_stats(trs, 12, 13)
    total_3m_res += n3r
    total_3m_pend += n3p
    md.append(f"| {t} | {len(trs)} | {n3r} | {n3p} | {n6r} | {n6p} |")
md.append(f"| **总** | **{total_a}** | **{total_3m_res}** | **{total_3m_pend}** | 0 | {total_a} |")
md.append("")

md.append("---")
md.append("")

# 每只票详细
md.append("## 1. 光通信 8 票逐票分析 (3m 维度)")
md.append("")
for t in OPTO:
    trs = by_ticker[t]
    md.append(f"### {t}")
    md.append("")

    # 1w, 1m, 3m, 6m 全部
    h_stats = {}
    for h, h_idx, e_idx in [("1w", 6, 7), ("1m", 8, 9), ("3m", 10, 11), ("6m", 12, 13)]:
        n_res, n_pend, n_hit, exc_vals = horizon_stats(trs, h_idx, e_idx)
        h_stats[h] = {
            "n_res": n_res, "n_pend": n_pend, "n_hit": n_hit, "exc": exc_vals
        }

    # entry_date 范围
    entry_dates = sorted([r[4] for r in trs if r[4]])
    pub_dates = sorted([r[3][:10] for r in trs if r[3]])

    md.append(f"- **tier_A 总数**: {len(trs)} 条")
    md.append(f"- **published_at 范围**: {pub_dates[0]} ~ {pub_dates[-1]}")
    md.append(f"- **entry_date 范围**: {entry_dates[0]} ~ {entry_dates[-1]}" if entry_dates else "")

    # 关键: 3m 已到期 vs pending
    md.append(f"- **3m 状态**:")
    if h_stats["3m"]["n_res"] > 0:
        n = h_stats["3m"]["n_res"]
        nh = h_stats["3m"]["n_hit"]
        med = statistics.median(h_stats["3m"]["exc"])
        avg = statistics.mean(h_stats["3m"]["exc"])
        md.append(f"  - ✅ resolved: **{n} 条** (其中 {nh} hit, hit_rate={nh/n*100:.1f}%)")
        md.append(f"  - median excess: **{med:+.2f}%** / avg: **{avg:+.2f}%**")
    else:
        md.append(f"  - ❌ resolved: **0 条**")
    md.append(f"  - ⏳ pending: **{h_stats['3m']['n_pend']} 条** (entry + 90 天还没到)")

    md.append(f"- **1m 状态**:")
    if h_stats["1m"]["n_res"] > 0:
        n = h_stats["1m"]["n_res"]
        nh = h_stats["1m"]["n_hit"]
        med = statistics.median(h_stats["1m"]["exc"])
        avg = statistics.mean(h_stats["1m"]["exc"])
        md.append(f"  - resolved: {n} 条 (hit {nh}, hit_rate={nh/n*100:.1f}%)")
        md.append(f"  - median excess: **{med:+.2f}%** / avg: **{avg:+.2f}%**")
    else:
        md.append(f"  - resolved: 0 条")
    md.append(f"  - pending: {h_stats['1m']['n_pend']} 条")

    md.append(f"- **6m 状态**: resolved {h_stats['6m']['n_res']} / pending {h_stats['6m']['n_pend']}")

    # 最早 entry_date + 90 天
    if entry_dates:
        earliest = entry_dates[0]
        md.append(f"- **3m 最早到期**: {earliest} + 90 天 = (entry + 90 天) — 看 entry_date 实际推算")

    md.append("")

md.append("---")
md.append("")

# 强区"97.7% 3m 命中" 拆开来自哪几只票多少条
md.append("## 2. 强区 '97.7% 3m 命中' 拆开")
md.append("")
md.append("**97.7% 这个数字建立在多少条已到期 3m 预测上?**")
md.append("")
md.append("| ticker | 3m_resolved | 3m_hit | 3m_hit_rate | 3m_med | 3m_avg |")
md.append("|---|---|---|---|---|---|")
for t in OPTO:
    trs = by_ticker[t]
    n_res, _, n_hit, exc_vals = horizon_stats(trs, 10, 11)
    if n_res > 0:
        med = statistics.median(exc_vals)
        avg = statistics.mean(exc_vals)
        hr = n_hit/n_res*100
        md.append(f"| {t} | {n_res} | {n_hit} | {hr:.1f}% | {med:+.2f}% | {avg:+.2f}% |")
    else:
        md.append(f"| {t} | 0 | 0 | N/A | N/A | N/A |")
md.append("")

# 累计
all_3m_res = []
all_3m_hit = 0
for t in OPTO:
    trs = by_ticker[t]
    n_res, _, n_hit, exc_vals = horizon_stats(trs, 10, 11)
    all_3m_res.append((t, n_res, n_hit, exc_vals))
    all_3m_hit += n_hit

total_3m_res = sum(x[1] for x in all_3m_res)
all_3m_hit_rate = all_3m_hit/total_3m_res*100 if total_3m_res else 0
md.append(f"**强区 97.7% 总览**: 光通信 8 票 3m 总 resolved = **{total_3m_res} 条**,总 hit = **{all_3m_hit} 条**,hit_rate = **{all_3m_hit_rate:.1f}%**")
md.append("")

md.append("**3m resolved 来自哪几只票:**")
md.append("")
for t, n_res, n_hit, exc_vals in sorted(all_3m_res, key=lambda x: -x[1]):
    if n_res > 0:
        med = statistics.median(exc_vals) if exc_vals else 0
        md.append(f"- **{t}**: {n_res} 条 ({n_res/total_3m_res*100:.1f}% 占比) — hit_rate {n_hit/n_res*100:.1f}%, median {med:+.1f}%")
md.append("")

md.append("**SIVE 在 3m 维度贡献: 0 条 resolved** (全部 pending)")
md.append("")

md.append("---")
md.append("")

# SIVE 详细
md.append("## 3. SIVE 的 1m 神话 vs 3m 真空")
md.append("")
md.append("**SIVE 1m 战绩**: 100% 命中 / median +136.5% / n=237")
md.append("")
md.append("**SIVE 3m 战绩**: ❌ **0 条 resolved** (全部 pending)")
md.append("")
md.append("**SIVE 6m 战绩**: ❌ **0 条 resolved** (全部 pending)")
md.append("")
md.append("**核心矛盾**:")
md.append("- 我们的手册主指标是 **3m**(因为 1m 是噪音,3m 真 α)")
md.append("- 但 SIVE **目前没有 3m 数据**")
md.append("- 她的 1m 神话能否代表 3m? **未知 — 没有数据就不知道**")
md.append("")
md.append("**老实说**:")
md.append("- ✅ SIVE 1m 已验证是真强信号 (n=237 / 100% / +136%)")
md.append("- ❓ SIVE 3m 是不是同样强? **未知,需等数据到期 (2026 年 6 月底开始)**")
md.append("- ❓ SIVE 6m 是不是同样强? **未知,需等数据到期 (2026 年 9 月后)**")
md.append("")
md.append("**不要用的措辞**:")
md.append("- ❌ 'SIVE 必然封神'")
md.append("- ❌ 'SIVE 是顶级信号'")
md.append("- ❌ 'SIVE 3m 必然延续'")
md.append("")
md.append("**可以用的措辞**:")
md.append("- ✅ 'SIVE 1m 已 100% 命中 n=237,信号极强'")
md.append("- ✅ 'SIVE 3m 数据未到期,目前无法评判'")
md.append("- ✅ 'SIVE 长期真实能力需等数据完整'")
md.append("")

md.append("---")
md.append("")

# 强区数字拆开
md.append("## 4. 强区数字拆开 — 已验证 vs 待验证")
md.append("")
md.append("**当前'光通信强区 3m 97.7%' 拆分:**")
md.append("")
md.append("### 已验证 (3m 已到期)")
md.append("")
md.append("| ticker | 3m_resolved | 3m_hit | 3m_hit_rate | 3m_med |")
md.append("|---|---|---|---|---|")
verified_3m = []
for t in OPTO:
    trs = by_ticker[t]
    n_res, _, n_hit, exc_vals = horizon_stats(trs, 10, 11)
    if n_res > 0:
        med = statistics.median(exc_vals) if exc_vals else 0
        verified_3m.append((t, n_res, n_hit, med))
        hr = n_hit/n_res*100
        md.append(f"| {t} | {n_res} | {n_hit} | {hr:.1f}% | {med:+.2f}% |")
md.append("")

total_v_res = sum(x[1] for x in verified_3m)
total_v_hit = sum(x[2] for x in verified_3m)
v_hr = total_v_hit/total_v_res*100 if total_v_res else 0
md.append(f"**已验证光通信 (3m)**: {total_v_res} 条 resolved,{total_v_hit} hit,**{v_hr:.1f}% hit_rate**")
md.append("")

md.append("### 待验证 (3m pending)")
md.append("")
md.append("| ticker | 3m_pending | 预计 3m 到期时间 |")
md.append("|---|---|---|")
for t in OPTO:
    trs = by_ticker[t]
    _, n_pend, _, _ = horizon_stats(trs, 10, 11)
    if n_pend > 0:
        # 最早 entry + 90
        entries = sorted([r[4] for r in trs if r[4]])
        if entries:
            md.append(f"| {t} | {n_pend} | entry {entries[0]} 起,陆续 2026-06 ~ 2026-09 到期 |")
md.append("")

md.append("---")
md.append("")

# 诚实重述
md.append("## 5. 诚实重述 — 哪些已验证,哪些待验证")
md.append("")
md.append("### ✅ 已验证 (3m 数据已到期)")
md.append("")
md.append("**光通信强区判定 (3m):**")
md.append(f"- {total_v_res} 条已到期 3m 预测中,{total_v_hit} hit,**hit_rate = {v_hr:.1f}%**")
md.append(f"- 这来自 {[x[0] for x in verified_3m]} (注:SIVE 不在内)")
md.append(f"- 样本量足够,可以做**已验证板块能力**判定")
md.append("")
md.append("**具体哪些票已验证:**")
md.append("")
verified_count = len(verified_3m)
md.append(f"- **{verified_count} 只票有 3m 已验证数据**: {', '.join(x[0] for x in verified_3m)}")
md.append("")
md.append("**关键**:**已验证的板块能力 = AAOI + AXTI + CRDO + LITE + POET 共 5 只票** (COHR/IQE 0 resolved,SIVE pending,未入已验证)**")
md.append("")
md.append("### ❌ 待验证 (3m pending,未经检验)")
md.append("")
md.append("**SIVE**:")
md.append("- ❌ 3m 数据 0 条 resolved (全部 pending)")
md.append("- ❌ 6m 数据 0 条 resolved (全部 pending)")
md.append("- ✅ 1m 数据已 100% 命中 (n=237)")
md.append("- **结论**: SIVE 的'强区'贡献 **目前只有 1m 维度**,3m/6m 维度**尚未验证**")
md.append("")
md.append("**这意味着**:")
md.append("")
md.append("1. **手册主指标 3m 的 '97.7% hit' 不包含 SIVE**")
md.append(f"2. 已验证的 5 只光通信票 3m hit {v_hr:.1f}% 是真实 α")
md.append("3. SIVE 是**待验证**的强信号 — 1m 已确认,3m 需等")
md.append("4. 不能把 SIVE 算进 '已验证强区' 的 8 只票里")
md.append("")
md.append("### 真实结论分层")
md.append("")
md.append("**已验证 (3m hit data)**:")
md.append(f"- **光通信强区 (5 票,排除 SIVE/COHR/IQE)**: 3m hit {v_hr:.1f}% / n={total_v_res}")
md.append("- 这是**真实可信的板块能力**")
md.append("")
md.append("**待验证 (1m 已确认, 3m pending)**:")
md.append("- **SIVE**: 1m 100% / n=237 / med +136.5% — 1m 维度极强,3m 维度待评")
md.append("- **COHR**: 1m 100% n=1,3m pending")
md.append("- **IQE**: 0 条 1m/3m resolved")
md.append("- 这些是**强信号但 3m 维度未验证**")
md.append("")
md.append("**手册规则 (修正版)**:")
md.append("")
md.append(f"**HARD PASS (3m 已验证强区)** — 仅以下 5 只票:")
md.append(f"- AAOI / AXTI / CRDO / LITE / POET (3m hit {v_hr:.1f}% / n=44)")
md.append("")
md.append("**SOFT PASS (1m 强信号,3m 待验证)** — 3 只票:")
md.append("- SIVE (1m 100% n=237, 3m pending) — 最大样本,信号最强")
md.append("- COHR (1m 100% n=1, 3m pending) — n=1,样本极小")
md.append("- IQE (n=4 全部 pending) — 0 数据")
md.append("- **建议**: 仓位减半 (等 3m 验证后再标准仓)")
md.append("- **不是**: '光通信强区' 自动包含 SIVE")
md.append("")

with open(OUT, "w", encoding="utf-8") as f:
    f.write("\n".join(md))

print(f"\n✅ 落 {OUT}")
print(f"   文件大小: {os.path.getsize(OUT)/1024:.1f} KB")
conn.close()
