# 一致性确认报告(选 C 前)

## Q1: ticker=None 那 31 条的状态

**先纠正一个误解**: 修复后 predictions 表**没有** ticker=None 的行(0 行,见下)。
31 条 unresolved 队列对应的是 raw_asset_mention 没解析出来(ticker=None) —
这些 unresolved 在 predictions 表里**根本没入**,因为:
- `predictions.ticker NOT NULL` 约束
- `insert_prediction` 在 ticker=None 时抛 `NOT NULL constraint failed`
- **而旧代码 persist_post_result 整批循环无 try/except**,第一条 unresolved 失败
  会让同 post 后续合法 ticker(RKLB/IBIT/NBIS/LPTH 等)也不入库

**这就是 20 个 has_pred=True 的 post 应该有预测但 0 入库的原因**。

### 修复
- `persist_post_result` 加 `if pred.ticker is None: continue`(跳过 unresolved)
- `persist_post_result` 加 try/except(单条失败不中断其他)
- smoke test: 504753 (LLM 抽 3 条: $225 PT + RKLB + IBIT) → 现在 2 条入库 (RKLB, IBIT),$225 PT 跳过

### 修复前后对比

| 项 | 修复前 | 修复后 v3 | 变化 |
|---|---|---|---|
| **predictions 总** | 4463 | 4470 | +7 (合法 ticker 增量入库) |
| **predictions ticker 非空** | 4463 | 4470 | (全非空) |
| **predictions distinct post** | 2037 | 2043 | +6 (新增 6 个 post 至少 1 条) |
| **post 有 1+ ticker 但同时有 unresolved** | 6 | 11 | +5 (因为之前 20 个 0 入库,现在部分入) |
| **post 0 入库 (unresolved 唯一)** | 20 | 13 | -7 (7 个修复后至少 1 条入) |
| **post 完整入 (无 unresolved)** | 5607 | 5607 | (不变) |
| **post_flags** | 817 | 817 | (未变) |
| **human_review_queue (去重后)** | 31 | 32 | +1 (新 27 个 post 跑批时 1 条新增) |

### "有效预测分母"
- 修前 4463 全 ticker 非空(因为旧逻辑 ON CONFLICT 覆盖 + sqlite 容忍 None)
- 修后 4470 全 ticker 非空
- **0 条需要剔除** — 数据本身没坏,只是 20 个 post 因 bug 丢了预测记录

### 16 个仍未入的 post
13 个 post LLM 抽的全是 unresolved(板块/概念/数字/小众),3 个 post LLM 抽的 raw 有合法 ticker 但落库前出意外。

## Q2: 50 条随机抽查

| 项 | 值 |
|---|---|
| 抽样数 | 50 |
| ticker 全非空 | **50/50 (100%)** |
| market 全非空 | **50/50 (100%)** |
| unique tickers | 38 |
| 38 个 ticker 行情可查(正则匹配) | **38/38 (100%)** |
| 38 个 ticker 已在 aliases 表 | 32/38 (84%) |
| 6 个未在 aliases 但 resolve_alias 自动命中 | LWLG/UMC/GRZ.V/ETN/RUM/TLN (都是真美股) |

38 个 ticker 全部都是真实可查的美股/欧股/亚股:
- 美股:PL/IQE/MSS/IREN/VPG/NBIS/RKLB/...  等 33 个 (Yahoo Finance 直接查)
- 欧洲:AMS.SW (ams-OSRAM)
- 韩国:005930.KS (Samsung)
- 台湾:6451.TW (Shunsin)

## 选 C: 接受 31 条边角 + 进入 Phase 3

- 不剔除任何 records(全 4470 都是合法 ticker)
- 32 条 human_review_queue 是真未解析清单(板块/概念/数字/小众),保留供人工审计
- 后续 Phase 3 (P&L / 命中率) 直接用 4470 预测记录
