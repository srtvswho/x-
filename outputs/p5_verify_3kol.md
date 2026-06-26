# 3 KOL 完整胜率验证 (P5-9 v3 — 修日期解析)

**生成时间**: 2026-06-25 03:38
**过滤链**: ORIGINAL → LLM 抽 direction → keep long/short → 90d 验证
**数据截止**: 2026-06-22  
**默认 horizon**: 90d  
**基准**: SPY / SOXX / QQQ
**已淘汰**: @TradexWhisperer (简介自吹 vs 实际不符)

**纪律**: 不下'可不可跟'结论, 三人一起给, 等你对照看 (尤其会拿市场常识查可疑数字).

---

## @amitisinvesting

### 数据

- ORIGINAL 总判断: 156
- LLM 抽完有方向 (long/short): 46
- 已验证 (90d 窗口, 数据截止 2026-06-22): 45
- Pending (entry > 2026-04-01, 90d 还没到期): 41
- Unresolved: {'no_px entry=2026-05-25 exit=2026-06-22': 1}

### 核心: raw 选股命中率 (不依赖基准)

- n_resolved: **45**
- raw 涨 (raw>0): **17**
- raw 跌 (raw<0): 24
- **raw_hit_rate: 37.8%**
- median_raw: **-0.8%**
- mean_raw: -0.9%

### Excess vs Benchmarks

| Bench | n | med_excess | mean_excess | hit_rate |
|---|---|---|---|---|
| SPY | 4 | +20.5% | +20.8% | 75.0% |
| SOXX | 4 | +8.7% | +6.1% | 75.0% |
| QQQ | 4 | +19.7% | +20.6% | 75.0% |

### 置信度: **D** (raw_hit 37.8%, n=45)

### 能力圈 (ticker, n≥1 预测, 按 n 倒序)

| ticker | n | raw_hit | med_raw | med_excess_soxx |
|---|---|---|---|---|
| META | 7 | 0.0% | -7.9% | +0.0% |
| NVDA | 5 | 0.0% | -0.8% | -26.6% |
| IREN | 4 | 50.0% | +0.0% | +0.0% |
| TSLA | 4 | 75.0% | +24.8% | +17.0% |
| RDDT | 4 | 75.0% | +17.8% | +0.0% |
| PLTR | 3 | 0.0% | -18.2% | +0.0% |
| SHOP | 2 | 50.0% | -0.5% | +0.0% |
| HOOD | 2 | 50.0% | -1.9% | +0.0% |
| MSFT | 2 | 0.0% | -11.3% | +0.0% |
| GEV | 1 | 0.0% | +0.0% | +0.0% |
| SPCX | 1 | 0.0% | -19.7% | +0.0% |
| IGV | 1 | 0.0% | -18.9% | +0.0% |
| SNAP | 1 | 0.0% | -19.5% | +0.0% |
| BB | 1 | 100.0% | +4.4% | +0.0% |
| TE | 1 | 100.0% | +19.3% | +0.0% |
| INTC | 1 | 100.0% | +16.9% | +0.0% |
| GLW | 1 | 100.0% | +1.2% | +0.0% |
| MU | 1 | 0.0% | -52.3% | +0.0% |
| AMD | 1 | 100.0% | +21.2% | +0.0% |
| AAPL | 1 | 100.0% | +7.3% | +0.0% |

### 4 分类

#### 4.1 raw 真赢 (17 条, 按 raw 倒序)

| ticker | dir | entry → exit | raw | excess_spy | excess_soxx |
|---|---|---|---|---|---|
| TSLA | long | 2025-07-06 → 2025-10-04 | +54.2% | +46.0% | +33.4% |
| HOOD | long | 2026-05-27 → 2026-06-22 | +38.7% | +0.0% | +0.0% |
| TSLA | long | 2025-07-19 → 2025-10-17 | +33.7% | +28.1% | +17.0% |
| AMD | long | 2026-05-08 → 2026-06-22 | +21.2% | +0.0% | +0.0% |
| TE | long | 2026-05-21 → 2026-06-22 | +19.3% | +0.0% | +0.0% |
| RDDT | long | 2026-05-26 → 2026-06-22 | +17.8% | +0.0% | +0.0% |
| RDDT | long | 2026-05-26 → 2026-06-22 | +17.8% | +0.0% | +0.0% |
| RDDT | long | 2026-05-26 → 2026-06-22 | +17.8% | +0.0% | +0.0% |
| INTC | long | 2026-05-12 → 2026-06-22 | +16.9% | +0.0% | +0.0% |
| TSLA | long | 2025-09-15 → 2025-12-14 | +15.9% | +12.9% | +0.3% |
| AAPL | long | 2026-05-03 → 2026-06-22 | +7.3% | +0.0% | +0.0% |
| NOW | long | 2026-04-29 → 2026-06-22 | +4.6% | +0.0% | +0.0% |
| BB | long | 2026-05-25 → 2026-06-22 | +4.4% | +0.0% | +0.0% |
| SHOP | long | 2026-05-26 → 2026-06-22 | +2.9% | +0.0% | +0.0% |
| GLW | long | 2026-05-11 → 2026-06-22 | +1.2% | +0.0% | +0.0% |
| IREN | long | 2026-05-07 → 2026-06-22 | +0.0% | +0.0% | +0.0% |
| IREN | long | 2026-05-07 → 2026-06-22 | +0.0% | +0.0% | +0.0% |

#### 4.2 raw 真输 (24 条, 按 raw 升序)

| ticker | dir | entry → exit | raw | excess_spy | excess_soxx |
|---|---|---|---|---|---|
| MU | short | 2026-05-11 → 2026-06-22 | -52.3% | +0.0% | +0.0% |
| HOOD | short | 2026-05-19 → 2026-06-22 | -42.5% | +0.0% | +0.0% |
| PLTR | long | 2026-05-30 → 2026-06-22 | -25.6% | +0.0% | +0.0% |
| SPCX | long | 2026-06-14 → 2026-06-22 | -19.7% | +0.0% | +0.0% |
| SNAP | long | 2026-05-25 → 2026-06-22 | -19.5% | +0.0% | +0.0% |
| IGV | long | 2026-05-31 → 2026-06-22 | -18.9% | +0.0% | +0.0% |
| PLTR | long | 2026-05-03 → 2026-06-22 | -18.2% | +0.0% | +0.0% |
| PLTR | long | 2026-05-21 → 2026-06-22 | -13.0% | +0.0% | +0.0% |
| MSFT | long | 2026-05-08 → 2026-06-22 | -11.5% | +0.0% | +0.0% |
| MSFT | long | 2026-05-03 → 2026-06-22 | -11.2% | +0.0% | +0.0% |
| TSLA | long | 2026-05-11 → 2026-06-22 | -9.0% | +0.0% | +0.0% |
| META | long | 2026-05-15 → 2026-06-22 | -8.2% | +0.0% | +0.0% |
| META | long | 2026-05-26 → 2026-06-22 | -7.9% | +0.0% | +0.0% |
| META | long | 2026-05-24 → 2026-06-22 | -7.9% | +0.0% | +0.0% |
| META | long | 2026-05-24 → 2026-06-22 | -7.9% | +0.0% | +0.0% |
| META | long | 2026-05-22 → 2026-06-22 | -7.6% | +0.0% | +0.0% |
| META | long | 2026-05-21 → 2026-06-22 | -7.2% | +0.0% | +0.0% |
| NVDA | long | 2026-05-20 → 2026-06-22 | -6.6% | +0.0% | +0.0% |
| META | long | 2026-06-01 → 2026-06-22 | -6.1% | +0.0% | +0.0% |
| NVDA | long | 2026-05-19 → 2026-06-22 | -5.4% | +0.0% | +0.0% |

