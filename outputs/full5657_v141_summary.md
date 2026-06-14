# 全量 5657 条 v1.4.1 抽取汇总报告

**运行时间**: 20260614_080150  
**总耗时**: 5314s (88.6min)  
  - Phase 1 (LLM call, 3 workers): 4033s
  - Phase 2 (1 线程批入库): 1246s
**Prompt Version**: deepseek:deepseek-v4-pro:v1.4.1  
**Model**: deepseek-v4-pro

## 1. 处理统计

| 项 | 值 |
|---|---|
| raw_posts 总数 | 6354 |
| 预过滤通过 | 5657 (89.0%) |
| 预过滤跳过 | 697 |
| 实际处理 | 5657 |
| 成功 (LLM OK) | 5657 |
| 失败 (parse/exception) | 0 |
| parse_error (LLM 返但 JSON 错) | 0 |
| LLM 实际吞吐 | 1.40 条/s |

## 2. 预测统计

| 项 | 值 |
|---|---|
| has_prediction=true | 2057 (36.4%) |
| has_prediction=false | 3600 (63.6%) |
| 总 PredictionRecord (LLM 抽) | 4507 |
| 平均 records/post (有预测) | 2.19 |
| 落库 is_repeat_call | 3856 |

### Claim Type 分布
- `directional`: 4120
- `quantitative`: 291
- `thematic`: 95
- `event_driven`: 1

### Conviction 分布
- `1`: 5
- `2`: 1693
- `3`: 1938
- `4`: 766
- `5`: 105

### Flag 类型计数
- `position_disclosure`: 506
- `victory_lap`: 212
- `self_reported_returns`: 79
- `influence_milestone`: 21
- `paid_promotion_disclosure`: 5
- `solicitation`: 1

### Ticker Top 30
- `NBIS`: 362
- `SIVE`: 342
- `AAOI`: 189
- `AXTI`: 157
- `LITE`: 106
- `IREN`: 98
- `CIFR`: 79
- `TSM`: 78
- `SOI`: 76
- `HIMS`: 66
- `RKLB`: 63
- `RDDT`: 61
- `COHR`: 59
- `AEHR`: 52
- `MU`: 51
- `IQE`: 50
- `MRVL`: 48
- `META`: 46
- `CRWV`: 43
- `TSEM`: 41
- `SK Hynix`: 40
- `ALAB`: 40
- `CRCL`: 40
- `WULF`: 40
- `AMZN`: 39
- `SNAP`: 38
- `SMCI`: 36
- `AMD`: 33
- `Shunsin`: 29
- `CRDO`: 29

(还有 564 个 ticker)

### Market 分布
- `美股`: 3404
- `SE`: 344
- `OTC`: 265
- `TW`: 175
- `KRX`: 74
- `crypto`: 71
- `JP`: 35
- `LSE`: 29
- `KR`: 22
- `A股`: 17
- `commodity`: 15
- `CA`: 5
- `TYO`: 5
- `thematic`: 5
- `国际`: 5
- `private`: 4
- `unknown`: 3
- `TSX`: 2
- `未上市`: 2
- `Japan`: 2
- `Korea`: 2
- `ASX`: 2
- `sector`: 2
- `broad_market`: 2
- `英国`: 2
- `unresolved`: 2
- `欧洲`: 2
- `TSE`: 1
- `TYSE`: 1
- `德国`: 1
- `日本`: 1
- `韩国`: 1
- `ETF`: 1
- `JPX`: 1
- `EPA`: 1
- `FR`: 1

## 3. 错误明细

失败数: 0

无错误

## 4. 未解析 ticker(unresolved)

human_review_queue `unresolved_ticker` 总条数: **2099**

涉及 distinct post_id: **913**

### 按 raw_mention 分布(Top 50)
- `IREN`: 98
- `CIFR`: 79
- `RDDT`: 61
- `MU`: 50
- `SK Hynix`: 43
- `CRWV`: 43
- `WULF`: 40
- `ALAB`: 40
- `SNAP`: 37
- `SMCI`: 36
- `AMD`: 33
- `VLN`: 29
- `NVDA`: 29
- `CRDO`: 29
- `WLAC`: 28
- `Samsung`: 27
- `LTC`: 27
- `FLNC`: 25
- `POET`: 24
- `ETOR`: 23
- `FLY`: 22
- `UPWK`: 21
- `Win Semi`: 20
- `ORCL`: 19
- `XFAB`: 18
- `WYFI`: 18
- `Soitec`: 17
- `ETH`: 17
- `SG`: 16
- `LPK`: 16
- `HPS.A`: 16
- `LASR`: 15
- `AIRO`: 15
- `UNH`: 13
- `GLXY`: 13
- `VIRT`: 12
- `TSSI`: 12
- `TGT`: 12
- `BMNR`: 12
- `SLNH`: 11
- `KRKNF`: 11
- `Sk Hynix`: 10
- `Samsung Electronics`: 10
- `RGTI`: 10
- `QBTS`: 10
- `MTSI`: 10
- `MSTR`: 10
- `TTD`: 9
- `TSLA`: 9
- `LULU`: 9

## 5. Token 用量 & 实际费用

| 项 | 值 |
|---|---|
| 累计 prompt_tokens | 23,892,087 |
| 累计 completion_tokens | 703,256 |
| 累计 total_tokens | 24,595,343 |
| 输入价 (per 1M) | $0.27 |
| 输出价 (per 1M) | $1.10 |
| **实际总费用** | **$7.2244** |
| 之前 200-sample 估算 | $5.18 |
| 实际 vs 估算 | 139.5% |
| 平均每条费用 | $1.2771¢ |

## 6. 落库验证

| 表 | 行数 |
|---|---|
| predictions | 4499 (2057 distinct post_id) |
| post_flags | 824 |
| human_review_queue (unresolved_ticker) | 2099 |
| human_review_queue (all) | 2099 |
| extraction_cache | 5657 |
| 唯一 prompt_version | ['deepseek:deepseek-v4-pro:v1.4.1'] |
