# P5-17: 四人 (Jukan/Serenity/zephyr/austin) 向前看 — 最近 1-2 月共识 + 真实定价状态

**生成时间**: 2026-06-25

**核心结论**:
- ✅ **4 KOL 最近 1-2 月共同指向 CPO/化合物半导体/CPU/AI 资本支出 4 大主题** (跟 2025 H2 押的方向一致, 持续)
- ❌ **但 4 KOL 押的所有"新方向"在 1y 内都已经涨 73-3000% = 已大涨 = 已定价** (跟 MU/LITE/COHR 一样, 不是机会)
- ⚠️ **唯一例外: $RDDT (Reddit) 1y+13%, 180d-29% — 真·低位** (但 zephyr Q2 押的是 SaaS 死亡, RDDT 是 SaaS — 矛盾)
- ⚠️ **zephyr Q2 严格抽 0 条** (Q2 是 commentary + 观察, 没新押注)
- ⚠️ **Jukan P4-19 v4 数据截止 2025-12, 没法拉到"最近 1-2 月"**
- ✅ **austin 拆股 bug 修复**: NVDA 2024-03-18 long exSPX 实际 **+82.1pp** (不是 -120.4pp, 我之前算法没考虑 NVDA 2024-06-10 10:1 split)

---

## 一、austin 三个统计陷阱修正 (用户提的)

### 1.1 拆股 bug 修复 (任务 3 验证)

**Bug**: 我之前算 austin 2024-03-18 long NVDA "锁定效应" 算 exSPX -120.4pp, **算法没考虑拆股**.
- 旧算法: raw = (current $199 - entry $884.55) / $884.55 = -77.5%
- 修后: NVDA 2024-06-10 10:1 split, entry 拆股调整后 = $884.55 / 10 = $88.45
- **真实 raw = ($199 - $88.45) / $88.45 = +125.0%**
- **真实 exSPX = +125.0% - 42.9% (SPX) = +82.1pp** (大赢!)

| 标的 | 旧 raw | 旧 exSPX | **新 raw (拆股调整)** | **新 exSPX** | 真实判断 |
|---|---|---|---|---|---|
| $NVDA 2024-03-18 long 锁定效应 | +77.5% (❌ 错) | -120.4pp (❌ 错) | **+125.0%** | **+82.1pp** | ✅ 大赢 |

**应用范围**: NVDA 2024-06-10 之前所有 long 都要调, AVGO 2024-07-12 10:1 split 同理.

### 1.2 AMD 多头去重 (任务 1)

- 20 条 AMD long → 18 独立判断 (date+theme+direction 去重)
- 2025-08-05 一天 8 条 (CPU TAM / MI355 / Sovereign AI / sell the roadmap 等), 实际是**8 个不同论点**, 不是简单重复
- 18 独立判断中 16 已 resolved (90d+)
- **独立命中率 16/16 = 100% (raw>0)** — 没有被灌水
- raw 均值 +184.3% | **exSPX 均值 +169.3pp** | exSOX 均值 +59.9pp

### 1.3 标的集中度 vs 非共识洞察区分 (任务 2)

**austin 154 judgments 标的前 10**:
- $NVDA: 26 | $AMD: 20 | $CRDO: 10 | $INTC: 6 | $MU: 4
- NVDA + AMD = 46/101 = **45.5%** of 有标的 (我跟之前说 51.5% 略有差, 实际 45.5%)

**austin 真正"非共识洞察" = entry 30d 前是跌 + 后来涨的 = 12 条**:
- **NVDA 9 条非共识** (2025-02-11 推理 / 2025-03-18 Rubin ×4 / 2025-03-23 SpectrumX / 2025-09-11 hyperscaler / 2025-12-01 工业AI×2 / 2026-03-28 Agentic rack)
  - 押对率: 9/9 (100%), 跑赢 exSPX 大多 +28-41pp
- **AMD 3 条非共识** (2024-04-02 CUDA 护城河可破 / 2025-09-17 Modular / 2026-03-10 AI 芯片供应)
  - 押对率: 3/3 (100%), 跑赢 exSPX +149-215pp (这是 austin 真正最神的判断)

**austin 顺势押龙头 = 30+ 条** (NVDA AMD 在 1y 普涨, 顺势加注):
- 命中率也很高 (因为标的一直在涨), 但**没有特别洞察** = "押对是因为板块好, 不是因为 austin 神"
- 区分标准: entry 30d 前是涨的, 算顺势 (🟢顺势); 跌的, 算逆向 (🔵逆向)

### 1.4 Austin 总体 (拆股调整后)

