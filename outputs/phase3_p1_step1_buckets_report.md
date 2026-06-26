# Phase 3 第一步 buckets 报告

**时间**: 2026-06-15T07:08:24.516153+00:00

## 1. 加拿大/委内瑞拉修正(已执行)

| ticker | corrected | n | reason | low_confidence |
|---|---|---|---|---|
| `HPS.A` | **CA** | 16 | Hammond Power Solutions 加拿大(TSX,加元) |  |
| `MVZ.A` | **VE** | 3 | Mercantil Servicios Financieros 委内瑞拉(加拉加斯 BVC,玻利瓦尔 |  |
| `MVZ.B` | **VE** | 4 | Mercantil Servicios Financieros B 类股 委内瑞拉(加拉加斯 BVC |  |
| `HSP.A` | **CA** | 1 | Hammond Power Solutions 关联(可能 A 类,样本仅 1 条存疑) | ✓ |
| `GRZ.V` | **CA** | 3 | GreenRise Foods 加拿大(TSX Venture,加元) |  |
| `VNP.TO` | **CA** | 1 | 5N Plus 加拿大(TSX 主板,加元) |  |
| `LYC.AX` | **ASX** | 1 | Lynas Rare Earths 澳洲(ASX,澳元) |  |
| `MOG.A` | (美股,不动) | 1 | Moog Inc NYSE 双类股,真美股 | |

## 2. price_source_available 标记

### 规则
```
UPDATE predictions 
SET price_source_available = CASE
  WHEN COALESCE(NULLIF(market_corrected, ''), market) = '美股' THEN 1
  WHEN ticker IN ('SIVE', 'SIVEF') THEN 1
  ELSE 0
END;
```

### 状态

| available | market | n |
|---|---|---|
| ⏸ 不可验证 | TW | 173 |
| ⏸ 不可验证 | KR | 93 |
| ⏸ 不可验证 | JP | 65 |
| ⏸ 不可验证 | CA | 24 |
| ⏸ 不可验证 | crypto | 21 |
| ⏸ 不可验证 | A股 | 18 |
| ⏸ 不可验证 | commodity | 12 |
| ⏸ 不可验证 | 未上市 | 7 |
| ⏸ 不可验证 | VE | 7 |
| ⏸ 不可验证 | 欧洲 | 4 |
| ⏸ 不可验证 | ASX | 2 |
| ⏸ 不可验证 | LSE | 1 |
| ✅ 可验证 | 美股 | 3693 |
| ✅ 可验证 | SE | 350 |

## 3. 分桶统计

### ✅ 可验证集 (price_source_available=1)

**predictions: 4043**
**unique ticker: 418**

| market | predictions |
|---|---|
| 美股 | 416 |
| SE | 2 |

**全部 ticker 清单** (n_avail_ticker 个):

```
  NBIS        n=364
  SIVE        n=346
  AAOI        n=189
  AXTI        n=157
  LITE        n=107
  IREN        n=98
  CIFR        n=79
  TSM         n=78
  SOI         n=70
  HIMS        n=66
  RKLB        n=63
  RDDT        n=61
  COHR        n=59
  AEHR        n=52
  IQE         n=50
  MU          n=50
  MRVL        n=48
  META        n=46
  CRWV        n=43
  TSEM        n=41
  ALAB        n=40
  CRCL        n=40
  WULF        n=40
  AMZN        n=38
  SNAP        n=38
  SMCI        n=36
  AMD         n=33
  CRDO        n=29
  SNDK        n=29
  VLN         n=29
  NVDA        n=28
  WLAC        n=28
  LTC         n=27
  XLU         n=27
  INTC        n=26
  LPTH        n=26
  AVGO        n=25
  FLNC        n=25
  IBIT        n=25
  HOOD        n=24
  POET        n=24
  ETOR        n=23
  MSS         n=23
  AVAV        n=22
  FLY         n=22
  UPWK        n=22
  VPG         n=22
  RPI         n=21
  TE          n=20
  CVX         n=19
  ... (还有 368 个)
```

### ⏸ 不可验证集 (price_source_available=0)

**predictions: 427**
**unique ticker: 97**

**细分原因**:

| 原因 | predictions | ticker |
|---|---|---|
| Polygon/Finnhub 免费源不覆盖 TW 交易所 | 173 | 34 |
| Polygon/Finnhub 免费源不覆盖 KR 交易所 | 93 | 4 |
| Polygon/Finnhub 免费源不覆盖 JP 交易所 | 65 | 22 |
| Polygon/Finnhub 免费源不覆盖 CA 交易所 | 24 | 6 |
| 验证逻辑待拍板(方案 A/B/C) | 21 | 5 |
| Polygon/Finnhub 免费源不覆盖 A股 交易所 | 18 | 9 |
| 商品期货代码(GC=F 等),需单独处理 | 12 | 7 |
| 委内瑞拉 BVC,玻利瓦尔,数据源不覆盖 | 7 | 2 |
| 私募/未上市,无公开行情 | 7 | 1 |
| Polygon/Finnhub 免费源不覆盖 欧洲 交易所 | 4 | 4 |
| Polygon/Finnhub 免费源不覆盖 ASX 交易所 | 2 | 2 |
| Polygon/Finnhub 免费源不覆盖 LSE 交易所 | 1 | 1 |

## 4. 第一版记分牌范围

- **跑**: 4043 predictions / 418 ticker (price_source_available=1)
- **跳过(v2 backlog)**: 427 predictions, validation_status=skipped

**注意**:第一版不是 100% 覆盖,美股 3722 预测里还有 Finnhub 报 no_quote_data 的 60 个 ticker (P3-1 报告),Polygon 日线覆盖率预计 ~95%。P3-2 实际拉日线时会再筛一次,具体到单 ticker 不可拉就再 skip。
