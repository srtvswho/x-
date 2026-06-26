# P3-7d 严格条件性 short 清单(if 是否在窗口内触发)

**生成时间**: 2026-06-16T03:11:39.634144Z

## 0. 范围

- 短头寸总数: 147 (P3-6 应用后,排除了 13 B 改 neutral 的)
- 严格条件性 + 还在 short 列表: **17 条**

**严格条件句标准**:
- 价格条件: if/when/once + 价格动作(break/fall/drop/rise/...) + above/below/to + $价格
- 事件条件: if + 财务/政治/地缘/公司事件 + 客观动作(passes/fails/approves/...)
- 中文: 如果/一旦 + 事件/价格动作

**排除 (伪条件/时间修饰)** — 不豁免:
- after/before/when + 时间(earnings/close/Q1/2026/H1)
- if + 弱动词(want/think/can/should/will)
- once + 模糊时间(market truly/publicly/...)

## 1. 按 label 分布

| Label | n |
|---|---|
| PRICE_TARGET | 15 |
| PRICE_DIP | 2 |
| PRICE_LEVEL | 1 |
| EVENT_GENERIC | 1 |

## 2. 按 ticker 分布

| ticker | n 真条件 |
|---|---|
| BMNR | 4 |
| RGTI | 2 |
| OKLO | 2 |
| QBTS | 2 |
| IONQ | 2 |
| TSLA | 1 |
| CRCL | 1 |
| PLTR | 1 |
| PL | 1 |
| BLSKY | 1 |

## 3. 严格条件性 short 完整清单

**对每条:需要你判定 if 条件在 1w/1m/3m/6m 窗口内是否真的发生**

### [1] BMNR short — pub=2025-09-25T21:04:48
- entry=2025-09-26, $49.58
- 1m: resolved_miss excess=-11.87% raw=-8.33%
- 1w: resolved_miss excess=-15.38%
- 3m: resolved_hit excess=+38.50%
- 6m: resolved_hit excess=+61.84%
- **条件 label**: ['PRICE_LEVEL', 'EVENT_GENERIC', 'PRICE_DIP']
- **匹配**: `if it drops to $3.5`
- **原文 (前 400 chars)**:
```
| So daily thoughts on Sept 25th + market drop if you like my insights: 
| 
| 1. 3x rate cut went from 65% to 56% from data today. This is a lot more material, since people are front-running rate cuts now. 
| 
| Either way, any rate cut usually lead to large inflows so it's generally bullish for markets months out. 
| 
| Powell's thoughts about market being overvalued holds kind of true for certain stocks. Oklo
```

### [2] BMNR short — pub=2025-09-26T00:30:30
- entry=2025-09-29, $52.12
- 1m: resolved_miss excess=-4.33% raw=-0.81%
- 1w: resolved_miss excess=-22.49%
- 3m: resolved_hit excess=+43.30%
- 6m: resolved_hit excess=+63.49%
- **条件 label**: ['PRICE_DIP']
- **匹配**: `if it dipped to $2200`
- **原文 (前 400 chars)**:
```
| @SebastianS79509 I would just stay away from $BMNR. 
| 
| I bought 6 fig of $ETH at $1600. I'd buy again if it dipped to $2200-$2400 and swing trade it under $2800. 
| 
| Otherwise $3k+, especially $3.9k (where it's now), I wouldn't buy a dip.
```

### [3] TSLA short — pub=2025-10-04T01:22:20
- entry=2025-10-06, $440.75
- 1m: resolved_miss excess=-1.34% raw=-0.80%
- 1w: resolved_hit excess=+2.38%
- 3m: resolved_miss excess=-0.56%
- 6m: resolved_hit excess=+20.35%
- **条件 label**: ['PRICE_TARGET']
- **匹配**: `$200 support`
- **原文 (前 400 chars)**:
```
| Friday Market Close, Personal Thoughts and Explanations:
| 
| Strong Buy
| $RDDT
| $SNAP
| $AMZN
| $ETOR
| $NBIS
| $LTC
| 
| Buy
| $UPWK
| $MSTR
| $ORCL
| $TGT
| $CIFR
| $VIRT
| $CRDO
| $WULF
| $SOFI
| $META
| $AVGO
| $MRVL
| $SMCI
| $DELL
| 
| Hold
| $RKLB
| $TSM
| $IREN
| $RR
| $ALAB
| $HOOD
| $FLNC
| $EOSE
| $BE
| $RIOT
| $MARA
| $GRAB
| $ASTS
| $NVO
| $NVDA
| 
| Sell
| $TSLA
| $CRCL
| $PLTR
| $BMNR
| 
| Strong Sell
| $RGTI
| $OKLO
| $QBTS
| $IONQ
| 
| _
| 
| (again, not great DD, just writing random thoug
```