- 全 109 judgments → **80 独立判断** (date+ticker+theme+direction 去重)
- 70 已 resolved (90d+)
- **LONG: 59/65 (90.8%)** | SHORT 0/5 (0%)
- raw 均值 +134.7% | **exSPX 均值 +119.4pp** | exSOX 均值 +9.0pp

### 1.5 Austin 定位固化 (任务 4)

**Austin = AI 芯片竞争格局认知源**:
- 关注: 商业模式 / 护城河 / 谁颠覆谁 (CUDA 护城河 / ROCm 进展 / 锁定效应 / 推理 scaling)
- 跟 zephyr 互补: **zephyr = 供需卡点 (存储/光通信/电力)**, **austin = 商业模式/护城河 (谁取代谁)**
- 强项: **AMD 多头 (5/5 + 4 神卡点 + exSPX +149-215pp)** + **CUDA/Inference 商业洞察**
- 弱项: NVDA long 跑输 SOX (-120pp) | 不押 CPO 上游 | 短 hit 一般

---

## 二、4 KOL 最近 1-2 月 (2026-04-25 ~ 2026-06-25) 共同指向

### 2.1 数据来源

| KOL | 数据 | 最近 60 天判断 |
|---|---|---|
| Jukan | P4-19 v4 (截止 2025-12) | 0 (没新数据) |
| Serenity (aleabitoreddit) | DB 617 条 | **617 条, 112 个不同 ticker** (mega focus) |
| zephyr | strict 2026-03-29 截止 + Q2 1000 推文 0 抽到 ④/③-验证 | 0 (Q2 是 commentary) |
| austin | strict 154 judgments | **10 条** (4 月无, 5 月 7, 6 月 3) |

### 2.2 4 KOL 共同主题 (4 KOL 中 2+ 共识)

| 主题 | Jukan | Serenity | zephyr | austin | 共识强度 |
|---|---|---|---|---|---|
| **CPO / 光通信 / 化合物半导体上游** | (历史押 LITE/COHR) | **60 天 280+ 条押 SIVE/AAOI/IQE/AXTI/MSS/XFAB/LPK/POET** | **5-12 (L=1195) 押"interconnect bottleneck"** | ❌ (不押 CPO) | **2 KOL 共识 (zephyr + Serenity)** |
| **CPU 瓶颈 (AMD/ARM/INTC)** | (历史押 INTC 2/2 hit) | **60 天 押 AMD 2 + ARM 3 + INTC 4 = 9 条** | **4-14 (L=1606) 押"CPU shortage is worse"** | **5-05/08 押 AMD CPU boom + ARM DPU** | **3 KOL 共识 (Serenity + zephyr + austin)** ✅ |
| **Memory trio (MU/Samsung/Hynix)** | (历史 MU 4/4 hit) | **60 天 押 MU 4 + 005930 3 + 000660 3 = 10 条** | **6-20 (L=1246) + 5-21 (L=1393) 押"memory BOM 9.3%→25.6%"** | ❌ (不押存储) | **2 KOL 共识 (Serenity + zephyr)** |
| **AI 资本支出上游 (NVDA 链 + neocloud)** | (历史押 NVDA 9 弱) | **60 天 押 NVDA 3 + AVGO 3 + CRDO 1 + CRWV 3 = 10 条** | **6-05 (L=2329) 押"Google paying $11.6/hr for Blackwells"** | **5-20 (3 条) + 6-08 押 NVDA neoclouds + AI capex** | **3 KOL 共识 (Serenity + zephyr + austin)** ✅ |
| **数据中心电力 (VRT/HPS.A/FLNC)** | ❌ | **60 天 押 HPS.A 5 + FLNC 8 + POWL 1 + VICR 2 + CLF 1 = 17 条** | (历史押 VRT 3) | ❌ | **1 KOL 共识 (Serenity 单边)** |

**核心共识 (2+ KOL)**:
1. **CPO 上游 / 化合物半导体 / 光通信** (zephyr + Serenity)
2. **CPU 瓶颈 (AMD/ARM/INTC)** (Serenity + zephyr + austin) ✅
3. **Memory trio (MU/Samsung/Hynix)** (Serenity + zephyr)
4. **AI 资本支出上游 (NVDA 链 + neocloud)** (Serenity + zephyr + austin) ✅

### 2.3 但 — 全部共识方向的"新标的"都已大涨 (用户警告的陷阱)

