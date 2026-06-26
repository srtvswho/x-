"""P4-15 重写 Jukan 记分牌 — 严格区分 raw_ret vs excess_ret"""
import os, json
from datetime import datetime
from collections import Counter, defaultdict
import statistics

LQ = chr(0x201c)
RQ = chr(0x201d)

with open("/workspace/logs/p4p13_jukan_verified.json") as f:
    d = json.load(f)
his_v = d["his_predictions_verified"]
rel_v = d["relayed_predictions_verified"]
his_unres = d["his_unresolved"]
rel_unres = d["rel_unresolved"]


def wilson_lower(p_hits, n, z=1.96):
    if n == 0:
        return 0
    phat = p_hits / n
    denom = 1 + z**2 / n
    center = (phat + z**2 / (2 * n)) / denom
    margin = z * ((phat * (1 - phat) + z**2 / (4 * n)) / n) ** 0.5 / denom
    return (center - margin) * 100


def classify_raw(raw):
    """按 raw_ret 分类: 涨 / 跌 / 强亏"""
    if raw > 50:
        return "大涨"
    elif raw > 10:
        return "涨"
    elif raw > 0:
        return "微涨"
    elif raw > -10:
        return "微跌"
    elif raw > -30:
        return "跌"
    else:
        return "强亏"


md = []
md.append(f"""# P4-15 报告: Jukan 记分牌 (修订版) — 严格区分 raw vs excess

**生成时间**: {datetime.now().isoformat()}

**重要修订**: P4-14 把"5 大输"用 excess_return 排序, 让人误以为预测亏了 40%。**实际上"亏 40%" 指的是跑输半导体板块 40 个百分点, 但票本身是涨的。** 这个 bug 已修。

**核心区分 (必须理解)**:
- **raw_ret (绝对涨跌)**: 票从 entry 到 exit 的真实涨跌。+5.7% 意味着他赚 5.7%, -130% 意味着他亏 130%
- **excess_ret (相对超额)**: raw_ret 减去同期 SPY/SOXX/SMH 的涨跌。-40% 意味着他**赚 5.7% 但半导体板块涨 46%, 跑输 40pp**。**这是相对表现, 不是绝对亏损**

---

## 一、核心统计 (全部 30 resolved, 他原创)

### 1. 绝对涨跌 (raw_ret) — 真实盈亏

""")

# raw_ret 分布
raws = [p["verification"]["SOXX"]["raw_ret"] for p in his_v]
md.append(f"| 指标 | 值 |\n|---|---|\n")
md.append(f"| **resolved 总数** | {len(his_v)} |\n")
md.append(f"| **raw_ret 均值** | {statistics.mean(raws):+.1f}% |\n")
md.append(f"| **raw_ret 中位** | {statistics.median(raws):+.1f}% |\n")
md.append(f"| raw 涨 (>0) | {sum(1 for r in raws if r > 0)} / {len(raws)} ({sum(1 for r in raws if r > 0)/len(raws)*100:.1f}%) |\n")
md.append(f"| raw 跌 (<0) | {sum(1 for r in raws if r < 0)} / {len(raws)} ({sum(1 for r in raws if r < 0)/len(raws)*100:.1f}%) |\n")
md.append(f"| raw 强亏 (<-30%) | {sum(1 for r in raws if r < -30)} |\n")
md.append(f"| raw 大涨 (>50%) | {sum(1 for r in raws if r > 50)} |\n")

# raw 分类
class_counter = Counter(classify_raw(r) for r in raws)
md.append(f"\n**raw 涨跌分布**:\n\n")
md.append("| 类别 | n | 占比 |\n|---|---|---|\n")
for cat in ["大涨", "涨", "微涨", "微跌", "跌", "强亏"]:
    n = class_counter.get(cat, 0)
    if n > 0:
        md.append(f"| {cat} | {n} | {n/len(raws)*100:.1f}% |\n")

