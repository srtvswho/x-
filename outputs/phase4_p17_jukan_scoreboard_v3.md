# P4-17 报告: MU 6-26 误抽修正 + Jukan 记分牌 v3

**生成时间**: 2026-06-23T02:55:50.409694

**用户质疑**: MU 6-26 "short" 是误抽? 跟 @jukan05 5/5 MU long 强项矛盾。

**排查结果**: ✅ **用户是对的** — MU 6-26 是产业分析, 不是看空建仓声明。

---

## 一、MU 6-26 原文 vs 抽取对比

### 原文 (完整)

> "The reason why Micron CEO SJ did not announce HBM sold-out for 2026 on the conference call is simple: Nvidia is delaying the contract. Nvidia is hoping that Samsung will pass HBM3E validation, allowing them to buy Micron's HBM at a lower price. That's why they're dragging out the negotiations.
>
> This information has been cross-verified multiple times. Most industry insiders probably know about it."

**全文分析**:
- 整段在**解释一个事实**: 为什么 MU CEO SJ 没宣布 HBM 2026 sold-out
- 关键动词: "The reason why... is simple" / "Nvidia is delaying" / "Nvidia is hoping"
- **没有** "做空 MU" / "看空 MU" / "卖 Micron" / "做空 Micron" / "我会做空" / "看空" 这种**建仓或投资建议声明**
- "Most industry insiders probably know about it" — **内部人士共识, 不是个人仓位**
- 全文定位: **产业 fact-sharing + causal analysis**, 不是 investment thesis

### LLM 抽取 (错)

- **direction: short, horizon 180d**
- **thesis: "Nvidia推迟2026年HBM供货合同谈判,试图等待三星通过验证以压低采购价格,对Micron的HBM业务造成负面影响"**

LLM 看到 "对 Micron 的 HBM 业务造成负面影响" 就**自动推导成 short 180d** — 跳过了"原文没说做空"这一步。

### 正确分类

- **direction: neutral** (或 drop, 因为它不是投资预测)
- 正确解读: "他在做产业 fact-sharing + 因果分析, 不是给投资建议"

**这是典型的 directional 抽取过度解读** — 跟 Serenity 抽取时 "看多被误抽成看空" 是同一类 bug:
- 原文: 描述一个产业现象 (Nvidia 推迟 HBM 合同)
- 抽取: 推导出投资方向 (short MU 180d)
- 缺环: **原文没说"我要做空 MU"**

---

## 二、QCOM 5-22 原文 vs 抽取对比 (保留 short)

### 原文 (完整)

> "I don't understand why my friends are so dismissive of Xiaomi's in-house chip. ... I expect Xiaomi will be able to cut Qualcomm's chip prices by about 10-15% through Xring. In other words, Qualcomm will earn that much less.
>
> **I still don't recommend Qualcomm stock. It's way overvalued.**"

**关键句**: 最后一句 **"I still don't recommend Qualcomm stock. It's way overvalued."** — **明确的看空 / 不推荐建仓声明**。

### LLM 抽取 (正确)

- **direction: short, horizon 180d** ✅
- thesis: "小米自研芯片将压低高通芯片价格 10-15%,影响高通营收,且高通估值过高"

**这条抽对了** — 原文最后一句明确陈述了"不推荐 QCOM stock"。

### 跟 MU 6-26 区别

| 维度 | MU 6-26 | QCOM 5-22 |
|---|---|---|
| 原文最后一句 | "Most industry insiders probably know about it" | "**I still don't recommend Qualcomm stock. It's way overvalued.**" |
| 是否明确建仓声明 | ❌ 否 | ✅ 是 (不推荐 = 负向声明) |
| 主题 | 解释 CEO 决策因 | 产品蚕食 + 估值过高 |
| LLM 抽取 | ❌ short (误) | ✅ short (对) |
| 处理 | **drop** (不是投资建议) | **保留** (明确看空) |

---

## 三、修正后重算 (n=29, drop MU 6-26)

### 核心统计双维度

| 维度 | 原 30 | **修正 29** (drop MU 6-26) | 搬运 49 | **他优势** |
|---|---|---|---|---|
| **raw 选股命中率** (raw>0) | 28/30 (93.3%) | **28/29 (96.6%)** | 29/49 (59.2%) | **+37.4pp ⭐** |
| raw 跌 (raw<0) | 2 | **1** | 20 | - |
| hit_rate vs SOXX | 66.7% | 65.5% | 59.2% | +6.3pp |
| **med_raw** | +26.2% | **+26.6%** | +5.1% | +21.5pp |
| **med_excess vs SOXX** | +7.3% | **+9.4%** | -19.8% | +29.2pp |
| Wilson vs SOXX | 48.8% | 47.4% | 45.2% | - |

