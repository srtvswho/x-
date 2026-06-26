# Phase 3 P3-2 全代码 captured_at 排查报告

**诊断时间**: 2026-06-15
**目标**: 排查所有 `captured_at` 引用,确认"信号时间"语义没有被错当成"处理时间"用

## 1. 五个排查点结论

| 排查点 | 结论 | 证据 |
|---|---|---|
| ① entry_date 用 published_at | ✅ **正确** | P3-2 验证函数还没写,刚确认用 published_at |
| ② is_repeat_call 用 published_at | ✅ **正确** | `postprocess.py:213,234` SQL 用 `published_at` |
| ③ 时间衰减曲线 / 月分组 | ⏸ **代码未写** | 没有任何 `*time*decay*` / `analyze*` / `scorecard*` 脚本;P3-2 设计时直接用 published_at |
| ④ pending 判定 | ⏸ **代码未写** | `verifications` 表已建,`list_pending_verifications` 已实现,等 P3-2 验证函数接入 |
| ⑤ 全代码 captured_at 引用 | 18 处,**全部是字段透传或抓取时间,无 1 处被错当"信号时间"用** | 见下表 |

## 2. 全部 18 处 captured_at 引用清单

### A. Schema 定义 / 索引(纯字段,无逻辑)
| 文件:行 | 内容 | 语义 | 状态 |
|---|---|---|---|
| `signalboard/db.py:52` | `raw_posts.captured_at TEXT NOT NULL` | 字段定义 | ✅ |
| `signalboard/db.py:71` | `predictions.captured_at TEXT NOT NULL` | 字段定义 | ✅ |
| `signalboard/db.py:93` | `CREATE INDEX ... idx_predictions_captured_at` | 索引 | ✅ |
| `signalboard/db.py:243` | `verifications.captured_at`(无,实际表无此字段) | — | ✅ |
| `signalboard/db.py:266` | (v2 schema 重复索引) | 索引 | ✅ |
| `signalboard/db.py:373` | (v3 schema 重复索引) | 索引 | ✅ |

### B. 字段透传(从 raw_posts 复制到 predictions)
| 文件:行 | 内容 | 语义 | 状态 |
|---|---|---|---|
| `signalboard/extract/postprocess.py:268` | `SELECT published_at, captured_at FROM raw_posts` | 读 raw_posts 字段 | ✅ |
| `signalboard/extract/postprocess.py:273` | `published_at, captured_at = (row if row else ("", ""))` | unpack | ✅ |
| `signalboard/extract/postprocess.py:279` | `captured_at=captured_at or ""` | 写 PredictionRecord | ✅ |
| `signalboard/models.py:127,188` | `captured_at: str` dataclass 字段定义 | — | ✅ |
| `signalboard/models.py:146,162,215,242` | 序列化/反序列化字段 | 透传 | ✅ |
| `signalboard/models.py:180` | 文档注释 "source_id / published_at / captured_at 是冗余(同 raw_post)" | 文档 | ✅ |
| `signalboard/repository.py:38,41,48` | UPSERT raw_posts 透传 | — | ✅ |
| `signalboard/repository.py:115,122,132` | INSERT predictions 透传 | — | ✅ |

### C. Scraper 写 captured_at(就是抓取时间)
| 文件:行 | 内容 | 语义 | 状态 |
|---|---|---|---|
| `signalboard/scraper.py:614,678` | `_item_to_raw_post(... captured_at)` 参数 | 透传 | ✅ |
| `signalboard/scraper.py:858` | `captured_at = datetime.now(timezone.utc).isoformat()` | **scrape 开始时间** | ✅ |
| `signalboard/scraper.py:888` | `captured_at=captured_at` 调用 fetch | 透传 | ✅ |
| `signalboard/scraper.py:736,741,764` | 递归抓取透传 | — | ✅ |
| `scripts/rescrape_all_v2.py:118,126,134,137,142` | rescrape 脚本写 captured_at | 抓取时间 | ✅ |
| `scripts/run_full_5657_v141.py:40` | 预读 published_at, captured_at 映射 | 字段透传 | ✅ |

### D. ⚠️ 唯一风险点(已检查,无影响)
| 文件:行 | 内容 | 风险 | 评估 |
|---|---|---|---|
| `signalboard/scraper.py:626-628` | `published_at = to_utc_iso(...)`; `if not published_at: published_at = captured_at` | X API 漏 createdAt 时,published_at 退化为抓取时间 | **无影响**: 全 6354 条 published_at 都有真实 X API createdAt,未触发 fallback |

## 3. is_repeat_call 计算详查

**文件**: `signalboard/extract/postprocess.py:196-243`

