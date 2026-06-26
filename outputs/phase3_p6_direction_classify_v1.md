# Phase 3 P3-6 逐条分诊 — 163 short → A/B/C 类

**运行时间**: 2026-06-16T02:26:34.614848Z

## 分类规则

- **A 类**: 真·反向持仓/明确反向观点(有论据、有时间、有目标价或催化剂)。保留 short 验证。
- **B 类**: 风险提示/谨慎/中性,不是建仓。改 neutral,不当 short 头寸算盈亏。
- **C 类**: 明确误判(原文中性/看多被抽 short)。改回正确方向。

## 1. 总体分类统计

- 已分类: 1 条 (A=0  B=0  C=1)
- 待分类: 162 条

## 2. 已分类逐条


### C 类 — 明确误判 (1 条)

| ticker | pred_id | pub | entry | px | 1m_status | 1m_excess |
|---|---|---|---|---|---|---|
| MU | `9106c8f1` | 2025-10-11 | 2025-10-13 | $190.79 | 190.79 | -26.37% |

## 3. 待分类(等你确认)

以下 ticker 的 short 我还没看原文,需要你确认分类:


### AAOI (n_long=186  n_short=3)


**[1]** pred=`4b73f50f-ed3d-4d91-80ca-b0375a67c969` pub=2026-03-12 entry=2026-03-13 px=$104.37
- LLM: dir=short conv=3 hz=event_driven qc=None hedged=0
- 1m: 104.37 raw=N/A excess=-40.26%
- 原文: `It’s usually better to just hold stocks long term and forget about it. As you never know if there’s going to be a surprise hyperscaler deal the next day. 

However, this is net bearish near term with a PTSD overhang that $AAOI pulls a $POET and keeps diluting if the new $250m atm is successful. 

But if you bought at $28, you wouldn’t need to care about to short term -20% to 20% day to day changes happening around $100`

**[2]** pred=`c8805d70-58a1-43a8-b082-159ab08b1e43` pub=2026-03-12 entry=2026-03-13 px=$104.37
- LLM: dir=short conv=2 hz=short_term qc=None hedged=0
- 1m: 104.37 raw=N/A excess=-40.26%
- 原文: `It happens. My guess is they’re probably selling $250m worth around $100 again like their previous ATM.

Short term bearish, long term likely accretive unless $AAOI repeat use ATM beyond what they actually need to execute. 

That was the overhang I was mad with $AAOI management about, because now there’s more uncertainty given they should have just announced what they needed from the start.`

**[3]** pred=`6dd0479f-6162-4234-8543-31be57862dfc` pub=2026-03-13 entry=2026-03-16 px=$100.00
- LLM: dir=short conv=3 hz=short_term qc=None hedged=0
- 1m: 100.0 raw=N/A excess=-42.55%
- 原文: `Short term, $AAOI is diluting $250m at $100 so probably won’t go too high above that number for awhile. 

Cause they’re selling it but the open market at that price. They tapped into their last ATM ASAP. 

Mid-Long term doesn’t really matter.

If I put on my day trading glasses, if it drops one more time to the $80s, strong yes imo.`


### ALAB (n_long=38  n_short=2)


**[1]** pred=`fa185bc7-9ebf-4035-9336-79782bf5afa3` pub=2025-09-08 entry=2025-09-09 px=$213.31
- LLM: dir=short conv=3 hz=event_driven qc=None hedged=0
- 1m: 213.305 raw=N/A excess=-2.84%
- 原文: `Changed my mind on $ALAB, took profit at $217 so exited long and opened up short with $CREDO as a hedge.

ALAB feels a bit overbought after going up 14%.

$CREDO should play catchup soon though. https://t.co/oDIuqi0mFn`

**[2]** pred=`b3da1f01-ad79-4f2c-85dc-46a98debdd4d` pub=2025-09-16 entry=2025-09-17 px=$244.22
- LLM: dir=short conv=3 hz=long_term qc=None hedged=0
- 1m: 244.225 raw=N/A excess=+33.03%
- 原文: `@DanielTan64198 Yeah $LTC is great for the next month! 

 $NBIS / $TSM is amazing over the next year. I still think $ETH / $ALAB is a bit overvalued at this point so you closed at a good time. 

$SG might need a bit of time to wait.`


### AMD (n_long=31  n_short=1)


**[1]** pred=`03da89f9-2001-4705-b046-c9e2dcb5b496` pub=2025-12-05 entry=2025-12-08 px=$219.09
- LLM: dir=short conv=3 hz=long_term qc=None hedged=0
- 1m: 219.085 raw=N/A excess=+6.58%
- 原文: `My stance changed on $AMD after LLMs like opus 4.5 beat gpt codex models in coding, gemini 3 models beat out chatgpt models in image generation, etc.

A large part of my initial bullishness on $AMD was expecting OpenAI to maintain its dominance in LLMs, IPO, and find a way to generate that $1T+ in capex spend that they promised.

But it's becoming less and less likely as time goes on, so I've become more bearish on stuff dependent on OpenAI ( $CRWV, $ORCL, $MSFT etc.)

Large part of $AMD's most ...`


### ARM (n_long=13  n_short=1)


**[1]** pred=`df20f804-ed72-4e20-b0b8-1bca9cdf4160` pub=2026-03-24 entry=2026-03-25 px=$148.25
- LLM: dir=short conv=3 hz=long_term qc=None hedged=0
- 1m: 148.255 raw=N/A excess=-58.38%
- 原文: `I'm actually personally pretty bearish on both $ARM and $QLCM.

Probably not the best person to ask on $ARM since I did help out RISC-V quite a bit so I'm a little biased.  

As for Qualcomm... Mediatek is probably better long, especially with their high growth ASIC arm working with $GOOGL.`


### AUO (n_long=0  n_short=1)


**[1]** pred=`132dc397-7b55-438c-b535-1a1b69f74323` pub=2026-05-14 entry=None px=NULL
- LLM: dir=short conv=3 hz=1y qc=None hedged=0
- 1m: None raw=N/A excess=N/A
- 原文: `IMO anything MicroLED is a waste of capital for CPO/photonics exposure over the next year.

Names like ams-OSRAM/AUO/Ennostar/Tyntek/PlayNitride, etc. 

Any volume shipments would probably be H2 2028 or H1 2029 if it even takes off from development stage. 

You're better looking at them for their other business segments.`


### AXTI (n_long=156  n_short=1)


**[1]** pred=`39e9dee8-b564-4775-8c30-5675a80e55be` pub=2026-04-06 entry=2026-04-07 px=$42.70
- LLM: dir=short conv=3 hz=event_driven qc=None hedged=0
- 1m: 42.7 raw=N/A excess=-145.50%
- 原文: `If you’re curious about $AXTI:

It’s down 21% on the new potential dilution news.

Board wanted to add 50M more shares (up to $2B worth to dilute) for shareholders vote in the 14th.

70m -> 120m shares.

I say this about $IREN excessive $6B dilution and it’s the same with AXT price proposal that I hold. 

I would not “trust in management” to use it wisely and the fact it’s filed is a red flag.

That being said: we’ll see what happens on the 14th. If it passes for 50m more share authorized diluti...`


### BABA (n_long=0  n_short=1)


**[1]** pred=`cb27aa2f-2f28-43b1-97db-308e393fbdd9` pub=2026-02-02 entry=2026-02-03 px=$163.88
- LLM: dir=short conv=3 hz=event_driven qc=None hedged=0
- 1m: 163.88 raw=N/A excess=+20.46%
- 原文: `Markets are seeing liquidation cascades.

Silver's crash is now extending into other markets like Crypto and US/Foreign stocks.

Here's what's happening:

And here's what to expect from:

- $BMNR (Crypto)
- $RKLB (High-Beta)  
- $SNDK (AI) 
- to Samsung (Foreign). 

The "Warsh" Fed Chair nomination was the initial trigger that caused the selloff as markets viewed him as a "Hawk" -> Quantitative Tightening. 

However, this is a mistake as the fed chair is likely aligned with Trump's policies, and...`


### BKSY (n_long=1  n_short=2)


**[1]** pred=`4f6296df-6763-4266-8b37-cdbded5e1194` pub=2025-10-11 entry=2025-10-13 px=$27.81
- LLM: dir=short conv=2 hz=6m qc=None hedged=0
- 1m: 27.81 raw=N/A excess=+42.22%
- 原文: `Based Friday Market Close (-3.6% SPY day), Thoughts and Explanations

Strong Buy
$IBIT
$LTC
$WLAC
$NBIS
$MP
$TSM
(For Next Year)
$ETOR
$DKNG
$SNAP

Buy
$UPWK
$CRDO
$ALAB
$AMZN
$META
$UNH
$SG
$TGT
$BULL
$FLY
$CIFR
$WULF
$IREN
$GLXY
$SMCI
$DELL
$MRVL

Hold
$RKLB
$HOOD
$RBRK
$MU
$HOOD
$GRAB
$MARA
$RIOT
$NVO
$RR
$ELOSE
$FLNC
$SEI
$PLTR

Sell
$CRCL
$ETH
$BMNR
$PL
$BKSY

Strong Sell
$RGTI
$OKLO
$IONQ
$QBTS
$QUBT

_

Explanations:

IBIT - Dumped to $104k, Bitcoin demand has been institutional, tariff f...`

**[2]** pred=`0490c0ef-e2ca-4e5d-ac56-5e65f505def5` pub=2025-10-12 entry=2025-10-13 px=$27.81
- LLM: dir=short conv=2 hz=6m qc=None hedged=0
- 1m: 27.81 raw=N/A excess=+42.22%
- 原文: `And there’s the de-escalation

Reuters: “Taiwan sees no significant impact on chip sector”

Trump: “Don’t worry about China, it will all be fine… President Xi just had a bad moment.”

Biggest crypto liquidation to date 

Stocks with little impact down 7%

Dip buying opportunity https://t.co/2sUEV7Dg8s`


### BLSKY (n_long=0  n_short=1)


**[1]** pred=`1ca2018f-b24f-477f-ac8f-7fecaba5ebdf` pub=2025-10-19 entry=None px=NULL
- LLM: dir=short conv=2 hz=6m qc=None hedged=0
- 1m: None raw=N/A excess=N/A
- 原文: `October 20th, Important Rate Cut Trading Week.

Personal thoughts and explanations: 

🛝 = Swing Trade

🐈 = Catalyst Trade

🎇 = 2026 Trade, Tax Harvested

Fire Sale
🔥 $NBIS 

Strong Buy
$TSM
$AMKR
$WLAC
$AMZN
$LTC 🐈
$RDDT
$HIMS 🛝
$IBIT
$ALAB
$CRDO
$SMCI
$FLY 🎇
$SNAP 🎇
$ETOR 🎇
$LULU 🎇

Buy
$AMD
$HOOD 
$RBRK
$UNH
$TGT 🐈
$IREN 🐈
$WYFI
$WULF
$CIFR
$SLNH
$BITF
$GLXY
$FLNC
$MU

(Skipping Hold, since any other stock I've mentioned in the past, it probably just hold it since nothing's changed).

Sell
$ET...`


### BMNR (n_long=1  n_short=12)


**[1]** pred=`c045c005-91d6-46ca-bb06-9447f3958c1a` pub=2025-09-25 entry=2025-09-26 px=$49.58
- LLM: dir=short conv=3 hz=event_driven qc=None hedged=0
- 1m: 49.58 raw=N/A excess=-8.33%
- 原文: `So daily thoughts on Sept 25th + market drop if you like my insights: 

1. 3x rate cut went from 65% to 56% from data today. This is a lot more material, since people are front-running rate cuts now. 

Either way, any rate cut usually lead to large inflows so it's generally bullish for markets months out. 

Powell's thoughts about market being overvalued holds kind of true for certain stocks. Oklo, Quantum, etc. way too overvalued but never short. Even stuff i love like RKLB, really overvalued. ...`

**[2]** pred=`c4163e7d-fae4-4f19-b582-843a116cc613` pub=2025-09-26 entry=2025-09-29 px=$52.12
- LLM: dir=short conv=3 hz=long_term qc=None hedged=0
- 1m: 52.12 raw=N/A excess=-0.81%
- 原文: `@SebastianS79509 I would just stay away from $BMNR. 

I bought 6 fig of $ETH at $1600. I'd buy again if it dipped to $2200-$2400 and swing trade it under $2800. 

Otherwise $3k+, especially $3.9k (where it's now), I wouldn't buy a dip.`

**[3]** pred=`19fc437c-9d47-46f3-93a8-334abd81cf7b` pub=2025-09-29 entry=2025-09-30 px=$51.76
- LLM: dir=short conv=2 hz=6m qc=None hedged=0
- 1m: 51.76 raw=N/A excess=+3.86%
- 原文: `Monday Market Close Thoughts:

Extremely Strong Buy
$NBIS
$ETOR
$LTC
$VIRT

Buy
$AMZN
$SMCI
$TGT
$CRM
$TSM
$CRDO
$SG
$CIFR
$LULU
$SLNH
$ORCL
$MSTR
$RIOT
$MARA

Hold
$IREN
$HIMS
$RKLB
$PYPL
$MRVL
$IBIT
$UPWK
$GRAB
$ALAB
$ASTS
$SOFI
$NVDA
$NVO

Sell
$HOOD
$TSLA
$RDDT
$CRCL
$PLTR
$BMNR

Strong Sell
$OKLO
$QBTS
$IONQ

_

Feel free to disagree but these are just my thoughts

Strong Buy Explanations

- Bought ~$70K of Virtu calls, 28% IV and just 6.6 forward p/e is undervalued.

- Always DCA NBIS on t...`

**[4]** pred=`ac86c0f2-7dd3-489a-8dea-9bdb410525c1` pub=2025-10-04 entry=2025-10-06 px=$59.58
- LLM: dir=short conv=2 hz=6m qc=None hedged=0
- 1m: 59.58 raw=N/A excess=+33.77%
- 原文: `Friday Market Close, Personal Thoughts and Explanations:

Strong Buy
$RDDT
$SNAP
$AMZN
$ETOR
$NBIS
$LTC

Buy
$UPWK
$MSTR
$ORCL
$TGT
$CIFR
$VIRT
$CRDO
$WULF
$SOFI
$META
$AVGO
$MRVL
$SMCI
$DELL

Hold
$RKLB
$TSM
$IREN
$RR
$ALAB
$HOOD
$FLNC
$EOSE
$BE
$RIOT
$MARA
$GRAB
$ASTS
$NVO
$NVDA

Sell
$TSLA
$CRCL
$PLTR
$BMNR

Strong Sell
$RGTI
$OKLO
$QBTS
$IONQ

_

(again, not great DD, just writing random thoughts about the process). 

Strong Buys

Reddit - Dropped 29% off immaterial news that ChatGPT wasn't ...`

**[5]** pred=`86582047-4485-435a-a15f-a3e2677a5b6a` pub=2025-10-11 entry=2025-10-13 px=$54.21
- LLM: dir=short conv=2 hz=6m qc=None hedged=0
- 1m: 54.21 raw=N/A excess=+26.97%
- 原文: `Based Friday Market Close (-3.6% SPY day), Thoughts and Explanations

Strong Buy
$IBIT
$LTC
$WLAC
$NBIS
$MP
$TSM
(For Next Year)
$ETOR
$DKNG
$SNAP

Buy
$UPWK
$CRDO
$ALAB
$AMZN
$META
$UNH
$SG
$TGT
$BULL
$FLY
$CIFR
$WULF
$IREN
$GLXY
$SMCI
$DELL
$MRVL

Hold
$RKLB
$HOOD
$RBRK
$MU
$HOOD
$GRAB
$MARA
$RIOT
$NVO
$RR
$ELOSE
$FLNC
$SEI
$PLTR

Sell
$CRCL
$ETH
$BMNR
$PL
$BKSY

Strong Sell
$RGTI
$OKLO
$IONQ
$QBTS
$QUBT

_

Explanations:

IBIT - Dumped to $104k, Bitcoin demand has been institutional, tariff f...`

**[6]** pred=`b67c853e-8f32-4ff4-8a75-77e99391ed20` pub=2025-10-12 entry=2025-10-13 px=$54.21
- LLM: dir=short conv=2 hz=6m qc=None hedged=0
- 1m: 54.21 raw=N/A excess=+26.97%
- 原文: `And there’s the de-escalation

Reuters: “Taiwan sees no significant impact on chip sector”

Trump: “Don’t worry about China, it will all be fine… President Xi just had a bad moment.”

Biggest crypto liquidation to date 

Stocks with little impact down 7%

Dip buying opportunity https://t.co/2sUEV7Dg8s`

**[7]** pred=`d8d72789-e08e-4d89-8329-0e9e1ba15853` pub=2025-10-19 entry=2025-10-20 px=$52.75
- LLM: dir=short conv=2 hz=6m qc=None hedged=0
- 1m: 52.75 raw=N/A excess=+38.81%
- 原文: `October 20th, Important Rate Cut Trading Week.

Personal thoughts and explanations: 

🛝 = Swing Trade

🐈 = Catalyst Trade

🎇 = 2026 Trade, Tax Harvested

Fire Sale
🔥 $NBIS 

Strong Buy
$TSM
$AMKR
$WLAC
$AMZN
$LTC 🐈
$RDDT
$HIMS 🛝
$IBIT
$ALAB
$CRDO
$SMCI
$FLY 🎇
$SNAP 🎇
$ETOR 🎇
$LULU 🎇

Buy
$AMD
$HOOD 
$RBRK
$UNH
$TGT 🐈
$IREN 🐈
$WYFI
$WULF
$CIFR
$SLNH
$BITF
$GLXY
$FLNC
$MU

(Skipping Hold, since any other stock I've mentioned in the past, it probably just hold it since nothing's changed).

Sell
$ET...`

