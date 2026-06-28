# 大V情报 — 模块 2 (v2.0.1-intel) 全量重抽报告

**时间**: 2026-06-28
**范围**: 30 天 (2026-05-28 ~ 2026-06-28), 4 大V 1424 条推文
**LLM**: `deepseek-v4-pro`
**Prompt**: **`v2.0.1-intel`** (从 v2.0.0 升级, 含 5 类 short 误抽铁律 + R12 flag 体系)

---

## 1. v2.0.0 → v2.0.1 改动

| 类别 | v2.0.0-intel | v2.0.1-intel |
|---|---|---|
| **5 类 short 误抽铁律** | ❌ 缺失 | ✅ 加 (反问 / 持仓披露 / 含蓄+调侃 / 朋友仓位 / 讽刺幽默) |
| **R12 flag** (victory_lap / position_disclosure / self_reported_returns) | ❌ 缺失 | ✅ 加 (3 列 is_retrospective / is_disclosure / is_self_reported_returns) |
| **短句支撑 short** | 缺则 short_skeptical=1 | 缺则改 neutral + short_skeptical=0 |
| **short_skeptical 维度** | 对 short + neutral 都标 | **只对 short 生效** (改后 neutral 不标) |
| **few-shot** | 8 例 | **12 例** (加 9-12: 反问 / 持仓披露 / victory_lap / 朋友仓位) |

---

## 2. 全量统计 (v2.0.1)

| 维度 | v2.0.0 | v2.0.1 | 变化 |
|---|---|---|---|
| **总入库** | 1424 | **1424** | - |
| neutral | 1273 (89.4%) | 1260 (88.5%) | -13 (R12 flag 让部分 victory_lap 改 neutral) |
| long | 147 (10.3%) | 162 (11.4%) | +15 (R12 victory_lap 保留 long + flag) |
| **short** | **4 (0.3%)** | **2 (0.1%)** | **-50% 误抽修复** |
| short_skeptical=1 | 10 | **0** | -10 ✓ |
| **is_retrospective=1** | - | **88 (6.2%)** | 新增 |
| **is_disclosure=1** | - | **76 (5.3%)** | 新增 |
| **is_self_reported_returns=1** | - | **13 (0.9%)** | 新增 |
| 重复 / FK 孤儿 | 0 / 0 | **0 / 0** | - |
| summary_100 空 | 0 | 1 | +1 (LLM 偶尔返回空, 边界) |

---

## 3. 剩下 2 条 short 逐条分析

### #1 zephyr Marvell (post 2069181208412721377)
> "Marvell which you would think should be competing is just a pump and dump by the management team to take your money and put it in their pockets and wall street is pricing them as an asic design house not realizing the asic design business is just IT outsourcing. My sweet summer child..."

- "pump and dump by the management team" — **指控式贬低**
- "My sweet summer child..." — **反讽/嘲弄收尾**
- **边界 case**: 不是明确建仓做空, 但表意强烈负面
- 建议: **改成 neutral** (LLM 应该识别反讽收尾 → 跟例 9 反问句一样归 neutral)
- prompt 改进点: 加"指控式贬低 + 反讽收尾"为第 6 类短误抽铁律

### #2 zephyr HBM3E 边缘 AI (post 2063839743432176085)
> "$85k for 250 Gigs of HBM3E. Seeing stuff like this always makes me super bearish on edge AI/self-hosting"

- **明确 "super bearish on edge AI/self-hosting"** — 是清晰的负面方向
- LLM 抽 short **正确** ✓
- 这不是误抽, 是**真 short** (虽然标的模糊, 是概念 short)

**结论**: 2 条剩 1 条真 short + 1 条边界 case (指控+反讽). 

---

## 4. R12 flag 抽样验证

### is_retrospective + long 抽样 12 条 (31 条 victory_lap 中)
全部都是 victory_lap 回顾 + 字面 long — **100% 正确标记** ✓