#### 4.3 跑赢 SOXX (按 excess_soxx 倒序)

| ticker | dir | entry → exit | raw | excess_soxx |
|---|---|---|---|---|
| TSLA | long | 2025-07-06 → 2025-10-04 | +54.2% | +33.4% |
| TSLA | long | 2025-07-19 → 2025-10-17 | +33.7% | +17.0% |
| TSLA | long | 2025-09-15 → 2025-12-14 | +15.9% | +0.3% |
| NVDA | long | 2026-06-21 → 2026-06-22 | +0.0% | +0.0% |
| GEV | long | 2026-06-21 → 2026-06-22 | +0.0% | +0.0% |
| IREN | long | 2026-06-21 → 2026-06-22 | +0.0% | +0.0% |
| NVDA | long | 2026-06-21 → 2026-06-22 | +0.0% | +0.0% |
| SHOP | long | 2026-06-15 → 2026-06-22 | -4.0% | +0.0% |
| SPCX | long | 2026-06-14 → 2026-06-22 | -19.7% | +0.0% |
| META | long | 2026-06-01 → 2026-06-22 | -6.1% | +0.0% |

#### 4.4 跑输 SOXX (按 excess_soxx 升序)

| ticker | dir | entry → exit | raw | excess_soxx |
|---|---|---|---|---|
| NVDA | long | 2025-11-19 → 2026-02-17 | -0.8% | -26.6% |
| NVDA | long | 2026-06-21 → 2026-06-22 | +0.0% | +0.0% |
| GEV | long | 2026-06-21 → 2026-06-22 | +0.0% | +0.0% |
| IREN | long | 2026-06-21 → 2026-06-22 | +0.0% | +0.0% |
| NVDA | long | 2026-06-21 → 2026-06-22 | +0.0% | +0.0% |
| SHOP | long | 2026-06-15 → 2026-06-22 | -4.0% | +0.0% |
| SPCX | long | 2026-06-14 → 2026-06-22 | -19.7% | +0.0% |
| META | long | 2026-06-01 → 2026-06-22 | -6.1% | +0.0% |
| IGV | long | 2026-05-31 → 2026-06-22 | -18.9% | +0.0% |
| RDDT | long | 2026-05-30 → 2026-06-22 | -4.2% | +0.0% |

### 全部 45 条已验证 (逐条, 给你对照看)