**[8]** pred=`6d155732-487a-4a16-b625-7e4748afe826` pub=2025-11-19 entry=2025-11-20 px=$30.24
- LLM: dir=short conv=2 hz=6m qc=None hedged=0
- 1m: 30.24 raw=N/A excess=+1.52%
- 原文: `The Great Reset, November 19th ratings:

Strong Buy

· $NBIS
· $CIFR
· $WULF
· $RDDT
· $SNAP
· $ALAB
· $META
· $AMZN
· $GOOGL
· $IBIT
· $SOL
· $TSM
· $RKLB
· $TSSI
· $SMCI
· $GLXY
· $SG

Buy

· $IREN
· $KRUS
· $CRCL
· $LTC
· $MRVL
· $KRKNF
· $OSS
· $CORZ
· $WLAC
· $WYFI
· $AMD
· $TE
· $CRDO
· $FLNC
· $HIMS
· $BULL
· $ETOR
· $FISV
· $FLY
· $MU

Hold

· $COIN
· $HOOD
· $IBKR
· $NVDA
· $PLTR
· $TSLA
· CRWV
· $APLD
· ORCL

Avoid

· RGTI
· $IONQ
· SLNH
· $QBTS
· OKLO
· $WMT
· BMNR
· $SBET
· CRWV
_

E...`

**[9]** pred=`91026989-8dbf-4f54-8403-65ff26a97ced` pub=2025-12-01 entry=2025-12-02 px=$30.67
- LLM: dir=short conv=3 hz=long_term qc=None hedged=0
- 1m: 30.67 raw=N/A excess=-1.70%
- 原文: `So, that just reinforced my point more. L2s get even cheaper data availability, which is good for scaling but doesn't address value accrual to ETH.

I've maintained Ethereum managed to scale. And it's a great network to develop on. But all that at the cost of $ETH appreciation, which is why I'm bearish also on $BMNR.

ETH's L2 idea was originally good for ETH price because scarce blockspace + rising usage = fee/burn flywheel.

But: Fusaka -> more blobs -> cheaper DA -> lower L2 fees. Not good fo...`

**[10]** pred=`038c6c56-b48e-47d4-8d3d-e0748ef9bfd9` pub=2026-01-02 entry=2026-01-05 px=$32.48
- LLM: dir=short conv=2 hz=6m qc=None hedged=0
- 1m: 32.48 raw=N/A excess=+37.50%
- 原文: `Welcome to 2026. Jan 1st ratings:

Strong Buy:
$TTD
$SMCI
$AIRO
$INTC
$HIMS
$AXTI
$TSM
$NBIS
$CIFR
Samsung Electronics (KRX: 005930)
$HUT
$IREN
$WULF
$GLXY
$TSSI
$META
$ETOR
$CRCL

Buy:
$KRKNF
$ONDS
$GEMI
$NVDA
$MU
$AMKR
SK Hynix
$SNAP
$RDDT
$AAOI
$COHR
$FISV
$FLY
$DJT
$LITE
$AMZN
$MRVL
$AVGO
$OSS
$BULL
$ORCL
$CRDO
$ALAB

Avoid:
$RGTI
$QBTS
$RGTI
$BMNR
$ETH
$PLTR
$WMT

_

TLDR thoughts:

TTD - Complete valuation reset dropping 67% YTD, compounded by EOY tax sell-off. Great recovery play going in...`

**[11]** pred=`5e3d3160-3bc9-454b-a47e-f1de477dcd63` pub=2026-02-02 entry=2026-02-03 px=$23.09
- LLM: dir=short conv=3 hz=event_driven qc=None hedged=0
- 1m: 23.09 raw=N/A excess=+11.87%
- 原文: `Markets are seeing liquidation cascades.

Silver's crash is now extending into other markets like Crypto and US/Foreign stocks.

Here's what's happening:

And here's what to expect from:

- $BMNR (Crypto)
- $RKLB (High-Beta)  
- $SNDK (AI) 
- to Samsung (Foreign). 

The "Warsh" Fed Chair nomination was the initial trigger that caused the selloff as markets viewed him as a "Hawk" -> Quantitative Tightening. 

However, this is a mistake as the fed chair is likely aligned with Trump's policies, and...`

**[12]** pred=`6a5d75b7-e36a-4a6b-b24a-5d8b89f0cd51` pub=2026-02-17 entry=2026-02-18 px=$20.08
- LLM: dir=short conv=3 hz=3m qc=None hedged=0
- 1m: 20.08 raw=N/A excess=-5.28%
- 原文: `This data is alarming... Robinhood users lost a collective:

- $24.6 Billion USD in Q4 2025. 

With Robinhood portfolios on X consisting of :

$HIMS, $DUOL, and $BMNR.

Q1 2026 is likely to be even worse, as these names drop 50-70%+. 

Everyone thinks they're Warren Buffet, making profit from Duolingo, $CRWV, and $ASST in an extreme bull market. 

But as markets turn sour: 

We'll start to see the real traders and investors, who are able to profit in any market condition.`


### BOA (n_long=1  n_short=1)


**[1]** pred=`6222569b-72c6-4c39-aad4-e750ea498bcb` pub=2026-01-01 entry=None px=NULL
- LLM: dir=short conv=2 hz=long_term qc=None hedged=0
- 1m: None raw=N/A excess=N/A
- 原文: `2026 Newsletter.

Thematic Investments: Evolution, Disruption, and Bottlenecks

1. Soft Robotics - Evolution to $TSLA, $ONDS, Boston Dynamics. 

2. SiPh - InP Bottleneck | $AXTI, $LITE, $GOOGL

3. Glass Substrates - Bottleneck | $NVDA, $INTC, $TSM

4. Money Movement - Disruption to $V, Stripe, $BOA

5. AI Cloud Layers - Bottleneck | $NBIS, $IREN, $HUT. 

6. LLM Cybersecuirty - Evolution to $CRWD, $CSCO, $MSFT 

7. LEO Space Infrastructure | Evolution to $RKLB,  SpaceX, $ASTS

8. Consumer Agentic...`


### CRCL (n_long=32  n_short=8)


**[1]** pred=`a022dabf-2f42-47d5-a190-2822bf7a07fe` pub=2025-08-23 entry=2025-08-25 px=$134.36
- LLM: dir=short conv=2 hz=6m qc=None hedged=0
- 1m: 134.36 raw=N/A excess=+2.07%
- 原文: `Some decent recovery/swing trades right now

1. $SG - $9.39
2. $SNAP - $7.21
3. $UNH - $306.8
4. $ETOR - $46.8
5. $NVO - $57.00
6. $HIMS - $44.73
7. $CRWV - $94.7

Stay away from these dips

1. $CRCL - $136.2
2. $PLTR - $159.6
3. $DUOL - $334.5`

**[2]** pred=`99c9167c-3cf2-4388-b0b0-21bd4a0762f3` pub=2025-09-16 entry=2025-09-17 px=$135.00
- LLM: dir=short conv=4 hz=event_driven qc=None hedged=0
- 1m: 135.0 raw=N/A excess=+4.84%
- 原文: `Rant: this $CRCL chart is a great lesson on why TA means very little - fundamentals matter more.

When people were posting $BULL TA's at IPO, I was doing arbitrage between warrants and rolling my eyes. 

BULL went from $10 to $70+ but people were trading on 1% of float. When shares were unlocked, BULL went back to $10 IPO price.

For CRCL, we saw the rally from $31 IPO price to $200+ because people are trading on a limited float and MC was almost the same as $COIN. (which has 50% interest revenu...`

**[3]** pred=`a04629a9-7eb7-4877-b79c-43e9d538b846` pub=2025-09-16 entry=2025-09-17 px=$135.00
- LLM: dir=short conv=3 hz=event_driven qc=None hedged=0
- 1m: 135.0 raw=N/A excess=+4.84%
- 原文: `We agree about irrational markets - but your reading comprehension is about as good as your TA.

The point you missed: TA is useless when it ignores float + fundamentals. If 1% of float drives MC and 99% unlocks later like $BULL, charts don’t matter.

The only valuation point I made was that $CRCL is a great short if it ever trades above 1/2 of $COIN, since interest income is split 50-50. I’m bullish on USDC but Circle at $200 today would be worth more than half of Coinbase.

Anyway, drawing a T...`

**[4]** pred=`bb41fff1-6336-4b8f-a69e-7fea4175dd4f` pub=2025-09-29 entry=2025-09-30 px=$136.20
- LLM: dir=short conv=2 hz=6m qc=None hedged=0
- 1m: 136.2 raw=N/A excess=+3.27%
- 原文: `Monday Market Close Thoughts:

Extremely Strong Buy
$NBIS
$ETOR
$LTC
$VIRT

Buy
$AMZN
$SMCI
$TGT
$CRM
$TSM
$CRDO
$SG
$CIFR
$LULU
$SLNH
$ORCL
$MSTR
$RIOT
$MARA

Hold
$IREN
$HIMS
$RKLB
$PYPL
$MRVL
$IBIT
$UPWK
$GRAB
$ALAB
$ASTS
$SOFI
$NVDA
$NVO

Sell
$HOOD
$TSLA
$RDDT
$CRCL
$PLTR
$BMNR

Strong Sell
$OKLO
$QBTS
$IONQ

_

Feel free to disagree but these are just my thoughts

Strong Buy Explanations

- Bought ~$70K of Virtu calls, 28% IV and just 6.6 forward p/e is undervalued.

- Always DCA NBIS on t...`

**[5]** pred=`fdf9ca55-f0c7-430d-b200-d617c77c8227` pub=2025-10-04 entry=2025-10-06 px=$154.01
- LLM: dir=short conv=2 hz=6m qc=None hedged=0
- 1m: 154.01 raw=N/A excess=+27.76%
- 原文: `Friday Market Close, Personal Thoughts and Explanations:

Strong Buy
$RDDT
$SNAP
$AMZN
$ETOR
$NBIS
$LTC

Buy
$UPWK
$MSTR
$ORCL
$TGT
$CIFR
$VIRT
$CRDO
$WULF
$SOFI
$META
$AVGO
$MRVL
$SMCI
$DELL

Hold
$RKLB
$TSM
$IREN
$RR
$ALAB
$HOOD
$FLNC
$EOSE
$BE
$RIOT
$MARA
$GRAB
$ASTS
$NVO
$NVDA

Sell
$TSLA
$CRCL
$PLTR
$BMNR

Strong Sell
$RGTI
$OKLO
$QBTS
$IONQ

_

(again, not great DD, just writing random thoughts about the process). 

Strong Buys

Reddit - Dropped 29% off immaterial news that ChatGPT wasn't ...`

**[6]** pred=`6910ce9e-f4c1-4d35-bf27-ed7ec8fe7b19` pub=2025-10-11 entry=2025-10-13 px=$138.06
- LLM: dir=short conv=2 hz=6m qc=None hedged=0
- 1m: 138.06 raw=N/A excess=+28.80%
- 原文: `Based Friday Market Close (-3.6% SPY day), Thoughts and Explanations

Strong Buy
$IBIT
$LTC
$WLAC
$NBIS
$MP
$TSM
(For Next Year)
$ETOR
$DKNG
$SNAP

Buy
$UPWK
$CRDO
$ALAB
$AMZN
$META
$UNH
$SG
$TGT
$BULL
$FLY
$CIFR
$WULF
$IREN
$GLXY
$SMCI
$DELL
$MRVL

Hold
$RKLB
$HOOD
$RBRK
$MU
$HOOD
$GRAB
$MARA
$RIOT
$NVO
$RR
$ELOSE
$FLNC
$SEI
$PLTR

Sell
$CRCL
$ETH
$BMNR
$PL
$BKSY

Strong Sell
$RGTI
$OKLO
$IONQ
$QBTS
$QUBT

_

Explanations:

IBIT - Dumped to $104k, Bitcoin demand has been institutional, tariff f...`

**[7]** pred=`9d1e98b7-858a-41a3-a607-8d86087370dd` pub=2025-10-12 entry=2025-10-13 px=$138.06
- LLM: dir=short conv=2 hz=6m qc=None hedged=0
- 1m: 138.06 raw=N/A excess=+28.80%
- 原文: `And there’s the de-escalation

Reuters: “Taiwan sees no significant impact on chip sector”

Trump: “Don’t worry about China, it will all be fine… President Xi just had a bad moment.”

Biggest crypto liquidation to date 

Stocks with little impact down 7%

Dip buying opportunity https://t.co/2sUEV7Dg8s`

**[8]** pred=`9bab0128-6bcf-4c7c-9656-814d0728137c` pub=2025-10-25 entry=2025-10-27 px=$146.93
- LLM: dir=short conv=3 hz=event_driven qc=None hedged=0
- 1m: 146.93 raw=N/A excess=+52.28%
- 原文: `Huge warning on $CRCL, especially going into December 2nd. You're trading on a low float.

Circle sold 34M Class A shares in the IPO at $31. There's 202,550,578 Class A shares outstanding.

77.6% of all outstanding Class A (157M/202.55M) and ~463% of the 34M IPO float will be unlocked in December. 

If anything I'd go short + long COIN as hedge during before the event.`


### CRWV (n_long=30  n_short=12)


**[1]** pred=`b31b3d84-cf02-440f-bb15-9effad10f5eb` pub=2025-10-06 entry=2025-10-07 px=$136.16
- LLM: dir=short conv=3 hz=event_driven qc=None hedged=0
- 1m: 136.155 raw=N/A excess=+15.96%
- 原文: `@yield_addicted For the deal, I'd say net negative: $NVDA, $CRWV (Nvda centric)

Net positive (almost everything else): $AMD, NBIS, CIFR, IREN, TSM, etc. 

The 2.5% drop makes sense off moat narrative changes.`

**[2]** pred=`99c06126-b070-4841-b998-e608eea6f07f` pub=2025-11-14 entry=2025-11-17 px=$75.51
- LLM: dir=short conv=3 hz=long_term qc=None hedged=0
- 1m: 75.51 raw=N/A excess=+10.37%
- 原文: `Neocloud isn't winner takes all, it's a whole ecosystem but not everything can become AWS.

We're seeing $NBIS, $IREN, $CRWV, and $ORCL compete in the true "Neocloud", most profitable full stack race to become Azure/AWS. Doing vertical integration, building capacity, buying GPUs, and doing orchestration, and some incubants entering the race. 

So far $NBIS is the clear winner with hyperscalers + enterprises + good balance sheet in a matter of time, $CRWV is swamped with interest debt, $ORCL fail...`

**[3]** pred=`b48f8cf6-7cab-4f9c-a5ee-33a9c6274dc7` pub=2025-11-19 entry=2025-11-20 px=$82.62
- LLM: dir=short conv=2 hz=6m qc=None hedged=0
- 1m: 82.62 raw=N/A excess=+2.86%
- 原文: `The Great Reset, November 19th ratings:

Strong Buy

· $NBIS
· $CIFR
· $WULF
· $RDDT
· $SNAP
· $ALAB
· $META
· $AMZN
· $GOOGL
· $IBIT
· $SOL
· $TSM
· $RKLB
· $TSSI
· $SMCI
· $GLXY
· $SG

Buy

· $IREN
· $KRUS
· $CRCL
· $LTC
· $MRVL
· $KRKNF
· $OSS
· $CORZ
· $WLAC
· $WYFI
· $AMD
· $TE
· $CRDO
· $FLNC
· $HIMS
· $BULL
· $ETOR
· $FISV
· $FLY
· $MU

Hold

· $COIN
· $HOOD
· $IBKR
· $NVDA
· $PLTR
· $TSLA
· CRWV
· $APLD
· ORCL

Avoid

· RGTI
· $IONQ
· SLNH
· $QBTS
· OKLO
· $WMT
· BMNR
· $SBET
· CRWV
_

E...`

**[4]** pred=`256e9ccc-5637-4dfb-bc41-bfd573bb950e` pub=2025-11-22 entry=2025-11-24 px=$72.95
- LLM: dir=short conv=3 hz=long_term qc=None hedged=0
- 1m: 72.95 raw=N/A excess=-4.76%
- 原文: `If you spent just 30 seconds reading the post, you would see I didn't rate $BITF. 

With $CRWV there's short term upside because sell-off was way too much to the $60s. But medium-long term they have way too much debt interest. 

While $NBIS and $IREN funds through convertibles or little interest cutting into margins every quarter, Coreweave pays over $1.2B+ in annual debt expense interest. 

OpenAI also makes up 1/3th of their total backlog, so while they have some defensible hyperscalers ( $MET...`

**[5]** pred=`fd3b85d4-8140-4d78-9451-09b7915186e1` pub=2025-11-25 entry=2025-11-26 px=$74.76
- LLM: dir=short conv=3 hz=long_term qc=None hedged=0
- 1m: 74.76 raw=N/A excess=+1.15%
- 原文: `The main fear I have in the "AI Bubble" is OpenAI and their $1T capex promises. That is a clear bubble (and private valuations of LLMs). Most other things, no. 

Any company directly reliant to them $ORCL, $CRWV might be in trouble given how AI models leapfrogged GPT. So the simple thing to do is stay away!

Personally speaking, ChatGPT5.1 is horrendous and I actually cancelled my subscription to go with Gemini/Claude. Claude Opus 4.5 outperforms Codex in coding tasks. Gemini outperforms ChatGPT...`

**[6]** pred=`c4cc36b2-5860-43a5-ae15-a976a5282923` pub=2025-11-30 entry=2025-12-01 px=$71.25
- LLM: dir=short conv=4 hz=long_term qc=None hedged=0
- 1m: 71.25 raw=N/A excess=-0.51%
- 原文: `Economics of Neocloud GPU Pricing

What happens when you normalize margins across the three major GPU neoclouds, accounting for depreciation and cost structure?

· Nebius ( $NBIS )

· CoreWeave ( $CRWV )

· IREN ( $IREN )

Below is what the research shows for margins using the same H100s:

35.8% $IREN - Bare-Metal H100

· Revenue: ~$2.50–2.75/GPU-hr -> $7.80M/MW-year
· COGS: $5.01M/MW  · GPU D&A: $3.50M  · Power: $0.22M  · DC depreciation: $0.47M    · Networking: $0.25M  · Third-party middleware...`

