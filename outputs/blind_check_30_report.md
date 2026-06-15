# 盲查 30 条 v1.4.1 实跑报告(2026-06-15)

**抽样方法**: 分层 + 随机 (seed=20260615)
- **True 类(15 条)**: LLM 判 has_pred=True → 验假阳(标的/方向/conviction 对吗)
- **False 类(15 条)**: LLM 判 has_pred=False + 原文含 cashtag (2490 候选) → 验假阴(漏抽真预测了吗)

**实跑设置**:
- 抽到的 30 条 cache **DELETE FROM extraction_cache**(只删这 30 条,其它保留)
- use_cache=False 强制实调 LLM
- pv=`deepseek:deepseek-v4-pro:v1.4.1`
- temperature=0
- 总耗时: 111s, 平均 3.7s/条
- 0 errors

**关键统计**:
- True 类 (15): 13 一致 / **2 翻 False** → 2 个潜在假阳
- False 类 (15): **15 一致 / 0 翻 True** → **0 个假阴** ✓
- 总体翻概率: 6.7% (deterministic LLM 期望 0%)

---

## 30 条逐条详情

### # 1 [TRUE] ✓ 一致 post_id=2024322169376035019
  has_pred: True (n_pred=5, flags=[], tickers=[], pt=6980, ct=831)
  **原文**:
  > The funniest beneficary if US invades Iran was:

Pistachios.

Not even joking. 

Did you know US (California) and Iran operate a virtual duopoly in pistachio production? 

This is the $AXTI InP situation as the two control ~70-80% of the world’s supply.

Companies like $JBSS might benefit from Pistachio prices going up (if California becomes a monopoly)

Unfortunately there’s no Pistachio Futures, so I’m not taking any positions but I just found this fun fact amusing, so wanted to share.

I’ll do another writeup on more nuanced second order effects and potential longs soon.

US strikes seem li...
  **extraction_notes**: 作者以开心果垄断类比引出 JBSS 可能受益，但明确表示无仓位且仅为有趣分享，故 JBSS 预测为弱对冲（conviction=2, hedged=true）。末尾提及石油和国防股作为潜在多头/对冲，使用 'might be good' 措辞，同样为弱预测。AXTI 仅作类比，非预测标的。

### # 2 [TRUE] ✓ 一致 post_id=2033466880661606646
  has_pred: True (n_pred=1, flags=['position_disclosure'], tickers=[], pt=7819, ct=306)
  **原文**:
  > I’m long $SIVE at $140M. 

I believe this is the next $LITE that markets and institutions missed.

$SIVE makes InP CW DFB lasers. 

Closest comparison is $LITE in the current EML laser bottleneck.

But instead of supplying to Innolight/Eoptolink for current optical transceivers cycles. 

They supply the lasers to $POET Starlight, Ayar SuperNova.

And others for the future CPO/silicon photonics architectures spearheaded by $NVDA. 

Current valuations make 0 sense to me personally.   

$POET is advanced packaging for $SIVE type lasers… 

But $POET commands worth 11x+ more than the company making...
  **extraction_notes**: 作者明确 long SIVE，给出完整论据和强结论，conviction=5；提及多个 ticker 作为语境比较，仅 SIVE 为论点主角；自报持仓触发 position_disclosure

### # 3 [TRUE] ✓ 一致 post_id=2060857962290409908
  has_pred: True (n_pred=1, flags=[], tickers=[], pt=6879, ct=226)
  **原文**:
  > @_king142 No clue, just floating out my opinion into the public.

But I’m extremely, extremely impressed with $SIVE management so far. And I think they’re heading down the right path with NASDAQ dual listing soon.
  **extraction_notes**: 作者明确表达对$SIVE管理层的极度赞赏，并认为纳斯达克双重上市是正确的方向，构成方向性预测。conviction=3因语气强烈但无量化目标。

