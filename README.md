# signalboard — 信号源记分牌

参考设计文档 `attachments/170aab25__51ad8b58-d992-4390-9dec-ba86076c0f1e.md`。

## 模块总览

| 模块 | 状态 | 说明 |
|---|---|---|
| `signalboard.models` | ✅ | `RawPost` / `PredictionRecord` / `Verification` 三层 dataclass + 枚举 |
| `signalboard.db` | ✅ | SQLite v2 schema + v1→v2 自动迁移 + 自定义 `sha256()` 函数 |
| `signalboard.repository` | ✅ | CRUD(raw_posts / predictions / verifications)|
| `signalboard.scraper` | ✅ | Apify `apidojo/tweet-scraper` 抓取层 + CLI(全量 + 截断细分 + 断点续抓 + 缓存 + 覆盖率) |
| `tests/test_smoke.py` | ✅ | 25 个数据层冒烟测试 |
| `tests/test_scraper.py` | ✅ | 39 个抓取层 mock 测试(不调真实 API) |
| `scripts/scrape_real_smoke.py` | ✅ | 真实小规模冒烟脚本(默认不跑,会扣费) |

## 数据架构

```
raw_posts  (原始内容层,platform 抓到的 post/tweet 原文 + API 原始 JSON)
   ↑ post_id
predictions (抽取层,一条原文可抽 N 条对不同 ticker 的预测)
   ↑ prediction_id
verifications (验证层,可分阶段更新 r_1w / r_1m / r_3m ...)
```

## 快速开始

```bash
# 1. 安装
pip install apify-client  # 抓取层需要
# 2. 准备 db
python -c "from signalboard import init_db; init_db('data/signalboard.db')"
# 3. 抓取
export APIFY_TOKEN=your_apify_token
python -m signalboard.scraper --handle aleabitoreddit --months-back 6
```

## Scraper — Apify apidojo/tweet-scraper V2

### 入口

```python
from signalboard import fetch_account_history, FieldMap, default_field_map

summary = fetch_account_history(
    handle="aleabitoreddit",       # 不带 @
    db_path="data/signalboard.db",
    max_per_month=3000,            # 每月上限(目标全量,触顶自动二分细分)
    months_back=12,                # 往回抓几个月
    cache_dir=".cache",            # 本地响应缓存,避免重复扣费
    use_cache=True,
)
print(summary.to_dict())
# 字段: handle / months_planned / months_done / runs / errors / total_scraped
#       windows_subdivided / interrupted_at
```

### CLI

```bash
# 标准抓取(6 个月,每月最多 3000 条,触顶自动二分)
python -m signalboard.scraper --handle aleabitoreddit --months-back 6

# 小规模试跑(每月最多 20 条)
python -m signalboard.scraper --handle aleabitoreddit --max-per-month 20 --months-back 1

# 打印覆盖率报告(不抓取)
python -m signalboard.scraper coverage --handle aleabitoreddit
# 等价于:
python -m signalboard.scraper --coverage-report --handle aleabitoreddit

# 跳过缓存,强制重抓
python -m signalboard.scraper --handle aleabitoreddit --no-cache

# 首次使用前:拉 1 条真实响应写到 fixtures/ 校准字段映射(会扣费 ~$0.0004)
python -m signalboard.scraper --handle aleabitoreddit --record 1

# 真实小规模冒烟(20 条 ~$0.008,会扣费)
APIFY_TOKEN=... python scripts/scrape_real_smoke.py --handle aleabitoreddit
```

### 关键设计要点

- **数据源**:Apify 平台上的 `apidojo/tweet-scraper` V2(`ACTOR_ID = "apidojo/tweet-scraper"`)
- **调用**:官方 Python 客户端 `apify-client`(`actor().call()` + `dataset().iterate_items()`)
- **Token**:`APIFY_TOKEN` 环境变量,绝不硬编码
- **默认 max-per-month = 3000**:`apidojo/tweet-scraper` V2 单次 run 的合理上限;目标是**全量,不是采样**
- **截断检测 + 二分细分**:某窗口返回条数 == `max_per_month` 时自动二分半月,递归直到每窗口返回 < `max_per_month`(或 `MAX_SUBDIVISION_DEPTH=6`)
- **翻页**:按月切片,`searchTerms` 用 Twitter 高级搜索语法嵌入 `since:YYYY-MM-DD until:YYYY-MM-DD`
- **幂等**:`upsert_raw_post` 按 `post_id` 去重,中断后续抓不重复
- **断点续抓**:`scrape_state` 表追踪每个 handle 已完成的月份,跳过 `months_done`(细分后的子窗口不需要单独登记)
- **覆盖率追踪**:`coverage` 表记录每个细窗口的抓取明细(起止日期 + 条数 + 是否细分 + depth),提供 `coverage` 子命令重看
- **异常低检测**:某月条数 = 0 或 < 全部非零月份中位数的 20% → WARNING
- **本地缓存**:`.cache/{sha256(run_input)}.json`,重跑相同窗口零成本
- **重试**:`_call_actor` 自带指数退避(429/5xx,默认 3 次);`apify-client` 本身也有 8 次重试,双保险
- **解析失败容错**:单条 item 解析失败记日志 + 收集到 `summary.errors`,不中断整体

