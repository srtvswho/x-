# jukan05_his — KOL Standard Scoreboard

**生成时间**: 2026-06-23T03:36:59  
**置信度**: **A+** — raw_hit 96.3%, Wilson 81.7%, n=27, 强信号  
**入参**: n_total=27 | n_resolved=27 | dropped=0

## 1. 核心指标 (raw 选股命中率 — 不依赖任何基准)

| 指标 | 值 |
|---|---|
| n_resolved | 27 |
| raw 涨 | 26 |
| raw 跌 | 1 |
| **raw 选股命中率** | **96.3%** |
| raw 中位 | +29.6% |
| Wilson 95% 下界 | 81.7% |

## 2. Excess vs Benchmarks

| Bench | n | med_excess | hit_rate |
|---|---|---|---|
| SPY | 27 | +27.8% | 77.8% |
| SOXX | 27 | +9.4% | 66.7% |
| SMH | 27 | +5.4% | 66.7% |

## 3. Attribution 分布 (铁律 3: 区分判断归属)

| 类型 | 计数 | 比例 |
|---|---|---|
| ORIGINAL | 26 | 96.3% |
| RELAYED+COMMENT | 1 | 3.7% |

## 4. 4 分类 (铁律 6: 禁止 '5 大赢/5 大输' 模糊说法)

### 4.1 raw 真赢 (26 条, 选 5 大)
| ticker | direction | horizon | raw_ret | excess_vs_soxx |
|---|---|---|---|---|
| SNDK | long | 90d | +180.8% | +169.3% |
| AMD | long | 180d | +158.7% | +96.4% |
| MU | long | 180d | +114.7% | +67.8% |
| ASML | long | 180d | +96.2% | +52.8% |
| NVDA | long | 180d | +88.5% | +9.4% |

### 4.2 raw 真输 (1 条)
| ticker | direction | horizon | raw_ret | excess_vs_soxx |
|---|---|---|---|---|
| QCOM | short | 180d | -14.3% | -53.3% |

### 4.3 跑赢板块 (27 条, 选 5 大)
| ticker | direction | horizon | raw_ret | excess_vs_soxx |
|---|---|---|---|---|
| SNDK | long | 90d | +180.8% | +169.3% |
| AMD | long | 180d | +158.7% | +96.4% |
| MU | long | 180d | +114.7% | +67.8% |
| ASML | long | 180d | +96.2% | +52.8% |
| MU | long | 180d | +46.4% | +35.7% |

### 4.4 跑输板块 (27 条, 含 raw 涨的)
| ticker | direction | horizon | raw_ret | excess_vs_soxx |
|---|---|---|---|---|
| AAPL | long | 180d | +12.5% | -60.8% |
| QCOM | short | 180d | -14.3% | -53.3% |
| NVDA | long | 180d | +4.6% | -42.5% |
| NVDA | long | 180d | +5.7% | -40.4% |
| NVDA | long | 180d | +5.5% | -36.5% |

## 5. 能力圈 (ticker cluster)

### 5.1 强项 (raw_hit ≥ 60% + n ≥ 3)
| ticker | n | raw_hit | med_excess_soxx |
|---|---|---|---|
| MU | 4 | 100.0% | +25.9% |
| NVDA | 9 | 100.0% | -15.3% |
| AMD | 3 | 100.0% | +1.6% |

### 5.2 弱项 (raw_hit < 50% + n ≥ 3)
| ticker | n | raw_hit | med_excess_soxx |
|---|---|---|---|

## 6. Dropped 误抽 (0 条 — 铁律 1+2 自动拦截)

| source_id | source_date | ticker | original_dir | action | reason |
|---|---|---|---|---|---|

## 7. 跟单建议

✅ **可跟单** — 跟 A+ 信号
- **能力圈**: MU, NVDA, AMD