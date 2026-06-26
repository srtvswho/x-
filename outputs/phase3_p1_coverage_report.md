# Phase 3 P3-1: Finnhub Quote 覆盖率摸底

**运行时间**: 2026-06-15 04:02:54 UTC
**耗时**: 1219s (20.3min)
**数据源**: Finnhub `/quote` 端点(Free tier)
**节流**: 1.05s/req (60 req/min)

## ⚠️ 重要限制

**Finnhub Free tier 禁 `/stock/candle` 端点**(全 403:1/5/15/30/60/D/W/M resolution)。
本次覆盖率**只验证 ticker 存在 + 当前报价**(`/quote` 端点),
**不等同于能拉历史日线**。

P3-2 实际拉日线时,需另选数据源:
- **Polygon.io Free**: 5 req/min,日线 OK(推荐)
- **eodhd.com Free**: 20/day,日线 OK
- **Tiingo Free**: 50/hour,日线 OK

## 1. 总体

- predictions 总数 (ticker 非空): 4470
- unique (ticker, market): 516
- Finnhub quote 可达: **368/516 ticker** (71.3%)
- 不可达: 148 ticker (含 429 限流 0)
- market='NONE' 不可查: 0 ticker (0 pred)


- 可达 predictions: **3389/4470** (75.8%)
- 不可达: 1081/4470 (24.2%)

## 2. 美股 vs 非美股

| 区域 | predictions | 可达 | 覆盖率 |
|---|---|---|---|
| **美股 + 美股 ETF + OTC** | 4081 | 3389 | 83.0% |
| **非美股 (SE/TW/KR/JP/A股/欧/加密/商品)** | 389 | 0 | 0.0% |

## 3. 按 market 分层覆盖率

| market | predictions | 唯一 ticker | quote 可达 ticker | 覆盖率 |
|---|---|---|---|---|
| 美股 | 4081 | 428 | 368 | ticker 86% / pred 83% |
| TW | 164 | 32 | 0 | ticker 0% / pred 0% |
| KR | 93 | 4 | 0 | ticker 0% / pred 0% |
| JP | 57 | 21 | 0 | ticker 0% / pred 0% |
| crypto | 21 | 5 | 0 | ticker 0% / pred 0% |
| A股 | 18 | 9 | 0 | ticker 0% / pred 0% |
| commodity | 12 | 7 | 0 | ticker 0% / pred 0% |
| SE | 8 | 1 | 0 | ticker 0% / pred 0% |
| 未上市 | 7 | 1 | 0 | ticker 0% / pred 0% |
| 欧洲 | 4 | 4 | 0 | ticker 0% / pred 0% |
| CA | 3 | 2 | 0 | ticker 0% / pred 0% |
| ASX | 1 | 1 | 0 | ticker 0% / pred 0% |
| LSE | 1 | 1 | 0 | ticker 0% / pred 0% |

## 4. fail 原因分布

| reason | ticker 数 |
|---|---|
| `http_403` | 80 |
| `no_quote_data` | 68 |

## 5. unresolved_price 清单(Finnhub quote 不可达)

**总计 148 ticker 不可达** (按 n_pred 降序前 50):

| ticker | market | n_pred | reason |
|---|---|---|---|
| SIVE | 美股 | 338 | no_quote_data |
| SOI | 美股 | 70 | no_quote_data |
| 000660.KS | KR | 54 | http_403 |
| IQE | 美股 | 50 | no_quote_data |
| 6451.TW | TW | 43 | http_403 |
| 005930.KS | KR | 37 | http_403 |
| 3105.TW | TW | 28 | http_403 |
| LTC | 美股 | 27 | http_403 |
| RPI | 美股 | 21 | no_quote_data |
| SOI.PA | JP | 19 | http_403 |
| XFAB | 美股 | 18 | no_quote_data |
| ETH | 美股 | 17 | http_403 |
| LPK | 美股 | 17 | no_quote_data |
| 3363.TW | TW | 16 | http_403 |
| HPS.A | 美股 | 16 | no_quote_data |
| BTC | crypto | 14 | http_403 |
| ALRIB | 美股 | 11 | no_quote_data |
| 8147.TW | TW | 9 | http_403 |
| ASHM | 美股 | 9 | no_quote_data |
| BTC | 美股 | 9 | http_403 |
| FOCI | 美股 | 8 | no_quote_data |
| SIVE | SE | 8 | http_403 |
| TOWA | 美股 | 8 | no_quote_data |
| 3081.TW | TW | 7 | http_403 |
| SOL | 美股 | 7 | http_403 |
| 私募 | 未上市 | 7 | no_quote_data |
| 3037.TW | TW | 6 | http_403 |
| 5801.T | JP | 6 | http_403 |
| 2408.TW | TW | 5 | http_403 |
| 2454.TW | TW | 5 | http_403 |
| 6488.TW | TW | 5 | http_403 |
| 8053.T | JP | 5 | http_403 |
| CREDO | 美股 | 5 | no_quote_data |
| 2337.TW | TW | 4 | http_403 |
| 3661.TW | TW | 4 | http_403 |
| 688017 | A股 | 4 | no_quote_data |
| 688017.SH | A股 | 4 | no_quote_data |
| MVZ.B | 美股 | 4 | no_quote_data |
| VNP | 美股 | 4 | no_quote_data |
| 2344.TW | TW | 3 | http_403 |
| 300308.SZ | A股 | 3 | http_403 |
| 3110.TW | TW | 3 | http_403 |
| 5360.T | JP | 3 | http_403 |
| 5802.T | JP | 3 | http_403 |
| 8299.TW | TW | 3 | http_403 |
| ETH | crypto | 3 | http_403 |
| GRZ.V | 美股 | 3 | http_403 |
| MVZ.A | 美股 | 3 | no_quote_data |
| SKC | 美股 | 3 | no_quote_data |
| silver | commodity | 3 | no_quote_data |

(还有 98 个,见 DB price_coverage 表)

## 6. 第一版验证范围建议

基于 Finnhub quote 覆盖率摸底:
- **第一版只验美股 (含 OTC/ETF)**: 3389 predictions,覆盖率 83.0%
- 第一版**跳过**所有非美股 (TW/KR/JP/A股/欧洲等),单列 `validation_status=skipped_non_us`
- 第一版**跳过** Finnhub 不可达 ticker,进 `unresolved_price`

**P3-2 数据源决策**:
- 方案 A: 用 Polygon 5 req/min 1.7h 拉美股历史,跳过非美股
- 方案 B: 用 Tiingo 50/h 10.3h 拉美股 + 欧洲(更全)
- 方案 C: 第一版只跑美股 quote-based 验证(快速但不完整)