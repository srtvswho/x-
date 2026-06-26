# Phase 3 第一步 apply 报告

**时间**: 2026-06-15T06:55 UTC

## ✅ 已执行

### 1. 强信号修正 (359 条)

| ticker | raw_market | corrected | n | reason |
|---|---|---|---|---|
| `SIVE` | 美股 | **SE** | 338 | Sivers Semiconductors 是瑞典公司(斯德哥尔摩主板 SIVE.ST,瑞典克朗),LLM 因美国 OTC 挂牌 SIVEF 误归美股 |
| `SIVEF` | 美股 | **SE** | 4 | 同 SIVE(同一公司 Sivers 美股 OTC 代码),推文证据 `'$SIVE trades US OTC as $SIVEF too'` |
| `FOCI` | 美股 | **TW** | 8 | FOCiS 3363 台湾上柜公司(光通讯),LLM 因 ticker 形似美股代码误归美股 |
| `WIN` | 美股 | **TW** | 1 | Win Semi 台湾上柜(稳懋半导体,3105.TW) |
| `TOWA` | 美股 | **JP** | 8 | TOWA Semiconductor 日本公司(5801.T,半导体后段设备) |

**总计 359 条 predictions 修正**,5 个 ticker。

### 4. aliases 归一化 (SIVE 案例)

| alias_raw | canonical | market | notes |
|---|---|---|---|
| `SIVE` | `SIVE` | SE | Sivers Semiconductors 斯德哥尔摩主板; 推文常见简写形式 |
| `SIVE.ST` | `SIVE` | SE | Sivers Semiconductors 斯德哥尔摩主板官方代码(克朗) |
| `SIVEF` | `SIVE` | SE | Sivers 美股 OTC 代码(美元); P3-2 验证优先(数据源唯一可拉) |

**验证 priority 顺序** (P3-2 验证函数读取时):
1. **SIVEF** (美股 OTC,Polygon/Finnhub 都通,USD 计价) ← 优先
2. **SIVE.ST** (斯德哥尔摩,数据源不覆盖,理论兜底)

## 修正后 market 分布(verification 用)

```
美股          3722
SE          350    (+342: SIVE 338 + SIVEF 4)
TW          173    (+9: FOCI 8 + WIN 1)
KR          93
JP          65     (+8: TOWA 8)
crypto      21
A股          18
commodity   12
未上市         7
欧洲          4
CA          3
LSE         1
ASX         1
```

## ⏸ 2. 加拿大 29 条待审查(不动)

**重点警示**:`.A`/`.B`/`.C` 在美股 = 股份类别(class A/B/C),**非国别后缀**。需逐个查证公司主体。

| ticker | n | 推文样本 | 公司判定 | 备注 |
|---|---|---|---|---|
| `HPS.A` | 16 | "multi-year bottlenecks: $HPS.A to $SNDK to $LITE" | **美股? 待查** | Hammond Power Solutions 实际是加拿大(TSX:HPS.A),但有 OTC 影子 |
| `HSP.A` | 1 | "$HSP.A for DC transformers bottleneck" | **待查** | 可能也是 Hammond 关联 |
| `MVZ.A` | 3 | "US has now toppled Maduro's regime... Venezuelan Gold Rush" | **待查** | 委内瑞拉相关公司,可能美股 OTC |
| `MVZ.B` | 4 | 同 MVZ.A | **待查** | 同上 |
| `MOG.A` | 1 | "30 US-available random stocks I like today" | **待查** | 推文说"US-available"暗示美股可买 |
| `GRZ.V` | 3 | "Many of these like $GRZ.V or $ASHM were risky, distressed assets, frozen because of Venezuelan government" | **加拿大 (TSX Venture) 确认** | "distressed assets" 模式,委内瑞拉资产 |
| `VNP.TO` | 1 | "$MTRN - Beryllium / $ESE" 等多 ticker 列表 | **加拿大 (TSX) 确认** | 5TP 供应链,加拿大资源股 |
| `LYC.AX` | 1 | "researching new stocks that actually look interesting" | **澳洲 (ASX) 确认** | Lynas Rare Earths 澳洲稀土 |