### [4] CRCL short — pub=2025-10-04T01:22:20
- entry=2025-10-06, $154.01
- 1m: resolved_hit excess=+27.22% raw=+27.76%
- 1w: resolved_hit excess=+12.02%
- 3m: resolved_hit excess=+45.00%
- 6m: resolved_hit excess=+43.51%
- **条件 label**: ['PRICE_TARGET']
- **匹配**: `$200 support`
- **原文 (前 400 chars)**:
```
| Friday Market Close, Personal Thoughts and Explanations:
| 
| Strong Buy
| $RDDT
| $SNAP
| $AMZN
| $ETOR
| $NBIS
| $LTC
| 
| Buy
| $UPWK
| $MSTR
| $ORCL
| $TGT
| $CIFR
| $VIRT
| $CRDO
| $WULF
| $SOFI
| $META
| $AVGO
| $MRVL
| $SMCI
| $DELL
| 
| Hold
| $RKLB
| $TSM
| $IREN
| $RR
| $ALAB
| $HOOD
| $FLNC
| $EOSE
| $BE
| $RIOT
| $MARA
| $GRAB
| $ASTS
| $NVO
| $NVDA
| 
| Sell
| $TSLA
| $CRCL
| $PLTR
| $BMNR
| 
| Strong Sell
| $RGTI
| $OKLO
| $QBTS
| $IONQ
| 
| _
| 
| (again, not great DD, just writing random thoug
```

### [5] PLTR short — pub=2025-10-04T01:22:20
- entry=2025-10-06, $179.18
- 1m: resolved_miss excess=-6.99% raw=-6.45%
- 1w: resolved_hit excess=+2.38%
- 3m: resolved_miss excess=-4.07%
- 6m: resolved_hit excess=+25.94%
- **条件 label**: ['PRICE_TARGET']
- **匹配**: `$200 support`
- **原文 (前 400 chars)**:
```
| Friday Market Close, Personal Thoughts and Explanations:
| 
| Strong Buy
| $RDDT
| $SNAP
| $AMZN
| $ETOR
| $NBIS
| $LTC
| 
| Buy
| $UPWK
| $MSTR
| $ORCL
| $TGT
| $CIFR
| $VIRT
| $CRDO
| $WULF
| $SOFI
| $META
| $AVGO
| $MRVL
| $SMCI
| $DELL
| 
| Hold
| $RKLB
| $TSM
| $IREN
| $RR
| $ALAB
| $HOOD
| $FLNC
| $EOSE
| $BE
| $RIOT
| $MARA
| $GRAB
| $ASTS
| $NVO
| $NVDA
| 
| Sell
| $TSLA
| $CRCL
| $PLTR
| $BMNR
| 
| Strong Sell
| $RGTI
| $OKLO
| $QBTS
| $IONQ
| 
| _
| 
| (again, not great DD, just writing random thoug
```