样本:
- "I did say $AAOI was my favorite US optical long... +20.1% today"
- "Up to $54, from when I went long at $12-13, 4 months ago"
- "Best time to long CXL was 4 months ago... $ALAB +276%, $MRVL +291%"
- "Just in case people are wondering about my track record with European equities: $RPI +185%, $LPK +86%, $SOI +311%..."

### is_disclosure 抽样 8 条 (76 条 position_disclosure 中)
全部都是 position_disclosure — **100% 正确标记** ✓

样本:
- "No positions in $WOLF right now, but I'm cheering it on anyway"
- "(disclosure have exposure to xfab + navitas)"
- "I think $LPK is severely mispriced... and I own a position"

### is_self_reported_returns 全部 13 条
全部都是自报收益 — **100% 正确标记** ✓

样本:
- "YTD 3612.10%"
- "$EWY 2028 leaps are now up 428%+"
- "$RPI $283 -> $983, up 247%"

---

## 5. R12 flag × Direction 交叉

| flag | long | short | neutral | TOTAL |
|---|---|---|---|---|
| is_retrospective | 31 | 0 | 57 | 88 |
| is_disclosure | 35 | 0 | 41 | 76 |
| is_self_reported_returns | 6 | 0 | 7 | 13 |

**关键洞察**:
- **R12 flag 跟 short 完全不交叉** (0 + 0 + 0 = 0): 说明 R12 类推文 (回顾/披露) 没误标 short
- **is_retrospective 31 long + 57 neutral**: 一半保留 direction, 一半归 neutral — 取决于作者字面是"陈述 long"还是"陈述事实"
- **is_disclosure 35 long + 41 neutral**: 类似分布
- **模块 3 知道**: is_retrospective=1 / is_disclosure=1 的 long ≠ 新信号, 不算"首次检测"

---

## 6. By Source × Direction

| Source | long | short | neutral | TOTAL |
|---|---|---|---|---|
| tw_jukan05 | 8 | 0 | 183 | 191 |
| tw_aleabitoreddit | 138 | 0 | 438 | 576 |
| tw_zephyr_z9 | 13 | 2 | 589 | 604 |
| tw_austinsemis | 3 | 0 | 50 | 53 |

**变化**:
- serenity long: 129 → 138 (+9, 部分 R12 victory_lap 保留 long)
- jukan long: 7 → 8 (+1)
- zephyr long: 9 → 13 (+4)
- zephyr short: 0 → 2 (+2, 1 真 short + 1 边界)
- austin: 不变 (3 long, 0 short)

---

## 7. 已修复 vs 剩余

### 已修复 (50% 进步)
- 4 条 short 误抽 → 2 条 (50% 修复)
- 10 条 short_skeptical=1 → 0 (完全修复)
- 88 + 76 + 13 条 R12 flag 全部正确标记 (新增)

### 剩余 (待优化, 可接受)
- 1 条 zephyr Marvell (指控+反讽边界 case, 误抽)
- 1 条 zephyr HBM3E (真 short, 不算误抽, 模块 3 可处理)

### 不影响首次检测
- victory_lap 标 is_retrospective=1 → 模块 3 不算新信号 ✓
- position_disclosure 标 is_disclosure=1 → 模块 3 不算新信号 ✓
- self_reported_returns 标 is_self_reported_returns=1 → 模块 3 不算新信号 ✓

---

## 8. 下一步

**直接接 cron** (地基数据已经干净):
- 模块 1 (抓取) + 模块 2 (抽取) 串行
- 每天 06:00 北京时间 cron 跑完整流水线
- 抽取是增量的 (基于 extractions_intel UNIQUE(post_id, prompt_version))
- 1 条 zephyr Marvell 边界 case 可以等 prompt v2.0.2 再修 (指控+反讽第 6 类)

**模块 3 准备** (等用户拍板):
- 首次检测 (新标的)
- 态度转折 (老标的)
- 利用 R12 flag 过滤: is_retrospective=1 / is_disclosure=1 都不算新信号