**[7]** pred=`02e6a333-6829-4297-b77e-465b991efd58` pub=2025-12-11 entry=2025-12-12 px=$86.19
- LLM: dir=short conv=4 hz=event_driven qc=None hedged=0
- 1m: 86.19 raw=N/A excess=-4.19%
- 原文: `Oracle [ $ORCL ] earning results and its effect on the neocloud sector like $NBIS & $IREN:

Oracle reported earnings with a beat on EPS and a record backlog but, dropped 12% after hours.

Oracle is down 39.8% from September 11th highs and brought down the sector with it.

Here's why:

The sell-off was not merely a reaction to marginal revenue miss, but both an algorithmic short and investor selloff on the sustainability of the AI capex cycle and the creditworthiness of the sector's primary tenan...`

**[8]** pred=`6508c55f-c3af-4737-bebc-b02bc73fa256` pub=2025-12-12 entry=2025-12-15 px=$79.33
- LLM: dir=short conv=3 hz=long_term qc=None hedged=0
- 1m: 79.33 raw=N/A excess=-19.77%
- 原文: `Broadcom [ $AVGO ] earnings results and its effect on the AI sector like $LITE and $NBIS:

Broadcom's ER was "double beat" with $18.02B revenue (+28% Y/Y) and $1.95 EPS, beating consensus.

But AVGO dropped -11.64% and brought down the AI sector. 

Is this a buying opportunity?

Yes.

Broadcom is seen as a hyperscaler ASIC proxy growth as companies like $AMZN Trainium, $MSFT Maia, and most importantly $GOOGL TPU V7 Ironwood are scaled through it.

And by proxy companies like $ALAB (-13.2%), $CRD...`

**[9]** pred=`8ae273f0-77fd-4bb5-8f01-efd5ebdc63e8` pub=2026-01-28 entry=2026-01-29 px=$103.86
- LLM: dir=short conv=4 hz=long_term qc=None hedged=0
- 1m: 103.86 raw=N/A excess=+24.85%
- 原文: `Thinking about buying $CRWV on the $NVDA deal?

Here's the way to think about it:

A casino gives you more money, so you could take on more debt with collateral to gamble.

Then all the extra money goes back to the Casino (aka. $NVDA). 

That doesn't make Coreweave a good long.

But it does make Nvidia one. 

Bet on the house, not the one with $14.7B+ in debt with $1.2B+ in yearly interest payments.`

**[10]** pred=`0c48d922-1622-4500-bed6-c8940a4302bc` pub=2026-01-28 entry=2026-01-29 px=$103.86
- LLM: dir=short conv=2 hz=long_term qc=None hedged=0
- 1m: 103.86 raw=N/A excess=+24.85%
- 原文: `저는 $NBIS 가 현재 매우 매력적이라고 생각합니다. $CIFR(네오클라우드가 아닌 코로케이션 부문) 같은 특정 종목들도 마찬가지입니다. 반면 $CRWV 는 그만큼 설득력이 있지는 않네요.

네비우스(Nebius)의 비즈니스 모델은 기본적으로 전년 대비(Y/Y) 100%씩 성장하는 5개의 회사가 하나로 합쳐진 형태입니다. ($UBER와 협력하는 자율주행 Avride, 약 150억 달러의 가치로 평가받는 Clickhouse, Toloka(AI 라벨링), 그리고 에듀테크). 여기에 약 70억 달러의 ARR(연간 반복 매출)을 기록한 주력 사업 부문이 포함됩니다.

따라서 이러한 낙관적인 매출 수치들은 실제 창출되는 FCF(잉여현금흐름)를 통해 면밀히 살펴봐야 하겠지만, 사측에서는 장기적으로 20%~30%의 EBIT 마진을 제시하고 있습니다.

가장 중요한 차이점은 코어위브(Coreweave)의 경우 12억 달러 이상의 부채 이자가 FCF를 잠식하고 있는 반면, 다른 기업들은 2~3% ...`

**[11]** pred=`a95297b0-ba35-4dbd-9675-4594ec8f91a6` pub=2026-01-28 entry=2026-01-29 px=$103.86
- LLM: dir=short conv=4 hz=long_term qc=None hedged=0
- 1m: 103.86 raw=N/A excess=+24.85%
- 原文: `$CRWV is probably the only $50B+ company I can think of that is likely going to go bankrupt. At least $ORCL has a profitable core business and owns tons of assets like  15% of Tiktok.  

Coreweave is a clear short to me purely because a large part of their revenue will be used to pay off debt interest. Then you compound that with GPU depreciation. 

But it's a good idea to hedge. I would personally long $NBIS, $CIFR short $CRWV, seems decent for long term. Nvidia is keeping them alive for now.`

**[12]** pred=`69021353-dc98-4c38-8079-7c76324527da` pub=2026-03-28 entry=2026-03-30 px=$75.31
- LLM: dir=short conv=4 hz=long_term qc=None hedged=0
- 1m: 75.31 raw=N/A excess=-51.63%
- 原文: `My thoughts on $NBIS, $IREN, $CRWV and the current Neocloud market. 

One of them ends up as the next AWS in 5 years:

My guess it’s Nebius. 

It's not winner takes all (DigitalOcean is there with Amazon), but there's clearly superior structures and likely winners.

The downside:

-> Low chance of rate cuts from Iran conflict. 

->Broader market doesn't appear to want to fund the CapEx cycle. But want to reap the benefits

With $IREN:

We get it, 4.5GW = X revenue. But who is funding the GPUs? 
...`


### DUOL (n_long=4  n_short=2)


**[1]** pred=`1ede796c-e922-4dd9-809a-11556fc9d6c7` pub=2025-08-23 entry=2025-08-25 px=$331.83
- LLM: dir=short conv=2 hz=6m qc=None hedged=0
- 1m: 331.83 raw=N/A excess=+9.24%
- 原文: `Some decent recovery/swing trades right now

1. $SG - $9.39
2. $SNAP - $7.21
3. $UNH - $306.8
4. $ETOR - $46.8
5. $NVO - $57.00
6. $HIMS - $44.73
7. $CRWV - $94.7

Stay away from these dips

1. $CRCL - $136.2
2. $PLTR - $159.6
3. $DUOL - $334.5`

**[2]** pred=`cbe3b639-3855-4db0-82c8-fcc33060c0bb` pub=2026-02-17 entry=2026-02-18 px=$112.01
- LLM: dir=short conv=3 hz=3m qc=None hedged=0
- 1m: 112.01 raw=N/A excess=+11.07%
- 原文: `This data is alarming... Robinhood users lost a collective:

- $24.6 Billion USD in Q4 2025. 

With Robinhood portfolios on X consisting of :

$HIMS, $DUOL, and $BMNR.

Q1 2026 is likely to be even worse, as these names drop 50-70%+. 

Everyone thinks they're Warren Buffet, making profit from Duolingo, $CRWV, and $ASST in an extreme bull market. 

But as markets turn sour: 

We'll start to see the real traders and investors, who are able to profit in any market condition.`


### EZU (n_long=0  n_short=1)


**[1]** pred=`587ffbdb-071f-4257-8a85-2aab9809de65` pub=2026-02-01 entry=2026-02-02 px=$66.96
- LLM: dir=short conv=3 hz=event_driven qc=None hedged=0
- 1m: 66.96 raw=N/A excess=+2.43%
- 原文: `Kevin Warsh is the next Federal Reserve Chair.

Markets may confuse him as a "Hawk". 

His actual stance in 2026 is nuanced.

Here's his policies and how they affect the markets: 

1. AI/Semis ( $NVDA, $MU): Extremely Bullish
2. Metals (Silver, Gold): Extreme Bearish
3. Crypto ( $BTC, $CRCL ): Paradoxically bullish
4. Banking & Financials ( $JPM, $BOA ): Bullish
5. Housing & Real Estate: Mixed/Uncertain
6. Renewable Energy: Bearish
7. Small-Caps ( $RUT ) : Bullish
8. Foreign Stocks (Japan, Korea...`


### HIMS (n_long=64  n_short=1)


**[1]** pred=`3ca5598b-75e1-41de-b691-7e3c16943d10` pub=2026-02-17 entry=2026-02-18 px=$16.11
- LLM: dir=short conv=3 hz=3m qc=None hedged=0
- 1m: 16.11 raw=N/A excess=-49.97%
- 原文: `This data is alarming... Robinhood users lost a collective:

- $24.6 Billion USD in Q4 2025. 

With Robinhood portfolios on X consisting of :

$HIMS, $DUOL, and $BMNR.

Q1 2026 is likely to be even worse, as these names drop 50-70%+. 

Everyone thinks they're Warren Buffet, making profit from Duolingo, $CRWV, and $ASST in an extreme bull market. 

But as markets turn sour: 

We'll start to see the real traders and investors, who are able to profit in any market condition.`


### HIMX (n_long=0  n_short=1)


**[1]** pred=`ff53cd57-b097-4a9c-8b55-550c11fece4b` pub=2026-05-25 entry=2026-05-26 px=$21.71
- LLM: dir=short conv=3 hz=long_term qc=None hedged=0
- 1m: 21.71 raw=N/A excess=N/A
- 原文: `几个值得重点关注的“实质性垄断”标的:

- MSSCORP (6830)：在检测和 CPO 良率把控上构筑了极深的专利护城河。 
- $SOI：主导绝缘体上硅 (SOI) 衬底市场。  
- NGK (5333)：稳拿薄膜铌酸锂 (TFLN) 晶圆核心技术。 
- $AXTI：把控磷化铟 (InP) 衬底等上游关键材料。

像讯芯 (Shunsin) 这类公司其实很难被轻易颠覆，毕竟背靠富士康，而富士康本身就深深扎根于众多核心供应链的腹地 🏭

$SIVE 的逻辑也极其相似。他们已经成功打入 (design in) 了众多顶尖 CPO 架构的设计体系，抱紧了 Ayar、Lightelligence (壁仞的供应商)、Lightmatter 以及 Celestial 等 众行业领军者的大腿 

相比之下，个人认为 $HIMX (奇景光电) 或 Foci (上诠) 未来面临被踢出局 (design out) 的风险最大，很有可能会被台积电的光学部门采钰 (Visera 6789) 这类巨头直接垂直整合。不过话说回来，在未来两三年内，借助 CPO 相关的光纤阵列 (FAU) 和无源器件，他...`


### HOOD (n_long=22  n_short=1)


**[1]** pred=`fc09a94f-e304-44a3-84b1-148fcb5b565a` pub=2025-09-29 entry=2025-09-30 px=$135.67
- LLM: dir=short conv=2 hz=6m qc=None hedged=0
- 1m: 135.67 raw=N/A excess=-6.73%
- 原文: `Monday Market Close Thoughts:

Extremely Strong Buy
$NBIS
$ETOR
$LTC
$VIRT

Buy
$AMZN
$SMCI
$TGT
$CRM
$TSM
$CRDO
$SG
$CIFR
$LULU
$SLNH
$ORCL
$MSTR
$RIOT
$MARA

Hold
$IREN
$HIMS
$RKLB
$PYPL
$MRVL
$IBIT
$UPWK
$GRAB
$ALAB
$ASTS
$SOFI
$NVDA
$NVO

Sell
$HOOD
$TSLA
$RDDT
$CRCL
$PLTR
$BMNR

Strong Sell
$OKLO
$QBTS
$IONQ

_

Feel free to disagree but these are just my thoughts

Strong Buy Explanations

- Bought ~$70K of Virtu calls, 28% IV and just 6.6 forward p/e is undervalued.

- Always DCA NBIS on t...`


### INTU (n_long=0  n_short=1)


**[1]** pred=`7797dc21-f973-4cdf-aeed-2e7d56ed5bbd` pub=2026-04-12 entry=2026-04-13 px=$354.50
- LLM: dir=short conv=3 hz=long_term qc=None hedged=0
- 1m: 354.5 raw=N/A excess=-9.38%
- 原文: `It's nuanced, I do think companies like $INTU are going to get slightly disrupted by Claude and others doing taxes + filing for you. And it's not a great contrarian buy-the-dip opportunity. 

On the flip side certain software names like $RDDT / $SNAP are likely going to end up more profitable with AI due to opex cuts (only if Evan's wife stopped using Snapchat like a piggy back). 

Disruption is real, but there's a few winners.`


### IONQ (n_long=1  n_short=6)


**[1]** pred=`d45855b7-c518-4014-895e-53fd37e9db47` pub=2025-09-29 entry=2025-09-30 px=$63.59
- LLM: dir=short conv=5 hz=6m qc=None hedged=0
- 1m: 63.59 raw=N/A excess=+3.90%
- 原文: `Monday Market Close Thoughts:

Extremely Strong Buy
$NBIS
$ETOR
$LTC
$VIRT

Buy
$AMZN
$SMCI
$TGT
$CRM
$TSM
$CRDO
$SG
$CIFR
$LULU
$SLNH
$ORCL
$MSTR
$RIOT
$MARA

Hold
$IREN
$HIMS
$RKLB
$PYPL
$MRVL
$IBIT
$UPWK
$GRAB
$ALAB
$ASTS
$SOFI
$NVDA
$NVO

Sell
$HOOD
$TSLA
$RDDT
$CRCL
$PLTR
$BMNR

Strong Sell
$OKLO
$QBTS
$IONQ

_

Feel free to disagree but these are just my thoughts

Strong Buy Explanations

- Bought ~$70K of Virtu calls, 28% IV and just 6.6 forward p/e is undervalued.

- Always DCA NBIS on t...`

**[2]** pred=`a288693d-740b-40ce-9bd3-8f2150fd7e4a` pub=2025-10-04 entry=2025-10-06 px=$72.00
- LLM: dir=short conv=2 hz=6m qc=None hedged=0
- 1m: 72.0 raw=N/A excess=+25.86%
- 原文: `Friday Market Close, Personal Thoughts and Explanations:

Strong Buy
$RDDT
$SNAP
$AMZN
$ETOR
$NBIS
$LTC

Buy
$UPWK
$MSTR
$ORCL
$TGT
$CIFR
$VIRT
$CRDO
$WULF
$SOFI
$META
$AVGO
$MRVL
$SMCI
$DELL

Hold
$RKLB
$TSM
$IREN
$RR
$ALAB
$HOOD
$FLNC
$EOSE
$BE
$RIOT
$MARA
$GRAB
$ASTS
$NVO
$NVDA

Sell
$TSLA
$CRCL
$PLTR
$BMNR

Strong Sell
$RGTI
$OKLO
$QBTS
$IONQ

_

(again, not great DD, just writing random thoughts about the process). 

Strong Buys

Reddit - Dropped 29% off immaterial news that ChatGPT wasn't ...`

**[3]** pred=`8da52c2c-3964-41ed-9bdd-e99a3fdec892` pub=2025-10-11 entry=2025-10-13 px=$74.11
- LLM: dir=short conv=2 hz=6m qc=None hedged=0
- 1m: 74.11 raw=N/A excess=+26.57%
- 原文: `Based Friday Market Close (-3.6% SPY day), Thoughts and Explanations

Strong Buy
$IBIT
$LTC
$WLAC
$NBIS
$MP
$TSM
(For Next Year)
$ETOR
$DKNG
$SNAP

Buy
$UPWK
$CRDO
$ALAB
$AMZN
$META
$UNH
$SG
$TGT
$BULL
$FLY
$CIFR
$WULF
$IREN
$GLXY
$SMCI
$DELL
$MRVL

Hold
$RKLB
$HOOD
$RBRK
$MU
$HOOD
$GRAB
$MARA
$RIOT
$NVO
$RR
$ELOSE
$FLNC
$SEI
$PLTR

Sell
$CRCL
$ETH
$BMNR
$PL
$BKSY

Strong Sell
$RGTI
$OKLO
$IONQ
$QBTS
$QUBT

_

Explanations:

IBIT - Dumped to $104k, Bitcoin demand has been institutional, tariff f...`

**[4]** pred=`39ce8d2d-b089-4db9-9e15-66ef70bb1853` pub=2025-10-12 entry=2025-10-13 px=$74.11
- LLM: dir=short conv=2 hz=6m qc=None hedged=0
- 1m: 74.11 raw=N/A excess=+26.57%
- 原文: `And there’s the de-escalation

Reuters: “Taiwan sees no significant impact on chip sector”

Trump: “Don’t worry about China, it will all be fine… President Xi just had a bad moment.”

Biggest crypto liquidation to date 

Stocks with little impact down 7%

Dip buying opportunity https://t.co/2sUEV7Dg8s`

**[5]** pred=`9507fe75-eb46-41fd-bda7-2f7d57789b66` pub=2025-10-19 entry=2025-10-20 px=$65.31
- LLM: dir=short conv=2 hz=6m qc=None hedged=0
- 1m: 65.31 raw=N/A excess=+24.79%
- 原文: `October 20th, Important Rate Cut Trading Week.

Personal thoughts and explanations: 

🛝 = Swing Trade

🐈 = Catalyst Trade

🎇 = 2026 Trade, Tax Harvested

Fire Sale
🔥 $NBIS 

Strong Buy
$TSM
$AMKR
$WLAC
$AMZN
$LTC 🐈
$RDDT
$HIMS 🛝
$IBIT
$ALAB
$CRDO
$SMCI
$FLY 🎇
$SNAP 🎇
$ETOR 🎇
$LULU 🎇

Buy
$AMD
$HOOD 
$RBRK
$UNH
$TGT 🐈
$IREN 🐈
$WYFI
$WULF
$CIFR
$SLNH
$BITF
$GLXY
$FLNC
$MU

(Skipping Hold, since any other stock I've mentioned in the past, it probably just hold it since nothing's changed).

Sell
$ET...`

