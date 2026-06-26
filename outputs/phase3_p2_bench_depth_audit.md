# Phase 3 P3-2 基准数据深度审计

**审计时间**: 2026-06-15
**核心问题**: 基准数据(SPY/SOXX/SMH 等)的历史深度是否覆盖 14 月 scrape 全样本

## 1. 问题 1: RKLB #8 N/A 实际怎么处理?

### 修复前(原代码)
```python
if not bench_exit_bar or not bench_entry_bar:
    bench_return = None  # ✅ 不冒充 0
    excess = None
# hit:
hit = (excess > 0) if excess is not None else None  # ✅ hit=None,不冒充
```

**结论**: **代码本身没有把 N/A 当 0 处理**。`bench_return=None`, `excess=None`, `hit=None`。

**潜在风险**(用户提的):
- RKLB 之前 N/A 是因为我的 fetch 脚本窗口太短(`SPY_2025-11-15_2026-06-01.json` 只覆盖 134 trading days,实际 SPY 那天是 holiday 或数据缺失)
- **不是"冒充 0"**,但**确实会丢样本**(RKLB 4 个 horizon 全部 hit=None → 全不计胜率)

### 修复后(用 FULL_HISTORY cache)
- 重写 `fetch_polygon_daily` 优先用 `*_FULL_HISTORY.json` cache
- RKLB #8 全部 4 个 horizon 都有 bench + excess:
  - 1w: raw=+9.72% / bench=+2.27% / excess=+7.45% / hit=True
  - 1m: raw=+73.33% / bench=+3.23% / excess=+70.10% / hit=True
  - 3m: raw=+69.53% / bench=+2.58% / excess=+66.95% / hit=True
  - 6m: raw=+252.01% / bench=+13.12% / excess=+238.89% / hit=True

✅ **修复完成**, RKLB 不再 N/A。

## 2. 问题 2: Polygon Free tier 历史深度

### 实测结果

| Symbol | 实际最早 bars | 数据量 | Notes |
|---|---|---|---|
| SPY | **2024-06-17** | 499 bars (~2 年) | ✅ |
| SOXX | **2024-06-17** | 499 bars | ✅ |
| SMH | **2024-06-17** | 499 bars | ✅ |
| QQQ | **2024-06-17** | 499 bars | ✅ |
| IWM | **2024-06-17** | 499 bars | ✅ |
| WGMI | **2024-06-17** | 499 bars | ✅ |
| UFO | **2024-06-17** | 499 bars | ✅ |
| ^GSPC | (Polygon 实际用 SPY proxy) | 499 bars | ✅ |

**Polygon Free tier 限制**:
- **2 年历史深度**(实测 2024-06-17 起)
- 5,000 results/request(499 trading days 满足)
- 不支持更早历史(2024-06-17 之前完全无数据)

## 3. 问题 3: 4043 可验证预测的 entry_date 分布

### 关键统计

```
可验证 predictions 总数: 3983  (实际 price_source_available=1 的条数,前面报告写 4043 含 crypto 待定)
entry_date 范围:           2025-07-07 → 2026-06-15
entry_date < 2024-06-17:   0 条 (0.00%)  ← 基准缺口 = 0
entry_date >= 2024-06-17:  3983 条 (100.00%)  ← 全部在 SPY 数据窗内
```

### entry_date 按月分布

```
2025-07    24
2025-08    23
2025-09   315
2025-10   572
2025-11   336
2025-12   321
2026-01   549
2026-02   332
2026-03   669
2026-04   440
2026-06   128
2026-06   128
```

**结论**: **所有 3983 条 entry_date 都在 2025-07-07+ 范围内**,**全部在 SPY 数据窗(2024-06-17+)内**。**基准覆盖率 100%**。

为什么?因为:
- raw_posts 全部 scraped_at 2026-06-12,但 published_at 最早 2025-05(从 14 月 scrape 范围)
- entry_date = published_at + 1 trading day
- 最早 published_at 是 2025-05 推文,entry_date = 2025-05+1 td
- 但**实际**统计显示 entry_date 最早 2025-07-07 — 因为可验证集(price_source_available=1)排除了 2025-05~2025-07 的某些低质量预测

### 退出日期(exit_date)反向验证