**已知确认(可立即修)**:
- `GRZ.V` (3) → CA
- `VNP.TO` (1) → CA
- `LYC.AX` (1) → ASX

**疑似美股股份类别(需查证,大概率不动)**:
- `HPS.A` (16) — Hammond Power Solutions 实际 TSX:HPS.A 加拿大,但 OTC:HPS.A 也是它
- `HSP.A` (1) — 同 HPS 关联
- `MVZ.A`/`MVZ.B` (7) — 委内瑞拉相关,待查
- `MOG.A` (1) — 推文明示"US-available"

**判定规则**:
- `.TO` = 多伦多主板 (TSX) — 必加拿大
- `.V` = TSX Venture (温哥华创业板) — 必加拿大
- `.A`/`.B`/`.C` = **股份类别(美股/加股都可能)** — 必须查公司主体
- `.AX` = 澳交所 — 必澳洲

**请逐个给我**:`{HPS.A / HSP.A / MVZ.A / MVZ.B / MOG.A}` 的公司全名 + 主交易所(美股/加股/其他),我才能决定 market_corrected。

## ⏸ 3. crypto 63 条(market_corrected 暂不动,等验证逻辑拍板)

| ticker | raw_market | n | 状态 |
|---|---|---|---|
| `BTC` | 美股 | 9 | alias: BTC→crypto; 等待验证逻辑设计 |
| `BTC` | crypto | 9 | ✓ 已正确(LLM 抽对) |
| `LTC` | 美股 | 27 | alias: LTC→crypto; 等待验证逻辑设计 |
| `ETH` | 美股 | 17 | alias: ETH→crypto; 等待验证逻辑设计 |
| `SOL` | 美股 | 7 | alias: SOL→crypto; 等待验证逻辑设计 |
| `EOSE` | 美股 | 1 | alias 错(EOSE = EOS Energy 储能,非 EOS crypto),保持美股 |

### P3-2 验证逻辑设计建议(待你拍板)

**方案 A. crypto 内基准**(主流 1)
- crypto 超额 = asset_return - BTC_return (同期)
- 优点: 区分选币α与crypto大盘β
- 缺点: 2024 后 BTC 主导市场,ETH/LTC/SOL 经常负超额但绝对收益高

**方案 B. 仅绝对收益**
- crypto 不算超额,只算 raw_return
- 优点: 简单,crypto 资产类别不同,强加宽基错位
- 缺点: 不能与股票胜率直接对比

**方案 C. 加密指数基准 (Composite)**
- 0.5*BTC + 0.3*ETH + 0.2*total_crypto_market_cap
- 优点: 反映整体加密市场
- 缺点: 复杂,数据需 CoinGecko / CoinMarketCap

**我的建议: 方案 A(简单 + 主流)** — 但需决定基准用 BTC only 还是 BTC+ETH:
- 主流 1: BTC only
- 主流 2: BTC 50% + ETH 50%
- 主流 3: 同期 crypto 总市值

**等你拍板 A/B/C,以及 A 内的基准选什么。**

## 数据现状

- ✅ `predictions.market_corrected` 列已加(默认 NULL)
- ✅ `market_corrections` 审计表已建
- ✅ 5 个 ticker 359 条预测已修正(SIVE 338 / SIVEF 4 / FOCI 8 / WIN 1 / TOWA 8)
- ✅ aliases 归一化:SIVE / SIVE.ST / SIVEF 全部映射 SIVE(SE)
- ⏸ 加拿大 5 个 ticker 待审查(`HPS.A / HSP.A / MVZ.A / MVZ.B / MOG.A`)
- ⏸ crypto 4 个 ticker 60 条 market_corrected 待执行
- ⏸ 已知确认 5 条(`GRZ.V 3 / VNP.TO 1 / LYC.AX 1`)等你批