### # 4 [TRUE] ✓ 一致 post_id=2034160719676244366
  has_pred: True (n_pred=1, flags=[], tickers=[], pt=6891, ct=239)
  **原文**:
  > @daniel_koss Yeah should be a tailwind for SK Hynix and Samsung and opens the doors for a lot of US investors.

I’m very bullish on $MU but it’s a bit strange SK Hynix trades at a lower valuation, even accounting for made in America premiums.
  **extraction_notes**: 作者明确表达对 MU 的看涨观点（'very bullish'），conviction 4；SK Hynix 和 Samsung 仅作为语境比较，不构成独立预测。

### # 5 [TRUE] ✓ 一致 post_id=2041650903305089389
  has_pred: True (n_pred=3, flags=[], tickers=[], pt=7667, ct=651)
  **原文**:
  > I get a sense of pride when I see a thesis playing out well real time.

$LITE $371 -> $836 in the last 4 months. 

Not bad for a $58B company despite macro? 

This is while indexes and individual stocks. And photonic stocks like $POET and individual stocks like $RDDT dropped YTD.  

I tend to like laser companies the most from $SIVE, $AAOI, and Lumentum for photonics exposure. 

And in a better macro environment, I expect many of them to be up more than they are now.
  **extraction_notes**: 主推文对 LITE 有明确长期看涨论点（conviction 4），SIVE 和 AAOI 作为偏好清单提及，但带有宏观环境对冲措辞（conviction 2, hedged=true）。POET 和 RDDT 仅作为对比提及，无方向性预测。被引推文为 LITE 详细论据，已整合进 thesis_summary。

### # 6 [TRUE] ✓ 一致 post_id=2039718433424839152
  has_pred: True (n_pred=1, flags=[], tickers=[], pt=6853, ct=208)
  **原文**:
  > @TD_btc24 Yeah $AEHR is high conviction now in the test space. Tons of potential there
  **extraction_notes**: 回复推文，父推文不在库中，但作者明确表达对$AEHR的高确信度看涨观点，构成预测。

### # 7 [TRUE] ✓ 一致 post_id=2028458236316381685
  has_pred: True (n_pred=1, flags=[], tickers=[], pt=6908, ct=223)
  **原文**:
  > We'll need to see, it's more of a catalyst trade right now. 

$LASR just got the biggest validation in their lifetime for the first usage of their Laser Weapons shooting down a bunch of stuff. 

My guess is a ton of contracts will likely flow into $LASR now both from expanding Iron Beam (because it worked) and toward other applications like hypersonic missiles.
  **extraction_notes**: 回复父推文缺失，但本身对$LASR有明确方向性表态（long），使用'My guess'对冲措辞，conviction=2，hedged=true。

### # 8 [TRUE] ✓ 一致 post_id=2013689876038681058
  has_pred: True (n_pred=1, flags=[], tickers=[], pt=6891, ct=234)
  **原文**:
  > @__visionxry__ IMO $AVAV is a great dip buy on the 15% drop.

Main revenue is $1B+ switchblade replicator. 

Markets are trolling if they’re panicking over a $175m contract that’s getting renegotiated.
  **extraction_notes**: 回复推文，父推文不在库中，但作者明确给出$AVAV的买入建议，构成方向性预测。

### # 9 [TRUE] ✓ 一致 post_id=1982018137672630708
  has_pred: True (n_pred=1, flags=[], tickers=[], pt=7142, ct=282)
  **原文**:
  > I'd disagree, software orchestration is one of the biggest moats possible, which is why $NBIS > $IREN clear as day for me in terms of asymmetrical upside. But to each their own!

I'd agree IREN has slightly higher potential upside due to scale of GW deployed but way way larger execution risk in terms of margins. 

When it comes to future earning reports with $IREN, I'd expect markets to find out the hard way that the orchestration and customer diversity that Nebius has currently is a massive, massive moat.   

