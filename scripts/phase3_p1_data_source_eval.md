# Phase 3 P3-1: 数据源选择评估

## 现状(2026-06-15 03:30)

**Yahoo Finance(yfinance) 全面限流沙箱 IP**

| 测试 | 状态 |
|---|---|
| yfinance `Ticker('IBM').history(period='5d')` | ❌ `YFRateLimitError: Too Many Requests` |
| 直接 curl `query1.finance.yahoo.com/v8/finance/chart/AAPL` | ❌ HTTP 429 |
| 直接 curl `query2.finance.yahoo.com/v8/finance/chart/AAPL` | ❌ "Edge: Too Many Requests" |
| 4 次退避重试(5s/15s/45s/135s) | ❌ 全 429,IP 级 ban |
| stooq.com (CSRF JS challenge) | ❌ 需浏览器验证 |
| alphavantage (demo key) | ⚠️ 通,但 5 req/min + 25 req/day 限额 |
| polygon.io (无 key) | ⚠️ 通端点,但需 API key |
| finnhub.io (无 key) | ⚠️ 通端点,但需 token |

**结论:Yahoo 全端点 ban 沙箱出口 IP,无解。必须换数据源。**

## 候选数据源(用户选 1 个)

### A. Polygon.io Free Tier(推荐)
- **注册**: https://polygon.io/ → 邮箱 → Dashboard 拿 API key
- **限制**: 5 req/min,美股为主,日线 end-of-day
- **覆盖**: 美股 ✓ / ETF ✓ / 加密 ✓ / forex △(美股主导)
- **不覆盖**: TW / KR / JP / A股 / 港股 等亚欧市场
- **预估**: 515 ticker / 5 req/min = 1.7 小时跑完,US 主标的可覆盖 ~80%
- **优点**: 历史数据全,日线 EOD 可用
- **缺点**: 美股 80%,亚欧市场需 fallback

### B. Finnhub.io Free Tier
- **注册**: https://finnhub.io/ → 邮箱 → 拿 API token
- **限制**: 60 req/min(很宽),美股 + 港股 + 部分欧股
- **覆盖**: 美股 ✓ / 港股 ✓ / 加拿大 △ / TW △
- **预估**: 515 ticker / 60 req/min = 8.5 分钟跑完
- **优点**: 限速宽松
- **缺点**: 日线数据只有 1 年 (Free tier 限制),亚欧市场也不全

### C. Tiingo Free Tier
- **注册**: https://tiingo.com/ → 邮箱 → 拿 token
- **限制**: 50 req/hour(≈ 0.83 req/min),500 unique symbols/day
- **覆盖**: 美股 ✓ / 部分 ETF
- **预估**: 515 / 50 per hour = 10.3 小时
- **优点**: 数据质量好,含 fundamentals
- **缺点**: 限速最严,跑 1 天以上

### D. Alpha Vantage(备选)
- **注册**: https://www.alphavantage.co/support/#api-key
- **限制**: 25 req/day
- **预估**: 515 / 25 = 21 天跑完 ❌ 不可行
- **优点**: 不需 email
- **缺点**: **限速太低,跑不完**

### E. 全部降级
- 仅做"覆盖可查"的子集(如只查美股 4081 条 + 简单日线)
- 牺牲覆盖率换时间
- 推荐:**先用 Polygon 美股试 1 小时看通不通**

## 我建议

**Polygon.io Free Tier**:
- 5 req/min 是最严限制,但 Yahoo 失败时**只有它是 end-of-day 数据 + 限速可接受**
- 亚欧市场先标 `unresolved_price`,进单独立报告
- 用户用 5 分钟注册 + 拿 key,给我即可

## 备选:用户提供 API key 后我做什么

1. 改 `resolve_symbol` 把 ticker → Polygon 符号 (大部分美股同名,TW 加 `.TW` 不行要用专用格式)
2. 改 `check_symbol` 用 `requests` 直接打 polygon
3. 5 req/min 节流,断点续跑,缓存日线到 `data/price_cache/`
4. 报告分两层:
   - **可达 (Polygon OK)**: Polled with raw OHLC + reason
   - **不可达 (Polygon not covered)**: market 分组 + 标注

## 立即可做(不需数据源)

- ✅ market_config 写好(已落 `scripts/phase3_p1_coverage.py`)
- ✅ ticker→yfinance 解析逻辑写好 (改 resolve_symbol 适配 polygon 仅需 5-10 行)
- ✅ price_coverage 表 schema 写好
- ✅ 覆盖率报告骨架写好
- ⏸ **数据获取层阻塞,需用户给 key**