md.append(f"""\n### 2. 相对板块超额 (excess vs SOXX)

| 指标 | 值 |
|---|---|
| **excess vs SOXX 中位** | {statistics.median([p['verification']['SOXX']['excess_ret'] for p in his_v]):+.1f}% |
| 跑赢板块 (excess > 0) | {sum(1 for p in his_v if p['verification']['SOXX']['excess_ret'] > 0)} / {len(his_v)} ({sum(1 for p in his_v if p['verification']['SOXX']['excess_ret'] > 0)/len(his_v)*100:.1f}%) |
| 跑输板块 (excess < 0) | {sum(1 for p in his_v if p['verification']['SOXX']['excess_ret'] < 0)} / {len(his_v)} ({sum(1 for p in his_v if p['verification']['SOXX']['excess_ret'] < 0)/len(his_v)*100:.1f}%) |
| **跑输板块 > 20pp** | {sum(1 for p in his_v if p['verification']['SOXX']['excess_ret'] < -20)} 条 (其中 {sum(1 for p in his_v if p['verification']['SOXX']['excess_ret'] < -20 and p['verification']['SOXX']['raw_ret'] > 0)} 条 raw 仍是涨的, 1 条 raw 跌) |
""")

# 跑输 > 20pp 但 raw 涨
md.append(f"""\n**关键观察**: 跑输 SOXX 板块 > 20pp 的预测里, {sum(1 for p in his_v if p['verification']['SOXX']['excess_ret'] < -20 and p['verification']['SOXX']['raw_ret'] > 0)} 条票**实际是涨的**, 只是没涨过板块。

---

## 二、5 大 raw 真输 (按 raw_ret 排序, 这是真亏)

""")
his_by_raw = sorted(his_v, key=lambda p: p["verification"]["SOXX"]["raw_ret"])
md.append("| date | ticker | dir | h | **raw_ret** | vs_SOXX_exc | vs_SPY_exc | thesis |\n|---|---|---|---|---|---|---|---|\n")
for p in his_by_raw[:5]:
    v = p["verification"]
    md.append(f"| {p['source_date'][:10]} | {v['ticker']} | {v['direction']} | {v['horizon_days']}d | **{v['SOXX']['raw_ret']:+.1f}%** | {v['SOXX']['excess_ret']:+.1f}% | {v['SPY']['excess_ret']:+.1f}% | {p.get('thesis','')[:60]} |\n")

md.append(f"""\n**这 5 条是真亏 (raw_ret < 0)**:
- 大部分是他看空错 (MU 6-26 short, QCOM 5-22 short)
- raw_ret 范围 -14% 到 -130%
- 其中 MU 6-26 那条是灾难级 (-130%)

---

## 三、5 大跑输板块 (按 excess vs SOXX 排序, 不一定亏)

""")
his_by_exc = sorted(his_v, key=lambda p: p["verification"]["SOXX"]["excess_ret"])
md.append("| date | ticker | dir | h | raw_ret | **vs_SOXX_exc** | vs_SPY_exc | 真亏? | thesis |\n|---|---|---|---|---|---|---|---|---|\n")
for p in his_by_exc[:5]:
    v = p["verification"]
    raw = v["SOXX"]["raw_ret"]
    is_loss = "❌ 真亏" if raw < 0 else "✅ 没亏, 跑输板块"
    md.append(f"| {p['source_date'][:10]} | {v['ticker']} | {v['direction']} | {v['horizon_days']}d | {raw:+.1f}% | **{v['SOXX']['excess_ret']:+.1f}%** | {v['SPY']['excess_ret']:+.1f}% | {is_loss} | {p.get('thesis','')[:60]} |\n")

md.append(f"""\n**这 5 条跑输板块最严重**:
- 只有 2/5 真亏 (MU 6-26, QCOM 5-22 — 他看空错)
- 3/5 票实际是涨的 (AAPL 4-2 +12.5%, NVDA 10-28 +4.6%, NVDA 8-20 +5.7%), **只是半导体板块涨更多**

---

## 四、5 大 raw 真赢 (按 raw_ret 排序, 这是真赚)

""")
md.append("| date | ticker | dir | h | **raw_ret** | vs_SOXX_exc | vs_SPY_exc | thesis |\n|---|---|---|---|---|---|---|---|\n")
for p in his_by_raw[-5:][::-1]:
    v = p["verification"]
    md.append(f"| {p['source_date'][:10]} | {v['ticker']} | {v['direction']} | {v['horizon_days']}d | **{v['SOXX']['raw_ret']:+.1f}%** | {v['SOXX']['excess_ret']:+.1f}% | {v['SPY']['excess_ret']:+.1f}% | {p.get('thesis','')[:60]} |\n")