| # | entry | exit | ticker | dir | raw | exc_spy | exc_soxx | exc_qqq | thesis |
|---|---|---|---|---|---|---|---|---|---|
| 1 | 2026-06-21 | 2026-06-22 | NVDA | long | +0.0% | +0.0% | +0.0% | +0.0% | First pick ended up being $NVDA Nvidia! |
| 2 | 2026-06-21 | 2026-06-22 | GEV | long | +0.0% | +0.0% | +0.0% | +0.0% | I think can do well... may want to legit start a position |
| 3 | 2026-06-21 | 2026-06-22 | IREN | long | +0.0% | +0.0% | +0.0% | +0.0% | I do think IREN is cheap |
| 4 | 2026-06-21 | 2026-06-22 | NVDA | long | +0.0% | +0.0% | +0.0% | +0.0% | 这些是我必须持有到2027年6月的选择 |
| 5 | 2025-07-19 | 2025-10-17 | TSLA | long | +33.7% | +28.1% | +17.0% | +26.7% | I’ll be buying $TSLA before the Q2 print |
| 6 | 2025-07-06 | 2025-10-04 | TSLA | long | +54.2% | +46.0% | +33.4% | +44.1% | 认为 Musk 组党可能引发 TSLA 下跌，创造绝佳买入机会 |
| 7 | 2025-09-15 | 2025-12-14 | TSLA | long | +15.9% | +12.9% | +0.3% | +12.7% | ELON MUSK BUYS $TSLA STOCK ON THE OPEN MARKET |
| 8 | 2025-11-19 | 2026-02-17 | NVDA | long | -0.8% | -3.9% | -26.6% | -1.1% | most important $NVDA earnings, bullish |
| 9 | 2026-06-15 | 2026-06-22 | SHOP | long | -4.0% | +0.0% | +0.0% | +0.0% | Yes $SHOP is a buy in my opinion |
| 10 | 2026-06-14 | 2026-06-22 | SPCX | long | -19.7% | +0.0% | +0.0% | +0.0% | If you are right about that then $SPCX is pretty cheap |
| 11 | 2026-06-01 | 2026-06-22 | META | long | -6.1% | +0.0% | +0.0% | +0.0% | $META is a screaming buy |
| 12 | 2026-05-31 | 2026-06-22 | IGV | long | -18.9% | +0.0% | +0.0% | +0.0% | it may be time to buy the breakout, risk reward very strong |
| 13 | 2026-05-30 | 2026-06-22 | RDDT | long | -4.2% | +0.0% | +0.0% | +0.0% | $RDDT should be leaving the station and moving much higher |
| 14 | 2026-05-30 | 2026-06-22 | PLTR | long | -25.6% | +0.0% | +0.0% | +0.0% | Palantir should continue to gain momentum |
| 15 | 2026-05-27 | 2026-06-22 | HOOD | long | +38.7% | +0.0% | +0.0% | +0.0% | Really excited for this, agentic products accelerate long-te |
| 16 | 2026-05-26 | 2026-06-22 | META | long | -7.9% | +0.0% | +0.0% | +0.0% | 作者已持有$META |
| 17 | 2026-05-26 | 2026-06-22 | RDDT | long | +17.8% | +0.0% | +0.0% | +0.0% | I do think $RDDT can do better short term given how much sma |
| 18 | 2026-05-26 | 2026-06-22 | SHOP | long | +2.9% | +0.0% | +0.0% | +0.0% | this is probably the cheapest Shopify has looked rel |
| 19 | 2026-05-26 | 2026-06-22 | RDDT | long | +17.8% | +0.0% | +0.0% | +0.0% | any cheaper prices would continue to make it a compelling bu |
| 20 | 2026-05-26 | 2026-06-22 | RDDT | long | +17.8% | +0.0% | +0.0% | +0.0% | I bought $RDDT |
| 21 | 2026-05-25 | 2026-06-22 | SNAP | long | -19.5% | +0.0% | +0.0% | +0.0% | I feel it is probably an okay buy here |
| 22 | 2026-05-25 | 2026-06-22 | BB | long | +4.4% | +0.0% | +0.0% | +0.0% | $BB is exciting due to valuation, could see ripping |
| 23 | 2026-05-24 | 2026-06-22 | META | long | -7.9% | +0.0% | +0.0% | +0.0% | $META is cheap |
| 24 | 2026-05-24 | 2026-06-22 | META | long | -7.9% | +0.0% | +0.0% | +0.0% | Meta应能轻松扩展并变现这一渠道分发模式 |
| 25 | 2026-05-22 | 2026-06-22 | META | long | -7.6% | +0.0% | +0.0% | +0.0% | LONG $META |
| 26 | 2026-05-21 | 2026-06-22 | TE | long | +19.3% | +0.0% | +0.0% | +0.0% | feet pics for more $TE shares isnt a bad deal… |
| 27 | 2026-05-21 | 2026-06-22 | PLTR | long | -13.0% | +0.0% | +0.0% | +0.0% | our beloved $PLTR paytience pays |
| 28 | 2026-05-21 | 2026-06-22 | META | long | -7.2% | +0.0% | +0.0% | +0.0% | I think $META is a great buy here. |
| 29 | 2026-05-20 | 2026-06-22 | NVDA | long | -6.6% | +0.0% | +0.0% | +0.0% | YES SIR IT’S $NVDA DAY |
| 30 | 2026-05-19 | 2026-06-22 | NVDA | long | -5.4% | +0.0% | +0.0% | +0.0% | there is no way Nvidia doesn’t demolish earnings...how big t |
| 31 | 2026-05-19 | 2026-06-22 | HOOD | short | -42.5% | +0.0% | +0.0% | +0.0% | $HOOD is going to have issues until $BTC turns around. |
| 32 | 2026-05-15 | 2026-06-22 | META | long | -8.2% | +0.0% | +0.0% | +0.0% | Buy $META and just not look at it for the next few years and |
| 33 | 2026-05-12 | 2026-06-22 | INTC | long | +16.9% | +0.0% | +0.0% | +0.0% | $INTC to $1T has to be the thesis |
| 34 | 2026-05-11 | 2026-06-22 | GLW | long | +1.2% | +0.0% | +0.0% | +0.0% | I’d be VERY happy to buy it 20% lower |
| 35 | 2026-05-11 | 2026-06-22 | MU | short | -52.3% | +0.0% | +0.0% | +0.0% | you should not give into the fomo, don’t chase a name |
| 36 | 2026-05-11 | 2026-06-22 | TSLA | long | -9.0% | +0.0% | +0.0% | +0.0% | $TSLA LOVES IT +2.5% |
| 37 | 2026-05-08 | 2026-06-22 | MSFT | long | -11.5% | +0.0% | +0.0% | +0.0% | MSFT will be back…just not now |
| 38 | 2026-05-08 | 2026-06-22 | AMD | long | +21.2% | +0.0% | +0.0% | +0.0% | bulls in control |
| 39 | 2026-05-07 | 2026-06-22 | IREN | long | +0.0% | +0.0% | +0.0% | +0.0% | IREN seems more bullish than not |
| 40 | 2026-05-07 | 2026-06-22 | IREN | short | -0.0% | +0.0% | +0.0% | +0.0% | that is always the bear case for these neocloud but $IREN ha |
| 41 | 2026-05-07 | 2026-06-22 | IREN | long | +0.0% | +0.0% | +0.0% | +0.0% | seems pretty bullish long term |
| 42 | 2026-05-03 | 2026-06-22 | AAPL | long | +7.3% | +0.0% | +0.0% | +0.0% | I think that winner, even after the run, is $AMZN |
| 43 | 2026-05-03 | 2026-06-22 | MSFT | long | -11.2% | +0.0% | +0.0% | +0.0% | $MSFT is cheap |
| 44 | 2026-05-03 | 2026-06-22 | PLTR | long | -18.2% | +0.0% | +0.0% | +0.0% | they will crush |
| 45 | 2026-04-29 | 2026-06-22 | NOW | long | +4.6% | +0.0% | +0.0% | +0.0% | I like $NOW, I don't think it should be this low |

---

## @StockSavvyShay

### 数据

- ORIGINAL 总判断: 333
- LLM 抽完有方向 (long/short): 76
- 已验证 (90d 窗口, 数据截止 2026-06-22): 70
- Pending (entry > 2026-04-01, 90d 还没到期): 62
- Unresolved: {'no_px entry=2026-06-20 exit=2026-06-22': 1, 'no_px entry=2026-06-09 exit=2026-06-22': 2, 'no_px entry=2026-06-07 exit=2026-06-22': 1, 'no_px entry=2026-05-30 exit=2026-06-22': 1, 'no_px entry=2026-05-21 exit=2026-06-22': 1}

### 核心: raw 选股命中率 (不依赖基准)

- n_resolved: **70**
- raw 涨 (raw>0): **22**
- raw 跌 (raw<0): 44
- **raw_hit_rate: 31.4%**
- median_raw: **-3.6%**
- mean_raw: -0.4%

### Excess vs Benchmarks

| Bench | n | med_excess | mean_excess | hit_rate |
|---|---|---|---|---|
| SPY | 8 | +12.3% | +11.6% | 75.0% |
| SOXX | 8 | +1.2% | -0.7% | 62.5% |
| QQQ | 8 | +11.5% | +11.6% | 75.0% |

### 置信度: **D** (raw_hit 31.4%, n=70)

### 能力圈 (ticker, n≥1 预测, 按 n 倒序)