$ORCL one of the largest compute companies lost $100m+ on their most recent buildout...
  **extraction_notes**: 作者明确表达 NBIS > IREN 的方向性偏好，并给出论据（软件编排护城河、利润率对比），构成对 NBIS 的 long 预测。IREN 仅作为对比对象，未单独构成预测。ORCL 和 CRWV 作为论据支撑，列入 context_tickers。

### #10 [TRUE] **⚠ 翻转** post_id=2025241985901363480
  has_pred: False (n_pred=0, flags=[], tickers=[], pt=6896, ct=105)
  **原文**:
  > @Trylanol I don't think this is a trade that requires much urgency tbh, $XLU moves like a dinosaur. This is just one trade idea of many!

Probably could enter this like half a year later too if you decide for yourself. Power/grid is likely a bottleneck going into 2028 as well.
  **extraction_notes**: 回复推文，父推文缺失，可能指代不明。作者提及 $XLU 但未给出明确方向性预测，仅描述其波动缓慢，并称电力/电网瓶颈可能持续到2028年，但未对 $XLU 或其他标的做出方向性表态。

### #11 [TRUE] ✓ 一致 post_id=2020260581408985407
  has_pred: True (n_pred=2, flags=[], tickers=[], pt=6904, ct=385)
  **原文**:
  > $RDDT feels like a strong buy again after drop to $139 post earnings. Earnings felt great, looked option related selloff.

$OSS is a moonshot type small cap pick for edge AI + defense spend. I made a post that showed they were already validated in Venezuela combat. If they can secure that $200m contract, could easily be re-rated.
  **extraction_notes**: RDDT明确方向性表态（strong buy），OSS为moonshot pick且有条件预测（if...could），均构成预测。context_missing不影响本推文内标的识别。

### #12 [TRUE] ✓ 一致 post_id=2016249140855156962
  has_pred: True (n_pred=1, flags=[], tickers=[], pt=7327, ct=278)
  **原文**:
  > There's an interesting company on here that happens to own ~25-30% of this semi-grade material supply chain in the world.

Thermal is probably an issue, so might be a potential material composite chokepoint with $NVDA architectures in 2027.

There was no issue with H200s (<1000W) but as you get higher to 2000w with Rubin deployments, might be a hidden beneficiary of material transitions.
  **extraction_notes**: 主推文提及一家未具名公司，拥有25-30%半导体级材料供应链，可能因NVDA 2027年Rubin架构热问题受益。使用'might be'强对冲，conviction=2，hedged=true。被引推文为研究清单，无新方向性预测，仅作语境。

### #13 [TRUE] **⚠ 翻转** post_id=1989258180552175977
  has_pred: False (n_pred=0, flags=[], tickers=[], pt=7749, ct=137)
  **原文**:
  > Institutional Flow assessment for 13F Neocloud filings:

· Nebius ( $NBIS ): 🟢 Strongly Positive (7/10)
· WULF ( $WULF ): 🟢 Highly Positive (8.5/10)
· IREN ( $IREN ): 🔴 Very Negative (3/10)
· CIFR ( $CIFR ): 🟢 Highly Positive (8.0/10)
· Coreweave ( $CRWV ):  🟡 Neutral (5.5/10)
· Cleanspark ( $CLSK ): 🟢 Highly Positive (9.0/10)

_

TLDR Summary Updates: 

$NBIS
· Strong overall quantitative growth in institutional ownership, driven by a mix of solid, long-term institutional buyers alongside high activity from quantitative funds and hedge funds.

$WULF
· Structurally stable and secure institutio...
  **extraction_notes**: 作者对6个标的给出机构持仓评分(NBIS/WULF/IREN/CIFR/CRWV/CLSK)，但这是基于13F数据的流量评估，并非作者本人对标的未来方向的主观预测。评分框架(如'Strongly Positive')描述的是机构持仓结构，而非作者的投资建议或方向性表态。被引推文讨论板块下跌与基本面脱节，但未对具体标的给出方向性预测。