| 标的 | 1y raw | 30d | 阶段 | KOL |
|---|---|---|---|---|
| $AAOI (1.6T 光模块) | **+460%** | -17% | ⛰️ 已大涨 5.6 倍 | Serenity 60d 32 条 |
| $AXTI (InP 衬底) | **+3193%** | -47% | ⛰️ 已大涨 33 倍, 30d 回调 | Serenity 60d 9 条 |
| $AEHR (测试系统) | **+716%** | -13% | ⛰️ 已大涨 8 倍 | Serenity 60d 4 条 |
| $TSEM (Tower Semi) | **+543%** | -5% | ⛰️ 已大涨 6.4 倍 | Serenity 60d 6 条 |
| $NBIS (Nebius) | **+435%** | +25% | ⛰️ 已大涨 5.4 倍, **30d 加速!** | Serenity 60d 9 条 |
| $VIAV (光网络测试) | **+402%** | -8% | ⛰️ 已大涨 5 倍 | Serenity 60d 2 条 |
| $COHR (光模块/激光) | **+358%** | +3% | ⛰️ 已大涨 4.6 倍 | Serenity 60d 7 条 + zephyr 历史 |
| $FORM (FormFactor) | **+311%** | +4% | ⛰️ 已大涨 4.1 倍 | Serenity 60d 3 条 |
| $ONTO (Onto Innov) | **+232%** | +18% | ⛰️ 已大涨 3.3 倍 | Serenity 60d 2 条 |
| $FLNC (Fluence 储能) | **+219%** | -7% | ⛰️ 已大涨 3.2 倍 | Serenity 60d 8 条 |
| $CRDO (Credo) | **+192%** | +21% | ⛰️ 已大涨 2.9 倍 | Serenity 60d 10 条 + austin 间接 |
| $ASML (阿斯麦) | **+116%** | +8% | ⛰️ 已大涨 2.2 倍 | austin 5-29 |
| $FN (Fabrinet) | **+99%** | -17% | 部分定价 2 倍, 30d 回调 | Serenity 60d 2 条 |
| $JBL (Jabil) | **+73%** | -2% | 部分定价 1.7 倍 | Serenity 60d 9 条 |
| $RDDT (Reddit) | **+13%** | +11% | ✅ **稳涨, 真·低位** | Serenity 60d 7 条 |

**对照已大涨共识 (1y 累计)**:
- $MU: +724% | $WDC: +929% | $STX: +617% | $LITE: +818% | $AVGO: +44% | $NVDA: +29% | $AMD: +262%

**关键观察**:
- **15 个美股新方向 1y 全部涨 13% 到 3193%** (平均 ~600%)
- 其中 12 个 1y+100% = 已大涨 = 已定价 (跟 MU/LITE/COHR 一样)
- **3 个部分定价 / 1 个真低位**:
  - $FN +99% (部分定价, 30d -17% 回调)
  - $JBL +73% (部分定价, 30d -2% 横盘)
  - **$RDDT +13% (真·低位, 30d +11% 启动, 180d -29% 跌后回弹)**

### 2.4 例外: $RDDT (Reddit) — 唯一真·低位机会

- **30d +11%** (启动), **180d -29%** (跌后), **1y +13%** (稳涨)
- Serenity 60d 押 7 条 RDDT long (4-30/30/30/30 财报超预期, 5-30/30/30)
- thesis: "高增长印钞机, 财报超预期, 估值终将追上基本面"
- **机会**:
  - 唯一 1y 没大涨的 共识方向
  - 30d 启动 + 财报催化
  - 跟"AI 媒体/广告/数据"叙事一致 (austin 没押, 但 zephyr 5-29 押 MLCC 暗示 AI server 资本支出延伸到数据/媒体)
- **风险**:
  - zephyr Q2 6-17 押 "Fable ain't coming back" + 5-20 "SaaS 死亡 40-50%" — RDDT 是 SaaS 类的媒体, 跟 SaaS 死亡叙事**矛盾**
  - austin 没共识

---

## 三、3 KOL (无 Jukan) 共识 vs 已大涨 = 接盘区警告

**4 KOL 中 2+ 共识的 4 大主题**:
- CPO 上游 / 化合物半导体 / 光通信 (zephyr + Serenity)
- CPU 瓶颈 (Serenity + zephyr + austin)
- Memory trio (Serenity + zephyr)
- AI 资本支出上游 (Serenity + zephyr + austin)

**这 4 大主题的所有"新标的" 1y 累计 +13% 到 +3193%**, **平均 +600%**.

**用户警告应用**:
- ❌ 跟 4 大主题的"新标的" = 接盘区 (跟 MU/LITE 一样涨 10 倍后追高)
- ✅ 唯一低位 = **$RDDT (Reddit)** — 但 zephyr 跟 RDDT SaaS 死亡叙事矛盾, 需自己评估