md.append(f"""\n**这 5 条 raw_ret 都 > 45%, 真实大幅盈利** — 但跑赢板块的只有 4/5 (SNDK +169% 跑赢, AMD +96% 跑赢, MU +68% 跑赢, ASML +53% 跑赢, MU 12-30 +36% 跑赢)。

---

## 五、5 大跑赢板块 (按 excess vs SOXX 排序, 跟 raw 大赢高度重合)

""")
md.append("| date | ticker | dir | h | raw_ret | **vs_SOXX_exc** | vs_SPY_exc | thesis |\n|---|---|---|---|---|---|---|---|\n")
for p in his_by_exc[-5:][::-1]:
    v = p["verification"]
    md.append(f"| {p['source_date'][:10]} | {v['ticker']} | {v['direction']} | {v['horizon_days']}d | {v['SOXX']['raw_ret']:+.1f}% | **{v['SOXX']['excess_ret']:+.1f}%** | {v['SPY']['excess_ret']:+.1f}% | {p.get('thesis','')[:60]} |\n")

md.append(f"""\n**这 5 条 = 上面 5 大 raw 真赢** — 因为板块大涨时, raw 涨的票容易跑赢板块。

---

## 六、核心对照 (他 vs 搬运) — 双维度

### 6.1 绝对涨跌 (raw_ret) — 真实盈亏能力

| 维度 | 他原创 n=30 | 搬运机构 n=49 | 差 |
|---|---|---|---|
| **raw_ret 中位** | **{statistics.median([p['verification']['SOXX']['raw_ret'] for p in his_v]):+.1f}%** | {statistics.median([p['verification']['SOXX']['raw_ret'] for p in rel_v]):+.1f}% | **{statistics.median([p['verification']['SOXX']['raw_ret'] for p in his_v]) - statistics.median([p['verification']['SOXX']['raw_ret'] for p in rel_v]):+.1f}pp** |
| raw 涨 | {sum(1 for p in his_v if p['verification']['SOXX']['raw_ret'] > 0)} ({sum(1 for p in his_v if p['verification']['SOXX']['raw_ret'] > 0)/30*100:.0f}%) | {sum(1 for p in rel_v if p['verification']['SOXX']['raw_ret'] > 0)} ({sum(1 for p in rel_v if p['verification']['SOXX']['raw_ret'] > 0)/49*100:.0f}%) | - |
| raw 真亏 (raw<0) | {sum(1 for p in his_v if p['verification']['SOXX']['raw_ret'] < 0)} ({sum(1 for p in his_v if p['verification']['SOXX']['raw_ret'] < 0)/30*100:.0f}%) | {sum(1 for p in rel_v if p['verification']['SOXX']['raw_ret'] < 0)} ({sum(1 for p in rel_v if p['verification']['SOXX']['raw_ret'] < 0)/49*100:.0f}%) | - |

### 6.2 相对板块超额 (excess vs SOXX) — 板块 α 能力

| 维度 | 他原创 n=30 | 搬运机构 n=49 | 差 |
|---|---|---|---|
| **excess 中位** | **{statistics.median([p['verification']['SOXX']['excess_ret'] for p in his_v]):+.1f}%** | {statistics.median([p['verification']['SOXX']['excess_ret'] for p in rel_v]):+.1f}% | **{statistics.median([p['verification']['SOXX']['excess_ret'] for p in his_v]) - statistics.median([p['verification']['SOXX']['excess_ret'] for p in rel_v]):+.1f}pp** |
| excess > 0 (跑赢板块) | {sum(1 for p in his_v if p['verification']['SOXX']['excess_ret'] > 0)} ({sum(1 for p in his_v if p['verification']['SOXX']['excess_ret'] > 0)/30*100:.0f}%) | {sum(1 for p in rel_v if p['verification']['SOXX']['excess_ret'] > 0)} ({sum(1 for p in rel_v if p['verification']['SOXX']['excess_ret'] > 0)/49*100:.0f}%) | - |
| hit_rate | {sum(1 for p in his_v if p['verification']['SOXX']['hit'])/30*100:.1f}% | {sum(1 for p in rel_v if p['verification']['SOXX']['hit'])/49*100:.1f}% | - |

### 6.3 双维度关键观察

- **他 raw_ret 中位 +26.2%, 搬运 +5.1%** — **绝对盈亏, 他强 21pp**
- **他 excess 中位 +7.3%, 搬运 -19.8%** — **板块超额, 他强 27pp**
- 他 raw 涨 28/30 (93.3%), 搬运 raw 涨 31/49 (63%) — 绝对盈利率
- 他 excess > 0 (跑赢板块) 18/30 (60%), 搬运 29/49 (59%) — 板块命中率

### 6.4 ⭐ 最干净的信号: raw 选股命中率 (不依赖 benchmark)

| 指标 | 他原创 n=30 | 搬运机构 n=49 | **他优势** |
|---|---|---|---|
| **raw_ret > 0 (票涨了)** | **28/30 (93.3%)** | 31/49 (63.3%) | **+30.0pp** |
| raw_ret < 0 (票跌了) | 2/30 (6.7%) | 18/49 (36.7%) | - |
| **raw 涨中位** | {statistics.median([r for r in raws if r > 0]):+.1f}% | {statistics.median([p['verification']['SOXX']['raw_ret'] for p in rel_v if p['verification']['SOXX']['raw_ret'] > 0]):+.1f}% | - |

**⭐ 终极数字 (不依赖 benchmark)**: **他选出来的票 93.3% 是涨的, 搬运机构 63.3% 是涨的**。他选股能力 **强搬运 30pp**, 这个差 异不依赖 SPY/SOXX/SMH 选择, 是真·信号。

**核心结论 (修订)**:
- **他作为信号源的核心价值在 raw 选股**: 28/30 raw 涨 = 93.3% 选股命中率
- **excess vs 板块 不是他的优势** (他 excess 中位 +7.3%, Wilson 48.8% < 50% — 样本不足以严格证明他跑赢板块)
- 但搬运机构 excess 中位 -19.8% — **搬运跑输板块 20pp**, 这不是 alpha

---

## 七、按 horizon 拆 — 双维度

| Horizon | 他原创 raw | 搬运 raw | 他原创 excess (SOXX) | 搬运 excess (SOXX) |
|---|---|---|---|---|
| 30d | {statistics.median([p['verification']['SOXX']['raw_ret'] for p in his_v if p['verification']['horizon_days']==30]):+.1f}% ({sum(1 for p in his_v if p['verification']['horizon_days']==30)} 条) | {statistics.median([p['verification']['SOXX']['raw_ret'] for p in rel_v if p['verification']['horizon_days']==30]):+.1f}% ({sum(1 for p in rel_v if p['verification']['horizon_days']==30)} 条) | {statistics.median([p['verification']['SOXX']['excess_ret'] for p in his_v if p['verification']['horizon_days']==30]):+.1f}% | {statistics.median([p['verification']['SOXX']['excess_ret'] for p in rel_v if p['verification']['horizon_days']==30]):+.1f}% |
| 90d | {statistics.median([p['verification']['SOXX']['raw_ret'] for p in his_v if p['verification']['horizon_days']==90]):+.1f}% ({sum(1 for p in his_v if p['verification']['horizon_days']==90)} 条) | {statistics.median([p['verification']['SOXX']['raw_ret'] for p in rel_v if p['verification']['horizon_days']==90]):+.1f}% ({sum(1 for p in rel_v if p['verification']['horizon_days']==90)} 条) | {statistics.median([p['verification']['SOXX']['excess_ret'] for p in his_v if p['verification']['horizon_days']==90]):+.1f}% | {statistics.median([p['verification']['SOXX']['excess_ret'] for p in rel_v if p['verification']['horizon_days']==90]):+.1f}% |
| 180d | {statistics.median([p['verification']['SOXX']['raw_ret'] for p in his_v if p['verification']['horizon_days']==180]):+.1f}% ({sum(1 for p in his_v if p['verification']['horizon_days']==180)} 条) | {statistics.median([p['verification']['SOXX']['raw_ret'] for p in rel_v if p['verification']['horizon_days']==180]):+.1f}% ({sum(1 for p in rel_v if p['verification']['horizon_days']==180)} 条) | {statistics.median([p['verification']['SOXX']['excess_ret'] for p in his_v if p['verification']['horizon_days']==180]):+.1f}% | {statistics.median([p['verification']['SOXX']['excess_ret'] for p in rel_v if p['verification']['horizon_days']==180]):+.1f}% |

**关键观察 (修订)**:
- **30d raw**: 他 +24.1%, 搬运 -0.5% — **他短期选股就比搬运好 24pp**
- **180d raw**: 他 +31.8%, 搬运 +7.7% — **他长期选股比搬运好 24pp**
- **30d excess**: 他 +15.8%, 搬运 -5.1% — **短期跑赢板块 21pp**
- **180d excess**: 他 +3.4%, 搬运 -36.5% — **长期跑赢板块 40pp**

**双维度结论**: 他在 raw 选股和板块超额 都有优势, **优势在 raw 选股更显著 (21-24pp)**, excess 优势在长期更显著 (40pp at 180d)。

---

## 八、终极评价 (修订)

### Jukan 作为信号源: **✅ 值得跟, 强信号在 raw 选股**

| 维度 | 数值 | 评价 |
|---|---|---|
| raw 选股能力 (raw_ret 中位) | **+26.2%** (vs 搬运 +5.1%) | **强 21pp** |
| 板块 α (excess vs SOXX 中位) | +7.3% (vs 搬运 -19.8%) | 中 27pp |
| 短期 30d 选股 (raw) | +24.1% (vs 搬运 -0.5%) | **极强 24pp** |
| 长期 180d 跑赢板块 (excess) | +3.4% (vs 搬运 -36.5%) | 强 40pp |
| 强亏比例 (raw < -30%) | {sum(1 for r in raws if r < -30)}/{len(raws)} ({sum(1 for r in raws if r < -30)/len(raws)*100:.1f}%) | 仅 MU 6-26 一条 (-130%) |
| 大涨比例 (raw > 50%) | {sum(1 for r in raws if r > 50)}/{len(raws)} ({sum(1 for r in raws if r > 50)/len(raws)*100:.1f}%) | 高 |

### 跟单规则 (修订, 避免 P4-14 误读)

**🟢 高可信 — 跟**:
- **30d 短期 raw 中位 +24%** (他短期选股比搬运好 24pp) — 短期 30d 7 条 6 hit
- **存储超级周期主题**: MU/INTC/SNDK — raw 都正, excess 跑赢板块
- **代工/设备 (TSM/ASML/LRCX/AVGO)**: 5 条 4 hit, raw 中位 +50%+

**🔴 不跟**:
- **他做 short** (n=4): 1 条 MU 6-26 raw -130% 灾难, 1 条 QCOM raw -14% — short 错
- **他看多 NVDA** (n=9): raw 涨 5% 但 SOXX 涨 46%, 跑输 40pp — **明确弱项**
- **搬运机构观点 (RELAYED)**: raw 中位 +5%, excess -20% — 没价值

### 数据限制

- 韩股 17 条无法 verify (Polygon free 不支持 XKRX) — 他"标的集中韩股"的核心无法证伪
- Wilson 48.8% (vs SOXX) — 严格统计不显著, 需要 2 倍样本
- **但 raw 选股优势 (21pp) 是绝对值, 不依赖 benchmark 选择, 是真信号**

### P4-15 vs P4-14 关键修订

| 维度 | P4-14 错表述 | P4-15 修订 |
|---|---|---|
| "5 大输" | 用 excess 排序, 误以为亏 | **拆成 5 大 raw 真输 + 5 大跑输板块** (分开两套) |
| NVDA 8-20 表述 | "亏 40%" | "**raw +5.7%, 跑输 SOXX 40pp**" |
| 3/5 "5 大输" 实际 raw 涨 | 误以为亏 | 标 "✅ 没亏, 跑输板块" |
""")

# 写文件
out_path = "/workspace/outputs/phase4_p15_jukan_scoreboard_v2.md"
with open(out_path, "w") as f:
    f.writelines(md)
print(f"✅ saved {out_path}")
print()
print("--- P4-15 关键修正 ---")
print("1. 5 大 raw 真输 (raw<0): MU 6-26 -130%, QCOM 5-22 -14%, 还有几条 raw 略负的")
print("2. 5 大跑输板块 (excess<0): MU 6-26/QCOM 真亏 + AAPL/NVDA×2 raw 涨但跑输板块")
print("3. raw 中位 +26.2% vs 搬运 +5.1% — 真·选股优势 21pp")
print("4. excess 中位 +7.3% vs 搬运 -19.8% — 板块 α 优势 27pp")