### [6] BMNR short — pub=2025-10-04T01:22:20
- entry=2025-10-06, $59.58
- 1m: resolved_hit excess=+33.23% raw=+33.77%
- 1w: resolved_hit excess=+5.86%
- 3m: resolved_hit excess=+46.37%
- 6m: resolved_hit excess=+63.38%
- **条件 label**: ['PRICE_TARGET']
- **匹配**: `$200 support`
- **原文 (前 400 chars)**:
```
| Friday Market Close, Personal Thoughts and Explanations:
| 
| Strong Buy
| $RDDT
| $SNAP
| $AMZN
| $ETOR
| $NBIS
| $LTC
| 
| Buy
| $UPWK
| $MSTR
| $ORCL
| $TGT
| $CIFR
| $VIRT
| $CRDO
| $WULF
| $SOFI
| $META
| $AVGO
| $MRVL
| $SMCI
| $DELL
| 
| Hold
| $RKLB
| $TSM
| $IREN
| $RR
| $ALAB
| $HOOD
| $FLNC
| $EOSE
| $BE
| $RIOT
| $MARA
| $GRAB
| $ASTS
| $NVO
| $NVDA
| 
| Sell
| $TSLA
| $CRCL
| $PLTR
| $BMNR
| 
| Strong Sell
| $RGTI
| $OKLO
| $QBTS
| $IONQ
| 
| _
| 
| (again, not great DD, just writing random thoug
```

### [7] RGTI short — pub=2025-10-04T01:22:20
- entry=2025-10-06, $38.80
- 1m: resolved_hit excess=+8.80% raw=+9.34%
- 1w: resolved_miss excess=-40.23%
- 3m: resolved_hit excess=+32.36%
- 6m: resolved_hit excess=+61.89%
- **条件 label**: ['PRICE_TARGET']
- **匹配**: `$200 support`
- **原文 (前 400 chars)**:
```
| Friday Market Close, Personal Thoughts and Explanations:
| 
| Strong Buy
| $RDDT
| $SNAP
| $AMZN
| $ETOR
| $NBIS
| $LTC
| 
| Buy
| $UPWK
| $MSTR
| $ORCL
| $TGT
| $CIFR
| $VIRT
| $CRDO
| $WULF
| $SOFI
| $META
| $AVGO
| $MRVL
| $SMCI
| $DELL
| 
| Hold
| $RKLB
| $TSM
| $IREN
| $RR
| $ALAB
| $HOOD
| $FLNC
| $EOSE
| $BE
| $RIOT
| $MARA
| $GRAB
| $ASTS
| $NVO
| $NVDA
| 
| Sell
| $TSLA
| $CRCL
| $PLTR
| $BMNR
| 
| Strong Sell
| $RGTI
| $OKLO
| $QBTS
| $IONQ
| 
| _
| 
| (again, not great DD, just writing random thoug
```

### [8] OKLO short — pub=2025-10-04T01:22:20
- entry=2025-10-06, $131.40
- 1m: resolved_hit excess=+14.05% raw=+14.59%
- 1w: resolved_miss excess=-28.87%
- 3m: resolved_hit excess=+23.04%
- 6m: resolved_hit excess=+62.42%
- **条件 label**: ['PRICE_TARGET']
- **匹配**: `$200 support`
- **原文 (前 400 chars)**:
```
| Friday Market Close, Personal Thoughts and Explanations:
| 
| Strong Buy
| $RDDT
| $SNAP
| $AMZN
| $ETOR
| $NBIS
| $LTC
| 
| Buy
| $UPWK
| $MSTR
| $ORCL
| $TGT
| $CIFR
| $VIRT
| $CRDO
| $WULF
| $SOFI
| $META
| $AVGO
| $MRVL
| $SMCI
| $DELL
| 
| Hold
| $RKLB
| $TSM
| $IREN
| $RR
| $ALAB
| $HOOD
| $FLNC
| $EOSE
| $BE
| $RIOT
| $MARA
| $GRAB
| $ASTS
| $NVO
| $NVDA
| 
| Sell
| $TSLA
| $CRCL
| $PLTR
| $BMNR
| 
| Strong Sell
| $RGTI
| $OKLO
| $QBTS
| $IONQ
| 
| _
| 
| (again, not great DD, just writing random thoug
```