| ticker | n | raw_hit | med_raw | med_excess_soxx |
|---|---|---|---|---|
| NVDA | 12 | 16.7% | -2.4% | -6.3% |
| NVTS | 5 | 0.0% | -23.2% | +0.0% |
| MU | 5 | 100.0% | +35.2% | +0.0% |
| PLTR | 4 | 0.0% | -13.5% | +0.0% |
| ONDS | 4 | 25.0% | -3.9% | +11.2% |
| NBIS | 3 | 66.7% | +7.2% | +0.0% |
| AMD | 3 | 100.0% | +9.5% | +0.0% |
| ALAB | 3 | 66.7% | +13.0% | +0.0% |
| MSFT | 3 | 0.0% | -16.8% | +0.0% |
| MELI | 3 | 0.0% | -3.0% | +0.0% |
| RKLB | 3 | 0.0% | -26.1% | +0.0% |
| TSLA | 2 | 50.0% | +13.8% | -0.9% |
| SPCX | 2 | 0.0% | -11.8% | +0.0% |
| ORCL | 2 | 0.0% | -11.1% | +0.0% |
| KTOS | 2 | 0.0% | -11.5% | +0.0% |
| IREN | 2 | 50.0% | +3.0% | +0.0% |
| ASTS | 2 | 0.0% | -24.6% | +0.0% |
| NU | 1 | 0.0% | +0.0% | +0.0% |
| AMZN | 1 | 100.0% | +5.5% | -4.8% |
| META | 1 | 100.0% | +12.4% | +0.1% |

### 4 分类

#### 4.1 raw 真赢 (22 条, 按 raw 倒序)

| ticker | dir | entry → exit | raw | excess_spy | excess_soxx |
|---|---|---|---|---|---|
| NVDA | long | 2025-04-07 → 2025-07-06 | +62.1% | +39.0% | +14.0% |
| ALAB | long | 2026-05-20 → 2026-06-22 | +52.9% | +0.0% | +0.0% |
| NBIS | long | 2026-05-23 → 2026-06-22 | +36.3% | +0.0% | +0.0% |
| MU | long | 2026-05-26 → 2026-06-22 | +35.2% | +0.0% | +0.0% |
| MU | long | 2026-05-26 → 2026-06-22 | +35.2% | +0.0% | +0.0% |
| MU | long | 2026-05-26 → 2026-06-22 | +35.2% | +0.0% | +0.0% |
| MU | long | 2026-05-26 → 2026-06-22 | +35.2% | +0.0% | +0.0% |
| MU | long | 2026-05-23 → 2026-06-22 | +35.2% | +0.0% | +0.0% |
| TSLA | long | 2025-04-23 → 2025-07-22 | +32.5% | +15.0% | -8.3% |
| ONDS | long | 2025-10-11 → 2026-01-09 | +26.6% | +22.0% | +11.2% |
| IREN | long | 2026-05-19 → 2026-06-22 | +19.1% | +0.0% | +0.0% |
| INTC | long | 2025-10-12 → 2026-01-10 | +18.4% | +13.5% | +2.4% |
| AMD | long | 2026-05-22 → 2026-06-22 | +18.0% | +0.0% | +0.0% |
| ALAB | long | 2026-06-15 → 2026-06-22 | +13.0% | +0.0% | +0.0% |
| META | long | 2025-11-01 → 2026-01-30 | +12.4% | +11.1% | +0.1% |
| AMD | long | 2026-05-26 → 2026-06-22 | +9.5% | +0.0% | +0.0% |
| NBIS | long | 2026-05-30 → 2026-06-22 | +7.2% | +0.0% | +0.0% |
| AMZN | long | 2025-10-05 → 2026-01-03 | +5.5% | +3.1% | -4.8% |
| OUST | long | 2026-06-02 → 2026-06-22 | +3.6% | +0.0% | +0.0% |
| CLPT | long | 2026-06-17 → 2026-06-22 | +1.5% | +0.0% | +0.0% |

#### 4.2 raw 真输 (44 条, 按 raw 升序)

| ticker | dir | entry → exit | raw | excess_spy | excess_soxx |
|---|---|---|---|---|---|
| ASTS | long | 2026-05-22 → 2026-06-22 | -30.9% | +0.0% | +0.0% |
| RKLB | long | 2026-05-23 → 2026-06-22 | -30.0% | +0.0% | +0.0% |
| RKLB | long | 2026-05-22 → 2026-06-22 | -26.1% | +0.0% | +0.0% |
| PLTR | long | 2026-05-31 → 2026-06-22 | -25.6% | +0.0% | +0.0% |
| NVTS | long | 2026-05-26 → 2026-06-22 | -25.4% | +0.0% | +0.0% |
| RKLB | long | 2026-05-20 → 2026-06-22 | -25.3% | +0.0% | +0.0% |
| NVTS | long | 2026-06-03 → 2026-06-22 | -23.2% | +0.0% | +0.0% |
| NVTS | long | 2026-06-03 → 2026-06-22 | -23.2% | +0.0% | +0.0% |
| NVTS | long | 2026-06-03 → 2026-06-22 | -23.2% | +0.0% | +0.0% |
| NVTS | long | 2026-06-03 → 2026-06-22 | -23.2% | +0.0% | +0.0% |
| SPCX | long | 2026-06-15 → 2026-06-22 | -19.7% | +0.0% | +0.0% |
| ASTS | long | 2026-05-20 → 2026-06-22 | -18.3% | +0.0% | +0.0% |
| ORCL | long | 2026-06-06 → 2026-06-22 | -17.3% | +0.0% | +0.0% |
| MSFT | long | 2026-06-02 → 2026-06-22 | -16.8% | +0.0% | +0.0% |
| MSFT | long | 2026-06-02 → 2026-06-22 | -16.8% | +0.0% | +0.0% |
| PLTR | long | 2026-06-04 → 2026-06-22 | -15.7% | +0.0% | +0.0% |
| IREN | long | 2026-06-03 → 2026-06-22 | -13.1% | +0.0% | +0.0% |
| KTOS | long | 2026-06-08 → 2026-06-22 | -11.5% | +0.0% | +0.0% |
| KTOS | long | 2026-06-08 → 2026-06-22 | -11.5% | +0.0% | +0.0% |
| PLTR | long | 2026-06-14 → 2026-06-22 | -11.3% | +0.0% | +0.0% |

#### 4.3 跑赢 SOXX (按 excess_soxx 倒序)

| ticker | dir | entry → exit | raw | excess_soxx |
|---|---|---|---|---|
| NVDA | long | 2025-04-07 → 2025-07-06 | +62.1% | +14.0% |
| ONDS | long | 2025-10-11 → 2026-01-09 | +26.6% | +11.2% |
| TSLA | long | 2024-07-08 → 2024-10-06 | -4.8% | +6.4% |
| INTC | long | 2025-10-12 → 2026-01-10 | +18.4% | +2.4% |
| META | long | 2025-11-01 → 2026-01-30 | +12.4% | +0.1% |
| NU | long | 2026-06-21 → 2026-06-22 | +0.0% | +0.0% |
| NBIS | long | 2026-06-21 → 2026-06-22 | +0.0% | +0.0% |
| PLTR | long | 2026-06-14 → 2026-06-22 | -11.3% | +0.0% |
| AMD | long | 2026-06-13 → 2026-06-22 | +0.8% | +0.0% |
| NVDA | long | 2026-06-13 → 2026-06-22 | -1.8% | +0.0% |