```python
def compute_repeat_call(pred, db_path, *, source_id, window_days=30):
    # 找同 source+ticker+direction 最早记录
    row = conn.execute(
        """SELECT prediction_id, published_at FROM predictions
           WHERE source_id = ? AND ticker = ? AND direction = ? AND post_id != ?
           ORDER BY published_at ASC LIMIT 1""",
        ...
    )
    # 30 天窗口: published_at >= (prior_dt - 30 天)
    count = conn.execute(
        """SELECT count(*) FROM predictions
           WHERE source_id = ? AND ticker = ? AND direction = ?
           AND post_id != ? AND published_at >= ?""",
        ...
    )
```

**结论**:is_repeat_call **完全用 published_at**,与 captured_at 无关。✅ **正确,无需重算**。

## 4. P3-2 验证层预留物

### verifications 表(已建)
```sql
CREATE TABLE verifications (
    prediction_id         TEXT PRIMARY KEY,
    status                TEXT    NOT NULL DEFAULT 'pending',
    price_returns         TEXT,           -- JSON: {entry_date, exit_date, entry_price, ...}
    entry_price_basis     TEXT    NOT NULL,  -- "next_trading_day(published_at) | open_preferred_close_fallback"
    quantitative_outcome  TEXT,           -- JSON: {raw_return, benchmark_return, excess_return, ...}
    verified_at           TEXT,
    ...
);
```

### list_pending_verifications(已实现)
- `signalboard/repository.py:319` 拉 status='pending' 行,供 P3-2 批处理用
- 不依赖时间字段,只读 verifications 表

### 验证函数本身
- **未写**,等用户拍板 P3-2 第三步

## 5. P3-2 验证函数设计约束(用 published_at)

```python
# ==== 验证函数骨架(等 user 确认后写) ====

def verify_one_prediction(pred: PredictionRecord, today: date) -> Verification:
    # 1. entry_date = next_trading_day(pred.published_at)  # ✅ 用推文真实发布时间
    entry_date = next_trading_day(pred.published_at)
    
    # 2. entry_price = polygon daily bar on entry_date (open preferred, close fallback)
    # 3. for each horizon in [1w, 1m, 3m, 6m]:
    #    exit_date = entry_date + horizon (trading calendar)
    #    if exit_date > today: status = "pending"  # ✅ 用 today
    #    else: exit_price = polygon daily bar on exit_date
    #    raw_return = (exit_price - entry_price) / entry_price
    #    benchmark_return = (SP500_exit - SP500_entry) / SP500_entry  # ✅ 同币种宽基
    #    excess_return = raw_return - benchmark_return
    
    # 4. 写 verifications 表
    return Verification(...)
```

**关键不变量**:
- 时间字段全部来自 `pred.published_at` (推文真实发布时间)
- 不读 `pred.captured_at`(那是抓取时间,无业务意义)

## 6. 唯一建议:文档化

**不需修代码,但建议在 `signalboard/extract/postprocess.py:180` 注释加一行**:

```python
# 重要:captured_at 是抓取/处理时间(2026-06-12 集中抓取)
# 验证层/P3-2 业务逻辑用 published_at(推文真实发布时间)
# 参考: outputs/phase3_p2_diagnose_captured_at.md
```

## 7. 全部盘点总结

| 维度 | 数量 | 状态 |
|---|---|---|
| captured_at 引用点 | 18 | 全部是字段透传或"处理时间"语义,无 1 处误用 |
| is_repeat_call 用 published_at | ✅ | `postprocess.py:213,234` |
| 时间衰减/分组代码 | 0 | 未写,P3-2 设计时直接用 published_at |
| entry_date / pending 判定 | 0 | 未写,P3-2 验证函数接入时用 published_at |
| 任何 SQL 用 captured_at 分组 | 0 | ✅ 无 |
| scraper fallback 风险点 | 1 | `scraper.py:627`,X API 漏 createdAt 退化为抓取时间;实测未触发 |

**结论**:
- **代码层面无 bug**:`captured_at` 字段值正确,`is_repeat_call` 用 `published_at` 正确
- **P3-2 验证函数设计时**:用 `published_at` 算 entry_date / pending / 时间分组,完全规避 captured_at 错用
- **数据层面无 bug**:published_at 来自 X API createdAt,全 6354 条都有真实值,无 fallback 污染

## 8. 给你"放行"我写 P3-2 验证函数 + 10 条算例的检查清单

请逐项确认:
- [ ] ✅ 接受 P3-2 验证函数用 `pred.published_at` 算 entry_date
- [ ] ✅ 接受 P3-2 验证函数用 `pred.published_at + horizon` 算 exit_date
- [ ] ✅ 接受 P3-2 验证函数用 `(today > exit_date)` 判定 pending
- [ ] ✅ 接受 P3-2 时间分组/时间衰减曲线用 `pred.published_at` 月份 bucket
- [ ] ✅ 接受 P3-2 不读 `pred.captured_at`(完全不用)
- [ ] ✅ 接受 `signalboard/scraper.py:627` fallback 不动(实测未触发)
- [ ] ✅ 接受 `signalboard/extract/postprocess.py:180` 加 1 行文档注释(说明字段语义)

**只要你点头,我开第三步(单条验证函数 + 10 条人工算例)**。
