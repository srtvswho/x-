# P3-7e 17 条严格条件性 short — 逐条判定 + 查证 if 触发

**生成时间**: 2026-06-16T03:14:19.009189Z

## 0. 总结

**17 条 strict 条件性 short,按用户严格规则逐条判定**:

| pid_prefix | ticker | pub | if 条件 | 触发? | 判定 | 豁免? |
|---|---|---|---|---|---|---|
| c045c005 | BMNR | 2025-09-25 | 原文含 'way too overvalued but never short' | **never short 声明**(非触发条件,是她的明确动作声明) | B - 评级/never short,不是建仓 | ✅ 是 |
| c4163e7d | BMNR | 2025-09-26 | 'stay away from BMNR' + ETH 价格 $2200-$2400 | **ETH 没跌到 $2200**(1m 窗口 ETH 一直 $3.5k+) | B - 条件性,if 未触发 | ✅ 是 |
| 9c4e9d56 | TSLA | 2025-10-04 | Friday Market Close 'Sell $TSLA' | **Sell 列表评级** — 不是建仓 short,只是建议读者不要买 | B - 评级列表,不是建仓 | ✅ 是 |
| fdf9ca55 | CRCL | 2025-10-04 | Friday Market Close 'Sell $CRCL' | **Sell 列表评级** | B - 评级列表,不是建仓 | ✅ 是 |
| 4ec267e1 | PLTR | 2025-10-04 | Friday Market Close 'Sell $PLTR' | **Sell 列表评级** | B - 评级列表,不是建仓 | ✅ 是 |
| ac86c0f2 | BMNR | 2025-10-04 | Friday Market Close 'Sell $BMNR' | **Sell 列表评级** | B - 评级列表,不是建仓 | ✅ 是 |
| b01d49d5 | RGTI | 2025-10-04 | Friday Market Close 'Strong Sell $RGTI' | **Strong Sell 列表评级** | B - 评级列表,不是建仓 | ✅ 是 |
| b86fde2f | OKLO | 2025-10-04 | Friday Market Close 'Strong Sell $OKLO' | **Strong Sell 列表评级** | B - 评级列表,不是建仓 | ✅ 是 |
| 4ba2421e | QBTS | 2025-10-04 | Friday Market Close 'Strong Sell $QBTS' | **Strong Sell 列表评级** | B - 评级列表,不是建仓 | ✅ 是 |
| a288693d | IONQ | 2025-10-04 | Friday Market Close 'Strong Sell $IONQ' | **Strong Sell 列表评级** | B - 评级列表,不是建仓 | ✅ 是 |
| d8d72789 | BMNR | 2025-10-19 | October 20th 'Sell $BMNR' | **Sell 列表评级** | B - 评级列表,不是建仓 | ✅ 是 |
| c3f0b059 | PL | 2025-10-19 | October 20th 'Sell $PL' | **Sell 列表评级** | B - 评级列表,不是建仓 | ✅ 是 |
| 1ca2018f | BLSKY | 2025-10-19 | October 20th 'Sell $BLSKY' | **Sell 列表评级** | B - 评级列表,不是建仓 | ✅ 是 |
| df51c451 | RGTI | 2025-10-19 | October 20th 'Strong Sell $RGTI' | **Strong Sell 列表评级** | B - 评级列表,不是建仓 | ✅ 是 |
| 102a449e | OKLO | 2025-10-19 | October 20th 'Strong Sell $OKLO' | **Strong Sell 列表评级** | B - 评级列表,不是建仓 | ✅ 是 |
| 9507fe75 | IONQ | 2025-10-19 | October 20th 'Strong Sell $IONQ' | **Strong Sell 列表评级** | B - 评级列表,不是建仓 | ✅ 是 |
| d2f38a5d | QBTS | 2025-10-19 | October 20th 'Strong Sell $QBTS' | **Strong Sell 列表评级** | B - 评级列表,不是建仓 | ✅ 是 |

**豁免(B 改 neutral 或条件未触发)**: 17 条
**保留验证**: 0 条

## 1. 逐条原文 + 判定