#### 4.4 跑输 SOXX (按 excess_soxx 升序)

| ticker | dir | entry → exit | raw | excess_soxx |
|---|---|---|---|---|
| NVDA | long | 2025-11-19 → 2026-02-17 | -0.8% | -26.6% |
| TSLA | long | 2025-04-23 → 2025-07-22 | +32.5% | -8.3% |
| AMZN | long | 2025-10-05 → 2026-01-03 | +5.5% | -4.8% |
| NU | long | 2026-06-21 → 2026-06-22 | +0.0% | +0.0% |
| NBIS | long | 2026-06-21 → 2026-06-22 | +0.0% | +0.0% |
| PLTR | long | 2026-06-14 → 2026-06-22 | -11.3% | +0.0% |
| AMD | long | 2026-06-13 → 2026-06-22 | +0.8% | +0.0% |
| NVDA | long | 2026-06-13 → 2026-06-22 | -1.8% | +0.0% |
| ALAB | long | 2026-06-20 → 2026-06-22 | +0.0% | +0.0% |
| ONDS | long | 2026-06-19 → 2026-06-22 | +0.0% | +0.0% |

### 全部 70 条已验证 (逐条, 给你对照看)

| # | entry | exit | ticker | dir | raw | exc_spy | exc_soxx | exc_qqq | thesis |
|---|---|---|---|---|---|---|---|---|---|
| 1 | 2026-06-21 | 2026-06-22 | NU | long | +0.0% | +0.0% | +0.0% | +0.0% | Colombia becomes NU's third major growth market, bullish sig |
| 2 | 2026-06-21 | 2026-06-22 | NBIS | long | +0.0% | +0.0% | +0.0% | +0.0% | 看好Nebius在AI推理工作负载中的定位，给出2030年目标价 |
| 3 | 2026-06-14 | 2026-06-22 | PLTR | long | -11.3% | +0.0% | +0.0% | +0.0% | 股票接近52周低点，股价受损但业务未受损，暗示低估 |
| 4 | 2026-06-13 | 2026-06-22 | AMD | long | +0.8% | +0.0% | +0.0% | +0.0% | Bullish: $AMD |
| 5 | 2026-06-13 | 2026-06-22 | NVDA | long | -1.8% | +0.0% | +0.0% | +0.0% | $NVDA is trading near its cheapest valuation in a decade |
| 6 | 2025-10-05 | 2026-01-03 | AMZN | long | +5.5% | +3.1% | -4.8% | +3.8% | AT ITS LOWEST VALUATION IN OVER A DECADE |
| 7 | 2025-04-23 | 2025-07-22 | TSLA | long | +32.5% | +15.0% | -8.3% | +9.0% | It's a leveraged call option |
| 8 | 2025-11-01 | 2026-01-30 | META | long | +12.4% | +11.1% | +0.1% | +14.0% | Bought the $META dip. |
| 9 | 2025-04-07 | 2025-07-06 | NVDA | long | +62.1% | +39.0% | +14.0% | +31.8% | THE FUTURE IS ON SALE RIGHT NOW IN OVERNIGHT TRADING |
| 10 | 2026-06-20 | 2026-06-22 | ALAB | long | +0.0% | +0.0% | +0.0% | +0.0% | 目前持有5%仓位 |
| 11 | 2026-06-19 | 2026-06-22 | ONDS | long | +0.0% | +0.0% | +0.0% | +0.0% | I first initiated $ONDS under $1 |
| 12 | 2025-10-12 | 2026-01-10 | INTC | long | +18.4% | +13.5% | +2.4% | +14.2% | Current exposure sits in $INTC for chip manufacturing |
| 13 | 2024-07-08 | 2024-10-06 | TSLA | long | -4.8% | -7.0% | +6.4% | -1.7% | THIS IS HUGE NEWS FOR $TSLA SHAREHOLDERS!!! THERE ARE RUMORS |
| 14 | 2025-11-19 | 2026-02-17 | NVDA | long | -0.8% | -3.9% | -26.6% | -1.1% | NVDA ended the short cycle narrative, demand rolling over wa |
| 15 | 2026-06-17 | 2026-06-22 | CLPT | long | +1.5% | +0.0% | +0.0% | +0.0% | This is super bullish for $CLPT |
| 16 | 2026-06-18 | 2026-06-22 | NVDA | long | -1.0% | +0.0% | +0.0% | +0.0% | I still think NVDA will be the world’s first $10T company |
| 17 | 2026-06-17 | 2026-06-22 | NFLX | long | -5.3% | +0.0% | +0.0% | +0.0% | 市场过度关注NFLX的不足，飞轮完好，市盈率近多年低点 |
| 18 | 2026-06-17 | 2026-06-22 | PLTR | long | -8.5% | +0.0% | +0.0% | +0.0% | why I own it |
| 19 | 2026-06-16 | 2026-06-22 | NOW | long | -8.2% | +0.0% | +0.0% | +0.0% | including why I own it |
| 20 | 2026-06-15 | 2026-06-22 | ALAB | long | +13.0% | +0.0% | +0.0% | +0.0% | $ALAB, $CRDO and $AAOI are my three horses in the race. |
| 21 | 2025-10-11 | 2026-01-09 | ONDS | long | +26.6% | +22.0% | +11.2% | +22.5% | 回调时定投计划中列为第一位 |
| 22 | 2026-06-15 | 2026-06-22 | SPCX | long | -19.7% | +0.0% | +0.0% | +0.0% | $SPCX $2T valuation isn’t as crazy as many people think |
| 23 | 2026-06-14 | 2026-06-22 | MSFT | long | -8.1% | +0.0% | +0.0% | +0.0% | you’re paying a melting-ice-cube multiple for the company ho |
| 24 | 2026-06-11 | 2026-06-22 | ADBE | long | -10.9% | +0.0% | +0.0% | +0.0% | AI-first ARR crossed $500M and tripled YoY which gives Adobe |
| 25 | 2026-06-11 | 2026-06-22 | ORCL | long | -4.9% | +0.0% | +0.0% | +0.0% | ORCL is early to one of the largest AI infrastructure buildo |
| 26 | 2026-06-09 | 2026-06-22 | ONDS | long | -7.9% | +0.0% | +0.0% | +0.0% | why I own it |
| 27 | 2026-06-09 | 2026-06-22 | ONDS | long | -7.9% | +0.0% | +0.0% | +0.0% | ONDS gives me exposure to the autonomy layer of drones... co |
| 28 | 2026-06-08 | 2026-06-22 | KTOS | long | -11.5% | +0.0% | +0.0% | +0.0% | why I own it |
| 29 | 2026-06-08 | 2026-06-22 | KTOS | long | -11.5% | +0.0% | +0.0% | +0.0% | KTOS gives me exposure to higher-end drone layer, engine bus |
| 30 | 2026-06-07 | 2026-06-22 | NVDA | long | +0.0% | +0.0% | +0.0% | +0.0% | NVDA将成为全球首家10万亿市值公司 |
| 31 | 2026-06-06 | 2026-06-22 | ORCL | long | -17.3% | +0.0% | +0.0% | +0.0% | $ORCL is a great one since its such a complex story in new A |
| 32 | 2026-06-06 | 2026-06-22 | MELI | long | -1.4% | +0.0% | +0.0% | +0.0% | $MELI is one of the best opportunities |
| 33 | 2026-06-04 | 2026-06-22 | PLTR | long | -15.7% | +0.0% | +0.0% | +0.0% | I added some $PLTR today |
| 34 | 2026-06-03 | 2026-06-22 | MELI | long | -3.0% | +0.0% | +0.0% | +0.0% | LatAm stocks are so cheap... look at $MELI |
| 35 | 2026-06-03 | 2026-06-22 | NVTS | long | -23.2% | +0.0% | +0.0% | +0.0% | AI 机架功率密度大增，NVTS 处于这一层，将获出价 |
| 36 | 2026-06-03 | 2026-06-22 | NVTS | long | -23.2% | +0.0% | +0.0% | +0.0% | If AI racks keep scaling to higher power levels then Navitas |
| 37 | 2026-06-03 | 2026-06-22 | IREN | long | -13.1% | +0.0% | +0.0% | +0.0% | every new megawatt expands the $IREN revenue opportunity and |
| 38 | 2026-06-03 | 2026-06-22 | NVTS | long | -23.2% | +0.0% | +0.0% | +0.0% | $NVTS is one of the best ways to play the AI power theme |
| 39 | 2026-06-03 | 2026-06-22 | NVTS | long | -23.2% | +0.0% | +0.0% | +0.0% | I currently own a 3% position in $NVTS in my Growth Portfoli |
| 40 | 2026-06-02 | 2026-06-22 | MSFT | long | -16.8% | +0.0% | +0.0% | +0.0% | 持有MSFT，量子是免费看涨期权 |
| 41 | 2026-06-02 | 2026-06-22 | MSFT | long | -16.8% | +0.0% | +0.0% | +0.0% | hold MSFT for Azure, improving Copilot monetization, plus a  |
| 42 | 2026-06-02 | 2026-06-22 | SOFI | long | -3.6% | +0.0% | +0.0% | +0.0% | $SOFI shouldn't be below $20 |
| 43 | 2026-06-02 | 2026-06-22 | OUST | long | +3.6% | +0.0% | +0.0% | +0.0% | Rev8 is a massive catalyst for $OUST because it justifies a  |
| 44 | 2026-05-31 | 2026-06-22 | PLTR | long | -25.6% | +0.0% | +0.0% | +0.0% | market is still underestimating how valuable owning that lay |
| 45 | 2026-05-30 | 2026-06-22 | NBIS | long | +7.2% | +0.0% | +0.0% | +0.0% | I currently own a 4% position in $NBIS in my Family Portfoli |
| 46 | 2026-05-30 | 2026-06-22 | NVDA | long | -7.0% | +0.0% | +0.0% | +0.0% | Bullish: $NVDA |
| 47 | 2026-05-29 | 2026-06-22 | SPCX | long | -3.9% | +0.0% | +0.0% | +0.0% | $SPCX deserves scarcity premiums |
| 48 | 2026-05-27 | 2026-06-22 | NVDA | long | -1.9% | +0.0% | +0.0% | +0.0% | $NVDA belongs above $300 |
| 49 | 2026-05-26 | 2026-06-22 | NVDA | long | -2.9% | +0.0% | +0.0% | +0.0% | I still believe it can become the world's first $10T company |
| 50 | 2026-05-26 | 2026-06-22 | AMD | long | +9.5% | +0.0% | +0.0% | +0.0% | AMD is the cleanest way to play the “CPUs are cool again” tr |
| 51 | 2026-05-26 | 2026-06-22 | MU | long | +35.2% | +0.0% | +0.0% | +0.0% | These 2027 $MU leaps I bought just two months ago are now up |
| 52 | 2026-05-26 | 2026-06-22 | MU | long | +35.2% | +0.0% | +0.0% | +0.0% | That $MU dip in the $300s two months ago was a gift. |
| 53 | 2026-05-26 | 2026-06-22 | MU | long | +35.2% | +0.0% | +0.0% | +0.0% | $MU going to hit $1000 next |
| 54 | 2026-05-26 | 2026-06-22 | NVTS | long | -25.4% | +0.0% | +0.0% | +0.0% | I added $NVTS last year |
| 55 | 2026-05-26 | 2026-06-22 | MU | long | +35.2% | +0.0% | +0.0% | +0.0% | Huge for $MU and Samsung as well |
| 56 | 2026-05-23 | 2026-06-22 | MELI | long | -3.6% | +0.0% | +0.0% | +0.0% | $MELI is one of best opportunities in market |
| 57 | 2026-05-23 | 2026-06-22 | MU | long | +35.2% | +0.0% | +0.0% | +0.0% | $MU could hit next year |
| 58 | 2026-05-23 | 2026-06-22 | NBIS | long | +36.3% | +0.0% | +0.0% | +0.0% | I own $NBIS in the family portfolio |
| 59 | 2026-05-23 | 2026-06-22 | RKLB | long | -30.0% | +0.0% | +0.0% | +0.0% | TOP 10 GROWTH PORTFOLIO POSITIONS includes $RKLB |
| 60 | 2026-05-22 | 2026-06-22 | ASTS | long | -30.9% | +0.0% | +0.0% | +0.0% | That $ASTS dip in the $70s last week was a gift |
| 61 | 2026-05-22 | 2026-06-22 | NVDA | long | -3.1% | +0.0% | +0.0% | +0.0% | Jensen's AI factory thesis got another major validation |
| 62 | 2026-05-22 | 2026-06-22 | AMD | long | +18.0% | +0.0% | +0.0% | +0.0% | CPU bottleneck will propel $AMD to $1T valuation. |
| 63 | 2026-05-22 | 2026-06-22 | RKLB | long | -26.1% | +0.0% | +0.0% | +0.0% | $RKLB going to be a $100B one day |
| 64 | 2026-05-21 | 2026-06-22 | NVDA | long | -4.9% | +0.0% | +0.0% | +0.0% | If you think this is peak earnings then just wait |
| 65 | 2026-05-21 | 2026-06-22 | NVDA | long | -4.9% | +0.0% | +0.0% | +0.0% | demand has gone parabolic because agentic AI has arrived |
| 66 | 2026-05-20 | 2026-06-22 | RKLB | long | -25.3% | +0.0% | +0.0% | +0.0% | I wanted Rocket Lab to raise again because this gives them m |
| 67 | 2026-05-20 | 2026-06-22 | ASTS | long | -18.3% | +0.0% | +0.0% | +0.0% | $ASTS remains a top 5 position for me |
| 68 | 2026-05-20 | 2026-06-22 | ALAB | long | +52.9% | +0.0% | +0.0% | +0.0% | $ALAB is now the latest multi-bagger in the family portfolio |
| 69 | 2026-05-20 | 2026-06-22 | NVDA | long | -6.6% | +0.0% | +0.0% | +0.0% | Jensen about to prove why $NVDA will be the worlds first $10 |
| 70 | 2026-05-19 | 2026-06-22 | IREN | long | +19.1% | +0.0% | +0.0% | +0.0% | I still own $IREN because I think the market is underestimat |