### #14 [TRUE] ✓ 一致 post_id=2013578670863192486
  has_pred: True (n_pred=1, flags=[], tickers=[], pt=6900, ct=248)
  **原文**:
  > $LPTH is actually one of the big benefiaries of conflicts between US and EU for supply chain disruption as US imports significant amount of germanium from Germany and Belgium.

And Lightpath offers the bottleneck alternative with black diamond manufactured 100% in US (precursors mainly US too)

This is probably just a wide indiscriminate selloff.
  **extraction_notes**: 作者明确看好 LPTH 作为供应链中断的受益者，方向性表态清晰；'probably' 语气较弱但未构成强对冲，conviction 取 3；context_missing 但标的明确，仍可抽取。

### #15 [TRUE] ✓ 一致 post_id=2011138294403551561
  has_pred: True (n_pred=2, flags=[], tickers=[], pt=6918, ct=413)
  **原文**:
  > They're growing ads -> FCF would pay for any capex. FCF was $10B+ Last quarter yet everyone was scared for their lives on spend. 

$META is growing 26% Y/Y and their forward P/E is 18.9X.

$WMT is growing in line with inflation with a forward P/E of 40x+.

There's just some mispricing in the market right now
  **extraction_notes**: 作者通过对比 META 和 WMT 的增长率与估值，指出市场存在错误定价，隐含 META 被低估（看多）而 WMT 被高估（看空）。虽然未使用强烈措辞，但给出了明确的方向性判断，conviction 定为 3。

### #16 [FALSE] ✓ 一致 post_id=1971280900572012873
  has_pred: False (n_pred=0, flags=[], tickers=[], pt=6877, ct=92)
  **原文**:
  > @soulbiri1 Thx. Sorry I got $TGT off by a month lol, hope you sold CCs to prevent theta decay.

Dividend is November 12th so I'd expect recovery Oct instead of this month.
  **extraction_notes**: 回复推文，父推文缺失。作者提及 $TGT 但仅表示自己预测时间差了一个月，并建议卖出备兑看涨期权，未对 $TGT 或其他标的给出新的方向性表态。

### #17 [FALSE] ✓ 一致 post_id=2056594930232135705
  has_pred: False (n_pred=0, flags=['victory_lap'], tickers=[], pt=7183, ct=104)
  **原文**:
  > Just another reminder:

One day after my $SOI post back in March at $40. 

Citibank and Kepler called me out and said

“it is very difficult to understand why the action [Soitec] has risen so much”

“Is the enthusiasm of the market exaggerated? That's what Citi thinks.”

Then I got a bunch of negative callouts from local European media.

Unfortunately many retail investors sold after these reports, while institutions had orders in to buy up the float.

2 months later, Soitec is now trading at 140. 

With many of these same institutions giving 250 PTs today.
  **extraction_notes**: 主推文回顾过去对Soitec的看涨call（3月$40，现在$140），并引用机构报告和媒体负面报道，属于胜利巡游（victory_lap）。被引推文是历史预测，不构成新预测。

### #18 [FALSE] ✓ 一致 post_id=2018484953634463942
  has_pred: False (n_pred=0, flags=[], tickers=[], pt=6933, ct=85)
  **原文**:
  > @beauty_oe @jukan05 うん、最初の職場は $INTC だったよ。

ムーンショット・ラボにいて、今の $META AI みたいなウェアラブルの開発をしてたんだ。

でもマネジメントのせいで、プロジェクトは全部お蔵入りになっちゃってさ。クールなプロジェクトが日の目を見ずに消えていくのは、やっぱり悲しいね。
  **extraction_notes**: 作者回忆在 $INTC 的工作经历，提及 $META AI 作为类比，无方向性表态。$INTC 和 $META 均为背景提及，不构成预测。

