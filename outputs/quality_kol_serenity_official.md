# KOL 评估报告 — @aleabitoreddit

**生成时间**: 2026-06-16T12:42:33.695462Z
**数据库**: /workspace/data/signalboard_full.db
**置信度等级**: **B** — tier_A 3m hit 65.4% ≥ 60% (+3); tier_A 3m median excess +12.9% ≥ 10 (+2); tier_A 6m hit 85.5% ≥ 60% (+2); tier_A 3m outlier 警告 RED (-2); tier_A 1m outlier 警告 RED (-1); 追高警告 RED (-1)

## 1. Tier 分层

| Tier | n | 占比 |
|---|---|---|
| tier_A 核心论证 | 348 | 8.7% |
| tier_B 清单扫货 | 1225 | 30.8% |
| tier_C 顺带提及 | 2410 | 60.5% |
| **总** | 3983 | 100% |

## 2. Tier × Horizon 记分牌

### tier_A 核心论证 (n_total=348)

| horizon | n_resolved | hit_rate | wilson_low | median_excess | avg_excess |
|---|---|---|---|---|---|
| 1w | 315 | 57.1% | 51.6% | +3.82% | +7.42% |
| 1m | 275 | 54.2% | 48.3% | +3.67% | +29.92% |
| 3m | 191 | 65.4% | 58.5% | +12.90% | +38.03% |
| 6m | 76 | 85.5% | 75.9% | +37.67% | +60.28% |

### tier_B 清单扫货 (n_total=1225)

| horizon | n_resolved | hit_rate | wilson_low | median_excess | avg_excess |
|---|---|---|---|---|---|
| 1w | 1169 | 48.3% | 45.5% | -0.28% | +0.16% |
| 1m | 1169 | 54.7% | 51.9% | +1.80% | +5.31% |
| 3m | 982 | 46.5% | 43.4% | -2.55% | +5.69% |
| 6m | 539 | 51.4% | 47.2% | +2.34% | +9.33% |

### tier_C 顺带提及 (n_total=2410)

| horizon | n_resolved | hit_rate | wilson_low | median_excess | avg_excess |
|---|---|---|---|---|---|
| 1w | 2175 | 59.1% | 57.0% | +2.48% | +5.42% |
| 1m | 2054 | 58.9% | 56.8% | +4.86% | +20.92% |
| 3m | 1477 | 55.5% | 53.0% | +4.69% | +25.66% |
| 6m | 727 | 59.3% | 55.7% | +9.45% | +15.81% |

## 3. tier_A outlier 自动体检

### 1w horizon

- 警告等级: **RED** — top1 (SIVE) 占 26.4% > 25.0%; top5 占 58.9% > 50.0%; outlier ticker: TSEM (median excess 3x overall)
- n: 348
- top1 集中度: 26.4% (SIVE)
- top5 集中度: 58.9%
- hit_rate (with outlier): 57.1%
- hit_rate (去 top1): 51.1%
- hit_rate (去 top2): 47.3%
- hit_rate (去 top3): 46.9%
- outlier ticker (median 3x+): TSEM

### 1m horizon

- 警告等级: **RED** — top1 (SIVE) 占 26.4% > 25.0%; top5 占 58.9% > 50.0%; outlier ticker: SIVE,RKLB,AEHR (median excess 3x overall)
- n: 348
- top1 集中度: 26.4% (SIVE)
- top5 集中度: 58.9%
- hit_rate (with outlier): 54.2%
- hit_rate (去 top1): 42.7%
- hit_rate (去 top2): 47.0%
- hit_rate (去 top3): 46.9%
- outlier ticker (median 3x+): SIVE, RKLB, AEHR, UAVS, TSEM, SIVEF

### 3m horizon

- 警告等级: **RED** — top1 (SIVE) 占 26.4% > 25.0%; top5 占 58.9% > 50.0%; outlier ticker: AAOI,POET,AXTI (median excess 3x overall)
- n: 348
- top1 集中度: 26.4% (SIVE)
- top5 集中度: 58.9%
- hit_rate (with outlier): 65.4%
- hit_rate (去 top1): 65.4%
- hit_rate (去 top2): 67.6%
- hit_rate (去 top3): 63.3%
- outlier ticker (median 3x+): AAOI, POET, AXTI, RKLB, LITE, AEHR, INTC, TSEM, TE, AEVA, SIMO

### 6m horizon

- 警告等级: **RED** — top1 (SIVE) 占 26.4% > 25.0%; top5 占 58.9% > 50.0%; outlier ticker: NBIS,AMD,FLY (median excess 3x overall)
- n: 348
- top1 集中度: 26.4% (SIVE)
- top5 集中度: 58.9%
- hit_rate (with outlier): 85.5%
- hit_rate (去 top1): 85.5%
- hit_rate (去 top2): 70.0%
- hit_rate (去 top3): 70.0%
- outlier ticker (median 3x+): NBIS, AMD, FLY, CIFR, RKLB, LITE, VIRT, WULF

## 4. tier_A 追高检验

**警告等级**: RED | 追高: 4 / 中段: 0 / 早期: 1

| ticker | 首次论证 | entry | pre_60d_low | 相对 low | 追高档位 | 票后涨 |
|---|---|---|---|---|---|---|
| SIVE | 2026-03-16 | $0.8600 | $0.7000 (2026-03-16) | **+22.9%** | early | +1016.3% |
| NBIS | 2025-09-19 | $101.9500 | $43.8900 (2025-07-11) | **+132.3%** | chasing | +127.9% |
| AAOI | 2025-12-11 | $35.3950 | $18.5000 (2025-11-21) | **+91.3%** | chasing | +377.6% |
| AXTI | 2025-12-26 | $14.2350 | $4.0000 (2025-10-10) | **+255.9%** | deep_chasing | +582.7% |
| LITE | 2025-12-01 | $320.7800 | $144.5200 (2025-09-25) | **+122.0%** | chasing | +187.3% |

## 5. 总评

tier_A 3m hit 65.4% / median excess +12.90% / ⚠ 3m outlier 警告 RED — top1 (SIVE) 占 26.4% > 25.0%; top5 占 58.9% > 50.0%; outlier ticker: AAOI,POET,AXTI (median excess 3x overall) / 追高检验: 4/0/1 = 追高/中段/早期