### [c045c005] BMNR — pub=2025-09-25
- entry=2025-09-26, $49.58, 1m: resolved_miss, exc=-11.9%
- **if 条件**: 原文含 'way too overvalued but never short'
- **触发查证**: **never short 声明**(非触发条件,是她的明确动作声明)
- **判定**: **B - 评级/never short,不是建仓**
- **建议豁免**: ✅ 豁免 (B 改 neutral 或 condition_not_triggered)
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

### [c4163e7d] BMNR — pub=2025-09-26
- entry=2025-09-29, $52.12, 1m: resolved_miss, exc=-4.3%
- **if 条件**: 'stay away from BMNR' + ETH 价格 $2200-$2400
- **触发查证**: **ETH 没跌到 $2200**(1m 窗口 ETH 一直 $3.5k+)
- **判定**: **B - 条件性,if 未触发**
- **建议豁免**: ✅ 豁免 (B 改 neutral 或 condition_not_triggered)
- **原文 (前 400 chars)**:
```
| @SebastianS79509 I would just stay away from $BMNR. 
| 
| I bought 6 fig of $ETH at $1600. I'd buy again if it dipped to $2200-$2400 and swing trade it under $2800. 
| 
| Otherwise $3k+, especially $3.9k (where it's now), I wouldn't buy a dip.
```

### [9c4e9d56] TSLA — pub=2025-10-04
- entry=2025-10-06, $440.75, 1m: resolved_miss, exc=-1.3%
- **if 条件**: Friday Market Close 'Sell $TSLA'
- **触发查证**: **Sell 列表评级** — 不是建仓 short,只是建议读者不要买
- **判定**: **B - 评级列表,不是建仓**
- **建议豁免**: ✅ 豁免 (B 改 neutral 或 condition_not_triggered)
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

### [fdf9ca55] CRCL — pub=2025-10-04
- entry=2025-10-06, $154.01, 1m: resolved_hit, exc=+27.2%
- **if 条件**: Friday Market Close 'Sell $CRCL'
- **触发查证**: **Sell 列表评级**
- **判定**: **B - 评级列表,不是建仓**
- **建议豁免**: ✅ 豁免 (B 改 neutral 或 condition_not_triggered)
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

### [4ec267e1] PLTR — pub=2025-10-04
- entry=2025-10-06, $179.18, 1m: resolved_miss, exc=-7.0%
- **if 条件**: Friday Market Close 'Sell $PLTR'
- **触发查证**: **Sell 列表评级**
- **判定**: **B - 评级列表,不是建仓**
- **建议豁免**: ✅ 豁免 (B 改 neutral 或 condition_not_triggered)
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

### [ac86c0f2] BMNR — pub=2025-10-04
- entry=2025-10-06, $59.58, 1m: resolved_hit, exc=+33.2%
- **if 条件**: Friday Market Close 'Sell $BMNR'
- **触发查证**: **Sell 列表评级**
- **判定**: **B - 评级列表,不是建仓**
- **建议豁免**: ✅ 豁免 (B 改 neutral 或 condition_not_triggered)
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

### [b01d49d5] RGTI — pub=2025-10-04
- entry=2025-10-06, $38.80, 1m: resolved_hit, exc=+8.8%
- **if 条件**: Friday Market Close 'Strong Sell $RGTI'
- **触发查证**: **Strong Sell 列表评级**
- **判定**: **B - 评级列表,不是建仓**
- **建议豁免**: ✅ 豁免 (B 改 neutral 或 condition_not_triggered)
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

### [b86fde2f] OKLO — pub=2025-10-04
- entry=2025-10-06, $131.40, 1m: resolved_hit, exc=+14.0%
- **if 条件**: Friday Market Close 'Strong Sell $OKLO'
- **触发查证**: **Strong Sell 列表评级**
- **判定**: **B - 评级列表,不是建仓**
- **建议豁免**: ✅ 豁免 (B 改 neutral 或 condition_not_triggered)
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

### [4ba2421e] QBTS — pub=2025-10-04
- entry=2025-10-06, $32.01, 1m: resolved_hit, exc=+6.6%
- **if 条件**: Friday Market Close 'Strong Sell $QBTS'
- **触发查证**: **Strong Sell 列表评级**
- **判定**: **B - 评级列表,不是建仓**
- **建议豁免**: ✅ 豁免 (B 改 neutral 或 condition_not_triggered)
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