**[6]** pred=`03cbe004-561a-499b-9b39-133db2e56458` pub=2025-11-19 entry=2025-11-20 px=$48.57
- LLM: dir=short conv=2 hz=6m qc=None hedged=0
- 1m: 48.57 raw=N/A excess=-5.81%
- 原文: `The Great Reset, November 19th ratings:

Strong Buy

· $NBIS
· $CIFR
· $WULF
· $RDDT
· $SNAP
· $ALAB
· $META
· $AMZN
· $GOOGL
· $IBIT
· $SOL
· $TSM
· $RKLB
· $TSSI
· $SMCI
· $GLXY
· $SG

Buy

· $IREN
· $KRUS
· $CRCL
· $LTC
· $MRVL
· $KRKNF
· $OSS
· $CORZ
· $WLAC
· $WYFI
· $AMD
· $TE
· $CRDO
· $FLNC
· $HIMS
· $BULL
· $ETOR
· $FISV
· $FLY
· $MU

Hold

· $COIN
· $HOOD
· $IBKR
· $NVDA
· $PLTR
· $TSLA
· CRWV
· $APLD
· ORCL

Avoid

· RGTI
· $IONQ
· SLNH
· $QBTS
· OKLO
· $WMT
· BMNR
· $SBET
· CRWV
_

E...`


### IREN (n_long=74  n_short=24)


**[1]** pred=`e9c6802c-a091-4aab-95d1-1550842f62f1` pub=2025-10-26 entry=2025-10-27 px=$64.99
- LLM: dir=short conv=3 hz=long_term qc=None hedged=0
- 1m: 64.99 raw=N/A excess=+26.96%
- 原文: `@soulbiri1 $NBIS is like DD Tsunade walking around becoming hokage like a legend. $IREN is some main character like Sakura with power that people admire at first but will come to realize is  useless as time goes on when you compare it to someone with the full package.`

**[2]** pred=`9a915673-e431-48ee-b842-8a291936508e` pub=2025-10-27 entry=2025-10-28 px=$63.68
- LLM: dir=short conv=4 hz=long_term qc=None hedged=0
- 1m: 63.68 raw=N/A excess=+23.92%
- 原文: `Great points! But...

You did base your thesis off misunderstanding gaap vs. non-gaap... which could be confusing to non-accountants and other people on X. 

$IREN reported non-GAAP and $NBIS GAAP when you look at hardware-segment profit to full-stack AWS margins.

The 92% percent was non-GAAP, hardware-specific profit metric that systematically excludes depreciation, data-center overhead, network expenses, support, etc. Hardware Profit Margin is typically calculated solely by deducting direct e...`

**[3]** pred=`bf99d759-13bb-4658-afcd-fa2354e74ffb` pub=2025-11-03 entry=2025-11-04 px=$64.22
- LLM: dir=short conv=3 hz=long_term qc=None hedged=0
- 1m: 64.215 raw=N/A excess=+30.37%
- 原文: `For $CIFR, doesn't matter about current earnings, market prices in forward earnings. And at first glance AWS deal looks amazing on top of their existing $GOOGL deals through Fluidstack. So well deserving of their 20% bump.

For $IREN on the other hand, the contract worse and worse when you examine it more. 

Revenue does not matter. FCF/margins from that revenue is what matters, especially since they're spending $5.8bn GPUs. I've seen some conservative-case calculations where they generate ~Annu...`

**[4]** pred=`dd1f076f-4d6e-4947-8a44-1c97baf7ad02` pub=2025-11-14 entry=2025-11-17 px=$46.11
- LLM: dir=short conv=3 hz=long_term qc=None hedged=0
- 1m: 46.11 raw=N/A excess=+22.36%
- 原文: `Institutional Flow assessment for 13F Neocloud filings:

· Nebius ( $NBIS ): 🟢 Strongly Positive (7/10)
· WULF ( $WULF ): 🟢 Highly Positive (8.5/10)
· IREN ( $IREN ): 🔴 Very Negative (3/10)
· CIFR ( $CIFR ): 🟢 Highly Positive (8.0/10)
· Coreweave ( $CRWV ):  🟡 Neutral (5.5/10)
· Cleanspark ( $CLSK ): 🟢 Highly Positive (9.0/10)

_

TLDR Summary Updates: 

$NBIS
· Strong overall quantitative growth in institutional ownership, driven by a mix of solid, long-term institutional buyers alongside high ...`

**[5]** pred=`1bd3cadd-0620-4bb6-9834-4597ea0a17c8` pub=2025-11-19 entry=2025-11-20 px=$48.97
- LLM: dir=short conv=4 hz=event_driven qc=None hedged=0
- 1m: 48.97 raw=N/A excess=+14.09%
- 原文: `Sure happy to explain further than the TLDR on why I've downgraded $IREN and upgraded $TSSI a strong buy.  $TSSI has high upside on the drop from $30 to $7 since it was an overreaction to temporary Q3 operational scaling bottlenecks and factory cost not underlying demand. 

It's well capitalized to piggybak off of Dell rampup, which doubled its AI serve guidance to $20B. Likewise $SMCI faced similar issues with short term misses, but massive ramp ups in revenue guidance around Q2 2026 like Dell....`

**[6]** pred=`f7ef86d9-6fec-44e9-b5c3-34656003fb1e` pub=2025-11-20 entry=2025-11-21 px=$42.86
- LLM: dir=short conv=4 hz=long_term qc=None hedged=0
- 1m: 42.86 raw=N/A excess=+2.05%
- 原文: `I'm very precise with my wording. You skipped over "expected" while reading discussions about guided contracted capacity.

So reiterating what I've said above but with a longer explanation: 

$IREN's original moat was GW capacity + vertical integration. $NBIS's moat was full-stack. 

However, Nebius achieved long-term parity with GW capacity that was originally thought to be $IREN's biggest moat. 

Here's a helpful explanation:
- Near term $IREN .66 GW connected vs. 22 GW connected with $NBIS. T...`

**[7]** pred=`b4cf7126-b69c-43a4-b80e-274dc0e10828` pub=2026-03-06 entry=2026-03-09 px=$36.46
- LLM: dir=short conv=4 hz=long_term qc=None hedged=0
- 1m: 36.46 raw=N/A excess=-1.01%
- 原文: `I see zero compelling case to hold $IREN.

Especially given the new $6B share dilution at a $12.8B marketcap.

People will likely see that marketcap inflate to $20-$25B.

But the value of their shares decrease over time. 

The risk reward is just not there anymore.

Companies like $CIFR offer much more asymmetrical upside given their colo model for $AMZN and $GOOGL through Fluidstack.

And companies like $NBIS offer much better diversification (robotaxis, clickhouse), derisked execution, and are...`

**[8]** pred=`faf18c84-10e6-4ff6-8736-b132df16487d` pub=2026-03-08 entry=2026-03-09 px=$36.46
- LLM: dir=short conv=4 hz=event_driven qc=None hedged=0
- 1m: 36.46 raw=N/A excess=-1.01%
- 原文: `$IREN $6 Billion ATM is massive. 

For the people who hold $IREN, the truth you might not want to hear is: 

-> Wait until existing holders get diluted to oblivion
-> Use them to "buy the dip" of $6 Billion in new shares for you. 
-> Go long after. 

If you're long now:

That inevitable $6B in new shares + selling pressure structurally caps upside in your equity and serves as a overhang in any rally.

Companies don’t file a $6B ATM not to use it.

They will, and as much as they can on any rally....`

**[9]** pred=`1bf402f0-f197-40ad-87ca-09358842a0ee` pub=2026-03-11 entry=2026-03-12 px=$40.76
- LLM: dir=short conv=4 hz=long_term qc=None hedged=0
- 1m: 40.76 raw=N/A excess=-5.67%
- 原文: `$NBIS vs. $IREN.

The difference is night and day.

Nebius: $2B dilution from $NVDA, zero immediate selling pressure to the public float

Iren: $6B dilution from ATM into selling pressure into the open market. This extracts liquidity directly from the public and suppresses momentum

Very clear, which company leads to higher share value appreciation from capex financing.

One is strategic with Nvidia, the other is toxic financing.`

**[10]** pred=`11199127-a0c4-4cd5-ab3b-f6d2fd71ac6b` pub=2026-03-11 entry=2026-03-12 px=$40.76
- LLM: dir=short conv=3 hz=6m qc=None hedged=0
- 1m: 40.76 raw=N/A excess=-5.67%
- 原文: `It’s not that $IREN will crash. 

It’s moreso short-medium term IREN’s upside is capped due to the $6B ATM.

If you’re investing in IREN it’s better to wait after existing holders get diluted to oblivion from up to $6B in selling pressure, then go long after. 

If you’re chasing equity appreciation, $NBIS has a much superior capex financing structure.`

**[11]** pred=`218c8984-a601-4fd7-b30e-5b538c0c5def` pub=2026-03-14 entry=2026-03-16 px=$44.03
- LLM: dir=short conv=3 hz=6m qc=None hedged=0
- 1m: 44.03 raw=N/A excess=-10.88%
- 原文: `@BTCSuperCycle Short $IREN, long $NBIS`

**[12]** pred=`24d787dc-572c-4290-8699-d7c380a15c68` pub=2026-03-24 entry=2026-03-25 px=$42.39
- LLM: dir=short conv=2 hz=event_driven qc=None hedged=0
- 1m: 42.39 raw=N/A excess=-19.46%
- 原文: `Much better opportunities out than $IREN. 

If you want the same sector, $NBIS is objectively better when you look at how they finance capex ( $NVDA $2B funding )…

Then there’s others like $AAOI that leapfrogs $IREN revenue + profit, with less capex.

But if you still want to hold $IREN, probably better to re-enter after everyone gets diluted to fund their buildout and reap the rewards after.`

**[13]** pred=`1ce00ef5-1187-423d-b6aa-fcc0146efb05` pub=2026-03-28 entry=2026-03-30 px=$35.89
- LLM: dir=short conv=3 hz=event_driven qc=None hedged=0
- 1m: 35.89 raw=N/A excess=-19.42%
- 原文: `With $IREN, you have $6B in newly minted selling pressure. This ATM is structural overhang in any rally.
 
If the marketcap is $11 Billion and they're selling up to $6,000,000,000 worth of new shares against you in the open market. 

I would not go long until the ATM is finished and existing holders get diluted. 

Same with $VCX, if you're trading at 2000% NAV of SpaceX (valued at $34 Trillion), eventually the math will work against you.`

**[14]** pred=`13098143-e148-4384-8f93-b77bff66dc46` pub=2026-03-29 entry=2026-03-30 px=$35.89
- LLM: dir=short conv=4 hz=event_driven qc=None hedged=0
- 1m: 35.89 raw=N/A excess=-19.42%
- 原文: `$IREN filed to dilute $6,000,000,000 at a $11.7B MC.

That is not noise.

This is Iren's way to monetize their 4.5GW capacity by selling all those new shares onto the open market. 

If you want some history on how this turns out:

Look at $BKKT that crashed 99% with Mike and $IREN board of directors history with excessive ATMs. Or his recent company $ASST.

It’s accretive to the company and executives: Because it wipes out all retail shareholders and they can always issue SBC. 

So they don’t ac...`

**[15]** pred=`ad983690-69e9-479a-86dc-c8ea8f115f58` pub=2026-03-29 entry=2026-03-30 px=$35.89
- LLM: dir=short conv=3 hz=event_driven qc=None hedged=0
- 1m: 35.89 raw=N/A excess=-19.42%
- 原文: `Yes, basically it. I’ve been bullish on $IREN last year. 

But with the $6B ATM I’m extreme bearish due to structural overhang. But if they manage to raise all that after diluting existing shareholders.

I’d consider flipping long again. This is just market mechanics of dilution…`

**[16]** pred=`0324ba16-5fdc-4ffc-a053-4f18c4b6d499` pub=2026-03-30 entry=2026-03-31 px=$32.97
- LLM: dir=short conv=4 hz=long_term qc=None hedged=0
- 1m: 32.97 raw=N/A excess=-38.03%
- 原文: `Do you guys think there’s only $5,650,000,000 dilution to go with $IREN?

Very surprising that people haven’t switched to $NBIS or other names if you’re long Neoclouds.

One already has confirmed funding with $NVDA + convertibles from institutions.

The other is likely actively selling new shares on the open market to get funding off retail shareholders.

The sad reality is:

$IREN simply cannot monetize the rest of their capacity without using that. It’s not “optionality”.

Financial structure ...`

**[17]** pred=`4e9195b3-7c25-4733-80ed-a57cca3bc8f1` pub=2026-04-02 entry=2026-04-06 px=$34.72
- LLM: dir=short conv=4 hz=event_driven qc=None hedged=0
- 1m: 34.72 raw=N/A excess=-57.66%
- 原文: `It still baffles me how people are still “Buying the Dip” on $IREN.

Amid their $6,000,0000,000 ATM, diluted and sold into the open market. 

Thinking that it will increase their share price.

While $NBIS was able to differentiate themselves and secure more hyperscaler deals + $NVDA backing.

$IREN GW raw asset moat they had two years ago is now almost gone.

It’s hard to see the stock appreciating much in value when $6,000,000,000 of structural dilution works against you in every rally.

Better...`

**[18]** pred=`195e8440-78b8-4d9c-86aa-d74e4ae2dada` pub=2026-04-11 entry=2026-04-13 px=$38.46
- LLM: dir=short conv=4 hz=event_driven qc=None hedged=0
- 1m: 38.46 raw=N/A excess=-47.06%
- 原文: `There's a reason $IREN is down -7.9% YTD.

While $NBIS is up 61.1% YTD.

The amount of delusion buying into a $6,000,000,000 ATM is unreal. 

Even after this, IREN AMC bagholders still can't admit they're wrong? 

Markets are the biggest arbiter of truth, and massive performance difference between Nebius and Iren is telling. 

As I said before, the marketcap for $IREN will keep going up, but people's share values will decrease. 

That's how ATMs work. Excessive ATMs are not accretive to current ...`

**[19]** pred=`d2043678-a1c8-4002-8f96-60562d32bc49` pub=2026-04-13 entry=2026-04-14 px=$45.24
- LLM: dir=short conv=3 hz=long_term qc=None hedged=0
- 1m: 45.245 raw=N/A excess=-21.94%
- 原文: `@mwallacegreen3 Glad to hear it… yeah it’s like a weight lifted off your shoulders that you’re not buying into a $6B ATM printed and sold into rallies with $IREN.

With other stocks like $NBIS you can actually benefit from long term share price appreciation.`

**[20]** pred=`1f41fa44-cb23-4c68-8cd6-796fb67aafa3` pub=2026-04-23 entry=2026-04-24 px=$53.24
- LLM: dir=short conv=3 hz=event_driven qc=None hedged=0
- 1m: 53.24 raw=N/A excess=-12.28%
- 原文: `@BitcoinAIGuy I’m still bearish on $IREN due to $6B ATM overhang, even if there’s rumors they’re doing colo. I was long last year you know.`

**[21]** pred=`40862ec7-982d-4c02-9847-f3c98037726c` pub=2026-04-30 entry=2026-05-01 px=$46.17
- LLM: dir=short conv=4 hz=long_term qc=None hedged=0
- 1m: 46.17 raw=N/A excess=-44.25%
- 原文: `$IREN is a horrendous long. I can’t imagine anyone that cares about portfolio appreciation to buy into a $6B ATM while executives award themselves record high SBC.

People are just buying in to get diluted because of a promise of secured power (which is no longer a moat, it was last year)`

**[22]** pred=`998837a8-6aa5-4b26-92bf-a1959fa87021` pub=2026-05-07 entry=2026-05-08 px=$63.84
- LLM: dir=short conv=4 hz=long_term qc=None hedged=0
- 1m: 63.845 raw=N/A excess=+15.39%
- 原文: `I still am bearish on $IREN.

Algorithms/retail probably read $NVDA + $IREN partnership and bought it up. 

However, if you look at the realtity, it's just looks like brand agreement giving $NVDA risk-free convertible notes. 

So $IREN can continue selling their $6,000,000,000 ATM into retail investors.  

It's the equivalent of a startup using AWS and saying they have an Amazon partnership so give them $6B.  

This wasn't Nvidia directly funding $IREN yet, just a risk free option to. 

There's ...`

**[23]** pred=`f6ae7b94-e4a8-4678-a5a1-bb6b07adc9ee` pub=2026-05-11 entry=2026-05-12 px=$55.40
- LLM: dir=short conv=4 hz=long_term qc=None hedged=0
- 1m: 55.4 raw=N/A excess=-2.36%
- 原文: `As I said before $IREN is basically dogsht compared to $NBIS.

$NVDA didn’t give $IREN funding yet. 

So IREN needs to figure out how to buy enough GPUs to monetize 5GW capacity through their 6B ATM and other means.

It’s an endless dilution machine just because they secured power.

I call $IREN holders 0 IQ because they just buy in it to get diluted without understanding nuances of financing. 

Nvidia actually gave $NBIS funds.

While Nvidia got a free no-risk purchase agreement for allowing $I...`

**[24]** pred=`834ad06a-b880-4d63-ba61-6df26771fb71` pub=2026-05-19 entry=2026-05-20 px=$49.12
- LLM: dir=short conv=4 hz=long_term qc=None hedged=0
- 1m: 49.12 raw=N/A excess=N/A
- 原文: `$IREN back down -34% from $70 to $46.

I wonder if one of the dumbest communities on X finally learned to read?

$NBIS is objectively the better Neocloud, with actual financing.

-> Nvidia didn’t fund $IREN at all. They got a free purchase agreement to let IREN use their logos and dilute for GPUS.

$NVDA actually gave $NBIS capital.

-> $IREN is facing endless dilution like $BKKT, $ASST, $SLNH as retail wealth transfers capital over from $6,000,000,000 ATMs, on a dwindling “5 GW capacity” moat. ...`