### [9] QBTS short — pub=2025-10-04T01:22:20
- entry=2025-10-06, $32.01
- 1m: resolved_hit excess=+6.55% raw=+7.09%
- 1w: resolved_miss excess=-25.62%
- 3m: resolved_hit excess=+2.98%
- 6m: resolved_hit excess=+55.43%
- **条件 label**: ['PRICE_TARGET']
- **匹配**: `$200 support`
- **原文 (前 400 chars)**:
```
| Friday Market Close, Personal Thoughts and Explanations:
| 
| Strong Buy
| $RDDT
| $SNAP
| $AMZN
| $ETOR
| $NBIS
| $LTC
| 
| Buy
| $UPWK
| $MSTR
| $ORCL
| $TGT
| $CIFR
| $VIRT
| $CRDO
| $WULF
| $SOFI
| $META
| $AVGO
| $MRVL
| $SMCI
| $DELL
| 
| Hold
| $RKLB
| $TSM
| $IREN
| $RR
| $ALAB
| $HOOD
| $FLNC
| $EOSE
| $BE
| $RIOT
| $MARA
| $GRAB
| $ASTS
| $NVO
| $NVDA
| 
| Sell
| $TSLA
| $CRCL
| $PLTR
| $BMNR
| 
| Strong Sell
| $RGTI
| $OKLO
| $QBTS
| $IONQ
| 
| _
| 
| (again, not great DD, just writing random thoug
```

### [10] IONQ short — pub=2025-10-04T01:22:20
- entry=2025-10-06, $72.00
- 1m: resolved_hit excess=+25.32% raw=+25.86%
- 1w: resolved_miss excess=-12.74%
- 3m: resolved_hit excess=+28.19%
- 6m: resolved_hit excess=+59.76%
- **条件 label**: ['PRICE_TARGET']
- **匹配**: `$200 support`
- **原文 (前 400 chars)**:
```
| Friday Market Close, Personal Thoughts and Explanations:
| 
| Strong Buy
| $RDDT
| $SNAP
| $AMZN
| $ETOR
| $NBIS
| $LTC
| 
| Buy
| $UPWK
| $MSTR
| $ORCL
| $TGT
| $CIFR
| $VIRT
| $CRDO
| $WULF
| $SOFI
| $META
| $AVGO
| $MRVL
| $SMCI
| $DELL
| 
| Hold
| $RKLB
| $TSM
| $IREN
| $RR
| $ALAB
| $HOOD
| $FLNC
| $EOSE
| $BE
| $RIOT
| $MARA
| $GRAB
| $ASTS
| $NVO
| $NVDA
| 
| Sell
| $TSLA
| $CRCL
| $PLTR
| $BMNR
| 
| Strong Sell
| $RGTI
| $OKLO
| $QBTS
| $IONQ
| 
| _
| 
| (again, not great DD, just writing random thoug
```

### [11] BMNR short — pub=2025-10-19T18:21:35
- entry=2025-10-20, $52.75
- 1m: resolved_hit excess=+40.48% raw=+38.81%
- 1w: resolved_miss excess=-3.90%
- 3m: resolved_hit excess=+42.58%
- 6m: resolved_hit excess=+52.76%
- **条件 label**: ['PRICE_TARGET']
- **匹配**: `$400 PT`
- **原文 (前 400 chars)**:
```
| October 20th, Important Rate Cut Trading Week.
| 
| Personal thoughts and explanations: 
| 
| 🛝 = Swing Trade
| 
| 🐈 = Catalyst Trade
| 
| 🎇 = 2026 Trade, Tax Harvested
| 
| Fire Sale
| 🔥 $NBIS 
| 
| Strong Buy
| $TSM
| $AMKR
| $WLAC
| $AMZN
| $LTC 🐈
| $RDDT
| $HIMS 🛝
| $IBIT
| $ALAB
| $CRDO
| $SMCI
| $FLY 🎇
| $SNAP 🎇
| $ETOR 🎇
| $LULU 🎇
| 
| Buy
| $AMD
| $HOOD 
| $RBRK
| $UNH
| $TGT 🐈
| $IREN 🐈
| $WYFI
| $WULF
| $CIFR
| $SLNH
| $BITF
| $GLXY
| $FLNC
| $MU
| 
| (Skipping Hold, since any 
```