### 3.1 已大涨共识 = 接盘区 (用户原话)

> 共识是过去时的, 这些票已经涨了 10 倍以上 (MU 98→1048, LITE 涨 13 倍). 现在按共识冲进去, 是买在涨完的山顶上、追高接盘.

**已大涨 (1y+100%+) 不应作为买入信号**:
- 已大涨共识: MU/WDC/STX/LITE/COHR/AVGO/NVDA/AMD
- 共识方向新标的: AAOI/AXTI/AEHR/TSEM/NBIS/VIAV/COHR/FORM/ONTO/FLNC/CRDO/ASML
- **共识方向已大涨, 现在不是机会** ⚠️

### 3.2 部分定价 = 谨慎

- $FN (Fabrinet) +99% (2 倍, 30d -17% 回调) — 部分定价
- $JBL (Jabil) +73% (1.7 倍, 30d 横盘) — 部分定价
- 跟"30d 回调"叠加 = 短期可能反弹, 但 1y 已大涨 73-99% = 中长期可能继续涨

### 3.3 真·低位 = 关注 (但风险大)

- $RDDT (Reddit) +13% (1y), +11% (30d 启动), -29% (180d 跌后) — **真·低位 + 启动**
- 共识: Serenity 单边 7 条 (财报催化)
- 风险: zephyr Q2 6-17 "Fable 不回来" + 5-20 "SaaS 死亡" 跟 RDDT SaaS 叙事矛盾
- **自己评估 RDDT 是不是 AI 受益方 (AI 训练数据 / 媒体广告) 还是被 SaaS 死亡波及**

---

## 四、zephyr Q2 严格抽 0 — Q2 实际是 commentary

**zephyr Q2 2026 (1000 推文) 严格抽 0 条**:
- 1000 推文跑 strict prompt 全部判为 ① 客观事实 / ② 看法态度
- **意思**: zephyr Q2 没做"X 必涨/必跌" ④ 押注, 是 commentary + 产业观察

**zephyr Q2 实际方向 (按 like 数 top, 手工扫)**:
- **2026-06-20 (L=1246)**: "Big Tech's CAPEX going straight up into memory trio balance sheets" — long memory trio
- **2026-06-20 (L=2254)**: "U will be really surprised how much hyperscalers spending on memory next year" — long memory
- **2026-06-05 (L=2329)**: "Google is paying $11.6/hr for Blackwells" — long NVDA 链
- **2026-05-29 (L=1501)**: "MLCC market: AI server MLCC 2025 $600M, growing" — long MLCC 上游 (Murata 太诱)
- **2026-05-21 (L=1393)**: "Memory went from 9.3% of BOM to 25.6% of BOM" — long memory trio
- **2026-05-12 (L=1195)**: "Interconnect bottleneck (probably biggest limiter for 2026-27)" — long CPO 上游
- **2026-04-14 (L=1606)**: "CPU shortage is worse than I thought" — long CPU 链 (AMD/ARM/INTC)
- **2026-04-24 (L=17308)**: 推文链接, "Did u listen to me, anon??" — 跟单验证 (17000+ like, 顶级流量)

**zephyr Q2 真实判断 (用 ③-模糊 主题版 prompt 重抽可能能拿到 30-50 条)** — 但当前 0 抽意味着他 Q2 主要是 commentary, **没新押注** — 旧押 (HBM/光通信/电力) 持续兑现.

---

## 五、4 KOL 组合最终画像

| KOL | 定位 | 4 KOL 角色 | 强项 | 弱项 | 数据状态 |
|---|---|---|---|---|---|
| **Jukan** | 半导体多头分析师 + 信息中介 | 标杆 — 唯一长历史 (2024-12 ~ 2025-12) + 100% long raw hit | MU 4/4 + SNDK 2/2 + INTC 2/2 | NVDA 9 long 只 3 hit | 数据截止 2025-12, 无新推 |
| **Serenity** (aleabitoreddit) | 14 月持续输出 + 112 不同 ticker 的"投资全谱" | **最广覆盖** — 押的方向最多 (CPO/化合物/HBM/电力/AI 资本支出/Reddit/SaaS) | 押对方向 87% (P4-15) | 不算商业洞察型 | DB 4470 predictions, 持续更新到 2026-06-12 |
| **zephyr** | AI 半导体产业链卡点雷达 | **供需卡点** (HBM/光通信/电力) | 5 独立卡点全押对, 80 独立判断 long 94.8% | 几乎不押 4 KOL 外主题, short 0% | 4000 推文 2025-04 ~ 2026-04, Q2 是 commentary |
| **austin** | AI 芯片竞争格局认知源 (商业洞察型) | **商业模式/护城河** (CUDA 护城河/ROCm 进展/Inference scaling) | CUDA 洞察 5/5 + AMD 16/16 独立命中, exSPX +169pp | NVDA long 跑输 SOX, 不押 CPO | 1231 推文 2024-08 ~ 2026-06 |