### JD (n_long=0  n_short=1)


**[1]** pred=`4c3c3419-0188-4d2d-ba1d-cca26e35df70` pub=2026-02-02 entry=2026-02-03 px=$28.10
- LLM: dir=short conv=3 hz=event_driven qc=None hedged=0
- 1m: 28.1 raw=N/A excess=+9.36%
- 原文: `Markets are seeing liquidation cascades.

Silver's crash is now extending into other markets like Crypto and US/Foreign stocks.

Here's what's happening:

And here's what to expect from:

- $BMNR (Crypto)
- $RKLB (High-Beta)  
- $SNDK (AI) 
- to Samsung (Foreign). 

The "Warsh" Fed Chair nomination was the initial trigger that caused the selloff as markets viewed him as a "Hawk" -> Quantitative Tightening. 

However, this is a mistake as the fed chair is likely aligned with Trump's policies, and...`


### LCID (n_long=0  n_short=1)


**[1]** pred=`1b022b19-7c0d-474f-84b8-d3c4885269db` pub=2026-03-28 entry=2026-03-30 px=$9.51
- LLM: dir=short conv=2 hz=event_driven qc=None hedged=0
- 1m: 9.51 raw=N/A excess=+39.43%
- 原文: `The Serenity Doomsday ETF:

25% | $FAZ
25% | $GUSH
20%| $LCID Short
10% | $SQQQ
10% $UVIX
10% | $NVDA Puts

Rationale:
$FAZ / 3x short financial - Private Market liquidity play on Middle Eastern capital abandoning private markets if all their oil fields get blown apart.

$GUSH / 2x Long US OIl and Gas - Global crude prices that will likely skyrocket, and American producers reap record windfall in profits.

$SQQQ / 3x short Nasdaq - Google, Amazon, Apple, Microsoft forced selling if liquidity get...`


### LUNR (n_long=0  n_short=1)


**[1]** pred=`93f50658-8da5-4bac-80cd-d1cc90e8392a` pub=2025-09-24 entry=2025-09-25 px=$9.64
- LLM: dir=short conv=3 hz=long_term qc=None hedged=0
- 1m: 9.64 raw=N/A excess=-32.88%
- 原文: `$LUNR is an enigma. I've sold puts on it because of high IV but I don't like it long term compared to $ASTS or $RKLB.

With $SNAP, I've always maintained that fundamentally it was extremely undervalued from 1.1B MAU but it just needs a change of CEO. They're heading the wrong direction with AR and should just compete with Tiktok.

With $DJT, yeah never short the President's company. 0 clue. Could be a 10x if the President wants to use his powers to help his own company, we'll never know.`


### LVMH (n_long=0  n_short=1)


**[1]** pred=`a715ae87-ce02-49ea-b2d6-9dc83c397e73` pub=2026-01-18 entry=None px=NULL
- LLM: dir=short conv=3 hz=event_driven qc=None hedged=0
- 1m: None raw=N/A excess=N/A
- 原文: `I'm a bull that's excited about Greenland trade tensions.   

US defense like $UAVS and $DPRO are likely to benefit. Same with rare earth/critical materials.   

Can't say the same about the pharma bulls in $NVO, European luxury like $LVMH, or possibly big tech.

As you mentioned, I agree it's just noise to the AI trade.`


### LWLG (n_long=0  n_short=1)


**[1]** pred=`a81fb02e-ca49-425a-8ccd-a192eb46de12` pub=2026-03-13 entry=2026-03-16 px=$7.83
- LLM: dir=short conv=3 hz=event_driven qc=None hedged=0
- 1m: 7.835 raw=N/A excess=-54.31%
- 原文: `@themissinglinks I personally shorted $LWLG because this ticker keeps getting spammed under all my posts.`


### MA (n_long=0  n_short=1)


**[1]** pred=`7c864374-fc7f-4fe3-b8c9-17b6f11d5cd7` pub=2026-03-19 entry=2026-03-20 px=$492.47
- LLM: dir=short conv=3 hz=long_term qc=None hedged=0
- 1m: 492.47 raw=N/A excess=-3.83%
- 原文: `I’m surprised markets aren’t pricing in long term disruption of card networks + interchange like $V and $MA.

By $CRCL and $COIN.

From Global Markets Head at Circle:

"Over the past nine months, AI agents completed 140 million payments with a total transaction volume of 43 million US dollars. 

Among these, 98.6% were settled in USDC, with an average transaction amount of only 0.31 US dollars."

Card networks and % fee payment processors like $PYPL are likely going to be cooked?`


### MELI (n_long=0  n_short=1)


**[1]** pred=`b6e20256-38cc-46df-8780-d6d5f5be898b` pub=2026-02-02 entry=2026-02-03 px=$2145.00
- LLM: dir=short conv=3 hz=event_driven qc=None hedged=0
- 1m: 2145.0 raw=N/A excess=+17.00%
- 原文: `Markets are seeing liquidation cascades.

Silver's crash is now extending into other markets like Crypto and US/Foreign stocks.

Here's what's happening:

And here's what to expect from:

- $BMNR (Crypto)
- $RKLB (High-Beta)  
- $SNDK (AI) 
- to Samsung (Foreign). 

The "Warsh" Fed Chair nomination was the initial trigger that caused the selloff as markets viewed him as a "Hawk" -> Quantitative Tightening. 

However, this is a mistake as the fed chair is likely aligned with Trump's policies, and...`


### MQ (n_long=0  n_short=1)


**[1]** pred=`151db4cd-3e1e-4602-9c0a-0e8d3b42fc61` pub=2025-10-30 entry=2025-10-31 px=$4.44
- LLM: dir=short conv=3 hz=long_term qc=None hedged=0
- 1m: 4.44 raw=N/A excess=-6.76%
- 原文: `@BarnieTaintpipe I’m aware of them both already. Off the top of my head $MQ not a fan because singular dependency on Square if that was the customer for Cash App. Also they can launch their own card offerings in the future.

$DAVE I liked a lot more`


### NVDA (n_long=23  n_short=4)


**[1]** pred=`d5a38401-78f6-41e0-b78c-8f3f56f0af94` pub=2025-10-06 entry=2025-10-07 px=$186.23
- LLM: dir=short conv=3 hz=event_driven qc=None hedged=0
- 1m: 186.23 raw=N/A excess=-4.82%
- 原文: `@yield_addicted For the deal, I'd say net negative: $NVDA, $CRWV (Nvda centric)

Net positive (almost everything else): $AMD, NBIS, CIFR, IREN, TSM, etc. 

The 2.5% drop makes sense off moat narrative changes.`

**[2]** pred=`73b49ac0-a89f-4598-aa9f-7087d64841ea` pub=2025-12-17 entry=2025-12-18 px=$174.53
- LLM: dir=short conv=3 hz=long_term qc=None hedged=0
- 1m: 174.53 raw=N/A excess=-5.04%
- 原文: `Just In: Amazon's $10B OpenAI Funding and The AI Supply Chain Ripple Effect. 

$AMZN is set to invest $10B+ in OpenAI at a $500B+ valuation

Why this is a MASSIVE structural shift for AI stocks:

1. De-Risking the AI DC trade: ( $ORCL, $CRWV, $APLD, $CORZ )

With the SPEED Bill mentioned earlier, the main issues affecting Neoclouds were:

1. DC Delays & Deferred Revenue 
2. Unsustainable CapEx → No FCF 
3. OpenAI Contagion/Backlog.

the Speed bill directly addresses #1 and #2. But not #3 with Op...`

**[3]** pred=`b55acb51-0900-4fe0-b363-2ed274fd4da6` pub=2025-12-19 entry=2025-12-22 px=$183.92
- LLM: dir=short conv=3 hz=long_term qc=None hedged=0
- 1m: 183.92 raw=N/A excess=-2.04%
- 原文: `Latest news: OpenAI is raising funds at a $750B valuation after their $10B+ Amazon round at $500B.

$CRWV: +15.85%
$NBIS: +10.28%

With this deal, companies like Coreweave and Oracle structurally have less counterparty risk with OpenAI's stronger balance sheet to fund capex requirements.

Companies like Nebius that are algorithmically tied to the sector leaders are up as a result. High-Beta Assets from Rocketlab to Bitcoin are up across the board.

There was extreme volatility recently with the ...`

**[4]** pred=`d41951b0-eb6b-4ae9-b498-34a233f43003` pub=2026-03-28 entry=2026-03-30 px=$168.78
- LLM: dir=short conv=2 hz=event_driven qc=None hedged=0
- 1m: 168.78 raw=N/A excess=-23.98%
- 原文: `The Serenity Doomsday ETF:

25% | $FAZ
25% | $GUSH
20%| $LCID Short
10% | $SQQQ
10% $UVIX
10% | $NVDA Puts

Rationale:
$FAZ / 3x short financial - Private Market liquidity play on Middle Eastern capital abandoning private markets if all their oil fields get blown apart.

$GUSH / 2x Long US OIl and Gas - Global crude prices that will likely skyrocket, and American producers reap record windfall in profits.

$SQQQ / 3x short Nasdaq - Google, Amazon, Apple, Microsoft forced selling if liquidity get...`


### NVO (n_long=4  n_short=1)


**[1]** pred=`ce9f007c-206f-46d2-a830-972ba11e8b3e` pub=2026-01-18 entry=2026-01-20 px=$60.22
- LLM: dir=short conv=3 hz=event_driven qc=None hedged=0
- 1m: 60.215 raw=N/A excess=+19.54%
- 原文: `I'm a bull that's excited about Greenland trade tensions.   

US defense like $UAVS and $DPRO are likely to benefit. Same with rare earth/critical materials.   

Can't say the same about the pharma bulls in $NVO, European luxury like $LVMH, or possibly big tech.

As you mentioned, I agree it's just noise to the AI trade.`


### OKLO (n_long=1  n_short=6)


**[1]** pred=`d300e7f1-1f5f-4fe7-94b7-a1eea418dcc4` pub=2025-09-29 entry=2025-09-30 px=$115.46
- LLM: dir=short conv=5 hz=6m qc=None hedged=0
- 1m: 115.46 raw=N/A excess=-24.22%
- 原文: `Monday Market Close Thoughts:

Extremely Strong Buy
$NBIS
$ETOR
$LTC
$VIRT

Buy
$AMZN
$SMCI
$TGT
$CRM
$TSM
$CRDO
$SG
$CIFR
$LULU
$SLNH
$ORCL
$MSTR
$RIOT
$MARA

Hold
$IREN
$HIMS
$RKLB
$PYPL
$MRVL
$IBIT
$UPWK
$GRAB
$ALAB
$ASTS
$SOFI
$NVDA
$NVO

Sell
$HOOD
$TSLA
$RDDT
$CRCL
$PLTR
$BMNR

Strong Sell
$OKLO
$QBTS
$IONQ

_

Feel free to disagree but these are just my thoughts

Strong Buy Explanations

- Bought ~$70K of Virtu calls, 28% IV and just 6.6 forward p/e is undervalued.

- Always DCA NBIS on t...`

**[2]** pred=`b86fde2f-61f6-46ad-9207-11a267c5a47c` pub=2025-10-04 entry=2025-10-06 px=$131.40
- LLM: dir=short conv=2 hz=6m qc=None hedged=0
- 1m: 131.395 raw=N/A excess=+14.59%
- 原文: `Friday Market Close, Personal Thoughts and Explanations:

Strong Buy
$RDDT
$SNAP
$AMZN
$ETOR
$NBIS
$LTC

Buy
$UPWK
$MSTR
$ORCL
$TGT
$CIFR
$VIRT
$CRDO
$WULF
$SOFI
$META
$AVGO
$MRVL
$SMCI
$DELL

Hold
$RKLB
$TSM
$IREN
$RR
$ALAB
$HOOD
$FLNC
$EOSE
$BE
$RIOT
$MARA
$GRAB
$ASTS
$NVO
$NVDA

Sell
$TSLA
$CRCL
$PLTR
$BMNR

Strong Sell
$RGTI
$OKLO
$QBTS
$IONQ

_

(again, not great DD, just writing random thoughts about the process). 

Strong Buys

Reddit - Dropped 29% off immaterial news that ChatGPT wasn't ...`

**[3]** pred=`00ef565a-ecfa-4463-a3fb-6eb00e2bbe35` pub=2025-10-11 entry=2025-10-13 px=$158.00
- LLM: dir=short conv=2 hz=6m qc=None hedged=0
- 1m: 158.0 raw=N/A excess=+34.04%
- 原文: `Based Friday Market Close (-3.6% SPY day), Thoughts and Explanations

Strong Buy
$IBIT
$LTC
$WLAC
$NBIS
$MP
$TSM
(For Next Year)
$ETOR
$DKNG
$SNAP

Buy
$UPWK
$CRDO
$ALAB
$AMZN
$META
$UNH
$SG
$TGT
$BULL
$FLY
$CIFR
$WULF
$IREN
$GLXY
$SMCI
$DELL
$MRVL

Hold
$RKLB
$HOOD
$RBRK
$MU
$HOOD
$GRAB
$MARA
$RIOT
$NVO
$RR
$ELOSE
$FLNC
$SEI
$PLTR

Sell
$CRCL
$ETH
$BMNR
$PL
$BKSY

Strong Sell
$RGTI
$OKLO
$IONQ
$QBTS
$QUBT

_

Explanations:

IBIT - Dumped to $104k, Bitcoin demand has been institutional, tariff f...`

**[4]** pred=`4735bff3-ef41-4a94-91ca-cc0c6261077c` pub=2025-10-12 entry=2025-10-13 px=$158.00
- LLM: dir=short conv=2 hz=6m qc=None hedged=0
- 1m: 158.0 raw=N/A excess=+34.04%
- 原文: `And there’s the de-escalation

Reuters: “Taiwan sees no significant impact on chip sector”

Trump: “Don’t worry about China, it will all be fine… President Xi just had a bad moment.”

Biggest crypto liquidation to date 

Stocks with little impact down 7%

Dip buying opportunity https://t.co/2sUEV7Dg8s`

**[5]** pred=`102a449e-0318-441f-92e6-3e278902b3d4` pub=2025-10-19 entry=2025-10-20 px=$167.19
- LLM: dir=short conv=2 hz=6m qc=None hedged=0
- 1m: 167.19 raw=N/A excess=+42.20%
- 原文: `October 20th, Important Rate Cut Trading Week.

Personal thoughts and explanations: 

🛝 = Swing Trade

🐈 = Catalyst Trade

🎇 = 2026 Trade, Tax Harvested

Fire Sale
🔥 $NBIS 

Strong Buy
$TSM
$AMKR
$WLAC
$AMZN
$LTC 🐈
$RDDT
$HIMS 🛝
$IBIT
$ALAB
$CRDO
$SMCI
$FLY 🎇
$SNAP 🎇
$ETOR 🎇
$LULU 🎇

Buy
$AMD
$HOOD 
$RBRK
$UNH
$TGT 🐈
$IREN 🐈
$WYFI
$WULF
$CIFR
$SLNH
$BITF
$GLXY
$FLNC
$MU

(Skipping Hold, since any other stock I've mentioned in the past, it probably just hold it since nothing's changed).

Sell
$ET...`

**[6]** pred=`0fc7045d-1208-42cc-9f35-57235aa4ecad` pub=2025-11-19 entry=2025-11-20 px=$106.11
- LLM: dir=short conv=2 hz=6m qc=None hedged=0
- 1m: 106.11 raw=N/A excess=+22.83%
- 原文: `The Great Reset, November 19th ratings:

Strong Buy

· $NBIS
· $CIFR
· $WULF
· $RDDT
· $SNAP
· $ALAB
· $META
· $AMZN
· $GOOGL
· $IBIT
· $SOL
· $TSM
· $RKLB
· $TSSI
· $SMCI
· $GLXY
· $SG

Buy

· $IREN
· $KRUS
· $CRCL
· $LTC
· $MRVL
· $KRKNF
· $OSS
· $CORZ
· $WLAC
· $WYFI
· $AMD
· $TE
· $CRDO
· $FLNC
· $HIMS
· $BULL
· $ETOR
· $FISV
· $FLY
· $MU

Hold

· $COIN
· $HOOD
· $IBKR
· $NVDA
· $PLTR
· $TSLA
· CRWV
· $APLD
· ORCL

Avoid

· RGTI
· $IONQ
· SLNH
· $QBTS
· OKLO
· $WMT
· BMNR
· $SBET
· CRWV
_

E...`


### ONDS (n_long=6  n_short=2)


**[1]** pred=`80b98d2e-98c8-45d9-9014-5a1f9e3dc7ae` pub=2026-01-19 entry=2026-01-20 px=$11.86
- LLM: dir=short conv=3 hz=long_term qc=None hedged=0
- 1m: 11.855 raw=N/A excess=+3.92%
- 原文: `Personally speaking, I feel like $ONDS is richly priced compared to other drone companies. 

I have $AVAV, $DPRO, $KTOS, and $AIRO for drone exposure. 

(Just going off the top of my head, dont take this too literally) Fwd EV/revenue multiples was ~28s+ now for Ondas. Even AVAV was 8-9 and they were in the replicator program. 

Airo was for counter UAV for replicator 2.

When I bought $AIRO was trading at ~2.5 fwd p/s (probably higher now, maybe 3-4's). 

Even $DPRO might even be potential 2.8 f...`

**[2]** pred=`f422613e-0afd-4f98-9370-997a9aca2d33` pub=2026-02-02 entry=2026-02-03 px=$11.01
- LLM: dir=short conv=3 hz=event_driven qc=None hedged=0
- 1m: 11.01 raw=N/A excess=+4.72%
- 原文: `Markets are seeing liquidation cascades.

Silver's crash is now extending into other markets like Crypto and US/Foreign stocks.

Here's what's happening:

And here's what to expect from:

- $BMNR (Crypto)
- $RKLB (High-Beta)  
- $SNDK (AI) 
- to Samsung (Foreign). 

The "Warsh" Fed Chair nomination was the initial trigger that caused the selloff as markets viewed him as a "Hawk" -> Quantitative Tightening. 

However, this is a mistake as the fed chair is likely aligned with Trump's policies, and...`


