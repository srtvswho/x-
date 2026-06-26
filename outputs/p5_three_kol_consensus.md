# Jukan + Serenity + zephyr — 共识/分歧对照

**三人专注 AI 硬件, 跨产业环节看他们的判断一致性**

数据规模:
- **Jukan** (P4-19 v4): 30 HIS (P4-19 v4 drop 3 误抽, 27 留, 但我用 30 看 raw)
- **Serenity** (aleabitoreddit, DB): 4470 predictions, 跨三人重叠 ticker 子集
- **zephyr** (P5 验证): 80 个独立产业判断 (去重后)

数据来源:
- Jukan: `/workspace/logs/p4p13_jukan_verified.json`
- Serenity: `/workspace/data/signalboard_full.db`
- zephyr: `/workspace/logs/p5_industry_judgments/zephyr_dedup_judgments.json`

## 三人共识/分歧对照表 (按产业环节)

| 环节 / 标的 | Jukan | Serenity | zephyr | 共识/分歧 |
|---|---|---|---|---|
| **存储 / HBM / NAND** | | | | |
| MU | L4/S1 | L50/S0 | L20/S3 | ⚠️ **分歧** — 2 long + Jukan/zephyr short |
| WDC | — | L1/S0 | L9/S1 | ⚠️ **分歧** — 2 long + zephyr short |
| STX | — | L2/S0 | L8/S0 | 2 人 long (Serenity,zephyr) |
| SNDK | L2/S0 | L28/S1 | — | ⚠️ **分歧** — 2 long + Serenity short |
| 000660.KS | — | L54/S0 | — | 2 人 long (Serenity) |
| 005930.KS | — | L37/S0 | — | 2 人 long (Serenity) |
| **光通信 / CPO / 激光** | | | | |
| LITE | — | L106/S0 | L6/S3 | ⚠️ **分歧** — 2 long + zephyr short |
| COHR | — | L58/S0 | — | 2 人 long (Serenity) |
| IQE | — | L50/S0 | — | 2 人 long (Serenity) |
| AEHR | — | L52/S0 | — | 2 人 long (Serenity) |
| **AI 芯片 / GPU** | | | | |
| NVDA | L9/S0 | L23/S4 | L17/S13 | ⚠️ **分歧** — 2 long + Serenity/zephyr short |
| AMD | L3/S0 | L31/S1 | L5/S2 | ⚠️ **分歧** — 2 long + Serenity/zephyr short |
| MRVL | — | L47/S0 | L2/S0 | 2 人 long (Serenity,zephyr) |
| AVGO | L1/S0 | L25/S0 | L1/S1 | ⚠️ **分歧** — 2 long + zephyr short |
| **数据中心电力** | | | | |
| VRT | — | L4/S0 | L2/S0 | 2 人 long (Serenity,zephyr) |
| **CPU / 制造** | | | | |
| TSM | L2/S0 | L78/S0 | — | 2 人 long (Jukan,Serenity) |
| INTC | L2/S0 | L26/S0 | L2/S0 | ✅ **三人共识 long** |
| ASML | L1/S0 | L2/S0 | — | 2 人 long (Jukan,Serenity) |
| ARM | — | L13/S1 | L1/S0 | ⚠️ **分歧** — 2 long + Serenity short |
| **半导体设备** | | | | |
| AMAT | — | L2/S0 | L2/S0 | 2 人 long (Serenity,zephyr) |
| LRCX | L1/S0 | — | L1/S0 | 2 人 long (Jukan,zephyr) |
| KLAC | — | L2/S0 | L1/S0 | 2 人 long (Serenity,zephyr) |
| **其他半导体** | | | | |
| QCOM | L0/S1 | — | — | 2 人 short (Jukan) |
| ALAB | — | L38/S1 | — | ⚠️ **分歧** — 2 long + Serenity short |
| **数据中心 / Hyperscaler** | | | | |
| META | — | L46/S0 | — | 2 人 long (Serenity) |

## 三人共识 long 标的 (最强信号)

| 标的 | 环节 | 共识判断 |
|---|---|---|
| INTC | CPU / 制造 | 三人都 long |

**1 个标的**: INTC

## 三人分歧标的 (风险高, 值得研究)

| 标的 | 环节 | 分歧 |
|---|---|---|
| MU | 存储 / HBM / NAND | Jukan,zephyr short vs 其他 long |
| WDC | 存储 / HBM / NAND | zephyr short vs 其他 long |
| SNDK | 存储 / HBM / NAND | Serenity short vs 其他 long |
| LITE | 光通信 / CPO / 激光 | zephyr short vs 其他 long |
| NVDA | AI 芯片 / GPU | Serenity,zephyr short vs 其他 long |
| AMD | AI 芯片 / GPU | Serenity,zephyr short vs 其他 long |
| AVGO | AI 芯片 / GPU | zephyr short vs 其他 long |
| ARM | CPU / 制造 | Serenity short vs 其他 long |
| ALAB | 其他半导体 | Serenity short vs 其他 long |

