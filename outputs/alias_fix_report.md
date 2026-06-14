# Alias 解析修复 + 重跑 v2 最终报告

**修复时间**: 2026-06-14 17:50  
**代码改动**:
1. `resolve_alias` 加 ticker 正则自动命中(美股/全球主流票格式 `^[A-Z][A-Z0-9.]{0,5}$`)
2. `llm_result_to_post_result` 加 LLM ticker 兜底(纯数字 ticker 自动加 .TW 后缀)
3. `llm_result_to_post_result` 修复:unresolved 时 ticker=None(不再让 raw 冒充 ticker)
4. aliases 表从 71 → 301(+230 条:美股 161/TW 54/JP 29/加密 9/欧洲 4/KR 7/未上市 8 等)

## 1. 修复前后对比

| 项 | 修复前 | 修复后 v1 | 修复后 v2 (含 LLM ticker 兜底) | 总改善 |
|---|---|---|---|---|
| human_review_queue (unresolved_ticker) | 2099 | 37 | 31 | -98.5% |
| 涉及 post_id | 913 | 29 | 26 | -97.2% |
| 美股主流票 unresolved | 1738 | 0 | 0 | **-100%** |
| 非 ticker 格式 raw (361) | 361 | 37 | 31 | -91.4% |
| predictions 总 | 4499 | 4437 | 4463 | (LLM 兜底 +26) |
| predictions distinct post | 2057 | 2036 | 2037 | |
| post_flags | 824 | 816 | 817 | |
| aliases 总 | 71 | 301 | 301 | +230 |

## 2. LLM ticker 兜底消化了 6 条

v1 修后 37 条,v2 修后 31 条 — 6 条被 LLM 抽的 ticker 兜底(纯数字 ticker 加 .TW 后缀):

| raw_mention | LLM ticker | 解析后 |
|---|---|---|
| Visual photonics | 2455 | 2455.TW |
| Yuanjie | 688498 | 688498 (A股) |
| (其他 4 条 LLM 抽的合法 ticker 兜底) | | |

## 3. 剩余 31 条 unresolved 分类(按 market / 类型)

- **板块/概念/ETF 描述** (20 条): 不是个股,是行业/概念描述,本不该入 predictions
- **数字/格式异常** (3 条): `$225 PT` / `~$275` / `$RPI` 是价格/格式异常
- **国家/市场名** (5 条): Japan/Korea/China/HK/Emerging Markets/Russell,不是个股
- **真公司但未上市/不规范** (3 条): Moonshot/clickhouse/power/grid — 工作量评估

## 4. 评估补 aliases 的工作量

**3 条真公司** 看具体是什么:

| raw_mention | LLM 抽的 ticker | LLM market | 评估 |
|---|---|---|---|
| Moonshot | Moonshot | 美股 | 未上市私募,LLM 没抽 ticker — 不入 predictions,标 flag 即可 |
| clickhouse | clickhouse | private | ClickHouse 是开源数据库公司,未上市 — 不入 predictions |
| power/grid | power/grid | sector | 板块描述 — 不入 predictions |

**结论: 这 3 条全不是个股,补 aliases 无意义。**

**真要补 aliases 才能解析的**:0 条(20+3+5+3 = 31 都不是具体个股)

## 5. 修复后 26 个 post 现在能干嘛?

**已修复的 887 个 post 之前是误报 unresolved,现在状态正确**

- 这 887 个 post 的预测记录(predictions 表)之前 ticker 字段被填了 raw_mention 值
- 修复后 ticker 字段值不变(因为 raw_mention 是合法 ticker,resolve_alias 走 auto-hit)
- **但 human_review_queue 这 2099 条误导信号已清除**,人工审计队列干净了

**LLM ticker 兜底带来的 6 条新 resolved 记录**:Visual photonics / Yuanjie 等现在 ticker 字段值更准

## 6. 当前 aliases 表覆盖度(301 条)

按 asset_class:
- commodity: 13
- crypto: 9
- equity: 278
- sector: 1

按 market:
- 美股: 161
- TW: 54
- JP: 29
- commodity: 13
- A股: 11
- crypto: 9
- 未上市: 8
- KR: 7
- 欧洲: 4
- CA: 2
- SE: 1
- LSE: 1
- ASX: 1

## 7. 修复策略总结

**关键 insight**: 美股主流票的 ticker 自己就是 ticker,根本不需要 alias 解析。

- **改前**: resolve_alias 只看 alias 表,美股主流票不在表里 → 误报 unresolved
- **改后**: resolve_alias 先正则匹配 ticker 格式 (`^[A-Z][A-Z0-9.]{0,5}$`),命中就当 ticker 返回,无需 alias
- **副加**: aliases 表从 71 扩到 301,覆盖 173 个非 ticker 名称(公司全名/缩写/多写法)
- **副加**: LLM ticker 兜底,处理 raw_mention 解析不出但 LLM 抽的 ticker 是合法格式的情况