### OPTT (n_long=3  n_short=1)


**[1]** pred=`a3691886-fab0-4f31-97b1-dc3ac69a584c` pub=2026-01-24 entry=2026-01-26 px=$0.60
- LLM: dir=short conv=3 hz=event_driven qc=None hedged=0
- 1m: 0.6 raw=N/A excess=+32.50%
- 原文: `For $OPTT, I made this comment to someone else where it's really susceptible to large movements (so profitable), bc there's hype on contracts like partnerships feeding into Andruil.

But they have $11m cash and $10m debt with $17m liabilities so it seems incredibly likely they’ll dilute if there's any retail interest. 

Feels like capital dilution is imminent unless there's any alpha i missed`


### ORCL (n_long=12  n_short=6)


**[1]** pred=`d3269bda-ca18-4edb-a199-a879ed40c3ab` pub=2025-11-14 entry=2025-11-17 px=$218.21
- LLM: dir=short conv=3 hz=long_term qc=None hedged=0
- 1m: 218.21 raw=N/A excess=+17.50%
- 原文: `Neocloud isn't winner takes all, it's a whole ecosystem but not everything can become AWS.

We're seeing $NBIS, $IREN, $CRWV, and $ORCL compete in the true "Neocloud", most profitable full stack race to become Azure/AWS. Doing vertical integration, building capacity, buying GPUs, and doing orchestration, and some incubants entering the race. 

So far $NBIS is the clear winner with hyperscalers + enterprises + good balance sheet in a matter of time, $CRWV is swamped with interest debt, $ORCL fail...`

**[2]** pred=`80b1a0b9-05b5-4659-8762-6d5d3fa1ef54` pub=2025-11-25 entry=2025-11-26 px=$209.50
- LLM: dir=short conv=3 hz=long_term qc=None hedged=0
- 1m: 209.5 raw=N/A excess=+5.87%
- 原文: `The main fear I have in the "AI Bubble" is OpenAI and their $1T capex promises. That is a clear bubble (and private valuations of LLMs). Most other things, no. 

Any company directly reliant to them $ORCL, $CRWV might be in trouble given how AI models leapfrogged GPT. So the simple thing to do is stay away!

Personally speaking, ChatGPT5.1 is horrendous and I actually cancelled my subscription to go with Gemini/Claude. Claude Opus 4.5 outperforms Codex in coding tasks. Gemini outperforms ChatGPT...`

**[3]** pred=`0caebbc5-b594-4878-9f4d-0dd8a7e01677` pub=2025-12-11 entry=2025-12-12 px=$196.37
- LLM: dir=short conv=3 hz=event_driven qc=None hedged=0
- 1m: 196.37 raw=N/A excess=+1.41%
- 原文: `I’ve been putting $ORCL on avoid and this earnings was the reason why on the 11% drop.

I need more time to look into it but it’s not just capex spend that’s worrying, a large part of it is because of OpenAi (which doesn’t have the funding for the backlog) that a lot of the spend is for.

Other neoclouds like $NBIS don’t have this problem because their backlog is from $MSFT that actually have the money. And hyperscaler capex funnel was the core Neocloud thesis, not levered/contingency on OpenAi ...`

**[4]** pred=`5dfe7954-1e7c-4e50-b52b-bd25b23d82ed` pub=2025-12-11 entry=2025-12-12 px=$196.37
- LLM: dir=short conv=4 hz=event_driven qc=None hedged=0
- 1m: 196.37 raw=N/A excess=+1.41%
- 原文: `Oracle [ $ORCL ] earning results and its effect on the neocloud sector like $NBIS & $IREN:

Oracle reported earnings with a beat on EPS and a record backlog but, dropped 12% after hours.

Oracle is down 39.8% from September 11th highs and brought down the sector with it.

Here's why:

The sell-off was not merely a reaction to marginal revenue miss, but both an algorithmic short and investor selloff on the sustainability of the AI capex cycle and the creditworthiness of the sector's primary tenan...`

**[5]** pred=`088c1ecd-749f-44a4-ba8b-6aa6df402cc8` pub=2025-12-12 entry=2025-12-15 px=$188.29
- LLM: dir=short conv=3 hz=long_term qc=None hedged=0
- 1m: 188.29 raw=N/A excess=-0.83%
- 原文: `Broadcom [ $AVGO ] earnings results and its effect on the AI sector like $LITE and $NBIS:

Broadcom's ER was "double beat" with $18.02B revenue (+28% Y/Y) and $1.95 EPS, beating consensus.

But AVGO dropped -11.64% and brought down the AI sector. 

Is this a buying opportunity?

Yes.

Broadcom is seen as a hyperscaler ASIC proxy growth as companies like $AMZN Trainium, $MSFT Maia, and most importantly $GOOGL TPU V7 Ironwood are scaled through it.

And by proxy companies like $ALAB (-13.2%), $CRD...`

**[6]** pred=`c4bc984b-1c81-4fc6-91c4-3cca6551fd71` pub=2026-01-24 entry=2026-01-26 px=$179.10
- LLM: dir=short conv=3 hz=long_term qc=None hedged=0
- 1m: 179.1 raw=N/A excess=+17.43%
- 原文: `I've been saying this about $ORCL in the 300's though too when they projected $25B capex to $50B+ in just 1 year time.

This is to fulfill $500B+ in backlog. But that backlog doesn't matter when it's OpenAI (eg. $300B Stargate). 

They're borrowing so much to build out on a sole customer, which happens to be the most obvious + extreme counterparty risk given OpenAI's other contractual obligations. 

When you compound that with losing revenue share to Gemini, it looks increasingly likely they'll ...`


### PL (n_long=3  n_short=3)


**[1]** pred=`c2ba60db-1a93-4645-b72a-6598f72729b2` pub=2025-10-11 entry=2025-10-13 px=$15.21
- LLM: dir=short conv=2 hz=6m qc=None hedged=0
- 1m: 15.21 raw=N/A excess=+18.01%
- 原文: `Based Friday Market Close (-3.6% SPY day), Thoughts and Explanations

Strong Buy
$IBIT
$LTC
$WLAC
$NBIS
$MP
$TSM
(For Next Year)
$ETOR
$DKNG
$SNAP

Buy
$UPWK
$CRDO
$ALAB
$AMZN
$META
$UNH
$SG
$TGT
$BULL
$FLY
$CIFR
$WULF
$IREN
$GLXY
$SMCI
$DELL
$MRVL

Hold
$RKLB
$HOOD
$RBRK
$MU
$HOOD
$GRAB
$MARA
$RIOT
$NVO
$RR
$ELOSE
$FLNC
$SEI
$PLTR

Sell
$CRCL
$ETH
$BMNR
$PL
$BKSY

Strong Sell
$RGTI
$OKLO
$IONQ
$QBTS
$QUBT

_

Explanations:

IBIT - Dumped to $104k, Bitcoin demand has been institutional, tariff f...`

**[2]** pred=`aa3e294c-fdad-4ed3-b9cf-e1fc1481511c` pub=2025-10-12 entry=2025-10-13 px=$15.21
- LLM: dir=short conv=2 hz=6m qc=None hedged=0
- 1m: 15.21 raw=N/A excess=+18.01%
- 原文: `And there’s the de-escalation

Reuters: “Taiwan sees no significant impact on chip sector”

Trump: “Don’t worry about China, it will all be fine… President Xi just had a bad moment.”

Biggest crypto liquidation to date 

Stocks with little impact down 7%

Dip buying opportunity https://t.co/2sUEV7Dg8s`

**[3]** pred=`c3f0b059-5da3-4cad-8f2e-266afa7f7132` pub=2025-10-19 entry=2025-10-20 px=$14.02
- LLM: dir=short conv=2 hz=6m qc=None hedged=0
- 1m: 14.02 raw=N/A excess=+18.33%
- 原文: `October 20th, Important Rate Cut Trading Week.

Personal thoughts and explanations: 

🛝 = Swing Trade

🐈 = Catalyst Trade

🎇 = 2026 Trade, Tax Harvested

Fire Sale
🔥 $NBIS 

Strong Buy
$TSM
$AMKR
$WLAC
$AMZN
$LTC 🐈
$RDDT
$HIMS 🛝
$IBIT
$ALAB
$CRDO
$SMCI
$FLY 🎇
$SNAP 🎇
$ETOR 🎇
$LULU 🎇

Buy
$AMD
$HOOD 
$RBRK
$UNH
$TGT 🐈
$IREN 🐈
$WYFI
$WULF
$CIFR
$SLNH
$BITF
$GLXY
$FLNC
$MU

(Skipping Hold, since any other stock I've mentioned in the past, it probably just hold it since nothing's changed).

Sell
$ET...`


### PLTR (n_long=2  n_short=5)


**[1]** pred=`cd4e84ef-d6fd-4448-8215-5de46a29bbb6` pub=2025-07-28 entry=2025-07-29 px=$158.72
- LLM: dir=short conv=3 hz=event_driven qc=None hedged=0
- 1m: 158.715 raw=N/A excess=+1.26%
- 原文: `Shorting $PLTR, thanks Jim. https://t.co/2xKvNnPqvE`

**[2]** pred=`cc40b45a-ebfa-4aef-a713-1e5f308bc287` pub=2025-08-23 entry=2025-08-25 px=$156.10
- LLM: dir=short conv=2 hz=6m qc=None hedged=0
- 1m: 156.1 raw=N/A excess=-15.03%
- 原文: `Some decent recovery/swing trades right now

1. $SG - $9.39
2. $SNAP - $7.21
3. $UNH - $306.8
4. $ETOR - $46.8
5. $NVO - $57.00
6. $HIMS - $44.73
7. $CRWV - $94.7

Stay away from these dips

1. $CRCL - $136.2
2. $PLTR - $159.6
3. $DUOL - $334.5`

**[3]** pred=`4d437ef0-e2c8-4d75-ad71-4e8187ce0c21` pub=2025-09-29 entry=2025-09-30 px=$178.98
- LLM: dir=short conv=2 hz=6m qc=None hedged=0
- 1m: 178.98 raw=N/A excess=-11.08%
- 原文: `Monday Market Close Thoughts:

Extremely Strong Buy
$NBIS
$ETOR
$LTC
$VIRT

Buy
$AMZN
$SMCI
$TGT
$CRM
$TSM
$CRDO
$SG
$CIFR
$LULU
$SLNH
$ORCL
$MSTR
$RIOT
$MARA

Hold
$IREN
$HIMS
$RKLB
$PYPL
$MRVL
$IBIT
$UPWK
$GRAB
$ALAB
$ASTS
$SOFI
$NVDA
$NVO

Sell
$HOOD
$TSLA
$RDDT
$CRCL
$PLTR
$BMNR

Strong Sell
$OKLO
$QBTS
$IONQ

_

Feel free to disagree but these are just my thoughts

Strong Buy Explanations

- Bought ~$70K of Virtu calls, 28% IV and just 6.6 forward p/e is undervalued.

- Always DCA NBIS on t...`

**[4]** pred=`4ec267e1-2613-4a43-a938-c49fdbef1193` pub=2025-10-04 entry=2025-10-06 px=$179.18
- LLM: dir=short conv=2 hz=6m qc=None hedged=0
- 1m: 179.18 raw=N/A excess=-6.45%
- 原文: `Friday Market Close, Personal Thoughts and Explanations:

Strong Buy
$RDDT
$SNAP
$AMZN
$ETOR
$NBIS
$LTC

Buy
$UPWK
$MSTR
$ORCL
$TGT
$CIFR
$VIRT
$CRDO
$WULF
$SOFI
$META
$AVGO
$MRVL
$SMCI
$DELL

Hold
$RKLB
$TSM
$IREN
$RR
$ALAB
$HOOD
$FLNC
$EOSE
$BE
$RIOT
$MARA
$GRAB
$ASTS
$NVO
$NVDA

Sell
$TSLA
$CRCL
$PLTR
$BMNR

Strong Sell
$RGTI
$OKLO
$QBTS
$IONQ

_

(again, not great DD, just writing random thoughts about the process). 

Strong Buys

Reddit - Dropped 29% off immaterial news that ChatGPT wasn't ...`

**[5]** pred=`247d832d-a016-4235-b712-1be8d32fd4d8` pub=2026-01-02 entry=2026-01-05 px=$174.88
- LLM: dir=short conv=2 hz=6m qc=None hedged=0
- 1m: 174.88 raw=N/A excess=+20.21%
- 原文: `Welcome to 2026. Jan 1st ratings:

Strong Buy:
$TTD
$SMCI
$AIRO
$INTC
$HIMS
$AXTI
$TSM
$NBIS
$CIFR
Samsung Electronics (KRX: 005930)
$HUT
$IREN
$WULF
$GLXY
$TSSI
$META
$ETOR
$CRCL

Buy:
$KRKNF
$ONDS
$GEMI
$NVDA
$MU
$AMKR
SK Hynix
$SNAP
$RDDT
$AAOI
$COHR
$FISV
$FLY
$DJT
$LITE
$AMZN
$MRVL
$AVGO
$OSS
$BULL
$ORCL
$CRDO
$ALAB

Avoid:
$RGTI
$QBTS
$RGTI
$BMNR
$ETH
$PLTR
$WMT

_

TLDR thoughts:

TTD - Complete valuation reset dropping 67% YTD, compounded by EOY tax sell-off. Great recovery play going in...`


### POET (n_long=23  n_short=1)


**[1]** pred=`678660f3-754b-448e-a56d-e8d6bf643b28` pub=2026-04-27 entry=2026-04-28 px=$7.54
- LLM: dir=short conv=3 hz=long_term qc=None hedged=0
- 1m: 7.54 raw=N/A excess=-75.86%
- 原文: `@AD14977 I've always said $POET is the most likely to get designed out down the road.

They just buy lasers and package them... and $MRVL can just go directly to the laser source and do the same with some delays to their roadmap.`


### PYPL (n_long=2  n_short=1)


**[1]** pred=`2d356a16-93c7-4620-af30-f9f826ef23fd` pub=2026-03-19 entry=2026-03-20 px=$44.33
- LLM: dir=short conv=3 hz=long_term qc=None hedged=0
- 1m: 44.33 raw=N/A excess=-14.78%
- 原文: `I’m surprised markets aren’t pricing in long term disruption of card networks + interchange like $V and $MA.

By $CRCL and $COIN.

From Global Markets Head at Circle:

"Over the past nine months, AI agents completed 140 million payments with a total transaction volume of 43 million US dollars. 

Among these, 98.6% were settled in USDC, with an average transaction amount of only 0.31 US dollars."

Card networks and % fee payment processors like $PYPL are likely going to be cooked?`


### QBTS (n_long=1  n_short=9)


**[1]** pred=`0276896b-6f57-4194-812b-361671074919` pub=2025-09-29 entry=2025-09-30 px=$24.94
- LLM: dir=short conv=5 hz=6m qc=None hedged=0
- 1m: 24.94 raw=N/A excess=-37.37%
- 原文: `Monday Market Close Thoughts:

Extremely Strong Buy
$NBIS
$ETOR
$LTC
$VIRT

Buy
$AMZN
$SMCI
$TGT
$CRM
$TSM
$CRDO
$SG
$CIFR
$LULU
$SLNH
$ORCL
$MSTR
$RIOT
$MARA

Hold
$IREN
$HIMS
$RKLB
$PYPL
$MRVL
$IBIT
$UPWK
$GRAB
$ALAB
$ASTS
$SOFI
$NVDA
$NVO

Sell
$HOOD
$TSLA
$RDDT
$CRCL
$PLTR
$BMNR

Strong Sell
$OKLO
$QBTS
$IONQ

_

Feel free to disagree but these are just my thoughts

Strong Buy Explanations

- Bought ~$70K of Virtu calls, 28% IV and just 6.6 forward p/e is undervalued.

- Always DCA NBIS on t...`

**[2]** pred=`4ba2421e-8d7b-4949-83bf-5ba62f918a48` pub=2025-10-04 entry=2025-10-06 px=$32.01
- LLM: dir=short conv=2 hz=6m qc=None hedged=0
- 1m: 32.01 raw=N/A excess=+7.09%
- 原文: `Friday Market Close, Personal Thoughts and Explanations:

Strong Buy
$RDDT
$SNAP
$AMZN
$ETOR
$NBIS
$LTC

Buy
$UPWK
$MSTR
$ORCL
$TGT
$CIFR
$VIRT
$CRDO
$WULF
$SOFI
$META
$AVGO
$MRVL
$SMCI
$DELL

Hold
$RKLB
$TSM
$IREN
$RR
$ALAB
$HOOD
$FLNC
$EOSE
$BE
$RIOT
$MARA
$GRAB
$ASTS
$NVO
$NVDA

Sell
$TSLA
$CRCL
$PLTR
$BMNR

Strong Sell
$RGTI
$OKLO
$QBTS
$IONQ

_

(again, not great DD, just writing random thoughts about the process). 

Strong Buys

Reddit - Dropped 29% off immaterial news that ChatGPT wasn't ...`