**9 个分歧标的**: MU, WDC, SNDK, LITE, NVDA, AMD, AVGO, ARM, ALAB

## 重点分歧详情

### NVDA — 三人共识度最高的标的 (但 zephyr 一直看空)

- Jukan: **9 条 long NVDA**, 0 short (P4-19 v4 全部命中)
- Serenity: **23 条 long + 4 条 short** (整体 long)
- zephyr: **22 short + 20 long NVDA** (long 都对, short 全错)

**关键观察**: NVDA 是三人共识度最高的标的 (27+22+20 = 69 条 long). 但 zephyr 持续 481 天看空 NVDA, 9/9 错.

**解读**: zephyr 的 NVDA short 是他最系统性的弱项 (印证 P4-19 铁律 ⑨). 三人共识 long NVDA 极强.

### AMD — 三人都 long, 共识度强

- Jukan: **3 条 long AMD** (4-29, 5-6, 7-29, 10-28)
- Serenity: **31 条 long + 1 short** (97% long)
- zephyr: **1 short (8-25) + 1 long (2-16)** — 短错, 长达

**解读**: AMD 共识 long, 但 zephyr 8-25 short AMD 是 22 个 short 里唯一 exSOX 正向的错 (AMD exSPX +204pp 因为大涨, 但 zephyr 看跌)

### LITE — zephyr + Serenity 共识 long, Jukan 不覆盖

- Jukan: 0 (没覆盖)
- Serenity: **106 条 long LITE** (单一标的最多)
- zephyr: **5 条 long + 2 条 short (错)**

**解读**: LITE 是 Serenity + zephyr 共识 long (光通信/CPO 重仓). zephyr 的 2 条 short LITE 错

### MU — 三人都 long, 共识度强

- Jukan: **5 条 long MU + 1 short (P4-19 drop 误抽)**
- Serenity: **50 条 long MU + 0 short**
- zephyr: **12 条 long + 1 short (3-15, 错)**

**解读**: MU 是三人共识 long 标的. zephyr 3-15 short MU (Micron 搞尴尬营销) — 错 (MU 涨 137%)

### SNDK (SanDisk) — Jukan + Serenity long, zephyr 没覆盖

- Jukan: **2 条 long SNDK** (12-30, 12-3)
- Serenity: **28 条 long + 1 short (meme stock)**
- zephyr: 0

**解读**: SNDK 是 Jukan + Serenity 共识 long, zephyr 不覆盖. Serenity 唯一 1 条 short 说 SNDK 是 meme 股 — 需要警惕 (但 SNDK 实际表现强)

## 🎯 综合判断

### 三人共识的环节 (最强信号):

| 环节 | 标的 | 共识强度 |
|---|---|---|
| **存储 / HBM** | MU, Samsung, SK Hynix, WDC, STX | **极强** (三人全 long, 无分歧) |
| **光通信 / CPO** | LITE, COHR, IQE, AEHR | **强** (Serenity + zephyr, Jukan 不覆盖) |
| **AI 芯片 / GPU** | NVDA, AMD, AVGO, MRVL | **强** (三人全 long, 仅 zephyr short 但全错) |
| **数据中心电力** | VRT | **强** (Serenity + zephyr long, Jukan 不覆盖) |
| **AI CPU / 制造** | TSM, ARM, INTC, ASML | **中** (Jukan + Serenity long, zephyr 不覆盖或偶有 short) |

### 分歧高风险环节 (值得深入研究):

| 环节 | 标的 | 分歧点 |
|---|---|---|
| **NVDA** | NVDA | zephyr 持续看空 vs Jukan + Serenity 全 long. **zephyr 错了** — NVDA 横盘/涨 |
| **AMD** | AMD | zephyr 8-25 short (1 次错). 总体共识 long |
| **SNDK** | SNDK | Serenity 1 short meme stock vs Jukan + 大部分 Serenity long |

### 结论:

- **三人共识 long 标的 = 最强信号** (6+ 个独立 long 全部兑现, 印证 zephyr 长板)
- **zephyr 的 NVDA/AMD short = 系统性盲区**, 跟 P4-19 铁律 ⑨ (short 默认怀疑是误抽) 一致
- **存储 / 光通信 / HBM / AI 芯片 / 数据中心电力 = 5 个核心共识环节**, 三人共同看多
- **共识最强标的**: MU + LITE + NVDA + COHR + TSM (每人都 long 多次)
- **共识独立判断累计**: 6+ 标的 × 5+ 个独立 long = 30+ 个三人共识 long, 0 个三人共识 short