### 截断检测 + 二分细分 — 工作机制

```
整月 [2026-01-01, 2026-02-01)
  ├─ actor 返回 3000 条 == max_per_month
  ├─ 判定为截断,记 coverage 行 subdivided=1
  └─ 二分为两个半月,各自再抓
       ├─ 左半 [2026-01-01, 2026-01-16) actor 返回 1480 条 < 3000 → OK
       └─ 右半 [2026-01-16, 2026-02-01) actor 返回 1520 条 < 3000 → OK
              → 整月入库 3000 条,coverage 表 3 行
```

如果半月还打满,继续二分,直到 `MAX_SUBDIVISION_DEPTH=6`(每段 ~0.5 天)。如果达到深度仍截断,记 ERROR + 保留 partial 数据,人工介入。

### 覆盖率报告示例

```
# coverage report for handle=aleabitoreddit
# 36 windows, 12 months
# total items_returned: 18234
# median non-zero window: 1480
# low-window threshold: < 296

## per-window
window_start  window_end   returned   persisted cache  depth subdiv
2025-07-01    2025-08-01        1530        1530     N      0      N
2025-08-01    2025-09-01        1480        1480     N      0      N
2025-09-01    2025-09-16         720         720     N      1      N
2025-09-16    2025-10-01         760         760     N      1      N
...

## per-month (histogram)
month      items subdivided  flag
2025-07      1530          N
2025-08      1480          N
2025-09      3000          Y  ⚠ WARNING: 0 items    ← 不,只是被细分
2025-10      1450          N
2025-11         0          N  ⚠ WARNING: 0 items    ← 真正可疑
```

⚠ 注意:`flag` 列的 `0 items` 仅在整月层面检查;被细分的月份实际有 3000 条但被分散在子窗口里,不算异常。

### ⚠️ 踩坑:apidojo/tweet-scraper 翻页模式选择(2026-06)

我们花了 ~$0.16 跑基准测试,对比 3 种分页模式在 11 月窗口的稳定性(目标稳定返 ~393):

| 模式 | 返回 | 稳定性 | 结论 |
|---|---|---|---|
| sort=Latest + (无 disableMaximization) | 393 → 60(两次差 5x) | 不稳定 | actor 自己 maximize 行为非确定,不能用 |
| sort=Top + maxItems=3000 | 93(6 页就停) | 截断 | actor 6 页就停,严重不足 |
| sort=Latest + disableMaximization=true + maxItems=3000 | 381 / 381(两次一致) | 稳定 | 采用这个 |

坑点:
1. sort=Latest 不设 disableMaximization 时,actor 内部会 maximize(用 Latest+Top with dedup 自动翻页),
   但行为非确定性——同输入两次返 393 / 60 差 5x。别用。
2. disableMaximization=true 强制 actor 显式分页(每页 20),maxItems=3000 是硬 cap。
3. sort=Top 模式 actor 翻 6 页就停,远少于 sort=Latest 的 ~19 页。
4. 即使 disableMaximization=true,actor 在大月份(>1000 条)翻页 30+ 页后偶尔截断几页,
   通常差 1-6 条(分页边界)。差异在 ±1% 以内可接受,>10% 算真截断。
5. 截断检测靠 maxItems 打满不充分——必须用分页模式 + 对照旧数据 diff。

build_run_input 现在默认(signalboard/scraper.py):
- sort=Latest
- disableMaximization=True(关键:强制显式分页,不让 actor 自己 maximize)
- maxItems=3000(硬 cap)

如果换 actor(ACTOR_ID 变)或升级 apidojo 版本,务必先跑基准测试(tests/test_pagination_modes.py)
确认新模式稳定再重抓生产 db。