**[3]** pred=`7a95e9cf-33b2-411a-aada-36ee40104abf` pub=2025-10-11 entry=2025-10-13 px=$34.28
- LLM: dir=short conv=2 hz=6m qc=None hedged=0
- 1m: 34.28 raw=N/A excess=+15.43%
- 原文: `Based Friday Market Close (-3.6% SPY day), Thoughts and Explanations

Strong Buy
$IBIT
$LTC
$WLAC
$NBIS
$MP
$TSM
(For Next Year)
$ETOR
$DKNG
$SNAP

Buy
$UPWK
$CRDO
$ALAB
$AMZN
$META
$UNH
$SG
$TGT
$BULL
$FLY
$CIFR
$WULF
$IREN
$GLXY
$SMCI
$DELL
$MRVL

Hold
$RKLB
$HOOD
$RBRK
$MU
$HOOD
$GRAB
$MARA
$RIOT
$NVO
$RR
$ELOSE
$FLNC
$SEI
$PLTR

Sell
$CRCL
$ETH
$BMNR
$PL
$BKSY

Strong Sell
$RGTI
$OKLO
$IONQ
$QBTS
$QUBT

_

Explanations:

IBIT - Dumped to $104k, Bitcoin demand has been institutional, tariff f...`

**[4]** pred=`18d808c7-c461-468f-9a15-215d273c4d72` pub=2025-10-12 entry=2025-10-13 px=$34.28
- LLM: dir=short conv=2 hz=6m qc=None hedged=0
- 1m: 34.28 raw=N/A excess=+15.43%
- 原文: `And there’s the de-escalation

Reuters: “Taiwan sees no significant impact on chip sector”

Trump: “Don’t worry about China, it will all be fine… President Xi just had a bad moment.”

Biggest crypto liquidation to date 

Stocks with little impact down 7%

Dip buying opportunity https://t.co/2sUEV7Dg8s`

**[5]** pred=`d2f38a5d-bf7d-4e3a-94c2-9a5f9596d946` pub=2025-10-19 entry=2025-10-20 px=$39.52
- LLM: dir=short conv=2 hz=6m qc=None hedged=0
- 1m: 39.5201 raw=N/A excess=+41.98%
- 原文: `October 20th, Important Rate Cut Trading Week.

Personal thoughts and explanations: 

🛝 = Swing Trade

🐈 = Catalyst Trade

🎇 = 2026 Trade, Tax Harvested

Fire Sale
🔥 $NBIS 

Strong Buy
$TSM
$AMKR
$WLAC
$AMZN
$LTC 🐈
$RDDT
$HIMS 🛝
$IBIT
$ALAB
$CRDO
$SMCI
$FLY 🎇
$SNAP 🎇
$ETOR 🎇
$LULU 🎇

Buy
$AMD
$HOOD 
$RBRK
$UNH
$TGT 🐈
$IREN 🐈
$WYFI
$WULF
$CIFR
$SLNH
$BITF
$GLXY
$FLNC
$MU

(Skipping Hold, since any other stock I've mentioned in the past, it probably just hold it since nothing's changed).

Sell
$ET...`

**[6]** pred=`2a5043a5-b28d-4c6b-83b4-95dccc57f74a` pub=2025-10-20 entry=2025-10-21 px=$33.62
- LLM: dir=short conv=3 hz=long_term qc=None hedged=0
- 1m: 33.62 raw=N/A excess=+30.28%
- 原文: `The difference is that $NBIS is doing 4-6B forward revenue in 2026 off ~70% gross margins.

The market cap is 28B and forward growth fundamentals are there to support valuation.

Quantum are pre-revenue with a lot of their income coming from interest instead of revenue. Companies like $RGTI and $QBTS that have no meaningful forward revenue, while being valued at tens of billions is a bubble.`

**[7]** pred=`4d7119f9-6e4e-40b4-a23c-281d829a8fde` pub=2025-11-19 entry=2025-11-20 px=$23.97
- LLM: dir=short conv=2 hz=6m qc=None hedged=0
- 1m: 23.97 raw=N/A excess=-21.49%
- 原文: `The Great Reset, November 19th ratings:

Strong Buy

· $NBIS
· $CIFR
· $WULF
· $RDDT
· $SNAP
· $ALAB
· $META
· $AMZN
· $GOOGL
· $IBIT
· $SOL
· $TSM
· $RKLB
· $TSSI
· $SMCI
· $GLXY
· $SG

Buy

· $IREN
· $KRUS
· $CRCL
· $LTC
· $MRVL
· $KRKNF
· $OSS
· $CORZ
· $WLAC
· $WYFI
· $AMD
· $TE
· $CRDO
· $FLNC
· $HIMS
· $BULL
· $ETOR
· $FISV
· $FLY
· $MU

Hold

· $COIN
· $HOOD
· $IBKR
· $NVDA
· $PLTR
· $TSLA
· CRWV
· $APLD
· ORCL

Avoid

· RGTI
· $IONQ
· SLNH
· $QBTS
· OKLO
· $WMT
· BMNR
· $SBET
· CRWV
_

E...`

**[8]** pred=`917265d0-ec34-4a39-9381-00bf9c466e06` pub=2026-01-02 entry=2026-01-05 px=$28.66
- LLM: dir=short conv=2 hz=6m qc=None hedged=0
- 1m: 28.655 raw=N/A excess=+29.82%
- 原文: `Welcome to 2026. Jan 1st ratings:

Strong Buy:
$TTD
$SMCI
$AIRO
$INTC
$HIMS
$AXTI
$TSM
$NBIS
$CIFR
Samsung Electronics (KRX: 005930)
$HUT
$IREN
$WULF
$GLXY
$TSSI
$META
$ETOR
$CRCL

Buy:
$KRKNF
$ONDS
$GEMI
$NVDA
$MU
$AMKR
SK Hynix
$SNAP
$RDDT
$AAOI
$COHR
$FISV
$FLY
$DJT
$LITE
$AMZN
$MRVL
$AVGO
$OSS
$BULL
$ORCL
$CRDO
$ALAB

Avoid:
$RGTI
$QBTS
$RGTI
$BMNR
$ETH
$PLTR
$WMT

_

TLDR thoughts:

TTD - Complete valuation reset dropping 67% YTD, compounded by EOY tax sell-off. Great recovery play going in...`

**[9]** pred=`2fb2b1e7-99d4-4f0a-b42b-7c1791f8e713` pub=2026-02-02 entry=2026-02-03 px=$21.54
- LLM: dir=short conv=3 hz=event_driven qc=None hedged=0
- 1m: 21.54 raw=N/A excess=+12.58%
- 原文: `Markets are seeing liquidation cascades.

Silver's crash is now extending into other markets like Crypto and US/Foreign stocks.

Here's what's happening:

And here's what to expect from:

- $BMNR (Crypto)
- $RKLB (High-Beta)  
- $SNDK (AI) 
- to Samsung (Foreign). 

The "Warsh" Fed Chair nomination was the initial trigger that caused the selloff as markets viewed him as a "Hawk" -> Quantitative Tightening. 

However, this is a mistake as the fed chair is likely aligned with Trump's policies, and...`


### QLCM (n_long=0  n_short=1)


**[1]** pred=`9318c500-cb14-43c6-86fd-a2dab7ceb991` pub=2026-03-24 entry=None px=NULL
- LLM: dir=short conv=3 hz=long_term qc=None hedged=0
- 1m: None raw=N/A excess=N/A
- 原文: `I'm actually personally pretty bearish on both $ARM and $QLCM.

Probably not the best person to ask on $ARM since I did help out RISC-V quite a bit so I'm a little biased.  

As for Qualcomm... Mediatek is probably better long, especially with their high growth ASIC arm working with $GOOGL.`


### QUBT (n_long=0  n_short=2)


**[1]** pred=`993704dd-70a1-4641-b4fe-2acdd9821dbd` pub=2025-10-11 entry=2025-10-13 px=$19.94
- LLM: dir=short conv=2 hz=6m qc=None hedged=0
- 1m: 19.94 raw=N/A excess=+40.12%
- 原文: `Based Friday Market Close (-3.6% SPY day), Thoughts and Explanations

Strong Buy
$IBIT
$LTC
$WLAC
$NBIS
$MP
$TSM
(For Next Year)
$ETOR
$DKNG
$SNAP

Buy
$UPWK
$CRDO
$ALAB
$AMZN
$META
$UNH
$SG
$TGT
$BULL
$FLY
$CIFR
$WULF
$IREN
$GLXY
$SMCI
$DELL
$MRVL

Hold
$RKLB
$HOOD
$RBRK
$MU
$HOOD
$GRAB
$MARA
$RIOT
$NVO
$RR
$ELOSE
$FLNC
$SEI
$PLTR

Sell
$CRCL
$ETH
$BMNR
$PL
$BKSY

Strong Sell
$RGTI
$OKLO
$IONQ
$QBTS
$QUBT

_

Explanations:

IBIT - Dumped to $104k, Bitcoin demand has been institutional, tariff f...`

**[2]** pred=`b4acd3cb-8723-4814-bf6b-1c8ffb8da298` pub=2025-10-12 entry=2025-10-13 px=$19.94
- LLM: dir=short conv=2 hz=6m qc=None hedged=0
- 1m: 19.94 raw=N/A excess=+40.12%
- 原文: `And there’s the de-escalation

Reuters: “Taiwan sees no significant impact on chip sector”

Trump: “Don’t worry about China, it will all be fine… President Xi just had a bad moment.”

Biggest crypto liquidation to date 

Stocks with little impact down 7%

Dip buying opportunity https://t.co/2sUEV7Dg8s`


### RDDT (n_long=60  n_short=1)


**[1]** pred=`88118c95-a5c3-4e6e-938e-f4775798adc2` pub=2025-09-29 entry=2025-09-30 px=$240.34
- LLM: dir=short conv=2 hz=6m qc=None hedged=0
- 1m: 240.335 raw=N/A excess=+12.30%
- 原文: `Monday Market Close Thoughts:

Extremely Strong Buy
$NBIS
$ETOR
$LTC
$VIRT

Buy
$AMZN
$SMCI
$TGT
$CRM
$TSM
$CRDO
$SG
$CIFR
$LULU
$SLNH
$ORCL
$MSTR
$RIOT
$MARA

Hold
$IREN
$HIMS
$RKLB
$PYPL
$MRVL
$IBIT
$UPWK
$GRAB
$ALAB
$ASTS
$SOFI
$NVDA
$NVO

Sell
$HOOD
$TSLA
$RDDT
$CRCL
$PLTR
$BMNR

Strong Sell
$OKLO
$QBTS
$IONQ

_

Feel free to disagree but these are just my thoughts

Strong Buy Explanations

- Bought ~$70K of Virtu calls, 28% IV and just 6.6 forward p/e is undervalued.

- Always DCA NBIS on t...`


### RGTI (n_long=1  n_short=9)


**[1]** pred=`e6c33bf4-1127-417d-a21b-676699957e5f` pub=2025-10-03 entry=2025-10-06 px=$38.80
- LLM: dir=short conv=3 hz=6m qc=None hedged=0
- 1m: 38.805 raw=N/A excess=+9.34%
- 原文: `@commonsenseplay $RGTI is an amazing short. 

But you do realize that the reason the IONQ/RGTI marketcap is $13B+ is largely driven by short interest.`

**[2]** pred=`b01d49d5-ad8a-4165-b25e-f79892d0fd56` pub=2025-10-04 entry=2025-10-06 px=$38.80
- LLM: dir=short conv=2 hz=6m qc=None hedged=0
- 1m: 38.805 raw=N/A excess=+9.34%
- 原文: `Friday Market Close, Personal Thoughts and Explanations:

Strong Buy
$RDDT
$SNAP
$AMZN
$ETOR
$NBIS
$LTC

Buy
$UPWK
$MSTR
$ORCL
$TGT
$CIFR
$VIRT
$CRDO
$WULF
$SOFI
$META
$AVGO
$MRVL
$SMCI
$DELL

Hold
$RKLB
$TSM
$IREN
$RR
$ALAB
$HOOD
$FLNC
$EOSE
$BE
$RIOT
$MARA
$GRAB
$ASTS
$NVO
$NVDA

Sell
$TSLA
$CRCL
$PLTR
$BMNR

Strong Sell
$RGTI
$OKLO
$QBTS
$IONQ

_

(again, not great DD, just writing random thoughts about the process). 

Strong Buys

Reddit - Dropped 29% off immaterial news that ChatGPT wasn't ...`

**[3]** pred=`9298fe62-267f-462c-932f-17de31be660b` pub=2025-10-11 entry=2025-10-13 px=$46.46
- LLM: dir=short conv=2 hz=6m qc=None hedged=0
- 1m: 46.46 raw=N/A excess=+32.41%
- 原文: `Based Friday Market Close (-3.6% SPY day), Thoughts and Explanations

Strong Buy
$IBIT
$LTC
$WLAC
$NBIS
$MP
$TSM
(For Next Year)
$ETOR
$DKNG
$SNAP

Buy
$UPWK
$CRDO
$ALAB
$AMZN
$META
$UNH
$SG
$TGT
$BULL
$FLY
$CIFR
$WULF
$IREN
$GLXY
$SMCI
$DELL
$MRVL

Hold
$RKLB
$HOOD
$RBRK
$MU
$HOOD
$GRAB
$MARA
$RIOT
$NVO
$RR
$ELOSE
$FLNC
$SEI
$PLTR

Sell
$CRCL
$ETH
$BMNR
$PL
$BKSY

Strong Sell
$RGTI
$OKLO
$IONQ
$QBTS
$QUBT

_

Explanations:

IBIT - Dumped to $104k, Bitcoin demand has been institutional, tariff f...`

**[4]** pred=`08a89ea5-4243-4ea6-b298-2d1b3df12333` pub=2025-10-12 entry=2025-10-13 px=$46.46
- LLM: dir=short conv=2 hz=6m qc=None hedged=0
- 1m: 46.46 raw=N/A excess=+32.41%
- 原文: `And there’s the de-escalation

Reuters: “Taiwan sees no significant impact on chip sector”

Trump: “Don’t worry about China, it will all be fine… President Xi just had a bad moment.”

Biggest crypto liquidation to date 

Stocks with little impact down 7%

Dip buying opportunity https://t.co/2sUEV7Dg8s`

**[5]** pred=`df51c451-a33b-47b6-8ee4-6e23fe8f4dbc` pub=2025-10-19 entry=2025-10-20 px=$47.48
- LLM: dir=short conv=2 hz=6m qc=None hedged=0
- 1m: 47.48 raw=N/A excess=+45.85%
- 原文: `October 20th, Important Rate Cut Trading Week.

Personal thoughts and explanations: 

🛝 = Swing Trade

🐈 = Catalyst Trade

🎇 = 2026 Trade, Tax Harvested

Fire Sale
🔥 $NBIS 

Strong Buy
$TSM
$AMKR
$WLAC
$AMZN
$LTC 🐈
$RDDT
$HIMS 🛝
$IBIT
$ALAB
$CRDO
$SMCI
$FLY 🎇
$SNAP 🎇
$ETOR 🎇
$LULU 🎇

Buy
$AMD
$HOOD 
$RBRK
$UNH
$TGT 🐈
$IREN 🐈
$WYFI
$WULF
$CIFR
$SLNH
$BITF
$GLXY
$FLNC
$MU

(Skipping Hold, since any other stock I've mentioned in the past, it probably just hold it since nothing's changed).

Sell
$ET...`

**[6]** pred=`eb25fdb5-adaf-49a7-8dfa-8988cabe7115` pub=2025-10-20 entry=2025-10-21 px=$42.52
- LLM: dir=short conv=3 hz=long_term qc=None hedged=0
- 1m: 42.52 raw=N/A excess=+40.12%
- 原文: `The difference is that $NBIS is doing 4-6B forward revenue in 2026 off ~70% gross margins.

The market cap is 28B and forward growth fundamentals are there to support valuation.

Quantum are pre-revenue with a lot of their income coming from interest instead of revenue. Companies like $RGTI and $QBTS that have no meaningful forward revenue, while being valued at tens of billions is a bubble.`

**[7]** pred=`16e355e8-1849-4dd3-9d96-1c1b6ab5dd3e` pub=2025-11-19 entry=2025-11-20 px=$26.32
- LLM: dir=short conv=2 hz=6m qc=None hedged=0
- 1m: 26.32 raw=N/A excess=+4.60%
- 原文: `The Great Reset, November 19th ratings:

Strong Buy

· $NBIS
· $CIFR
· $WULF
· $RDDT
· $SNAP
· $ALAB
· $META
· $AMZN
· $GOOGL
· $IBIT
· $SOL
· $TSM
· $RKLB
· $TSSI
· $SMCI
· $GLXY
· $SG

Buy

· $IREN
· $KRUS
· $CRCL
· $LTC
· $MRVL
· $KRKNF
· $OSS
· $CORZ
· $WLAC
· $WYFI
· $AMD
· $TE
· $CRDO
· $FLNC
· $HIMS
· $BULL
· $ETOR
· $FISV
· $FLY
· $MU

Hold

· $COIN
· $HOOD
· $IBKR
· $NVDA
· $PLTR
· $TSLA
· CRWV
· $APLD
· ORCL

Avoid

· RGTI
· $IONQ
· SLNH
· $QBTS
· OKLO
· $WMT
· BMNR
· $SBET
· CRWV
_

E...`

**[8]** pred=`bde4f261-83fc-4b06-a5e1-63099abbd07f` pub=2026-01-02 entry=2026-01-05 px=$23.69
- LLM: dir=short conv=2 hz=6m qc=None hedged=0
- 1m: 23.69 raw=N/A excess=+27.44%
- 原文: `Welcome to 2026. Jan 1st ratings:

Strong Buy:
$TTD
$SMCI
$AIRO
$INTC
$HIMS
$AXTI
$TSM
$NBIS
$CIFR
Samsung Electronics (KRX: 005930)
$HUT
$IREN
$WULF
$GLXY
$TSSI
$META
$ETOR
$CRCL

Buy:
$KRKNF
$ONDS
$GEMI
$NVDA
$MU
$AMKR
SK Hynix
$SNAP
$RDDT
$AAOI
$COHR
$FISV
$FLY
$DJT
$LITE
$AMZN
$MRVL
$AVGO
$OSS
$BULL
$ORCL
$CRDO
$ALAB

Avoid:
$RGTI
$QBTS
$RGTI
$BMNR
$ETH
$PLTR
$WMT

_

TLDR thoughts:

TTD - Complete valuation reset dropping 67% YTD, compounded by EOY tax sell-off. Great recovery play going in...`