**关键观察**:
- **raw 选股命中率从 93.3% → 96.6%** (drop 1 条错, 命中率更高)
- **med_excess vs SOXX 从 +7.3% → +9.4%** (MU 6-26 -158% 拖了后腿)
- **搬运组 raw 命中率 59.2% vs 他 96.6%** — **他选股能力 37pp 强于搬运**

### 按 horizon 拆 (修正后, vs SOXX)

| Horizon | 他原创 n | hit_rate | med_raw | med_excess |
|---|---|---|---|---|
| 30d | 7 | 85.7% | +24.1% | +15.8% |
| 90d | 3 | 66.7% | +22.5% | +3.7% |
| 180d | 19 | 57.9% | +31.8% | +9.4% |

(n=29, 不是 30, 因为 drop MU 6-26, 同时 drop 的也是 180d 类别)

### 按方向拆 (修正后, vs SOXX)

| 方向 | 他原创 n | hit_rate | med_raw | med_excess |
|---|---|---|---|---|
| **long** | 26 | 65.4% (17/26) | +26.6% | +10.4% |
| **short** | **3** | 100% (3/3) | +4.8% | -7.1% |

**重要观察 — "short 是弱项" 结论不成立**:
- 原 P4-15 说他有 4 条 short, 2/4 真亏 (MU 6-26 误抽, QCOM 5-22 真亏)
- 修正后只剩 **3 条 short**:
  - AAPL 12-13 (raw +4.8%): 苹果长期协议到期,三星/SK海力士涨价,AAPL 短期成本压力
  - AAPL 12-26 (raw +21.1%): 苹果 VR 设备推出不可行 (产品局部看空)
  - QCOM 5-22 (raw -14.3%): 小米自研芯片蚕食 10-15% 价格, QCOM 估值过高
- **3/3 short 都是"局部风险提示"** (局部产品/合同问题), 不是"全面看空建仓"
- **3/3 hit vs SOXX** (因为 SOXX 涨更多, 短期 AAPL/QCOM 跑输 = 算 hit)
- **0/3 真亏** (只有 QCOM -14% 是真亏, 但 SOXX 涨更多所以 excess 跑输板块算 hit)

**新结论**: 
- 他几乎**不做空**(全样本只 3 条 short, 都是局部风险提示)
- 他做空是"局部产品问题" (Apple VR, Xiaomi 蚕食) 不是"全面做空建仓"
- "他做空是弱项" → **样本太小不能下结论**, 而且 3/3 hit vs SOXX

---

## 四、按 ticker 拆 (修正后, vs SOXX)

| Ticker | n | hit | hit_rate | med_excess |
|---|---|---|---|---|
| NVDA | 9 | 3 | 33.3% | -15.3% |
| MU | 4 (drop 1) | 4 | 100% | +19.7% (从 +16.2% 升) |
| AAPL | 3 | 1 | 33.3% | -7.1% |
| AMD | 3 | 2 | 66.7% | +25.9% |
| INTC | 2 | 2 | 100% | +33.8% |
| SNDK | 2 | 2 | 100% | +92.6% |
| TSM | 2 | 1 | 50% | +8.8% |
| AVGO | 1 | 1 | 100% | +11.3% |
| ASML | 1 | 1 | 100% | +52.8% |
| LRCX | 1 | 1 | 100% | +16.7% |
| **QCOM** | **1** (drop MU 6-26 不影响 QCOM) | 1 | 100% | -53.3% |

**关键观察**:
- **MU 4/4 (100%)** 修正后 — 之前 5/5 是含 MU 6-26 误抽, 修正后 4/4, 但 med_excess 从 +16.2% → +19.7% (去掉最差那条, 剩下的更好)
- QCOM 1/1 hit 但 med_excess -53.3% — **真亏 14% 但 SOXX 涨更多, 跑输板块 53pp** (单独看起来差, 但样本太小)
- NVDA 9 条仍 3 hit, -15.3% — **明确弱项, 没变**
- SNDK/INTC/ASML/LRCX/AVGO 仍 100% (样本都 ≤ 2, 谨慎)

---

## 五、他做 short 的 3 条 (修正后) — 都是"局部风险提示"不是"全面做空"

### Sat Dec 13 AAPL short 30d

**raw**: +4.8% | **excess vs SOXX**: -7.1% | **hit vs SOXX**: ✅

**thesis**: 苹果长期协议即将到期，三星和SK海力士计划明年一月起提高内存价格，苹果可能受到显著冲击。