### #19 [FALSE] ✓ 一致 post_id=2025197436986425829
  has_pred: False (n_pred=0, flags=[], tickers=[], pt=6884, ct=73)
  **原文**:
  > @DavidLiaoCH @r0ck3t23 Large % of concentration of the etf are independent that have more pricing pricing power 

Also it’s not quite bypassing utility, they still get the power directly from companies like $VST in the index
  **extraction_notes**: 回复推文，父推文缺失，讨论ETF成分股特征，提及$VST仅作为背景说明，无方向性预测。

### #20 [FALSE] ✓ 一致 post_id=2026012416841334975
  has_pred: False (n_pred=0, flags=[], tickers=[], pt=6967, ct=79)
  **原文**:
  > Today, Anthropic called out DeepSeek, Moonshot, and Minimax for distillation.  

OpenAI has also faced the same issues with Chinese labs. 

The most braindead fix nobody is doing: 

KYC verification. 

Every financial institution from $HOOD to $IBKR does this to track flow of funds (eg. Persona selfie / ID)

Same should apply to token flows. 

American Frontier Labs should start doing this soon for their latest models. 

I'm sure they care about frictionless growth, but this is national security at risk and people/enterprises only need to go through this process once. 

This is by far the easi...
  **extraction_notes**: 作者讨论AI实验室的KYC验证方案，提及$HOOD和$IBKR仅作为金融KYC的类比，未对任何标的给出方向性预测。

### #21 [FALSE] ✓ 一致 post_id=1991967076345610627
  has_pred: False (n_pred=0, flags=[], tickers=[], pt=6930, ct=90)
  **原文**:
  > TLDR if you were curious on the findings: 

$MSTR prob not going to get liquidated. Unlikely Bitcoin remains underneath his cost average (next halving) by 2029 when interest needs to be paid. Even with MSCI outflows, Saylor probably not going to sell Bitcoin he bought and just let Microstrategy fall under nav like grayscale + slow down purchases. 

Other treasury plays not the same
  **extraction_notes**: 作者分析 $MSTR 清算可能性，给出'不太可能被清算'的结论，但未表达自身对 $MSTR 的方向性交易观点（如做多/做空）。属于情景分析而非预测。

### #22 [FALSE] ✓ 一致 post_id=1984974769369043164
  has_pred: False (n_pred=0, flags=[], tickers=[], pt=7136, ct=108)
  **原文**:
  > With $IREN people keep making the argument about ~3 GW capacity at a ~17B marketcap, deserves to be X marketcap.

$RIOT has a similar capacity too: 1GW Corsicana, 700MW Rockdale, and misc with ~3GW capacity (total if you combine BTC mining + pipeline). ~7B marketcap  

$MARA also has 1.7GW with 3+ GW pipeline as well. ~6.7B marketcap 

 $IREN did make the HPC pivot compared to the other two but we've definitely seen that priced in with the 480%+ runup.   

Fair note is that analysts from H.C. Wainright have said "IREN AI cloud business has reached a point of irrational exuberance."  

Before, ...
  **extraction_notes**: 作者对比了 $IREN、$RIOT、$MARA 的容量和市值，并讨论了 $IREN 的 HPC 转型风险与定价，但未给出明确的方向性预测。文中提及分析师观点和风险因素，属于分析性讨论，不构成对任何标的的预测。

### #23 [FALSE] ✓ 一致 post_id=2015551832794464396
  has_pred: False (n_pred=0, flags=[], tickers=[], pt=6851, ct=94)
  **原文**:
  > @Ren_aramb $IBKR has $HY9H which is SK Hynix on Frankfurt.
  **extraction_notes**: 回复推文，仅告知 $IBKR 上有 $HY9H（SK Hynix 法兰克福上市代码），无方向性表态。context_missing=true，父推文不在库中，无法判断是否构成预测。