---

## @Sam_Badawi

### 数据

- ORIGINAL 总判断: 107
- LLM 抽完有方向 (long/short): 23
- 已验证 (90d 窗口, 数据截止 2026-06-22): 19
- Pending (entry > 2026-04-01, 90d 还没到期): 10
- Unresolved: {'no_px entry=2026-06-21 exit=2026-06-22': 2, 'no_px entry=2026-06-19 exit=2026-06-22': 1, 'no_px entry=2026-06-16 exit=2026-06-22': 1}

### 核心: raw 选股命中率 (不依赖基准)

- n_resolved: **19**
- raw 涨 (raw>0): **5**
- raw 跌 (raw<0): 11
- **raw_hit_rate: 26.3%**
- median_raw: **-1.3%**
- mean_raw: -3.9%

### Excess vs Benchmarks

| Bench | n | med_excess | mean_excess | hit_rate |
|---|---|---|---|---|
| SPY | 9 | -16.1% | -10.1% | 33.3% |
| SOXX | 9 | -26.7% | -21.8% | 22.2% |
| QQQ | 9 | -15.1% | -9.8% | 33.3% |

### 置信度: **D** (raw_hit 26.3%, n=19)

### 能力圈 (ticker, n≥1 预测, 按 n 倒序)

| ticker | n | raw_hit | med_raw | med_excess_soxx |
|---|---|---|---|---|
| NBIS | 3 | 33.3% | -1.0% | -11.5% |
| SNAP | 2 | 50.0% | +5.1% | +0.0% |
| IREN | 2 | 0.0% | -15.9% | -27.1% |
| HNGE | 1 | 0.0% | +0.0% | +0.0% |
| TE | 1 | 0.0% | +0.0% | +0.0% |
| META | 1 | 100.0% | +12.4% | +0.1% |
| BMNR | 1 | 0.0% | -31.9% | -54.2% |
| ORCL | 1 | 0.0% | -18.0% | -26.7% |
| AMZN | 1 | 100.0% | +4.6% | -15.0% |
| NVDA | 1 | 0.0% | -11.5% | +0.0% |
| TSLA | 1 | 0.0% | -4.5% | -23.2% |
| SOFI | 1 | 0.0% | -3.4% | +0.0% |
| MU | 1 | 100.0% | +11.3% | +0.0% |
| NVTS | 1 | 0.0% | -1.3% | +0.0% |
| RKLB | 1 | 0.0% | -7.1% | +0.0% |

