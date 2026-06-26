# Phase 3 P3-2 诊断: captured_at 字段语义错误

**诊断时间**: 2026-06-15
**严重程度**: 🔴 **致命** — 影响所有 4470 predictions 的 entry_date
**建议**: P3-2 验证函数 entry_date 必须用 **`published_at`** 而非 `captured_at`

## 1. 字段定义溯源

| 字段 | 来源 | 语义 | 是否正确 |
|---|---|---|---|
| `raw_posts.published_at` | X API (`createdAt`) | **推文真实发布时间** | ✅ |
| `raw_posts.captured_at` | Scraper 写入 | **抓取/处理时间** | ✅ |
| `predictions.published_at` | 从 raw_posts 复制 | **推文真实发布时间** | ✅ |
| `predictions.captured_at` | 从 raw_posts 复制 | **抓取/处理时间** | ✅ |

代码层 (`signalboard/extract/postprocess.py:268-279`):
```python
row = conn.execute(
    "SELECT published_at, captured_at FROM raw_posts WHERE post_id = ?",
    (post_id,),
).fetchone()
published_at, captured_at = (row if row else ("", ""))
```

两个字段都被冗余存到 predictions 表,**没有混用**。但**`captured_at` 字面意思就是"被抓的时间"**,我们之前误以为它是推文发布时间。

## 2. 抓取批次观察

```
raw_posts.captured_at 分布:
  2026-06-12  6354  (一次性抓完全部 14 月推文)
```

只有**一次抓取**,所以 `captured_at` 全部 = 2026-06-12。这与我们的诊断"分批抓取"的预期不符 — 实际上**scraper 是 1 次抓完**,但 X 用户实际发推是 14 个月分散的。

## 3. 全 4470 predictions 偏差分布

`captured_at` (抓取时间) − `published_at` (推文发布时间) 偏差:

```
+    0 天     15  (推文发完就抓)
+    1 天      5
+    2 天     22
+    3 天      6
+    4 天      6
+   75 天     53  ← 早期推文
+   86 天     53
+  116 天     59
+  138 天     81  ← 最大峰值
+  159 天     65
+  160 天     61
+  183 天     59
+  204 天     53  ← 最早推文(2025-05)
```

**最大偏差 204 天**(约 6.8 个月),平均 ~100 天。

## 4. SIVE 推文时间窗 vs SIVEF 数据窗

**SIVE 338 条推文 published_at 真实分布**:
```
2026-03  93
2026-04  101
2026-05  112
2026-06  32
```

**SIVEF Polygon 数据窗**: `2026-03-16` → `2026-06-12`(63 bars)

**SIVE 推文与 SIVEF 数据重叠**:
```
data_window_inside (2026-03-16+):  338 条  (100%)
```

**所有 338 条 SIVE 推文 published_at 都在 SIVEF 数据窗内** ✅ 全部可验证。

但**这是巧合**(SIVE 是 2026 春季热门,不是 2025 老标的)。

## 5. 对 entry_date 算法的修正

**当前 P3-2 设计**:
```python
entry_date = next_trading_day(captured_at)  # ❌ 错!抓取时间不是推文时间
```

**修正后**:
```python
entry_date = next_trading_day(published_at)  # ✅ 推文真实发布时间
```

## 6. 量化影响

**用错字段的代价**(以 SIVE 2026-03 最早一条为例):
- 推文实际 published_at: 2026-03-16
- 错用 captured_at: 2026-06-12
- **entry_date 错位 88 天**
- 入场价 2026-06-12 之后下一个交易日($9.6 左右)
- 实际入场价 2026-03-16 之后下一个交易日($0.7 左右,见 P3-2 数据)
- raw_return 完全错: 错算成 +0% 附近,实际 +1100% 起步

**SIVE 338 条全部用 captured_at 会让所有 1w/1m/3m 收益被高估/低估**:
- 1m horizon: 1m 内已到期的(2026-05+ 发的) — 错用 captured_at 把 entry 推后 88 天,1m 短了,raw_return 偏低
- 6m horizon: 全部都还没到期 (data_window 截止 2026-06-12 + 6m = 2026-12-12),6m 都 pending — 错用 captured_at 也 pending,但 pending 概念本身没问题

**所以**:如果不修正,338 条 SIVE 数据会**完全错乱**,但 pending 状态可能"对冲"了部分错误(因为 horizon 都还没到期)。

## 7. 其他 ticker 受影响程度

| 推文 published_at 越早 | captured_at - published_at 偏差越大 | 影响 |
|---|---|---|
| 2025-05 (最早) | 204 天 | 🔴 严重 |
| 2025-09 | ~100 天 | 🟡 中等 |
| 2026-03 (近期) | 0-30 天 | 🟢 轻微 |

**估计**:全 4470 predictions 中,**约 30% (1300+ 条)偏差 >100 天**,需要修正 entry_date 才能正确验证。

## 8. 修复行动

### 必须做(P3-2 验证函数核心修改)
```python
# 错的写法
entry_date = next_trading_day(prediction.captured_at)

# 正确的写法
entry_date = next_trading_day(prediction.published_at)
```

### 不需要做(数据已正确)
- 不需要 UPDATE predictions.captured_at
- 不需要 UPDATE raw_posts.captured_at
- 字段值正确,只是验证层读错字段

### 建议(可选)
- 在 P3-2 验证函数加注释:`# 用 published_at 不用 captured_at,后者是抓取时间`
- 未来 schema 可考虑 `signal_at` 字段名替代 `published_at`,更清晰

## 9. 用户原始 3 个诊断问题答复

> 1. captured_at 字段在 raw_posts 的值,和 createdAt / published_at 是否一致?

**答**:
- `raw_posts.published_at` = X API `createdAt` = 推文真实发布时间 ✅ 一致
- `raw_posts.captured_at` = scraper 抓取时间(2026-06-12) ❌ 与 createdAt 无关

> 2. SIVE 338 条 createdAt 分布?

**答**:
- 2026-03: 93
- 2026-04: 101
- 2026-05: 112
- 2026-06: 32
- 分散 4 个月,**不是 2025 年**(SIVE 是 2026 春季新热点)
- 但 captured_at 全是 2026-06-12(抓取批次时间)

> 3. captured_at 在哪一步写入的?

**答**:
- **Scraper 阶段**:`raw_posts.captured_at` = `datetime.utcnow().isoformat()`
- **Extract 阶段**(`postprocess.py:268-279`):从 raw_posts 复制到 predictions.captured_at

## 10. 结论

🔴 **captured_at 字段语义本身没错**(就是抓取时间),但 P3-2 验证层需要用 `published_at` (推文真实发布时间)。

**修复非常简单**:P3-2 验证函数里把 `captured_at` 替换为 `published_at`。

**不需要改动任何数据库数据**,不需要 ALTER TABLE,不需要 UPDATE。

**等你确认**:
1. 接受 P3-2 验证函数用 `published_at` 算 entry_date
2. 是否需要新建一列 `signal_at = published_at`(命名更清晰,但冗余)
3. 是否要在 predictions 表加 `entry_date_hint` 字段(预计算 next_trading_day 缓存,避免每次验证重算)