### [a288693d] IONQ — pub=2025-10-04
- entry=2025-10-06, $72.00, 1m: resolved_hit, exc=+25.3%
- **if 条件**: Friday Market Close 'Strong Sell $IONQ'
- **触发查证**: **Strong Sell 列表评级**
- **判定**: **B - 评级列表,不是建仓**
- **建议豁免**: ✅ 豁免 (B 改 neutral 或 condition_not_triggered)
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

### [d8d72789] BMNR — pub=2025-10-19
- entry=2025-10-20, $52.75, 1m: resolved_hit, exc=+40.5%
- **if 条件**: October 20th 'Sell $BMNR'
- **触发查证**: **Sell 列表评级**
- **判定**: **B - 评级列表,不是建仓**
- **建议豁免**: ✅ 豁免 (B 改 neutral 或 condition_not_triggered)
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

### [c3f0b059] PL — pub=2025-10-19
- entry=2025-10-20, $14.02, 1m: resolved_hit, exc=+20.0%
- **if 条件**: October 20th 'Sell $PL'
- **触发查证**: **Sell 列表评级**
- **判定**: **B - 评级列表,不是建仓**
- **建议豁免**: ✅ 豁免 (B 改 neutral 或 condition_not_triggered)
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

### [1ca2018f] BLSKY — pub=2025-10-19
- entry=None, $0.00, 1m: skipped_no_price, exc=+0.0%
- **if 条件**: October 20th 'Sell $BLSKY'
- **触发查证**: **Sell 列表评级**
- **判定**: **B - 评级列表,不是建仓**
- **建议豁免**: ✅ 豁免 (B 改 neutral 或 condition_not_triggered)
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

### [df51c451] RGTI — pub=2025-10-19
- entry=2025-10-20, $47.48, 1m: resolved_hit, exc=+47.5%
- **if 条件**: October 20th 'Strong Sell $RGTI'
- **触发查证**: **Strong Sell 列表评级**
- **判定**: **B - 评级列表,不是建仓**
- **建议豁免**: ✅ 豁免 (B 改 neutral 或 condition_not_triggered)
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

### [102a449e] OKLO — pub=2025-10-19
- entry=2025-10-20, $167.19, 1m: resolved_hit, exc=+43.9%
- **if 条件**: October 20th 'Strong Sell $OKLO'
- **触发查证**: **Strong Sell 列表评级**
- **判定**: **B - 评级列表,不是建仓**
- **建议豁免**: ✅ 豁免 (B 改 neutral 或 condition_not_triggered)
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

### [9507fe75] IONQ — pub=2025-10-19
- entry=2025-10-20, $65.31, 1m: resolved_hit, exc=+26.5%
- **if 条件**: October 20th 'Strong Sell $IONQ'
- **触发查证**: **Strong Sell 列表评级**
- **判定**: **B - 评级列表,不是建仓**
- **建议豁免**: ✅ 豁免 (B 改 neutral 或 condition_not_triggered)
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

### [d2f38a5d] QBTS — pub=2025-10-19
- entry=2025-10-20, $39.52, 1m: resolved_hit, exc=+43.7%
- **if 条件**: October 20th 'Strong Sell $QBTS'
- **触发查证**: **Strong Sell 列表评级**
- **判定**: **B - 评级列表,不是建仓**
- **建议豁免**: ✅ 豁免 (B 改 neutral 或 condition_not_triggered)
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

## 2. 判定原则

**B 类(风险提示 / 评级列表 / never short 声明)** 的标准:

1. **明确的 never short 声明** — 原文 'never short' 等明示她不会建仓
2. **评级列表** — 'Friday Market Close' / 'October 20th' 等综合评级推文,虽然含 'Sell'/'Strong Sell' 标签,但**不是建仓 short 仓位**,只是建议读者卖
3. **条件未触发** — 'if 价格/事件' 在 1m/3m/6m 窗口内未发生,她没建仓

**A 类(真建仓 short)保留**: 明确建仓声明 + 论据(IREN 24 条 'bearish on $6B ATM', CRCL 'great short if above 1/2 COIN' 实际价格条件没触发但她**整体 7 条**都明确说'go short' — 整体看是阶段性看空立场)

**B 类豁免的具体操作**: 改 predictions.direction='neutral',verifications 标 skipped_risk_note,移出 hit_rate 分母