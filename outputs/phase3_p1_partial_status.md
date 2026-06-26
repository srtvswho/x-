# Phase 3 P3-1 部分状态报告

**时间**: 2026-06-15 03:30 UTC  
**任务**: 行情覆盖率测试(数据源选型前)

## 结论先行

**Yahoo Finance 全面限流沙箱 IP**:`YFRateLimitError` 在 4 次退避(5s/15s/45s/135s)后仍持续 429。Yahoo 全部端点(query1/query2, /v7/v8)均 ban 沙箱出口 IP。

**当前 P3-1 状态:阻塞在数据源选型**,需要用户选 1 个候选 API 提供 key 后我才能继续。

## 数据源评估

| 候选 | 注册 | 限速 | 覆盖 | 预计 515 ticker 用时 | 推荐 |
|---|---|---|---|---|---|
| **Polygon.io Free** | 1 分钟 | 5 req/min | 美股 + 加密 + ETF | 1.7 h | ⭐⭐⭐ |
| **Finnhub.io Free** | 1 分钟 | 60 req/min | 美股 + 港股 | 8.5 min | ⭐⭐ |
| **Tiingo Free** | 1 分钟 | 50/h | 美股 | 10.3 h | ⭐ |
| Alpha Vantage Free | 30 秒 | 5/min + 25/day | 美股为主 | 21 天 ❌ | ✗ |
| Stooq | 免注册 | 高 | 全球 | 不可用(JS challenge) | ✗ |

详细评估见 `scripts/phase3_p1_data_source_eval.md`。

## 已完成(不需数据源)

- ✅ **market_config**:`scripts/phase3_p1_coverage.py` 第 18-65 行,美股/SE/TW/KR/JP/LSE/CA/ASX/A股/commodity/crypto 等 14 个市场
- ✅ **ticker→yfinance symbol 解析**:`resolve_symbol()`(特殊 override + 数字 ticker 后缀 + market 默认后缀)
- ✅ **price_coverage 表 schema**:`(ticker, market, yfinance_symbol, n_predictions, last_close, last_date, rows_fetched, ok, reason)` PK=(ticker, market)
- ✅ **覆盖报告骨架**:按 market 分层 + top 10 failed + unverifiable 清单
- ✅ **Polygon 备用脚本**:`scripts/phase3_p1_polygon_coverage.py`(5 req/min 节流,等用户给 POLYGON_API_KEY)

## 待做(需要 API key)

- [ ] 真实数据获取 + 覆盖率验证
- [ ] 517 ticker 中实际可查数(预期 70-80% 美股主标的可覆盖)
- [ ] 市场分层不可达清单(亚欧市场大概率多归此类)

## 建议路径

1. **用户去 https://polygon.io/ 注册 → 拿 free API key**(1 分钟)
2. 给我 API key,跑 `POLYGON_API_KEY=xxx python scripts/phase3_p1_polygon_coverage.py`
3. 1.7 小时后输出真实覆盖率报告
4. 进入 P3-2(单条验证函数)+ P3-3(记分牌)

## 备选快速路径

如果不想等 1.7 小时,可用 **Finnhub**(8.5 分钟),但日线数据只有 1 年 — 可能不够覆盖 14 月数据。

**等待用户决策**。