**[9]** pred=`4cf601e4-e68d-4cb0-85ea-95b5a43951e4` pub=2026-02-02 entry=2026-02-03 px=$18.24
- LLM: dir=short conv=3 hz=event_driven qc=None hedged=0
- 1m: 18.24 raw=N/A excess=+6.96%
- 原文: `Markets are seeing liquidation cascades.

Silver's crash is now extending into other markets like Crypto and US/Foreign stocks.

Here's what's happening:

And here's what to expect from:

- $BMNR (Crypto)
- $RKLB (High-Beta)  
- $SNDK (AI) 
- to Samsung (Foreign). 

The "Warsh" Fed Chair nomination was the initial trigger that caused the selloff as markets viewed him as a "Hawk" -> Quantitative Tightening. 

However, this is a mistake as the fed chair is likely aligned with Trump's policies, and...`


### RKLB (n_long=61  n_short=2)


**[1]** pred=`98668a95-3ee8-4568-8593-00d326a3fc05` pub=2025-12-20 entry=2025-12-22 px=$72.94
- LLM: dir=short conv=3 hz=6m qc=None hedged=0
- 1m: 72.94 raw=N/A excess=-21.88%
- 原文: `So I’d say $RKLB is definitely the most overvalued right now. 

$LITE is edging toward the overbought territory but it definitely warrants a re-rating given how critical it is in TPUv7, Trainium, and Blackwell chips.

$NBIS and $CRCL are most undervalued out of the bunch, then goes $ALAB.`

**[2]** pred=`17caaa8e-daab-4eef-85ab-605cb9ca6a96` pub=2026-02-02 entry=2026-02-03 px=$78.60
- LLM: dir=short conv=3 hz=event_driven qc=None hedged=0
- 1m: 78.6 raw=N/A excess=+10.94%
- 原文: `Markets are seeing liquidation cascades.

Silver's crash is now extending into other markets like Crypto and US/Foreign stocks.

Here's what's happening:

And here's what to expect from:

- $BMNR (Crypto)
- $RKLB (High-Beta)  
- $SNDK (AI) 
- to Samsung (Foreign). 

The "Warsh" Fed Chair nomination was the initial trigger that caused the selloff as markets viewed him as a "Hawk" -> Quantitative Tightening. 

However, this is a mistake as the fed chair is likely aligned with Trump's policies, and...`


### SBET (n_long=0  n_short=1)


**[1]** pred=`e621e3b3-c83c-421f-aff7-0fa2ec9b3da6` pub=2025-11-19 entry=2025-11-20 px=$10.16
- LLM: dir=short conv=2 hz=6m qc=None hedged=0
- 1m: 10.165 raw=N/A excess=+9.10%
- 原文: `The Great Reset, November 19th ratings:

Strong Buy

· $NBIS
· $CIFR
· $WULF
· $RDDT
· $SNAP
· $ALAB
· $META
· $AMZN
· $GOOGL
· $IBIT
· $SOL
· $TSM
· $RKLB
· $TSSI
· $SMCI
· $GLXY
· $SG

Buy

· $IREN
· $KRUS
· $CRCL
· $LTC
· $MRVL
· $KRKNF
· $OSS
· $CORZ
· $WLAC
· $WYFI
· $AMD
· $TE
· $CRDO
· $FLNC
· $HIMS
· $BULL
· $ETOR
· $FISV
· $FLY
· $MU

Hold

· $COIN
· $HOOD
· $IBKR
· $NVDA
· $PLTR
· $TSLA
· CRWV
· $APLD
· ORCL

Avoid

· RGTI
· $IONQ
· SLNH
· $QBTS
· OKLO
· $WMT
· BMNR
· $SBET
· CRWV
_

E...`


### SLNH (n_long=8  n_short=3)


**[1]** pred=`557ca18b-b06f-4e2c-987c-ceae4acfef2b` pub=2025-11-19 entry=2025-11-20 px=$1.92
- LLM: dir=short conv=2 hz=6m qc=None hedged=0
- 1m: 1.92 raw=N/A excess=+19.79%
- 原文: `The Great Reset, November 19th ratings:

Strong Buy

· $NBIS
· $CIFR
· $WULF
· $RDDT
· $SNAP
· $ALAB
· $META
· $AMZN
· $GOOGL
· $IBIT
· $SOL
· $TSM
· $RKLB
· $TSSI
· $SMCI
· $GLXY
· $SG

Buy

· $IREN
· $KRUS
· $CRCL
· $LTC
· $MRVL
· $KRKNF
· $OSS
· $CORZ
· $WLAC
· $WYFI
· $AMD
· $TE
· $CRDO
· $FLNC
· $HIMS
· $BULL
· $ETOR
· $FISV
· $FLY
· $MU

Hold

· $COIN
· $HOOD
· $IBKR
· $NVDA
· $PLTR
· $TSLA
· CRWV
· $APLD
· ORCL

Avoid

· RGTI
· $IONQ
· SLNH
· $QBTS
· OKLO
· $WMT
· BMNR
· $SBET
· CRWV
_

E...`

**[2]** pred=`377ec56d-182e-477a-a359-0671e704aa4b` pub=2026-04-30 entry=2026-05-01 px=$1.56
- LLM: dir=short conv=4 hz=event_driven qc=None hedged=0
- 1m: 1.56 raw=N/A excess=-5.77%
- 原文: `$SLNH is a shtco like $BKKT, $ASST, and $IREN.

That is actively diluting everyone with a $500M ATM.

Not sure why anyone even listens to a guy who has consistently crashed retail portfolios over and over.

I’m going to watch them raise $500M off retail bagholders that get diluted to $0.

Then say “we have $500m on our balance sheets, MC should be higher” and award themselves SBC off the ATM. 

They’re all absolutely terrible longs.`

**[3]** pred=`048fa9ad-50db-4d76-af4c-762918a4d704` pub=2026-05-03 entry=2026-05-04 px=$1.54
- LLM: dir=short conv=4 hz=long_term qc=None hedged=0
- 1m: 1.545 raw=N/A excess=+0.32%
- 原文: `@SingularityRes $SLNH is utter garbage for equity appreciation. 

I'm just in disbelief people think they're going to have it appreciate in value when they're getting actively diluted $1 BILLION off a $219m MC.`


### SNDK (n_long=28  n_short=1)


**[1]** pred=`052a2a51-f42c-4ccb-a9ed-a7942ad7ceb5` pub=2026-05-08 entry=2026-05-11 px=$1586.25
- LLM: dir=short conv=3 hz=long_term qc=None hedged=0
- 1m: 1586.25 raw=N/A excess=-3.59%
- 原文: `Nobody can convince me $SNDK isn’t a meme stock at this point.

But as I’ve said, bottlenecks with multi-year visibility like $HPS.A or $LITE tend to perform better. https://t.co/WkjoG1jIYu`


### TSLA (n_long=6  n_short=2)


**[1]** pred=`f697dacf-a432-4f07-b065-6aa2d807780b` pub=2025-09-29 entry=2025-09-30 px=$441.52
- LLM: dir=short conv=2 hz=6m qc=None hedged=0
- 1m: 441.52 raw=N/A excess=-4.53%
- 原文: `Monday Market Close Thoughts:

Extremely Strong Buy
$NBIS
$ETOR
$LTC
$VIRT

Buy
$AMZN
$SMCI
$TGT
$CRM
$TSM
$CRDO
$SG
$CIFR
$LULU
$SLNH
$ORCL
$MSTR
$RIOT
$MARA

Hold
$IREN
$HIMS
$RKLB
$PYPL
$MRVL
$IBIT
$UPWK
$GRAB
$ALAB
$ASTS
$SOFI
$NVDA
$NVO

Sell
$HOOD
$TSLA
$RDDT
$CRCL
$PLTR
$BMNR

Strong Sell
$OKLO
$QBTS
$IONQ

_

Feel free to disagree but these are just my thoughts

Strong Buy Explanations

- Bought ~$70K of Virtu calls, 28% IV and just 6.6 forward p/e is undervalued.

- Always DCA NBIS on t...`

**[2]** pred=`9c4e9d56-a040-41be-825c-3727ff9cff9d` pub=2025-10-04 entry=2025-10-06 px=$440.75
- LLM: dir=short conv=2 hz=6m qc=None hedged=0
- 1m: 440.75 raw=N/A excess=-0.80%
- 原文: `Friday Market Close, Personal Thoughts and Explanations:

Strong Buy
$RDDT
$SNAP
$AMZN
$ETOR
$NBIS
$LTC

Buy
$UPWK
$MSTR
$ORCL
$TGT
$CIFR
$VIRT
$CRDO
$WULF
$SOFI
$META
$AVGO
$MRVL
$SMCI
$DELL

Hold
$RKLB
$TSM
$IREN
$RR
$ALAB
$HOOD
$FLNC
$EOSE
$BE
$RIOT
$MARA
$GRAB
$ASTS
$NVO
$NVDA

Sell
$TSLA
$CRCL
$PLTR
$BMNR

Strong Sell
$RGTI
$OKLO
$QBTS
$IONQ

_

(again, not great DD, just writing random thoughts about the process). 

Strong Buys

Reddit - Dropped 29% off immaterial news that ChatGPT wasn't ...`


### UAVS (n_long=2  n_short=1)


**[1]** pred=`44764230-92e5-4ecb-aebc-35c5c1292e62` pub=2026-01-14 entry=2026-01-15 px=$1.66
- LLM: dir=short conv=4 hz=event_driven qc=None hedged=0
- 1m: 1.66 raw=N/A excess=+40.11%
- 原文: `Warning to retail investors: 

Stay away from $UAVS until the result of the vote on the 22nd. 

I was researching drone stock recs, and found SEC filings where the shady board voted for a wealth transfer from retail to arbitrage.

It's a drone company that's been getting retail attention because it's used by:

US Army USACE, NATO (KFOR), and other armed forces with a lot of news published recently.

I was super excited about this potential long for a $75M company, since they pivoted their agricu...`


### ULBI (n_long=0  n_short=1)


**[1]** pred=`bc170d1a-13b3-43c1-995c-7e59cd5827a7` pub=2026-01-12 entry=2026-01-13 px=$6.30
- LLM: dir=short conv=3 hz=event_driven qc=None hedged=0
- 1m: 6.3 raw=N/A excess=+0.63%
- 原文: `@_gautam94 @KawzInvests Just a heads up $ULBI has -50.3M in debt, -84.8M total accrued expenses, with $9.3M left. 

They're also commodity status as 22% gross margin. 

That's the reason for low P/S number, there is likely heavy dilution ahead. I'd likely stay away`


### V (n_long=0  n_short=2)


**[1]** pred=`abb38ced-606a-4626-af32-63ad7a3916bb` pub=2026-01-01 entry=2026-01-02 px=$349.87
- LLM: dir=short conv=2 hz=long_term qc=None hedged=0
- 1m: 349.87 raw=N/A excess=+5.99%
- 原文: `2026 Newsletter.

Thematic Investments: Evolution, Disruption, and Bottlenecks

1. Soft Robotics - Evolution to $TSLA, $ONDS, Boston Dynamics. 

2. SiPh - InP Bottleneck | $AXTI, $LITE, $GOOGL

3. Glass Substrates - Bottleneck | $NVDA, $INTC, $TSM

4. Money Movement - Disruption to $V, Stripe, $BOA

5. AI Cloud Layers - Bottleneck | $NBIS, $IREN, $HUT. 

6. LLM Cybersecuirty - Evolution to $CRWD, $CSCO, $MSFT 

7. LEO Space Infrastructure | Evolution to $RKLB,  SpaceX, $ASTS

8. Consumer Agentic...`

**[2]** pred=`bb567dd5-5191-4aee-9700-187ea554900b` pub=2026-03-19 entry=2026-03-20 px=$299.85
- LLM: dir=short conv=3 hz=long_term qc=None hedged=0
- 1m: 299.85 raw=N/A excess=-3.36%
- 原文: `I’m surprised markets aren’t pricing in long term disruption of card networks + interchange like $V and $MA.

By $CRCL and $COIN.

From Global Markets Head at Circle:

"Over the past nine months, AI agents completed 140 million payments with a total transaction volume of 43 million US dollars. 

Among these, 98.6% were settled in USDC, with an average transaction amount of only 0.31 US dollars."

Card networks and % fee payment processors like $PYPL are likely going to be cooked?`


### VCX (n_long=0  n_short=2)


**[1]** pred=`82d52a3b-aba0-4702-86f3-3b5d468d9953` pub=2026-03-25 entry=2026-03-26 px=$445.00
- LLM: dir=short conv=2 hz=event_driven qc=None hedged=0
- 1m: 445.0 raw=N/A excess=+80.90%
- 原文: `@erikles_white $VCX probably a great short when hedging becomes available.`

**[2]** pred=`0c4c7efb-6498-4a6f-821c-aa986594f311` pub=2026-03-28 entry=2026-03-30 px=$156.00
- LLM: dir=short conv=3 hz=event_driven qc=None hedged=0
- 1m: 156.0 raw=N/A excess=+45.51%
- 原文: `With $IREN, you have $6B in newly minted selling pressure. This ATM is structural overhang in any rally.
 
If the marketcap is $11 Billion and they're selling up to $6,000,000,000 worth of new shares against you in the open market. 

I would not go long until the ATM is finished and existing holders get diluted. 

Same with $VCX, if you're trading at 2000% NAV of SpaceX (valued at $34 Trillion), eventually the math will work against you.`


### VGK (n_long=0  n_short=1)


**[1]** pred=`dcfefeef-922f-4202-9467-97f1f8465545` pub=2026-02-01 entry=2026-02-02 px=$87.81
- LLM: dir=short conv=3 hz=event_driven qc=None hedged=0
- 1m: 87.81 raw=N/A excess=+1.39%
- 原文: `Kevin Warsh is the next Federal Reserve Chair.

Markets may confuse him as a "Hawk". 

His actual stance in 2026 is nuanced.

Here's his policies and how they affect the markets: 

1. AI/Semis ( $NVDA, $MU): Extremely Bullish
2. Metals (Silver, Gold): Extreme Bearish
3. Crypto ( $BTC, $CRCL ): Paradoxically bullish
4. Banking & Financials ( $JPM, $BOA ): Bullish
5. Housing & Real Estate: Mixed/Uncertain
6. Renewable Energy: Bearish
7. Small-Caps ( $RUT ) : Bullish
8. Foreign Stocks (Japan, Korea...`


### WMT (n_long=0  n_short=3)


**[1]** pred=`32f48fd1-4588-42d6-b9cb-b87438d8ce93` pub=2025-11-19 entry=2025-11-20 px=$103.94
- LLM: dir=short conv=2 hz=6m qc=None hedged=0
- 1m: 103.94 raw=N/A excess=-6.70%
- 原文: `The Great Reset, November 19th ratings:

Strong Buy

· $NBIS
· $CIFR
· $WULF
· $RDDT
· $SNAP
· $ALAB
· $META
· $AMZN
· $GOOGL
· $IBIT
· $SOL
· $TSM
· $RKLB
· $TSSI
· $SMCI
· $GLXY
· $SG

Buy

· $IREN
· $KRUS
· $CRCL
· $LTC
· $MRVL
· $KRKNF
· $OSS
· $CORZ
· $WLAC
· $WYFI
· $AMD
· $TE
· $CRDO
· $FLNC
· $HIMS
· $BULL
· $ETOR
· $FISV
· $FLY
· $MU

Hold

· $COIN
· $HOOD
· $IBKR
· $NVDA
· $PLTR
· $TSLA
· CRWV
· $APLD
· ORCL

Avoid

· RGTI
· $IONQ
· SLNH
· $QBTS
· OKLO
· $WMT
· BMNR
· $SBET
· CRWV
_

E...`

**[2]** pred=`a8777bbf-125a-4473-89b2-47643c794c84` pub=2026-01-02 entry=2026-01-05 px=$112.82
- LLM: dir=short conv=2 hz=6m qc=None hedged=0
- 1m: 112.82 raw=N/A excess=-13.46%
- 原文: `Welcome to 2026. Jan 1st ratings:

Strong Buy:
$TTD
$SMCI
$AIRO
$INTC
$HIMS
$AXTI
$TSM
$NBIS
$CIFR
Samsung Electronics (KRX: 005930)
$HUT
$IREN
$WULF
$GLXY
$TSSI
$META
$ETOR
$CRCL

Buy:
$KRKNF
$ONDS
$GEMI
$NVDA
$MU
$AMKR
SK Hynix
$SNAP
$RDDT
$AAOI
$COHR
$FISV
$FLY
$DJT
$LITE
$AMZN
$MRVL
$AVGO
$OSS
$BULL
$ORCL
$CRDO
$ALAB

Avoid:
$RGTI
$QBTS
$RGTI
$BMNR
$ETH
$PLTR
$WMT

_

TLDR thoughts:

TTD - Complete valuation reset dropping 67% YTD, compounded by EOY tax sell-off. Great recovery play going in...`

**[3]** pred=`1c35a1c2-9184-4754-a44a-17b51e75cf66` pub=2026-01-13 entry=2026-01-14 px=$120.19
- LLM: dir=short conv=3 hz=long_term qc=None hedged=0
- 1m: 120.19 raw=N/A excess=-11.40%
- 原文: `They're growing ads -> FCF would pay for any capex. FCF was $10B+ Last quarter yet everyone was scared for their lives on spend. 

$META is growing 26% Y/Y and their forward P/E is 18.9X.

$WMT is growing in line with inflation with a forward P/E of 40x+.

There's just some mispricing in the market right now`
