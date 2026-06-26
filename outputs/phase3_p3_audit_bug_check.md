# Phase 3 P3-3 审计: 5 个诊断(验证计算 bug 检查)

**运行时间**: 2026-06-15T14:33:52.599703Z

## 1. SIVE 3 条手算核对

### [首次(SIVE 入场)] pub=2026-03-16
- prediction_id: `009893a3-2db0-41dd-b980-532de75c6ddc`
- entry_date: 2026-03-17  entry_price: $0.8600
- **1w**: exit=2026-03-24 exit_px=$1.3650 raw=+58.72% bench=-2.63% excess=+61.35%
- **1m**: exit=2026-04-16 exit_px=$2.8900 raw=+236.05% bench=+4.60% excess=+231.44%
- **3m**: pending (no detail)
- **6m**: pending (no detail)

### [中段] pub=2026-04-15
- prediction_id: `2ea9d935-0989-4b8c-a4df-d56614584d38`
- entry_date: 2026-04-16  entry_price: $2.4600
- **1w**: exit=2026-04-23 exit_px=$3.1170 raw=+26.71% bench=+0.97% excess=+25.74%
- **1m**: exit=2026-05-15 exit_px=$5.9500 raw=+141.87% bench=+5.35% excess=+136.52%
- **3m**: pending (no detail)
- **6m**: pending (no detail)

### [后段] pub=2026-05-25
- prediction_id: `cca8f1b4-4a9b-4e11-9b34-4c0ff62d1a7a`
- entry_date: 2026-05-26  entry_price: $8.8700
- **1w**: exit=2026-06-02 exit_px=$9.9000 raw=+11.61% bench=+1.20% excess=+10.42%
- **1m**: pending (no detail)
- **3m**: pending (no detail)
- **6m**: pending (no detail)

## 2. 复权一致性审计(关键)

**核心问题**:个股(adjusted) vs 基准(adjusted) 是否复权口径一致?

对比 SIVEF / SPY / SOXX 在 1w / 1m / 3m 区间的 adjusted vs unadjusted 收益:

| 区间 | symbol | adj return | unadj return | diff |
|---|---|---|---|---|

(实际值见上面终端输出,会一并写入文件)

## 3. 5 条长 horizon 负超额

(实际值见上面终端输出)

## 4. pending 样本偏差

- 已 resolved (≥1 horizon 到期): 3670 predictions
- 全 pending: 313 predictions
- resolved 中位月份: 2026-01
- pending 中位月份: 2026-04

**关键问题**:如果 resolved 中位月份 vs pending 中位月份差异大,会有样本偏差

## 5. 绝对收益 vs 超额收益

| horizon | raw_hit_rate | excess_hit_rate | bench_avg | bench_median |
|---|---|---|---|---|
| 1w | 57.1% | 55.5% | +0.53% | +0.49% |
| 1m | 58.4% | 57.1% | +1.98% | +1.02% |
| 3m | 55.9% | 52.9% | +3.03% | +3.24% |
| 6m | 59.5% | 57.6% | +5.45% | +5.82% |

**核心问题**:如果 raw_hit_rate 明显高于 excess_hit_rate,说明她跑赢绝对但跑输基准(基准异常放大).
如果两者接近,说明超额计算正确,她真的跑输基准.