### 4 分类

#### 4.1 raw 真赢 (5 条, 按 raw 倒序)

| ticker | dir | entry → exit | raw | excess_spy | excess_soxx |
|---|---|---|---|---|---|
| NBIS | long | 2025-08-24 → 2025-11-22 | +31.2% | +27.2% | +17.5% |
| META | long | 2025-11-01 → 2026-01-30 | +12.4% | +11.1% | +0.1% |
| MU | long | 2026-06-13 → 2026-06-22 | +11.3% | +0.0% | +0.0% |
| SNAP | short | 2026-06-16 → 2026-06-22 | +10.3% | +0.0% | +0.0% |
| AMZN | long | 2025-10-23 → 2026-01-21 | +4.6% | +2.6% | -15.0% |

#### 4.2 raw 真输 (11 条, 按 raw 升序)

| ticker | dir | entry → exit | raw | excess_spy | excess_soxx |
|---|---|---|---|---|---|
| NBIS | long | 2025-10-02 → 2025-12-31 | -33.5% | -35.4% | -40.4% |
| BMNR | long | 2025-09-02 → 2025-12-01 | -31.9% | -38.1% | -54.2% |
| ORCL | long | 2025-12-11 → 2026-03-11 | -18.0% | -16.1% | -26.7% |
| IREN | long | 2025-10-06 → 2026-01-04 | -16.5% | -18.9% | -26.8% |
| IREN | long | 2025-10-03 → 2026-01-01 | -15.4% | -17.5% | -27.4% |
| NVDA | long | 2026-05-14 → 2026-06-22 | -11.5% | +0.0% | +0.0% |
| RKLB | long | 2026-06-17 → 2026-06-22 | -7.1% | +0.0% | +0.0% |
| TSLA | long | 2025-10-22 → 2026-01-20 | -4.5% | -6.0% | -23.2% |
| SOFI | long | 2026-06-16 → 2026-06-22 | -3.4% | +0.0% | +0.0% |
| NVTS | long | 2026-06-18 → 2026-06-22 | -1.3% | +0.0% | +0.0% |
| NBIS | short | 2026-06-17 → 2026-06-22 | -1.0% | +0.0% | +0.0% |

#### 4.3 跑赢 SOXX (按 excess_soxx 倒序)

| ticker | dir | entry → exit | raw | excess_soxx |
|---|---|---|---|---|
| NBIS | long | 2025-08-24 → 2025-11-22 | +31.2% | +17.5% |
| META | long | 2025-11-01 → 2026-01-30 | +12.4% | +0.1% |
| HNGE | long | 2026-06-21 → 2026-06-22 | +0.0% | +0.0% |
| TE | long | 2026-06-21 → 2026-06-22 | +0.0% | +0.0% |
| NBIS | short | 2026-06-17 → 2026-06-22 | -1.0% | +0.0% |
| SNAP | long | 2026-06-20 → 2026-06-22 | +0.0% | +0.0% |
| NVDA | long | 2026-05-14 → 2026-06-22 | -11.5% | +0.0% |
| SOFI | long | 2026-06-16 → 2026-06-22 | -3.4% | +0.0% |
| MU | long | 2026-06-13 → 2026-06-22 | +11.3% | +0.0% |
| NVTS | long | 2026-06-18 → 2026-06-22 | -1.3% | +0.0% |

