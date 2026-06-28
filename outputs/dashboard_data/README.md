# 大V情报 — Dashboard 数据样本 (第一版, 真实数据)

**生成时间**: 2026-06-28T08:39:58.047914+00:00
**目的**: 给 UI 设计师导出数据样本, 让 UI 能对上真实的数据结构
**说明**: 不做 UI, 只导出数据

## 文件清单

| 文件 | 内容 | 用途 |
|---|---|---|
| `01_extractions_intel_25_samples.json` | 25 条 extractions_intel 真实样本, 全字段 (含 R12 flag) | UI 调样式时用 |
| `02_raw_posts_5_samples.json` | 5 条 raw_posts 原文 (跟 extractions 对应) | 看推文原始结构 |
| `03_schema.json` | 两张表的 CREATE TABLE schema | UI 知道字段类型和命名 |
| `04_kol_mapping.json` | 4 大V handle → source_id → 强项/弱项 映射 | 区块 1 人物卡用 |

## 4 大V (人物卡用)

- **Jukan** (`tw_jukan05`): 真·信号源, 强存储/代工
- **Serenity** (`tw_aleabitoreddit`): 光通信瓶颈专家, 顺势押龙头
- **zephyr** (`tw_zephyr_z9`): 产业卡点雷达, long-only 看卡点极准
- **Austin** (`tw_austinsemis`): 商业格局分析, 认知源 (非信号源)

## extractions_intel 字段说明 (12 个 + 6 个 R12 状态)

| 字段 | 类型 | 用途 |
|---|---|---|
| `id` | INTEGER | 主键 |
| `post_id` | TEXT | FK → raw_posts.post_id |
| `source_id` | TEXT | `tw_jukan05` / `tw_aleabitoreddit` / `tw_zephyr_z9` / `tw_austinsemis` |
| `extracted_at` | TEXT | ISO 8601 |
| `model_version` | TEXT | `deepseek-v4-pro` |
| `prompt_version` | TEXT | `v2.0.1-intel` |
| `raw_response` | TEXT | 完整 LLM JSON 响应 (调试用) |
| `ticker` | TEXT/JSON | e.g. `'["MU", "SNDK"]'` 或 `null` |
| `company` | TEXT/JSON | e.g. `'["Micron"]'` |
| `direction` | TEXT | `long` / `short` / `neutral` |
| `short_skeptical` | INT | 0 / 1 (仅 short 生效) |
| `bottleneck` | TEXT | HBM/光通信/CPO/存储/AI算力/InP/Substrate/封装/光刻/电力/EDA/interconnect/混合键合/化合物半导体/晶圆代工/推理/训练 等 |
| `attribution` | TEXT | `ORIGINAL` (原创) / `RELAYED` (转发+评论) / `RC` (纯转发) / `NA` (单条原创无声明) |
| `rebuts_narrative` | TEXT | 作者反驳的主流叙事, e.g. "反驳认为小模型廉价服务有益的说法" |
| `summary_100` | TEXT | ≤100 字客观概括 |
| `is_retrospective` | INT 0/1 | R12: victory_lap 回顾 (模块 3 不算新信号) |
| `is_disclosure` | INT 0/1 | R12: position_disclosure 持仓披露 |
| `is_self_reported_returns` | INT 0/1 | R12: 自报收益数字 |

## 注意: JSON array 字段

`ticker` 和 `company` 在 DB 里存的是 **JSON 字符串**, 不是逗号分隔:
- `ticker='["MU", "SNDK"]'` (UI 解析时 split by `","` 然后 strip `[ ]`)
- `ticker='["NVDA"]'` 或 `ticker=null`

## 待模块 3 补的字段 (UI 占位)

- **判断序列**: 某大V 对某标的 N 次喊单的时序
- **最新态度转折**: 最近 30/60/90 天从 long → short 或反之
- **是否还有空间**: 当前价 vs 历史喊单价 + 接盘区/二次机会区/真低位 三分类

## 其他数据点 (UI 可能要加)

- `raw_posts.published_at` (ISO 8601, 用于时间窗筛选 1/3/6/12 月)
- `raw_posts.raw_text` (原文, 详情展开用)
- `raw_posts.raw_url` (跳转 X 用)
- `raw_posts.captured_at` (落库时间, 用于"今日/昨天"判定)
- `raw_posts.raw_json` (完整 Apify JSON, 含 media)

## 增量抽取保证 (重要)

`extractions_intel` 用 `(post_id, prompt_version)` 唯一索引, 增量抽取:
- 每天 cron 跑时, `intel_extract.py --since 7d_ago` 只抽没抽取过的
- 同一 post_id 用不同 prompt_version (v2.0.1 → v2.0.2) 时会重抽, 历史数据不被破坏