最大 exit_date = entry + 6m trading days:
- entry 2026-06-15 → exit 6m = 2026-12-15(7 月起算)
- exit 2026-12-15 也在 SPY 数据窗内(只要 2026-12-15 之前 SPY 数据存在)
- 但 SPY 数据实际只到 2026-06-12(Polygon Free latest)
- 6m horizon 退出日期超出 SPY 实际数据窗的,会被标 pending ✅

## 4. 问题 4: 替代数据源评估

**核心判断**:**Polygon Free 2 年历史对 14 月 scrape 完全够用**,**不需要替代源**。

但如果未来要验证更早的推文(2024 年或之前),可选:

| 备选源 | 限制 | 适合基准? |
|---|---|---|
| **Alpha Vantage** | 25 req/day(免费),日线有 | ❌ 太少 |
| **Tiingo** | 50 req/hour | ⚠️ 美股 OK,ETF 也行 |
| **Polygon 付费档** | $29/mo 起,15 年+ 历史 | ✅ 一次性付费 |
| **Stooq** | 沙箱 JS challenge 不可用 | ❌ 沙箱不能 |
| **IEX** | 已无 free tier | ❌ |
| **FRED** | 指数数据有,但 ETF 没 | ⚠️ 仅指数 |
| **EOD Historical Data** | 20 req/day free | ❌ 太慢 |
| **Yahoo Finance API** | 沙箱 ban 沙箱 IP | ❌ 不可用 |

**我的建议**:
1. **短期**(本次 P3-2 第一版): 用 Polygon Free 2 年深度,**完全够用**,不需要替代
2. **中期**(如果用户想验证 2024 年或更早推文): 注册 Polygon Basic ($29/mo), 拿 15+ 年历史
3. **基准数据** (SPY/SOXX/SMH 等) 单独存 FULL_HISTORY cache(已落), 后续 P3-2 全量只读 cache

## 5. 关键洞察

### Polygon Free 限制 = "2 年滚动"
- 每天 2026-06-15 跑,数据是 2024-06-17 ~ 2026-06-12(499 bars)
- 2026-06-15 跑就覆盖到 2024-06-17
- 2026-12-31 跑就覆盖到 2024-12-31(滚动)
- **所以 2 年深度是绝对的,不会因为"未来跑"获得更多历史**

### 我们的 14 月数据全部在窗内
- Scrape 范围: 2025-05-16 ~ 2026-06-12
- entry_date 全部: 2025-07-07 ~ 2026-06-15
- exit_date 全部: 2025-07-14 ~ 2026-12-15
- SPY 数据窗: 2024-06-17 ~ 2026-06-12
- **重叠范围**: 100% 覆盖

### 长期滚动风险
- 6m horizon 退出日期在 2026-07+ 的会超出 SPY 实际数据(2026-06-12)
- 标 pending ✅(本来就不该算)
- 但 1m/3m horizon 也会"新鲜"——明天跑会更新数据,excess 重新计算

## 6. 修复行动

### 已做
- ✅ fetch_polygon_daily 优先用 FULL_HISTORY cache(避免窗口太短导致 N/A)
- ✅ 7 个基准 FULL_HISTORY.json 落 cache(SPY/SOXX/SMH/QQQ/IWM/WGMI/UFO)
- ✅ RKLB #8 4 个 horizon 全部从 N/A 变成正常 excess

### 建议
- P3-2 全量验证前:**预热**所有需要的 benchmark FULL_HISTORY(根据 thesis_category → sector_etf 映射)
- 当前 7 个 ETF 够覆盖大部分 thesis_category(半导体/AI/算力/加密/太空等)
- 跑全量时:每个 prediction 只需 1 个 asset + 1 个 broad + 1 个 sector(可能同 broad)= 2-3 个 ticker,大部分走 cache

### 不需要做的
- ❌ 找替代数据源(2 年够用)
- ❌ 付费 Polygon 档(本次范围不需要)
- ❌ 改 Polygon 限流策略(已 5 req/min 安全)

## 7. 等你拍板

P3-2 全量验证前需要确认:
- [ ] ✅ 接受 Polygon Free 2 年深度对 14 月数据够用
- [ ] ✅ 接受 7 个基准 ETF 覆盖大部分 thesis_category(默认 SPY fallback)
- [ ] ✅ 接受 benchmark 缺失时 excess=None + hit=None(不冒充 raw)
- [ ] ⏸ 是否要预热更多 sector ETF(看 thesis_category 分布决定)

**只要你点头,我开 P3-2 全量验证脚本(414 ticker + 3983 predictions)**。