### [12] PL short — pub=2025-10-19T18:21:35
- entry=2025-10-20, $14.02
- 1m: resolved_hit excess=+20.00% raw=+18.33%
- 1w: resolved_hit excess=+2.99%
- 3m: resolved_miss excess=-88.51%
- 6m: resolved_miss excess=-178.64%
- **条件 label**: ['PRICE_TARGET']
- **匹配**: `$400 PT`
- **原文 (前 400 chars)**:
```
| October 20th, Important Rate Cut Trading Week.
| 
| Personal thoughts and explanations: 
| 
| 🛝 = Swing Trade
| 
| 🐈 = Catalyst Trade
| 
| 🎇 = 2026 Trade, Tax Harvested
| 
| Fire Sale
| 🔥 $NBIS 
| 
| Strong Buy
| $TSM
| $AMKR
| $WLAC
| $AMZN
| $LTC 🐈
| $RDDT
| $HIMS 🛝
| $IBIT
| $ALAB
| $CRDO
| $SMCI
| $FLY 🎇
| $SNAP 🎇
| $ETOR 🎇
| $LULU 🎇
| 
| Buy
| $AMD
| $HOOD 
| $RBRK
| $UNH
| $TGT 🐈
| $IREN 🐈
| $WYFI
| $WULF
| $CIFR
| $SLNH
| $BITF
| $GLXY
| $FLNC
| $MU
| 
| (Skipping Hold, since any 
```

### [13] BLSKY short — pub=2025-10-19T18:21:35
- entry=None
- 1m: skipped_no_price excess=+0.00% raw=+0.00%
- 1w: skipped_no_price excess=+0.00%
- 3m: skipped_no_price excess=+0.00%
- 6m: skipped_no_price excess=+0.00%
- **条件 label**: ['PRICE_TARGET']
- **匹配**: `$400 PT`
- **原文 (前 400 chars)**:
```
| October 20th, Important Rate Cut Trading Week.
| 
| Personal thoughts and explanations: 
| 
| 🛝 = Swing Trade
| 
| 🐈 = Catalyst Trade
| 
| 🎇 = 2026 Trade, Tax Harvested
| 
| Fire Sale
| 🔥 $NBIS 
| 
| Strong Buy
| $TSM
| $AMKR
| $WLAC
| $AMZN
| $LTC 🐈
| $RDDT
| $HIMS 🛝
| $IBIT
| $ALAB
| $CRDO
| $SMCI
| $FLY 🎇
| $SNAP 🎇
| $ETOR 🎇
| $LULU 🎇
| 
| Buy
| $AMD
| $HOOD 
| $RBRK
| $UNH
| $TGT 🐈
| $IREN 🐈
| $WYFI
| $WULF
| $CIFR
| $SLNH
| $BITF
| $GLXY
| $FLNC
| $MU
| 
| (Skipping Hold, since any 
```

### [14] RGTI short — pub=2025-10-19T18:21:35
- entry=2025-10-20, $47.48
- 1m: resolved_hit excess=+47.52% raw=+45.85%
- 1w: resolved_hit excess=+13.17%
- 3m: resolved_hit excess=+44.80%
- 6m: resolved_hit excess=+58.96%
- **条件 label**: ['PRICE_TARGET']
- **匹配**: `$400 PT`
- **原文 (前 400 chars)**:
```
| October 20th, Important Rate Cut Trading Week.
| 
| Personal thoughts and explanations: 
| 
| 🛝 = Swing Trade
| 
| 🐈 = Catalyst Trade
| 
| 🎇 = 2026 Trade, Tax Harvested
| 
| Fire Sale
| 🔥 $NBIS 
| 
| Strong Buy
| $TSM
| $AMKR
| $WLAC
| $AMZN
| $LTC 🐈
| $RDDT
| $HIMS 🛝
| $IBIT
| $ALAB
| $CRDO
| $SMCI
| $FLY 🎇
| $SNAP 🎇
| $ETOR 🎇
| $LULU 🎇
| 
| Buy
| $AMD
| $HOOD 
| $RBRK
| $UNH
| $TGT 🐈
| $IREN 🐈
| $WYFI
| $WULF
| $CIFR
| $SLNH
| $BITF
| $GLXY
| $FLNC
| $MU
| 
| (Skipping Hold, since any 
```