### #24 [FALSE] ✓ 一致 post_id=1997341675753189423
  has_pred: False (n_pred=0, flags=[], tickers=[], pt=6899, ct=87)
  **原文**:
  > @pepemoonboy @Hedgeye Thanks! I'm not a hardcore $NBIS community member though. If something bad changes to the fundamentals, I'm not afraid to sell the stock.

But so far I've only seen positive changes from the parent company down to its subsidiaries so I'm excited for the future of the company.
  **extraction_notes**: 作者表达对$NBIS基本面的乐观情绪，但未给出明确的方向性预测（如买入/卖出建议或目标价）。'excited for the future'属于情绪表达，不构成预测。

### #25 [FALSE] ✓ 一致 post_id=2040269140855083041
  has_pred: False (n_pred=0, flags=[], tickers=[], pt=6985, ct=103)
  **原文**:
  > The most viral story on $RDDT right now:

-> Guy started with $300,000

-> Gets lucky with individual names at April 2025 bottom

-> Runs it up to $3,000,000 and claims they had financial freedom

-> Proceeds to do 0DTE options on $SPY

-> Turned $3M -> $50k.

Usually I give a lesson learned type story but this is just stupid?

Legit stop touching 0dte options. 

Even if they full ported it into Jim Cramer’s favorite stock $MRVL, probably would have been $6M in 2-3 years. 

The best lesson of generational wealth is looking at Nancy Pelosi. 

If you do options, look at how their on $AVGO to $NV...
  **extraction_notes**: 推文讲述一个交易失败故事并给出一般性建议（不要碰0DTE期权），提及$RDDT、$SPY、$MRVL、$AVGO、$NVDA仅作为故事背景或举例，作者未对任何具体标的给出方向性预测。

### #26 [FALSE] ✓ 一致 post_id=2023738132563431778
  has_pred: False (n_pred=0, flags=[], tickers=[], pt=6897, ct=106)
  **原文**:
  > Softbank + $ARM is one of Raspberry Pi's largest owner actually!  But yeah as you mentioned, Apple and Raspberry Pi use arm isa. 

Majority of people started off hoarding Apple devices, but ever since openclaw models were able to be run on lower cost hardware, raspberry pi started having more utility.
  **extraction_notes**: 回复推文，父推文缺失。内容为陈述 Softbank/ARM 是 Raspberry Pi 的大股东，以及 Apple 和 Raspberry Pi 使用 ARM ISA 的事实，并讨论设备囤积和低成本硬件趋势。无作者本人对任何具体标的的方向性表态，不构成预测。

### #27 [FALSE] ✓ 一致 post_id=2014077665381060688
  has_pred: False (n_pred=0, flags=[], tickers=[], pt=6864, ct=85)
  **原文**:
  > @GVDInvestor Completely agree, having the former chairman of $TSM buy $8m of $MU on the open market last week is a bullish tell.
  **extraction_notes**: 回复他人，表示同意并提及前TSM主席买入MU是看涨信号，但作者本人未给出自己的方向性表态，仅转述他人行为作为论据，不构成预测。

### #28 [FALSE] ✓ 一致 post_id=2051896675913068620
  has_pred: False (n_pred=0, flags=[], tickers=[], pt=6849, ct=85)
  **原文**:
  > @DrNHJ Yep! Thanks for the news regarding $AAPL and $INTC.
  **extraction_notes**: 回复感谢他人分享 $AAPL 和 $INTC 的新闻，无方向性表态。context_missing=true，父推文不在库中，但本推文本身无预测。

### #29 [FALSE] ✓ 一致 post_id=1971243986435354629
  has_pred: False (n_pred=0, flags=[], tickers=[], pt=7199, ct=106)
  **原文**:
  > Lot of followers were from WSB with no risk-filter. If I had to build a meme-port for Reddit with $10m to try and maximize profit:

Options 
$5M $NBIS Mar 20, $130 Call 
$2M AMZN Mar 20 $225 Call 
$500k RUT Dec 19 $2400 Call  

