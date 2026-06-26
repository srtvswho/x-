# Phase 3 第一步: market_corrected 机制 + 排查 + 别名归一化

**时间**: 2026-06-15T06:20:49.637228+00:00

## 1. market_corrected 机制

### 数据不可变原则
- `predictions.market` = LLM 原始抽取值(**永远不动**,审计用)
- `predictions.market_corrected` = 人工/规则修正值(默认 NULL = 沿用 raw)

### 验证层读取顺序
```sql
SELECT 
  COALESCE(NULLIF(p.market_corrected, ''), p.market) AS market_for_verification,
  p.market AS raw_market,
  CASE WHEN p.market_corrected IS NOT NULL THEN 1 ELSE 0 END AS is_corrected
FROM predictions p;
```

### 审计表 market_corrections
| 字段 | 说明 |
|---|---|
| correction_id | 主键 |
| ticker | 标的 |
| raw_market | LLM 原始 |
| corrected_market | 修正后 |
| reason | 修正理由(短) |
| evidence | 证据(可长) |
| affected_predictions | 涉及行数 |
| created_at | 创建时间 |
| applied | 0/1 是否已写 predictions |
| applied_at | 写入时间 |

## 2. 全表排查 '疑似误归美股' 候选清单

**总计: 393 条 predictions / 22 个 ticker 候选修正**

### 2.1 强信号(aliases 表指向非美股, 339 条)

| ticker | 当前 market | 应修正 | n | alias 证据 |
|---|---|---|---|---|
| `SIVE` | 美股 | **SE** | 338 | Sivers Semiconductors 斯德哥尔摩 |
| `LTC` | 美股 | **crypto** | 27 | None |
| `ETH` | 美股 | **crypto** | 17 | None |
| `FOCI` | 美股 | **TW** | 16 | FOCiS 3363 |
| `BTC` | 美股 | **commodity** | 9 |  |
| `BTC` | 美股 | **crypto** | 9 |  |
| `TOWA` | 美股 | **JP** | 8 | None |
| `EOSE` | 美股 | **crypto** | 1 | None |
| `WIN` | 美股 | **TW** | 1 | None |

### 2.2 中信号(ticker 含非美股后缀, 54 条)

| ticker | 应修正 | n | 后缀证据 |
|---|---|---|---|
| `GRZ.V` | **CA** | 3 | suffix=.V |
| `HPS.A` | **CA** | 16 | suffix=.A |
| `HSP.A` | **CA** | 1 | suffix=.A |
| `LYC.AX` | **ASX** | 1 | suffix=.AX |
| `MOG.A` | **CA** | 1 | suffix=.A |
| `MVZ.A` | **CA** | 3 | suffix=.A |
| `MVZ.B` | **CA** | 4 | suffix=.B |
| `VNP.TO` | **CA** | 1 | suffix=.TO |

### 2.3 模糊 case(待人工 case-by-case, **不动**)

- BTC: 18 条 (9 美股 / 9 crypto),$BTC 可能是 spot crypto 或美股 BTC ETF/期货,需逐条看 raw_text
- ETH: 17 条 (全在美股),$ETH 同理
- LTC: 27 条 (全在美股),$LTC 同理
- EOSE: 1 条 (alias 表误指向 crypto,实际是美股 EOS Energy 储能公司)

**判断逻辑**:`$BTC/$ETH/$LTC` 在金融推文里通常指 spot crypto,不是 BTC ETF(IBIT/FBTC);美股市场也有 spot crypto ETF 但 2024 前极少
**建议**:第一批修正**不动**这些,留 raw_market;在 P3-2 验证函数里用 ticker 字符串判断(见下)。

## 3. 修正后 market 分布预览

| market | raw 分布 | 修正后分布 | Δ |
|---|---|---|---|
| 美股 | 4081 | 4080 | -1 |
| SE | 8 | 346 | +338 |
| TW | 164 | 181 | +17 |
| KR | 93 | 93 | 0 |
| crypto | 21 | 75 | +54 |
| JP | 57 | 65 | +8 |
| CA | 3 | 32 | +29 |
| commodity | 12 | 21 | +9 |
| A股 | 18 | 18 | 0 |
| 未上市 | 7 | 7 | 0 |
| 欧洲 | 4 | 4 | 0 |
| ASX | 1 | 2 | +1 |
| LSE | 1 | 1 | 0 |

## 4. aliases 归一化(SIVE 案例)

**当前状态**:

| alias_raw | ticker | market | notes |
|---|---|---|---|
| `SIVE` | `SIVE` | SE | Sivers Semiconductors 斯德哥尔摩 |

**归一化方案(等 user 确认)**:

```sql
-- 检查现有
SELECT alias_raw FROM aliases WHERE alias_raw IN ('SIVE', 'SIVE.ST', 'SIVEF');
-- 3 条 alias_raw → 同一 canonical SIVE(SE)
INSERT OR REPLACE INTO aliases (alias_raw, ticker, market, asset_class, locale, source, confidence, notes, created_at)
VALUES
  ('SIVE',     'SIVE', 'SE', 'equity', 'en', 'manual', 1.0, 'Sivers Semiconductors 斯德哥尔摩主板; 推文常见简写', '2026-06-15'),
  ('SIVE.ST',  'SIVE', 'SE', 'equity', 'en', 'manual', 1.0, 'Sivers Semiconductors 斯德哥尔摩主板官方代码', '2026-06-15'),
  ('SIVEF',    'SIVE', 'SE', 'equity', 'en', 'manual', 1.0, 'Sivers 美股 OTC 代码; 验证优先(P3-2 唯一可拉)','2026-06-15');
```

**验证 priority 顺序**(P3-2 验证函数读取时):
1. 优先 SIVEF (美股 OTC,Polygon/Finnhub 都通,USD 计价)
2. 兜底 SIVE.ST (Polygon/Finnhub 不覆盖,但理论上)