#### 4.4 跑输 SOXX (按 excess_soxx 升序)

| ticker | dir | entry → exit | raw | excess_soxx |
|---|---|---|---|---|
| BMNR | long | 2025-09-02 → 2025-12-01 | -31.9% | -54.2% |
| NBIS | long | 2025-10-02 → 2025-12-31 | -33.5% | -40.4% |
| IREN | long | 2025-10-03 → 2026-01-01 | -15.4% | -27.4% |
| IREN | long | 2025-10-06 → 2026-01-04 | -16.5% | -26.8% |
| ORCL | long | 2025-12-11 → 2026-03-11 | -18.0% | -26.7% |
| TSLA | long | 2025-10-22 → 2026-01-20 | -4.5% | -23.2% |
| AMZN | long | 2025-10-23 → 2026-01-21 | +4.6% | -15.0% |
| HNGE | long | 2026-06-21 → 2026-06-22 | +0.0% | +0.0% |
| TE | long | 2026-06-21 → 2026-06-22 | +0.0% | +0.0% |
| NBIS | short | 2026-06-17 → 2026-06-22 | -1.0% | +0.0% |

### 全部 19 条已验证 (逐条, 给你对照看)

| # | entry | exit | ticker | dir | raw | exc_spy | exc_soxx | exc_qqq | thesis |
|---|---|---|---|---|---|---|---|---|---|
| 1 | 2026-06-21 | 2026-06-22 | HNGE | long | +0.0% | +0.0% | +0.0% | +0.0% | $HNGE looking super sexy right now |
| 2 | 2026-06-21 | 2026-06-22 | TE | long | +0.0% | +0.0% | +0.0% | +0.0% | My money is on $TE as a swing |
| 3 | 2025-11-01 | 2026-01-30 | META | long | +12.4% | +11.1% | +0.1% | +14.0% | $META is now the CHEAPEST Mag7 stock. |
| 4 | 2025-08-24 | 2025-11-22 | NBIS | long | +31.2% | +27.2% | +17.5% | +25.1% | 回购授权和注销4000万股立即提升EPS和所有权 |
| 5 | 2025-09-02 | 2025-12-01 | BMNR | long | -31.9% | -38.1% | -54.2% | -41.0% | a clear discount… buy more? yes |
| 6 | 2026-06-17 | 2026-06-22 | NBIS | short | -1.0% | +0.0% | +0.0% | +0.0% | $NBIS 将有不可避免的30%回调 |
| 7 | 2026-06-20 | 2026-06-22 | SNAP | long | +0.0% | +0.0% | +0.0% | +0.0% | Maybe we should be going all in on $SNAP |
| 8 | 2025-10-06 | 2026-01-04 | IREN | long | -16.5% | -18.9% | -26.8% | -18.2% | Even he said we’re still early… |
| 9 | 2025-12-11 | 2026-03-11 | ORCL | long | -18.0% | -16.1% | -26.7% | -15.1% | Told gramps to buy $ORCL at 330 |
| 10 | 2025-10-02 | 2025-12-31 | NBIS | long | -33.5% | -35.4% | -40.4% | -34.9% | $NBIS IS UP 6% PM AFTER NEW INFO ON THE $19.4B DEAL |
| 11 | 2025-10-23 | 2026-01-21 | AMZN | long | +4.6% | +2.6% | -15.0% | +3.7% | $AMZN remains one of the cheapest megacaps in the market |
| 12 | 2026-05-14 | 2026-06-22 | NVDA | long | -11.5% | +0.0% | +0.0% | +0.0% | Time for $250 |
| 13 | 2025-10-22 | 2026-01-20 | TSLA | long | -4.5% | -6.0% | -23.2% | -4.9% | It's very underrated. |
| 14 | 2025-10-03 | 2026-01-01 | IREN | long | -15.4% | -17.5% | -27.4% | -17.0% | 建议定投进入（DCA in）享受长期收益 |
| 15 | 2026-06-16 | 2026-06-22 | SOFI | long | -3.4% | +0.0% | +0.0% | +0.0% | CEO ANTHONY NOTO HAS BOUGHT OVER $2.3M WORTH OF SHARES; buys |
| 16 | 2026-06-13 | 2026-06-22 | MU | long | +11.3% | +0.0% | +0.0% | +0.0% | The AI Memory Trade Is Still Being Bought |
| 17 | 2026-06-18 | 2026-06-22 | NVTS | long | -1.3% | +0.0% | +0.0% | +0.0% | 我的投资组合平均分为NVTS等股 |
| 18 | 2026-06-17 | 2026-06-22 | RKLB | long | -7.1% | +0.0% | +0.0% | +0.0% | 我不会卖出CC除非想卖股票，暗示持仓看多 |
| 19 | 2026-06-16 | 2026-06-22 | SNAP | short | +10.3% | +0.0% | +0.0% | +0.0% | SNAP 肯定会到 100，不过是 100 美分 |

---

## 三人对照表 (事实数字, 你自己下判断)

| KOL | n_orig | n_dir | n_resolved | pending | raw_hit | med_raw | vs SPY | vs SOXX | vs QQQ | 置信度 |
|---|---|---|---|---|---|---|---|---|---|---|
| @amitisinvesting | 156 | 46 | 45 | 41 | 37.8% | -0.8% | +20.5% | +8.7% | +19.7% | **D** |
| @StockSavvyShay | 333 | 76 | 70 | 62 | 31.4% | -3.6% | +12.3% | +1.2% | +11.5% | **D** |
| @Sam_Badawi | 107 | 23 | 19 | 10 | 26.3% | -1.3% | -16.1% | -26.7% | -15.1% | **D** |

## 备注 / 已知坑

- LLM 抽 direction 用 deepseek-v4-pro, max_tokens 800, 25-30 worker 并发
- 剩 6 条 (3+2+1) 真的抽不动 (LLM 多次返空), 标 '?', 不算入统计
- **修日期解析 bug**: 之前用 `createdAt[:10]` 拿 'Sun Apr 12', 实际是 'Sun Apr 12 01:41:11 +0000 2026' = 2026-04-12. 改用 email.utils.parsedate_to_datetime
- 4 候选全部 US (Polygon 可验), 100% 美股
- 拉取时间窗: Apify `from:handle` 模式跨 1-2 年 (最新 2 月爆 50-60%, 旧月份散落 1-5 条)
- 暂不下'可不可跟'结论 — 你自己对照看 (尤其会拿市场常识查可疑数字)
