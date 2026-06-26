# jukan05 — KOL Standard Scoreboard

**生成时间**: 2026-06-23T03:36:59  
**置信度**: **A** — raw_hit 72.4%, Wilson 61.4%, n=76  
**入参**: n_total=76 | n_resolved=76 | dropped=0

## 1. 核心指标 (raw 选股命中率 — 不依赖任何基准)

| 指标 | 值 |
|---|---|
| n_resolved | 76 |
| raw 涨 | 55 |
| raw 跌 | 21 |
| **raw 选股命中率** | **72.4%** |
| raw 中位 | +8.8% |
| Wilson 95% 下界 | 61.4% |

## 2. Excess vs Benchmarks

| Bench | n | med_excess | hit_rate |
|---|---|---|---|
| SPY | 76 | +1.8% | 73.7% |
| SOXX | 76 | -9.3% | 61.8% |
| SMH | 76 | -9.0% | 60.5% |

## 3. Attribution 分布 (铁律 3: 区分判断归属)

| 类型 | 计数 | 比例 |
|---|---|---|
| ORIGINAL | 26 | 34.2% |
| RELAYED+COMMENT | 1 | 1.3% |
| RELAYED | 49 | 64.5% |

## 4. 4 分类 (铁律 6: 禁止 '5 大赢/5 大输' 模糊说法)

### 4.1 raw 真赢 (55 条, 选 5 大)
| ticker | direction | horizon | raw_ret | excess_vs_soxx |
|---|---|---|---|---|
| MU | long | 180d | +257.5% | +215.5% |
| MU | long | 180d | +250.7% | +203.8% |
| SNDK | long | 90d | +180.8% | +169.3% |
| AMD | long | 180d | +158.7% | +96.4% |
| MU | long | 180d | +114.7% | +67.8% |

### 4.2 raw 真输 (21 条)
| ticker | direction | horizon | raw_ret | excess_vs_soxx |
|---|---|---|---|---|
| NVDA | short | 180d | -75.8% | -141.2% |
| GOOGL | short | 180d | -57.8% | -100.7% |
| NVDA | short | 180d | -44.2% | -53.2% |
| AMD | short | 90d | -36.6% | -50.4% |
| INTC | short | 30d | -32.5% | -41.1% |

### 4.3 跑赢板块 (76 条, 选 5 大)
| ticker | direction | horizon | raw_ret | excess_vs_soxx |
|---|---|---|---|---|
| MU | long | 180d | +257.5% | +215.5% |
| MU | long | 180d | +250.7% | +203.8% |
| SNDK | long | 90d | +180.8% | +169.3% |
| AMD | long | 180d | +158.7% | +96.4% |
| MU | long | 180d | +114.7% | +67.8% |

### 4.4 跑输板块 (76 条, 含 raw 涨的)
| ticker | direction | horizon | raw_ret | excess_vs_soxx |
|---|---|---|---|---|
| NVDA | short | 180d | -75.8% | -141.2% |
| GOOGL | short | 180d | -57.8% | -100.7% |
| NVDA | short | 180d | -8.7% | -98.7% |
| META | long | 180d | -19.7% | -88.8% |
| AVGO | long | 180d | +9.4% | -85.9% |

## 5. 能力圈 (ticker cluster)

### 5.1 强项 (raw_hit ≥ 60% + n ≥ 3)
| ticker | n | raw_hit | med_excess_soxx |
|---|---|---|---|
| MU | 6 | 100.0% | +51.7% |
| AVGO | 5 | 100.0% | -31.4% |
| TSM | 9 | 88.9% | +6.9% |
| AMD | 5 | 80.0% | -20.5% |
| NVDA | 32 | 68.8% | -22.5% |
| INTC | 3 | 66.7% | +32.7% |

### 5.2 弱项 (raw_hit < 50% + n ≥ 3)
| ticker | n | raw_hit | med_excess_soxx |
|---|---|---|---|
| AAPL | 5 | 40.0% | -17.2% |

## 6. Dropped 误抽 (0 条 — 铁律 1+2 自动拦截)

| source_id | source_date | ticker | original_dir | action | reason |
|---|---|---|---|---|---|

## 7. 跟单建议

✅ **可跟单** — 跟 A 信号
- **能力圈**: MU, AVGO, TSM, AMD, NVDA
- **避开**: AAPL