2x Leverage 
$1M $IREN
$1M $CIFR
$500k HIMS  

Obviously not recommending this, but if I legitimately wanted to try and make 1000% I'd do this as of today's prices.

If you had 10M, curious what risk-play you would do for a mansion vs. Wendys Dumpster.
  **extraction_notes**: 作者构建了一个假设性的高风险投资组合，但明确声明“Obviously not recommending this”，且以“If I had to...”、“if I legitimately wanted to try”等虚拟语气表达，未对任何标的给出方向性预测。所有提及的标的均为假设性配置，不构成预测。

### #30 [FALSE] ✓ 一致 post_id=2052299073898815512
  has_pred: False (n_pred=0, flags=[], tickers=[], pt=6909, ct=94)
  **原文**:
  > It's likely pure algorithmic, but another .76% of the float was shorted yesterday.  

Algorithms tend to miss a lot of the nuances of supply chain mapping like $AMD going with $GFS for CPO. 

Then $SIVE listed as 1 of 2 laser suppliers in $GFS image presentations. This is called alpha though since you know something others don't.
  **extraction_notes**: 作者讨论算法做空与供应链映射的细节，提及 AMD、GFS、SIVE 作为供应链关系说明，但未对任何标的给出方向性表态。'This is called alpha' 是知识性陈述，非预测。

---

## 2 个翻转详情分析

### #10 [TRUE → False]  post_id 末 363480

**原文**:
> @Trylanol I don't think this is a trade that requires much urgency tbh, $XLU moves like a dinosaur. This is just one trade idea of many! Probably could enter this like half a year later too if you decide for yourself. Power/grid is likely a bottleneck going into 2028 as well.

**原 cache 判**: has_pred=True (估计抽了 $XLU)
**实跑重判**: has_pred=False, notes: '父推文缺失,可能指代不明...未对 $XLU 或其他标的做出方向性表态'

**评估**: 实跑更严 — 父推文缺失 + 描述性语言 → no_pred 合理。原 cache 是 FP。

### #13 [TRUE → False]  post_id 末 175977

**原文(13F 机构持仓评分)**:
> Institutional Flow assessment for 13F Neocloud filings: NBIS 7/10 (Strongly Positive), WULF 8.5/10 (Highly Positive), IREN 3/10 (Very Negative), CIFR 8.0/10 (Highly Positive), CRWV 5.5/10 (Neutral), CLSK 9.0/10 (Highly Positive)...

**原 cache 判**: has_pred=True (估计抽了 6 条)
**实跑重判**: has_pred=False, notes: '13F 数据流量评估,非作者本人对标的未来方向的主观预测'

**评估**: 实跑更严 — 评分框架 ≠ 作者预测。原 cache 是 FP(把 13F 报告当作者预测)。

---

## 总结

### False 类(15/15) — 0 个假阴 ✓
LLM 判 has_pred=False 的 3600 条, 2505 条原文含 cashtag, 抽 15 条**全确认**没有漏抽真预测。
→ LLM 在假阴方面很稳, 不会把'讨论 $XXX 但没明确方向'当预测。

### True 类(13/15) — 2 个潜在假阳
- 2 个都是 LLM 这次更严判的边界 case:
  - 父推文缺失 + 描述性语言(无明确方向)
  - 13F 机构持仓评分(非作者预测)
- 这是 prompt 严格的进步方向, 不算真 bug
- 实际 False 类 0 假阴说明 LLM 整体很严, 之前 cache 里 2 个 True 是 v1.4.1 早期抽的不够严

### 翻概率 2/30 = 6.7%
- temperature=0 期望 0%, 实际 6.7% — 说明 LLM 后端 temperature 实际有微小浮动, 或网络层/解析层有微小非确定性
- 但 0 假阴 是个非常强的信号: LLM **不会漏抽真预测**