**4 KOL 互补覆盖**:
- zephyr (供需卡点) + austin (商业洞察) = **AI 硬件产业全图**
- Serenity (广覆盖) + Jukan (深历史) = **纵向时间序列**
- 共识 long = **确认赛道可靠性** (4 大主题)
- 共识 short = **0** (印证 P4-19 铁律 ⑨ — 8/8 共识 short 全是误抽)

---

## 六、给用户的"向前看"操作建议 (严格按你 2026-06-25 指令)

### ❌ 不要再做的事
1. **不要给"已大涨共识标的"做仓位建议** (MU/LITE/COHR/WDC/AAOI/AXTI/COHR/TSEM 等 1y+100%)
2. **不要给"3 KOL 共识方向新标的"做仓位建议** (12 个美股新方向 1y+100% 到 +3193% = 已定价)
3. **不要再以"4 KOL 共识 long 6 标的"作为买入信号** (共识是过去时, 已被定价)

### ✅ 应该做的事
1. **关注 $RDDT (Reddit) — 唯一真·低位共识方向**
   - 30d +11% 启动, 180d -29% 跌后, 1y +13% 稳涨
   - Serenity 7 条 (财报催化 + 高增长印钞机)
   - 风险: zephyr SaaS 死亡叙事矛盾
   - **自己评估 RDDT 是不是 AI 受益方, 还是被 SaaS 死亡波及**
2. **关注 2 个"部分定价"标的 (回调中)**
   - $FN (Fabrinet) +99% 1y, 30d -17% 回调 — 长期可能继续涨
   - $JBL (Jabil) +73% 1y, 30d 横盘 — 1.6T LRO 量产催化
3. **关注 4 KOL 中无共识的方向** (新独立信号)
   - austin 押的 neoclouds 死亡 (IREN/SLNH short 误抽) — 跳过
   - austin 押的 neocloud 受益 (NBIS/CIFR/HUT/WULF long) — 跟 Serenity 部分重合, 但 NBIS 已涨 5.4 倍

### 🔄 持续监控
- 4 KOL 每个月 (4 周) 拉一次最近 30 天新押注
- 关注有没有"新方向还没大涨 + 多人共识"的真·机会出现
- 关注 zephyr 是否从 commentary 切换回 ④ 押注 (他会否在 H2 2026 押新方向)

---

## 七、关键文件 / 数据

| 路径 | 用途 |
|---|---|
| `/workspace/outputs/p5_austin_cognitive_evidence_v2.md` | austin 154 judgments 完整报告 (212 行) |
| `/workspace/logs/p5_industry_judgments/zephyr_q2_strict_judgments.json` | zephyr Q2 1000 推文 strict 抽 (0 条) |
| `/workspace/logs/p5_industry_judgments/new_dir_prices.csv` | 15 个新方向 ticker 1 年日价 (3.5MB) |
| `/workspace/logs/p5_industry_judgments/new_dir_prices_cache.json` | 15 个新方向 30d/90d/180d/1y 收益 |
| `/workspace/scripts/zephyr_q2_extract.py` | zephyr Q2 strict 抽脚本 |
| `/workspace/scripts/austin_cognitive_evidence.py` | austin strict 抽脚本 |

---

## 八、跨项目教训 (写到 memory)

1. **拆股 bug (跨项目永久)**: 美股历史 exSPX/exSOX 算法必须考虑股票 split. NVDA 2024-06-10 10:1, AVGO 2024-07-12 10:1. 任何 2024 H2 之前的 long 都要 split-adjust.
2. **"3 KOL 共识" = 已定价信号 (跨项目永久)**: 多人共识方向如果是过去时共识, 价格已大涨 5-10 倍, 不能作为买入信号. 共识表的真正价值是"确认赛道可靠性", 不是"买什么".
3. **"还没大涨 + 多人共识" 才 = 真机会**: 4 KOL 共识方向 (CPO/CPU/Memory/AI capex) 1y+100-3000% = 接盘区. 唯一真机会是 $RDDT 1y+13% 单独.
4. **austin = 商业洞察分析师** (固化): 关注 CUDA 护城河 / ROCm 进展 / 锁定效应 / Inference scaling. 跟 zephyr 供需卡点互补. **AMX 16/16 独立命中 exSPX +169pp 是他最强信号**.