### [15] OKLO short — pub=2025-10-19T18:21:35
- entry=2025-10-20, $167.19
- 1m: resolved_hit excess=+43.87% raw=+42.20%
- 1w: resolved_hit excess=+15.72%
- 3m: resolved_hit excess=+42.98%
- 6m: resolved_hit excess=+48.73%
- **条件 label**: ['PRICE_TARGET']
- **匹配**: `$400 PT`
- **原文 (前 400 chars)**:
```
| October 20th, Important Rate Cut Trading Week.
| 
| Personal thoughts and explanations: 
| 
| 🛝 = Swing Trade
| 
| 🐈 = Catalyst Trade
| 
| 🎇 = 2026 Trade, Tax Harvested
| 
| Fire Sale
| 🔥 $NBIS 
| 
| Strong Buy
| $TSM
| $AMKR
| $WLAC
| $AMZN
| $LTC 🐈
| $RDDT
| $HIMS 🛝
| $IBIT
| $ALAB
| $CRDO
| $SMCI
| $FLY 🎇
| $SNAP 🎇
| $ETOR 🎇
| $LULU 🎇
| 
| Buy
| $AMD
| $HOOD 
| $RBRK
| $UNH
| $TGT 🐈
| $IREN 🐈
| $WYFI
| $WULF
| $CIFR
| $SLNH
| $BITF
| $GLXY
| $FLNC
| $MU
| 
| (Skipping Hold, since any 
```

### [16] IONQ short — pub=2025-10-19T18:21:35
- entry=2025-10-20, $65.31
- 1m: resolved_hit excess=+26.46% raw=+24.79%
- 1w: resolved_hit excess=+1.77%
- 3m: resolved_hit excess=+21.83%
- 6m: resolved_hit excess=+27.66%
- **条件 label**: ['PRICE_TARGET']
- **匹配**: `$400 PT`
- **原文 (前 400 chars)**:
```
| October 20th, Important Rate Cut Trading Week.
| 
| Personal thoughts and explanations: 
| 
| 🛝 = Swing Trade
| 
| 🐈 = Catalyst Trade
| 
| 🎇 = 2026 Trade, Tax Harvested
| 
| Fire Sale
| 🔥 $NBIS 
| 
| Strong Buy
| $TSM
| $AMKR
| $WLAC
| $AMZN
| $LTC 🐈
| $RDDT
| $HIMS 🛝
| $IBIT
| $ALAB
| $CRDO
| $SMCI
| $FLY 🎇
| $SNAP 🎇
| $ETOR 🎇
| $LULU 🎇
| 
| Buy
| $AMD
| $HOOD 
| $RBRK
| $UNH
| $TGT 🐈
| $IREN 🐈
| $WYFI
| $WULF
| $CIFR
| $SLNH
| $BITF
| $GLXY
| $FLNC
| $MU
| 
| (Skipping Hold, since any 
```

### [17] QBTS short — pub=2025-10-19T18:21:35
- entry=2025-10-20, $39.52
- 1m: resolved_hit excess=+43.65% raw=+41.98%
- 1w: resolved_hit excess=+9.26%
- 3m: resolved_hit excess=+27.96%
- 6m: resolved_hit excess=+45.60%
- **条件 label**: ['PRICE_TARGET']
- **匹配**: `$400 PT`
- **原文 (前 400 chars)**:
```
| October 20th, Important Rate Cut Trading Week.
| 
| Personal thoughts and explanations: 
| 
| 🛝 = Swing Trade
| 
| 🐈 = Catalyst Trade
| 
| 🎇 = 2026 Trade, Tax Harvested
| 
| Fire Sale
| 🔥 $NBIS 
| 
| Strong Buy
| $TSM
| $AMKR
| $WLAC
| $AMZN
| $LTC 🐈
| $RDDT
| $HIMS 🛝
| $IBIT
| $ALAB
| $CRDO
| $SMCI
| $FLY 🎇
| $SNAP 🎇
| $ETOR 🎇
| $LULU 🎇
| 
| Buy
| $AMD
| $HOOD 
| $RBRK
| $UNH
| $TGT 🐈
| $IREN 🐈
| $WYFI
| $WULF
| $CIFR
| $SLNH
| $BITF
| $GLXY
| $FLNC
| $MU
| 
| (Skipping Hold, since any 
```