### ⚠️ 首次使用前必读

`default_field_map()` 里的字段名是按 Twitter API V2 + apidojo 常见命名约定的**最佳猜测**。真实响应字段名以首次 `--record 1` 的输出为准:

```bash
export APIFY_TOKEN=...
python -m signalboard.scraper --handle aleabitoreddit --record 1
# → fixtures/tweet_response_sample.json
# 打开看,如果字段名不同(比如 actor 用了 'tweet_id' 而不是 'id'),
#   改 signalboard/scraper.py 的 default_field_map() 校准,
#   然后跑 tests/test_scraper.py 确认 mock 测试通过。
```

### 费用估算(apidojo/tweet-scraper V2,**$0.40 / 1000 tweets**)

按 Apify 页面实价(pay per result, $0.40 / 1k):

| 场景 | 推文数 | 费用 |
|---|---|---|
| `--record 1` 校准 | 1 | ~$0.0004 |
| `scrape_real_smoke.py` 冒烟(20 条/月 × 1 月) | 20 | ~$0.008 |
| 单源 6 月 × ~300 条/月(普通活跃账号) | 1,800 | ~$0.72 |
| 单源 12 月 × ~300 条/月 | 3,600 | ~$1.44 |
| 单源 12 月 × ~3,000 条/月(高频账号) | 36,000 | ~$14.40 |
| 20 源 × 12 月 × ~300 条/月(Phase 2 起步) | 72,000 | ~$28.80 |
| 100 源 × 12 月 × ~300 条/月(规模化) | 360,000 | ~$144.00 |

> 💡 上面按月均 300 条估算;高频账号(财经/科技大 V)可达 1k~3k 条/月,按比例放大费用。

**省钱 tip**:
- `--max-per-month` 显式设小(20~300)够 Phase 1 试跑;Phase 2 提到 1000
- `use_cache=True` + `.cache/` 目录别删,重跑相同月份零成本
- 断点续抓 + 细分都是"做一次就够,不会重复扣费"的设计
- 异常月(`coverage` 报告里 0 条 / 异常低)人工抽查,可能那个月本来就没发推,不需要重抓

### 验收 checklist

- **同一 handle 跑两遍,raw_posts 行数不变**:
  ```bash
  python -m signalboard.scraper --handle X
  sqlite3 data/signalboard.db "SELECT count(*) FROM raw_posts WHERE source_id='tw_X'"
  python -m signalboard.scraper --handle X   # 第二次
  sqlite3 data/signalboard.db "SELECT count(*) FROM raw_posts WHERE source_id='tw_X'"  # 应相同
  ```

- **随机抽 10 条,raw_text 与推特网页原文一致**:
  ```bash
  sqlite3 data/signalboard.db "SELECT post_id, raw_text, raw_url FROM raw_posts ORDER BY RANDOM() LIMIT 10"
  ```
  对照 https://x.com/{handle}/status/{post_id} 检查。

- **检查覆盖率报告**:
  ```bash
  python -m signalboard.scraper coverage --handle X
  ```
  per-month 表里看 WARNING 行,0 条或异常低的月份人工确认。

- **中断后续抓**:
  1. 第一次跑时 `Ctrl+C`(`scrape_state` 写盘了)
  2. 第二次 `python -m signalboard.scraper --handle X`(从断点继续,不重抓已完成的月份)
  3. `sqlite3 data/signalboard.db "SELECT * FROM scrape_state WHERE handle='X'"` 确认进度
  4. 细分后的子窗口不会重新调 API(被 cache 复用)

## 跑测试

```bash
# 全部 mock 测试,无费用
python tests/test_smoke.py        # 25 个数据层
python tests/test_scraper.py     # 39 个抓取层
```

## 文件结构

```
signalboard/
├── __init__.py
├── __main__.py            # 支持 python -m signalboard scraper ...
├── models.py
├── db.py
├── repository.py
└── scraper.py
tests/
├── test_smoke.py          # 25 个
└── test_scraper.py        # 39 个
fixtures/
└── tweet_response_sample.json  # synth 样例(mock 测试用;真实以 --record 为准)
scripts/
└── scrape_real_smoke.py   # 真实小规模冒烟(默认不跑,会扣费)
attachments/
└── 170aab25__51ad8b58-d992-4390-9dec-ba86076c0f1e.md  # 设计文档
```
