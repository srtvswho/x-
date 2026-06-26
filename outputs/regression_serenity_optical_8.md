# aleabitoreddit (optical 8) — KOL Standard Scoreboard

**生成时间**: 2026-06-23T03:37:00  
**置信度**: **A** — raw_hit 70.2%, Wilson 66.6%, n=687  
**入参**: n_total=687 | n_resolved=687 | dropped=0

## 1. 核心指标 (raw 选股命中率 — 不依赖任何基准)

| 指标 | 值 |
|---|---|
| n_resolved | 687 |
| raw 涨 | 482 |
| raw 跌 | 205 |
| **raw 选股命中率** | **70.2%** |
| raw 中位 | +0.5% |
| Wilson 95% 下界 | 66.6% |

## 2. Excess vs Benchmarks

| Bench | n | med_excess | hit_rate |
|---|---|---|---|
| SPY | 638 | +0.3% | 63.0% |
| SOXX | 638 | +0.3% | 62.0% |
| SMH | 0 | +0.0% | 0.0% |

## 3. Attribution 分布 (铁律 3: 区分判断归属)

| 类型 | 计数 | 比例 |
|---|---|---|
| ORIGINAL | 687 | 100.0% |

## 4. 4 分类 (铁律 6: 禁止 '5 大赢/5 大输' 模糊说法)

### 4.1 raw 真赢 (482 条, 选 5 大)
| ticker | direction | horizon | raw_ret | excess_vs_soxx |
|---|---|---|---|---|
| SIVE | long | 90d | +11.5% | +0.0% |
| SIVE | long | 90d | +11.5% | +0.0% |
| SIVE | long | 90d | +11.5% | +0.0% |
| SIVE | long | 90d | +11.5% | +0.0% |
| SIVE | long | 90d | +11.5% | +0.0% |

### 4.2 raw 真输 (205 条)
| ticker | direction | horizon | raw_ret | excess_vs_soxx |
|---|---|---|---|---|
| NBIS | long | 90d | -0.4% | -0.4% |
| NBIS | long | 90d | -0.4% | -0.4% |
| NBIS | long | 90d | -0.4% | -0.4% |
| NBIS | long | 90d | -0.4% | -0.4% |
| NBIS | long | 90d | -0.4% | -0.4% |

### 4.3 跑赢板块 (687 条, 选 5 大)
| ticker | direction | horizon | raw_ret | excess_vs_soxx |
|---|---|---|---|---|
| AXTI | long | 90d | +4.8% | +4.8% |
| AXTI | long | 90d | +4.8% | +4.8% |
| AXTI | long | 90d | +4.8% | +4.8% |
| AXTI | long | 90d | +4.8% | +4.7% |
| AXTI | long | 90d | +4.1% | +4.1% |

### 4.4 跑输板块 (687 条, 含 raw 涨的)
| ticker | direction | horizon | raw_ret | excess_vs_soxx |
|---|---|---|---|---|
| NBIS | long | 90d | -0.4% | -0.4% |
| NBIS | long | 90d | -0.4% | -0.4% |
| NBIS | long | 90d | -0.4% | -0.4% |
| NBIS | long | 90d | -0.4% | -0.4% |
| NBIS | long | 90d | -0.4% | -0.4% |

## 5. 能力圈 (ticker cluster)

### 5.1 强项 (raw_hit ≥ 60% + n ≥ 3)
| ticker | n | raw_hit | med_excess_soxx |
|---|---|---|---|
| LITE | 65 | 100.0% | +0.8% |
| COHR | 37 | 100.0% | +0.5% |
| AAOI | 97 | 100.0% | +1.0% |
| AXTI | 119 | 100.0% | +2.0% |
| AEHR | 7 | 100.0% | +2.1% |
| SIVE | 25 | 100.0% | +0.0% |

### 5.2 弱项 (raw_hit < 50% + n ≥ 3)
| ticker | n | raw_hit | med_excess_soxx |
|---|---|---|---|
| NBIS | 337 | 39.2% | -0.1% |

## 6. Dropped 误抽 (0 条 — 铁律 1+2 自动拦截)

| source_id | source_date | ticker | original_dir | action | reason |
|---|---|---|---|---|---|

## 7. 跟单建议

✅ **可跟单** — 跟 A 信号
- **能力圈**: LITE, COHR, AAOI, AXTI, AEHR
- **避开**: NBIS