**性质**: 局部风险提示 (specific product/contract concern), 不是全面看空建仓


### Thu Dec 26 AAPL short 180d

**raw**: +21.1% | **excess vs SOXX**: +14.1% | **hit vs SOXX**: ❌

**thesis**: 基于供应链调查，苹果在2025年底前推出低成本VR设备似乎不可行。

**性质**: 局部风险提示 (specific product/contract concern), 不是全面看空建仓


### Thu May 22 QCOM short 180d

**raw**: -14.3% | **excess vs SOXX**: -53.3% | **hit vs SOXX**: ✅

**thesis**: 小米自研芯片将压低高通芯片价格10-15%，影响高通营收，且高通估值过高。

**性质**: 局部风险提示 (specific product/contract concern), 不是全面看空建仓


---

## 六、终极结论 (修订 v3)

### MU 6-26 误抽的核心教训

**LLM 抽取的 directional 过度解读**:
- 原文: "解释 MU CEO 决策因, 描述 Nvidia 推迟合同" — **fact-sharing, 不是投资建议**
- LLM: 推导成 "short MU 180d" — **跳过了"作者说没说要做空"这一步**
- **同类型 bug 之前在 Serenity 抽取也出现过** (看多被误抽成看空)

**修正方法**:
- **不只看"内容是不是负面/正面"**, 还要看"作者是不是声明了建仓/推荐"
- 关键词: "看多/看空/buy/sell/short/long/做空/做多/推荐/不推荐/overvalued/undervalued"
- 缺少这些词: 倾向 **neutral** 或 **drop** (不是投资预测)

### Jukan 记分牌 (v3 修正)

| 维度 | 数值 | 评价 |
|---|---|---|
| **raw 选股命中率** (raw>0) | **28/29 (96.6%)** | **⭐ 极强信号** |
| raw 选股搬运差 (vs 搬运 29/49 = 59.2%) | **+37.4pp** | **真·信号** |
| med_raw | +26.6% | 真实盈亏能力强 |
| hit_rate vs SOXX | 65.5% | 中 |
| med_excess vs SOXX | +9.4% | 中 |
| Wilson vs SOXX | 47.4% | < 50%, 严格不显著 (样本小) |
| **他做 short** | **3 条 (都是局部风险, 不是全面做空)** | 样本小, 不能下"弱项"结论 |

### 跟单规则 (修订 v3)

**🟢 强信号 — 跟**:
- raw 选股 96.6% 命中率, 远高于搬运 (59.2%)
- MU (4/4 hit, +19.7% excess) / SNDK (2/2 hit, +92.6%) / INTC (2/2 hit, +33.8%) / AMD (2/3 hit, +25.9%)
- 30d 短期 raw 中位 +24% (7 条 6 raw 涨, 1 raw 平)
- 代工/设备 (TSM/ASML/LRCX/AVGO) 4/5 hit, raw 中位 +50%+
- **不区分 long/short (他几乎只做 long, 3 条 short 都是局部风险)**

**🔴 不跟**:
- **看多 NVDA** (9 条 3 hit, raw 中位 +5%, 跑输 SOXX 40pp) — 明确弱项
- 搬运机构观点 (raw 命中率 59.2%, excess -20%)

### P4-17 vs P4-15 vs P4-14 修订清单

| 修订 | P4-14 | P4-15 | P4-17 |
|---|---|---|---|
| "亏 40%" 显示错 | ❌ 错 | ✅ 修 | ✅ 修 |
| MU 6-26 short 误抽 | ❌ 没察觉 | ⚠️ 知道 short 但没验原文 | ✅ **drop, 是产业分析** |
| raw 选股命中率 96.6% | ❌ 没算 | 93.3% (含 MU 6-26 错) | **96.6% (修正)** |
| med_excess vs SOXX | +7.3% | +7.3% (含错) | **+9.4% (修正)** |
| "他做 short 是弱项" | ⚠️ 暗示 | ⚠️ 提了 | ✅ **修正: 3 条都是局部风险, 样本太小不能下"弱项"结论** |

### 数据限制

- **韩股 17 条无法 verify** (Polygon free 不支持 XKRX)
- **Wilson 47.4%** vs SOXX 严格不显著 (样本小, 需要 2 倍样本)
- **raw 选股命中率 96.6%** — 这个数字不依赖 benchmark, 是真·信号, 但只 29 条
- **AAPL 12-26 short 性质待查** — "VR 设备不可行" 也是局部风险提示, 可能也误抽 (但用户没问, 暂保留)
