# P3-8 条件性预测对称性抽样 — 盈亏各 50 条原文全文

**生成时间**: 2026-06-16T03:25:13.226500Z

## 铁律

**判定 if 条件是否触发必须独立于这条预测的盈亏结果**。
- 客观可查证已触发 → 留分母正常验证
- 客观可查证未触发 → condition_not_triggered,移出(无论盈亏)
- 不可客观判定 → unverifiable_conditional,移出(无论盈亏,单独统计)

## 范围

- 总 1m resolved: 3498
- 严格条件性 + 1m resolved: **153**

## Top 50 亏损(按 1m excess 从负到正)

**铁律测试**: 这 50 条的 if 条件触发判定,跟我用同样规则判 top 50 盈利,应该一致

### [亏损 #1] NKLR long hz=6m — pub=2025-10-15T07:42:21
- entry=2025-10-16, $17.60
- 1m: **resolved_miss** raw=-73.86% bench=+1.71% excess=-75.57%
- 3m: excess=-68.93%  6m: excess=-70.61%
- **条件 label**: ['PRICE_TARGET']
- **if 句**: ['This would be a $3T company if this were a US company, insane profit margins, insane growth rate for their size', '5T), even if buying at ATHs', "AMZN hitting $213-215 today was a good chance to stock up since it usually floats between $218-$227 if you're short term swing trading but long term I'd expect it to catchup to other mag7"]
- **原文 (全文)**:
```
The Great Soybean/Seed Oil Crash, personal thoughts and explanations:

Strong Buy
$ALAB
$CRDO
$NBIS
$WLAC
$LTC
$TSM
$BTC
(+ same as tax harvest stocks last time)
$AMZN
$SMCI
_

Buy
$AMD
$FLNC
$SEI
$BZAI
$NKLR
$IREN
$WULF
$CIFR
$CRWV
$BITF
$WYFI
$SLNH
$BITF
$RBRK
$GLXY
$GRAB
$SEA
$META
$TGT
$SNAP
$MU
$RKLB
$FLY
$UNH

Hold
$MP
$HOOD
$EOSE
$NVDA
$GOOGL
$DFLI
$SOFI
$VIRT
$RR
$AVGO
$BE
$ASTS

(Hit the ticker maximum but everything else from last post, still sell on Quantum or Oklo)
_

Strong Buys
ALAB - Huge part of datacenter buildout, NVDA like margins, Mag7 customers. Already had competitors from AVGO,  really don't think Arista would be a competitive threat.

CRDO - Same sell-off as ALAB, thought they were both kind of overvalued before, but now they're back in correction territory so good to stock up.

NBIS - $400 PT bull case. We have macro tailwind from government re-opening + rate cut EOM october into earnings, so short term looks promising. Lot of things going for it (eg. meta x crwv, so there's potential for more mag7 clients), sum of parts doing well, eg. clickhouse, and scaling rev from $100m to $1.5B+ a quarter is insane. there's already contracts locked in its just a matter of company execution.

WLAC - Wrote a thesis about this earlier at $13. Even at $14.5 strong because it can re-rate 100%+ easily.

LTC - Affected by leverage traders and government shutdown. The shutdown is predicted to last awhile and the main reason to buy was the ETF getting approved. But a great buy sub <$100 anyway, because it will get approved in due time (~95% chance).

TSM - Holy crap. This would be a $3T company if this were a US company, insane profit margins, insane growth rate for their size. And every post you see about OpenAi X (**sydney sweeney partnership) or AMD buildout/NVDA buildout. TSM is the center of it all and would easily be a $2T+ company (from here at ~$1.5T), even if buying at ATHs.

BTC - $112K good entry point. Goldt keeps hitting ATH, nothing really changed fundamentally, just lot of liquidations recently
(+ same as tax harvest stocks last time)

AMZN - I really don't know how it's still down YTD. I don't think Amazon needs much explaining but still growing  (eg. AWS backlog massive, still going like 24% but not as much as ORCL, GCP and others obviously), but with EOY seasonality and runup to Feb, now is probably the best chance to catch the bottom. AMZN hitting $213-215 today was a good chance to stock up since it usually floats between $218-$227 if you're short term swing trading but long term I'd expect it to catchup to other mag7.

SMCI - Underrated. Markets were looking short term performance, and Charles was quoting like 55%+ Y/Y forward revenue growth which nobody believed + backlog that didnt get realized yet. But now with all the data center buildouts, now it's kinda making sense. So should re-rate in the next two earnings.

_
Buy

AMD - So many deals from OpenAI x AMD, oracle building out with AMD, this is going to re-rate to a potential $1T+ company if it's actually a strong competitive to $NVDA.  I don't think it's winner takes all and you can see a $4.5T+ market cap size with NVDA and some $350B marketcap size with AMD, so we can see a large ramp up (OpenAI is usually the leader in frontier models and if Sam says they can use AMD chips + elon said its' good for small-medium weight models, prboably means something positive)

FLNC - Strong re-rate on energy after AI consumption, great buy.

SEI - Strong re-rate on energy after AI consumption, great buy.

BZAI - Someone else did a DD on this company, just cause of sector and shift to edge compute (eg. Robotics goign to be hot). Because of low MC and runup of similar companies could turn out well.

NKLR - Nuclear stocks like $OKLO have been taking off, this is just follow the lader.

IREN - Needs no introduction, huge GW compute capacity just no announced mag7 deals yet but could come anytime -> strong re-rate. Only reason not a strong buy is because not fully convinced miners can pivot like CRWV and maintain great margins (eg. $ORCL hit piece) but we'll see.

WULF - GOOGL backlog, another $3.6+ or so in funding helps a lot.

CIFR - Lot of info on X about future capacity and strong re-rating. Always liked this company because it was NBIS-lite. You can probably buy any Neocloud and it will go up because the sector is incredibly high potential with Mag7 funneling revenue.

CRWV - Didn't like this as much as others because of debt but because of the seed oil correction much better buy point at $134 (below when META deal was announced)

BITF - Same in Neocloud category

WYFI - Same in Neocloud category

BITF - Same in Neocloud category

GLXY - Same in Neocloud category, helps with their buildout

RBRK - Did a DD on this, great buy for cybersecurity sector in mid term, they just need to scale back marketing and then it looks like they have a lot more FCF because they're spending most OPEX on marketing.

GRAB - Great fundamentally, -6.56% correction good to buy again

SEA - AMZN in SEA, tons of people use them. Just a buy just because of costumer base + monetization potenetial. Fundamentally growing $5B+ rev 38% Y/Y is also great.

META - I really don't like all their expensive capex on AI since they're not really putting out fronteir models like ChatGPT with it, who knows what Zuck is doing. But that aside, down 7.3% over the month, going to $700 support, probably a good buy around here to play catchup.

TGT - Dividend next month good catalyst.

SNAP - The Jenners are coming back (helps with popularity), they're shifting former memory opex to revenue, and this will probably cause a HUGE rerating next year. Just suffers from tax harvesting otherwise would be a strong buy rn. Usually tax harvesting events are kinda done in December.

MU - Now that China fears are kinda less intense, MU is a lot stronger buy just cause of memory use on buildout.

RKLB - Neutron, golden dome contracts, lot of cataylsts

FLY - Medium lift

UNH - Healthcare stock not affected by soybeans but had a correction. Would likely go up one instituions post their ports (eg. warren likely bought more)

Random thoughts
Basically any growth/risk stock that's not named Oklo is great because we have

-> Rate Cut end of month October
-> Government re-opening sometime (likely around end of Oct or early Nov)

Into
-> Rate Cut December.
-> Midterms (Bullish for stocks)

Usually market crashes happen when there's tightening not easing. And your stupid quantum bubbles would likely continue for another 3-12 months afterward. If you're short, then probably wait till next Feb.

Anyway, this is a great time for risk-on, and specially riding trends with neoclouds -> affiliated sectors (eg. energy) -> affiliated companies (eg. smci, tsm, etc).

I half joke-about soybeans because it likely signed escalating tensions, but I'd probably see a run-up into next year. Also I could write up a lot about each one but it's pretty time consuming but I'll put on a thesis post about random ones eg. $RBRK, from time to time.

Space/robotics/energy/quantum/ai/semi/critical top verticals right now, don't fight against momentum. I can think something is overvalued (eg. some critical materials bc. it's still spectulative compared to neoclouds that kinda have guaranteed rev based on execution from mag7) but I wouldn't short it into rate cuts.

Just personal thoughts, NFA
```

### [亏损 #2] SLNH long hz=6m — pub=2025-10-15T07:42:21
- entry=2025-10-16, $4.77
- 1m: **resolved_miss** raw=-64.99% bench=+1.71% excess=-66.70%
- 3m: excess=-69.65%  6m: excess=-79.11%
- **条件 label**: ['PRICE_TARGET']
- **if 句**: ['This would be a $3T company if this were a US company, insane profit margins, insane growth rate for their size', '5T), even if buying at ATHs', "AMZN hitting $213-215 today was a good chance to stock up since it usually floats between $218-$227 if you're short term swing trading but long term I'd expect it to catchup to other mag7"]
- **原文 (全文)**:
```
The Great Soybean/Seed Oil Crash, personal thoughts and explanations:

Strong Buy
$ALAB
$CRDO
$NBIS
$WLAC
$LTC
$TSM
$BTC
(+ same as tax harvest stocks last time)
$AMZN
$SMCI
_

Buy
$AMD
$FLNC
$SEI
$BZAI
$NKLR
$IREN
$WULF
$CIFR
$CRWV
$BITF
$WYFI
$SLNH
$BITF
$RBRK
$GLXY
$GRAB
$SEA
$META
$TGT
$SNAP
$MU
$RKLB
$FLY
$UNH

Hold
$MP
$HOOD
$EOSE
$NVDA
$GOOGL
$DFLI
$SOFI
$VIRT
$RR
$AVGO
$BE
$ASTS

(Hit the ticker maximum but everything else from last post, still sell on Quantum or Oklo)
_

Strong Buys
ALAB - Huge part of datacenter buildout, NVDA like margins, Mag7 customers. Already had competitors from AVGO,  really don't think Arista would be a competitive threat.

CRDO - Same sell-off as ALAB, thought they were both kind of overvalued before, but now they're back in correction territory so good to stock up.

NBIS - $400 PT bull case. We have macro tailwind from government re-opening + rate cut EOM october into earnings, so short term looks promising. Lot of things going for it (eg. meta x crwv, so there's potential for more mag7 clients), sum of parts doing well, eg. clickhouse, and scaling rev from $100m to $1.5B+ a quarter is insane. there's already contracts locked in its just a matter of company execution.

WLAC - Wrote a thesis about this earlier at $13. Even at $14.5 strong because it can re-rate 100%+ easily.

LTC - Affected by leverage traders and government shutdown. The shutdown is predicted to last awhile and the main reason to buy was the ETF getting approved. But a great buy sub <$100 anyway, because it will get approved in due time (~95% chance).

TSM - Holy crap. This would be a $3T company if this were a US company, insane profit margins, insane growth rate for their size. And every post you see about OpenAi X (**sydney sweeney partnership) or AMD buildout/NVDA buildout. TSM is the center of it all and would easily be a $2T+ company (from here at ~$1.5T), even if buying at ATHs.

BTC - $112K good entry point. Goldt keeps hitting ATH, nothing really changed fundamentally, just lot of liquidations recently
(+ same as tax harvest stocks last time)

AMZN - I really don't know how it's still down YTD. I don't think Amazon needs much explaining but still growing  (eg. AWS backlog massive, still going like 24% but not as much as ORCL, GCP and others obviously), but with EOY seasonality and runup to Feb, now is probably the best chance to catch the bottom. AMZN hitting $213-215 today was a good chance to stock up since it usually floats between $218-$227 if you're short term swing trading but long term I'd expect it to catchup to other mag7.

SMCI - Underrated. Markets were looking short term performance, and Charles was quoting like 55%+ Y/Y forward revenue growth which nobody believed + backlog that didnt get realized yet. But now with all the data center buildouts, now it's kinda making sense. So should re-rate in the next two earnings.

_
Buy

AMD - So many deals from OpenAI x AMD, oracle building out with AMD, this is going to re-rate to a potential $1T+ company if it's actually a strong competitive to $NVDA.  I don't think it's winner takes all and you can see a $4.5T+ market cap size with NVDA and some $350B marketcap size with AMD, so we can see a large ramp up (OpenAI is usually the leader in frontier models and if Sam says they can use AMD chips + elon said its' good for small-medium weight models, prboably means something positive)

FLNC - Strong re-rate on energy after AI consumption, great buy.

SEI - Strong re-rate on energy after AI consumption, great buy.

BZAI - Someone else did a DD on this company, just cause of sector and shift to edge compute (eg. Robotics goign to be hot). Because of low MC and runup of similar companies could turn out well.

NKLR - Nuclear stocks like $OKLO have been taking off, this is just follow the lader.

IREN - Needs no introduction, huge GW compute capacity just no announced mag7 deals yet but could come anytime -> strong re-rate. Only reason not a strong buy is because not fully convinced miners can pivot like CRWV and maintain great margins (eg. $ORCL hit piece) but we'll see.

WULF - GOOGL backlog, another $3.6+ or so in funding helps a lot.

CIFR - Lot of info on X about future capacity and strong re-rating. Always liked this company because it was NBIS-lite. You can probably buy any Neocloud and it will go up because the sector is incredibly high potential with Mag7 funneling revenue.

CRWV - Didn't like this as much as others because of debt but because of the seed oil correction much better buy point at $134 (below when META deal was announced)

BITF - Same in Neocloud category

WYFI - Same in Neocloud category

BITF - Same in Neocloud category

GLXY - Same in Neocloud category, helps with their buildout

RBRK - Did a DD on this, great buy for cybersecurity sector in mid term, they just need to scale back marketing and then it looks like they have a lot more FCF because they're spending most OPEX on marketing.

GRAB - Great fundamentally, -6.56% correction good to buy again

SEA - AMZN in SEA, tons of people use them. Just a buy just because of costumer base + monetization potenetial. Fundamentally growing $5B+ rev 38% Y/Y is also great.

META - I really don't like all their expensive capex on AI since they're not really putting out fronteir models like ChatGPT with it, who knows what Zuck is doing. But that aside, down 7.3% over the month, going to $700 support, probably a good buy around here to play catchup.

TGT - Dividend next month good catalyst.

SNAP - The Jenners are coming back (helps with popularity), they're shifting former memory opex to revenue, and this will probably cause a HUGE rerating next year. Just suffers from tax harvesting otherwise would be a strong buy rn. Usually tax harvesting events are kinda done in December.

MU - Now that China fears are kinda less intense, MU is a lot stronger buy just cause of memory use on buildout.

RKLB - Neutron, golden dome contracts, lot of cataylsts

FLY - Medium lift

UNH - Healthcare stock not affected by soybeans but had a correction. Would likely go up one instituions post their ports (eg. warren likely bought more)

Random thoughts
Basically any growth/risk stock that's not named Oklo is great because we have

-> Rate Cut end of month October
-> Government re-opening sometime (likely around end of Oct or early Nov)

Into
-> Rate Cut December.
-> Midterms (Bullish for stocks)

Usually market crashes happen when there's tightening not easing. And your stupid quantum bubbles would likely continue for another 3-12 months afterward. If you're short, then probably wait till next Feb.

Anyway, this is a great time for risk-on, and specially riding trends with neoclouds -> affiliated sectors (eg. energy) -> affiliated companies (eg. smci, tsm, etc).

I half joke-about soybeans because it likely signed escalating tensions, but I'd probably see a run-up into next year. Also I could write up a lot about each one but it's pretty time consuming but I'll put on a thesis post about random ones eg. $RBRK, from time to time.

Space/robotics/energy/quantum/ai/semi/critical top verticals right now, don't fight against momentum. I can think something is overvalued (eg. some critical materials bc. it's still spectulative compared to neoclouds that kinda have guaranteed rev based on execution from mag7) but I wouldn't short it into rate cuts.

Just personal thoughts, NFA
```

### [亏损 #3] BZAI long hz=6m — pub=2025-10-15T07:42:21
- entry=2025-10-16, $6.60
- 1m: **resolved_miss** raw=-62.05% bench=+1.71% excess=-63.75%
- 3m: excess=-71.35%  6m: excess=-74.15%
- **条件 label**: ['PRICE_TARGET']
- **if 句**: ['This would be a $3T company if this were a US company, insane profit margins, insane growth rate for their size', '5T), even if buying at ATHs', "AMZN hitting $213-215 today was a good chance to stock up since it usually floats between $218-$227 if you're short term swing trading but long term I'd expect it to catchup to other mag7"]
- **原文 (全文)**:
```
The Great Soybean/Seed Oil Crash, personal thoughts and explanations:

Strong Buy
$ALAB
$CRDO
$NBIS
$WLAC
$LTC
$TSM
$BTC
(+ same as tax harvest stocks last time)
$AMZN
$SMCI
_

Buy
$AMD
$FLNC
$SEI
$BZAI
$NKLR
$IREN
$WULF
$CIFR
$CRWV
$BITF
$WYFI
$SLNH
$BITF
$RBRK
$GLXY
$GRAB
$SEA
$META
$TGT
$SNAP
$MU
$RKLB
$FLY
$UNH

Hold
$MP
$HOOD
$EOSE
$NVDA
$GOOGL
$DFLI
$SOFI
$VIRT
$RR
$AVGO
$BE
$ASTS

(Hit the ticker maximum but everything else from last post, still sell on Quantum or Oklo)
_

Strong Buys
ALAB - Huge part of datacenter buildout, NVDA like margins, Mag7 customers. Already had competitors from AVGO,  really don't think Arista would be a competitive threat.

CRDO - Same sell-off as ALAB, thought they were both kind of overvalued before, but now they're back in correction territory so good to stock up.

NBIS - $400 PT bull case. We have macro tailwind from government re-opening + rate cut EOM october into earnings, so short term looks promising. Lot of things going for it (eg. meta x crwv, so there's potential for more mag7 clients), sum of parts doing well, eg. clickhouse, and scaling rev from $100m to $1.5B+ a quarter is insane. there's already contracts locked in its just a matter of company execution.

WLAC - Wrote a thesis about this earlier at $13. Even at $14.5 strong because it can re-rate 100%+ easily.

LTC - Affected by leverage traders and government shutdown. The shutdown is predicted to last awhile and the main reason to buy was the ETF getting approved. But a great buy sub <$100 anyway, because it will get approved in due time (~95% chance).

TSM - Holy crap. This would be a $3T company if this were a US company, insane profit margins, insane growth rate for their size. And every post you see about OpenAi X (**sydney sweeney partnership) or AMD buildout/NVDA buildout. TSM is the center of it all and would easily be a $2T+ company (from here at ~$1.5T), even if buying at ATHs.

BTC - $112K good entry point. Goldt keeps hitting ATH, nothing really changed fundamentally, just lot of liquidations recently
(+ same as tax harvest stocks last time)

AMZN - I really don't know how it's still down YTD. I don't think Amazon needs much explaining but still growing  (eg. AWS backlog massive, still going like 24% but not as much as ORCL, GCP and others obviously), but with EOY seasonality and runup to Feb, now is probably the best chance to catch the bottom. AMZN hitting $213-215 today was a good chance to stock up since it usually floats between $218-$227 if you're short term swing trading but long term I'd expect it to catchup to other mag7.

SMCI - Underrated. Markets were looking short term performance, and Charles was quoting like 55%+ Y/Y forward revenue growth which nobody believed + backlog that didnt get realized yet. But now with all the data center buildouts, now it's kinda making sense. So should re-rate in the next two earnings.

_
Buy

AMD - So many deals from OpenAI x AMD, oracle building out with AMD, this is going to re-rate to a potential $1T+ company if it's actually a strong competitive to $NVDA.  I don't think it's winner takes all and you can see a $4.5T+ market cap size with NVDA and some $350B marketcap size with AMD, so we can see a large ramp up (OpenAI is usually the leader in frontier models and if Sam says they can use AMD chips + elon said its' good for small-medium weight models, prboably means something positive)

FLNC - Strong re-rate on energy after AI consumption, great buy.

SEI - Strong re-rate on energy after AI consumption, great buy.

BZAI - Someone else did a DD on this company, just cause of sector and shift to edge compute (eg. Robotics goign to be hot). Because of low MC and runup of similar companies could turn out well.

NKLR - Nuclear stocks like $OKLO have been taking off, this is just follow the lader.

IREN - Needs no introduction, huge GW compute capacity just no announced mag7 deals yet but could come anytime -> strong re-rate. Only reason not a strong buy is because not fully convinced miners can pivot like CRWV and maintain great margins (eg. $ORCL hit piece) but we'll see.

WULF - GOOGL backlog, another $3.6+ or so in funding helps a lot.

CIFR - Lot of info on X about future capacity and strong re-rating. Always liked this company because it was NBIS-lite. You can probably buy any Neocloud and it will go up because the sector is incredibly high potential with Mag7 funneling revenue.

CRWV - Didn't like this as much as others because of debt but because of the seed oil correction much better buy point at $134 (below when META deal was announced)

BITF - Same in Neocloud category

WYFI - Same in Neocloud category

BITF - Same in Neocloud category

GLXY - Same in Neocloud category, helps with their buildout

RBRK - Did a DD on this, great buy for cybersecurity sector in mid term, they just need to scale back marketing and then it looks like they have a lot more FCF because they're spending most OPEX on marketing.

GRAB - Great fundamentally, -6.56% correction good to buy again

SEA - AMZN in SEA, tons of people use them. Just a buy just because of costumer base + monetization potenetial. Fundamentally growing $5B+ rev 38% Y/Y is also great.

META - I really don't like all their expensive capex on AI since they're not really putting out fronteir models like ChatGPT with it, who knows what Zuck is doing. But that aside, down 7.3% over the month, going to $700 support, probably a good buy around here to play catchup.

TGT - Dividend next month good catalyst.

SNAP - The Jenners are coming back (helps with popularity), they're shifting former memory opex to revenue, and this will probably cause a HUGE rerating next year. Just suffers from tax harvesting otherwise would be a strong buy rn. Usually tax harvesting events are kinda done in December.

MU - Now that China fears are kinda less intense, MU is a lot stronger buy just cause of memory use on buildout.

RKLB - Neutron, golden dome contracts, lot of cataylsts

FLY - Medium lift

UNH - Healthcare stock not affected by soybeans but had a correction. Would likely go up one instituions post their ports (eg. warren likely bought more)

Random thoughts
Basically any growth/risk stock that's not named Oklo is great because we have

-> Rate Cut end of month October
-> Government re-opening sometime (likely around end of Oct or early Nov)

Into
-> Rate Cut December.
-> Midterms (Bullish for stocks)

Usually market crashes happen when there's tightening not easing. And your stupid quantum bubbles would likely continue for another 3-12 months afterward. If you're short, then probably wait till next Feb.

Anyway, this is a great time for risk-on, and specially riding trends with neoclouds -> affiliated sectors (eg. energy) -> affiliated companies (eg. smci, tsm, etc).

I half joke-about soybeans because it likely signed escalating tensions, but I'd probably see a run-up into next year. Also I could write up a lot about each one but it's pretty time consuming but I'll put on a thesis post about random ones eg. $RBRK, from time to time.

Space/robotics/energy/quantum/ai/semi/critical top verticals right now, don't fight against momentum. I can think something is overvalued (eg. some critical materials bc. it's still spectulative compared to neoclouds that kinda have guaranteed rev based on execution from mag7) but I wouldn't short it into rate cuts.

Just personal thoughts, NFA
```

### [亏损 #4] BITF long hz=6m — pub=2025-10-15T07:42:21
- entry=2025-10-16, $5.98
- 1m: **resolved_miss** raw=-56.86% bench=+1.71% excess=-58.57%
- 3m: excess=-57.92%  6m: excess=+0.00%
- **条件 label**: ['PRICE_TARGET']
- **if 句**: ['This would be a $3T company if this were a US company, insane profit margins, insane growth rate for their size', '5T), even if buying at ATHs', "AMZN hitting $213-215 today was a good chance to stock up since it usually floats between $218-$227 if you're short term swing trading but long term I'd expect it to catchup to other mag7"]
- **原文 (全文)**:
```
The Great Soybean/Seed Oil Crash, personal thoughts and explanations:

Strong Buy
$ALAB
$CRDO
$NBIS
$WLAC
$LTC
$TSM
$BTC
(+ same as tax harvest stocks last time)
$AMZN
$SMCI
_

Buy
$AMD
$FLNC
$SEI
$BZAI
$NKLR
$IREN
$WULF
$CIFR
$CRWV
$BITF
$WYFI
$SLNH
$BITF
$RBRK
$GLXY
$GRAB
$SEA
$META
$TGT
$SNAP
$MU
$RKLB
$FLY
$UNH

Hold
$MP
$HOOD
$EOSE
$NVDA
$GOOGL
$DFLI
$SOFI
$VIRT
$RR
$AVGO
$BE
$ASTS

(Hit the ticker maximum but everything else from last post, still sell on Quantum or Oklo)
_

Strong Buys
ALAB - Huge part of datacenter buildout, NVDA like margins, Mag7 customers. Already had competitors from AVGO,  really don't think Arista would be a competitive threat.

CRDO - Same sell-off as ALAB, thought they were both kind of overvalued before, but now they're back in correction territory so good to stock up.

NBIS - $400 PT bull case. We have macro tailwind from government re-opening + rate cut EOM october into earnings, so short term looks promising. Lot of things going for it (eg. meta x crwv, so there's potential for more mag7 clients), sum of parts doing well, eg. clickhouse, and scaling rev from $100m to $1.5B+ a quarter is insane. there's already contracts locked in its just a matter of company execution.

WLAC - Wrote a thesis about this earlier at $13. Even at $14.5 strong because it can re-rate 100%+ easily.

LTC - Affected by leverage traders and government shutdown. The shutdown is predicted to last awhile and the main reason to buy was the ETF getting approved. But a great buy sub <$100 anyway, because it will get approved in due time (~95% chance).

TSM - Holy crap. This would be a $3T company if this were a US company, insane profit margins, insane growth rate for their size. And every post you see about OpenAi X (**sydney sweeney partnership) or AMD buildout/NVDA buildout. TSM is the center of it all and would easily be a $2T+ company (from here at ~$1.5T), even if buying at ATHs.

BTC - $112K good entry point. Goldt keeps hitting ATH, nothing really changed fundamentally, just lot of liquidations recently
(+ same as tax harvest stocks last time)

AMZN - I really don't know how it's still down YTD. I don't think Amazon needs much explaining but still growing  (eg. AWS backlog massive, still going like 24% but not as much as ORCL, GCP and others obviously), but with EOY seasonality and runup to Feb, now is probably the best chance to catch the bottom. AMZN hitting $213-215 today was a good chance to stock up since it usually floats between $218-$227 if you're short term swing trading but long term I'd expect it to catchup to other mag7.

SMCI - Underrated. Markets were looking short term performance, and Charles was quoting like 55%+ Y/Y forward revenue growth which nobody believed + backlog that didnt get realized yet. But now with all the data center buildouts, now it's kinda making sense. So should re-rate in the next two earnings.

_
Buy

AMD - So many deals from OpenAI x AMD, oracle building out with AMD, this is going to re-rate to a potential $1T+ company if it's actually a strong competitive to $NVDA.  I don't think it's winner takes all and you can see a $4.5T+ market cap size with NVDA and some $350B marketcap size with AMD, so we can see a large ramp up (OpenAI is usually the leader in frontier models and if Sam says they can use AMD chips + elon said its' good for small-medium weight models, prboably means something positive)

FLNC - Strong re-rate on energy after AI consumption, great buy.

SEI - Strong re-rate on energy after AI consumption, great buy.

BZAI - Someone else did a DD on this company, just cause of sector and shift to edge compute (eg. Robotics goign to be hot). Because of low MC and runup of similar companies could turn out well.

NKLR - Nuclear stocks like $OKLO have been taking off, this is just follow the lader.

IREN - Needs no introduction, huge GW compute capacity just no announced mag7 deals yet but could come anytime -> strong re-rate. Only reason not a strong buy is because not fully convinced miners can pivot like CRWV and maintain great margins (eg. $ORCL hit piece) but we'll see.

WULF - GOOGL backlog, another $3.6+ or so in funding helps a lot.

CIFR - Lot of info on X about future capacity and strong re-rating. Always liked this company because it was NBIS-lite. You can probably buy any Neocloud and it will go up because the sector is incredibly high potential with Mag7 funneling revenue.

CRWV - Didn't like this as much as others because of debt but because of the seed oil correction much better buy point at $134 (below when META deal was announced)

BITF - Same in Neocloud category

WYFI - Same in Neocloud category

BITF - Same in Neocloud category

GLXY - Same in Neocloud category, helps with their buildout

RBRK - Did a DD on this, great buy for cybersecurity sector in mid term, they just need to scale back marketing and then it looks like they have a lot more FCF because they're spending most OPEX on marketing.

GRAB - Great fundamentally, -6.56% correction good to buy again

SEA - AMZN in SEA, tons of people use them. Just a buy just because of costumer base + monetization potenetial. Fundamentally growing $5B+ rev 38% Y/Y is also great.

META - I really don't like all their expensive capex on AI since they're not really putting out fronteir models like ChatGPT with it, who knows what Zuck is doing. But that aside, down 7.3% over the month, going to $700 support, probably a good buy around here to play catchup.

TGT - Dividend next month good catalyst.

SNAP - The Jenners are coming back (helps with popularity), they're shifting former memory opex to revenue, and this will probably cause a HUGE rerating next year. Just suffers from tax harvesting otherwise would be a strong buy rn. Usually tax harvesting events are kinda done in December.

MU - Now that China fears are kinda less intense, MU is a lot stronger buy just cause of memory use on buildout.

RKLB - Neutron, golden dome contracts, lot of cataylsts

FLY - Medium lift

UNH - Healthcare stock not affected by soybeans but had a correction. Would likely go up one instituions post their ports (eg. warren likely bought more)

Random thoughts
Basically any growth/risk stock that's not named Oklo is great because we have

-> Rate Cut end of month October
-> Government re-opening sometime (likely around end of Oct or early Nov)

Into
-> Rate Cut December.
-> Midterms (Bullish for stocks)

Usually market crashes happen when there's tightening not easing. And your stupid quantum bubbles would likely continue for another 3-12 months afterward. If you're short, then probably wait till next Feb.

Anyway, this is a great time for risk-on, and specially riding trends with neoclouds -> affiliated sectors (eg. energy) -> affiliated companies (eg. smci, tsm, etc).

I half joke-about soybeans because it likely signed escalating tensions, but I'd probably see a run-up into next year. Also I could write up a lot about each one but it's pretty time consuming but I'll put on a thesis post about random ones eg. $RBRK, from time to time.

Space/robotics/energy/quantum/ai/semi/critical top verticals right now, don't fight against momentum. I can think something is overvalued (eg. some critical materials bc. it's still spectulative compared to neoclouds that kinda have guaranteed rev based on execution from mag7) but I wouldn't short it into rate cuts.

Just personal thoughts, NFA
```

### [亏损 #5] SLNH long hz=long_term — pub=2025-10-19T18:21:35
- entry=2025-10-20, $4.73
- 1m: **resolved_miss** raw=-58.99% bench=-1.67% excess=-57.31%
- 3m: excess=-74.62%  6m: excess=-77.20%
- **条件 label**: ['PRICE_TARGET']
- **if 句**: ['5T marketcap, AMD has a lot to catch up on even if it takes a small percent share', "BMNR - If I don't like Ethereum at these levels, no point of holding treasury companies"]
- **原文 (全文)**:
```
October 20th, Important Rate Cut Trading Week.

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
$ETH
$BMNR
$PL
$BLSKY
$RGTI
$OKLO
$IONQ
$QBTS

_

So macro wise, we are 9 days away from (~97% or so rate cut). Market is in fear mode. This is the ideal time to go long and not cut positions.

Fire Sale
_

$NBIS - Needs no explanation, I still maintain $400 PT on a bull case 2026 due to 4-6B+ forward revenue off ~60-75% gross margins, and another likely hyperscaler contract (eg. $META)

What happened on the 10%+ drop on Friday was mechanical hedging and MM Pinning. You can see this with the price stuck at $113.5, despite any volatility. 

I'd expect short hedges to unwind Monday (given MMs bought puts and were short calls -> heavy short into expiration) and price to go back up. I ended up buying 6 figures worth of calls on the drop as there was no material changes.

Strong Buy

TSM - Holy crap, please have this in your portfolio. This is a money printer, and scaling your revenue by 38-40% every year WHILE increasing gross margins is just insane. It dipped as well after smashing earnings so it's one of the easiest longs in my life.

AMKR - I don't have this in my portfolio yet but will be looking to add due to TSM's involvement in Arizona and potential to be a big partner in the US supply chain (as America tries to push TSM toward US fab + manufacturing).

WLAC - Neocloud SPAC IPO, large upside. I talk about this a lot recently, but it's probably one of the best valued Neoclouds out there, and already has great profit margins (not a pivot from miners, where it's a bit more uncertain). They work with Fluidstack, and I'd expect a 500%+ re-rating on top of a Mag7 contract.

AMZN - $213 is insane lol. I have no clue how this is down -3% YTD during a bull market.

LTC - Affected by crypto liquidations and government shutdown delaying ETFs. Great time to buy and just wait for ETF to be approved.

RDDT - Great dip to $190. I thought $200 would be a bottom but ended up going lower. The news about ChatGPT citing it less caused a large sell-off which I think was very immaterial.

HIMS - 14%+ drop off CEO share sale. Owners sell shares all the time, it doesn't really affect the fundamentals of the company much, just short term sentiment. I'd expect it to rebound.

IBIT - Bitcoin $108k great entry point, it's been swinging between $110k - $120k for awhile so anything under is usually great.

ALAB - I said this last time but it sold off way too much from news of a new competitor. It's already competing vs AVGO in the market lol, NVDA-like margins, growing hundreds of percent Y/Y, Mag7 using them in data center buildout. 

CRDO - Similar thesis to ALAB, sold off alongside Astera but a bit less.

SMCI - Should get re-rated for 55%+ or so revenue growth into next year. I doubted the projections earlier but with the data center growth, it's looking realistic.

FLY - This was a medium lift payload play. People doubt fly's execution but NOC co-developing medium lift takes a lot of risk off the table (and possible re-rating it 500%+ when it competes vs falcon9)

SNAP - Did the math on Snap monetization of memories in an earlier DD post and it's completely not priced in yet. It's doing $1.3B+ quarterly revenue on a $13B market cap lol, and the amount FCF they would get from increasing their revenue + lowering Google OPEX costs is insane.

ETOR  - Majority cash, growing at IBKR rates, suffering from tax harvesting

LULU - Suffering from tax harvesting + competition from Alo, Vuori, etc. But seasonally should be good, and extremely low p/e now.

Buy
AMD - ChatGPT putting in AMD orders, ORCL building out AMD data centers. Likely going to get a re-rating in the next year as a potential $NVDA competitor. Still think Nvidia will dominate but with it's 4.5T marketcap, AMD has a lot to catch up on even if it takes a small percent share.

HOOD - Looking at a lot better after the 10%+ correction. Could pull a PLTR

RBRK - Did DD on this earlier, looks better on the drop as a cybersecurity company really low multiples in the space. Just needs to cut back on marketing, customers sticky. 

UNH - Healthcare is sht in America but not going anywhere. Think Warren and the others know this 

TGT 🐈 - Dividend next moth, big dividend stock. Around now is a good time to load up IMO

IREN 🐈 - Huge GW, expect mag7 or similar deal. 

WYFI - Any neocloud is a buy (eg. see thesis on mag7 funneling revenue down toward these small 1B-5B companies)

WULF - neocloud play

CIFR - neocloud play

SLNH - neocloud play

BITF - neocloud play

GLXY - neocloud derivative play

FLNC - neocloud energy play

MU - China derisked, memory had a huge market there, memory also likely going to get re-rating in tdata center buildout

_

Sell

ETH - Not a fan of Ethereum at $4k+
BMNR - If I don't like Ethereum at these levels, no point of holding treasury companies 
PL - Low revenue, space stock (extremely high valuation)
BLSKY -Low revenue, space stock (extremely high valuation)
RGTI - Quantum bubble
OKLO - Nuclear bubble
IONQ -Quantum bubble 
QBTS - Quantum bubble

_

Quick macro heads up:
-> Rate cut in 9 days ~97% odds. Frontrunning expected, go long.  That's all.
```

### [亏损 #6] WYFI long hz=6m — pub=2025-10-15T07:42:21
- entry=2025-10-16, $37.00
- 1m: **resolved_miss** raw=-51.35% bench=+1.71% excess=-53.06%
- 3m: excess=-50.75%  6m: excess=-63.41%
- **条件 label**: ['PRICE_TARGET']
- **if 句**: ['This would be a $3T company if this were a US company, insane profit margins, insane growth rate for their size', '5T), even if buying at ATHs', "AMZN hitting $213-215 today was a good chance to stock up since it usually floats between $218-$227 if you're short term swing trading but long term I'd expect it to catchup to other mag7"]
- **原文 (全文)**:
```
The Great Soybean/Seed Oil Crash, personal thoughts and explanations:

Strong Buy
$ALAB
$CRDO
$NBIS
$WLAC
$LTC
$TSM
$BTC
(+ same as tax harvest stocks last time)
$AMZN
$SMCI
_

Buy
$AMD
$FLNC
$SEI
$BZAI
$NKLR
$IREN
$WULF
$CIFR
$CRWV
$BITF
$WYFI
$SLNH
$BITF
$RBRK
$GLXY
$GRAB
$SEA
$META
$TGT
$SNAP
$MU
$RKLB
$FLY
$UNH

Hold
$MP
$HOOD
$EOSE
$NVDA
$GOOGL
$DFLI
$SOFI
$VIRT
$RR
$AVGO
$BE
$ASTS

(Hit the ticker maximum but everything else from last post, still sell on Quantum or Oklo)
_

Strong Buys
ALAB - Huge part of datacenter buildout, NVDA like margins, Mag7 customers. Already had competitors from AVGO,  really don't think Arista would be a competitive threat.

CRDO - Same sell-off as ALAB, thought they were both kind of overvalued before, but now they're back in correction territory so good to stock up.

NBIS - $400 PT bull case. We have macro tailwind from government re-opening + rate cut EOM october into earnings, so short term looks promising. Lot of things going for it (eg. meta x crwv, so there's potential for more mag7 clients), sum of parts doing well, eg. clickhouse, and scaling rev from $100m to $1.5B+ a quarter is insane. there's already contracts locked in its just a matter of company execution.

WLAC - Wrote a thesis about this earlier at $13. Even at $14.5 strong because it can re-rate 100%+ easily.

LTC - Affected by leverage traders and government shutdown. The shutdown is predicted to last awhile and the main reason to buy was the ETF getting approved. But a great buy sub <$100 anyway, because it will get approved in due time (~95% chance).

TSM - Holy crap. This would be a $3T company if this were a US company, insane profit margins, insane growth rate for their size. And every post you see about OpenAi X (**sydney sweeney partnership) or AMD buildout/NVDA buildout. TSM is the center of it all and would easily be a $2T+ company (from here at ~$1.5T), even if buying at ATHs.

BTC - $112K good entry point. Goldt keeps hitting ATH, nothing really changed fundamentally, just lot of liquidations recently
(+ same as tax harvest stocks last time)

AMZN - I really don't know how it's still down YTD. I don't think Amazon needs much explaining but still growing  (eg. AWS backlog massive, still going like 24% but not as much as ORCL, GCP and others obviously), but with EOY seasonality and runup to Feb, now is probably the best chance to catch the bottom. AMZN hitting $213-215 today was a good chance to stock up since it usually floats between $218-$227 if you're short term swing trading but long term I'd expect it to catchup to other mag7.

SMCI - Underrated. Markets were looking short term performance, and Charles was quoting like 55%+ Y/Y forward revenue growth which nobody believed + backlog that didnt get realized yet. But now with all the data center buildouts, now it's kinda making sense. So should re-rate in the next two earnings.

_
Buy

AMD - So many deals from OpenAI x AMD, oracle building out with AMD, this is going to re-rate to a potential $1T+ company if it's actually a strong competitive to $NVDA.  I don't think it's winner takes all and you can see a $4.5T+ market cap size with NVDA and some $350B marketcap size with AMD, so we can see a large ramp up (OpenAI is usually the leader in frontier models and if Sam says they can use AMD chips + elon said its' good for small-medium weight models, prboably means something positive)

FLNC - Strong re-rate on energy after AI consumption, great buy.

SEI - Strong re-rate on energy after AI consumption, great buy.

BZAI - Someone else did a DD on this company, just cause of sector and shift to edge compute (eg. Robotics goign to be hot). Because of low MC and runup of similar companies could turn out well.

NKLR - Nuclear stocks like $OKLO have been taking off, this is just follow the lader.

IREN - Needs no introduction, huge GW compute capacity just no announced mag7 deals yet but could come anytime -> strong re-rate. Only reason not a strong buy is because not fully convinced miners can pivot like CRWV and maintain great margins (eg. $ORCL hit piece) but we'll see.

WULF - GOOGL backlog, another $3.6+ or so in funding helps a lot.

CIFR - Lot of info on X about future capacity and strong re-rating. Always liked this company because it was NBIS-lite. You can probably buy any Neocloud and it will go up because the sector is incredibly high potential with Mag7 funneling revenue.

CRWV - Didn't like this as much as others because of debt but because of the seed oil correction much better buy point at $134 (below when META deal was announced)

BITF - Same in Neocloud category

WYFI - Same in Neocloud category

BITF - Same in Neocloud category

GLXY - Same in Neocloud category, helps with their buildout

RBRK - Did a DD on this, great buy for cybersecurity sector in mid term, they just need to scale back marketing and then it looks like they have a lot more FCF because they're spending most OPEX on marketing.

GRAB - Great fundamentally, -6.56% correction good to buy again

SEA - AMZN in SEA, tons of people use them. Just a buy just because of costumer base + monetization potenetial. Fundamentally growing $5B+ rev 38% Y/Y is also great.

META - I really don't like all their expensive capex on AI since they're not really putting out fronteir models like ChatGPT with it, who knows what Zuck is doing. But that aside, down 7.3% over the month, going to $700 support, probably a good buy around here to play catchup.

TGT - Dividend next month good catalyst.

SNAP - The Jenners are coming back (helps with popularity), they're shifting former memory opex to revenue, and this will probably cause a HUGE rerating next year. Just suffers from tax harvesting otherwise would be a strong buy rn. Usually tax harvesting events are kinda done in December.

MU - Now that China fears are kinda less intense, MU is a lot stronger buy just cause of memory use on buildout.

RKLB - Neutron, golden dome contracts, lot of cataylsts

FLY - Medium lift

UNH - Healthcare stock not affected by soybeans but had a correction. Would likely go up one instituions post their ports (eg. warren likely bought more)

Random thoughts
Basically any growth/risk stock that's not named Oklo is great because we have

-> Rate Cut end of month October
-> Government re-opening sometime (likely around end of Oct or early Nov)

Into
-> Rate Cut December.
-> Midterms (Bullish for stocks)

Usually market crashes happen when there's tightening not easing. And your stupid quantum bubbles would likely continue for another 3-12 months afterward. If you're short, then probably wait till next Feb.

Anyway, this is a great time for risk-on, and specially riding trends with neoclouds -> affiliated sectors (eg. energy) -> affiliated companies (eg. smci, tsm, etc).

I half joke-about soybeans because it likely signed escalating tensions, but I'd probably see a run-up into next year. Also I could write up a lot about each one but it's pretty time consuming but I'll put on a thesis post about random ones eg. $RBRK, from time to time.

Space/robotics/energy/quantum/ai/semi/critical top verticals right now, don't fight against momentum. I can think something is overvalued (eg. some critical materials bc. it's still spectulative compared to neoclouds that kinda have guaranteed rev based on execution from mag7) but I wouldn't short it into rate cuts.

Just personal thoughts, NFA
```

### [亏损 #7] BITF long hz=long_term — pub=2025-10-19T18:21:35
- entry=2025-10-20, $5.41
- 1m: **resolved_miss** raw=-49.12% bench=-1.67% excess=-47.45%
- 3m: excess=-53.42%  6m: excess=+0.00%
- **条件 label**: ['PRICE_TARGET']
- **if 句**: ['5T marketcap, AMD has a lot to catch up on even if it takes a small percent share', "BMNR - If I don't like Ethereum at these levels, no point of holding treasury companies"]
- **原文 (全文)**:
```
October 20th, Important Rate Cut Trading Week.

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
$ETH
$BMNR
$PL
$BLSKY
$RGTI
$OKLO
$IONQ
$QBTS

_

So macro wise, we are 9 days away from (~97% or so rate cut). Market is in fear mode. This is the ideal time to go long and not cut positions.

Fire Sale
_

$NBIS - Needs no explanation, I still maintain $400 PT on a bull case 2026 due to 4-6B+ forward revenue off ~60-75% gross margins, and another likely hyperscaler contract (eg. $META)

What happened on the 10%+ drop on Friday was mechanical hedging and MM Pinning. You can see this with the price stuck at $113.5, despite any volatility. 

I'd expect short hedges to unwind Monday (given MMs bought puts and were short calls -> heavy short into expiration) and price to go back up. I ended up buying 6 figures worth of calls on the drop as there was no material changes.

Strong Buy

TSM - Holy crap, please have this in your portfolio. This is a money printer, and scaling your revenue by 38-40% every year WHILE increasing gross margins is just insane. It dipped as well after smashing earnings so it's one of the easiest longs in my life.

AMKR - I don't have this in my portfolio yet but will be looking to add due to TSM's involvement in Arizona and potential to be a big partner in the US supply chain (as America tries to push TSM toward US fab + manufacturing).

WLAC - Neocloud SPAC IPO, large upside. I talk about this a lot recently, but it's probably one of the best valued Neoclouds out there, and already has great profit margins (not a pivot from miners, where it's a bit more uncertain). They work with Fluidstack, and I'd expect a 500%+ re-rating on top of a Mag7 contract.

AMZN - $213 is insane lol. I have no clue how this is down -3% YTD during a bull market.

LTC - Affected by crypto liquidations and government shutdown delaying ETFs. Great time to buy and just wait for ETF to be approved.

RDDT - Great dip to $190. I thought $200 would be a bottom but ended up going lower. The news about ChatGPT citing it less caused a large sell-off which I think was very immaterial.

HIMS - 14%+ drop off CEO share sale. Owners sell shares all the time, it doesn't really affect the fundamentals of the company much, just short term sentiment. I'd expect it to rebound.

IBIT - Bitcoin $108k great entry point, it's been swinging between $110k - $120k for awhile so anything under is usually great.

ALAB - I said this last time but it sold off way too much from news of a new competitor. It's already competing vs AVGO in the market lol, NVDA-like margins, growing hundreds of percent Y/Y, Mag7 using them in data center buildout. 

CRDO - Similar thesis to ALAB, sold off alongside Astera but a bit less.

SMCI - Should get re-rated for 55%+ or so revenue growth into next year. I doubted the projections earlier but with the data center growth, it's looking realistic.

FLY - This was a medium lift payload play. People doubt fly's execution but NOC co-developing medium lift takes a lot of risk off the table (and possible re-rating it 500%+ when it competes vs falcon9)

SNAP - Did the math on Snap monetization of memories in an earlier DD post and it's completely not priced in yet. It's doing $1.3B+ quarterly revenue on a $13B market cap lol, and the amount FCF they would get from increasing their revenue + lowering Google OPEX costs is insane.

ETOR  - Majority cash, growing at IBKR rates, suffering from tax harvesting

LULU - Suffering from tax harvesting + competition from Alo, Vuori, etc. But seasonally should be good, and extremely low p/e now.

Buy
AMD - ChatGPT putting in AMD orders, ORCL building out AMD data centers. Likely going to get a re-rating in the next year as a potential $NVDA competitor. Still think Nvidia will dominate but with it's 4.5T marketcap, AMD has a lot to catch up on even if it takes a small percent share.

HOOD - Looking at a lot better after the 10%+ correction. Could pull a PLTR

RBRK - Did DD on this earlier, looks better on the drop as a cybersecurity company really low multiples in the space. Just needs to cut back on marketing, customers sticky. 

UNH - Healthcare is sht in America but not going anywhere. Think Warren and the others know this 

TGT 🐈 - Dividend next moth, big dividend stock. Around now is a good time to load up IMO

IREN 🐈 - Huge GW, expect mag7 or similar deal. 

WYFI - Any neocloud is a buy (eg. see thesis on mag7 funneling revenue down toward these small 1B-5B companies)

WULF - neocloud play

CIFR - neocloud play

SLNH - neocloud play

BITF - neocloud play

GLXY - neocloud derivative play

FLNC - neocloud energy play

MU - China derisked, memory had a huge market there, memory also likely going to get re-rating in tdata center buildout

_

Sell

ETH - Not a fan of Ethereum at $4k+
BMNR - If I don't like Ethereum at these levels, no point of holding treasury companies 
PL - Low revenue, space stock (extremely high valuation)
BLSKY -Low revenue, space stock (extremely high valuation)
RGTI - Quantum bubble
OKLO - Nuclear bubble
IONQ -Quantum bubble 
QBTS - Quantum bubble

_

Quick macro heads up:
-> Rate cut in 9 days ~97% odds. Frontrunning expected, go long.  That's all.
```

### [亏损 #8] CRWV long hz=6m — pub=2025-10-15T07:42:21
- entry=2025-10-16, $141.44
- 1m: **resolved_miss** raw=-45.31% bench=+1.71% excess=-47.01%
- 3m: excess=-35.24%  6m: excess=-25.16%
- **条件 label**: ['PRICE_TARGET']
- **if 句**: ['This would be a $3T company if this were a US company, insane profit margins, insane growth rate for their size', '5T), even if buying at ATHs', "AMZN hitting $213-215 today was a good chance to stock up since it usually floats between $218-$227 if you're short term swing trading but long term I'd expect it to catchup to other mag7"]
- **原文 (全文)**:
```
The Great Soybean/Seed Oil Crash, personal thoughts and explanations:

Strong Buy
$ALAB
$CRDO
$NBIS
$WLAC
$LTC
$TSM
$BTC
(+ same as tax harvest stocks last time)
$AMZN
$SMCI
_

Buy
$AMD
$FLNC
$SEI
$BZAI
$NKLR
$IREN
$WULF
$CIFR
$CRWV
$BITF
$WYFI
$SLNH
$BITF
$RBRK
$GLXY
$GRAB
$SEA
$META
$TGT
$SNAP
$MU
$RKLB
$FLY
$UNH

Hold
$MP
$HOOD
$EOSE
$NVDA
$GOOGL
$DFLI
$SOFI
$VIRT
$RR
$AVGO
$BE
$ASTS

(Hit the ticker maximum but everything else from last post, still sell on Quantum or Oklo)
_

Strong Buys
ALAB - Huge part of datacenter buildout, NVDA like margins, Mag7 customers. Already had competitors from AVGO,  really don't think Arista would be a competitive threat.

CRDO - Same sell-off as ALAB, thought they were both kind of overvalued before, but now they're back in correction territory so good to stock up.

NBIS - $400 PT bull case. We have macro tailwind from government re-opening + rate cut EOM october into earnings, so short term looks promising. Lot of things going for it (eg. meta x crwv, so there's potential for more mag7 clients), sum of parts doing well, eg. clickhouse, and scaling rev from $100m to $1.5B+ a quarter is insane. there's already contracts locked in its just a matter of company execution.

WLAC - Wrote a thesis about this earlier at $13. Even at $14.5 strong because it can re-rate 100%+ easily.

LTC - Affected by leverage traders and government shutdown. The shutdown is predicted to last awhile and the main reason to buy was the ETF getting approved. But a great buy sub <$100 anyway, because it will get approved in due time (~95% chance).

TSM - Holy crap. This would be a $3T company if this were a US company, insane profit margins, insane growth rate for their size. And every post you see about OpenAi X (**sydney sweeney partnership) or AMD buildout/NVDA buildout. TSM is the center of it all and would easily be a $2T+ company (from here at ~$1.5T), even if buying at ATHs.

BTC - $112K good entry point. Goldt keeps hitting ATH, nothing really changed fundamentally, just lot of liquidations recently
(+ same as tax harvest stocks last time)

AMZN - I really don't know how it's still down YTD. I don't think Amazon needs much explaining but still growing  (eg. AWS backlog massive, still going like 24% but not as much as ORCL, GCP and others obviously), but with EOY seasonality and runup to Feb, now is probably the best chance to catch the bottom. AMZN hitting $213-215 today was a good chance to stock up since it usually floats between $218-$227 if you're short term swing trading but long term I'd expect it to catchup to other mag7.

SMCI - Underrated. Markets were looking short term performance, and Charles was quoting like 55%+ Y/Y forward revenue growth which nobody believed + backlog that didnt get realized yet. But now with all the data center buildouts, now it's kinda making sense. So should re-rate in the next two earnings.

_
Buy

AMD - So many deals from OpenAI x AMD, oracle building out with AMD, this is going to re-rate to a potential $1T+ company if it's actually a strong competitive to $NVDA.  I don't think it's winner takes all and you can see a $4.5T+ market cap size with NVDA and some $350B marketcap size with AMD, so we can see a large ramp up (OpenAI is usually the leader in frontier models and if Sam says they can use AMD chips + elon said its' good for small-medium weight models, prboably means something positive)

FLNC - Strong re-rate on energy after AI consumption, great buy.

SEI - Strong re-rate on energy after AI consumption, great buy.

BZAI - Someone else did a DD on this company, just cause of sector and shift to edge compute (eg. Robotics goign to be hot). Because of low MC and runup of similar companies could turn out well.

NKLR - Nuclear stocks like $OKLO have been taking off, this is just follow the lader.

IREN - Needs no introduction, huge GW compute capacity just no announced mag7 deals yet but could come anytime -> strong re-rate. Only reason not a strong buy is because not fully convinced miners can pivot like CRWV and maintain great margins (eg. $ORCL hit piece) but we'll see.

WULF - GOOGL backlog, another $3.6+ or so in funding helps a lot.

CIFR - Lot of info on X about future capacity and strong re-rating. Always liked this company because it was NBIS-lite. You can probably buy any Neocloud and it will go up because the sector is incredibly high potential with Mag7 funneling revenue.

CRWV - Didn't like this as much as others because of debt but because of the seed oil correction much better buy point at $134 (below when META deal was announced)

BITF - Same in Neocloud category

WYFI - Same in Neocloud category

BITF - Same in Neocloud category

GLXY - Same in Neocloud category, helps with their buildout

RBRK - Did a DD on this, great buy for cybersecurity sector in mid term, they just need to scale back marketing and then it looks like they have a lot more FCF because they're spending most OPEX on marketing.

GRAB - Great fundamentally, -6.56% correction good to buy again

SEA - AMZN in SEA, tons of people use them. Just a buy just because of costumer base + monetization potenetial. Fundamentally growing $5B+ rev 38% Y/Y is also great.

META - I really don't like all their expensive capex on AI since they're not really putting out fronteir models like ChatGPT with it, who knows what Zuck is doing. But that aside, down 7.3% over the month, going to $700 support, probably a good buy around here to play catchup.

TGT - Dividend next month good catalyst.

SNAP - The Jenners are coming back (helps with popularity), they're shifting former memory opex to revenue, and this will probably cause a HUGE rerating next year. Just suffers from tax harvesting otherwise would be a strong buy rn. Usually tax harvesting events are kinda done in December.

MU - Now that China fears are kinda less intense, MU is a lot stronger buy just cause of memory use on buildout.

RKLB - Neutron, golden dome contracts, lot of cataylsts

FLY - Medium lift

UNH - Healthcare stock not affected by soybeans but had a correction. Would likely go up one instituions post their ports (eg. warren likely bought more)

Random thoughts
Basically any growth/risk stock that's not named Oklo is great because we have

-> Rate Cut end of month October
-> Government re-opening sometime (likely around end of Oct or early Nov)

Into
-> Rate Cut December.
-> Midterms (Bullish for stocks)

Usually market crashes happen when there's tightening not easing. And your stupid quantum bubbles would likely continue for another 3-12 months afterward. If you're short, then probably wait till next Feb.

Anyway, this is a great time for risk-on, and specially riding trends with neoclouds -> affiliated sectors (eg. energy) -> affiliated companies (eg. smci, tsm, etc).

I half joke-about soybeans because it likely signed escalating tensions, but I'd probably see a run-up into next year. Also I could write up a lot about each one but it's pretty time consuming but I'll put on a thesis post about random ones eg. $RBRK, from time to time.

Space/robotics/energy/quantum/ai/semi/critical top verticals right now, don't fight against momentum. I can think something is overvalued (eg. some critical materials bc. it's still spectulative compared to neoclouds that kinda have guaranteed rev based on execution from mag7) but I wouldn't short it into rate cuts.

Just personal thoughts, NFA
```

### [亏损 #9] SPRB long hz=event_driven — pub=2025-10-06T21:36:09
- entry=2025-10-07, $211.95
- 1m: **resolved_miss** raw=-43.38% bench=+1.26% excess=-44.65%
- 3m: excess=-68.27%  6m: excess=-71.52%
- **条件 label**: ['PRICE_TARGET']
- **if 句**: ["TLDR: Might go up to $500 temporary strike if there's no dilution just because of TA-ERT catalyst", "In OP's post they claimed $500 PT, which is fair if company doesn't dilute", "After issuing new shares + dilution (Market cap at $150m-$200m might normalize share price to ~$50-75), don't really see the $500 figure if dilution is included"]
- **原文 (全文)**:
```
TLDR: Might go up to $500 temporary strike if there's no dilution just because of TA-ERT catalyst. But it's playing Russian Roulette on dilution days.

So had some more time to look into things:

Fair value $SPRB market cap is = ~$150–200m. ($85M now). In OP's post they claimed $500 PT, which is fair if company doesn't dilute. 

However:

SPRB has $16.4M in cash equivalents, June 30, 2025, dilution with new shares seems inevitable just because of low cahs balance. Price rise was due to low float + good news (there's no short interest like .16% so not a short squeeze)

After issuing new shares + dilution (Market cap at $150m-$200m might normalize share price to ~$50-75), don't really see the $500 figure if dilution is included.  

We might see another 100%+ runup just because of limited float toward that $500 mark (like how $BULL ran to a $60B MC off low float), but I would be against holding it long term because of russian roulette dilution on a random day. 

Either way, I like playing Russian Roulette. Welcome any counterpoints
```

### [亏损 #10] SPRB long hz=event_driven — pub=2025-10-06T22:29:49
- entry=2025-10-07, $211.95
- 1m: **resolved_miss** raw=-43.38% bench=+1.26% excess=-44.65%
- 3m: excess=-68.27%  6m: excess=-71.52%
- **条件 label**: ['PRICE_TARGET']
- **if 句**: ["If you have the patience for shares for a year or two, I'd expect a 50%+ return, just whenever the market wants to price it in", "It's genuinely overvalued even if it's highest conviction 5Y long but at this point it might pull a $PLTR", "all these ten or hundred billion dollar deals if they're valued at 500B lol"]
- **原文 (全文)**:
```
Monday October 6th Market Close Thoughts:

- $NBIS extremely good dip buy. Down 2.38% after rising 5.78% in the morning. All other Neoclouds from $IREN to $CIFR held their 4%-14%+ gains. Nebius likely influenced by option flow, should play catchup soon and I stand by $225 PT. 

- $AMZN, $META two Mag7 that should outperform next 2-3 months and play catchup with the rest. Especially Amazon.

-  $SNAP, $RDDT two good recovery plays. Snapchat especially because of the revenue monetization changes. If you have the patience for shares for a year or two, I'd expect a 50%+ return, just whenever the market wants to price it in. Not everyone has patience and opportunity cost using the funds in $SNAP instead of Neoclouds might not be worth. 

Reddit I've maintained that the citations from ChatGPT is a BS reason for a 29% sell-off so I bought into it.

- $SPRB caught everyone's attention. I do expect it to keep rising to a $150-$200m marketcap from $75m but it's like playing Russian Roulette, usually dilution happens 2-3 days after a major event.

- Stuff like $RKLB, just need to hold lol. It's genuinely overvalued even if it's highest conviction 5Y long but at this point it might pull a $PLTR. 

- $AMD x OpenAI deal heavily bullish for semi industry. I expected $TSM, $ASML, energy stocks and Neoclouds to get a boost from AI infra buildout. Main negative ones were $CRWV, because of $NVDA dependencies and obviously NVDA, but Neoclouds aren't locked into one player, and they already have 5-10+ year contracts locked in.

It just puts a tiny dent in the $NVDA moat idea but nothing material yet. 

I personally think AMD might pull an $ORCL where it dips past rally, and then ends up pulling an $AVGO when markets start pricing in forward revenue. 

Then again, I don't know where OpenAI is getting all this money to promise Oracle, AMD, etc. all these ten or hundred billion dollar deals if they're valued at 500B lol. 

- Gold rallying to ATH every day just signals that $BTC is always a good buy, even at $123k, if it ends up becoming a hedge against inflation. It's close to 1/10th the market-cap. 

- $LTC still a great buy because of ETF approval. There's the government shutdown so people just forgot it hasn't happened yet, but should get approved eventually.

- $VIRT great buy at $32.5, I'd cost average around this range (sorry if you bought calls at $36, my positions are down 35% or so). But again it's an asymmetrical hedge to VIX (VIX IV very high for hedging, VIRT is undervalued ~6.3 forward p/e with buybacks an low IV), so even if positions are down, your other stocks should go up to balance it out. 

- Still looking into other beneficiaries of buildouts from energy stocks, small caps like $EOSE, memory like $MU, etc. that followers recommended. I try not to talk about something much until I'm informed myself.  

- If you're on leverage or going long, now is the time to do it until January. 3x rate cut, market probably frontrunning Oct rate cut now.
```

### [亏损 #11] WYFI long hz=long_term — pub=2025-10-19T18:21:35
- entry=2025-10-20, $30.99
- 1m: **resolved_miss** raw=-45.60% bench=-1.67% excess=-43.92%
- 3m: excess=-39.10%  6m: excess=-51.58%
- **条件 label**: ['PRICE_TARGET']
- **if 句**: ['5T marketcap, AMD has a lot to catch up on even if it takes a small percent share', "BMNR - If I don't like Ethereum at these levels, no point of holding treasury companies"]
- **原文 (全文)**:
```
October 20th, Important Rate Cut Trading Week.

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
$ETH
$BMNR
$PL
$BLSKY
$RGTI
$OKLO
$IONQ
$QBTS

_

So macro wise, we are 9 days away from (~97% or so rate cut). Market is in fear mode. This is the ideal time to go long and not cut positions.

Fire Sale
_

$NBIS - Needs no explanation, I still maintain $400 PT on a bull case 2026 due to 4-6B+ forward revenue off ~60-75% gross margins, and another likely hyperscaler contract (eg. $META)

What happened on the 10%+ drop on Friday was mechanical hedging and MM Pinning. You can see this with the price stuck at $113.5, despite any volatility. 

I'd expect short hedges to unwind Monday (given MMs bought puts and were short calls -> heavy short into expiration) and price to go back up. I ended up buying 6 figures worth of calls on the drop as there was no material changes.

Strong Buy

TSM - Holy crap, please have this in your portfolio. This is a money printer, and scaling your revenue by 38-40% every year WHILE increasing gross margins is just insane. It dipped as well after smashing earnings so it's one of the easiest longs in my life.

AMKR - I don't have this in my portfolio yet but will be looking to add due to TSM's involvement in Arizona and potential to be a big partner in the US supply chain (as America tries to push TSM toward US fab + manufacturing).

WLAC - Neocloud SPAC IPO, large upside. I talk about this a lot recently, but it's probably one of the best valued Neoclouds out there, and already has great profit margins (not a pivot from miners, where it's a bit more uncertain). They work with Fluidstack, and I'd expect a 500%+ re-rating on top of a Mag7 contract.

AMZN - $213 is insane lol. I have no clue how this is down -3% YTD during a bull market.

LTC - Affected by crypto liquidations and government shutdown delaying ETFs. Great time to buy and just wait for ETF to be approved.

RDDT - Great dip to $190. I thought $200 would be a bottom but ended up going lower. The news about ChatGPT citing it less caused a large sell-off which I think was very immaterial.

HIMS - 14%+ drop off CEO share sale. Owners sell shares all the time, it doesn't really affect the fundamentals of the company much, just short term sentiment. I'd expect it to rebound.

IBIT - Bitcoin $108k great entry point, it's been swinging between $110k - $120k for awhile so anything under is usually great.

ALAB - I said this last time but it sold off way too much from news of a new competitor. It's already competing vs AVGO in the market lol, NVDA-like margins, growing hundreds of percent Y/Y, Mag7 using them in data center buildout. 

CRDO - Similar thesis to ALAB, sold off alongside Astera but a bit less.

SMCI - Should get re-rated for 55%+ or so revenue growth into next year. I doubted the projections earlier but with the data center growth, it's looking realistic.

FLY - This was a medium lift payload play. People doubt fly's execution but NOC co-developing medium lift takes a lot of risk off the table (and possible re-rating it 500%+ when it competes vs falcon9)

SNAP - Did the math on Snap monetization of memories in an earlier DD post and it's completely not priced in yet. It's doing $1.3B+ quarterly revenue on a $13B market cap lol, and the amount FCF they would get from increasing their revenue + lowering Google OPEX costs is insane.

ETOR  - Majority cash, growing at IBKR rates, suffering from tax harvesting

LULU - Suffering from tax harvesting + competition from Alo, Vuori, etc. But seasonally should be good, and extremely low p/e now.

Buy
AMD - ChatGPT putting in AMD orders, ORCL building out AMD data centers. Likely going to get a re-rating in the next year as a potential $NVDA competitor. Still think Nvidia will dominate but with it's 4.5T marketcap, AMD has a lot to catch up on even if it takes a small percent share.

HOOD - Looking at a lot better after the 10%+ correction. Could pull a PLTR

RBRK - Did DD on this earlier, looks better on the drop as a cybersecurity company really low multiples in the space. Just needs to cut back on marketing, customers sticky. 

UNH - Healthcare is sht in America but not going anywhere. Think Warren and the others know this 

TGT 🐈 - Dividend next moth, big dividend stock. Around now is a good time to load up IMO

IREN 🐈 - Huge GW, expect mag7 or similar deal. 

WYFI - Any neocloud is a buy (eg. see thesis on mag7 funneling revenue down toward these small 1B-5B companies)

WULF - neocloud play

CIFR - neocloud play

SLNH - neocloud play

BITF - neocloud play

GLXY - neocloud derivative play

FLNC - neocloud energy play

MU - China derisked, memory had a huge market there, memory also likely going to get re-rating in tdata center buildout

_

Sell

ETH - Not a fan of Ethereum at $4k+
BMNR - If I don't like Ethereum at these levels, no point of holding treasury companies 
PL - Low revenue, space stock (extremely high valuation)
BLSKY -Low revenue, space stock (extremely high valuation)
RGTI - Quantum bubble
OKLO - Nuclear bubble
IONQ -Quantum bubble 
QBTS - Quantum bubble

_

Quick macro heads up:
-> Rate cut in 9 days ~97% odds. Frontrunning expected, go long.  That's all.
```

### [亏损 #12] GLXY long hz=6m — pub=2025-10-15T07:42:21
- entry=2025-10-16, $42.39
- 1m: **resolved_miss** raw=-37.86% bench=+1.71% excess=-39.57%
- 3m: excess=-26.84%  6m: excess=-47.72%
- **条件 label**: ['PRICE_TARGET']
- **if 句**: ['This would be a $3T company if this were a US company, insane profit margins, insane growth rate for their size', '5T), even if buying at ATHs', "AMZN hitting $213-215 today was a good chance to stock up since it usually floats between $218-$227 if you're short term swing trading but long term I'd expect it to catchup to other mag7"]
- **原文 (全文)**:
```
The Great Soybean/Seed Oil Crash, personal thoughts and explanations:

Strong Buy
$ALAB
$CRDO
$NBIS
$WLAC
$LTC
$TSM
$BTC
(+ same as tax harvest stocks last time)
$AMZN
$SMCI
_

Buy
$AMD
$FLNC
$SEI
$BZAI
$NKLR
$IREN
$WULF
$CIFR
$CRWV
$BITF
$WYFI
$SLNH
$BITF
$RBRK
$GLXY
$GRAB
$SEA
$META
$TGT
$SNAP
$MU
$RKLB
$FLY
$UNH

Hold
$MP
$HOOD
$EOSE
$NVDA
$GOOGL
$DFLI
$SOFI
$VIRT
$RR
$AVGO
$BE
$ASTS

(Hit the ticker maximum but everything else from last post, still sell on Quantum or Oklo)
_

Strong Buys
ALAB - Huge part of datacenter buildout, NVDA like margins, Mag7 customers. Already had competitors from AVGO,  really don't think Arista would be a competitive threat.

CRDO - Same sell-off as ALAB, thought they were both kind of overvalued before, but now they're back in correction territory so good to stock up.

NBIS - $400 PT bull case. We have macro tailwind from government re-opening + rate cut EOM october into earnings, so short term looks promising. Lot of things going for it (eg. meta x crwv, so there's potential for more mag7 clients), sum of parts doing well, eg. clickhouse, and scaling rev from $100m to $1.5B+ a quarter is insane. there's already contracts locked in its just a matter of company execution.

WLAC - Wrote a thesis about this earlier at $13. Even at $14.5 strong because it can re-rate 100%+ easily.

LTC - Affected by leverage traders and government shutdown. The shutdown is predicted to last awhile and the main reason to buy was the ETF getting approved. But a great buy sub <$100 anyway, because it will get approved in due time (~95% chance).

TSM - Holy crap. This would be a $3T company if this were a US company, insane profit margins, insane growth rate for their size. And every post you see about OpenAi X (**sydney sweeney partnership) or AMD buildout/NVDA buildout. TSM is the center of it all and would easily be a $2T+ company (from here at ~$1.5T), even if buying at ATHs.

BTC - $112K good entry point. Goldt keeps hitting ATH, nothing really changed fundamentally, just lot of liquidations recently
(+ same as tax harvest stocks last time)

AMZN - I really don't know how it's still down YTD. I don't think Amazon needs much explaining but still growing  (eg. AWS backlog massive, still going like 24% but not as much as ORCL, GCP and others obviously), but with EOY seasonality and runup to Feb, now is probably the best chance to catch the bottom. AMZN hitting $213-215 today was a good chance to stock up since it usually floats between $218-$227 if you're short term swing trading but long term I'd expect it to catchup to other mag7.

SMCI - Underrated. Markets were looking short term performance, and Charles was quoting like 55%+ Y/Y forward revenue growth which nobody believed + backlog that didnt get realized yet. But now with all the data center buildouts, now it's kinda making sense. So should re-rate in the next two earnings.

_
Buy

AMD - So many deals from OpenAI x AMD, oracle building out with AMD, this is going to re-rate to a potential $1T+ company if it's actually a strong competitive to $NVDA.  I don't think it's winner takes all and you can see a $4.5T+ market cap size with NVDA and some $350B marketcap size with AMD, so we can see a large ramp up (OpenAI is usually the leader in frontier models and if Sam says they can use AMD chips + elon said its' good for small-medium weight models, prboably means something positive)

FLNC - Strong re-rate on energy after AI consumption, great buy.

SEI - Strong re-rate on energy after AI consumption, great buy.

BZAI - Someone else did a DD on this company, just cause of sector and shift to edge compute (eg. Robotics goign to be hot). Because of low MC and runup of similar companies could turn out well.

NKLR - Nuclear stocks like $OKLO have been taking off, this is just follow the lader.

IREN - Needs no introduction, huge GW compute capacity just no announced mag7 deals yet but could come anytime -> strong re-rate. Only reason not a strong buy is because not fully convinced miners can pivot like CRWV and maintain great margins (eg. $ORCL hit piece) but we'll see.

WULF - GOOGL backlog, another $3.6+ or so in funding helps a lot.

CIFR - Lot of info on X about future capacity and strong re-rating. Always liked this company because it was NBIS-lite. You can probably buy any Neocloud and it will go up because the sector is incredibly high potential with Mag7 funneling revenue.

CRWV - Didn't like this as much as others because of debt but because of the seed oil correction much better buy point at $134 (below when META deal was announced)

BITF - Same in Neocloud category

WYFI - Same in Neocloud category

BITF - Same in Neocloud category

GLXY - Same in Neocloud category, helps with their buildout

RBRK - Did a DD on this, great buy for cybersecurity sector in mid term, they just need to scale back marketing and then it looks like they have a lot more FCF because they're spending most OPEX on marketing.

GRAB - Great fundamentally, -6.56% correction good to buy again

SEA - AMZN in SEA, tons of people use them. Just a buy just because of costumer base + monetization potenetial. Fundamentally growing $5B+ rev 38% Y/Y is also great.

META - I really don't like all their expensive capex on AI since they're not really putting out fronteir models like ChatGPT with it, who knows what Zuck is doing. But that aside, down 7.3% over the month, going to $700 support, probably a good buy around here to play catchup.

TGT - Dividend next month good catalyst.

SNAP - The Jenners are coming back (helps with popularity), they're shifting former memory opex to revenue, and this will probably cause a HUGE rerating next year. Just suffers from tax harvesting otherwise would be a strong buy rn. Usually tax harvesting events are kinda done in December.

MU - Now that China fears are kinda less intense, MU is a lot stronger buy just cause of memory use on buildout.

RKLB - Neutron, golden dome contracts, lot of cataylsts

FLY - Medium lift

UNH - Healthcare stock not affected by soybeans but had a correction. Would likely go up one instituions post their ports (eg. warren likely bought more)

Random thoughts
Basically any growth/risk stock that's not named Oklo is great because we have

-> Rate Cut end of month October
-> Government re-opening sometime (likely around end of Oct or early Nov)

Into
-> Rate Cut December.
-> Midterms (Bullish for stocks)

Usually market crashes happen when there's tightening not easing. And your stupid quantum bubbles would likely continue for another 3-12 months afterward. If you're short, then probably wait till next Feb.

Anyway, this is a great time for risk-on, and specially riding trends with neoclouds -> affiliated sectors (eg. energy) -> affiliated companies (eg. smci, tsm, etc).

I half joke-about soybeans because it likely signed escalating tensions, but I'd probably see a run-up into next year. Also I could write up a lot about each one but it's pretty time consuming but I'll put on a thesis post about random ones eg. $RBRK, from time to time.

Space/robotics/energy/quantum/ai/semi/critical top verticals right now, don't fight against momentum. I can think something is overvalued (eg. some critical materials bc. it's still spectulative compared to neoclouds that kinda have guaranteed rev based on execution from mag7) but I wouldn't short it into rate cuts.

Just personal thoughts, NFA
```

### [亏损 #13] RKLB long hz=6m — pub=2025-10-15T07:42:21
- entry=2025-10-16, $70.07
- 1m: **resolved_miss** raw=-35.01% bench=+1.71% excess=-36.72%
- 3m: excess=+24.68%  6m: excess=+17.07%
- **条件 label**: ['PRICE_TARGET']
- **if 句**: ['This would be a $3T company if this were a US company, insane profit margins, insane growth rate for their size', '5T), even if buying at ATHs', "AMZN hitting $213-215 today was a good chance to stock up since it usually floats between $218-$227 if you're short term swing trading but long term I'd expect it to catchup to other mag7"]
- **原文 (全文)**:
```
The Great Soybean/Seed Oil Crash, personal thoughts and explanations:

Strong Buy
$ALAB
$CRDO
$NBIS
$WLAC
$LTC
$TSM
$BTC
(+ same as tax harvest stocks last time)
$AMZN
$SMCI
_

Buy
$AMD
$FLNC
$SEI
$BZAI
$NKLR
$IREN
$WULF
$CIFR
$CRWV
$BITF
$WYFI
$SLNH
$BITF
$RBRK
$GLXY
$GRAB
$SEA
$META
$TGT
$SNAP
$MU
$RKLB
$FLY
$UNH

Hold
$MP
$HOOD
$EOSE
$NVDA
$GOOGL
$DFLI
$SOFI
$VIRT
$RR
$AVGO
$BE
$ASTS

(Hit the ticker maximum but everything else from last post, still sell on Quantum or Oklo)
_

Strong Buys
ALAB - Huge part of datacenter buildout, NVDA like margins, Mag7 customers. Already had competitors from AVGO,  really don't think Arista would be a competitive threat.

CRDO - Same sell-off as ALAB, thought they were both kind of overvalued before, but now they're back in correction territory so good to stock up.

NBIS - $400 PT bull case. We have macro tailwind from government re-opening + rate cut EOM october into earnings, so short term looks promising. Lot of things going for it (eg. meta x crwv, so there's potential for more mag7 clients), sum of parts doing well, eg. clickhouse, and scaling rev from $100m to $1.5B+ a quarter is insane. there's already contracts locked in its just a matter of company execution.

WLAC - Wrote a thesis about this earlier at $13. Even at $14.5 strong because it can re-rate 100%+ easily.

LTC - Affected by leverage traders and government shutdown. The shutdown is predicted to last awhile and the main reason to buy was the ETF getting approved. But a great buy sub <$100 anyway, because it will get approved in due time (~95% chance).

TSM - Holy crap. This would be a $3T company if this were a US company, insane profit margins, insane growth rate for their size. And every post you see about OpenAi X (**sydney sweeney partnership) or AMD buildout/NVDA buildout. TSM is the center of it all and would easily be a $2T+ company (from here at ~$1.5T), even if buying at ATHs.

BTC - $112K good entry point. Goldt keeps hitting ATH, nothing really changed fundamentally, just lot of liquidations recently
(+ same as tax harvest stocks last time)

AMZN - I really don't know how it's still down YTD. I don't think Amazon needs much explaining but still growing  (eg. AWS backlog massive, still going like 24% but not as much as ORCL, GCP and others obviously), but with EOY seasonality and runup to Feb, now is probably the best chance to catch the bottom. AMZN hitting $213-215 today was a good chance to stock up since it usually floats between $218-$227 if you're short term swing trading but long term I'd expect it to catchup to other mag7.

SMCI - Underrated. Markets were looking short term performance, and Charles was quoting like 55%+ Y/Y forward revenue growth which nobody believed + backlog that didnt get realized yet. But now with all the data center buildouts, now it's kinda making sense. So should re-rate in the next two earnings.

_
Buy

AMD - So many deals from OpenAI x AMD, oracle building out with AMD, this is going to re-rate to a potential $1T+ company if it's actually a strong competitive to $NVDA.  I don't think it's winner takes all and you can see a $4.5T+ market cap size with NVDA and some $350B marketcap size with AMD, so we can see a large ramp up (OpenAI is usually the leader in frontier models and if Sam says they can use AMD chips + elon said its' good for small-medium weight models, prboably means something positive)

FLNC - Strong re-rate on energy after AI consumption, great buy.

SEI - Strong re-rate on energy after AI consumption, great buy.

BZAI - Someone else did a DD on this company, just cause of sector and shift to edge compute (eg. Robotics goign to be hot). Because of low MC and runup of similar companies could turn out well.

NKLR - Nuclear stocks like $OKLO have been taking off, this is just follow the lader.

IREN - Needs no introduction, huge GW compute capacity just no announced mag7 deals yet but could come anytime -> strong re-rate. Only reason not a strong buy is because not fully convinced miners can pivot like CRWV and maintain great margins (eg. $ORCL hit piece) but we'll see.

WULF - GOOGL backlog, another $3.6+ or so in funding helps a lot.

CIFR - Lot of info on X about future capacity and strong re-rating. Always liked this company because it was NBIS-lite. You can probably buy any Neocloud and it will go up because the sector is incredibly high potential with Mag7 funneling revenue.

CRWV - Didn't like this as much as others because of debt but because of the seed oil correction much better buy point at $134 (below when META deal was announced)

BITF - Same in Neocloud category

WYFI - Same in Neocloud category

BITF - Same in Neocloud category

GLXY - Same in Neocloud category, helps with their buildout

RBRK - Did a DD on this, great buy for cybersecurity sector in mid term, they just need to scale back marketing and then it looks like they have a lot more FCF because they're spending most OPEX on marketing.

GRAB - Great fundamentally, -6.56% correction good to buy again

SEA - AMZN in SEA, tons of people use them. Just a buy just because of costumer base + monetization potenetial. Fundamentally growing $5B+ rev 38% Y/Y is also great.

META - I really don't like all their expensive capex on AI since they're not really putting out fronteir models like ChatGPT with it, who knows what Zuck is doing. But that aside, down 7.3% over the month, going to $700 support, probably a good buy around here to play catchup.

TGT - Dividend next month good catalyst.

SNAP - The Jenners are coming back (helps with popularity), they're shifting former memory opex to revenue, and this will probably cause a HUGE rerating next year. Just suffers from tax harvesting otherwise would be a strong buy rn. Usually tax harvesting events are kinda done in December.

MU - Now that China fears are kinda less intense, MU is a lot stronger buy just cause of memory use on buildout.

RKLB - Neutron, golden dome contracts, lot of cataylsts

FLY - Medium lift

UNH - Healthcare stock not affected by soybeans but had a correction. Would likely go up one instituions post their ports (eg. warren likely bought more)

Random thoughts
Basically any growth/risk stock that's not named Oklo is great because we have

-> Rate Cut end of month October
-> Government re-opening sometime (likely around end of Oct or early Nov)

Into
-> Rate Cut December.
-> Midterms (Bullish for stocks)

Usually market crashes happen when there's tightening not easing. And your stupid quantum bubbles would likely continue for another 3-12 months afterward. If you're short, then probably wait till next Feb.

Anyway, this is a great time for risk-on, and specially riding trends with neoclouds -> affiliated sectors (eg. energy) -> affiliated companies (eg. smci, tsm, etc).

I half joke-about soybeans because it likely signed escalating tensions, but I'd probably see a run-up into next year. Also I could write up a lot about each one but it's pretty time consuming but I'll put on a thesis post about random ones eg. $RBRK, from time to time.

Space/robotics/energy/quantum/ai/semi/critical top verticals right now, don't fight against momentum. I can think something is overvalued (eg. some critical materials bc. it's still spectulative compared to neoclouds that kinda have guaranteed rev based on execution from mag7) but I wouldn't short it into rate cuts.

Just personal thoughts, NFA
```

### [亏损 #14] NBIS long hz=6m — pub=2025-10-15T07:42:21
- entry=2025-10-16, $128.09
- 1m: **resolved_miss** raw=-34.78% bench=+1.71% excess=-36.49%
- 3m: excess=-25.05%  6m: excess=+15.64%
- **条件 label**: ['PRICE_TARGET']
- **if 句**: ['This would be a $3T company if this were a US company, insane profit margins, insane growth rate for their size', '5T), even if buying at ATHs', "AMZN hitting $213-215 today was a good chance to stock up since it usually floats between $218-$227 if you're short term swing trading but long term I'd expect it to catchup to other mag7"]
- **原文 (全文)**:
```
The Great Soybean/Seed Oil Crash, personal thoughts and explanations:

Strong Buy
$ALAB
$CRDO
$NBIS
$WLAC
$LTC
$TSM
$BTC
(+ same as tax harvest stocks last time)
$AMZN
$SMCI
_

Buy
$AMD
$FLNC
$SEI
$BZAI
$NKLR
$IREN
$WULF
$CIFR
$CRWV
$BITF
$WYFI
$SLNH
$BITF
$RBRK
$GLXY
$GRAB
$SEA
$META
$TGT
$SNAP
$MU
$RKLB
$FLY
$UNH

Hold
$MP
$HOOD
$EOSE
$NVDA
$GOOGL
$DFLI
$SOFI
$VIRT
$RR
$AVGO
$BE
$ASTS

(Hit the ticker maximum but everything else from last post, still sell on Quantum or Oklo)
_

Strong Buys
ALAB - Huge part of datacenter buildout, NVDA like margins, Mag7 customers. Already had competitors from AVGO,  really don't think Arista would be a competitive threat.

CRDO - Same sell-off as ALAB, thought they were both kind of overvalued before, but now they're back in correction territory so good to stock up.

NBIS - $400 PT bull case. We have macro tailwind from government re-opening + rate cut EOM october into earnings, so short term looks promising. Lot of things going for it (eg. meta x crwv, so there's potential for more mag7 clients), sum of parts doing well, eg. clickhouse, and scaling rev from $100m to $1.5B+ a quarter is insane. there's already contracts locked in its just a matter of company execution.

WLAC - Wrote a thesis about this earlier at $13. Even at $14.5 strong because it can re-rate 100%+ easily.

LTC - Affected by leverage traders and government shutdown. The shutdown is predicted to last awhile and the main reason to buy was the ETF getting approved. But a great buy sub <$100 anyway, because it will get approved in due time (~95% chance).

TSM - Holy crap. This would be a $3T company if this were a US company, insane profit margins, insane growth rate for their size. And every post you see about OpenAi X (**sydney sweeney partnership) or AMD buildout/NVDA buildout. TSM is the center of it all and would easily be a $2T+ company (from here at ~$1.5T), even if buying at ATHs.

BTC - $112K good entry point. Goldt keeps hitting ATH, nothing really changed fundamentally, just lot of liquidations recently
(+ same as tax harvest stocks last time)

AMZN - I really don't know how it's still down YTD. I don't think Amazon needs much explaining but still growing  (eg. AWS backlog massive, still going like 24% but not as much as ORCL, GCP and others obviously), but with EOY seasonality and runup to Feb, now is probably the best chance to catch the bottom. AMZN hitting $213-215 today was a good chance to stock up since it usually floats between $218-$227 if you're short term swing trading but long term I'd expect it to catchup to other mag7.

SMCI - Underrated. Markets were looking short term performance, and Charles was quoting like 55%+ Y/Y forward revenue growth which nobody believed + backlog that didnt get realized yet. But now with all the data center buildouts, now it's kinda making sense. So should re-rate in the next two earnings.

_
Buy

AMD - So many deals from OpenAI x AMD, oracle building out with AMD, this is going to re-rate to a potential $1T+ company if it's actually a strong competitive to $NVDA.  I don't think it's winner takes all and you can see a $4.5T+ market cap size with NVDA and some $350B marketcap size with AMD, so we can see a large ramp up (OpenAI is usually the leader in frontier models and if Sam says they can use AMD chips + elon said its' good for small-medium weight models, prboably means something positive)

FLNC - Strong re-rate on energy after AI consumption, great buy.

SEI - Strong re-rate on energy after AI consumption, great buy.

BZAI - Someone else did a DD on this company, just cause of sector and shift to edge compute (eg. Robotics goign to be hot). Because of low MC and runup of similar companies could turn out well.

NKLR - Nuclear stocks like $OKLO have been taking off, this is just follow the lader.

IREN - Needs no introduction, huge GW compute capacity just no announced mag7 deals yet but could come anytime -> strong re-rate. Only reason not a strong buy is because not fully convinced miners can pivot like CRWV and maintain great margins (eg. $ORCL hit piece) but we'll see.

WULF - GOOGL backlog, another $3.6+ or so in funding helps a lot.

CIFR - Lot of info on X about future capacity and strong re-rating. Always liked this company because it was NBIS-lite. You can probably buy any Neocloud and it will go up because the sector is incredibly high potential with Mag7 funneling revenue.

CRWV - Didn't like this as much as others because of debt but because of the seed oil correction much better buy point at $134 (below when META deal was announced)

BITF - Same in Neocloud category

WYFI - Same in Neocloud category

BITF - Same in Neocloud category

GLXY - Same in Neocloud category, helps with their buildout

RBRK - Did a DD on this, great buy for cybersecurity sector in mid term, they just need to scale back marketing and then it looks like they have a lot more FCF because they're spending most OPEX on marketing.

GRAB - Great fundamentally, -6.56% correction good to buy again

SEA - AMZN in SEA, tons of people use them. Just a buy just because of costumer base + monetization potenetial. Fundamentally growing $5B+ rev 38% Y/Y is also great.

META - I really don't like all their expensive capex on AI since they're not really putting out fronteir models like ChatGPT with it, who knows what Zuck is doing. But that aside, down 7.3% over the month, going to $700 support, probably a good buy around here to play catchup.

TGT - Dividend next month good catalyst.

SNAP - The Jenners are coming back (helps with popularity), they're shifting former memory opex to revenue, and this will probably cause a HUGE rerating next year. Just suffers from tax harvesting otherwise would be a strong buy rn. Usually tax harvesting events are kinda done in December.

MU - Now that China fears are kinda less intense, MU is a lot stronger buy just cause of memory use on buildout.

RKLB - Neutron, golden dome contracts, lot of cataylsts

FLY - Medium lift

UNH - Healthcare stock not affected by soybeans but had a correction. Would likely go up one instituions post their ports (eg. warren likely bought more)

Random thoughts
Basically any growth/risk stock that's not named Oklo is great because we have

-> Rate Cut end of month October
-> Government re-opening sometime (likely around end of Oct or early Nov)

Into
-> Rate Cut December.
-> Midterms (Bullish for stocks)

Usually market crashes happen when there's tightening not easing. And your stupid quantum bubbles would likely continue for another 3-12 months afterward. If you're short, then probably wait till next Feb.

Anyway, this is a great time for risk-on, and specially riding trends with neoclouds -> affiliated sectors (eg. energy) -> affiliated companies (eg. smci, tsm, etc).

I half joke-about soybeans because it likely signed escalating tensions, but I'd probably see a run-up into next year. Also I could write up a lot about each one but it's pretty time consuming but I'll put on a thesis post about random ones eg. $RBRK, from time to time.

Space/robotics/energy/quantum/ai/semi/critical top verticals right now, don't fight against momentum. I can think something is overvalued (eg. some critical materials bc. it's still spectulative compared to neoclouds that kinda have guaranteed rev based on execution from mag7) but I wouldn't short it into rate cuts.

Just personal thoughts, NFA
```

### [亏损 #15] SMCI long hz=long_term — pub=2025-10-19T18:21:35
- entry=2025-10-20, $55.04
- 1m: **resolved_miss** raw=-36.59% bench=-1.67% excess=-34.92%
- 3m: excess=-43.68%  6m: excess=-56.93%
- **条件 label**: ['PRICE_TARGET']
- **if 句**: ['5T marketcap, AMD has a lot to catch up on even if it takes a small percent share', "BMNR - If I don't like Ethereum at these levels, no point of holding treasury companies"]
- **原文 (全文)**:
```
October 20th, Important Rate Cut Trading Week.

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
$ETH
$BMNR
$PL
$BLSKY
$RGTI
$OKLO
$IONQ
$QBTS

_

So macro wise, we are 9 days away from (~97% or so rate cut). Market is in fear mode. This is the ideal time to go long and not cut positions.

Fire Sale
_

$NBIS - Needs no explanation, I still maintain $400 PT on a bull case 2026 due to 4-6B+ forward revenue off ~60-75% gross margins, and another likely hyperscaler contract (eg. $META)

What happened on the 10%+ drop on Friday was mechanical hedging and MM Pinning. You can see this with the price stuck at $113.5, despite any volatility. 

I'd expect short hedges to unwind Monday (given MMs bought puts and were short calls -> heavy short into expiration) and price to go back up. I ended up buying 6 figures worth of calls on the drop as there was no material changes.

Strong Buy

TSM - Holy crap, please have this in your portfolio. This is a money printer, and scaling your revenue by 38-40% every year WHILE increasing gross margins is just insane. It dipped as well after smashing earnings so it's one of the easiest longs in my life.

AMKR - I don't have this in my portfolio yet but will be looking to add due to TSM's involvement in Arizona and potential to be a big partner in the US supply chain (as America tries to push TSM toward US fab + manufacturing).

WLAC - Neocloud SPAC IPO, large upside. I talk about this a lot recently, but it's probably one of the best valued Neoclouds out there, and already has great profit margins (not a pivot from miners, where it's a bit more uncertain). They work with Fluidstack, and I'd expect a 500%+ re-rating on top of a Mag7 contract.

AMZN - $213 is insane lol. I have no clue how this is down -3% YTD during a bull market.

LTC - Affected by crypto liquidations and government shutdown delaying ETFs. Great time to buy and just wait for ETF to be approved.

RDDT - Great dip to $190. I thought $200 would be a bottom but ended up going lower. The news about ChatGPT citing it less caused a large sell-off which I think was very immaterial.

HIMS - 14%+ drop off CEO share sale. Owners sell shares all the time, it doesn't really affect the fundamentals of the company much, just short term sentiment. I'd expect it to rebound.

IBIT - Bitcoin $108k great entry point, it's been swinging between $110k - $120k for awhile so anything under is usually great.

ALAB - I said this last time but it sold off way too much from news of a new competitor. It's already competing vs AVGO in the market lol, NVDA-like margins, growing hundreds of percent Y/Y, Mag7 using them in data center buildout. 

CRDO - Similar thesis to ALAB, sold off alongside Astera but a bit less.

SMCI - Should get re-rated for 55%+ or so revenue growth into next year. I doubted the projections earlier but with the data center growth, it's looking realistic.

FLY - This was a medium lift payload play. People doubt fly's execution but NOC co-developing medium lift takes a lot of risk off the table (and possible re-rating it 500%+ when it competes vs falcon9)

SNAP - Did the math on Snap monetization of memories in an earlier DD post and it's completely not priced in yet. It's doing $1.3B+ quarterly revenue on a $13B market cap lol, and the amount FCF they would get from increasing their revenue + lowering Google OPEX costs is insane.

ETOR  - Majority cash, growing at IBKR rates, suffering from tax harvesting

LULU - Suffering from tax harvesting + competition from Alo, Vuori, etc. But seasonally should be good, and extremely low p/e now.

Buy
AMD - ChatGPT putting in AMD orders, ORCL building out AMD data centers. Likely going to get a re-rating in the next year as a potential $NVDA competitor. Still think Nvidia will dominate but with it's 4.5T marketcap, AMD has a lot to catch up on even if it takes a small percent share.

HOOD - Looking at a lot better after the 10%+ correction. Could pull a PLTR

RBRK - Did DD on this earlier, looks better on the drop as a cybersecurity company really low multiples in the space. Just needs to cut back on marketing, customers sticky. 

UNH - Healthcare is sht in America but not going anywhere. Think Warren and the others know this 

TGT 🐈 - Dividend next moth, big dividend stock. Around now is a good time to load up IMO

IREN 🐈 - Huge GW, expect mag7 or similar deal. 

WYFI - Any neocloud is a buy (eg. see thesis on mag7 funneling revenue down toward these small 1B-5B companies)

WULF - neocloud play

CIFR - neocloud play

SLNH - neocloud play

BITF - neocloud play

GLXY - neocloud derivative play

FLNC - neocloud energy play

MU - China derisked, memory had a huge market there, memory also likely going to get re-rating in tdata center buildout

_

Sell

ETH - Not a fan of Ethereum at $4k+
BMNR - If I don't like Ethereum at these levels, no point of holding treasury companies 
PL - Low revenue, space stock (extremely high valuation)
BLSKY -Low revenue, space stock (extremely high valuation)
RGTI - Quantum bubble
OKLO - Nuclear bubble
IONQ -Quantum bubble 
QBTS - Quantum bubble

_

Quick macro heads up:
-> Rate cut in 9 days ~97% odds. Frontrunning expected, go long.  That's all.
```

### [亏损 #16] IREN long hz=6m — pub=2025-10-15T07:42:21
- entry=2025-10-16, $68.94
- 1m: **resolved_miss** raw=-32.74% bench=+1.71% excess=-34.45%
- 3m: excess=-23.86%  6m: excess=-41.05%
- **条件 label**: ['PRICE_TARGET']
- **if 句**: ['This would be a $3T company if this were a US company, insane profit margins, insane growth rate for their size', '5T), even if buying at ATHs', "AMZN hitting $213-215 today was a good chance to stock up since it usually floats between $218-$227 if you're short term swing trading but long term I'd expect it to catchup to other mag7"]
- **原文 (全文)**:
```
The Great Soybean/Seed Oil Crash, personal thoughts and explanations:

Strong Buy
$ALAB
$CRDO
$NBIS
$WLAC
$LTC
$TSM
$BTC
(+ same as tax harvest stocks last time)
$AMZN
$SMCI
_

Buy
$AMD
$FLNC
$SEI
$BZAI
$NKLR
$IREN
$WULF
$CIFR
$CRWV
$BITF
$WYFI
$SLNH
$BITF
$RBRK
$GLXY
$GRAB
$SEA
$META
$TGT
$SNAP
$MU
$RKLB
$FLY
$UNH

Hold
$MP
$HOOD
$EOSE
$NVDA
$GOOGL
$DFLI
$SOFI
$VIRT
$RR
$AVGO
$BE
$ASTS

(Hit the ticker maximum but everything else from last post, still sell on Quantum or Oklo)
_

Strong Buys
ALAB - Huge part of datacenter buildout, NVDA like margins, Mag7 customers. Already had competitors from AVGO,  really don't think Arista would be a competitive threat.

CRDO - Same sell-off as ALAB, thought they were both kind of overvalued before, but now they're back in correction territory so good to stock up.

NBIS - $400 PT bull case. We have macro tailwind from government re-opening + rate cut EOM october into earnings, so short term looks promising. Lot of things going for it (eg. meta x crwv, so there's potential for more mag7 clients), sum of parts doing well, eg. clickhouse, and scaling rev from $100m to $1.5B+ a quarter is insane. there's already contracts locked in its just a matter of company execution.

WLAC - Wrote a thesis about this earlier at $13. Even at $14.5 strong because it can re-rate 100%+ easily.

LTC - Affected by leverage traders and government shutdown. The shutdown is predicted to last awhile and the main reason to buy was the ETF getting approved. But a great buy sub <$100 anyway, because it will get approved in due time (~95% chance).

TSM - Holy crap. This would be a $3T company if this were a US company, insane profit margins, insane growth rate for their size. And every post you see about OpenAi X (**sydney sweeney partnership) or AMD buildout/NVDA buildout. TSM is the center of it all and would easily be a $2T+ company (from here at ~$1.5T), even if buying at ATHs.

BTC - $112K good entry point. Goldt keeps hitting ATH, nothing really changed fundamentally, just lot of liquidations recently
(+ same as tax harvest stocks last time)

AMZN - I really don't know how it's still down YTD. I don't think Amazon needs much explaining but still growing  (eg. AWS backlog massive, still going like 24% but not as much as ORCL, GCP and others obviously), but with EOY seasonality and runup to Feb, now is probably the best chance to catch the bottom. AMZN hitting $213-215 today was a good chance to stock up since it usually floats between $218-$227 if you're short term swing trading but long term I'd expect it to catchup to other mag7.

SMCI - Underrated. Markets were looking short term performance, and Charles was quoting like 55%+ Y/Y forward revenue growth which nobody believed + backlog that didnt get realized yet. But now with all the data center buildouts, now it's kinda making sense. So should re-rate in the next two earnings.

_
Buy

AMD - So many deals from OpenAI x AMD, oracle building out with AMD, this is going to re-rate to a potential $1T+ company if it's actually a strong competitive to $NVDA.  I don't think it's winner takes all and you can see a $4.5T+ market cap size with NVDA and some $350B marketcap size with AMD, so we can see a large ramp up (OpenAI is usually the leader in frontier models and if Sam says they can use AMD chips + elon said its' good for small-medium weight models, prboably means something positive)

FLNC - Strong re-rate on energy after AI consumption, great buy.

SEI - Strong re-rate on energy after AI consumption, great buy.

BZAI - Someone else did a DD on this company, just cause of sector and shift to edge compute (eg. Robotics goign to be hot). Because of low MC and runup of similar companies could turn out well.

NKLR - Nuclear stocks like $OKLO have been taking off, this is just follow the lader.

IREN - Needs no introduction, huge GW compute capacity just no announced mag7 deals yet but could come anytime -> strong re-rate. Only reason not a strong buy is because not fully convinced miners can pivot like CRWV and maintain great margins (eg. $ORCL hit piece) but we'll see.

WULF - GOOGL backlog, another $3.6+ or so in funding helps a lot.

CIFR - Lot of info on X about future capacity and strong re-rating. Always liked this company because it was NBIS-lite. You can probably buy any Neocloud and it will go up because the sector is incredibly high potential with Mag7 funneling revenue.

CRWV - Didn't like this as much as others because of debt but because of the seed oil correction much better buy point at $134 (below when META deal was announced)

BITF - Same in Neocloud category

WYFI - Same in Neocloud category

BITF - Same in Neocloud category

GLXY - Same in Neocloud category, helps with their buildout

RBRK - Did a DD on this, great buy for cybersecurity sector in mid term, they just need to scale back marketing and then it looks like they have a lot more FCF because they're spending most OPEX on marketing.

GRAB - Great fundamentally, -6.56% correction good to buy again

SEA - AMZN in SEA, tons of people use them. Just a buy just because of costumer base + monetization potenetial. Fundamentally growing $5B+ rev 38% Y/Y is also great.

META - I really don't like all their expensive capex on AI since they're not really putting out fronteir models like ChatGPT with it, who knows what Zuck is doing. But that aside, down 7.3% over the month, going to $700 support, probably a good buy around here to play catchup.

TGT - Dividend next month good catalyst.

SNAP - The Jenners are coming back (helps with popularity), they're shifting former memory opex to revenue, and this will probably cause a HUGE rerating next year. Just suffers from tax harvesting otherwise would be a strong buy rn. Usually tax harvesting events are kinda done in December.

MU - Now that China fears are kinda less intense, MU is a lot stronger buy just cause of memory use on buildout.

RKLB - Neutron, golden dome contracts, lot of cataylsts

FLY - Medium lift

UNH - Healthcare stock not affected by soybeans but had a correction. Would likely go up one instituions post their ports (eg. warren likely bought more)

Random thoughts
Basically any growth/risk stock that's not named Oklo is great because we have

-> Rate Cut end of month October
-> Government re-opening sometime (likely around end of Oct or early Nov)

Into
-> Rate Cut December.
-> Midterms (Bullish for stocks)

Usually market crashes happen when there's tightening not easing. And your stupid quantum bubbles would likely continue for another 3-12 months afterward. If you're short, then probably wait till next Feb.

Anyway, this is a great time for risk-on, and specially riding trends with neoclouds -> affiliated sectors (eg. energy) -> affiliated companies (eg. smci, tsm, etc).

I half joke-about soybeans because it likely signed escalating tensions, but I'd probably see a run-up into next year. Also I could write up a lot about each one but it's pretty time consuming but I'll put on a thesis post about random ones eg. $RBRK, from time to time.

Space/robotics/energy/quantum/ai/semi/critical top verticals right now, don't fight against momentum. I can think something is overvalued (eg. some critical materials bc. it's still spectulative compared to neoclouds that kinda have guaranteed rev based on execution from mag7) but I wouldn't short it into rate cuts.

Just personal thoughts, NFA
```

### [亏损 #17] SMCI long hz=6m — pub=2025-10-15T07:42:21
- entry=2025-10-16, $54.00
- 1m: **resolved_miss** raw=-32.56% bench=+1.71% excess=-34.26%
- 3m: excess=-44.40%  6m: excess=-53.93%
- **条件 label**: ['PRICE_TARGET']
- **if 句**: ['This would be a $3T company if this were a US company, insane profit margins, insane growth rate for their size', '5T), even if buying at ATHs', "AMZN hitting $213-215 today was a good chance to stock up since it usually floats between $218-$227 if you're short term swing trading but long term I'd expect it to catchup to other mag7"]
- **原文 (全文)**:
```
The Great Soybean/Seed Oil Crash, personal thoughts and explanations:

Strong Buy
$ALAB
$CRDO
$NBIS
$WLAC
$LTC
$TSM
$BTC
(+ same as tax harvest stocks last time)
$AMZN
$SMCI
_

Buy
$AMD
$FLNC
$SEI
$BZAI
$NKLR
$IREN
$WULF
$CIFR
$CRWV
$BITF
$WYFI
$SLNH
$BITF
$RBRK
$GLXY
$GRAB
$SEA
$META
$TGT
$SNAP
$MU
$RKLB
$FLY
$UNH

Hold
$MP
$HOOD
$EOSE
$NVDA
$GOOGL
$DFLI
$SOFI
$VIRT
$RR
$AVGO
$BE
$ASTS

(Hit the ticker maximum but everything else from last post, still sell on Quantum or Oklo)
_

Strong Buys
ALAB - Huge part of datacenter buildout, NVDA like margins, Mag7 customers. Already had competitors from AVGO,  really don't think Arista would be a competitive threat.

CRDO - Same sell-off as ALAB, thought they were both kind of overvalued before, but now they're back in correction territory so good to stock up.

NBIS - $400 PT bull case. We have macro tailwind from government re-opening + rate cut EOM october into earnings, so short term looks promising. Lot of things going for it (eg. meta x crwv, so there's potential for more mag7 clients), sum of parts doing well, eg. clickhouse, and scaling rev from $100m to $1.5B+ a quarter is insane. there's already contracts locked in its just a matter of company execution.

WLAC - Wrote a thesis about this earlier at $13. Even at $14.5 strong because it can re-rate 100%+ easily.

LTC - Affected by leverage traders and government shutdown. The shutdown is predicted to last awhile and the main reason to buy was the ETF getting approved. But a great buy sub <$100 anyway, because it will get approved in due time (~95% chance).

TSM - Holy crap. This would be a $3T company if this were a US company, insane profit margins, insane growth rate for their size. And every post you see about OpenAi X (**sydney sweeney partnership) or AMD buildout/NVDA buildout. TSM is the center of it all and would easily be a $2T+ company (from here at ~$1.5T), even if buying at ATHs.

BTC - $112K good entry point. Goldt keeps hitting ATH, nothing really changed fundamentally, just lot of liquidations recently
(+ same as tax harvest stocks last time)

AMZN - I really don't know how it's still down YTD. I don't think Amazon needs much explaining but still growing  (eg. AWS backlog massive, still going like 24% but not as much as ORCL, GCP and others obviously), but with EOY seasonality and runup to Feb, now is probably the best chance to catch the bottom. AMZN hitting $213-215 today was a good chance to stock up since it usually floats between $218-$227 if you're short term swing trading but long term I'd expect it to catchup to other mag7.

SMCI - Underrated. Markets were looking short term performance, and Charles was quoting like 55%+ Y/Y forward revenue growth which nobody believed + backlog that didnt get realized yet. But now with all the data center buildouts, now it's kinda making sense. So should re-rate in the next two earnings.

_
Buy

AMD - So many deals from OpenAI x AMD, oracle building out with AMD, this is going to re-rate to a potential $1T+ company if it's actually a strong competitive to $NVDA.  I don't think it's winner takes all and you can see a $4.5T+ market cap size with NVDA and some $350B marketcap size with AMD, so we can see a large ramp up (OpenAI is usually the leader in frontier models and if Sam says they can use AMD chips + elon said its' good for small-medium weight models, prboably means something positive)

FLNC - Strong re-rate on energy after AI consumption, great buy.

SEI - Strong re-rate on energy after AI consumption, great buy.

BZAI - Someone else did a DD on this company, just cause of sector and shift to edge compute (eg. Robotics goign to be hot). Because of low MC and runup of similar companies could turn out well.

NKLR - Nuclear stocks like $OKLO have been taking off, this is just follow the lader.

IREN - Needs no introduction, huge GW compute capacity just no announced mag7 deals yet but could come anytime -> strong re-rate. Only reason not a strong buy is because not fully convinced miners can pivot like CRWV and maintain great margins (eg. $ORCL hit piece) but we'll see.

WULF - GOOGL backlog, another $3.6+ or so in funding helps a lot.

CIFR - Lot of info on X about future capacity and strong re-rating. Always liked this company because it was NBIS-lite. You can probably buy any Neocloud and it will go up because the sector is incredibly high potential with Mag7 funneling revenue.

CRWV - Didn't like this as much as others because of debt but because of the seed oil correction much better buy point at $134 (below when META deal was announced)

BITF - Same in Neocloud category

WYFI - Same in Neocloud category

BITF - Same in Neocloud category

GLXY - Same in Neocloud category, helps with their buildout

RBRK - Did a DD on this, great buy for cybersecurity sector in mid term, they just need to scale back marketing and then it looks like they have a lot more FCF because they're spending most OPEX on marketing.

GRAB - Great fundamentally, -6.56% correction good to buy again

SEA - AMZN in SEA, tons of people use them. Just a buy just because of costumer base + monetization potenetial. Fundamentally growing $5B+ rev 38% Y/Y is also great.

META - I really don't like all their expensive capex on AI since they're not really putting out fronteir models like ChatGPT with it, who knows what Zuck is doing. But that aside, down 7.3% over the month, going to $700 support, probably a good buy around here to play catchup.

TGT - Dividend next month good catalyst.

SNAP - The Jenners are coming back (helps with popularity), they're shifting former memory opex to revenue, and this will probably cause a HUGE rerating next year. Just suffers from tax harvesting otherwise would be a strong buy rn. Usually tax harvesting events are kinda done in December.

MU - Now that China fears are kinda less intense, MU is a lot stronger buy just cause of memory use on buildout.

RKLB - Neutron, golden dome contracts, lot of cataylsts

FLY - Medium lift

UNH - Healthcare stock not affected by soybeans but had a correction. Would likely go up one instituions post their ports (eg. warren likely bought more)

Random thoughts
Basically any growth/risk stock that's not named Oklo is great because we have

-> Rate Cut end of month October
-> Government re-opening sometime (likely around end of Oct or early Nov)

Into
-> Rate Cut December.
-> Midterms (Bullish for stocks)

Usually market crashes happen when there's tightening not easing. And your stupid quantum bubbles would likely continue for another 3-12 months afterward. If you're short, then probably wait till next Feb.

Anyway, this is a great time for risk-on, and specially riding trends with neoclouds -> affiliated sectors (eg. energy) -> affiliated companies (eg. smci, tsm, etc).

I half joke-about soybeans because it likely signed escalating tensions, but I'd probably see a run-up into next year. Also I could write up a lot about each one but it's pretty time consuming but I'll put on a thesis post about random ones eg. $RBRK, from time to time.

Space/robotics/energy/quantum/ai/semi/critical top verticals right now, don't fight against momentum. I can think something is overvalued (eg. some critical materials bc. it's still spectulative compared to neoclouds that kinda have guaranteed rev based on execution from mag7) but I wouldn't short it into rate cuts.

Just personal thoughts, NFA
```

### [亏损 #18] NBIS long hz=long_term — pub=2025-10-14T00:01:53
- entry=2025-10-15, $131.90
- 1m: **resolved_miss** raw=-32.81% bench=+1.03% excess=-33.84%
- 3m: excess=-21.55%  6m: excess=+14.12%
- **条件 label**: ['PRICE_TARGET']
- **原文 (全文)**:
```
@Rexxig $NBIS $400 PT on a bull case. It's sitting at $135.

Definitely worth dropping into Nebius at least. Can't really say the same as safely for the rest, but all neoclouds should go up with mag7 funneling revenue down to them.
```

### [亏损 #19] CIFR long hz=6m — pub=2025-10-15T07:42:21
- entry=2025-10-16, $21.11
- 1m: **resolved_miss** raw=-31.98% bench=+1.71% excess=-33.68%
- 3m: excess=-17.68%  6m: excess=-21.12%
- **条件 label**: ['PRICE_TARGET']
- **if 句**: ['This would be a $3T company if this were a US company, insane profit margins, insane growth rate for their size', '5T), even if buying at ATHs', "AMZN hitting $213-215 today was a good chance to stock up since it usually floats between $218-$227 if you're short term swing trading but long term I'd expect it to catchup to other mag7"]
- **原文 (全文)**:
```
The Great Soybean/Seed Oil Crash, personal thoughts and explanations:

Strong Buy
$ALAB
$CRDO
$NBIS
$WLAC
$LTC
$TSM
$BTC
(+ same as tax harvest stocks last time)
$AMZN
$SMCI
_

Buy
$AMD
$FLNC
$SEI
$BZAI
$NKLR
$IREN
$WULF
$CIFR
$CRWV
$BITF
$WYFI
$SLNH
$BITF
$RBRK
$GLXY
$GRAB
$SEA
$META
$TGT
$SNAP
$MU
$RKLB
$FLY
$UNH

Hold
$MP
$HOOD
$EOSE
$NVDA
$GOOGL
$DFLI
$SOFI
$VIRT
$RR
$AVGO
$BE
$ASTS

(Hit the ticker maximum but everything else from last post, still sell on Quantum or Oklo)
_

Strong Buys
ALAB - Huge part of datacenter buildout, NVDA like margins, Mag7 customers. Already had competitors from AVGO,  really don't think Arista would be a competitive threat.

CRDO - Same sell-off as ALAB, thought they were both kind of overvalued before, but now they're back in correction territory so good to stock up.

NBIS - $400 PT bull case. We have macro tailwind from government re-opening + rate cut EOM october into earnings, so short term looks promising. Lot of things going for it (eg. meta x crwv, so there's potential for more mag7 clients), sum of parts doing well, eg. clickhouse, and scaling rev from $100m to $1.5B+ a quarter is insane. there's already contracts locked in its just a matter of company execution.

WLAC - Wrote a thesis about this earlier at $13. Even at $14.5 strong because it can re-rate 100%+ easily.

LTC - Affected by leverage traders and government shutdown. The shutdown is predicted to last awhile and the main reason to buy was the ETF getting approved. But a great buy sub <$100 anyway, because it will get approved in due time (~95% chance).

TSM - Holy crap. This would be a $3T company if this were a US company, insane profit margins, insane growth rate for their size. And every post you see about OpenAi X (**sydney sweeney partnership) or AMD buildout/NVDA buildout. TSM is the center of it all and would easily be a $2T+ company (from here at ~$1.5T), even if buying at ATHs.

BTC - $112K good entry point. Goldt keeps hitting ATH, nothing really changed fundamentally, just lot of liquidations recently
(+ same as tax harvest stocks last time)

AMZN - I really don't know how it's still down YTD. I don't think Amazon needs much explaining but still growing  (eg. AWS backlog massive, still going like 24% but not as much as ORCL, GCP and others obviously), but with EOY seasonality and runup to Feb, now is probably the best chance to catch the bottom. AMZN hitting $213-215 today was a good chance to stock up since it usually floats between $218-$227 if you're short term swing trading but long term I'd expect it to catchup to other mag7.

SMCI - Underrated. Markets were looking short term performance, and Charles was quoting like 55%+ Y/Y forward revenue growth which nobody believed + backlog that didnt get realized yet. But now with all the data center buildouts, now it's kinda making sense. So should re-rate in the next two earnings.

_
Buy

AMD - So many deals from OpenAI x AMD, oracle building out with AMD, this is going to re-rate to a potential $1T+ company if it's actually a strong competitive to $NVDA.  I don't think it's winner takes all and you can see a $4.5T+ market cap size with NVDA and some $350B marketcap size with AMD, so we can see a large ramp up (OpenAI is usually the leader in frontier models and if Sam says they can use AMD chips + elon said its' good for small-medium weight models, prboably means something positive)

FLNC - Strong re-rate on energy after AI consumption, great buy.

SEI - Strong re-rate on energy after AI consumption, great buy.

BZAI - Someone else did a DD on this company, just cause of sector and shift to edge compute (eg. Robotics goign to be hot). Because of low MC and runup of similar companies could turn out well.

NKLR - Nuclear stocks like $OKLO have been taking off, this is just follow the lader.

IREN - Needs no introduction, huge GW compute capacity just no announced mag7 deals yet but could come anytime -> strong re-rate. Only reason not a strong buy is because not fully convinced miners can pivot like CRWV and maintain great margins (eg. $ORCL hit piece) but we'll see.

WULF - GOOGL backlog, another $3.6+ or so in funding helps a lot.

CIFR - Lot of info on X about future capacity and strong re-rating. Always liked this company because it was NBIS-lite. You can probably buy any Neocloud and it will go up because the sector is incredibly high potential with Mag7 funneling revenue.

CRWV - Didn't like this as much as others because of debt but because of the seed oil correction much better buy point at $134 (below when META deal was announced)

BITF - Same in Neocloud category

WYFI - Same in Neocloud category

BITF - Same in Neocloud category

GLXY - Same in Neocloud category, helps with their buildout

RBRK - Did a DD on this, great buy for cybersecurity sector in mid term, they just need to scale back marketing and then it looks like they have a lot more FCF because they're spending most OPEX on marketing.

GRAB - Great fundamentally, -6.56% correction good to buy again

SEA - AMZN in SEA, tons of people use them. Just a buy just because of costumer base + monetization potenetial. Fundamentally growing $5B+ rev 38% Y/Y is also great.

META - I really don't like all their expensive capex on AI since they're not really putting out fronteir models like ChatGPT with it, who knows what Zuck is doing. But that aside, down 7.3% over the month, going to $700 support, probably a good buy around here to play catchup.

TGT - Dividend next month good catalyst.

SNAP - The Jenners are coming back (helps with popularity), they're shifting former memory opex to revenue, and this will probably cause a HUGE rerating next year. Just suffers from tax harvesting otherwise would be a strong buy rn. Usually tax harvesting events are kinda done in December.

MU - Now that China fears are kinda less intense, MU is a lot stronger buy just cause of memory use on buildout.

RKLB - Neutron, golden dome contracts, lot of cataylsts

FLY - Medium lift

UNH - Healthcare stock not affected by soybeans but had a correction. Would likely go up one instituions post their ports (eg. warren likely bought more)

Random thoughts
Basically any growth/risk stock that's not named Oklo is great because we have

-> Rate Cut end of month October
-> Government re-opening sometime (likely around end of Oct or early Nov)

Into
-> Rate Cut December.
-> Midterms (Bullish for stocks)

Usually market crashes happen when there's tightening not easing. And your stupid quantum bubbles would likely continue for another 3-12 months afterward. If you're short, then probably wait till next Feb.

Anyway, this is a great time for risk-on, and specially riding trends with neoclouds -> affiliated sectors (eg. energy) -> affiliated companies (eg. smci, tsm, etc).

I half joke-about soybeans because it likely signed escalating tensions, but I'd probably see a run-up into next year. Also I could write up a lot about each one but it's pretty time consuming but I'll put on a thesis post about random ones eg. $RBRK, from time to time.

Space/robotics/energy/quantum/ai/semi/critical top verticals right now, don't fight against momentum. I can think something is overvalued (eg. some critical materials bc. it's still spectulative compared to neoclouds that kinda have guaranteed rev based on execution from mag7) but I wouldn't short it into rate cuts.

Just personal thoughts, NFA
```

### [亏损 #20] GLXY long hz=long_term — pub=2025-10-19T18:21:35
- entry=2025-10-20, $39.13
- 1m: **resolved_miss** raw=-34.63% bench=-1.67% excess=-32.96%
- 3m: excess=-23.61%  6m: excess=-38.37%
- **条件 label**: ['PRICE_TARGET']
- **if 句**: ['5T marketcap, AMD has a lot to catch up on even if it takes a small percent share', "BMNR - If I don't like Ethereum at these levels, no point of holding treasury companies"]
- **原文 (全文)**:
```
October 20th, Important Rate Cut Trading Week.

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
$ETH
$BMNR
$PL
$BLSKY
$RGTI
$OKLO
$IONQ
$QBTS

_

So macro wise, we are 9 days away from (~97% or so rate cut). Market is in fear mode. This is the ideal time to go long and not cut positions.

Fire Sale
_

$NBIS - Needs no explanation, I still maintain $400 PT on a bull case 2026 due to 4-6B+ forward revenue off ~60-75% gross margins, and another likely hyperscaler contract (eg. $META)

What happened on the 10%+ drop on Friday was mechanical hedging and MM Pinning. You can see this with the price stuck at $113.5, despite any volatility. 

I'd expect short hedges to unwind Monday (given MMs bought puts and were short calls -> heavy short into expiration) and price to go back up. I ended up buying 6 figures worth of calls on the drop as there was no material changes.

Strong Buy

TSM - Holy crap, please have this in your portfolio. This is a money printer, and scaling your revenue by 38-40% every year WHILE increasing gross margins is just insane. It dipped as well after smashing earnings so it's one of the easiest longs in my life.

AMKR - I don't have this in my portfolio yet but will be looking to add due to TSM's involvement in Arizona and potential to be a big partner in the US supply chain (as America tries to push TSM toward US fab + manufacturing).

WLAC - Neocloud SPAC IPO, large upside. I talk about this a lot recently, but it's probably one of the best valued Neoclouds out there, and already has great profit margins (not a pivot from miners, where it's a bit more uncertain). They work with Fluidstack, and I'd expect a 500%+ re-rating on top of a Mag7 contract.

AMZN - $213 is insane lol. I have no clue how this is down -3% YTD during a bull market.

LTC - Affected by crypto liquidations and government shutdown delaying ETFs. Great time to buy and just wait for ETF to be approved.

RDDT - Great dip to $190. I thought $200 would be a bottom but ended up going lower. The news about ChatGPT citing it less caused a large sell-off which I think was very immaterial.

HIMS - 14%+ drop off CEO share sale. Owners sell shares all the time, it doesn't really affect the fundamentals of the company much, just short term sentiment. I'd expect it to rebound.

IBIT - Bitcoin $108k great entry point, it's been swinging between $110k - $120k for awhile so anything under is usually great.

ALAB - I said this last time but it sold off way too much from news of a new competitor. It's already competing vs AVGO in the market lol, NVDA-like margins, growing hundreds of percent Y/Y, Mag7 using them in data center buildout. 

CRDO - Similar thesis to ALAB, sold off alongside Astera but a bit less.

SMCI - Should get re-rated for 55%+ or so revenue growth into next year. I doubted the projections earlier but with the data center growth, it's looking realistic.

FLY - This was a medium lift payload play. People doubt fly's execution but NOC co-developing medium lift takes a lot of risk off the table (and possible re-rating it 500%+ when it competes vs falcon9)

SNAP - Did the math on Snap monetization of memories in an earlier DD post and it's completely not priced in yet. It's doing $1.3B+ quarterly revenue on a $13B market cap lol, and the amount FCF they would get from increasing their revenue + lowering Google OPEX costs is insane.

ETOR  - Majority cash, growing at IBKR rates, suffering from tax harvesting

LULU - Suffering from tax harvesting + competition from Alo, Vuori, etc. But seasonally should be good, and extremely low p/e now.

Buy
AMD - ChatGPT putting in AMD orders, ORCL building out AMD data centers. Likely going to get a re-rating in the next year as a potential $NVDA competitor. Still think Nvidia will dominate but with it's 4.5T marketcap, AMD has a lot to catch up on even if it takes a small percent share.

HOOD - Looking at a lot better after the 10%+ correction. Could pull a PLTR

RBRK - Did DD on this earlier, looks better on the drop as a cybersecurity company really low multiples in the space. Just needs to cut back on marketing, customers sticky. 

UNH - Healthcare is sht in America but not going anywhere. Think Warren and the others know this 

TGT 🐈 - Dividend next moth, big dividend stock. Around now is a good time to load up IMO

IREN 🐈 - Huge GW, expect mag7 or similar deal. 

WYFI - Any neocloud is a buy (eg. see thesis on mag7 funneling revenue down toward these small 1B-5B companies)

WULF - neocloud play

CIFR - neocloud play

SLNH - neocloud play

BITF - neocloud play

GLXY - neocloud derivative play

FLNC - neocloud energy play

MU - China derisked, memory had a huge market there, memory also likely going to get re-rating in tdata center buildout

_

Sell

ETH - Not a fan of Ethereum at $4k+
BMNR - If I don't like Ethereum at these levels, no point of holding treasury companies 
PL - Low revenue, space stock (extremely high valuation)
BLSKY -Low revenue, space stock (extremely high valuation)
RGTI - Quantum bubble
OKLO - Nuclear bubble
IONQ -Quantum bubble 
QBTS - Quantum bubble

_

Quick macro heads up:
-> Rate cut in 9 days ~97% odds. Frontrunning expected, go long.  That's all.
```

### [亏损 #21] MSTR long hz=6m — pub=2025-10-04T01:22:20
- entry=2025-10-06, $362.95
- 1m: **resolved_miss** raw=-31.95% bench=+0.54% excess=-32.49%
- 3m: excess=-58.09%  6m: excess=-65.73%
- **条件 label**: ['PRICE_TARGET']
- **if 句**: ["BMNR - Just buy ETH if you believe in it but I wouldn't buy at ETH at $4500"]
- **原文 (全文)**:
```
Friday Market Close, Personal Thoughts and Explanations:

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

Reddit - Dropped 29% off immaterial news that ChatGPT wasn't citing it as much. Nobody visits Reddit through ChatGPT, good recovery buy off $200 support. 

SNAP - Finally they're doing something that's USEFUL for the first time in many years lol. Tons of Capex was spent on storing photos random drawings people saved 12 years ago taking GBs of space for their insane Google Cloud costs. They're finally monetizing it like Apple. Huge tailwind, should improve net income by a ton next year. 

AMZN - Under $220 now, great buy. AMZN prime Oct 8th, good for seasonality in Nov/Dec.

ETOR - I can't believe this is still $41. 33% cash, 1B+ cash pile growing at IBKR rates. Just suffers from tax harvesting I'd assume it goes up next year. 

NBIS - Strong buy until $150+ or new hyperscaler contract repricing. 

LTC - ETF catalyst delayed from Gov shutdown but should be approved anyway. 

Buys

Upwork - Down 4.5% or so for no reason, should recover

MSTR - BTC close to all time highs, MSTR way off ATHs cause of long btc short MSTR but NAV premium should catch up again from the BTC fomo.

ORCL - Standard rise on great forward earnings, drop for short term option chain, then rise because 14B tiktok deal and large future cloud contracts

TGT - Just undervalued great buy under $93, dividend catalyst next month

CIFR - NBIS light with GOOGL deal.

VIRT - VIX doesn't look like it's going down anytime soon but they're trading at like 6.4 or so forward P/E so it's worth.

CRDO - Good buy on correction with hypescaler buildout

WULF - Hasn't gone up as much as the other neoclouds, googl backlog

SOFI - Corrected, might recover back to ATH given macro tailwind

META - Monthly low good DCA, not as good as AMZN

AVGO - Same as ORCL, might end up like NVDA one day with hyperscaler chips

MRVL - Still down 24% YTD. 

SMCI - Good buy on datacenter buildout + server racks

Dell - Good buy on datacenter buildout + server racks

Hold

Nothing changed

Sell

TSLA - Overvalued, better longs like NBIS

CRCL - I will keep making this argument, but just buy COIN instead. You will get the same 50% revenue sharing but with a crypto exchange + ETF holding income too.  

PLTR - Disconnected from reality

BMNR - Just buy ETH if you believe in it but I wouldn't buy at ETH at $4500.

Strong Sell

RGTI - Disconnected from reality lol

All disconnected from reality, wouldn't short though cause all cult stocks. 
OKLO
QBTS
IONQ
```

### [亏损 #22] WULF long hz=6m — pub=2025-10-15T07:42:21
- entry=2025-10-16, $15.53
- 1m: **resolved_miss** raw=-29.21% bench=+1.71% excess=-30.92%
- 3m: excess=-16.70%  6m: excess=+20.77%
- **条件 label**: ['PRICE_TARGET']
- **if 句**: ['This would be a $3T company if this were a US company, insane profit margins, insane growth rate for their size', '5T), even if buying at ATHs', "AMZN hitting $213-215 today was a good chance to stock up since it usually floats between $218-$227 if you're short term swing trading but long term I'd expect it to catchup to other mag7"]
- **原文 (全文)**:
```
The Great Soybean/Seed Oil Crash, personal thoughts and explanations:

Strong Buy
$ALAB
$CRDO
$NBIS
$WLAC
$LTC
$TSM
$BTC
(+ same as tax harvest stocks last time)
$AMZN
$SMCI
_

Buy
$AMD
$FLNC
$SEI
$BZAI
$NKLR
$IREN
$WULF
$CIFR
$CRWV
$BITF
$WYFI
$SLNH
$BITF
$RBRK
$GLXY
$GRAB
$SEA
$META
$TGT
$SNAP
$MU
$RKLB
$FLY
$UNH

Hold
$MP
$HOOD
$EOSE
$NVDA
$GOOGL
$DFLI
$SOFI
$VIRT
$RR
$AVGO
$BE
$ASTS

(Hit the ticker maximum but everything else from last post, still sell on Quantum or Oklo)
_

Strong Buys
ALAB - Huge part of datacenter buildout, NVDA like margins, Mag7 customers. Already had competitors from AVGO,  really don't think Arista would be a competitive threat.

CRDO - Same sell-off as ALAB, thought they were both kind of overvalued before, but now they're back in correction territory so good to stock up.

NBIS - $400 PT bull case. We have macro tailwind from government re-opening + rate cut EOM october into earnings, so short term looks promising. Lot of things going for it (eg. meta x crwv, so there's potential for more mag7 clients), sum of parts doing well, eg. clickhouse, and scaling rev from $100m to $1.5B+ a quarter is insane. there's already contracts locked in its just a matter of company execution.

WLAC - Wrote a thesis about this earlier at $13. Even at $14.5 strong because it can re-rate 100%+ easily.

LTC - Affected by leverage traders and government shutdown. The shutdown is predicted to last awhile and the main reason to buy was the ETF getting approved. But a great buy sub <$100 anyway, because it will get approved in due time (~95% chance).

TSM - Holy crap. This would be a $3T company if this were a US company, insane profit margins, insane growth rate for their size. And every post you see about OpenAi X (**sydney sweeney partnership) or AMD buildout/NVDA buildout. TSM is the center of it all and would easily be a $2T+ company (from here at ~$1.5T), even if buying at ATHs.

BTC - $112K good entry point. Goldt keeps hitting ATH, nothing really changed fundamentally, just lot of liquidations recently
(+ same as tax harvest stocks last time)

AMZN - I really don't know how it's still down YTD. I don't think Amazon needs much explaining but still growing  (eg. AWS backlog massive, still going like 24% but not as much as ORCL, GCP and others obviously), but with EOY seasonality and runup to Feb, now is probably the best chance to catch the bottom. AMZN hitting $213-215 today was a good chance to stock up since it usually floats between $218-$227 if you're short term swing trading but long term I'd expect it to catchup to other mag7.

SMCI - Underrated. Markets were looking short term performance, and Charles was quoting like 55%+ Y/Y forward revenue growth which nobody believed + backlog that didnt get realized yet. But now with all the data center buildouts, now it's kinda making sense. So should re-rate in the next two earnings.

_
Buy

AMD - So many deals from OpenAI x AMD, oracle building out with AMD, this is going to re-rate to a potential $1T+ company if it's actually a strong competitive to $NVDA.  I don't think it's winner takes all and you can see a $4.5T+ market cap size with NVDA and some $350B marketcap size with AMD, so we can see a large ramp up (OpenAI is usually the leader in frontier models and if Sam says they can use AMD chips + elon said its' good for small-medium weight models, prboably means something positive)

FLNC - Strong re-rate on energy after AI consumption, great buy.

SEI - Strong re-rate on energy after AI consumption, great buy.

BZAI - Someone else did a DD on this company, just cause of sector and shift to edge compute (eg. Robotics goign to be hot). Because of low MC and runup of similar companies could turn out well.

NKLR - Nuclear stocks like $OKLO have been taking off, this is just follow the lader.

IREN - Needs no introduction, huge GW compute capacity just no announced mag7 deals yet but could come anytime -> strong re-rate. Only reason not a strong buy is because not fully convinced miners can pivot like CRWV and maintain great margins (eg. $ORCL hit piece) but we'll see.

WULF - GOOGL backlog, another $3.6+ or so in funding helps a lot.

CIFR - Lot of info on X about future capacity and strong re-rating. Always liked this company because it was NBIS-lite. You can probably buy any Neocloud and it will go up because the sector is incredibly high potential with Mag7 funneling revenue.

CRWV - Didn't like this as much as others because of debt but because of the seed oil correction much better buy point at $134 (below when META deal was announced)

BITF - Same in Neocloud category

WYFI - Same in Neocloud category

BITF - Same in Neocloud category

GLXY - Same in Neocloud category, helps with their buildout

RBRK - Did a DD on this, great buy for cybersecurity sector in mid term, they just need to scale back marketing and then it looks like they have a lot more FCF because they're spending most OPEX on marketing.

GRAB - Great fundamentally, -6.56% correction good to buy again

SEA - AMZN in SEA, tons of people use them. Just a buy just because of costumer base + monetization potenetial. Fundamentally growing $5B+ rev 38% Y/Y is also great.

META - I really don't like all their expensive capex on AI since they're not really putting out fronteir models like ChatGPT with it, who knows what Zuck is doing. But that aside, down 7.3% over the month, going to $700 support, probably a good buy around here to play catchup.

TGT - Dividend next month good catalyst.

SNAP - The Jenners are coming back (helps with popularity), they're shifting former memory opex to revenue, and this will probably cause a HUGE rerating next year. Just suffers from tax harvesting otherwise would be a strong buy rn. Usually tax harvesting events are kinda done in December.

MU - Now that China fears are kinda less intense, MU is a lot stronger buy just cause of memory use on buildout.

RKLB - Neutron, golden dome contracts, lot of cataylsts

FLY - Medium lift

UNH - Healthcare stock not affected by soybeans but had a correction. Would likely go up one instituions post their ports (eg. warren likely bought more)

Random thoughts
Basically any growth/risk stock that's not named Oklo is great because we have

-> Rate Cut end of month October
-> Government re-opening sometime (likely around end of Oct or early Nov)

Into
-> Rate Cut December.
-> Midterms (Bullish for stocks)

Usually market crashes happen when there's tightening not easing. And your stupid quantum bubbles would likely continue for another 3-12 months afterward. If you're short, then probably wait till next Feb.

Anyway, this is a great time for risk-on, and specially riding trends with neoclouds -> affiliated sectors (eg. energy) -> affiliated companies (eg. smci, tsm, etc).

I half joke-about soybeans because it likely signed escalating tensions, but I'd probably see a run-up into next year. Also I could write up a lot about each one but it's pretty time consuming but I'll put on a thesis post about random ones eg. $RBRK, from time to time.

Space/robotics/energy/quantum/ai/semi/critical top verticals right now, don't fight against momentum. I can think something is overvalued (eg. some critical materials bc. it's still spectulative compared to neoclouds that kinda have guaranteed rev based on execution from mag7) but I wouldn't short it into rate cuts.

Just personal thoughts, NFA
```

### [亏损 #23] HIMS long hz=6m — pub=2025-10-19T18:21:35
- entry=2025-10-20, $51.37
- 1m: **resolved_miss** raw=-29.41% bench=-1.67% excess=-27.74%
- 3m: excess=-43.22%  6m: excess=-50.74%
- **条件 label**: ['PRICE_TARGET']
- **if 句**: ['5T marketcap, AMD has a lot to catch up on even if it takes a small percent share', "BMNR - If I don't like Ethereum at these levels, no point of holding treasury companies"]
- **原文 (全文)**:
```
October 20th, Important Rate Cut Trading Week.

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
$ETH
$BMNR
$PL
$BLSKY
$RGTI
$OKLO
$IONQ
$QBTS

_

So macro wise, we are 9 days away from (~97% or so rate cut). Market is in fear mode. This is the ideal time to go long and not cut positions.

Fire Sale
_

$NBIS - Needs no explanation, I still maintain $400 PT on a bull case 2026 due to 4-6B+ forward revenue off ~60-75% gross margins, and another likely hyperscaler contract (eg. $META)

What happened on the 10%+ drop on Friday was mechanical hedging and MM Pinning. You can see this with the price stuck at $113.5, despite any volatility. 

I'd expect short hedges to unwind Monday (given MMs bought puts and were short calls -> heavy short into expiration) and price to go back up. I ended up buying 6 figures worth of calls on the drop as there was no material changes.

Strong Buy

TSM - Holy crap, please have this in your portfolio. This is a money printer, and scaling your revenue by 38-40% every year WHILE increasing gross margins is just insane. It dipped as well after smashing earnings so it's one of the easiest longs in my life.

AMKR - I don't have this in my portfolio yet but will be looking to add due to TSM's involvement in Arizona and potential to be a big partner in the US supply chain (as America tries to push TSM toward US fab + manufacturing).

WLAC - Neocloud SPAC IPO, large upside. I talk about this a lot recently, but it's probably one of the best valued Neoclouds out there, and already has great profit margins (not a pivot from miners, where it's a bit more uncertain). They work with Fluidstack, and I'd expect a 500%+ re-rating on top of a Mag7 contract.

AMZN - $213 is insane lol. I have no clue how this is down -3% YTD during a bull market.

LTC - Affected by crypto liquidations and government shutdown delaying ETFs. Great time to buy and just wait for ETF to be approved.

RDDT - Great dip to $190. I thought $200 would be a bottom but ended up going lower. The news about ChatGPT citing it less caused a large sell-off which I think was very immaterial.

HIMS - 14%+ drop off CEO share sale. Owners sell shares all the time, it doesn't really affect the fundamentals of the company much, just short term sentiment. I'd expect it to rebound.

IBIT - Bitcoin $108k great entry point, it's been swinging between $110k - $120k for awhile so anything under is usually great.

ALAB - I said this last time but it sold off way too much from news of a new competitor. It's already competing vs AVGO in the market lol, NVDA-like margins, growing hundreds of percent Y/Y, Mag7 using them in data center buildout. 

CRDO - Similar thesis to ALAB, sold off alongside Astera but a bit less.

SMCI - Should get re-rated for 55%+ or so revenue growth into next year. I doubted the projections earlier but with the data center growth, it's looking realistic.

FLY - This was a medium lift payload play. People doubt fly's execution but NOC co-developing medium lift takes a lot of risk off the table (and possible re-rating it 500%+ when it competes vs falcon9)

SNAP - Did the math on Snap monetization of memories in an earlier DD post and it's completely not priced in yet. It's doing $1.3B+ quarterly revenue on a $13B market cap lol, and the amount FCF they would get from increasing their revenue + lowering Google OPEX costs is insane.

ETOR  - Majority cash, growing at IBKR rates, suffering from tax harvesting

LULU - Suffering from tax harvesting + competition from Alo, Vuori, etc. But seasonally should be good, and extremely low p/e now.

Buy
AMD - ChatGPT putting in AMD orders, ORCL building out AMD data centers. Likely going to get a re-rating in the next year as a potential $NVDA competitor. Still think Nvidia will dominate but with it's 4.5T marketcap, AMD has a lot to catch up on even if it takes a small percent share.

HOOD - Looking at a lot better after the 10%+ correction. Could pull a PLTR

RBRK - Did DD on this earlier, looks better on the drop as a cybersecurity company really low multiples in the space. Just needs to cut back on marketing, customers sticky. 

UNH - Healthcare is sht in America but not going anywhere. Think Warren and the others know this 

TGT 🐈 - Dividend next moth, big dividend stock. Around now is a good time to load up IMO

IREN 🐈 - Huge GW, expect mag7 or similar deal. 

WYFI - Any neocloud is a buy (eg. see thesis on mag7 funneling revenue down toward these small 1B-5B companies)

WULF - neocloud play

CIFR - neocloud play

SLNH - neocloud play

BITF - neocloud play

GLXY - neocloud derivative play

FLNC - neocloud energy play

MU - China derisked, memory had a huge market there, memory also likely going to get re-rating in tdata center buildout

_

Sell

ETH - Not a fan of Ethereum at $4k+
BMNR - If I don't like Ethereum at these levels, no point of holding treasury companies 
PL - Low revenue, space stock (extremely high valuation)
BLSKY -Low revenue, space stock (extremely high valuation)
RGTI - Quantum bubble
OKLO - Nuclear bubble
IONQ -Quantum bubble 
QBTS - Quantum bubble

_

Quick macro heads up:
-> Rate cut in 9 days ~97% odds. Frontrunning expected, go long.  That's all.
```

### [亏损 #24] NBIS long hz=1y — pub=2025-10-12T23:33:40
- entry=2025-10-13, $135.21
- 1m: **resolved_miss** raw=-24.40% bench=+3.01% excess=-27.41%
- 3m: excess=-28.70%  6m: excess=+16.46%
- **条件 label**: ['PRICE_TARGET']
- **if 句**: ['FTX investing in Anthropic, $HOOD, where they all went up 1000% over a few years) can outlast a main business even if margins got compressed and $NBIS has a large stake in great companies like Clickhouse']
- **原文 (全文)**:
```
I still have 6fig in random $CIFR strikes but not high conviction. 

Short TLDR on why I have high conviction in $NBIS compared to others is because 

-Nebius is full stack -> higher margin (software orchestration for GPU utilization, we why that's important and a moat from $ORCL build-out failure, and why $CRWV bought out a lot of software companies).

-sum of parts (eg. FTX investing in Anthropic, $HOOD, where they all went up 1000% over a few years) can outlast a main business even if margins got compressed and $NBIS has a large stake in great companies like Clickhouse

-more diversified client base (learned from $ORCL why that's important too) for buildout -> usage compared to other Neoclouds.

High conviction $400 PT, $100B MC in 1Y for a bull case. 

I'm long stuff like $IREN too just because of their power capacity or $CIFR being Nebius-light in terms how they did fundraising + Mag7 client but it's slightly different me believing in a company vs. thinking they will outform from fundamentals.
```

### [亏损 #25] CIFR long hz=long_term — pub=2025-10-19T18:21:35
- entry=2025-10-20, $20.00
- 1m: **resolved_miss** raw=-27.10% bench=-1.67% excess=-25.43%
- 3m: excess=-15.68%  6m: excess=-12.08%
- **条件 label**: ['PRICE_TARGET']
- **if 句**: ['5T marketcap, AMD has a lot to catch up on even if it takes a small percent share', "BMNR - If I don't like Ethereum at these levels, no point of holding treasury companies"]
- **原文 (全文)**:
```
October 20th, Important Rate Cut Trading Week.

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
$ETH
$BMNR
$PL
$BLSKY
$RGTI
$OKLO
$IONQ
$QBTS

_

So macro wise, we are 9 days away from (~97% or so rate cut). Market is in fear mode. This is the ideal time to go long and not cut positions.

Fire Sale
_

$NBIS - Needs no explanation, I still maintain $400 PT on a bull case 2026 due to 4-6B+ forward revenue off ~60-75% gross margins, and another likely hyperscaler contract (eg. $META)

What happened on the 10%+ drop on Friday was mechanical hedging and MM Pinning. You can see this with the price stuck at $113.5, despite any volatility. 

I'd expect short hedges to unwind Monday (given MMs bought puts and were short calls -> heavy short into expiration) and price to go back up. I ended up buying 6 figures worth of calls on the drop as there was no material changes.

Strong Buy

TSM - Holy crap, please have this in your portfolio. This is a money printer, and scaling your revenue by 38-40% every year WHILE increasing gross margins is just insane. It dipped as well after smashing earnings so it's one of the easiest longs in my life.

AMKR - I don't have this in my portfolio yet but will be looking to add due to TSM's involvement in Arizona and potential to be a big partner in the US supply chain (as America tries to push TSM toward US fab + manufacturing).

WLAC - Neocloud SPAC IPO, large upside. I talk about this a lot recently, but it's probably one of the best valued Neoclouds out there, and already has great profit margins (not a pivot from miners, where it's a bit more uncertain). They work with Fluidstack, and I'd expect a 500%+ re-rating on top of a Mag7 contract.

AMZN - $213 is insane lol. I have no clue how this is down -3% YTD during a bull market.

LTC - Affected by crypto liquidations and government shutdown delaying ETFs. Great time to buy and just wait for ETF to be approved.

RDDT - Great dip to $190. I thought $200 would be a bottom but ended up going lower. The news about ChatGPT citing it less caused a large sell-off which I think was very immaterial.

HIMS - 14%+ drop off CEO share sale. Owners sell shares all the time, it doesn't really affect the fundamentals of the company much, just short term sentiment. I'd expect it to rebound.

IBIT - Bitcoin $108k great entry point, it's been swinging between $110k - $120k for awhile so anything under is usually great.

ALAB - I said this last time but it sold off way too much from news of a new competitor. It's already competing vs AVGO in the market lol, NVDA-like margins, growing hundreds of percent Y/Y, Mag7 using them in data center buildout. 

CRDO - Similar thesis to ALAB, sold off alongside Astera but a bit less.

SMCI - Should get re-rated for 55%+ or so revenue growth into next year. I doubted the projections earlier but with the data center growth, it's looking realistic.

FLY - This was a medium lift payload play. People doubt fly's execution but NOC co-developing medium lift takes a lot of risk off the table (and possible re-rating it 500%+ when it competes vs falcon9)

SNAP - Did the math on Snap monetization of memories in an earlier DD post and it's completely not priced in yet. It's doing $1.3B+ quarterly revenue on a $13B market cap lol, and the amount FCF they would get from increasing their revenue + lowering Google OPEX costs is insane.

ETOR  - Majority cash, growing at IBKR rates, suffering from tax harvesting

LULU - Suffering from tax harvesting + competition from Alo, Vuori, etc. But seasonally should be good, and extremely low p/e now.

Buy
AMD - ChatGPT putting in AMD orders, ORCL building out AMD data centers. Likely going to get a re-rating in the next year as a potential $NVDA competitor. Still think Nvidia will dominate but with it's 4.5T marketcap, AMD has a lot to catch up on even if it takes a small percent share.

HOOD - Looking at a lot better after the 10%+ correction. Could pull a PLTR

RBRK - Did DD on this earlier, looks better on the drop as a cybersecurity company really low multiples in the space. Just needs to cut back on marketing, customers sticky. 

UNH - Healthcare is sht in America but not going anywhere. Think Warren and the others know this 

TGT 🐈 - Dividend next moth, big dividend stock. Around now is a good time to load up IMO

IREN 🐈 - Huge GW, expect mag7 or similar deal. 

WYFI - Any neocloud is a buy (eg. see thesis on mag7 funneling revenue down toward these small 1B-5B companies)

WULF - neocloud play

CIFR - neocloud play

SLNH - neocloud play

BITF - neocloud play

GLXY - neocloud derivative play

FLNC - neocloud energy play

MU - China derisked, memory had a huge market there, memory also likely going to get re-rating in tdata center buildout

_

Sell

ETH - Not a fan of Ethereum at $4k+
BMNR - If I don't like Ethereum at these levels, no point of holding treasury companies 
PL - Low revenue, space stock (extremely high valuation)
BLSKY -Low revenue, space stock (extremely high valuation)
RGTI - Quantum bubble
OKLO - Nuclear bubble
IONQ -Quantum bubble 
QBTS - Quantum bubble

_

Quick macro heads up:
-> Rate cut in 9 days ~97% odds. Frontrunning expected, go long.  That's all.
```

### [亏损 #26] FLY long hz=6m — pub=2025-10-15T07:42:21
- entry=2025-10-16, $29.80
- 1m: **resolved_miss** raw=-22.99% bench=+1.71% excess=-24.70%
- 3m: excess=-0.75%  6m: excess=+34.67%
- **条件 label**: ['PRICE_TARGET']
- **if 句**: ['This would be a $3T company if this were a US company, insane profit margins, insane growth rate for their size', '5T), even if buying at ATHs', "AMZN hitting $213-215 today was a good chance to stock up since it usually floats between $218-$227 if you're short term swing trading but long term I'd expect it to catchup to other mag7"]
- **原文 (全文)**:
```
The Great Soybean/Seed Oil Crash, personal thoughts and explanations:

Strong Buy
$ALAB
$CRDO
$NBIS
$WLAC
$LTC
$TSM
$BTC
(+ same as tax harvest stocks last time)
$AMZN
$SMCI
_

Buy
$AMD
$FLNC
$SEI
$BZAI
$NKLR
$IREN
$WULF
$CIFR
$CRWV
$BITF
$WYFI
$SLNH
$BITF
$RBRK
$GLXY
$GRAB
$SEA
$META
$TGT
$SNAP
$MU
$RKLB
$FLY
$UNH

Hold
$MP
$HOOD
$EOSE
$NVDA
$GOOGL
$DFLI
$SOFI
$VIRT
$RR
$AVGO
$BE
$ASTS

(Hit the ticker maximum but everything else from last post, still sell on Quantum or Oklo)
_

Strong Buys
ALAB - Huge part of datacenter buildout, NVDA like margins, Mag7 customers. Already had competitors from AVGO,  really don't think Arista would be a competitive threat.

CRDO - Same sell-off as ALAB, thought they were both kind of overvalued before, but now they're back in correction territory so good to stock up.

NBIS - $400 PT bull case. We have macro tailwind from government re-opening + rate cut EOM october into earnings, so short term looks promising. Lot of things going for it (eg. meta x crwv, so there's potential for more mag7 clients), sum of parts doing well, eg. clickhouse, and scaling rev from $100m to $1.5B+ a quarter is insane. there's already contracts locked in its just a matter of company execution.

WLAC - Wrote a thesis about this earlier at $13. Even at $14.5 strong because it can re-rate 100%+ easily.

LTC - Affected by leverage traders and government shutdown. The shutdown is predicted to last awhile and the main reason to buy was the ETF getting approved. But a great buy sub <$100 anyway, because it will get approved in due time (~95% chance).

TSM - Holy crap. This would be a $3T company if this were a US company, insane profit margins, insane growth rate for their size. And every post you see about OpenAi X (**sydney sweeney partnership) or AMD buildout/NVDA buildout. TSM is the center of it all and would easily be a $2T+ company (from here at ~$1.5T), even if buying at ATHs.

BTC - $112K good entry point. Goldt keeps hitting ATH, nothing really changed fundamentally, just lot of liquidations recently
(+ same as tax harvest stocks last time)

AMZN - I really don't know how it's still down YTD. I don't think Amazon needs much explaining but still growing  (eg. AWS backlog massive, still going like 24% but not as much as ORCL, GCP and others obviously), but with EOY seasonality and runup to Feb, now is probably the best chance to catch the bottom. AMZN hitting $213-215 today was a good chance to stock up since it usually floats between $218-$227 if you're short term swing trading but long term I'd expect it to catchup to other mag7.

SMCI - Underrated. Markets were looking short term performance, and Charles was quoting like 55%+ Y/Y forward revenue growth which nobody believed + backlog that didnt get realized yet. But now with all the data center buildouts, now it's kinda making sense. So should re-rate in the next two earnings.

_
Buy

AMD - So many deals from OpenAI x AMD, oracle building out with AMD, this is going to re-rate to a potential $1T+ company if it's actually a strong competitive to $NVDA.  I don't think it's winner takes all and you can see a $4.5T+ market cap size with NVDA and some $350B marketcap size with AMD, so we can see a large ramp up (OpenAI is usually the leader in frontier models and if Sam says they can use AMD chips + elon said its' good for small-medium weight models, prboably means something positive)

FLNC - Strong re-rate on energy after AI consumption, great buy.

SEI - Strong re-rate on energy after AI consumption, great buy.

BZAI - Someone else did a DD on this company, just cause of sector and shift to edge compute (eg. Robotics goign to be hot). Because of low MC and runup of similar companies could turn out well.

NKLR - Nuclear stocks like $OKLO have been taking off, this is just follow the lader.

IREN - Needs no introduction, huge GW compute capacity just no announced mag7 deals yet but could come anytime -> strong re-rate. Only reason not a strong buy is because not fully convinced miners can pivot like CRWV and maintain great margins (eg. $ORCL hit piece) but we'll see.

WULF - GOOGL backlog, another $3.6+ or so in funding helps a lot.

CIFR - Lot of info on X about future capacity and strong re-rating. Always liked this company because it was NBIS-lite. You can probably buy any Neocloud and it will go up because the sector is incredibly high potential with Mag7 funneling revenue.

CRWV - Didn't like this as much as others because of debt but because of the seed oil correction much better buy point at $134 (below when META deal was announced)

BITF - Same in Neocloud category

WYFI - Same in Neocloud category

BITF - Same in Neocloud category

GLXY - Same in Neocloud category, helps with their buildout

RBRK - Did a DD on this, great buy for cybersecurity sector in mid term, they just need to scale back marketing and then it looks like they have a lot more FCF because they're spending most OPEX on marketing.

GRAB - Great fundamentally, -6.56% correction good to buy again

SEA - AMZN in SEA, tons of people use them. Just a buy just because of costumer base + monetization potenetial. Fundamentally growing $5B+ rev 38% Y/Y is also great.

META - I really don't like all their expensive capex on AI since they're not really putting out fronteir models like ChatGPT with it, who knows what Zuck is doing. But that aside, down 7.3% over the month, going to $700 support, probably a good buy around here to play catchup.

TGT - Dividend next month good catalyst.

SNAP - The Jenners are coming back (helps with popularity), they're shifting former memory opex to revenue, and this will probably cause a HUGE rerating next year. Just suffers from tax harvesting otherwise would be a strong buy rn. Usually tax harvesting events are kinda done in December.

MU - Now that China fears are kinda less intense, MU is a lot stronger buy just cause of memory use on buildout.

RKLB - Neutron, golden dome contracts, lot of cataylsts

FLY - Medium lift

UNH - Healthcare stock not affected by soybeans but had a correction. Would likely go up one instituions post their ports (eg. warren likely bought more)

Random thoughts
Basically any growth/risk stock that's not named Oklo is great because we have

-> Rate Cut end of month October
-> Government re-opening sometime (likely around end of Oct or early Nov)

Into
-> Rate Cut December.
-> Midterms (Bullish for stocks)

Usually market crashes happen when there's tightening not easing. And your stupid quantum bubbles would likely continue for another 3-12 months afterward. If you're short, then probably wait till next Feb.

Anyway, this is a great time for risk-on, and specially riding trends with neoclouds -> affiliated sectors (eg. energy) -> affiliated companies (eg. smci, tsm, etc).

I half joke-about soybeans because it likely signed escalating tensions, but I'd probably see a run-up into next year. Also I could write up a lot about each one but it's pretty time consuming but I'll put on a thesis post about random ones eg. $RBRK, from time to time.

Space/robotics/energy/quantum/ai/semi/critical top verticals right now, don't fight against momentum. I can think something is overvalued (eg. some critical materials bc. it's still spectulative compared to neoclouds that kinda have guaranteed rev based on execution from mag7) but I wouldn't short it into rate cuts.

Just personal thoughts, NFA
```

### [亏损 #27] NBIS long hz=1y — pub=2025-11-01T05:32:25
- entry=2025-11-03, $134.00
- 1m: **resolved_miss** raw=-23.28% bench=+0.15% excess=-23.44%
- 3m: excess=-44.04%  6m: excess=+30.83%
- **条件 label**: ['PRICE_TARGET']
- **if 句**: ['Even if $NBIS is near ATH, it’s growing rapidly and it will keep having new ATHs every week']
- **原文 (全文)**:
```
@blu400_ Personally I’d cost average.

Even if $NBIS is near ATH, it’s growing rapidly and it will keep having new ATHs every week.

I’ve maintained $400 PT bull case, so $130 now seems quite undervalued

https://t.co/RTbdrjXqtx
```

### [亏损 #28] FLY long hz=long_term — pub=2025-10-19T18:21:35
- entry=2025-10-20, $26.38
- 1m: **resolved_miss** raw=-25.09% bench=-1.67% excess=-23.42%
- 3m: excess=+14.58%  6m: excess=+40.56%
- **条件 label**: ['PRICE_TARGET']
- **if 句**: ['5T marketcap, AMD has a lot to catch up on even if it takes a small percent share', "BMNR - If I don't like Ethereum at these levels, no point of holding treasury companies"]
- **原文 (全文)**:
```
October 20th, Important Rate Cut Trading Week.

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
$ETH
$BMNR
$PL
$BLSKY
$RGTI
$OKLO
$IONQ
$QBTS

_

So macro wise, we are 9 days away from (~97% or so rate cut). Market is in fear mode. This is the ideal time to go long and not cut positions.

Fire Sale
_

$NBIS - Needs no explanation, I still maintain $400 PT on a bull case 2026 due to 4-6B+ forward revenue off ~60-75% gross margins, and another likely hyperscaler contract (eg. $META)

What happened on the 10%+ drop on Friday was mechanical hedging and MM Pinning. You can see this with the price stuck at $113.5, despite any volatility. 

I'd expect short hedges to unwind Monday (given MMs bought puts and were short calls -> heavy short into expiration) and price to go back up. I ended up buying 6 figures worth of calls on the drop as there was no material changes.

Strong Buy

TSM - Holy crap, please have this in your portfolio. This is a money printer, and scaling your revenue by 38-40% every year WHILE increasing gross margins is just insane. It dipped as well after smashing earnings so it's one of the easiest longs in my life.

AMKR - I don't have this in my portfolio yet but will be looking to add due to TSM's involvement in Arizona and potential to be a big partner in the US supply chain (as America tries to push TSM toward US fab + manufacturing).

WLAC - Neocloud SPAC IPO, large upside. I talk about this a lot recently, but it's probably one of the best valued Neoclouds out there, and already has great profit margins (not a pivot from miners, where it's a bit more uncertain). They work with Fluidstack, and I'd expect a 500%+ re-rating on top of a Mag7 contract.

AMZN - $213 is insane lol. I have no clue how this is down -3% YTD during a bull market.

LTC - Affected by crypto liquidations and government shutdown delaying ETFs. Great time to buy and just wait for ETF to be approved.

RDDT - Great dip to $190. I thought $200 would be a bottom but ended up going lower. The news about ChatGPT citing it less caused a large sell-off which I think was very immaterial.

HIMS - 14%+ drop off CEO share sale. Owners sell shares all the time, it doesn't really affect the fundamentals of the company much, just short term sentiment. I'd expect it to rebound.

IBIT - Bitcoin $108k great entry point, it's been swinging between $110k - $120k for awhile so anything under is usually great.

ALAB - I said this last time but it sold off way too much from news of a new competitor. It's already competing vs AVGO in the market lol, NVDA-like margins, growing hundreds of percent Y/Y, Mag7 using them in data center buildout. 

CRDO - Similar thesis to ALAB, sold off alongside Astera but a bit less.

SMCI - Should get re-rated for 55%+ or so revenue growth into next year. I doubted the projections earlier but with the data center growth, it's looking realistic.

FLY - This was a medium lift payload play. People doubt fly's execution but NOC co-developing medium lift takes a lot of risk off the table (and possible re-rating it 500%+ when it competes vs falcon9)

SNAP - Did the math on Snap monetization of memories in an earlier DD post and it's completely not priced in yet. It's doing $1.3B+ quarterly revenue on a $13B market cap lol, and the amount FCF they would get from increasing their revenue + lowering Google OPEX costs is insane.

ETOR  - Majority cash, growing at IBKR rates, suffering from tax harvesting

LULU - Suffering from tax harvesting + competition from Alo, Vuori, etc. But seasonally should be good, and extremely low p/e now.

Buy
AMD - ChatGPT putting in AMD orders, ORCL building out AMD data centers. Likely going to get a re-rating in the next year as a potential $NVDA competitor. Still think Nvidia will dominate but with it's 4.5T marketcap, AMD has a lot to catch up on even if it takes a small percent share.

HOOD - Looking at a lot better after the 10%+ correction. Could pull a PLTR

RBRK - Did DD on this earlier, looks better on the drop as a cybersecurity company really low multiples in the space. Just needs to cut back on marketing, customers sticky. 

UNH - Healthcare is sht in America but not going anywhere. Think Warren and the others know this 

TGT 🐈 - Dividend next moth, big dividend stock. Around now is a good time to load up IMO

IREN 🐈 - Huge GW, expect mag7 or similar deal. 

WYFI - Any neocloud is a buy (eg. see thesis on mag7 funneling revenue down toward these small 1B-5B companies)

WULF - neocloud play

CIFR - neocloud play

SLNH - neocloud play

BITF - neocloud play

GLXY - neocloud derivative play

FLNC - neocloud energy play

MU - China derisked, memory had a huge market there, memory also likely going to get re-rating in tdata center buildout

_

Sell

ETH - Not a fan of Ethereum at $4k+
BMNR - If I don't like Ethereum at these levels, no point of holding treasury companies 
PL - Low revenue, space stock (extremely high valuation)
BLSKY -Low revenue, space stock (extremely high valuation)
RGTI - Quantum bubble
OKLO - Nuclear bubble
IONQ -Quantum bubble 
QBTS - Quantum bubble

_

Quick macro heads up:
-> Rate cut in 9 days ~97% odds. Frontrunning expected, go long.  That's all.
```

### [亏损 #29] HIMS long hz=short_term — pub=2025-09-30T19:09:16
- entry=2025-10-01, $55.90
- 1m: **resolved_miss** raw=-21.18% bench=+1.70% excess=-22.88%
- 3m: excess=-42.43%  6m: excess=-62.21%
- **条件 label**: ['PRICE_TARGET']
- **if 句**: ["So I'd use this time to DCA and buy calls/shares even if it's up 1", "If you wanted to build a long term position I'd buy at this level", "If it drops past $273, I'd just DCA and then if it drops further switch to calls"]
- **原文 (全文)**:
```
Lot of inspirational trader mindsets going around X lately like:
 
"It will pay off. Be Patient". All BS. 

Traders consider sector momentum, catalysts, valuation, pullbacks, macro, IV, option flows, etc. 

Here's my mindset for short term trading for various stocks: 

1. $NBIS - $111.91, even though it's up 1.53% on the day, CRWV is up 12% off Meta gives them a $14B contract.

So usually it's bullish for all neoclouds. It spiked to $117 ( i probably would have still held) but pulled back to $111 likely from too much open interest, but we'll likely keep seeing a rally upward. So I'd use this time to DCA and buy calls/shares even if it's up 1.53%

Not "truly a dip" but it's more of a dip during a rally. 

2. $HIMS - $56.4 Down 4.67%, usually people just blindly buy the dip but this was actually caused from something material, which was Trump launching a direct to consumer GOV drug website. Short interest decreased back to 33% on the rise to $60. 

This dip will likely be used for short covering. I did buy $46 support but sold shortly on a bounce after I just felt like it would go down more. But I just personally prefer bottom entry points so that's probably closer to $50. 

I still remember AMZN launching a competitor, HIMS crashed 20% then rose again, I'd expect the same with Trump's program mid term but near term it's a headwind. 

3. $RDDT - $228, down 5.45%, no news. Just probably valuation concerns. We saw similar growth stocks like ALAB, CRED, have random 20% pullbacks. Lot of software/social stocks like SNAP down 8.1% off non-material news. Correction is healthy, stocks don't just keep going up, I'd prefer to wait in the $100+ again, rather than $200+ (just personally), but it's actually a better buy than the rest, given RDDT has larger 5-8% pullbacks on random days, just from historical experiences so 6-7% drop is a good buy intra-day and you'd likely see it recover but we might see a lot of growth stocks have a larger correction into massive rally Nov/Dec so might not be an actual bottom. 

I don't really look at chart RSI nowadays, just do this based on feelings from experience looking at the stock + IV every day for the past year or two. 

4. AMZN - No major macro news, prob government shutdown Oct 1st that might cause some panic for index but it's pretty immaterial. It dropped, 1.35% so I'd buy since it' a good time to cost average. 

5. Klarna - $36, 5.3% drop. Sometimes you just go off gut feeling. Below IPO price, no major news. Most IPOs were down like Gemini, etc. If you wanted to build a long term position I'd buy at this level. 

6. TSM - $277, I've been guilty of swing trading between $273-$279, so I just buy every drop to $273 and sell at $277-$279 for 2% profit purely with shares. So far I've done this ~2 times with shares. If it drops past $273, I'd just DCA and then if it drops further switch to calls. 

There's no True or False way to do this, everyone kind of has their own approach. (also sorry about CRM, bad earnings got that one wrong, I'll probably cost avg if ti declines further). 

But generally this is just what I'm thinking about when I go down the list of every single stock. Once again, everyone thinks differently, I just wanted to write down how I think if it's helpful to others.
```

### [亏损 #30] IREN long hz=event_driven — pub=2025-10-19T18:21:35
- entry=2025-10-20, $63.61
- 1m: **resolved_miss** raw=-23.20% bench=-1.67% excess=-21.53%
- 3m: excess=-20.48%  6m: excess=-23.75%
- **条件 label**: ['PRICE_TARGET']
- **if 句**: ['5T marketcap, AMD has a lot to catch up on even if it takes a small percent share', "BMNR - If I don't like Ethereum at these levels, no point of holding treasury companies"]
- **原文 (全文)**:
```
October 20th, Important Rate Cut Trading Week.

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
$ETH
$BMNR
$PL
$BLSKY
$RGTI
$OKLO
$IONQ
$QBTS

_

So macro wise, we are 9 days away from (~97% or so rate cut). Market is in fear mode. This is the ideal time to go long and not cut positions.

Fire Sale
_

$NBIS - Needs no explanation, I still maintain $400 PT on a bull case 2026 due to 4-6B+ forward revenue off ~60-75% gross margins, and another likely hyperscaler contract (eg. $META)

What happened on the 10%+ drop on Friday was mechanical hedging and MM Pinning. You can see this with the price stuck at $113.5, despite any volatility. 

I'd expect short hedges to unwind Monday (given MMs bought puts and were short calls -> heavy short into expiration) and price to go back up. I ended up buying 6 figures worth of calls on the drop as there was no material changes.

Strong Buy

TSM - Holy crap, please have this in your portfolio. This is a money printer, and scaling your revenue by 38-40% every year WHILE increasing gross margins is just insane. It dipped as well after smashing earnings so it's one of the easiest longs in my life.

AMKR - I don't have this in my portfolio yet but will be looking to add due to TSM's involvement in Arizona and potential to be a big partner in the US supply chain (as America tries to push TSM toward US fab + manufacturing).

WLAC - Neocloud SPAC IPO, large upside. I talk about this a lot recently, but it's probably one of the best valued Neoclouds out there, and already has great profit margins (not a pivot from miners, where it's a bit more uncertain). They work with Fluidstack, and I'd expect a 500%+ re-rating on top of a Mag7 contract.

AMZN - $213 is insane lol. I have no clue how this is down -3% YTD during a bull market.

LTC - Affected by crypto liquidations and government shutdown delaying ETFs. Great time to buy and just wait for ETF to be approved.

RDDT - Great dip to $190. I thought $200 would be a bottom but ended up going lower. The news about ChatGPT citing it less caused a large sell-off which I think was very immaterial.

HIMS - 14%+ drop off CEO share sale. Owners sell shares all the time, it doesn't really affect the fundamentals of the company much, just short term sentiment. I'd expect it to rebound.

IBIT - Bitcoin $108k great entry point, it's been swinging between $110k - $120k for awhile so anything under is usually great.

ALAB - I said this last time but it sold off way too much from news of a new competitor. It's already competing vs AVGO in the market lol, NVDA-like margins, growing hundreds of percent Y/Y, Mag7 using them in data center buildout. 

CRDO - Similar thesis to ALAB, sold off alongside Astera but a bit less.

SMCI - Should get re-rated for 55%+ or so revenue growth into next year. I doubted the projections earlier but with the data center growth, it's looking realistic.

FLY - This was a medium lift payload play. People doubt fly's execution but NOC co-developing medium lift takes a lot of risk off the table (and possible re-rating it 500%+ when it competes vs falcon9)

SNAP - Did the math on Snap monetization of memories in an earlier DD post and it's completely not priced in yet. It's doing $1.3B+ quarterly revenue on a $13B market cap lol, and the amount FCF they would get from increasing their revenue + lowering Google OPEX costs is insane.

ETOR  - Majority cash, growing at IBKR rates, suffering from tax harvesting

LULU - Suffering from tax harvesting + competition from Alo, Vuori, etc. But seasonally should be good, and extremely low p/e now.

Buy
AMD - ChatGPT putting in AMD orders, ORCL building out AMD data centers. Likely going to get a re-rating in the next year as a potential $NVDA competitor. Still think Nvidia will dominate but with it's 4.5T marketcap, AMD has a lot to catch up on even if it takes a small percent share.

HOOD - Looking at a lot better after the 10%+ correction. Could pull a PLTR

RBRK - Did DD on this earlier, looks better on the drop as a cybersecurity company really low multiples in the space. Just needs to cut back on marketing, customers sticky. 

UNH - Healthcare is sht in America but not going anywhere. Think Warren and the others know this 

TGT 🐈 - Dividend next moth, big dividend stock. Around now is a good time to load up IMO

IREN 🐈 - Huge GW, expect mag7 or similar deal. 

WYFI - Any neocloud is a buy (eg. see thesis on mag7 funneling revenue down toward these small 1B-5B companies)

WULF - neocloud play

CIFR - neocloud play

SLNH - neocloud play

BITF - neocloud play

GLXY - neocloud derivative play

FLNC - neocloud energy play

MU - China derisked, memory had a huge market there, memory also likely going to get re-rating in tdata center buildout

_

Sell

ETH - Not a fan of Ethereum at $4k+
BMNR - If I don't like Ethereum at these levels, no point of holding treasury companies 
PL - Low revenue, space stock (extremely high valuation)
BLSKY -Low revenue, space stock (extremely high valuation)
RGTI - Quantum bubble
OKLO - Nuclear bubble
IONQ -Quantum bubble 
QBTS - Quantum bubble

_

Quick macro heads up:
-> Rate cut in 9 days ~97% odds. Frontrunning expected, go long.  That's all.
```

### [亏损 #31] WLAC long hz=6m — pub=2025-10-15T07:42:21
- entry=2025-10-16, $14.70
- 1m: **resolved_miss** raw=-19.73% bench=+1.71% excess=-21.44%
- 3m: excess=-16.03%  6m: excess=-18.48%
- **条件 label**: ['PRICE_TARGET']
- **if 句**: ['This would be a $3T company if this were a US company, insane profit margins, insane growth rate for their size', '5T), even if buying at ATHs', "AMZN hitting $213-215 today was a good chance to stock up since it usually floats between $218-$227 if you're short term swing trading but long term I'd expect it to catchup to other mag7"]
- **原文 (全文)**:
```
The Great Soybean/Seed Oil Crash, personal thoughts and explanations:

Strong Buy
$ALAB
$CRDO
$NBIS
$WLAC
$LTC
$TSM
$BTC
(+ same as tax harvest stocks last time)
$AMZN
$SMCI
_

Buy
$AMD
$FLNC
$SEI
$BZAI
$NKLR
$IREN
$WULF
$CIFR
$CRWV
$BITF
$WYFI
$SLNH
$BITF
$RBRK
$GLXY
$GRAB
$SEA
$META
$TGT
$SNAP
$MU
$RKLB
$FLY
$UNH

Hold
$MP
$HOOD
$EOSE
$NVDA
$GOOGL
$DFLI
$SOFI
$VIRT
$RR
$AVGO
$BE
$ASTS

(Hit the ticker maximum but everything else from last post, still sell on Quantum or Oklo)
_

Strong Buys
ALAB - Huge part of datacenter buildout, NVDA like margins, Mag7 customers. Already had competitors from AVGO,  really don't think Arista would be a competitive threat.

CRDO - Same sell-off as ALAB, thought they were both kind of overvalued before, but now they're back in correction territory so good to stock up.

NBIS - $400 PT bull case. We have macro tailwind from government re-opening + rate cut EOM october into earnings, so short term looks promising. Lot of things going for it (eg. meta x crwv, so there's potential for more mag7 clients), sum of parts doing well, eg. clickhouse, and scaling rev from $100m to $1.5B+ a quarter is insane. there's already contracts locked in its just a matter of company execution.

WLAC - Wrote a thesis about this earlier at $13. Even at $14.5 strong because it can re-rate 100%+ easily.

LTC - Affected by leverage traders and government shutdown. The shutdown is predicted to last awhile and the main reason to buy was the ETF getting approved. But a great buy sub <$100 anyway, because it will get approved in due time (~95% chance).

TSM - Holy crap. This would be a $3T company if this were a US company, insane profit margins, insane growth rate for their size. And every post you see about OpenAi X (**sydney sweeney partnership) or AMD buildout/NVDA buildout. TSM is the center of it all and would easily be a $2T+ company (from here at ~$1.5T), even if buying at ATHs.

BTC - $112K good entry point. Goldt keeps hitting ATH, nothing really changed fundamentally, just lot of liquidations recently
(+ same as tax harvest stocks last time)

AMZN - I really don't know how it's still down YTD. I don't think Amazon needs much explaining but still growing  (eg. AWS backlog massive, still going like 24% but not as much as ORCL, GCP and others obviously), but with EOY seasonality and runup to Feb, now is probably the best chance to catch the bottom. AMZN hitting $213-215 today was a good chance to stock up since it usually floats between $218-$227 if you're short term swing trading but long term I'd expect it to catchup to other mag7.

SMCI - Underrated. Markets were looking short term performance, and Charles was quoting like 55%+ Y/Y forward revenue growth which nobody believed + backlog that didnt get realized yet. But now with all the data center buildouts, now it's kinda making sense. So should re-rate in the next two earnings.

_
Buy

AMD - So many deals from OpenAI x AMD, oracle building out with AMD, this is going to re-rate to a potential $1T+ company if it's actually a strong competitive to $NVDA.  I don't think it's winner takes all and you can see a $4.5T+ market cap size with NVDA and some $350B marketcap size with AMD, so we can see a large ramp up (OpenAI is usually the leader in frontier models and if Sam says they can use AMD chips + elon said its' good for small-medium weight models, prboably means something positive)

FLNC - Strong re-rate on energy after AI consumption, great buy.

SEI - Strong re-rate on energy after AI consumption, great buy.

BZAI - Someone else did a DD on this company, just cause of sector and shift to edge compute (eg. Robotics goign to be hot). Because of low MC and runup of similar companies could turn out well.

NKLR - Nuclear stocks like $OKLO have been taking off, this is just follow the lader.

IREN - Needs no introduction, huge GW compute capacity just no announced mag7 deals yet but could come anytime -> strong re-rate. Only reason not a strong buy is because not fully convinced miners can pivot like CRWV and maintain great margins (eg. $ORCL hit piece) but we'll see.

WULF - GOOGL backlog, another $3.6+ or so in funding helps a lot.

CIFR - Lot of info on X about future capacity and strong re-rating. Always liked this company because it was NBIS-lite. You can probably buy any Neocloud and it will go up because the sector is incredibly high potential with Mag7 funneling revenue.

CRWV - Didn't like this as much as others because of debt but because of the seed oil correction much better buy point at $134 (below when META deal was announced)

BITF - Same in Neocloud category

WYFI - Same in Neocloud category

BITF - Same in Neocloud category

GLXY - Same in Neocloud category, helps with their buildout

RBRK - Did a DD on this, great buy for cybersecurity sector in mid term, they just need to scale back marketing and then it looks like they have a lot more FCF because they're spending most OPEX on marketing.

GRAB - Great fundamentally, -6.56% correction good to buy again

SEA - AMZN in SEA, tons of people use them. Just a buy just because of costumer base + monetization potenetial. Fundamentally growing $5B+ rev 38% Y/Y is also great.

META - I really don't like all their expensive capex on AI since they're not really putting out fronteir models like ChatGPT with it, who knows what Zuck is doing. But that aside, down 7.3% over the month, going to $700 support, probably a good buy around here to play catchup.

TGT - Dividend next month good catalyst.

SNAP - The Jenners are coming back (helps with popularity), they're shifting former memory opex to revenue, and this will probably cause a HUGE rerating next year. Just suffers from tax harvesting otherwise would be a strong buy rn. Usually tax harvesting events are kinda done in December.

MU - Now that China fears are kinda less intense, MU is a lot stronger buy just cause of memory use on buildout.

RKLB - Neutron, golden dome contracts, lot of cataylsts

FLY - Medium lift

UNH - Healthcare stock not affected by soybeans but had a correction. Would likely go up one instituions post their ports (eg. warren likely bought more)

Random thoughts
Basically any growth/risk stock that's not named Oklo is great because we have

-> Rate Cut end of month October
-> Government re-opening sometime (likely around end of Oct or early Nov)

Into
-> Rate Cut December.
-> Midterms (Bullish for stocks)

Usually market crashes happen when there's tightening not easing. And your stupid quantum bubbles would likely continue for another 3-12 months afterward. If you're short, then probably wait till next Feb.

Anyway, this is a great time for risk-on, and specially riding trends with neoclouds -> affiliated sectors (eg. energy) -> affiliated companies (eg. smci, tsm, etc).

I half joke-about soybeans because it likely signed escalating tensions, but I'd probably see a run-up into next year. Also I could write up a lot about each one but it's pretty time consuming but I'll put on a thesis post about random ones eg. $RBRK, from time to time.

Space/robotics/energy/quantum/ai/semi/critical top verticals right now, don't fight against momentum. I can think something is overvalued (eg. some critical materials bc. it's still spectulative compared to neoclouds that kinda have guaranteed rev based on execution from mag7) but I wouldn't short it into rate cuts.

Just personal thoughts, NFA
```

### [亏损 #32] NBIS long hz=long_term — pub=2025-10-19T18:21:35
- entry=2025-10-20, $116.79
- 1m: **resolved_miss** raw=-22.48% bench=-1.67% excess=-20.80%
- 3m: excess=-19.71%  6m: excess=+28.96%
- **条件 label**: ['PRICE_TARGET']
- **if 句**: ['5T marketcap, AMD has a lot to catch up on even if it takes a small percent share', "BMNR - If I don't like Ethereum at these levels, no point of holding treasury companies"]
- **原文 (全文)**:
```
October 20th, Important Rate Cut Trading Week.

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
$ETH
$BMNR
$PL
$BLSKY
$RGTI
$OKLO
$IONQ
$QBTS

_

So macro wise, we are 9 days away from (~97% or so rate cut). Market is in fear mode. This is the ideal time to go long and not cut positions.

Fire Sale
_

$NBIS - Needs no explanation, I still maintain $400 PT on a bull case 2026 due to 4-6B+ forward revenue off ~60-75% gross margins, and another likely hyperscaler contract (eg. $META)

What happened on the 10%+ drop on Friday was mechanical hedging and MM Pinning. You can see this with the price stuck at $113.5, despite any volatility. 

I'd expect short hedges to unwind Monday (given MMs bought puts and were short calls -> heavy short into expiration) and price to go back up. I ended up buying 6 figures worth of calls on the drop as there was no material changes.

Strong Buy

TSM - Holy crap, please have this in your portfolio. This is a money printer, and scaling your revenue by 38-40% every year WHILE increasing gross margins is just insane. It dipped as well after smashing earnings so it's one of the easiest longs in my life.

AMKR - I don't have this in my portfolio yet but will be looking to add due to TSM's involvement in Arizona and potential to be a big partner in the US supply chain (as America tries to push TSM toward US fab + manufacturing).

WLAC - Neocloud SPAC IPO, large upside. I talk about this a lot recently, but it's probably one of the best valued Neoclouds out there, and already has great profit margins (not a pivot from miners, where it's a bit more uncertain). They work with Fluidstack, and I'd expect a 500%+ re-rating on top of a Mag7 contract.

AMZN - $213 is insane lol. I have no clue how this is down -3% YTD during a bull market.

LTC - Affected by crypto liquidations and government shutdown delaying ETFs. Great time to buy and just wait for ETF to be approved.

RDDT - Great dip to $190. I thought $200 would be a bottom but ended up going lower. The news about ChatGPT citing it less caused a large sell-off which I think was very immaterial.

HIMS - 14%+ drop off CEO share sale. Owners sell shares all the time, it doesn't really affect the fundamentals of the company much, just short term sentiment. I'd expect it to rebound.

IBIT - Bitcoin $108k great entry point, it's been swinging between $110k - $120k for awhile so anything under is usually great.

ALAB - I said this last time but it sold off way too much from news of a new competitor. It's already competing vs AVGO in the market lol, NVDA-like margins, growing hundreds of percent Y/Y, Mag7 using them in data center buildout. 

CRDO - Similar thesis to ALAB, sold off alongside Astera but a bit less.

SMCI - Should get re-rated for 55%+ or so revenue growth into next year. I doubted the projections earlier but with the data center growth, it's looking realistic.

FLY - This was a medium lift payload play. People doubt fly's execution but NOC co-developing medium lift takes a lot of risk off the table (and possible re-rating it 500%+ when it competes vs falcon9)

SNAP - Did the math on Snap monetization of memories in an earlier DD post and it's completely not priced in yet. It's doing $1.3B+ quarterly revenue on a $13B market cap lol, and the amount FCF they would get from increasing their revenue + lowering Google OPEX costs is insane.

ETOR  - Majority cash, growing at IBKR rates, suffering from tax harvesting

LULU - Suffering from tax harvesting + competition from Alo, Vuori, etc. But seasonally should be good, and extremely low p/e now.

Buy
AMD - ChatGPT putting in AMD orders, ORCL building out AMD data centers. Likely going to get a re-rating in the next year as a potential $NVDA competitor. Still think Nvidia will dominate but with it's 4.5T marketcap, AMD has a lot to catch up on even if it takes a small percent share.

HOOD - Looking at a lot better after the 10%+ correction. Could pull a PLTR

RBRK - Did DD on this earlier, looks better on the drop as a cybersecurity company really low multiples in the space. Just needs to cut back on marketing, customers sticky. 

UNH - Healthcare is sht in America but not going anywhere. Think Warren and the others know this 

TGT 🐈 - Dividend next moth, big dividend stock. Around now is a good time to load up IMO

IREN 🐈 - Huge GW, expect mag7 or similar deal. 

WYFI - Any neocloud is a buy (eg. see thesis on mag7 funneling revenue down toward these small 1B-5B companies)

WULF - neocloud play

CIFR - neocloud play

SLNH - neocloud play

BITF - neocloud play

GLXY - neocloud derivative play

FLNC - neocloud energy play

MU - China derisked, memory had a huge market there, memory also likely going to get re-rating in tdata center buildout

_

Sell

ETH - Not a fan of Ethereum at $4k+
BMNR - If I don't like Ethereum at these levels, no point of holding treasury companies 
PL - Low revenue, space stock (extremely high valuation)
BLSKY -Low revenue, space stock (extremely high valuation)
RGTI - Quantum bubble
OKLO - Nuclear bubble
IONQ -Quantum bubble 
QBTS - Quantum bubble

_

Quick macro heads up:
-> Rate cut in 9 days ~97% odds. Frontrunning expected, go long.  That's all.
```

### [亏损 #33] SEI long hz=6m — pub=2025-10-15T07:42:21
- entry=2025-10-16, $55.36
- 1m: **resolved_miss** raw=-18.33% bench=+1.71% excess=-20.04%
- 3m: excess=-3.29%  6m: excess=+11.69%
- **条件 label**: ['PRICE_TARGET']
- **if 句**: ['This would be a $3T company if this were a US company, insane profit margins, insane growth rate for their size', '5T), even if buying at ATHs', "AMZN hitting $213-215 today was a good chance to stock up since it usually floats between $218-$227 if you're short term swing trading but long term I'd expect it to catchup to other mag7"]
- **原文 (全文)**:
```
The Great Soybean/Seed Oil Crash, personal thoughts and explanations:

Strong Buy
$ALAB
$CRDO
$NBIS
$WLAC
$LTC
$TSM
$BTC
(+ same as tax harvest stocks last time)
$AMZN
$SMCI
_

Buy
$AMD
$FLNC
$SEI
$BZAI
$NKLR
$IREN
$WULF
$CIFR
$CRWV
$BITF
$WYFI
$SLNH
$BITF
$RBRK
$GLXY
$GRAB
$SEA
$META
$TGT
$SNAP
$MU
$RKLB
$FLY
$UNH

Hold
$MP
$HOOD
$EOSE
$NVDA
$GOOGL
$DFLI
$SOFI
$VIRT
$RR
$AVGO
$BE
$ASTS

(Hit the ticker maximum but everything else from last post, still sell on Quantum or Oklo)
_

Strong Buys
ALAB - Huge part of datacenter buildout, NVDA like margins, Mag7 customers. Already had competitors from AVGO,  really don't think Arista would be a competitive threat.

CRDO - Same sell-off as ALAB, thought they were both kind of overvalued before, but now they're back in correction territory so good to stock up.

NBIS - $400 PT bull case. We have macro tailwind from government re-opening + rate cut EOM october into earnings, so short term looks promising. Lot of things going for it (eg. meta x crwv, so there's potential for more mag7 clients), sum of parts doing well, eg. clickhouse, and scaling rev from $100m to $1.5B+ a quarter is insane. there's already contracts locked in its just a matter of company execution.

WLAC - Wrote a thesis about this earlier at $13. Even at $14.5 strong because it can re-rate 100%+ easily.

LTC - Affected by leverage traders and government shutdown. The shutdown is predicted to last awhile and the main reason to buy was the ETF getting approved. But a great buy sub <$100 anyway, because it will get approved in due time (~95% chance).

TSM - Holy crap. This would be a $3T company if this were a US company, insane profit margins, insane growth rate for their size. And every post you see about OpenAi X (**sydney sweeney partnership) or AMD buildout/NVDA buildout. TSM is the center of it all and would easily be a $2T+ company (from here at ~$1.5T), even if buying at ATHs.

BTC - $112K good entry point. Goldt keeps hitting ATH, nothing really changed fundamentally, just lot of liquidations recently
(+ same as tax harvest stocks last time)

AMZN - I really don't know how it's still down YTD. I don't think Amazon needs much explaining but still growing  (eg. AWS backlog massive, still going like 24% but not as much as ORCL, GCP and others obviously), but with EOY seasonality and runup to Feb, now is probably the best chance to catch the bottom. AMZN hitting $213-215 today was a good chance to stock up since it usually floats between $218-$227 if you're short term swing trading but long term I'd expect it to catchup to other mag7.

SMCI - Underrated. Markets were looking short term performance, and Charles was quoting like 55%+ Y/Y forward revenue growth which nobody believed + backlog that didnt get realized yet. But now with all the data center buildouts, now it's kinda making sense. So should re-rate in the next two earnings.

_
Buy

AMD - So many deals from OpenAI x AMD, oracle building out with AMD, this is going to re-rate to a potential $1T+ company if it's actually a strong competitive to $NVDA.  I don't think it's winner takes all and you can see a $4.5T+ market cap size with NVDA and some $350B marketcap size with AMD, so we can see a large ramp up (OpenAI is usually the leader in frontier models and if Sam says they can use AMD chips + elon said its' good for small-medium weight models, prboably means something positive)

FLNC - Strong re-rate on energy after AI consumption, great buy.

SEI - Strong re-rate on energy after AI consumption, great buy.

BZAI - Someone else did a DD on this company, just cause of sector and shift to edge compute (eg. Robotics goign to be hot). Because of low MC and runup of similar companies could turn out well.

NKLR - Nuclear stocks like $OKLO have been taking off, this is just follow the lader.

IREN - Needs no introduction, huge GW compute capacity just no announced mag7 deals yet but could come anytime -> strong re-rate. Only reason not a strong buy is because not fully convinced miners can pivot like CRWV and maintain great margins (eg. $ORCL hit piece) but we'll see.

WULF - GOOGL backlog, another $3.6+ or so in funding helps a lot.

CIFR - Lot of info on X about future capacity and strong re-rating. Always liked this company because it was NBIS-lite. You can probably buy any Neocloud and it will go up because the sector is incredibly high potential with Mag7 funneling revenue.

CRWV - Didn't like this as much as others because of debt but because of the seed oil correction much better buy point at $134 (below when META deal was announced)

BITF - Same in Neocloud category

WYFI - Same in Neocloud category

BITF - Same in Neocloud category

GLXY - Same in Neocloud category, helps with their buildout

RBRK - Did a DD on this, great buy for cybersecurity sector in mid term, they just need to scale back marketing and then it looks like they have a lot more FCF because they're spending most OPEX on marketing.

GRAB - Great fundamentally, -6.56% correction good to buy again

SEA - AMZN in SEA, tons of people use them. Just a buy just because of costumer base + monetization potenetial. Fundamentally growing $5B+ rev 38% Y/Y is also great.

META - I really don't like all their expensive capex on AI since they're not really putting out fronteir models like ChatGPT with it, who knows what Zuck is doing. But that aside, down 7.3% over the month, going to $700 support, probably a good buy around here to play catchup.

TGT - Dividend next month good catalyst.

SNAP - The Jenners are coming back (helps with popularity), they're shifting former memory opex to revenue, and this will probably cause a HUGE rerating next year. Just suffers from tax harvesting otherwise would be a strong buy rn. Usually tax harvesting events are kinda done in December.

MU - Now that China fears are kinda less intense, MU is a lot stronger buy just cause of memory use on buildout.

RKLB - Neutron, golden dome contracts, lot of cataylsts

FLY - Medium lift

UNH - Healthcare stock not affected by soybeans but had a correction. Would likely go up one instituions post their ports (eg. warren likely bought more)

Random thoughts
Basically any growth/risk stock that's not named Oklo is great because we have

-> Rate Cut end of month October
-> Government re-opening sometime (likely around end of Oct or early Nov)

Into
-> Rate Cut December.
-> Midterms (Bullish for stocks)

Usually market crashes happen when there's tightening not easing. And your stupid quantum bubbles would likely continue for another 3-12 months afterward. If you're short, then probably wait till next Feb.

Anyway, this is a great time for risk-on, and specially riding trends with neoclouds -> affiliated sectors (eg. energy) -> affiliated companies (eg. smci, tsm, etc).

I half joke-about soybeans because it likely signed escalating tensions, but I'd probably see a run-up into next year. Also I could write up a lot about each one but it's pretty time consuming but I'll put on a thesis post about random ones eg. $RBRK, from time to time.

Space/robotics/energy/quantum/ai/semi/critical top verticals right now, don't fight against momentum. I can think something is overvalued (eg. some critical materials bc. it's still spectulative compared to neoclouds that kinda have guaranteed rev based on execution from mag7) but I wouldn't short it into rate cuts.

Just personal thoughts, NFA
```

### [亏损 #34] DPRO long hz=long_term — pub=2026-01-20T14:35:20
- entry=2026-01-21, $9.67
- 1m: **resolved_miss** raw=-18.41% bench=+0.59% excess=-19.00%
- 3m: excess=-36.65%  6m: excess=+0.00%
- **条件 label**: ['PRICE_TARGET']
- **原文 (全文)**:
```
I’ve initiated small positions in $DPRO ($240m).  

This is an end-to-end war drone contractor and Draganfly looks like the $RKLB to Ondas.  

$ONDS went from ($.51 -> $15, 13x) and was looking for an equivalent.

Here’s what markets (and myself missed). 

Draganfly is a vertically integrated defense prime, not just a drone maker.   

$DPRO controls the entire ecosystem, from the factory infrastructure to the end-drone. And it’s the largest beneficiary of NDAA that banned DJI, which controlled est. 70-80% of market share.

The biggest moat I didn’t understand earlier: embedded production.

I looked small current revenue numbers but missed the that they’re buildout distributed manufacturing throughout many US bases.

Draganfly’s contract with the U.S. Army (Sept 2025) isn't just to ship drones; it is to install Micro-Factories at US bases.

It integrates Draganfly into the fabric of US Dpt. of War, creating a layer of "stickiness" that is impossible for competitors to displace.

Here's why I entered positions: they went from $5M drone capacity ramp in 2025 to $400m.

Combining this with its partnership with Global Ordnance (where it’s a sub-contractor and Ordnance received $750 Million IDIQ), US-CAD programs (benefits from both) like $220m CAD funding to NATO.

It’s possible for $DPRO from triple digits or possibly 1000%+ revenue growth rates Y/Y.

And... revenue hits balance sheet by surprise in the earnings.

Each drone player from $AVAV, $AIRO, $ONDS, have their own specialty, $DPRO focuses on the nonkinetic and infrastructure aspect:

-> European countries like Sweden use $DPRO drones (2026) for life-saving operations.
-> DEF-C -> reconnaissance drones for Ukraine conflict -> Global Ordnance (massive defense contractor)
-> U.S. Department of War (US Army)

and those nonkinetic drones can be transformed with kinetic applications.

With $51M cash on hand (healthy balance sheet), just 20% of capacity ramp would be ~2.2 fwd p/s.

This is a very speculative venture style bet as they've been rapidly expanding infrastructure (like $RKLB at the start), with Northland giving $20 PT's.

And this is a hunch that the revenue will catch up to the infrastructure they've deployed across the US army (esp. with Replicator programs and is hidden until earnings). 

$DPRO has already been popular on FinX (and it took some convincing from other users) so I've personally joined the party as I'm curious to see where it heads.

TLDR: took small speculative positions in $DPRO as it's setup to be the Infrastructure of Drone Warfare (like $RKLB back at $2 for space) with high potential upside.

 As it's extremely early, there's lot of risks as well with revenue recognition from capacity buildout.
```

### [亏损 #35] ETOR long hz=6m — pub=2025-10-04T01:22:20
- entry=2025-10-06, $41.30
- 1m: **resolved_miss** raw=-16.61% bench=+0.54% excess=-17.15%
- 3m: excess=-22.09%  6m: excess=-23.61%
- **条件 label**: ['PRICE_TARGET']
- **if 句**: ["BMNR - Just buy ETH if you believe in it but I wouldn't buy at ETH at $4500"]
- **原文 (全文)**:
```
Friday Market Close, Personal Thoughts and Explanations:

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

Reddit - Dropped 29% off immaterial news that ChatGPT wasn't citing it as much. Nobody visits Reddit through ChatGPT, good recovery buy off $200 support. 

SNAP - Finally they're doing something that's USEFUL for the first time in many years lol. Tons of Capex was spent on storing photos random drawings people saved 12 years ago taking GBs of space for their insane Google Cloud costs. They're finally monetizing it like Apple. Huge tailwind, should improve net income by a ton next year. 

AMZN - Under $220 now, great buy. AMZN prime Oct 8th, good for seasonality in Nov/Dec.

ETOR - I can't believe this is still $41. 33% cash, 1B+ cash pile growing at IBKR rates. Just suffers from tax harvesting I'd assume it goes up next year. 

NBIS - Strong buy until $150+ or new hyperscaler contract repricing. 

LTC - ETF catalyst delayed from Gov shutdown but should be approved anyway. 

Buys

Upwork - Down 4.5% or so for no reason, should recover

MSTR - BTC close to all time highs, MSTR way off ATHs cause of long btc short MSTR but NAV premium should catch up again from the BTC fomo.

ORCL - Standard rise on great forward earnings, drop for short term option chain, then rise because 14B tiktok deal and large future cloud contracts

TGT - Just undervalued great buy under $93, dividend catalyst next month

CIFR - NBIS light with GOOGL deal.

VIRT - VIX doesn't look like it's going down anytime soon but they're trading at like 6.4 or so forward P/E so it's worth.

CRDO - Good buy on correction with hypescaler buildout

WULF - Hasn't gone up as much as the other neoclouds, googl backlog

SOFI - Corrected, might recover back to ATH given macro tailwind

META - Monthly low good DCA, not as good as AMZN

AVGO - Same as ORCL, might end up like NVDA one day with hyperscaler chips

MRVL - Still down 24% YTD. 

SMCI - Good buy on datacenter buildout + server racks

Dell - Good buy on datacenter buildout + server racks

Hold

Nothing changed

Sell

TSLA - Overvalued, better longs like NBIS

CRCL - I will keep making this argument, but just buy COIN instead. You will get the same 50% revenue sharing but with a crypto exchange + ETF holding income too.  

PLTR - Disconnected from reality

BMNR - Just buy ETH if you believe in it but I wouldn't buy at ETH at $4500.

Strong Sell

RGTI - Disconnected from reality lol

All disconnected from reality, wouldn't short though cause all cult stocks. 
OKLO
QBTS
IONQ
```

### [亏损 #36] NBIS long hz=6m — pub=2025-10-04T01:22:20
- entry=2025-10-06, $132.40
- 1m: **resolved_miss** raw=-16.51% bench=+0.54% excess=-17.05%
- 3m: excess=-30.01%  6m: excess=+1.73%
- **条件 label**: ['PRICE_TARGET']
- **if 句**: ["BMNR - Just buy ETH if you believe in it but I wouldn't buy at ETH at $4500"]
- **原文 (全文)**:
```
Friday Market Close, Personal Thoughts and Explanations:

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

Reddit - Dropped 29% off immaterial news that ChatGPT wasn't citing it as much. Nobody visits Reddit through ChatGPT, good recovery buy off $200 support. 

SNAP - Finally they're doing something that's USEFUL for the first time in many years lol. Tons of Capex was spent on storing photos random drawings people saved 12 years ago taking GBs of space for their insane Google Cloud costs. They're finally monetizing it like Apple. Huge tailwind, should improve net income by a ton next year. 

AMZN - Under $220 now, great buy. AMZN prime Oct 8th, good for seasonality in Nov/Dec.

ETOR - I can't believe this is still $41. 33% cash, 1B+ cash pile growing at IBKR rates. Just suffers from tax harvesting I'd assume it goes up next year. 

NBIS - Strong buy until $150+ or new hyperscaler contract repricing. 

LTC - ETF catalyst delayed from Gov shutdown but should be approved anyway. 

Buys

Upwork - Down 4.5% or so for no reason, should recover

MSTR - BTC close to all time highs, MSTR way off ATHs cause of long btc short MSTR but NAV premium should catch up again from the BTC fomo.

ORCL - Standard rise on great forward earnings, drop for short term option chain, then rise because 14B tiktok deal and large future cloud contracts

TGT - Just undervalued great buy under $93, dividend catalyst next month

CIFR - NBIS light with GOOGL deal.

VIRT - VIX doesn't look like it's going down anytime soon but they're trading at like 6.4 or so forward P/E so it's worth.

CRDO - Good buy on correction with hypescaler buildout

WULF - Hasn't gone up as much as the other neoclouds, googl backlog

SOFI - Corrected, might recover back to ATH given macro tailwind

META - Monthly low good DCA, not as good as AMZN

AVGO - Same as ORCL, might end up like NVDA one day with hyperscaler chips

MRVL - Still down 24% YTD. 

SMCI - Good buy on datacenter buildout + server racks

Dell - Good buy on datacenter buildout + server racks

Hold

Nothing changed

Sell

TSLA - Overvalued, better longs like NBIS

CRCL - I will keep making this argument, but just buy COIN instead. You will get the same 50% revenue sharing but with a crypto exchange + ETF holding income too.  

PLTR - Disconnected from reality

BMNR - Just buy ETH if you believe in it but I wouldn't buy at ETH at $4500.

Strong Sell

RGTI - Disconnected from reality lol

All disconnected from reality, wouldn't short though cause all cult stocks. 
OKLO
QBTS
IONQ
```

### [亏损 #37] WYFI long hz=long_term — pub=2025-10-07T22:30:56
- entry=2025-10-08, $33.89
- 1m: **resolved_miss** raw=-17.23% bench=-0.42% excess=-16.82%
- 3m: excess=-50.83%  6m: excess=-57.05%
- **条件 label**: ['PRICE_TARGET']
- **原文 (全文)**:
```
True. Jokes aside (sorry to scare @DeepValueBagger) $WYFI's edge is probably converting facilities for 40% lower cost than greenfield (built from scratch) data centers that others need to build, and they're not lease heavy. 

It's also pure play HPC compared to miners. 

Downside is they don't build their own orchestration stack like $NBIS or scale as fast as $IREN. But they own the infrastructure instead of leasing. Vertically integrated HPC infrastructure for hardware and psychical only. 

I'm just going off the assumption there's room to grow across all Neoclouds and there's more room for re-rating considering the small $1.3B market cap size.

The analysts at Clear Street that gave a $51 PT probably do a better job with number crunching so I'd just refer to them.
```

### [亏损 #38] META long hz=6m — pub=2025-10-15T07:42:21
- entry=2025-10-16, $717.55
- 1m: **resolved_miss** raw=-15.06% bench=+1.71% excess=-16.77%
- 3m: excess=-18.37%  6m: excess=-13.36%
- **条件 label**: ['PRICE_TARGET']
- **if 句**: ['This would be a $3T company if this were a US company, insane profit margins, insane growth rate for their size', '5T), even if buying at ATHs', "AMZN hitting $213-215 today was a good chance to stock up since it usually floats between $218-$227 if you're short term swing trading but long term I'd expect it to catchup to other mag7"]
- **原文 (全文)**:
```
The Great Soybean/Seed Oil Crash, personal thoughts and explanations:

Strong Buy
$ALAB
$CRDO
$NBIS
$WLAC
$LTC
$TSM
$BTC
(+ same as tax harvest stocks last time)
$AMZN
$SMCI
_

Buy
$AMD
$FLNC
$SEI
$BZAI
$NKLR
$IREN
$WULF
$CIFR
$CRWV
$BITF
$WYFI
$SLNH
$BITF
$RBRK
$GLXY
$GRAB
$SEA
$META
$TGT
$SNAP
$MU
$RKLB
$FLY
$UNH

Hold
$MP
$HOOD
$EOSE
$NVDA
$GOOGL
$DFLI
$SOFI
$VIRT
$RR
$AVGO
$BE
$ASTS

(Hit the ticker maximum but everything else from last post, still sell on Quantum or Oklo)
_

Strong Buys
ALAB - Huge part of datacenter buildout, NVDA like margins, Mag7 customers. Already had competitors from AVGO,  really don't think Arista would be a competitive threat.

CRDO - Same sell-off as ALAB, thought they were both kind of overvalued before, but now they're back in correction territory so good to stock up.

NBIS - $400 PT bull case. We have macro tailwind from government re-opening + rate cut EOM october into earnings, so short term looks promising. Lot of things going for it (eg. meta x crwv, so there's potential for more mag7 clients), sum of parts doing well, eg. clickhouse, and scaling rev from $100m to $1.5B+ a quarter is insane. there's already contracts locked in its just a matter of company execution.

WLAC - Wrote a thesis about this earlier at $13. Even at $14.5 strong because it can re-rate 100%+ easily.

LTC - Affected by leverage traders and government shutdown. The shutdown is predicted to last awhile and the main reason to buy was the ETF getting approved. But a great buy sub <$100 anyway, because it will get approved in due time (~95% chance).

TSM - Holy crap. This would be a $3T company if this were a US company, insane profit margins, insane growth rate for their size. And every post you see about OpenAi X (**sydney sweeney partnership) or AMD buildout/NVDA buildout. TSM is the center of it all and would easily be a $2T+ company (from here at ~$1.5T), even if buying at ATHs.

BTC - $112K good entry point. Goldt keeps hitting ATH, nothing really changed fundamentally, just lot of liquidations recently
(+ same as tax harvest stocks last time)

AMZN - I really don't know how it's still down YTD. I don't think Amazon needs much explaining but still growing  (eg. AWS backlog massive, still going like 24% but not as much as ORCL, GCP and others obviously), but with EOY seasonality and runup to Feb, now is probably the best chance to catch the bottom. AMZN hitting $213-215 today was a good chance to stock up since it usually floats between $218-$227 if you're short term swing trading but long term I'd expect it to catchup to other mag7.

SMCI - Underrated. Markets were looking short term performance, and Charles was quoting like 55%+ Y/Y forward revenue growth which nobody believed + backlog that didnt get realized yet. But now with all the data center buildouts, now it's kinda making sense. So should re-rate in the next two earnings.

_
Buy

AMD - So many deals from OpenAI x AMD, oracle building out with AMD, this is going to re-rate to a potential $1T+ company if it's actually a strong competitive to $NVDA.  I don't think it's winner takes all and you can see a $4.5T+ market cap size with NVDA and some $350B marketcap size with AMD, so we can see a large ramp up (OpenAI is usually the leader in frontier models and if Sam says they can use AMD chips + elon said its' good for small-medium weight models, prboably means something positive)

FLNC - Strong re-rate on energy after AI consumption, great buy.

SEI - Strong re-rate on energy after AI consumption, great buy.

BZAI - Someone else did a DD on this company, just cause of sector and shift to edge compute (eg. Robotics goign to be hot). Because of low MC and runup of similar companies could turn out well.

NKLR - Nuclear stocks like $OKLO have been taking off, this is just follow the lader.

IREN - Needs no introduction, huge GW compute capacity just no announced mag7 deals yet but could come anytime -> strong re-rate. Only reason not a strong buy is because not fully convinced miners can pivot like CRWV and maintain great margins (eg. $ORCL hit piece) but we'll see.

WULF - GOOGL backlog, another $3.6+ or so in funding helps a lot.

CIFR - Lot of info on X about future capacity and strong re-rating. Always liked this company because it was NBIS-lite. You can probably buy any Neocloud and it will go up because the sector is incredibly high potential with Mag7 funneling revenue.

CRWV - Didn't like this as much as others because of debt but because of the seed oil correction much better buy point at $134 (below when META deal was announced)

BITF - Same in Neocloud category

WYFI - Same in Neocloud category

BITF - Same in Neocloud category

GLXY - Same in Neocloud category, helps with their buildout

RBRK - Did a DD on this, great buy for cybersecurity sector in mid term, they just need to scale back marketing and then it looks like they have a lot more FCF because they're spending most OPEX on marketing.

GRAB - Great fundamentally, -6.56% correction good to buy again

SEA - AMZN in SEA, tons of people use them. Just a buy just because of costumer base + monetization potenetial. Fundamentally growing $5B+ rev 38% Y/Y is also great.

META - I really don't like all their expensive capex on AI since they're not really putting out fronteir models like ChatGPT with it, who knows what Zuck is doing. But that aside, down 7.3% over the month, going to $700 support, probably a good buy around here to play catchup.

TGT - Dividend next month good catalyst.

SNAP - The Jenners are coming back (helps with popularity), they're shifting former memory opex to revenue, and this will probably cause a HUGE rerating next year. Just suffers from tax harvesting otherwise would be a strong buy rn. Usually tax harvesting events are kinda done in December.

MU - Now that China fears are kinda less intense, MU is a lot stronger buy just cause of memory use on buildout.

RKLB - Neutron, golden dome contracts, lot of cataylsts

FLY - Medium lift

UNH - Healthcare stock not affected by soybeans but had a correction. Would likely go up one instituions post their ports (eg. warren likely bought more)

Random thoughts
Basically any growth/risk stock that's not named Oklo is great because we have

-> Rate Cut end of month October
-> Government re-opening sometime (likely around end of Oct or early Nov)

Into
-> Rate Cut December.
-> Midterms (Bullish for stocks)

Usually market crashes happen when there's tightening not easing. And your stupid quantum bubbles would likely continue for another 3-12 months afterward. If you're short, then probably wait till next Feb.

Anyway, this is a great time for risk-on, and specially riding trends with neoclouds -> affiliated sectors (eg. energy) -> affiliated companies (eg. smci, tsm, etc).

I half joke-about soybeans because it likely signed escalating tensions, but I'd probably see a run-up into next year. Also I could write up a lot about each one but it's pretty time consuming but I'll put on a thesis post about random ones eg. $RBRK, from time to time.

Space/robotics/energy/quantum/ai/semi/critical top verticals right now, don't fight against momentum. I can think something is overvalued (eg. some critical materials bc. it's still spectulative compared to neoclouds that kinda have guaranteed rev based on execution from mag7) but I wouldn't short it into rate cuts.

Just personal thoughts, NFA
```

### [亏损 #39] FLNC long hz=6m — pub=2025-10-15T07:42:21
- entry=2025-10-16, $20.93
- 1m: **resolved_miss** raw=-14.43% bench=+1.71% excess=-16.14%
- 3m: excess=+19.32%  6m: excess=-45.56%
- **条件 label**: ['PRICE_TARGET']
- **if 句**: ['This would be a $3T company if this were a US company, insane profit margins, insane growth rate for their size', '5T), even if buying at ATHs', "AMZN hitting $213-215 today was a good chance to stock up since it usually floats between $218-$227 if you're short term swing trading but long term I'd expect it to catchup to other mag7"]
- **原文 (全文)**:
```
The Great Soybean/Seed Oil Crash, personal thoughts and explanations:

Strong Buy
$ALAB
$CRDO
$NBIS
$WLAC
$LTC
$TSM
$BTC
(+ same as tax harvest stocks last time)
$AMZN
$SMCI
_

Buy
$AMD
$FLNC
$SEI
$BZAI
$NKLR
$IREN
$WULF
$CIFR
$CRWV
$BITF
$WYFI
$SLNH
$BITF
$RBRK
$GLXY
$GRAB
$SEA
$META
$TGT
$SNAP
$MU
$RKLB
$FLY
$UNH

Hold
$MP
$HOOD
$EOSE
$NVDA
$GOOGL
$DFLI
$SOFI
$VIRT
$RR
$AVGO
$BE
$ASTS

(Hit the ticker maximum but everything else from last post, still sell on Quantum or Oklo)
_

Strong Buys
ALAB - Huge part of datacenter buildout, NVDA like margins, Mag7 customers. Already had competitors from AVGO,  really don't think Arista would be a competitive threat.

CRDO - Same sell-off as ALAB, thought they were both kind of overvalued before, but now they're back in correction territory so good to stock up.

NBIS - $400 PT bull case. We have macro tailwind from government re-opening + rate cut EOM october into earnings, so short term looks promising. Lot of things going for it (eg. meta x crwv, so there's potential for more mag7 clients), sum of parts doing well, eg. clickhouse, and scaling rev from $100m to $1.5B+ a quarter is insane. there's already contracts locked in its just a matter of company execution.

WLAC - Wrote a thesis about this earlier at $13. Even at $14.5 strong because it can re-rate 100%+ easily.

LTC - Affected by leverage traders and government shutdown. The shutdown is predicted to last awhile and the main reason to buy was the ETF getting approved. But a great buy sub <$100 anyway, because it will get approved in due time (~95% chance).

TSM - Holy crap. This would be a $3T company if this were a US company, insane profit margins, insane growth rate for their size. And every post you see about OpenAi X (**sydney sweeney partnership) or AMD buildout/NVDA buildout. TSM is the center of it all and would easily be a $2T+ company (from here at ~$1.5T), even if buying at ATHs.

BTC - $112K good entry point. Goldt keeps hitting ATH, nothing really changed fundamentally, just lot of liquidations recently
(+ same as tax harvest stocks last time)

AMZN - I really don't know how it's still down YTD. I don't think Amazon needs much explaining but still growing  (eg. AWS backlog massive, still going like 24% but not as much as ORCL, GCP and others obviously), but with EOY seasonality and runup to Feb, now is probably the best chance to catch the bottom. AMZN hitting $213-215 today was a good chance to stock up since it usually floats between $218-$227 if you're short term swing trading but long term I'd expect it to catchup to other mag7.

SMCI - Underrated. Markets were looking short term performance, and Charles was quoting like 55%+ Y/Y forward revenue growth which nobody believed + backlog that didnt get realized yet. But now with all the data center buildouts, now it's kinda making sense. So should re-rate in the next two earnings.

_
Buy

AMD - So many deals from OpenAI x AMD, oracle building out with AMD, this is going to re-rate to a potential $1T+ company if it's actually a strong competitive to $NVDA.  I don't think it's winner takes all and you can see a $4.5T+ market cap size with NVDA and some $350B marketcap size with AMD, so we can see a large ramp up (OpenAI is usually the leader in frontier models and if Sam says they can use AMD chips + elon said its' good for small-medium weight models, prboably means something positive)

FLNC - Strong re-rate on energy after AI consumption, great buy.

SEI - Strong re-rate on energy after AI consumption, great buy.

BZAI - Someone else did a DD on this company, just cause of sector and shift to edge compute (eg. Robotics goign to be hot). Because of low MC and runup of similar companies could turn out well.

NKLR - Nuclear stocks like $OKLO have been taking off, this is just follow the lader.

IREN - Needs no introduction, huge GW compute capacity just no announced mag7 deals yet but could come anytime -> strong re-rate. Only reason not a strong buy is because not fully convinced miners can pivot like CRWV and maintain great margins (eg. $ORCL hit piece) but we'll see.

WULF - GOOGL backlog, another $3.6+ or so in funding helps a lot.

CIFR - Lot of info on X about future capacity and strong re-rating. Always liked this company because it was NBIS-lite. You can probably buy any Neocloud and it will go up because the sector is incredibly high potential with Mag7 funneling revenue.

CRWV - Didn't like this as much as others because of debt but because of the seed oil correction much better buy point at $134 (below when META deal was announced)

BITF - Same in Neocloud category

WYFI - Same in Neocloud category

BITF - Same in Neocloud category

GLXY - Same in Neocloud category, helps with their buildout

RBRK - Did a DD on this, great buy for cybersecurity sector in mid term, they just need to scale back marketing and then it looks like they have a lot more FCF because they're spending most OPEX on marketing.

GRAB - Great fundamentally, -6.56% correction good to buy again

SEA - AMZN in SEA, tons of people use them. Just a buy just because of costumer base + monetization potenetial. Fundamentally growing $5B+ rev 38% Y/Y is also great.

META - I really don't like all their expensive capex on AI since they're not really putting out fronteir models like ChatGPT with it, who knows what Zuck is doing. But that aside, down 7.3% over the month, going to $700 support, probably a good buy around here to play catchup.

TGT - Dividend next month good catalyst.

SNAP - The Jenners are coming back (helps with popularity), they're shifting former memory opex to revenue, and this will probably cause a HUGE rerating next year. Just suffers from tax harvesting otherwise would be a strong buy rn. Usually tax harvesting events are kinda done in December.

MU - Now that China fears are kinda less intense, MU is a lot stronger buy just cause of memory use on buildout.

RKLB - Neutron, golden dome contracts, lot of cataylsts

FLY - Medium lift

UNH - Healthcare stock not affected by soybeans but had a correction. Would likely go up one instituions post their ports (eg. warren likely bought more)

Random thoughts
Basically any growth/risk stock that's not named Oklo is great because we have

-> Rate Cut end of month October
-> Government re-opening sometime (likely around end of Oct or early Nov)

Into
-> Rate Cut December.
-> Midterms (Bullish for stocks)

Usually market crashes happen when there's tightening not easing. And your stupid quantum bubbles would likely continue for another 3-12 months afterward. If you're short, then probably wait till next Feb.

Anyway, this is a great time for risk-on, and specially riding trends with neoclouds -> affiliated sectors (eg. energy) -> affiliated companies (eg. smci, tsm, etc).

I half joke-about soybeans because it likely signed escalating tensions, but I'd probably see a run-up into next year. Also I could write up a lot about each one but it's pretty time consuming but I'll put on a thesis post about random ones eg. $RBRK, from time to time.

Space/robotics/energy/quantum/ai/semi/critical top verticals right now, don't fight against momentum. I can think something is overvalued (eg. some critical materials bc. it's still spectulative compared to neoclouds that kinda have guaranteed rev based on execution from mag7) but I wouldn't short it into rate cuts.

Just personal thoughts, NFA
```

### [亏损 #40] SAFRY long hz=long_term — pub=2026-04-05T04:56:46
- entry=2026-04-06, $84.85
- 1m: **resolved_miss** raw=-6.23% bench=+9.84% excess=-16.07%
- 3m: excess=+0.00%  6m: excess=+0.00%
- **条件 label**: ['EVENT_VERB']
- **if 句**: ['Then if it fails fallback would be names like:', 'Analysis states that if the optical mesh fails due to clouds or lack of stations, the architecture "falls back to Ka-band RF links"', 'But not quite sure if capex is to the scale of hyperscaler AI buildouts yet to benefit these companies enough']
- **原文 (全文)**:
```
The Space Bottleneck: Optical ground infrastructure.

- "The industry has built roughly 10 percent of the optical ground infrastructure"

Now, who are the beneficiaries?

- $EOS.ASX (operating stations at Mt. Stromlo equipped with "adaptive optics.") 
- $SKPJF (TYO: 9412) |  $NTTYY | Space Compass is JV with NTT and satellite operator SKY Perfect JSAT
- $SGBAF - Works with Cailabs to for terrestrial optical terminals
- $SAFRY - Manufacturer of the optical ground stations

Then if it fails fallback would be names like:
$VSAT, $GILT

Analysis states that if the optical mesh fails due to clouds or lack of stations, the architecture "falls back to Ka-band RF links". 
 
-> Near term capital flows to Relay Providers (Kepler, Space Compass, General Atomics). 

-> Long term structural winners will be the photonics hardware manufacturers (Cailabs, Safran).

-> Then companies like SpaceX wins by default. Many are private. 

"This infrastructure deficit is no longer just an engineering problem but a direct threat to a major White House [Golden Dome] policy objective"

Orbital laser communications market are hard-capped until physical ground infra scales, hence the current bottleneck. 

But not quite sure if capex is to the scale of hyperscaler AI buildouts yet to benefit these companies enough.
```

### [亏损 #41] SNAP long hz=1y — pub=2025-10-06T22:29:49
- entry=2025-10-07, $8.56
- 1m: **resolved_miss** raw=-14.77% bench=+1.26% excess=-16.03%
- 3m: excess=-4.97%  6m: excess=-45.27%
- **条件 label**: ['PRICE_TARGET']
- **if 句**: ["If you have the patience for shares for a year or two, I'd expect a 50%+ return, just whenever the market wants to price it in", "It's genuinely overvalued even if it's highest conviction 5Y long but at this point it might pull a $PLTR", "all these ten or hundred billion dollar deals if they're valued at 500B lol"]
- **原文 (全文)**:
```
Monday October 6th Market Close Thoughts:

- $NBIS extremely good dip buy. Down 2.38% after rising 5.78% in the morning. All other Neoclouds from $IREN to $CIFR held their 4%-14%+ gains. Nebius likely influenced by option flow, should play catchup soon and I stand by $225 PT. 

- $AMZN, $META two Mag7 that should outperform next 2-3 months and play catchup with the rest. Especially Amazon.

-  $SNAP, $RDDT two good recovery plays. Snapchat especially because of the revenue monetization changes. If you have the patience for shares for a year or two, I'd expect a 50%+ return, just whenever the market wants to price it in. Not everyone has patience and opportunity cost using the funds in $SNAP instead of Neoclouds might not be worth. 

Reddit I've maintained that the citations from ChatGPT is a BS reason for a 29% sell-off so I bought into it.

- $SPRB caught everyone's attention. I do expect it to keep rising to a $150-$200m marketcap from $75m but it's like playing Russian Roulette, usually dilution happens 2-3 days after a major event.

- Stuff like $RKLB, just need to hold lol. It's genuinely overvalued even if it's highest conviction 5Y long but at this point it might pull a $PLTR. 

- $AMD x OpenAI deal heavily bullish for semi industry. I expected $TSM, $ASML, energy stocks and Neoclouds to get a boost from AI infra buildout. Main negative ones were $CRWV, because of $NVDA dependencies and obviously NVDA, but Neoclouds aren't locked into one player, and they already have 5-10+ year contracts locked in.

It just puts a tiny dent in the $NVDA moat idea but nothing material yet. 

I personally think AMD might pull an $ORCL where it dips past rally, and then ends up pulling an $AVGO when markets start pricing in forward revenue. 

Then again, I don't know where OpenAI is getting all this money to promise Oracle, AMD, etc. all these ten or hundred billion dollar deals if they're valued at 500B lol. 

- Gold rallying to ATH every day just signals that $BTC is always a good buy, even at $123k, if it ends up becoming a hedge against inflation. It's close to 1/10th the market-cap. 

- $LTC still a great buy because of ETF approval. There's the government shutdown so people just forgot it hasn't happened yet, but should get approved eventually.

- $VIRT great buy at $32.5, I'd cost average around this range (sorry if you bought calls at $36, my positions are down 35% or so). But again it's an asymmetrical hedge to VIX (VIX IV very high for hedging, VIRT is undervalued ~6.3 forward p/e with buybacks an low IV), so even if positions are down, your other stocks should go up to balance it out. 

- Still looking into other beneficiaries of buildouts from energy stocks, small caps like $EOSE, memory like $MU, etc. that followers recommended. I try not to talk about something much until I'm informed myself.  

- If you're on leverage or going long, now is the time to do it until January. 3x rate cut, market probably frontrunning Oct rate cut now.
```

### [亏损 #42] ORCL long hz=6m — pub=2025-10-04T01:22:20
- entry=2025-10-06, $292.38
- 1m: **resolved_miss** raw=-15.12% bench=+0.54% excess=-15.66%
- 3m: excess=-36.72%  6m: excess=-54.08%
- **条件 label**: ['PRICE_TARGET']
- **if 句**: ["BMNR - Just buy ETH if you believe in it but I wouldn't buy at ETH at $4500"]
- **原文 (全文)**:
```
Friday Market Close, Personal Thoughts and Explanations:

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

Reddit - Dropped 29% off immaterial news that ChatGPT wasn't citing it as much. Nobody visits Reddit through ChatGPT, good recovery buy off $200 support. 

SNAP - Finally they're doing something that's USEFUL for the first time in many years lol. Tons of Capex was spent on storing photos random drawings people saved 12 years ago taking GBs of space for their insane Google Cloud costs. They're finally monetizing it like Apple. Huge tailwind, should improve net income by a ton next year. 

AMZN - Under $220 now, great buy. AMZN prime Oct 8th, good for seasonality in Nov/Dec.

ETOR - I can't believe this is still $41. 33% cash, 1B+ cash pile growing at IBKR rates. Just suffers from tax harvesting I'd assume it goes up next year. 

NBIS - Strong buy until $150+ or new hyperscaler contract repricing. 

LTC - ETF catalyst delayed from Gov shutdown but should be approved anyway. 

Buys

Upwork - Down 4.5% or so for no reason, should recover

MSTR - BTC close to all time highs, MSTR way off ATHs cause of long btc short MSTR but NAV premium should catch up again from the BTC fomo.

ORCL - Standard rise on great forward earnings, drop for short term option chain, then rise because 14B tiktok deal and large future cloud contracts

TGT - Just undervalued great buy under $93, dividend catalyst next month

CIFR - NBIS light with GOOGL deal.

VIRT - VIX doesn't look like it's going down anytime soon but they're trading at like 6.4 or so forward P/E so it's worth.

CRDO - Good buy on correction with hypescaler buildout

WULF - Hasn't gone up as much as the other neoclouds, googl backlog

SOFI - Corrected, might recover back to ATH given macro tailwind

META - Monthly low good DCA, not as good as AMZN

AVGO - Same as ORCL, might end up like NVDA one day with hyperscaler chips

MRVL - Still down 24% YTD. 

SMCI - Good buy on datacenter buildout + server racks

Dell - Good buy on datacenter buildout + server racks

Hold

Nothing changed

Sell

TSLA - Overvalued, better longs like NBIS

CRCL - I will keep making this argument, but just buy COIN instead. You will get the same 50% revenue sharing but with a crypto exchange + ETF holding income too.  

PLTR - Disconnected from reality

BMNR - Just buy ETH if you believe in it but I wouldn't buy at ETH at $4500.

Strong Sell

RGTI - Disconnected from reality lol

All disconnected from reality, wouldn't short though cause all cult stocks. 
OKLO
QBTS
IONQ
```

### [亏损 #43] WULF long hz=long_term — pub=2025-10-19T18:21:35
- entry=2025-10-20, $14.45
- 1m: **resolved_miss** raw=-16.96% bench=-1.67% excess=-15.28%
- 3m: excess=-13.43%  6m: excess=+35.43%
- **条件 label**: ['PRICE_TARGET']
- **if 句**: ['5T marketcap, AMD has a lot to catch up on even if it takes a small percent share', "BMNR - If I don't like Ethereum at these levels, no point of holding treasury companies"]
- **原文 (全文)**:
```
October 20th, Important Rate Cut Trading Week.

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
$ETH
$BMNR
$PL
$BLSKY
$RGTI
$OKLO
$IONQ
$QBTS

_

So macro wise, we are 9 days away from (~97% or so rate cut). Market is in fear mode. This is the ideal time to go long and not cut positions.

Fire Sale
_

$NBIS - Needs no explanation, I still maintain $400 PT on a bull case 2026 due to 4-6B+ forward revenue off ~60-75% gross margins, and another likely hyperscaler contract (eg. $META)

What happened on the 10%+ drop on Friday was mechanical hedging and MM Pinning. You can see this with the price stuck at $113.5, despite any volatility. 

I'd expect short hedges to unwind Monday (given MMs bought puts and were short calls -> heavy short into expiration) and price to go back up. I ended up buying 6 figures worth of calls on the drop as there was no material changes.

Strong Buy

TSM - Holy crap, please have this in your portfolio. This is a money printer, and scaling your revenue by 38-40% every year WHILE increasing gross margins is just insane. It dipped as well after smashing earnings so it's one of the easiest longs in my life.

AMKR - I don't have this in my portfolio yet but will be looking to add due to TSM's involvement in Arizona and potential to be a big partner in the US supply chain (as America tries to push TSM toward US fab + manufacturing).

WLAC - Neocloud SPAC IPO, large upside. I talk about this a lot recently, but it's probably one of the best valued Neoclouds out there, and already has great profit margins (not a pivot from miners, where it's a bit more uncertain). They work with Fluidstack, and I'd expect a 500%+ re-rating on top of a Mag7 contract.

AMZN - $213 is insane lol. I have no clue how this is down -3% YTD during a bull market.

LTC - Affected by crypto liquidations and government shutdown delaying ETFs. Great time to buy and just wait for ETF to be approved.

RDDT - Great dip to $190. I thought $200 would be a bottom but ended up going lower. The news about ChatGPT citing it less caused a large sell-off which I think was very immaterial.

HIMS - 14%+ drop off CEO share sale. Owners sell shares all the time, it doesn't really affect the fundamentals of the company much, just short term sentiment. I'd expect it to rebound.

IBIT - Bitcoin $108k great entry point, it's been swinging between $110k - $120k for awhile so anything under is usually great.

ALAB - I said this last time but it sold off way too much from news of a new competitor. It's already competing vs AVGO in the market lol, NVDA-like margins, growing hundreds of percent Y/Y, Mag7 using them in data center buildout. 

CRDO - Similar thesis to ALAB, sold off alongside Astera but a bit less.

SMCI - Should get re-rated for 55%+ or so revenue growth into next year. I doubted the projections earlier but with the data center growth, it's looking realistic.

FLY - This was a medium lift payload play. People doubt fly's execution but NOC co-developing medium lift takes a lot of risk off the table (and possible re-rating it 500%+ when it competes vs falcon9)

SNAP - Did the math on Snap monetization of memories in an earlier DD post and it's completely not priced in yet. It's doing $1.3B+ quarterly revenue on a $13B market cap lol, and the amount FCF they would get from increasing their revenue + lowering Google OPEX costs is insane.

ETOR  - Majority cash, growing at IBKR rates, suffering from tax harvesting

LULU - Suffering from tax harvesting + competition from Alo, Vuori, etc. But seasonally should be good, and extremely low p/e now.

Buy
AMD - ChatGPT putting in AMD orders, ORCL building out AMD data centers. Likely going to get a re-rating in the next year as a potential $NVDA competitor. Still think Nvidia will dominate but with it's 4.5T marketcap, AMD has a lot to catch up on even if it takes a small percent share.

HOOD - Looking at a lot better after the 10%+ correction. Could pull a PLTR

RBRK - Did DD on this earlier, looks better on the drop as a cybersecurity company really low multiples in the space. Just needs to cut back on marketing, customers sticky. 

UNH - Healthcare is sht in America but not going anywhere. Think Warren and the others know this 

TGT 🐈 - Dividend next moth, big dividend stock. Around now is a good time to load up IMO

IREN 🐈 - Huge GW, expect mag7 or similar deal. 

WYFI - Any neocloud is a buy (eg. see thesis on mag7 funneling revenue down toward these small 1B-5B companies)

WULF - neocloud play

CIFR - neocloud play

SLNH - neocloud play

BITF - neocloud play

GLXY - neocloud derivative play

FLNC - neocloud energy play

MU - China derisked, memory had a huge market there, memory also likely going to get re-rating in tdata center buildout

_

Sell

ETH - Not a fan of Ethereum at $4k+
BMNR - If I don't like Ethereum at these levels, no point of holding treasury companies 
PL - Low revenue, space stock (extremely high valuation)
BLSKY -Low revenue, space stock (extremely high valuation)
RGTI - Quantum bubble
OKLO - Nuclear bubble
IONQ -Quantum bubble 
QBTS - Quantum bubble

_

Quick macro heads up:
-> Rate cut in 9 days ~97% odds. Frontrunning expected, go long.  That's all.
```

### [亏损 #44] NBIS long hz=long_term — pub=2025-11-19T20:33:56
- entry=2025-11-20, $99.43
- 1m: **resolved_miss** raw=-9.45% bench=+5.43% excess=-14.88%
- 3m: excess=+0.50%  6m: excess=+94.56%
- **条件 label**: ['PRICE_TARGET']
- **if 句**: ['Stock should be easily trading $140+ right now if markets take 2026 projections seriously']
- **原文 (全文)**:
```
For starters it's incredibly undervalued at $94. Q1 would need to have many DCs burn down for it to justify current prices.

However, for it to be in line with my $400 PT, $NBIS needs to be executing current guidance eg.moving toward 2.5 GW capacity, 1GW capacity connected, revenue projections.

We're expecting $2.1B/quarter 2026 Q4 for $NBIS which is absolutely mindblowing growth.

Market prices in forward growth, but it's more of how long in the future it prices in. 

For Nebius, it's like it's wearing blindfolds. Stock should be easily trading $140+ right now if markets take 2026 projections seriously.
```

### [亏损 #45] IBIT long hz=6m — pub=2025-10-19T18:21:35
- entry=2025-10-20, $62.88
- 1m: **resolved_miss** raw=-16.25% bench=-1.67% excess=-14.58%
- 3m: excess=-22.05%  6m: excess=-35.48%
- **条件 label**: ['PRICE_TARGET']
- **if 句**: ['5T marketcap, AMD has a lot to catch up on even if it takes a small percent share', "BMNR - If I don't like Ethereum at these levels, no point of holding treasury companies"]
- **原文 (全文)**:
```
October 20th, Important Rate Cut Trading Week.

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
$ETH
$BMNR
$PL
$BLSKY
$RGTI
$OKLO
$IONQ
$QBTS

_

So macro wise, we are 9 days away from (~97% or so rate cut). Market is in fear mode. This is the ideal time to go long and not cut positions.

Fire Sale
_

$NBIS - Needs no explanation, I still maintain $400 PT on a bull case 2026 due to 4-6B+ forward revenue off ~60-75% gross margins, and another likely hyperscaler contract (eg. $META)

What happened on the 10%+ drop on Friday was mechanical hedging and MM Pinning. You can see this with the price stuck at $113.5, despite any volatility. 

I'd expect short hedges to unwind Monday (given MMs bought puts and were short calls -> heavy short into expiration) and price to go back up. I ended up buying 6 figures worth of calls on the drop as there was no material changes.

Strong Buy

TSM - Holy crap, please have this in your portfolio. This is a money printer, and scaling your revenue by 38-40% every year WHILE increasing gross margins is just insane. It dipped as well after smashing earnings so it's one of the easiest longs in my life.

AMKR - I don't have this in my portfolio yet but will be looking to add due to TSM's involvement in Arizona and potential to be a big partner in the US supply chain (as America tries to push TSM toward US fab + manufacturing).

WLAC - Neocloud SPAC IPO, large upside. I talk about this a lot recently, but it's probably one of the best valued Neoclouds out there, and already has great profit margins (not a pivot from miners, where it's a bit more uncertain). They work with Fluidstack, and I'd expect a 500%+ re-rating on top of a Mag7 contract.

AMZN - $213 is insane lol. I have no clue how this is down -3% YTD during a bull market.

LTC - Affected by crypto liquidations and government shutdown delaying ETFs. Great time to buy and just wait for ETF to be approved.

RDDT - Great dip to $190. I thought $200 would be a bottom but ended up going lower. The news about ChatGPT citing it less caused a large sell-off which I think was very immaterial.

HIMS - 14%+ drop off CEO share sale. Owners sell shares all the time, it doesn't really affect the fundamentals of the company much, just short term sentiment. I'd expect it to rebound.

IBIT - Bitcoin $108k great entry point, it's been swinging between $110k - $120k for awhile so anything under is usually great.

ALAB - I said this last time but it sold off way too much from news of a new competitor. It's already competing vs AVGO in the market lol, NVDA-like margins, growing hundreds of percent Y/Y, Mag7 using them in data center buildout. 

CRDO - Similar thesis to ALAB, sold off alongside Astera but a bit less.

SMCI - Should get re-rated for 55%+ or so revenue growth into next year. I doubted the projections earlier but with the data center growth, it's looking realistic.

FLY - This was a medium lift payload play. People doubt fly's execution but NOC co-developing medium lift takes a lot of risk off the table (and possible re-rating it 500%+ when it competes vs falcon9)

SNAP - Did the math on Snap monetization of memories in an earlier DD post and it's completely not priced in yet. It's doing $1.3B+ quarterly revenue on a $13B market cap lol, and the amount FCF they would get from increasing their revenue + lowering Google OPEX costs is insane.

ETOR  - Majority cash, growing at IBKR rates, suffering from tax harvesting

LULU - Suffering from tax harvesting + competition from Alo, Vuori, etc. But seasonally should be good, and extremely low p/e now.

Buy
AMD - ChatGPT putting in AMD orders, ORCL building out AMD data centers. Likely going to get a re-rating in the next year as a potential $NVDA competitor. Still think Nvidia will dominate but with it's 4.5T marketcap, AMD has a lot to catch up on even if it takes a small percent share.

HOOD - Looking at a lot better after the 10%+ correction. Could pull a PLTR

RBRK - Did DD on this earlier, looks better on the drop as a cybersecurity company really low multiples in the space. Just needs to cut back on marketing, customers sticky. 

UNH - Healthcare is sht in America but not going anywhere. Think Warren and the others know this 

TGT 🐈 - Dividend next moth, big dividend stock. Around now is a good time to load up IMO

IREN 🐈 - Huge GW, expect mag7 or similar deal. 

WYFI - Any neocloud is a buy (eg. see thesis on mag7 funneling revenue down toward these small 1B-5B companies)

WULF - neocloud play

CIFR - neocloud play

SLNH - neocloud play

BITF - neocloud play

GLXY - neocloud derivative play

FLNC - neocloud energy play

MU - China derisked, memory had a huge market there, memory also likely going to get re-rating in tdata center buildout

_

Sell

ETH - Not a fan of Ethereum at $4k+
BMNR - If I don't like Ethereum at these levels, no point of holding treasury companies 
PL - Low revenue, space stock (extremely high valuation)
BLSKY -Low revenue, space stock (extremely high valuation)
RGTI - Quantum bubble
OKLO - Nuclear bubble
IONQ -Quantum bubble 
QBTS - Quantum bubble

_

Quick macro heads up:
-> Rate cut in 9 days ~97% odds. Frontrunning expected, go long.  That's all.
```

### [亏损 #46] IBIT long hz=5y — pub=2025-10-02T21:01:45
- entry=2025-10-03, $68.61
- 1m: **resolved_miss** raw=-11.77% bench=+2.11% excess=-13.88%
- 3m: excess=-26.92%  6m: excess=-42.10%
- **条件 label**: ['PRICE_TARGET']
- **原文 (全文)**:
```
@WaggaDoo $225 PT 1 year. I don't have enough info to give predictions outside that timeframe.

For stuff like $RKLB or $IBIT im happy giving 5 year predictions though
```

### [亏损 #47] ALAB long hz=6m — pub=2025-10-15T07:42:21
- entry=2025-10-16, $163.96
- 1m: **resolved_miss** raw=-11.97% bench=+1.71% excess=-13.68%
- 3m: excess=+9.51%  6m: excess=+10.51%
- **条件 label**: ['PRICE_TARGET']
- **if 句**: ['This would be a $3T company if this were a US company, insane profit margins, insane growth rate for their size', '5T), even if buying at ATHs', "AMZN hitting $213-215 today was a good chance to stock up since it usually floats between $218-$227 if you're short term swing trading but long term I'd expect it to catchup to other mag7"]
- **原文 (全文)**:
```
The Great Soybean/Seed Oil Crash, personal thoughts and explanations:

Strong Buy
$ALAB
$CRDO
$NBIS
$WLAC
$LTC
$TSM
$BTC
(+ same as tax harvest stocks last time)
$AMZN
$SMCI
_

Buy
$AMD
$FLNC
$SEI
$BZAI
$NKLR
$IREN
$WULF
$CIFR
$CRWV
$BITF
$WYFI
$SLNH
$BITF
$RBRK
$GLXY
$GRAB
$SEA
$META
$TGT
$SNAP
$MU
$RKLB
$FLY
$UNH

Hold
$MP
$HOOD
$EOSE
$NVDA
$GOOGL
$DFLI
$SOFI
$VIRT
$RR
$AVGO
$BE
$ASTS

(Hit the ticker maximum but everything else from last post, still sell on Quantum or Oklo)
_

Strong Buys
ALAB - Huge part of datacenter buildout, NVDA like margins, Mag7 customers. Already had competitors from AVGO,  really don't think Arista would be a competitive threat.

CRDO - Same sell-off as ALAB, thought they were both kind of overvalued before, but now they're back in correction territory so good to stock up.

NBIS - $400 PT bull case. We have macro tailwind from government re-opening + rate cut EOM october into earnings, so short term looks promising. Lot of things going for it (eg. meta x crwv, so there's potential for more mag7 clients), sum of parts doing well, eg. clickhouse, and scaling rev from $100m to $1.5B+ a quarter is insane. there's already contracts locked in its just a matter of company execution.

WLAC - Wrote a thesis about this earlier at $13. Even at $14.5 strong because it can re-rate 100%+ easily.

LTC - Affected by leverage traders and government shutdown. The shutdown is predicted to last awhile and the main reason to buy was the ETF getting approved. But a great buy sub <$100 anyway, because it will get approved in due time (~95% chance).

TSM - Holy crap. This would be a $3T company if this were a US company, insane profit margins, insane growth rate for their size. And every post you see about OpenAi X (**sydney sweeney partnership) or AMD buildout/NVDA buildout. TSM is the center of it all and would easily be a $2T+ company (from here at ~$1.5T), even if buying at ATHs.

BTC - $112K good entry point. Goldt keeps hitting ATH, nothing really changed fundamentally, just lot of liquidations recently
(+ same as tax harvest stocks last time)

AMZN - I really don't know how it's still down YTD. I don't think Amazon needs much explaining but still growing  (eg. AWS backlog massive, still going like 24% but not as much as ORCL, GCP and others obviously), but with EOY seasonality and runup to Feb, now is probably the best chance to catch the bottom. AMZN hitting $213-215 today was a good chance to stock up since it usually floats between $218-$227 if you're short term swing trading but long term I'd expect it to catchup to other mag7.

SMCI - Underrated. Markets were looking short term performance, and Charles was quoting like 55%+ Y/Y forward revenue growth which nobody believed + backlog that didnt get realized yet. But now with all the data center buildouts, now it's kinda making sense. So should re-rate in the next two earnings.

_
Buy

AMD - So many deals from OpenAI x AMD, oracle building out with AMD, this is going to re-rate to a potential $1T+ company if it's actually a strong competitive to $NVDA.  I don't think it's winner takes all and you can see a $4.5T+ market cap size with NVDA and some $350B marketcap size with AMD, so we can see a large ramp up (OpenAI is usually the leader in frontier models and if Sam says they can use AMD chips + elon said its' good for small-medium weight models, prboably means something positive)

FLNC - Strong re-rate on energy after AI consumption, great buy.

SEI - Strong re-rate on energy after AI consumption, great buy.

BZAI - Someone else did a DD on this company, just cause of sector and shift to edge compute (eg. Robotics goign to be hot). Because of low MC and runup of similar companies could turn out well.

NKLR - Nuclear stocks like $OKLO have been taking off, this is just follow the lader.

IREN - Needs no introduction, huge GW compute capacity just no announced mag7 deals yet but could come anytime -> strong re-rate. Only reason not a strong buy is because not fully convinced miners can pivot like CRWV and maintain great margins (eg. $ORCL hit piece) but we'll see.

WULF - GOOGL backlog, another $3.6+ or so in funding helps a lot.

CIFR - Lot of info on X about future capacity and strong re-rating. Always liked this company because it was NBIS-lite. You can probably buy any Neocloud and it will go up because the sector is incredibly high potential with Mag7 funneling revenue.

CRWV - Didn't like this as much as others because of debt but because of the seed oil correction much better buy point at $134 (below when META deal was announced)

BITF - Same in Neocloud category

WYFI - Same in Neocloud category

BITF - Same in Neocloud category

GLXY - Same in Neocloud category, helps with their buildout

RBRK - Did a DD on this, great buy for cybersecurity sector in mid term, they just need to scale back marketing and then it looks like they have a lot more FCF because they're spending most OPEX on marketing.

GRAB - Great fundamentally, -6.56% correction good to buy again

SEA - AMZN in SEA, tons of people use them. Just a buy just because of costumer base + monetization potenetial. Fundamentally growing $5B+ rev 38% Y/Y is also great.

META - I really don't like all their expensive capex on AI since they're not really putting out fronteir models like ChatGPT with it, who knows what Zuck is doing. But that aside, down 7.3% over the month, going to $700 support, probably a good buy around here to play catchup.

TGT - Dividend next month good catalyst.

SNAP - The Jenners are coming back (helps with popularity), they're shifting former memory opex to revenue, and this will probably cause a HUGE rerating next year. Just suffers from tax harvesting otherwise would be a strong buy rn. Usually tax harvesting events are kinda done in December.

MU - Now that China fears are kinda less intense, MU is a lot stronger buy just cause of memory use on buildout.

RKLB - Neutron, golden dome contracts, lot of cataylsts

FLY - Medium lift

UNH - Healthcare stock not affected by soybeans but had a correction. Would likely go up one instituions post their ports (eg. warren likely bought more)

Random thoughts
Basically any growth/risk stock that's not named Oklo is great because we have

-> Rate Cut end of month October
-> Government re-opening sometime (likely around end of Oct or early Nov)

Into
-> Rate Cut December.
-> Midterms (Bullish for stocks)

Usually market crashes happen when there's tightening not easing. And your stupid quantum bubbles would likely continue for another 3-12 months afterward. If you're short, then probably wait till next Feb.

Anyway, this is a great time for risk-on, and specially riding trends with neoclouds -> affiliated sectors (eg. energy) -> affiliated companies (eg. smci, tsm, etc).

I half joke-about soybeans because it likely signed escalating tensions, but I'd probably see a run-up into next year. Also I could write up a lot about each one but it's pretty time consuming but I'll put on a thesis post about random ones eg. $RBRK, from time to time.

Space/robotics/energy/quantum/ai/semi/critical top verticals right now, don't fight against momentum. I can think something is overvalued (eg. some critical materials bc. it's still spectulative compared to neoclouds that kinda have guaranteed rev based on execution from mag7) but I wouldn't short it into rate cuts.

Just personal thoughts, NFA
```

### [亏损 #48] NTTYY long hz=long_term — pub=2026-04-05T04:56:46
- entry=2026-04-06, $25.18
- 1m: **resolved_miss** raw=-3.77% bench=+9.84% excess=-13.61%
- 3m: excess=+0.00%  6m: excess=+0.00%
- **条件 label**: ['EVENT_VERB']
- **if 句**: ['Then if it fails fallback would be names like:', 'Analysis states that if the optical mesh fails due to clouds or lack of stations, the architecture "falls back to Ka-band RF links"', 'But not quite sure if capex is to the scale of hyperscaler AI buildouts yet to benefit these companies enough']
- **原文 (全文)**:
```
The Space Bottleneck: Optical ground infrastructure.

- "The industry has built roughly 10 percent of the optical ground infrastructure"

Now, who are the beneficiaries?

- $EOS.ASX (operating stations at Mt. Stromlo equipped with "adaptive optics.") 
- $SKPJF (TYO: 9412) |  $NTTYY | Space Compass is JV with NTT and satellite operator SKY Perfect JSAT
- $SGBAF - Works with Cailabs to for terrestrial optical terminals
- $SAFRY - Manufacturer of the optical ground stations

Then if it fails fallback would be names like:
$VSAT, $GILT

Analysis states that if the optical mesh fails due to clouds or lack of stations, the architecture "falls back to Ka-band RF links". 
 
-> Near term capital flows to Relay Providers (Kepler, Space Compass, General Atomics). 

-> Long term structural winners will be the photonics hardware manufacturers (Cailabs, Safran).

-> Then companies like SpaceX wins by default. Many are private. 

"This infrastructure deficit is no longer just an engineering problem but a direct threat to a major White House [Golden Dome] policy objective"

Orbital laser communications market are hard-capped until physical ground infra scales, hence the current bottleneck. 

But not quite sure if capex is to the scale of hyperscaler AI buildouts yet to benefit these companies enough.
```

### [亏损 #49] AEHR long hz=long_term — pub=2026-02-26T17:55:14
- entry=2026-02-27, $38.25
- 1m: **resolved_miss** raw=-21.27% bench=-7.87% excess=-13.39%
- 3m: excess=+131.11%  6m: excess=+0.00%
- **条件 label**: ['EVENT_VERB']
- **if 句**: ["With new gen $NVDA or $AMD type chips that gets hot,  if one chip melts down, it's a disaster", 'So tech giants -> every single chip stress tested with heat to see if it fails prematurely in the field', 'so they buy more if they like $AEHR, and this ramps up revenue']
- **原文 (全文)**:
```
A simpler overview of $AEHR - $1.1B (without the jargon). One of my long positions:

With AI, thermal is a known bottleneck.

With new gen $NVDA or $AMD type chips that gets hot,  if one chip melts down, it's a disaster. 

So tech giants -> every single chip stress tested with heat to see if it fails prematurely in the field. 

$AEHR sells the machines that does the testing of these chips. 

Last year, they were like $POET (pre-qualification/test phase) 

-> but now they've passed.

We're seeing that inflection from R&D to mass production:

Today: 

-> $14M order for $AEHR burn-in systems to help scale chip production (wafer level)

But that $14M machine order can only handle a finite number of wafers per week. 

-> As this AI customer scales up, they will physically run out of thermal testing throughput.

so they buy more if they like $AEHR, and this ramps up revenue. 

They also have a separate product line (Sonoma) for testing chips after they're packaged.

Hyperscalers have been ordering this, so two different testing stages, two revenue streams.

Management guided for a massive second half 2026 $60M to $80M in new bookings (which is big growth). 

You can look at $TER ($51B) or Advantest (~$125B) to see the ceiling of how big a lot of these companies can get.

They also do testing across other data center layers too: 

- So they're working with NAND Flash memory suppliers 
- Silicon photonics

Tried to strip out as much technical jargon as possible so it's more understandable to majority, but it's a very nuanced/technical field. 

$AEHR has potential as it's now scaling up real-volume after years of R&D and qualification. 

And we're sitting in an enormous capex cycle (think $ASML cycles, where people order a lot of machines for the buildout).
```

### [亏损 #50] SNAP long hz=6m — pub=2025-10-04T01:22:20
- entry=2025-10-06, $8.55
- 1m: **resolved_miss** raw=-12.68% bench=+0.54% excess=-13.22%
- 3m: excess=-1.92%  6m: excess=-43.37%
- **条件 label**: ['PRICE_TARGET']
- **if 句**: ["BMNR - Just buy ETH if you believe in it but I wouldn't buy at ETH at $4500"]
- **原文 (全文)**:
```
Friday Market Close, Personal Thoughts and Explanations:

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

Reddit - Dropped 29% off immaterial news that ChatGPT wasn't citing it as much. Nobody visits Reddit through ChatGPT, good recovery buy off $200 support. 

SNAP - Finally they're doing something that's USEFUL for the first time in many years lol. Tons of Capex was spent on storing photos random drawings people saved 12 years ago taking GBs of space for their insane Google Cloud costs. They're finally monetizing it like Apple. Huge tailwind, should improve net income by a ton next year. 

AMZN - Under $220 now, great buy. AMZN prime Oct 8th, good for seasonality in Nov/Dec.

ETOR - I can't believe this is still $41. 33% cash, 1B+ cash pile growing at IBKR rates. Just suffers from tax harvesting I'd assume it goes up next year. 

NBIS - Strong buy until $150+ or new hyperscaler contract repricing. 

LTC - ETF catalyst delayed from Gov shutdown but should be approved anyway. 

Buys

Upwork - Down 4.5% or so for no reason, should recover

MSTR - BTC close to all time highs, MSTR way off ATHs cause of long btc short MSTR but NAV premium should catch up again from the BTC fomo.

ORCL - Standard rise on great forward earnings, drop for short term option chain, then rise because 14B tiktok deal and large future cloud contracts

TGT - Just undervalued great buy under $93, dividend catalyst next month

CIFR - NBIS light with GOOGL deal.

VIRT - VIX doesn't look like it's going down anytime soon but they're trading at like 6.4 or so forward P/E so it's worth.

CRDO - Good buy on correction with hypescaler buildout

WULF - Hasn't gone up as much as the other neoclouds, googl backlog

SOFI - Corrected, might recover back to ATH given macro tailwind

META - Monthly low good DCA, not as good as AMZN

AVGO - Same as ORCL, might end up like NVDA one day with hyperscaler chips

MRVL - Still down 24% YTD. 

SMCI - Good buy on datacenter buildout + server racks

Dell - Good buy on datacenter buildout + server racks

Hold

Nothing changed

Sell

TSLA - Overvalued, better longs like NBIS

CRCL - I will keep making this argument, but just buy COIN instead. You will get the same 50% revenue sharing but with a crypto exchange + ETF holding income too.  

PLTR - Disconnected from reality

BMNR - Just buy ETH if you believe in it but I wouldn't buy at ETH at $4500.

Strong Sell

RGTI - Disconnected from reality lol

All disconnected from reality, wouldn't short though cause all cult stocks. 
OKLO
QBTS
IONQ
```

## Top 50 盈利(按 1m excess 从正到负)

**铁律测试**: 这 50 条的 if 条件触发判定,跟我用同样规则判 top 50 亏损,应该一致

### [盈利 #1] RKLB long hz=5y — pub=2025-11-20T10:23:51
- entry=2025-11-21, $39.83
- 1m: **resolved_hit** raw=+93.77% bench=+4.76% excess=+89.02%
- 3m: excess=+77.81%  6m: excess=+257.15%
- **条件 label**: ['PRICE_TARGET']
- **if 句**: ["My thesis was that if Mag7 is dependent on a company ($NVDA for GPUs) ( NBIS, IREN, CIFR for DC AI cloud buildout), the company will blow away expections quarter after quarter, and we're seeing this", "A TLDR of my most recent thesis post was that they're cutting their massive opex bloat from memories/videos stored 10 years ago and if you look into their GCP hosting fees, it's cutting in margins", 'Happy to discuss more if you drop your own portfolio + concentrations']
- **原文 (全文)**:
```
Based on the equity ranking table:

Here's a deeper analysis of each stock, alongside how I reposition my portfolio to capitalize on the market reset:

· $NBIS at $92, PT $400 / 1Y
· $RKLB at $43, PT $500 / 5Y
· $CRCL at $72, PT $150 / 8M
· $ALAB at $143.4, PT $250 / 6M
· $SNAP at $8.1, PT $22 / 1Y
· $CIFR at $14.8, PT $28 / 6M
· $RDDT at $185, PT $275 / 8M
· $SMCI at $34, PT $55 / 6M
· $HIMS at $35, PT $60 / 6M

This is in order of concentration weighting from when posted and internal PT speculation based on existing information for mid-cap ($5B+) sections.

Here’s a deeper breakdown on each one and PT timeframe, and a “qualitative”why:

1. Nebius ( $NBIS ): $23B marketcap. Incredibly undervalued and detached from fundamentals.

$7-9B forward ARR, 20-30% EBIT, enterprise contracts from Shopify, Accenture, Cursor, foreign governments and hyperscaler contracts from Meta and Microsoft give Nebius revenue visibility. With $4.8B+ in cash, it's isolated from credit tightening affecting data centers. With 2.5 GW expected capacity contracted 2026, it rivals many others eg. $IREN at 2.8 GW, and defeats many of the capacity/power arguments. With many portfolio companies powering companies like Tesla and Anthropic, it also has higher growth potential (think $MSFT with its portfolio companies for longer defensibility).

We also had stellar $NVDA earnings going into Q4 with their blowout, Jensen clarifying arguments against GPU depreciation, which helps with DC sector sentiment. 

$400 1 year price target, $100B+ valuation given forward revenue/margins.

2. Rocketlab ( $RKLB ): $22B marketcap. Overvalued current term, undervalued long term potential. 

Rocketlab is my highest conviction 5Y long alongside Bitcoin. With Space, it's not winner takes all, and I've maintained $350-500B long term PT to match SpaceX’s most recent valuation/capabilities.

As of now, it's overvalued. But it's an incredible + defensible moat from purely a technological standpoint building reusable rockets and we're early in terms of commercialization of their end-to-end space products at scale (likely ~2028).

However, we're pricing in forward growth with Flatlite commericalization (eg. Starlink), and medium-lift payloads (SpaceX Falcon 9). The market prices in forward growth as well but it’s more about how long in the future with Rocketlab. It's always a solid buy, depending on how patient you are with company execution. 

3. Circle ( $CRCL ) - $16B marketcap, undervalued.

With Circle, I've been bear posting it since it was a $50B marketcap, saying short Circle, long Coinbase, given $COIN has 50% revenue sharing with Circle.

It was overvalued due to float numbers and massive insider lockups 2-3 days after earnings/Dec 2nd led to a sell-off (like $BULL). Float dynamics matter a lot that ETF managers like Cathie Wood seem to not understand (hence my warnings). 

But now we're reaching respectable valuation numbers. I expect USDC commercialization to continue and given a regulatory focus in the digital asset market, I see $CRCL taking over a lot of Tether's marketcap. 

That being said, it's well deserving of a $30B+ marketcap pricing in stablecoin volume growth once we start seeing insider shares redistributed to institutions and long term holders. 

4. Astera Labs ( $ALAB ) - $22B marketcap, reasonable valuation

ALAB was one of my mid-term high conviction picks, due to Mag7 adoption of connectivity for datacenter buildout. 

Incredibly high growth and $NVDA-like margins sitting at ~74%, latest er: $230m/q (101% Y/Y growth). My thesis was that if Mag7 is dependent on a company ($NVDA for GPUs) ( NBIS, IREN, CIFR for DC AI cloud buildout), the company will blow away expections quarter after quarter, and we're seeing this.

There's been a recent sell-off on Astera from $250 back to $140 marks, depsite beating earning expectations across the board and this presents a good buying opportunity.

I maintain a medium term PT $250 for recovery after NVDA earnings and record-high DC buildout from Antrophic's $40B DC to $GOOGL's $50B DC in Texas + connectivity demand.

5. Snapchat ( $SNAP ) $13B marketcap, undervalued. 

$SNAP is one of my least favorite stocks and CEO's (sorry Evan). 

However, I can't argue with fundamental changes. A TLDR of my most recent thesis post was that they're cutting their massive opex bloat from memories/videos stored 10 years ago and if you look into their GCP hosting fees, it's cutting in margins.

Now they're both reducing that OPex cost and increasing revenue from that.  We also have AI deals with perplexity adding $400m+ additional revenue streams like RDDT. 

However, short term it's suffering from tax-harvesting due to underperformance this year relative to AI companies. In 2026 Q1, I expect the market to start pricing in the new fundamentals Hard. and for this company to beat expectation soundly. 

That being said I expect over a 200%+ upside 1Y from here with the market pricing in the new dynamics. 

5. CIFR ( $CIFR ) - Undervalued at $5B marketcap

$CIFR is my second favorite stock in the Neocloud sector. From memory, it holds a lot of Bitcoin on its balance sheet and is materially affected by the selloff in BTC prices from $120k to $90k. 

However I expect crypto asset prices to recover in a few months once cascading margin liqudations finish and instituions buy-in Bitcoin at low prices. 

Nebius is top because it owns the full AI-cloud value chain for higher revenue potential and stronger returns, even though it forces them to handle orchestration, software, and GPU lifecycle risk instead of sticking to colocation.  

However,  $CIFR because it avoids that entire risk surface and has backing from AMZN and GOOGL for long term revenue anchors. It also stays insulated from GPU procurement, management, and depreciation.  

For CIFR's economics we get a a high-margin, annuity structure built on space, power, and cooling for hyperscalers. Risk-adjusted, it’s one of the safest names in the group. But the trade-off is capped upside  Long leases like 10Y, 15Y slow the revenue ramp and mute the payoff relative to full-stack Neocloud operators like NBIS that go from $145m quarterly revenue to $2.1B in a year.

That being said I maintain a $28 PT in 1 month once market prices in $AMZN, $GOOGL Fluidstack revenue and Bitcoin prices recover. 

6. Reddit ( $RDDT ) - Moderate valuation

Coming from the Wendy's dumpsters on WSB subreddit, I am naturally biased toward this platform.

However, the initial sell-off of Reddit at $270 was due to fears over ChatGPT citations, which was immaterial. Now, recent data shows that citations are back, but Reddit's price still sits at $185 (way below that number) + partly due to macro.

Reddit is one of the least bloated, highly profitable social media companies. And it's here to stay due to long term defensibility of the network effect of both younger + older audiences (compared to Snap 900m+ MAU of mostly younger generation).

I expect RDDT to scale up monetization avenues through acquisitions like $HOOD (exchanges) due to their massive FCF and profitability or how Facebook originally acquired WhatsApp, Instagram, built out messenger. It's a low-risk, high growth stock, which is why I maintain a $275 PT in 8 months. 

7. SMCI ( $SMCI ) - Undervalued, $20B marketcap.

$20B marketcap is a joke. Nothing else to say. They're doing $5B quarterly revenue (off lower-margins for sure). However, market is pricing in the company revenue dropping. 

SMCI quoted majority of the backlog delay to Q2 2026, which aligns with a lot of the DC buildout from Neoclouds to Mag7 customers. 

They expect revenue to grow 50%+ Y/Y next year, with at least $36 billion revenue, but judging from DC buildout from blowout NVDA earnings, I expect server rack companies like $DELL and SMCI to outperform Q2  2026. 

This is why I'm taking advantage of revenue lag delays from the current quarter and assigning a $55 PT in 6 months time. 

8. Hims and Her Health ( $HIMS) - Undervalued ( $8B marketcap)

Personally, I've used HIMS just for short term trading breakouts. And I've been one to not long-term hold the stock above $50.  

However, back at $35, it's reset most of the year's growth but grew revenue 49% Y/Y to $500m and is producing a good amount of FCF.

The most under-priced narrative is the Zava acquisition. This adds 1.3M+ users to the HIMS platform and allows the company to expand to the EU market.

Similar to how META acquires companies like Instagram, grows its base + monetizes, I expect HIMS to do the same with Zava + market is pricing in current est. Zava numbers. 

It's probably my least confident stock out of the bunch, especially leaving me with a bad taste with the CEO selling shares after leaving 👀 on SS posts back at $70. 

But that being said it's a great rebound opportunity to $60 in a 6 month timeframe. 

Hope you enjoyed my perspective. There's a lot of x at price posts, but I try to leave a more qualitative breakdown (+ part quantitative but leave out a lot of technical for easier reading) to help retail develop their own conviction and understanding.

Building understanding is important to create internal valuation models yourself rather than blindly following along FinX posters + capitulating when stock prices temporarily drop. 

Happy to discuss more if you drop your own portfolio + concentrations.
```

### [盈利 #2] RGTI short hz=6m — pub=2025-10-19T18:21:35
- entry=2025-10-20, $47.48
- 1m: **resolved_hit** raw=+45.85% bench=-1.67% excess=+47.52%
- 3m: excess=+44.80%  6m: excess=+58.96%
- **条件 label**: ['PRICE_TARGET']
- **if 句**: ['5T marketcap, AMD has a lot to catch up on even if it takes a small percent share', "BMNR - If I don't like Ethereum at these levels, no point of holding treasury companies"]
- **原文 (全文)**:
```
October 20th, Important Rate Cut Trading Week.

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
$ETH
$BMNR
$PL
$BLSKY
$RGTI
$OKLO
$IONQ
$QBTS

_

So macro wise, we are 9 days away from (~97% or so rate cut). Market is in fear mode. This is the ideal time to go long and not cut positions.

Fire Sale
_

$NBIS - Needs no explanation, I still maintain $400 PT on a bull case 2026 due to 4-6B+ forward revenue off ~60-75% gross margins, and another likely hyperscaler contract (eg. $META)

What happened on the 10%+ drop on Friday was mechanical hedging and MM Pinning. You can see this with the price stuck at $113.5, despite any volatility. 

I'd expect short hedges to unwind Monday (given MMs bought puts and were short calls -> heavy short into expiration) and price to go back up. I ended up buying 6 figures worth of calls on the drop as there was no material changes.

Strong Buy

TSM - Holy crap, please have this in your portfolio. This is a money printer, and scaling your revenue by 38-40% every year WHILE increasing gross margins is just insane. It dipped as well after smashing earnings so it's one of the easiest longs in my life.

AMKR - I don't have this in my portfolio yet but will be looking to add due to TSM's involvement in Arizona and potential to be a big partner in the US supply chain (as America tries to push TSM toward US fab + manufacturing).

WLAC - Neocloud SPAC IPO, large upside. I talk about this a lot recently, but it's probably one of the best valued Neoclouds out there, and already has great profit margins (not a pivot from miners, where it's a bit more uncertain). They work with Fluidstack, and I'd expect a 500%+ re-rating on top of a Mag7 contract.

AMZN - $213 is insane lol. I have no clue how this is down -3% YTD during a bull market.

LTC - Affected by crypto liquidations and government shutdown delaying ETFs. Great time to buy and just wait for ETF to be approved.

RDDT - Great dip to $190. I thought $200 would be a bottom but ended up going lower. The news about ChatGPT citing it less caused a large sell-off which I think was very immaterial.

HIMS - 14%+ drop off CEO share sale. Owners sell shares all the time, it doesn't really affect the fundamentals of the company much, just short term sentiment. I'd expect it to rebound.

IBIT - Bitcoin $108k great entry point, it's been swinging between $110k - $120k for awhile so anything under is usually great.

ALAB - I said this last time but it sold off way too much from news of a new competitor. It's already competing vs AVGO in the market lol, NVDA-like margins, growing hundreds of percent Y/Y, Mag7 using them in data center buildout. 

CRDO - Similar thesis to ALAB, sold off alongside Astera but a bit less.

SMCI - Should get re-rated for 55%+ or so revenue growth into next year. I doubted the projections earlier but with the data center growth, it's looking realistic.

FLY - This was a medium lift payload play. People doubt fly's execution but NOC co-developing medium lift takes a lot of risk off the table (and possible re-rating it 500%+ when it competes vs falcon9)

SNAP - Did the math on Snap monetization of memories in an earlier DD post and it's completely not priced in yet. It's doing $1.3B+ quarterly revenue on a $13B market cap lol, and the amount FCF they would get from increasing their revenue + lowering Google OPEX costs is insane.

ETOR  - Majority cash, growing at IBKR rates, suffering from tax harvesting

LULU - Suffering from tax harvesting + competition from Alo, Vuori, etc. But seasonally should be good, and extremely low p/e now.

Buy
AMD - ChatGPT putting in AMD orders, ORCL building out AMD data centers. Likely going to get a re-rating in the next year as a potential $NVDA competitor. Still think Nvidia will dominate but with it's 4.5T marketcap, AMD has a lot to catch up on even if it takes a small percent share.

HOOD - Looking at a lot better after the 10%+ correction. Could pull a PLTR

RBRK - Did DD on this earlier, looks better on the drop as a cybersecurity company really low multiples in the space. Just needs to cut back on marketing, customers sticky. 

UNH - Healthcare is sht in America but not going anywhere. Think Warren and the others know this 

TGT 🐈 - Dividend next moth, big dividend stock. Around now is a good time to load up IMO

IREN 🐈 - Huge GW, expect mag7 or similar deal. 

WYFI - Any neocloud is a buy (eg. see thesis on mag7 funneling revenue down toward these small 1B-5B companies)

WULF - neocloud play

CIFR - neocloud play

SLNH - neocloud play

BITF - neocloud play

GLXY - neocloud derivative play

FLNC - neocloud energy play

MU - China derisked, memory had a huge market there, memory also likely going to get re-rating in tdata center buildout

_

Sell

ETH - Not a fan of Ethereum at $4k+
BMNR - If I don't like Ethereum at these levels, no point of holding treasury companies 
PL - Low revenue, space stock (extremely high valuation)
BLSKY -Low revenue, space stock (extremely high valuation)
RGTI - Quantum bubble
OKLO - Nuclear bubble
IONQ -Quantum bubble 
QBTS - Quantum bubble

_

Quick macro heads up:
-> Rate cut in 9 days ~97% odds. Frontrunning expected, go long.  That's all.
```

### [盈利 #3] CIFR long hz=6m — pub=2025-10-04T01:22:20
- entry=2025-10-06, $15.54
- 1m: **resolved_hit** raw=+44.85% bench=+0.54% excess=+44.31%
- 3m: excess=+0.80%  6m: excess=+4.04%
- **条件 label**: ['PRICE_TARGET']
- **if 句**: ["BMNR - Just buy ETH if you believe in it but I wouldn't buy at ETH at $4500"]
- **原文 (全文)**:
```
Friday Market Close, Personal Thoughts and Explanations:

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

Reddit - Dropped 29% off immaterial news that ChatGPT wasn't citing it as much. Nobody visits Reddit through ChatGPT, good recovery buy off $200 support. 

SNAP - Finally they're doing something that's USEFUL for the first time in many years lol. Tons of Capex was spent on storing photos random drawings people saved 12 years ago taking GBs of space for their insane Google Cloud costs. They're finally monetizing it like Apple. Huge tailwind, should improve net income by a ton next year. 

AMZN - Under $220 now, great buy. AMZN prime Oct 8th, good for seasonality in Nov/Dec.

ETOR - I can't believe this is still $41. 33% cash, 1B+ cash pile growing at IBKR rates. Just suffers from tax harvesting I'd assume it goes up next year. 

NBIS - Strong buy until $150+ or new hyperscaler contract repricing. 

LTC - ETF catalyst delayed from Gov shutdown but should be approved anyway. 

Buys

Upwork - Down 4.5% or so for no reason, should recover

MSTR - BTC close to all time highs, MSTR way off ATHs cause of long btc short MSTR but NAV premium should catch up again from the BTC fomo.

ORCL - Standard rise on great forward earnings, drop for short term option chain, then rise because 14B tiktok deal and large future cloud contracts

TGT - Just undervalued great buy under $93, dividend catalyst next month

CIFR - NBIS light with GOOGL deal.

VIRT - VIX doesn't look like it's going down anytime soon but they're trading at like 6.4 or so forward P/E so it's worth.

CRDO - Good buy on correction with hypescaler buildout

WULF - Hasn't gone up as much as the other neoclouds, googl backlog

SOFI - Corrected, might recover back to ATH given macro tailwind

META - Monthly low good DCA, not as good as AMZN

AVGO - Same as ORCL, might end up like NVDA one day with hyperscaler chips

MRVL - Still down 24% YTD. 

SMCI - Good buy on datacenter buildout + server racks

Dell - Good buy on datacenter buildout + server racks

Hold

Nothing changed

Sell

TSLA - Overvalued, better longs like NBIS

CRCL - I will keep making this argument, but just buy COIN instead. You will get the same 50% revenue sharing but with a crypto exchange + ETF holding income too.  

PLTR - Disconnected from reality

BMNR - Just buy ETH if you believe in it but I wouldn't buy at ETH at $4500.

Strong Sell

RGTI - Disconnected from reality lol

All disconnected from reality, wouldn't short though cause all cult stocks. 
OKLO
QBTS
IONQ
```

### [盈利 #4] OKLO short hz=6m — pub=2025-10-19T18:21:35
- entry=2025-10-20, $167.19
- 1m: **resolved_hit** raw=+42.20% bench=-1.67% excess=+43.87%
- 3m: excess=+42.98%  6m: excess=+48.73%
- **条件 label**: ['PRICE_TARGET']
- **if 句**: ['5T marketcap, AMD has a lot to catch up on even if it takes a small percent share', "BMNR - If I don't like Ethereum at these levels, no point of holding treasury companies"]
- **原文 (全文)**:
```
October 20th, Important Rate Cut Trading Week.

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
$ETH
$BMNR
$PL
$BLSKY
$RGTI
$OKLO
$IONQ
$QBTS

_

So macro wise, we are 9 days away from (~97% or so rate cut). Market is in fear mode. This is the ideal time to go long and not cut positions.

Fire Sale
_

$NBIS - Needs no explanation, I still maintain $400 PT on a bull case 2026 due to 4-6B+ forward revenue off ~60-75% gross margins, and another likely hyperscaler contract (eg. $META)

What happened on the 10%+ drop on Friday was mechanical hedging and MM Pinning. You can see this with the price stuck at $113.5, despite any volatility. 

I'd expect short hedges to unwind Monday (given MMs bought puts and were short calls -> heavy short into expiration) and price to go back up. I ended up buying 6 figures worth of calls on the drop as there was no material changes.

Strong Buy

TSM - Holy crap, please have this in your portfolio. This is a money printer, and scaling your revenue by 38-40% every year WHILE increasing gross margins is just insane. It dipped as well after smashing earnings so it's one of the easiest longs in my life.

AMKR - I don't have this in my portfolio yet but will be looking to add due to TSM's involvement in Arizona and potential to be a big partner in the US supply chain (as America tries to push TSM toward US fab + manufacturing).

WLAC - Neocloud SPAC IPO, large upside. I talk about this a lot recently, but it's probably one of the best valued Neoclouds out there, and already has great profit margins (not a pivot from miners, where it's a bit more uncertain). They work with Fluidstack, and I'd expect a 500%+ re-rating on top of a Mag7 contract.

AMZN - $213 is insane lol. I have no clue how this is down -3% YTD during a bull market.

LTC - Affected by crypto liquidations and government shutdown delaying ETFs. Great time to buy and just wait for ETF to be approved.

RDDT - Great dip to $190. I thought $200 would be a bottom but ended up going lower. The news about ChatGPT citing it less caused a large sell-off which I think was very immaterial.

HIMS - 14%+ drop off CEO share sale. Owners sell shares all the time, it doesn't really affect the fundamentals of the company much, just short term sentiment. I'd expect it to rebound.

IBIT - Bitcoin $108k great entry point, it's been swinging between $110k - $120k for awhile so anything under is usually great.

ALAB - I said this last time but it sold off way too much from news of a new competitor. It's already competing vs AVGO in the market lol, NVDA-like margins, growing hundreds of percent Y/Y, Mag7 using them in data center buildout. 

CRDO - Similar thesis to ALAB, sold off alongside Astera but a bit less.

SMCI - Should get re-rated for 55%+ or so revenue growth into next year. I doubted the projections earlier but with the data center growth, it's looking realistic.

FLY - This was a medium lift payload play. People doubt fly's execution but NOC co-developing medium lift takes a lot of risk off the table (and possible re-rating it 500%+ when it competes vs falcon9)

SNAP - Did the math on Snap monetization of memories in an earlier DD post and it's completely not priced in yet. It's doing $1.3B+ quarterly revenue on a $13B market cap lol, and the amount FCF they would get from increasing their revenue + lowering Google OPEX costs is insane.

ETOR  - Majority cash, growing at IBKR rates, suffering from tax harvesting

LULU - Suffering from tax harvesting + competition from Alo, Vuori, etc. But seasonally should be good, and extremely low p/e now.

Buy
AMD - ChatGPT putting in AMD orders, ORCL building out AMD data centers. Likely going to get a re-rating in the next year as a potential $NVDA competitor. Still think Nvidia will dominate but with it's 4.5T marketcap, AMD has a lot to catch up on even if it takes a small percent share.

HOOD - Looking at a lot better after the 10%+ correction. Could pull a PLTR

RBRK - Did DD on this earlier, looks better on the drop as a cybersecurity company really low multiples in the space. Just needs to cut back on marketing, customers sticky. 

UNH - Healthcare is sht in America but not going anywhere. Think Warren and the others know this 

TGT 🐈 - Dividend next moth, big dividend stock. Around now is a good time to load up IMO

IREN 🐈 - Huge GW, expect mag7 or similar deal. 

WYFI - Any neocloud is a buy (eg. see thesis on mag7 funneling revenue down toward these small 1B-5B companies)

WULF - neocloud play

CIFR - neocloud play

SLNH - neocloud play

BITF - neocloud play

GLXY - neocloud derivative play

FLNC - neocloud energy play

MU - China derisked, memory had a huge market there, memory also likely going to get re-rating in tdata center buildout

_

Sell

ETH - Not a fan of Ethereum at $4k+
BMNR - If I don't like Ethereum at these levels, no point of holding treasury companies 
PL - Low revenue, space stock (extremely high valuation)
BLSKY -Low revenue, space stock (extremely high valuation)
RGTI - Quantum bubble
OKLO - Nuclear bubble
IONQ -Quantum bubble 
QBTS - Quantum bubble

_

Quick macro heads up:
-> Rate cut in 9 days ~97% odds. Frontrunning expected, go long.  That's all.
```

### [盈利 #5] QBTS short hz=6m — pub=2025-10-19T18:21:35
- entry=2025-10-20, $39.52
- 1m: **resolved_hit** raw=+41.98% bench=-1.67% excess=+43.65%
- 3m: excess=+27.96%  6m: excess=+45.60%
- **条件 label**: ['PRICE_TARGET']
- **if 句**: ['5T marketcap, AMD has a lot to catch up on even if it takes a small percent share', "BMNR - If I don't like Ethereum at these levels, no point of holding treasury companies"]
- **原文 (全文)**:
```
October 20th, Important Rate Cut Trading Week.

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
$ETH
$BMNR
$PL
$BLSKY
$RGTI
$OKLO
$IONQ
$QBTS

_

So macro wise, we are 9 days away from (~97% or so rate cut). Market is in fear mode. This is the ideal time to go long and not cut positions.

Fire Sale
_

$NBIS - Needs no explanation, I still maintain $400 PT on a bull case 2026 due to 4-6B+ forward revenue off ~60-75% gross margins, and another likely hyperscaler contract (eg. $META)

What happened on the 10%+ drop on Friday was mechanical hedging and MM Pinning. You can see this with the price stuck at $113.5, despite any volatility. 

I'd expect short hedges to unwind Monday (given MMs bought puts and were short calls -> heavy short into expiration) and price to go back up. I ended up buying 6 figures worth of calls on the drop as there was no material changes.

Strong Buy

TSM - Holy crap, please have this in your portfolio. This is a money printer, and scaling your revenue by 38-40% every year WHILE increasing gross margins is just insane. It dipped as well after smashing earnings so it's one of the easiest longs in my life.

AMKR - I don't have this in my portfolio yet but will be looking to add due to TSM's involvement in Arizona and potential to be a big partner in the US supply chain (as America tries to push TSM toward US fab + manufacturing).

WLAC - Neocloud SPAC IPO, large upside. I talk about this a lot recently, but it's probably one of the best valued Neoclouds out there, and already has great profit margins (not a pivot from miners, where it's a bit more uncertain). They work with Fluidstack, and I'd expect a 500%+ re-rating on top of a Mag7 contract.

AMZN - $213 is insane lol. I have no clue how this is down -3% YTD during a bull market.

LTC - Affected by crypto liquidations and government shutdown delaying ETFs. Great time to buy and just wait for ETF to be approved.

RDDT - Great dip to $190. I thought $200 would be a bottom but ended up going lower. The news about ChatGPT citing it less caused a large sell-off which I think was very immaterial.

HIMS - 14%+ drop off CEO share sale. Owners sell shares all the time, it doesn't really affect the fundamentals of the company much, just short term sentiment. I'd expect it to rebound.

IBIT - Bitcoin $108k great entry point, it's been swinging between $110k - $120k for awhile so anything under is usually great.

ALAB - I said this last time but it sold off way too much from news of a new competitor. It's already competing vs AVGO in the market lol, NVDA-like margins, growing hundreds of percent Y/Y, Mag7 using them in data center buildout. 

CRDO - Similar thesis to ALAB, sold off alongside Astera but a bit less.

SMCI - Should get re-rated for 55%+ or so revenue growth into next year. I doubted the projections earlier but with the data center growth, it's looking realistic.

FLY - This was a medium lift payload play. People doubt fly's execution but NOC co-developing medium lift takes a lot of risk off the table (and possible re-rating it 500%+ when it competes vs falcon9)

SNAP - Did the math on Snap monetization of memories in an earlier DD post and it's completely not priced in yet. It's doing $1.3B+ quarterly revenue on a $13B market cap lol, and the amount FCF they would get from increasing their revenue + lowering Google OPEX costs is insane.

ETOR  - Majority cash, growing at IBKR rates, suffering from tax harvesting

LULU - Suffering from tax harvesting + competition from Alo, Vuori, etc. But seasonally should be good, and extremely low p/e now.

Buy
AMD - ChatGPT putting in AMD orders, ORCL building out AMD data centers. Likely going to get a re-rating in the next year as a potential $NVDA competitor. Still think Nvidia will dominate but with it's 4.5T marketcap, AMD has a lot to catch up on even if it takes a small percent share.

HOOD - Looking at a lot better after the 10%+ correction. Could pull a PLTR

RBRK - Did DD on this earlier, looks better on the drop as a cybersecurity company really low multiples in the space. Just needs to cut back on marketing, customers sticky. 

UNH - Healthcare is sht in America but not going anywhere. Think Warren and the others know this 

TGT 🐈 - Dividend next moth, big dividend stock. Around now is a good time to load up IMO

IREN 🐈 - Huge GW, expect mag7 or similar deal. 

WYFI - Any neocloud is a buy (eg. see thesis on mag7 funneling revenue down toward these small 1B-5B companies)

WULF - neocloud play

CIFR - neocloud play

SLNH - neocloud play

BITF - neocloud play

GLXY - neocloud derivative play

FLNC - neocloud energy play

MU - China derisked, memory had a huge market there, memory also likely going to get re-rating in tdata center buildout

_

Sell

ETH - Not a fan of Ethereum at $4k+
BMNR - If I don't like Ethereum at these levels, no point of holding treasury companies 
PL - Low revenue, space stock (extremely high valuation)
BLSKY -Low revenue, space stock (extremely high valuation)
RGTI - Quantum bubble
OKLO - Nuclear bubble
IONQ -Quantum bubble 
QBTS - Quantum bubble

_

Quick macro heads up:
-> Rate cut in 9 days ~97% odds. Frontrunning expected, go long.  That's all.
```

### [盈利 #6] BMNR short hz=6m — pub=2025-10-19T18:21:35
- entry=2025-10-20, $52.75
- 1m: **resolved_hit** raw=+38.81% bench=-1.67% excess=+40.48%
- 3m: excess=+42.58%  6m: excess=+52.76%
- **条件 label**: ['PRICE_TARGET']
- **if 句**: ['5T marketcap, AMD has a lot to catch up on even if it takes a small percent share', "BMNR - If I don't like Ethereum at these levels, no point of holding treasury companies"]
- **原文 (全文)**:
```
October 20th, Important Rate Cut Trading Week.

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
$ETH
$BMNR
$PL
$BLSKY
$RGTI
$OKLO
$IONQ
$QBTS

_

So macro wise, we are 9 days away from (~97% or so rate cut). Market is in fear mode. This is the ideal time to go long and not cut positions.

Fire Sale
_

$NBIS - Needs no explanation, I still maintain $400 PT on a bull case 2026 due to 4-6B+ forward revenue off ~60-75% gross margins, and another likely hyperscaler contract (eg. $META)

What happened on the 10%+ drop on Friday was mechanical hedging and MM Pinning. You can see this with the price stuck at $113.5, despite any volatility. 

I'd expect short hedges to unwind Monday (given MMs bought puts and were short calls -> heavy short into expiration) and price to go back up. I ended up buying 6 figures worth of calls on the drop as there was no material changes.

Strong Buy

TSM - Holy crap, please have this in your portfolio. This is a money printer, and scaling your revenue by 38-40% every year WHILE increasing gross margins is just insane. It dipped as well after smashing earnings so it's one of the easiest longs in my life.

AMKR - I don't have this in my portfolio yet but will be looking to add due to TSM's involvement in Arizona and potential to be a big partner in the US supply chain (as America tries to push TSM toward US fab + manufacturing).

WLAC - Neocloud SPAC IPO, large upside. I talk about this a lot recently, but it's probably one of the best valued Neoclouds out there, and already has great profit margins (not a pivot from miners, where it's a bit more uncertain). They work with Fluidstack, and I'd expect a 500%+ re-rating on top of a Mag7 contract.

AMZN - $213 is insane lol. I have no clue how this is down -3% YTD during a bull market.

LTC - Affected by crypto liquidations and government shutdown delaying ETFs. Great time to buy and just wait for ETF to be approved.

RDDT - Great dip to $190. I thought $200 would be a bottom but ended up going lower. The news about ChatGPT citing it less caused a large sell-off which I think was very immaterial.

HIMS - 14%+ drop off CEO share sale. Owners sell shares all the time, it doesn't really affect the fundamentals of the company much, just short term sentiment. I'd expect it to rebound.

IBIT - Bitcoin $108k great entry point, it's been swinging between $110k - $120k for awhile so anything under is usually great.

ALAB - I said this last time but it sold off way too much from news of a new competitor. It's already competing vs AVGO in the market lol, NVDA-like margins, growing hundreds of percent Y/Y, Mag7 using them in data center buildout. 

CRDO - Similar thesis to ALAB, sold off alongside Astera but a bit less.

SMCI - Should get re-rated for 55%+ or so revenue growth into next year. I doubted the projections earlier but with the data center growth, it's looking realistic.

FLY - This was a medium lift payload play. People doubt fly's execution but NOC co-developing medium lift takes a lot of risk off the table (and possible re-rating it 500%+ when it competes vs falcon9)

SNAP - Did the math on Snap monetization of memories in an earlier DD post and it's completely not priced in yet. It's doing $1.3B+ quarterly revenue on a $13B market cap lol, and the amount FCF they would get from increasing their revenue + lowering Google OPEX costs is insane.

ETOR  - Majority cash, growing at IBKR rates, suffering from tax harvesting

LULU - Suffering from tax harvesting + competition from Alo, Vuori, etc. But seasonally should be good, and extremely low p/e now.

Buy
AMD - ChatGPT putting in AMD orders, ORCL building out AMD data centers. Likely going to get a re-rating in the next year as a potential $NVDA competitor. Still think Nvidia will dominate but with it's 4.5T marketcap, AMD has a lot to catch up on even if it takes a small percent share.

HOOD - Looking at a lot better after the 10%+ correction. Could pull a PLTR

RBRK - Did DD on this earlier, looks better on the drop as a cybersecurity company really low multiples in the space. Just needs to cut back on marketing, customers sticky. 

UNH - Healthcare is sht in America but not going anywhere. Think Warren and the others know this 

TGT 🐈 - Dividend next moth, big dividend stock. Around now is a good time to load up IMO

IREN 🐈 - Huge GW, expect mag7 or similar deal. 

WYFI - Any neocloud is a buy (eg. see thesis on mag7 funneling revenue down toward these small 1B-5B companies)

WULF - neocloud play

CIFR - neocloud play

SLNH - neocloud play

BITF - neocloud play

GLXY - neocloud derivative play

FLNC - neocloud energy play

MU - China derisked, memory had a huge market there, memory also likely going to get re-rating in tdata center buildout

_

Sell

ETH - Not a fan of Ethereum at $4k+
BMNR - If I don't like Ethereum at these levels, no point of holding treasury companies 
PL - Low revenue, space stock (extremely high valuation)
BLSKY -Low revenue, space stock (extremely high valuation)
RGTI - Quantum bubble
OKLO - Nuclear bubble
IONQ -Quantum bubble 
QBTS - Quantum bubble

_

Quick macro heads up:
-> Rate cut in 9 days ~97% odds. Frontrunning expected, go long.  That's all.
```

### [盈利 #7] BMNR short hz=6m — pub=2025-10-04T01:22:20
- entry=2025-10-06, $59.58
- 1m: **resolved_hit** raw=+33.77% bench=+0.54% excess=+33.23%
- 3m: excess=+46.37%  6m: excess=+63.38%
- **条件 label**: ['PRICE_TARGET']
- **if 句**: ["BMNR - Just buy ETH if you believe in it but I wouldn't buy at ETH at $4500"]
- **原文 (全文)**:
```
Friday Market Close, Personal Thoughts and Explanations:

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

Reddit - Dropped 29% off immaterial news that ChatGPT wasn't citing it as much. Nobody visits Reddit through ChatGPT, good recovery buy off $200 support. 

SNAP - Finally they're doing something that's USEFUL for the first time in many years lol. Tons of Capex was spent on storing photos random drawings people saved 12 years ago taking GBs of space for their insane Google Cloud costs. They're finally monetizing it like Apple. Huge tailwind, should improve net income by a ton next year. 

AMZN - Under $220 now, great buy. AMZN prime Oct 8th, good for seasonality in Nov/Dec.

ETOR - I can't believe this is still $41. 33% cash, 1B+ cash pile growing at IBKR rates. Just suffers from tax harvesting I'd assume it goes up next year. 

NBIS - Strong buy until $150+ or new hyperscaler contract repricing. 

LTC - ETF catalyst delayed from Gov shutdown but should be approved anyway. 

Buys

Upwork - Down 4.5% or so for no reason, should recover

MSTR - BTC close to all time highs, MSTR way off ATHs cause of long btc short MSTR but NAV premium should catch up again from the BTC fomo.

ORCL - Standard rise on great forward earnings, drop for short term option chain, then rise because 14B tiktok deal and large future cloud contracts

TGT - Just undervalued great buy under $93, dividend catalyst next month

CIFR - NBIS light with GOOGL deal.

VIRT - VIX doesn't look like it's going down anytime soon but they're trading at like 6.4 or so forward P/E so it's worth.

CRDO - Good buy on correction with hypescaler buildout

WULF - Hasn't gone up as much as the other neoclouds, googl backlog

SOFI - Corrected, might recover back to ATH given macro tailwind

META - Monthly low good DCA, not as good as AMZN

AVGO - Same as ORCL, might end up like NVDA one day with hyperscaler chips

MRVL - Still down 24% YTD. 

SMCI - Good buy on datacenter buildout + server racks

Dell - Good buy on datacenter buildout + server racks

Hold

Nothing changed

Sell

TSLA - Overvalued, better longs like NBIS

CRCL - I will keep making this argument, but just buy COIN instead. You will get the same 50% revenue sharing but with a crypto exchange + ETF holding income too.  

PLTR - Disconnected from reality

BMNR - Just buy ETH if you believe in it but I wouldn't buy at ETH at $4500.

Strong Sell

RGTI - Disconnected from reality lol

All disconnected from reality, wouldn't short though cause all cult stocks. 
OKLO
QBTS
IONQ
```

### [盈利 #8] RKLB long hz=event_driven — pub=2025-10-01T23:39:48
- entry=2025-10-02, $48.64
- 1m: **resolved_hit** raw=+29.48% bench=+1.92% excess=+27.56%
- 3m: excess=+57.89%  6m: excess=+37.84%
- **条件 label**: ['PRICE_TARGET']
- **if 句**: ["You can do it with stuff like Rocketlab since long term if you hold enough, even if it dips past $40 it will likely recover since it's a strong buy fundamentally albeit a tiny overvalued now", 'If it ever dips past $210, you can do leaps', 'These lines mean nothing if forward revenue falls a lot or industry margins compresses']
- **原文 (全文)**:
```
How I do swing trading with charts, Part 2:  Short term (few week) + Short-Medium Term (few month). 

I'll do long term ones in another post.   

Ex 1: $RKLB. Just going off feels on this, seems like a great buy at $40 support, and $54 sell. Usually lower half (dotted line) like $44 is a good buy too cause risk-reward is good but u wont get the actual bottom.  

You can do it with stuff like Rocketlab since long term if you hold enough, even if it dips past $40 it will likely recover since it's a strong buy fundamentally albeit a tiny overvalued now.   

Example 2: $AMZN - Great buy with shares now. If it ever dips past $210, you can do leaps. Lower than $200 for example, shorter dated calls.   

_ 

Knowing fundamentals, macro, and whether catalysts are material or not is really also important. These lines mean nothing if forward revenue falls a lot or industry margins compresses.   

Lot of time they drop on more irrational things eg. GOOGL with Apple search, or maybe overall market SPY dipping but in those cases they usually rise up again if there's no difference + company keeps growing.   Again different for everyone, you need to analyze more than the charts when timing bottoms. This is just part of what I do.
```

### [盈利 #9] CRCL short hz=6m — pub=2025-10-04T01:22:20
- entry=2025-10-06, $154.01
- 1m: **resolved_hit** raw=+27.76% bench=+0.54% excess=+27.22%
- 3m: excess=+45.00%  6m: excess=+43.51%
- **条件 label**: ['PRICE_TARGET']
- **if 句**: ["BMNR - Just buy ETH if you believe in it but I wouldn't buy at ETH at $4500"]
- **原文 (全文)**:
```
Friday Market Close, Personal Thoughts and Explanations:

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

Reddit - Dropped 29% off immaterial news that ChatGPT wasn't citing it as much. Nobody visits Reddit through ChatGPT, good recovery buy off $200 support. 

SNAP - Finally they're doing something that's USEFUL for the first time in many years lol. Tons of Capex was spent on storing photos random drawings people saved 12 years ago taking GBs of space for their insane Google Cloud costs. They're finally monetizing it like Apple. Huge tailwind, should improve net income by a ton next year. 

AMZN - Under $220 now, great buy. AMZN prime Oct 8th, good for seasonality in Nov/Dec.

ETOR - I can't believe this is still $41. 33% cash, 1B+ cash pile growing at IBKR rates. Just suffers from tax harvesting I'd assume it goes up next year. 

NBIS - Strong buy until $150+ or new hyperscaler contract repricing. 

LTC - ETF catalyst delayed from Gov shutdown but should be approved anyway. 

Buys

Upwork - Down 4.5% or so for no reason, should recover

MSTR - BTC close to all time highs, MSTR way off ATHs cause of long btc short MSTR but NAV premium should catch up again from the BTC fomo.

ORCL - Standard rise on great forward earnings, drop for short term option chain, then rise because 14B tiktok deal and large future cloud contracts

TGT - Just undervalued great buy under $93, dividend catalyst next month

CIFR - NBIS light with GOOGL deal.

VIRT - VIX doesn't look like it's going down anytime soon but they're trading at like 6.4 or so forward P/E so it's worth.

CRDO - Good buy on correction with hypescaler buildout

WULF - Hasn't gone up as much as the other neoclouds, googl backlog

SOFI - Corrected, might recover back to ATH given macro tailwind

META - Monthly low good DCA, not as good as AMZN

AVGO - Same as ORCL, might end up like NVDA one day with hyperscaler chips

MRVL - Still down 24% YTD. 

SMCI - Good buy on datacenter buildout + server racks

Dell - Good buy on datacenter buildout + server racks

Hold

Nothing changed

Sell

TSLA - Overvalued, better longs like NBIS

CRCL - I will keep making this argument, but just buy COIN instead. You will get the same 50% revenue sharing but with a crypto exchange + ETF holding income too.  

PLTR - Disconnected from reality

BMNR - Just buy ETH if you believe in it but I wouldn't buy at ETH at $4500.

Strong Sell

RGTI - Disconnected from reality lol

All disconnected from reality, wouldn't short though cause all cult stocks. 
OKLO
QBTS
IONQ
```

### [盈利 #10] IONQ short hz=6m — pub=2025-10-19T18:21:35
- entry=2025-10-20, $65.31
- 1m: **resolved_hit** raw=+24.79% bench=-1.67% excess=+26.46%
- 3m: excess=+21.83%  6m: excess=+27.66%
- **条件 label**: ['PRICE_TARGET']
- **if 句**: ['5T marketcap, AMD has a lot to catch up on even if it takes a small percent share', "BMNR - If I don't like Ethereum at these levels, no point of holding treasury companies"]
- **原文 (全文)**:
```
October 20th, Important Rate Cut Trading Week.

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
$ETH
$BMNR
$PL
$BLSKY
$RGTI
$OKLO
$IONQ
$QBTS

_

So macro wise, we are 9 days away from (~97% or so rate cut). Market is in fear mode. This is the ideal time to go long and not cut positions.

Fire Sale
_

$NBIS - Needs no explanation, I still maintain $400 PT on a bull case 2026 due to 4-6B+ forward revenue off ~60-75% gross margins, and another likely hyperscaler contract (eg. $META)

What happened on the 10%+ drop on Friday was mechanical hedging and MM Pinning. You can see this with the price stuck at $113.5, despite any volatility. 

I'd expect short hedges to unwind Monday (given MMs bought puts and were short calls -> heavy short into expiration) and price to go back up. I ended up buying 6 figures worth of calls on the drop as there was no material changes.

Strong Buy

TSM - Holy crap, please have this in your portfolio. This is a money printer, and scaling your revenue by 38-40% every year WHILE increasing gross margins is just insane. It dipped as well after smashing earnings so it's one of the easiest longs in my life.

AMKR - I don't have this in my portfolio yet but will be looking to add due to TSM's involvement in Arizona and potential to be a big partner in the US supply chain (as America tries to push TSM toward US fab + manufacturing).

WLAC - Neocloud SPAC IPO, large upside. I talk about this a lot recently, but it's probably one of the best valued Neoclouds out there, and already has great profit margins (not a pivot from miners, where it's a bit more uncertain). They work with Fluidstack, and I'd expect a 500%+ re-rating on top of a Mag7 contract.

AMZN - $213 is insane lol. I have no clue how this is down -3% YTD during a bull market.

LTC - Affected by crypto liquidations and government shutdown delaying ETFs. Great time to buy and just wait for ETF to be approved.

RDDT - Great dip to $190. I thought $200 would be a bottom but ended up going lower. The news about ChatGPT citing it less caused a large sell-off which I think was very immaterial.

HIMS - 14%+ drop off CEO share sale. Owners sell shares all the time, it doesn't really affect the fundamentals of the company much, just short term sentiment. I'd expect it to rebound.

IBIT - Bitcoin $108k great entry point, it's been swinging between $110k - $120k for awhile so anything under is usually great.

ALAB - I said this last time but it sold off way too much from news of a new competitor. It's already competing vs AVGO in the market lol, NVDA-like margins, growing hundreds of percent Y/Y, Mag7 using them in data center buildout. 

CRDO - Similar thesis to ALAB, sold off alongside Astera but a bit less.

SMCI - Should get re-rated for 55%+ or so revenue growth into next year. I doubted the projections earlier but with the data center growth, it's looking realistic.

FLY - This was a medium lift payload play. People doubt fly's execution but NOC co-developing medium lift takes a lot of risk off the table (and possible re-rating it 500%+ when it competes vs falcon9)

SNAP - Did the math on Snap monetization of memories in an earlier DD post and it's completely not priced in yet. It's doing $1.3B+ quarterly revenue on a $13B market cap lol, and the amount FCF they would get from increasing their revenue + lowering Google OPEX costs is insane.

ETOR  - Majority cash, growing at IBKR rates, suffering from tax harvesting

LULU - Suffering from tax harvesting + competition from Alo, Vuori, etc. But seasonally should be good, and extremely low p/e now.

Buy
AMD - ChatGPT putting in AMD orders, ORCL building out AMD data centers. Likely going to get a re-rating in the next year as a potential $NVDA competitor. Still think Nvidia will dominate but with it's 4.5T marketcap, AMD has a lot to catch up on even if it takes a small percent share.

HOOD - Looking at a lot better after the 10%+ correction. Could pull a PLTR

RBRK - Did DD on this earlier, looks better on the drop as a cybersecurity company really low multiples in the space. Just needs to cut back on marketing, customers sticky. 

UNH - Healthcare is sht in America but not going anywhere. Think Warren and the others know this 

TGT 🐈 - Dividend next moth, big dividend stock. Around now is a good time to load up IMO

IREN 🐈 - Huge GW, expect mag7 or similar deal. 

WYFI - Any neocloud is a buy (eg. see thesis on mag7 funneling revenue down toward these small 1B-5B companies)

WULF - neocloud play

CIFR - neocloud play

SLNH - neocloud play

BITF - neocloud play

GLXY - neocloud derivative play

FLNC - neocloud energy play

MU - China derisked, memory had a huge market there, memory also likely going to get re-rating in tdata center buildout

_

Sell

ETH - Not a fan of Ethereum at $4k+
BMNR - If I don't like Ethereum at these levels, no point of holding treasury companies 
PL - Low revenue, space stock (extremely high valuation)
BLSKY -Low revenue, space stock (extremely high valuation)
RGTI - Quantum bubble
OKLO - Nuclear bubble
IONQ -Quantum bubble 
QBTS - Quantum bubble

_

Quick macro heads up:
-> Rate cut in 9 days ~97% odds. Frontrunning expected, go long.  That's all.
```

### [盈利 #11] IONQ short hz=6m — pub=2025-10-04T01:22:20
- entry=2025-10-06, $72.00
- 1m: **resolved_hit** raw=+25.86% bench=+0.54% excess=+25.32%
- 3m: excess=+28.19%  6m: excess=+59.76%
- **条件 label**: ['PRICE_TARGET']
- **if 句**: ["BMNR - Just buy ETH if you believe in it but I wouldn't buy at ETH at $4500"]
- **原文 (全文)**:
```
Friday Market Close, Personal Thoughts and Explanations:

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

Reddit - Dropped 29% off immaterial news that ChatGPT wasn't citing it as much. Nobody visits Reddit through ChatGPT, good recovery buy off $200 support. 

SNAP - Finally they're doing something that's USEFUL for the first time in many years lol. Tons of Capex was spent on storing photos random drawings people saved 12 years ago taking GBs of space for their insane Google Cloud costs. They're finally monetizing it like Apple. Huge tailwind, should improve net income by a ton next year. 

AMZN - Under $220 now, great buy. AMZN prime Oct 8th, good for seasonality in Nov/Dec.

ETOR - I can't believe this is still $41. 33% cash, 1B+ cash pile growing at IBKR rates. Just suffers from tax harvesting I'd assume it goes up next year. 

NBIS - Strong buy until $150+ or new hyperscaler contract repricing. 

LTC - ETF catalyst delayed from Gov shutdown but should be approved anyway. 

Buys

Upwork - Down 4.5% or so for no reason, should recover

MSTR - BTC close to all time highs, MSTR way off ATHs cause of long btc short MSTR but NAV premium should catch up again from the BTC fomo.

ORCL - Standard rise on great forward earnings, drop for short term option chain, then rise because 14B tiktok deal and large future cloud contracts

TGT - Just undervalued great buy under $93, dividend catalyst next month

CIFR - NBIS light with GOOGL deal.

VIRT - VIX doesn't look like it's going down anytime soon but they're trading at like 6.4 or so forward P/E so it's worth.

CRDO - Good buy on correction with hypescaler buildout

WULF - Hasn't gone up as much as the other neoclouds, googl backlog

SOFI - Corrected, might recover back to ATH given macro tailwind

META - Monthly low good DCA, not as good as AMZN

AVGO - Same as ORCL, might end up like NVDA one day with hyperscaler chips

MRVL - Still down 24% YTD. 

SMCI - Good buy on datacenter buildout + server racks

Dell - Good buy on datacenter buildout + server racks

Hold

Nothing changed

Sell

TSLA - Overvalued, better longs like NBIS

CRCL - I will keep making this argument, but just buy COIN instead. You will get the same 50% revenue sharing but with a crypto exchange + ETF holding income too.  

PLTR - Disconnected from reality

BMNR - Just buy ETH if you believe in it but I wouldn't buy at ETH at $4500.

Strong Sell

RGTI - Disconnected from reality lol

All disconnected from reality, wouldn't short though cause all cult stocks. 
OKLO
QBTS
IONQ
```

### [盈利 #12] MU long hz=6m — pub=2025-10-15T07:42:21
- entry=2025-10-16, $199.96
- 1m: **resolved_hit** raw=+23.44% bench=+1.71% excess=+21.73%
- 3m: excess=+79.97%  6m: excess=+118.16%
- **条件 label**: ['PRICE_TARGET']
- **if 句**: ['This would be a $3T company if this were a US company, insane profit margins, insane growth rate for their size', '5T), even if buying at ATHs', "AMZN hitting $213-215 today was a good chance to stock up since it usually floats between $218-$227 if you're short term swing trading but long term I'd expect it to catchup to other mag7"]
- **原文 (全文)**:
```
The Great Soybean/Seed Oil Crash, personal thoughts and explanations:

Strong Buy
$ALAB
$CRDO
$NBIS
$WLAC
$LTC
$TSM
$BTC
(+ same as tax harvest stocks last time)
$AMZN
$SMCI
_

Buy
$AMD
$FLNC
$SEI
$BZAI
$NKLR
$IREN
$WULF
$CIFR
$CRWV
$BITF
$WYFI
$SLNH
$BITF
$RBRK
$GLXY
$GRAB
$SEA
$META
$TGT
$SNAP
$MU
$RKLB
$FLY
$UNH

Hold
$MP
$HOOD
$EOSE
$NVDA
$GOOGL
$DFLI
$SOFI
$VIRT
$RR
$AVGO
$BE
$ASTS

(Hit the ticker maximum but everything else from last post, still sell on Quantum or Oklo)
_

Strong Buys
ALAB - Huge part of datacenter buildout, NVDA like margins, Mag7 customers. Already had competitors from AVGO,  really don't think Arista would be a competitive threat.

CRDO - Same sell-off as ALAB, thought they were both kind of overvalued before, but now they're back in correction territory so good to stock up.

NBIS - $400 PT bull case. We have macro tailwind from government re-opening + rate cut EOM october into earnings, so short term looks promising. Lot of things going for it (eg. meta x crwv, so there's potential for more mag7 clients), sum of parts doing well, eg. clickhouse, and scaling rev from $100m to $1.5B+ a quarter is insane. there's already contracts locked in its just a matter of company execution.

WLAC - Wrote a thesis about this earlier at $13. Even at $14.5 strong because it can re-rate 100%+ easily.

LTC - Affected by leverage traders and government shutdown. The shutdown is predicted to last awhile and the main reason to buy was the ETF getting approved. But a great buy sub <$100 anyway, because it will get approved in due time (~95% chance).

TSM - Holy crap. This would be a $3T company if this were a US company, insane profit margins, insane growth rate for their size. And every post you see about OpenAi X (**sydney sweeney partnership) or AMD buildout/NVDA buildout. TSM is the center of it all and would easily be a $2T+ company (from here at ~$1.5T), even if buying at ATHs.

BTC - $112K good entry point. Goldt keeps hitting ATH, nothing really changed fundamentally, just lot of liquidations recently
(+ same as tax harvest stocks last time)

AMZN - I really don't know how it's still down YTD. I don't think Amazon needs much explaining but still growing  (eg. AWS backlog massive, still going like 24% but not as much as ORCL, GCP and others obviously), but with EOY seasonality and runup to Feb, now is probably the best chance to catch the bottom. AMZN hitting $213-215 today was a good chance to stock up since it usually floats between $218-$227 if you're short term swing trading but long term I'd expect it to catchup to other mag7.

SMCI - Underrated. Markets were looking short term performance, and Charles was quoting like 55%+ Y/Y forward revenue growth which nobody believed + backlog that didnt get realized yet. But now with all the data center buildouts, now it's kinda making sense. So should re-rate in the next two earnings.

_
Buy

AMD - So many deals from OpenAI x AMD, oracle building out with AMD, this is going to re-rate to a potential $1T+ company if it's actually a strong competitive to $NVDA.  I don't think it's winner takes all and you can see a $4.5T+ market cap size with NVDA and some $350B marketcap size with AMD, so we can see a large ramp up (OpenAI is usually the leader in frontier models and if Sam says they can use AMD chips + elon said its' good for small-medium weight models, prboably means something positive)

FLNC - Strong re-rate on energy after AI consumption, great buy.

SEI - Strong re-rate on energy after AI consumption, great buy.

BZAI - Someone else did a DD on this company, just cause of sector and shift to edge compute (eg. Robotics goign to be hot). Because of low MC and runup of similar companies could turn out well.

NKLR - Nuclear stocks like $OKLO have been taking off, this is just follow the lader.

IREN - Needs no introduction, huge GW compute capacity just no announced mag7 deals yet but could come anytime -> strong re-rate. Only reason not a strong buy is because not fully convinced miners can pivot like CRWV and maintain great margins (eg. $ORCL hit piece) but we'll see.

WULF - GOOGL backlog, another $3.6+ or so in funding helps a lot.

CIFR - Lot of info on X about future capacity and strong re-rating. Always liked this company because it was NBIS-lite. You can probably buy any Neocloud and it will go up because the sector is incredibly high potential with Mag7 funneling revenue.

CRWV - Didn't like this as much as others because of debt but because of the seed oil correction much better buy point at $134 (below when META deal was announced)

BITF - Same in Neocloud category

WYFI - Same in Neocloud category

BITF - Same in Neocloud category

GLXY - Same in Neocloud category, helps with their buildout

RBRK - Did a DD on this, great buy for cybersecurity sector in mid term, they just need to scale back marketing and then it looks like they have a lot more FCF because they're spending most OPEX on marketing.

GRAB - Great fundamentally, -6.56% correction good to buy again

SEA - AMZN in SEA, tons of people use them. Just a buy just because of costumer base + monetization potenetial. Fundamentally growing $5B+ rev 38% Y/Y is also great.

META - I really don't like all their expensive capex on AI since they're not really putting out fronteir models like ChatGPT with it, who knows what Zuck is doing. But that aside, down 7.3% over the month, going to $700 support, probably a good buy around here to play catchup.

TGT - Dividend next month good catalyst.

SNAP - The Jenners are coming back (helps with popularity), they're shifting former memory opex to revenue, and this will probably cause a HUGE rerating next year. Just suffers from tax harvesting otherwise would be a strong buy rn. Usually tax harvesting events are kinda done in December.

MU - Now that China fears are kinda less intense, MU is a lot stronger buy just cause of memory use on buildout.

RKLB - Neutron, golden dome contracts, lot of cataylsts

FLY - Medium lift

UNH - Healthcare stock not affected by soybeans but had a correction. Would likely go up one instituions post their ports (eg. warren likely bought more)

Random thoughts
Basically any growth/risk stock that's not named Oklo is great because we have

-> Rate Cut end of month October
-> Government re-opening sometime (likely around end of Oct or early Nov)

Into
-> Rate Cut December.
-> Midterms (Bullish for stocks)

Usually market crashes happen when there's tightening not easing. And your stupid quantum bubbles would likely continue for another 3-12 months afterward. If you're short, then probably wait till next Feb.

Anyway, this is a great time for risk-on, and specially riding trends with neoclouds -> affiliated sectors (eg. energy) -> affiliated companies (eg. smci, tsm, etc).

I half joke-about soybeans because it likely signed escalating tensions, but I'd probably see a run-up into next year. Also I could write up a lot about each one but it's pretty time consuming but I'll put on a thesis post about random ones eg. $RBRK, from time to time.

Space/robotics/energy/quantum/ai/semi/critical top verticals right now, don't fight against momentum. I can think something is overvalued (eg. some critical materials bc. it's still spectulative compared to neoclouds that kinda have guaranteed rev based on execution from mag7) but I wouldn't short it into rate cuts.

Just personal thoughts, NFA
```

### [盈利 #13] WULF long hz=6m — pub=2025-10-04T01:22:20
- entry=2025-10-06, $12.39
- 1m: **resolved_hit** raw=+21.15% bench=+0.54% excess=+20.61%
- 3m: excess=-1.87%  6m: excess=+52.36%
- **条件 label**: ['PRICE_TARGET']
- **if 句**: ["BMNR - Just buy ETH if you believe in it but I wouldn't buy at ETH at $4500"]
- **原文 (全文)**:
```
Friday Market Close, Personal Thoughts and Explanations:

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

Reddit - Dropped 29% off immaterial news that ChatGPT wasn't citing it as much. Nobody visits Reddit through ChatGPT, good recovery buy off $200 support. 

SNAP - Finally they're doing something that's USEFUL for the first time in many years lol. Tons of Capex was spent on storing photos random drawings people saved 12 years ago taking GBs of space for their insane Google Cloud costs. They're finally monetizing it like Apple. Huge tailwind, should improve net income by a ton next year. 

AMZN - Under $220 now, great buy. AMZN prime Oct 8th, good for seasonality in Nov/Dec.

ETOR - I can't believe this is still $41. 33% cash, 1B+ cash pile growing at IBKR rates. Just suffers from tax harvesting I'd assume it goes up next year. 

NBIS - Strong buy until $150+ or new hyperscaler contract repricing. 

LTC - ETF catalyst delayed from Gov shutdown but should be approved anyway. 

Buys

Upwork - Down 4.5% or so for no reason, should recover

MSTR - BTC close to all time highs, MSTR way off ATHs cause of long btc short MSTR but NAV premium should catch up again from the BTC fomo.

ORCL - Standard rise on great forward earnings, drop for short term option chain, then rise because 14B tiktok deal and large future cloud contracts

TGT - Just undervalued great buy under $93, dividend catalyst next month

CIFR - NBIS light with GOOGL deal.

VIRT - VIX doesn't look like it's going down anytime soon but they're trading at like 6.4 or so forward P/E so it's worth.

CRDO - Good buy on correction with hypescaler buildout

WULF - Hasn't gone up as much as the other neoclouds, googl backlog

SOFI - Corrected, might recover back to ATH given macro tailwind

META - Monthly low good DCA, not as good as AMZN

AVGO - Same as ORCL, might end up like NVDA one day with hyperscaler chips

MRVL - Still down 24% YTD. 

SMCI - Good buy on datacenter buildout + server racks

Dell - Good buy on datacenter buildout + server racks

Hold

Nothing changed

Sell

TSLA - Overvalued, better longs like NBIS

CRCL - I will keep making this argument, but just buy COIN instead. You will get the same 50% revenue sharing but with a crypto exchange + ETF holding income too.  

PLTR - Disconnected from reality

BMNR - Just buy ETH if you believe in it but I wouldn't buy at ETH at $4500.

Strong Sell

RGTI - Disconnected from reality lol

All disconnected from reality, wouldn't short though cause all cult stocks. 
OKLO
QBTS
IONQ
```

### [盈利 #14] PL short hz=6m — pub=2025-10-19T18:21:35
- entry=2025-10-20, $14.02
- 1m: **resolved_hit** raw=+18.33% bench=-1.67% excess=+20.00%
- 3m: excess=-88.51%  6m: excess=-178.64%
- **条件 label**: ['PRICE_TARGET']
- **if 句**: ['5T marketcap, AMD has a lot to catch up on even if it takes a small percent share', "BMNR - If I don't like Ethereum at these levels, no point of holding treasury companies"]
- **原文 (全文)**:
```
October 20th, Important Rate Cut Trading Week.

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
$ETH
$BMNR
$PL
$BLSKY
$RGTI
$OKLO
$IONQ
$QBTS

_

So macro wise, we are 9 days away from (~97% or so rate cut). Market is in fear mode. This is the ideal time to go long and not cut positions.

Fire Sale
_

$NBIS - Needs no explanation, I still maintain $400 PT on a bull case 2026 due to 4-6B+ forward revenue off ~60-75% gross margins, and another likely hyperscaler contract (eg. $META)

What happened on the 10%+ drop on Friday was mechanical hedging and MM Pinning. You can see this with the price stuck at $113.5, despite any volatility. 

I'd expect short hedges to unwind Monday (given MMs bought puts and were short calls -> heavy short into expiration) and price to go back up. I ended up buying 6 figures worth of calls on the drop as there was no material changes.

Strong Buy

TSM - Holy crap, please have this in your portfolio. This is a money printer, and scaling your revenue by 38-40% every year WHILE increasing gross margins is just insane. It dipped as well after smashing earnings so it's one of the easiest longs in my life.

AMKR - I don't have this in my portfolio yet but will be looking to add due to TSM's involvement in Arizona and potential to be a big partner in the US supply chain (as America tries to push TSM toward US fab + manufacturing).

WLAC - Neocloud SPAC IPO, large upside. I talk about this a lot recently, but it's probably one of the best valued Neoclouds out there, and already has great profit margins (not a pivot from miners, where it's a bit more uncertain). They work with Fluidstack, and I'd expect a 500%+ re-rating on top of a Mag7 contract.

AMZN - $213 is insane lol. I have no clue how this is down -3% YTD during a bull market.

LTC - Affected by crypto liquidations and government shutdown delaying ETFs. Great time to buy and just wait for ETF to be approved.

RDDT - Great dip to $190. I thought $200 would be a bottom but ended up going lower. The news about ChatGPT citing it less caused a large sell-off which I think was very immaterial.

HIMS - 14%+ drop off CEO share sale. Owners sell shares all the time, it doesn't really affect the fundamentals of the company much, just short term sentiment. I'd expect it to rebound.

IBIT - Bitcoin $108k great entry point, it's been swinging between $110k - $120k for awhile so anything under is usually great.

ALAB - I said this last time but it sold off way too much from news of a new competitor. It's already competing vs AVGO in the market lol, NVDA-like margins, growing hundreds of percent Y/Y, Mag7 using them in data center buildout. 

CRDO - Similar thesis to ALAB, sold off alongside Astera but a bit less.

SMCI - Should get re-rated for 55%+ or so revenue growth into next year. I doubted the projections earlier but with the data center growth, it's looking realistic.

FLY - This was a medium lift payload play. People doubt fly's execution but NOC co-developing medium lift takes a lot of risk off the table (and possible re-rating it 500%+ when it competes vs falcon9)

SNAP - Did the math on Snap monetization of memories in an earlier DD post and it's completely not priced in yet. It's doing $1.3B+ quarterly revenue on a $13B market cap lol, and the amount FCF they would get from increasing their revenue + lowering Google OPEX costs is insane.

ETOR  - Majority cash, growing at IBKR rates, suffering from tax harvesting

LULU - Suffering from tax harvesting + competition from Alo, Vuori, etc. But seasonally should be good, and extremely low p/e now.

Buy
AMD - ChatGPT putting in AMD orders, ORCL building out AMD data centers. Likely going to get a re-rating in the next year as a potential $NVDA competitor. Still think Nvidia will dominate but with it's 4.5T marketcap, AMD has a lot to catch up on even if it takes a small percent share.

HOOD - Looking at a lot better after the 10%+ correction. Could pull a PLTR

RBRK - Did DD on this earlier, looks better on the drop as a cybersecurity company really low multiples in the space. Just needs to cut back on marketing, customers sticky. 

UNH - Healthcare is sht in America but not going anywhere. Think Warren and the others know this 

TGT 🐈 - Dividend next moth, big dividend stock. Around now is a good time to load up IMO

IREN 🐈 - Huge GW, expect mag7 or similar deal. 

WYFI - Any neocloud is a buy (eg. see thesis on mag7 funneling revenue down toward these small 1B-5B companies)

WULF - neocloud play

CIFR - neocloud play

SLNH - neocloud play

BITF - neocloud play

GLXY - neocloud derivative play

FLNC - neocloud energy play

MU - China derisked, memory had a huge market there, memory also likely going to get re-rating in tdata center buildout

_

Sell

ETH - Not a fan of Ethereum at $4k+
BMNR - If I don't like Ethereum at these levels, no point of holding treasury companies 
PL - Low revenue, space stock (extremely high valuation)
BLSKY -Low revenue, space stock (extremely high valuation)
RGTI - Quantum bubble
OKLO - Nuclear bubble
IONQ -Quantum bubble 
QBTS - Quantum bubble

_

Quick macro heads up:
-> Rate cut in 9 days ~97% odds. Frontrunning expected, go long.  That's all.
```

### [盈利 #15] CRCL long hz=8m — pub=2025-11-20T10:23:51
- entry=2025-11-21, $66.92
- 1m: **resolved_hit** raw=+23.48% bench=+4.76% excess=+18.72%
- 3m: excess=+25.72%  6m: excess=+47.23%
- **条件 label**: ['PRICE_TARGET']
- **if 句**: ["My thesis was that if Mag7 is dependent on a company ($NVDA for GPUs) ( NBIS, IREN, CIFR for DC AI cloud buildout), the company will blow away expections quarter after quarter, and we're seeing this", "A TLDR of my most recent thesis post was that they're cutting their massive opex bloat from memories/videos stored 10 years ago and if you look into their GCP hosting fees, it's cutting in margins", 'Happy to discuss more if you drop your own portfolio + concentrations']
- **原文 (全文)**:
```
Based on the equity ranking table:

Here's a deeper analysis of each stock, alongside how I reposition my portfolio to capitalize on the market reset:

· $NBIS at $92, PT $400 / 1Y
· $RKLB at $43, PT $500 / 5Y
· $CRCL at $72, PT $150 / 8M
· $ALAB at $143.4, PT $250 / 6M
· $SNAP at $8.1, PT $22 / 1Y
· $CIFR at $14.8, PT $28 / 6M
· $RDDT at $185, PT $275 / 8M
· $SMCI at $34, PT $55 / 6M
· $HIMS at $35, PT $60 / 6M

This is in order of concentration weighting from when posted and internal PT speculation based on existing information for mid-cap ($5B+) sections.

Here’s a deeper breakdown on each one and PT timeframe, and a “qualitative”why:

1. Nebius ( $NBIS ): $23B marketcap. Incredibly undervalued and detached from fundamentals.

$7-9B forward ARR, 20-30% EBIT, enterprise contracts from Shopify, Accenture, Cursor, foreign governments and hyperscaler contracts from Meta and Microsoft give Nebius revenue visibility. With $4.8B+ in cash, it's isolated from credit tightening affecting data centers. With 2.5 GW expected capacity contracted 2026, it rivals many others eg. $IREN at 2.8 GW, and defeats many of the capacity/power arguments. With many portfolio companies powering companies like Tesla and Anthropic, it also has higher growth potential (think $MSFT with its portfolio companies for longer defensibility).

We also had stellar $NVDA earnings going into Q4 with their blowout, Jensen clarifying arguments against GPU depreciation, which helps with DC sector sentiment. 

$400 1 year price target, $100B+ valuation given forward revenue/margins.

2. Rocketlab ( $RKLB ): $22B marketcap. Overvalued current term, undervalued long term potential. 

Rocketlab is my highest conviction 5Y long alongside Bitcoin. With Space, it's not winner takes all, and I've maintained $350-500B long term PT to match SpaceX’s most recent valuation/capabilities.

As of now, it's overvalued. But it's an incredible + defensible moat from purely a technological standpoint building reusable rockets and we're early in terms of commercialization of their end-to-end space products at scale (likely ~2028).

However, we're pricing in forward growth with Flatlite commericalization (eg. Starlink), and medium-lift payloads (SpaceX Falcon 9). The market prices in forward growth as well but it’s more about how long in the future with Rocketlab. It's always a solid buy, depending on how patient you are with company execution. 

3. Circle ( $CRCL ) - $16B marketcap, undervalued.

With Circle, I've been bear posting it since it was a $50B marketcap, saying short Circle, long Coinbase, given $COIN has 50% revenue sharing with Circle.

It was overvalued due to float numbers and massive insider lockups 2-3 days after earnings/Dec 2nd led to a sell-off (like $BULL). Float dynamics matter a lot that ETF managers like Cathie Wood seem to not understand (hence my warnings). 

But now we're reaching respectable valuation numbers. I expect USDC commercialization to continue and given a regulatory focus in the digital asset market, I see $CRCL taking over a lot of Tether's marketcap. 

That being said, it's well deserving of a $30B+ marketcap pricing in stablecoin volume growth once we start seeing insider shares redistributed to institutions and long term holders. 

4. Astera Labs ( $ALAB ) - $22B marketcap, reasonable valuation

ALAB was one of my mid-term high conviction picks, due to Mag7 adoption of connectivity for datacenter buildout. 

Incredibly high growth and $NVDA-like margins sitting at ~74%, latest er: $230m/q (101% Y/Y growth). My thesis was that if Mag7 is dependent on a company ($NVDA for GPUs) ( NBIS, IREN, CIFR for DC AI cloud buildout), the company will blow away expections quarter after quarter, and we're seeing this.

There's been a recent sell-off on Astera from $250 back to $140 marks, depsite beating earning expectations across the board and this presents a good buying opportunity.

I maintain a medium term PT $250 for recovery after NVDA earnings and record-high DC buildout from Antrophic's $40B DC to $GOOGL's $50B DC in Texas + connectivity demand.

5. Snapchat ( $SNAP ) $13B marketcap, undervalued. 

$SNAP is one of my least favorite stocks and CEO's (sorry Evan). 

However, I can't argue with fundamental changes. A TLDR of my most recent thesis post was that they're cutting their massive opex bloat from memories/videos stored 10 years ago and if you look into their GCP hosting fees, it's cutting in margins.

Now they're both reducing that OPex cost and increasing revenue from that.  We also have AI deals with perplexity adding $400m+ additional revenue streams like RDDT. 

However, short term it's suffering from tax-harvesting due to underperformance this year relative to AI companies. In 2026 Q1, I expect the market to start pricing in the new fundamentals Hard. and for this company to beat expectation soundly. 

That being said I expect over a 200%+ upside 1Y from here with the market pricing in the new dynamics. 

5. CIFR ( $CIFR ) - Undervalued at $5B marketcap

$CIFR is my second favorite stock in the Neocloud sector. From memory, it holds a lot of Bitcoin on its balance sheet and is materially affected by the selloff in BTC prices from $120k to $90k. 

However I expect crypto asset prices to recover in a few months once cascading margin liqudations finish and instituions buy-in Bitcoin at low prices. 

Nebius is top because it owns the full AI-cloud value chain for higher revenue potential and stronger returns, even though it forces them to handle orchestration, software, and GPU lifecycle risk instead of sticking to colocation.  

However,  $CIFR because it avoids that entire risk surface and has backing from AMZN and GOOGL for long term revenue anchors. It also stays insulated from GPU procurement, management, and depreciation.  

For CIFR's economics we get a a high-margin, annuity structure built on space, power, and cooling for hyperscalers. Risk-adjusted, it’s one of the safest names in the group. But the trade-off is capped upside  Long leases like 10Y, 15Y slow the revenue ramp and mute the payoff relative to full-stack Neocloud operators like NBIS that go from $145m quarterly revenue to $2.1B in a year.

That being said I maintain a $28 PT in 1 month once market prices in $AMZN, $GOOGL Fluidstack revenue and Bitcoin prices recover. 

6. Reddit ( $RDDT ) - Moderate valuation

Coming from the Wendy's dumpsters on WSB subreddit, I am naturally biased toward this platform.

However, the initial sell-off of Reddit at $270 was due to fears over ChatGPT citations, which was immaterial. Now, recent data shows that citations are back, but Reddit's price still sits at $185 (way below that number) + partly due to macro.

Reddit is one of the least bloated, highly profitable social media companies. And it's here to stay due to long term defensibility of the network effect of both younger + older audiences (compared to Snap 900m+ MAU of mostly younger generation).

I expect RDDT to scale up monetization avenues through acquisitions like $HOOD (exchanges) due to their massive FCF and profitability or how Facebook originally acquired WhatsApp, Instagram, built out messenger. It's a low-risk, high growth stock, which is why I maintain a $275 PT in 8 months. 

7. SMCI ( $SMCI ) - Undervalued, $20B marketcap.

$20B marketcap is a joke. Nothing else to say. They're doing $5B quarterly revenue (off lower-margins for sure). However, market is pricing in the company revenue dropping. 

SMCI quoted majority of the backlog delay to Q2 2026, which aligns with a lot of the DC buildout from Neoclouds to Mag7 customers. 

They expect revenue to grow 50%+ Y/Y next year, with at least $36 billion revenue, but judging from DC buildout from blowout NVDA earnings, I expect server rack companies like $DELL and SMCI to outperform Q2  2026. 

This is why I'm taking advantage of revenue lag delays from the current quarter and assigning a $55 PT in 6 months time. 

8. Hims and Her Health ( $HIMS) - Undervalued ( $8B marketcap)

Personally, I've used HIMS just for short term trading breakouts. And I've been one to not long-term hold the stock above $50.  

However, back at $35, it's reset most of the year's growth but grew revenue 49% Y/Y to $500m and is producing a good amount of FCF.

The most under-priced narrative is the Zava acquisition. This adds 1.3M+ users to the HIMS platform and allows the company to expand to the EU market.

Similar to how META acquires companies like Instagram, grows its base + monetizes, I expect HIMS to do the same with Zava + market is pricing in current est. Zava numbers. 

It's probably my least confident stock out of the bunch, especially leaving me with a bad taste with the CEO selling shares after leaving 👀 on SS posts back at $70. 

But that being said it's a great rebound opportunity to $60 in a 6 month timeframe. 

Hope you enjoyed my perspective. There's a lot of x at price posts, but I try to leave a more qualitative breakdown (+ part quantitative but leave out a lot of technical for easier reading) to help retail develop their own conviction and understanding.

Building understanding is important to create internal valuation models yourself rather than blindly following along FinX posters + capitulating when stock prices temporarily drop. 

Happy to discuss more if you drop your own portfolio + concentrations.
```

### [盈利 #16] AMD long hz=event_driven — pub=2025-10-06T22:29:49
- entry=2025-10-07, $214.85
- 1m: **resolved_hit** raw=+19.31% bench=+1.26% excess=+18.04%
- 3m: excess=-7.78%  6m: excess=+12.51%
- **条件 label**: ['PRICE_TARGET']
- **if 句**: ["If you have the patience for shares for a year or two, I'd expect a 50%+ return, just whenever the market wants to price it in", "It's genuinely overvalued even if it's highest conviction 5Y long but at this point it might pull a $PLTR", "all these ten or hundred billion dollar deals if they're valued at 500B lol"]
- **原文 (全文)**:
```
Monday October 6th Market Close Thoughts:

- $NBIS extremely good dip buy. Down 2.38% after rising 5.78% in the morning. All other Neoclouds from $IREN to $CIFR held their 4%-14%+ gains. Nebius likely influenced by option flow, should play catchup soon and I stand by $225 PT. 

- $AMZN, $META two Mag7 that should outperform next 2-3 months and play catchup with the rest. Especially Amazon.

-  $SNAP, $RDDT two good recovery plays. Snapchat especially because of the revenue monetization changes. If you have the patience for shares for a year or two, I'd expect a 50%+ return, just whenever the market wants to price it in. Not everyone has patience and opportunity cost using the funds in $SNAP instead of Neoclouds might not be worth. 

Reddit I've maintained that the citations from ChatGPT is a BS reason for a 29% sell-off so I bought into it.

- $SPRB caught everyone's attention. I do expect it to keep rising to a $150-$200m marketcap from $75m but it's like playing Russian Roulette, usually dilution happens 2-3 days after a major event.

- Stuff like $RKLB, just need to hold lol. It's genuinely overvalued even if it's highest conviction 5Y long but at this point it might pull a $PLTR. 

- $AMD x OpenAI deal heavily bullish for semi industry. I expected $TSM, $ASML, energy stocks and Neoclouds to get a boost from AI infra buildout. Main negative ones were $CRWV, because of $NVDA dependencies and obviously NVDA, but Neoclouds aren't locked into one player, and they already have 5-10+ year contracts locked in.

It just puts a tiny dent in the $NVDA moat idea but nothing material yet. 

I personally think AMD might pull an $ORCL where it dips past rally, and then ends up pulling an $AVGO when markets start pricing in forward revenue. 

Then again, I don't know where OpenAI is getting all this money to promise Oracle, AMD, etc. all these ten or hundred billion dollar deals if they're valued at 500B lol. 

- Gold rallying to ATH every day just signals that $BTC is always a good buy, even at $123k, if it ends up becoming a hedge against inflation. It's close to 1/10th the market-cap. 

- $LTC still a great buy because of ETF approval. There's the government shutdown so people just forgot it hasn't happened yet, but should get approved eventually.

- $VIRT great buy at $32.5, I'd cost average around this range (sorry if you bought calls at $36, my positions are down 35% or so). But again it's an asymmetrical hedge to VIX (VIX IV very high for hedging, VIRT is undervalued ~6.3 forward p/e with buybacks an low IV), so even if positions are down, your other stocks should go up to balance it out. 

- Still looking into other beneficiaries of buildouts from energy stocks, small caps like $EOSE, memory like $MU, etc. that followers recommended. I try not to talk about something much until I'm informed myself.  

- If you're on leverage or going long, now is the time to do it until January. 3x rate cut, market probably frontrunning Oct rate cut now.
```

### [盈利 #17] ALAB long hz=6m — pub=2025-11-20T10:23:51
- entry=2025-11-21, $138.60
- 1m: **resolved_hit** raw=+22.63% bench=+4.76% excess=+17.88%
- 3m: excess=-14.64%  6m: excess=+137.42%
- **条件 label**: ['PRICE_TARGET']
- **if 句**: ["My thesis was that if Mag7 is dependent on a company ($NVDA for GPUs) ( NBIS, IREN, CIFR for DC AI cloud buildout), the company will blow away expections quarter after quarter, and we're seeing this", "A TLDR of my most recent thesis post was that they're cutting their massive opex bloat from memories/videos stored 10 years ago and if you look into their GCP hosting fees, it's cutting in margins", 'Happy to discuss more if you drop your own portfolio + concentrations']
- **原文 (全文)**:
```
Based on the equity ranking table:

Here's a deeper analysis of each stock, alongside how I reposition my portfolio to capitalize on the market reset:

· $NBIS at $92, PT $400 / 1Y
· $RKLB at $43, PT $500 / 5Y
· $CRCL at $72, PT $150 / 8M
· $ALAB at $143.4, PT $250 / 6M
· $SNAP at $8.1, PT $22 / 1Y
· $CIFR at $14.8, PT $28 / 6M
· $RDDT at $185, PT $275 / 8M
· $SMCI at $34, PT $55 / 6M
· $HIMS at $35, PT $60 / 6M

This is in order of concentration weighting from when posted and internal PT speculation based on existing information for mid-cap ($5B+) sections.

Here’s a deeper breakdown on each one and PT timeframe, and a “qualitative”why:

1. Nebius ( $NBIS ): $23B marketcap. Incredibly undervalued and detached from fundamentals.

$7-9B forward ARR, 20-30% EBIT, enterprise contracts from Shopify, Accenture, Cursor, foreign governments and hyperscaler contracts from Meta and Microsoft give Nebius revenue visibility. With $4.8B+ in cash, it's isolated from credit tightening affecting data centers. With 2.5 GW expected capacity contracted 2026, it rivals many others eg. $IREN at 2.8 GW, and defeats many of the capacity/power arguments. With many portfolio companies powering companies like Tesla and Anthropic, it also has higher growth potential (think $MSFT with its portfolio companies for longer defensibility).

We also had stellar $NVDA earnings going into Q4 with their blowout, Jensen clarifying arguments against GPU depreciation, which helps with DC sector sentiment. 

$400 1 year price target, $100B+ valuation given forward revenue/margins.

2. Rocketlab ( $RKLB ): $22B marketcap. Overvalued current term, undervalued long term potential. 

Rocketlab is my highest conviction 5Y long alongside Bitcoin. With Space, it's not winner takes all, and I've maintained $350-500B long term PT to match SpaceX’s most recent valuation/capabilities.

As of now, it's overvalued. But it's an incredible + defensible moat from purely a technological standpoint building reusable rockets and we're early in terms of commercialization of their end-to-end space products at scale (likely ~2028).

However, we're pricing in forward growth with Flatlite commericalization (eg. Starlink), and medium-lift payloads (SpaceX Falcon 9). The market prices in forward growth as well but it’s more about how long in the future with Rocketlab. It's always a solid buy, depending on how patient you are with company execution. 

3. Circle ( $CRCL ) - $16B marketcap, undervalued.

With Circle, I've been bear posting it since it was a $50B marketcap, saying short Circle, long Coinbase, given $COIN has 50% revenue sharing with Circle.

It was overvalued due to float numbers and massive insider lockups 2-3 days after earnings/Dec 2nd led to a sell-off (like $BULL). Float dynamics matter a lot that ETF managers like Cathie Wood seem to not understand (hence my warnings). 

But now we're reaching respectable valuation numbers. I expect USDC commercialization to continue and given a regulatory focus in the digital asset market, I see $CRCL taking over a lot of Tether's marketcap. 

That being said, it's well deserving of a $30B+ marketcap pricing in stablecoin volume growth once we start seeing insider shares redistributed to institutions and long term holders. 

4. Astera Labs ( $ALAB ) - $22B marketcap, reasonable valuation

ALAB was one of my mid-term high conviction picks, due to Mag7 adoption of connectivity for datacenter buildout. 

Incredibly high growth and $NVDA-like margins sitting at ~74%, latest er: $230m/q (101% Y/Y growth). My thesis was that if Mag7 is dependent on a company ($NVDA for GPUs) ( NBIS, IREN, CIFR for DC AI cloud buildout), the company will blow away expections quarter after quarter, and we're seeing this.

There's been a recent sell-off on Astera from $250 back to $140 marks, depsite beating earning expectations across the board and this presents a good buying opportunity.

I maintain a medium term PT $250 for recovery after NVDA earnings and record-high DC buildout from Antrophic's $40B DC to $GOOGL's $50B DC in Texas + connectivity demand.

5. Snapchat ( $SNAP ) $13B marketcap, undervalued. 

$SNAP is one of my least favorite stocks and CEO's (sorry Evan). 

However, I can't argue with fundamental changes. A TLDR of my most recent thesis post was that they're cutting their massive opex bloat from memories/videos stored 10 years ago and if you look into their GCP hosting fees, it's cutting in margins.

Now they're both reducing that OPex cost and increasing revenue from that.  We also have AI deals with perplexity adding $400m+ additional revenue streams like RDDT. 

However, short term it's suffering from tax-harvesting due to underperformance this year relative to AI companies. In 2026 Q1, I expect the market to start pricing in the new fundamentals Hard. and for this company to beat expectation soundly. 

That being said I expect over a 200%+ upside 1Y from here with the market pricing in the new dynamics. 

5. CIFR ( $CIFR ) - Undervalued at $5B marketcap

$CIFR is my second favorite stock in the Neocloud sector. From memory, it holds a lot of Bitcoin on its balance sheet and is materially affected by the selloff in BTC prices from $120k to $90k. 

However I expect crypto asset prices to recover in a few months once cascading margin liqudations finish and instituions buy-in Bitcoin at low prices. 

Nebius is top because it owns the full AI-cloud value chain for higher revenue potential and stronger returns, even though it forces them to handle orchestration, software, and GPU lifecycle risk instead of sticking to colocation.  

However,  $CIFR because it avoids that entire risk surface and has backing from AMZN and GOOGL for long term revenue anchors. It also stays insulated from GPU procurement, management, and depreciation.  

For CIFR's economics we get a a high-margin, annuity structure built on space, power, and cooling for hyperscalers. Risk-adjusted, it’s one of the safest names in the group. But the trade-off is capped upside  Long leases like 10Y, 15Y slow the revenue ramp and mute the payoff relative to full-stack Neocloud operators like NBIS that go from $145m quarterly revenue to $2.1B in a year.

That being said I maintain a $28 PT in 1 month once market prices in $AMZN, $GOOGL Fluidstack revenue and Bitcoin prices recover. 

6. Reddit ( $RDDT ) - Moderate valuation

Coming from the Wendy's dumpsters on WSB subreddit, I am naturally biased toward this platform.

However, the initial sell-off of Reddit at $270 was due to fears over ChatGPT citations, which was immaterial. Now, recent data shows that citations are back, but Reddit's price still sits at $185 (way below that number) + partly due to macro.

Reddit is one of the least bloated, highly profitable social media companies. And it's here to stay due to long term defensibility of the network effect of both younger + older audiences (compared to Snap 900m+ MAU of mostly younger generation).

I expect RDDT to scale up monetization avenues through acquisitions like $HOOD (exchanges) due to their massive FCF and profitability or how Facebook originally acquired WhatsApp, Instagram, built out messenger. It's a low-risk, high growth stock, which is why I maintain a $275 PT in 8 months. 

7. SMCI ( $SMCI ) - Undervalued, $20B marketcap.

$20B marketcap is a joke. Nothing else to say. They're doing $5B quarterly revenue (off lower-margins for sure). However, market is pricing in the company revenue dropping. 

SMCI quoted majority of the backlog delay to Q2 2026, which aligns with a lot of the DC buildout from Neoclouds to Mag7 customers. 

They expect revenue to grow 50%+ Y/Y next year, with at least $36 billion revenue, but judging from DC buildout from blowout NVDA earnings, I expect server rack companies like $DELL and SMCI to outperform Q2  2026. 

This is why I'm taking advantage of revenue lag delays from the current quarter and assigning a $55 PT in 6 months time. 

8. Hims and Her Health ( $HIMS) - Undervalued ( $8B marketcap)

Personally, I've used HIMS just for short term trading breakouts. And I've been one to not long-term hold the stock above $50.  

However, back at $35, it's reset most of the year's growth but grew revenue 49% Y/Y to $500m and is producing a good amount of FCF.

The most under-priced narrative is the Zava acquisition. This adds 1.3M+ users to the HIMS platform and allows the company to expand to the EU market.

Similar to how META acquires companies like Instagram, grows its base + monetizes, I expect HIMS to do the same with Zava + market is pricing in current est. Zava numbers. 

It's probably my least confident stock out of the bunch, especially leaving me with a bad taste with the CEO selling shares after leaving 👀 on SS posts back at $70. 

But that being said it's a great rebound opportunity to $60 in a 6 month timeframe. 

Hope you enjoyed my perspective. There's a lot of x at price posts, but I try to leave a more qualitative breakdown (+ part quantitative but leave out a lot of technical for easier reading) to help retail develop their own conviction and understanding.

Building understanding is important to create internal valuation models yourself rather than blindly following along FinX posters + capitulating when stock prices temporarily drop. 

Happy to discuss more if you drop your own portfolio + concentrations.
```

### [盈利 #18] RDDT long hz=8m — pub=2025-11-20T10:23:51
- entry=2025-11-21, $185.04
- 1m: **resolved_hit** raw=+22.05% bench=+4.76% excess=+17.30%
- 3m: excess=-22.85%  6m: excess=-23.88%
- **条件 label**: ['PRICE_TARGET']
- **if 句**: ["My thesis was that if Mag7 is dependent on a company ($NVDA for GPUs) ( NBIS, IREN, CIFR for DC AI cloud buildout), the company will blow away expections quarter after quarter, and we're seeing this", "A TLDR of my most recent thesis post was that they're cutting their massive opex bloat from memories/videos stored 10 years ago and if you look into their GCP hosting fees, it's cutting in margins", 'Happy to discuss more if you drop your own portfolio + concentrations']
- **原文 (全文)**:
```
Based on the equity ranking table:

Here's a deeper analysis of each stock, alongside how I reposition my portfolio to capitalize on the market reset:

· $NBIS at $92, PT $400 / 1Y
· $RKLB at $43, PT $500 / 5Y
· $CRCL at $72, PT $150 / 8M
· $ALAB at $143.4, PT $250 / 6M
· $SNAP at $8.1, PT $22 / 1Y
· $CIFR at $14.8, PT $28 / 6M
· $RDDT at $185, PT $275 / 8M
· $SMCI at $34, PT $55 / 6M
· $HIMS at $35, PT $60 / 6M

This is in order of concentration weighting from when posted and internal PT speculation based on existing information for mid-cap ($5B+) sections.

Here’s a deeper breakdown on each one and PT timeframe, and a “qualitative”why:

1. Nebius ( $NBIS ): $23B marketcap. Incredibly undervalued and detached from fundamentals.

$7-9B forward ARR, 20-30% EBIT, enterprise contracts from Shopify, Accenture, Cursor, foreign governments and hyperscaler contracts from Meta and Microsoft give Nebius revenue visibility. With $4.8B+ in cash, it's isolated from credit tightening affecting data centers. With 2.5 GW expected capacity contracted 2026, it rivals many others eg. $IREN at 2.8 GW, and defeats many of the capacity/power arguments. With many portfolio companies powering companies like Tesla and Anthropic, it also has higher growth potential (think $MSFT with its portfolio companies for longer defensibility).

We also had stellar $NVDA earnings going into Q4 with their blowout, Jensen clarifying arguments against GPU depreciation, which helps with DC sector sentiment. 

$400 1 year price target, $100B+ valuation given forward revenue/margins.

2. Rocketlab ( $RKLB ): $22B marketcap. Overvalued current term, undervalued long term potential. 

Rocketlab is my highest conviction 5Y long alongside Bitcoin. With Space, it's not winner takes all, and I've maintained $350-500B long term PT to match SpaceX’s most recent valuation/capabilities.

As of now, it's overvalued. But it's an incredible + defensible moat from purely a technological standpoint building reusable rockets and we're early in terms of commercialization of their end-to-end space products at scale (likely ~2028).

However, we're pricing in forward growth with Flatlite commericalization (eg. Starlink), and medium-lift payloads (SpaceX Falcon 9). The market prices in forward growth as well but it’s more about how long in the future with Rocketlab. It's always a solid buy, depending on how patient you are with company execution. 

3. Circle ( $CRCL ) - $16B marketcap, undervalued.

With Circle, I've been bear posting it since it was a $50B marketcap, saying short Circle, long Coinbase, given $COIN has 50% revenue sharing with Circle.

It was overvalued due to float numbers and massive insider lockups 2-3 days after earnings/Dec 2nd led to a sell-off (like $BULL). Float dynamics matter a lot that ETF managers like Cathie Wood seem to not understand (hence my warnings). 

But now we're reaching respectable valuation numbers. I expect USDC commercialization to continue and given a regulatory focus in the digital asset market, I see $CRCL taking over a lot of Tether's marketcap. 

That being said, it's well deserving of a $30B+ marketcap pricing in stablecoin volume growth once we start seeing insider shares redistributed to institutions and long term holders. 

4. Astera Labs ( $ALAB ) - $22B marketcap, reasonable valuation

ALAB was one of my mid-term high conviction picks, due to Mag7 adoption of connectivity for datacenter buildout. 

Incredibly high growth and $NVDA-like margins sitting at ~74%, latest er: $230m/q (101% Y/Y growth). My thesis was that if Mag7 is dependent on a company ($NVDA for GPUs) ( NBIS, IREN, CIFR for DC AI cloud buildout), the company will blow away expections quarter after quarter, and we're seeing this.

There's been a recent sell-off on Astera from $250 back to $140 marks, depsite beating earning expectations across the board and this presents a good buying opportunity.

I maintain a medium term PT $250 for recovery after NVDA earnings and record-high DC buildout from Antrophic's $40B DC to $GOOGL's $50B DC in Texas + connectivity demand.

5. Snapchat ( $SNAP ) $13B marketcap, undervalued. 

$SNAP is one of my least favorite stocks and CEO's (sorry Evan). 

However, I can't argue with fundamental changes. A TLDR of my most recent thesis post was that they're cutting their massive opex bloat from memories/videos stored 10 years ago and if you look into their GCP hosting fees, it's cutting in margins.

Now they're both reducing that OPex cost and increasing revenue from that.  We also have AI deals with perplexity adding $400m+ additional revenue streams like RDDT. 

However, short term it's suffering from tax-harvesting due to underperformance this year relative to AI companies. In 2026 Q1, I expect the market to start pricing in the new fundamentals Hard. and for this company to beat expectation soundly. 

That being said I expect over a 200%+ upside 1Y from here with the market pricing in the new dynamics. 

5. CIFR ( $CIFR ) - Undervalued at $5B marketcap

$CIFR is my second favorite stock in the Neocloud sector. From memory, it holds a lot of Bitcoin on its balance sheet and is materially affected by the selloff in BTC prices from $120k to $90k. 

However I expect crypto asset prices to recover in a few months once cascading margin liqudations finish and instituions buy-in Bitcoin at low prices. 

Nebius is top because it owns the full AI-cloud value chain for higher revenue potential and stronger returns, even though it forces them to handle orchestration, software, and GPU lifecycle risk instead of sticking to colocation.  

However,  $CIFR because it avoids that entire risk surface and has backing from AMZN and GOOGL for long term revenue anchors. It also stays insulated from GPU procurement, management, and depreciation.  

For CIFR's economics we get a a high-margin, annuity structure built on space, power, and cooling for hyperscalers. Risk-adjusted, it’s one of the safest names in the group. But the trade-off is capped upside  Long leases like 10Y, 15Y slow the revenue ramp and mute the payoff relative to full-stack Neocloud operators like NBIS that go from $145m quarterly revenue to $2.1B in a year.

That being said I maintain a $28 PT in 1 month once market prices in $AMZN, $GOOGL Fluidstack revenue and Bitcoin prices recover. 

6. Reddit ( $RDDT ) - Moderate valuation

Coming from the Wendy's dumpsters on WSB subreddit, I am naturally biased toward this platform.

However, the initial sell-off of Reddit at $270 was due to fears over ChatGPT citations, which was immaterial. Now, recent data shows that citations are back, but Reddit's price still sits at $185 (way below that number) + partly due to macro.

Reddit is one of the least bloated, highly profitable social media companies. And it's here to stay due to long term defensibility of the network effect of both younger + older audiences (compared to Snap 900m+ MAU of mostly younger generation).

I expect RDDT to scale up monetization avenues through acquisitions like $HOOD (exchanges) due to their massive FCF and profitability or how Facebook originally acquired WhatsApp, Instagram, built out messenger. It's a low-risk, high growth stock, which is why I maintain a $275 PT in 8 months. 

7. SMCI ( $SMCI ) - Undervalued, $20B marketcap.

$20B marketcap is a joke. Nothing else to say. They're doing $5B quarterly revenue (off lower-margins for sure). However, market is pricing in the company revenue dropping. 

SMCI quoted majority of the backlog delay to Q2 2026, which aligns with a lot of the DC buildout from Neoclouds to Mag7 customers. 

They expect revenue to grow 50%+ Y/Y next year, with at least $36 billion revenue, but judging from DC buildout from blowout NVDA earnings, I expect server rack companies like $DELL and SMCI to outperform Q2  2026. 

This is why I'm taking advantage of revenue lag delays from the current quarter and assigning a $55 PT in 6 months time. 

8. Hims and Her Health ( $HIMS) - Undervalued ( $8B marketcap)

Personally, I've used HIMS just for short term trading breakouts. And I've been one to not long-term hold the stock above $50.  

However, back at $35, it's reset most of the year's growth but grew revenue 49% Y/Y to $500m and is producing a good amount of FCF.

The most under-priced narrative is the Zava acquisition. This adds 1.3M+ users to the HIMS platform and allows the company to expand to the EU market.

Similar to how META acquires companies like Instagram, grows its base + monetizes, I expect HIMS to do the same with Zava + market is pricing in current est. Zava numbers. 

It's probably my least confident stock out of the bunch, especially leaving me with a bad taste with the CEO selling shares after leaving 👀 on SS posts back at $70. 

But that being said it's a great rebound opportunity to $60 in a 6 month timeframe. 

Hope you enjoyed my perspective. There's a lot of x at price posts, but I try to leave a more qualitative breakdown (+ part quantitative but leave out a lot of technical for easier reading) to help retail develop their own conviction and understanding.

Building understanding is important to create internal valuation models yourself rather than blindly following along FinX posters + capitulating when stock prices temporarily drop. 

Happy to discuss more if you drop your own portfolio + concentrations.
```

### [盈利 #19] RKLB long hz=5y — pub=2025-10-02T21:01:45
- entry=2025-10-03, $52.05
- 1m: **resolved_hit** raw=+17.85% bench=+2.11% excess=+15.74%
- 3m: excess=+61.91%  6m: excess=+31.70%
- **条件 label**: ['PRICE_TARGET']
- **原文 (全文)**:
```
@WaggaDoo $225 PT 1 year. I don't have enough info to give predictions outside that timeframe.

For stuff like $RKLB or $IBIT im happy giving 5 year predictions though
```

### [盈利 #20] OKLO short hz=6m — pub=2025-10-04T01:22:20
- entry=2025-10-06, $131.40
- 1m: **resolved_hit** raw=+14.59% bench=+0.54% excess=+14.05%
- 3m: excess=+23.04%  6m: excess=+62.42%
- **条件 label**: ['PRICE_TARGET']
- **if 句**: ["BMNR - Just buy ETH if you believe in it but I wouldn't buy at ETH at $4500"]
- **原文 (全文)**:
```
Friday Market Close, Personal Thoughts and Explanations:

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

Reddit - Dropped 29% off immaterial news that ChatGPT wasn't citing it as much. Nobody visits Reddit through ChatGPT, good recovery buy off $200 support. 

SNAP - Finally they're doing something that's USEFUL for the first time in many years lol. Tons of Capex was spent on storing photos random drawings people saved 12 years ago taking GBs of space for their insane Google Cloud costs. They're finally monetizing it like Apple. Huge tailwind, should improve net income by a ton next year. 

AMZN - Under $220 now, great buy. AMZN prime Oct 8th, good for seasonality in Nov/Dec.

ETOR - I can't believe this is still $41. 33% cash, 1B+ cash pile growing at IBKR rates. Just suffers from tax harvesting I'd assume it goes up next year. 

NBIS - Strong buy until $150+ or new hyperscaler contract repricing. 

LTC - ETF catalyst delayed from Gov shutdown but should be approved anyway. 

Buys

Upwork - Down 4.5% or so for no reason, should recover

MSTR - BTC close to all time highs, MSTR way off ATHs cause of long btc short MSTR but NAV premium should catch up again from the BTC fomo.

ORCL - Standard rise on great forward earnings, drop for short term option chain, then rise because 14B tiktok deal and large future cloud contracts

TGT - Just undervalued great buy under $93, dividend catalyst next month

CIFR - NBIS light with GOOGL deal.

VIRT - VIX doesn't look like it's going down anytime soon but they're trading at like 6.4 or so forward P/E so it's worth.

CRDO - Good buy on correction with hypescaler buildout

WULF - Hasn't gone up as much as the other neoclouds, googl backlog

SOFI - Corrected, might recover back to ATH given macro tailwind

META - Monthly low good DCA, not as good as AMZN

AVGO - Same as ORCL, might end up like NVDA one day with hyperscaler chips

MRVL - Still down 24% YTD. 

SMCI - Good buy on datacenter buildout + server racks

Dell - Good buy on datacenter buildout + server racks

Hold

Nothing changed

Sell

TSLA - Overvalued, better longs like NBIS

CRCL - I will keep making this argument, but just buy COIN instead. You will get the same 50% revenue sharing but with a crypto exchange + ETF holding income too.  

PLTR - Disconnected from reality

BMNR - Just buy ETH if you believe in it but I wouldn't buy at ETH at $4500.

Strong Sell

RGTI - Disconnected from reality lol

All disconnected from reality, wouldn't short though cause all cult stocks. 
OKLO
QBTS
IONQ
```

### [盈利 #21] AXTI long hz=long_term — pub=2026-01-12T10:55:59
- entry=2026-01-13, $22.10
- 1m: **resolved_hit** raw=+12.17% bench=-1.80% excess=+13.97%
- 3m: excess=+183.86%  6m: excess=+0.00%
- **条件 label**: ['PRICE_TARGET']
- **if 句**: ['However, if the "Supply Shock" thesis holds and $AXT becomes a strategic monopoly, the math completely breaks like $MU or Sandisk, and we might see a massive re-rating upward', 'If $AXTI goes to $28 next week, he will likely issue a new note raising it to $32']
- **原文 (全文)**:
```
Just in: Craig-Hallum re-rates $AXTI to "Buy" with a $26 price target, a 160% increase. 

They stated AXT benefits from a "trifecta of dynamics" that put:

- constraints on competitors (Sumitomo, JX) 
- while increasing capacity after Northland's Capital raise.
 
Shannon, ranked as the #1 Semiconductor Analyst on WSJ, pegs AXT at $0.75 EPS by 2028, applying a 30x multiple by assuming AXT is a "normal" growth company. 

Critical defense/AI supply chains (like Heico or specialized chip firms) can easily trade at 50x-60x, which would set $AXTI at a $37.50 PT (for a growth company).

However, if the "Supply Shock" thesis holds and $AXT becomes a strategic monopoly, the math completely breaks like $MU or Sandisk, and we might see a massive re-rating upward. 

This is a "Step-Ladder" valuation, analysts typically walk the target up. If $AXTI goes to $28 next week, he will likely issue a new note raising it to $32.

Institutions are validating the thesis, but are trailing both the price and alpha on X.
```

### [盈利 #22] VSAT long hz=long_term — pub=2026-04-05T04:56:46
- entry=2026-04-06, $52.98
- 1m: **resolved_hit** raw=+23.76% bench=+9.84% excess=+13.92%
- 3m: excess=+0.00%  6m: excess=+0.00%
- **条件 label**: ['EVENT_VERB']
- **if 句**: ['Then if it fails fallback would be names like:', 'Analysis states that if the optical mesh fails due to clouds or lack of stations, the architecture "falls back to Ka-band RF links"', 'But not quite sure if capex is to the scale of hyperscaler AI buildouts yet to benefit these companies enough']
- **原文 (全文)**:
```
The Space Bottleneck: Optical ground infrastructure.

- "The industry has built roughly 10 percent of the optical ground infrastructure"

Now, who are the beneficiaries?

- $EOS.ASX (operating stations at Mt. Stromlo equipped with "adaptive optics.") 
- $SKPJF (TYO: 9412) |  $NTTYY | Space Compass is JV with NTT and satellite operator SKY Perfect JSAT
- $SGBAF - Works with Cailabs to for terrestrial optical terminals
- $SAFRY - Manufacturer of the optical ground stations

Then if it fails fallback would be names like:
$VSAT, $GILT

Analysis states that if the optical mesh fails due to clouds or lack of stations, the architecture "falls back to Ka-band RF links". 
 
-> Near term capital flows to Relay Providers (Kepler, Space Compass, General Atomics). 

-> Long term structural winners will be the photonics hardware manufacturers (Cailabs, Safran).

-> Then companies like SpaceX wins by default. Many are private. 

"This infrastructure deficit is no longer just an engineering problem but a direct threat to a major White House [Golden Dome] policy objective"

Orbital laser communications market are hard-capped until physical ground infra scales, hence the current bottleneck. 

But not quite sure if capex is to the scale of hyperscaler AI buildouts yet to benefit these companies enough.
```

### [盈利 #23] AAOI long hz=long_term — pub=2026-03-04T11:44:02
- entry=2026-03-05, $97.49
- 1m: **resolved_hit** raw=+10.22% bench=-3.28% excess=+13.50%
- 3m: excess=+96.99%  6m: excess=+0.00%
- **条件 label**: ['PRICE_TARGET']
- **原文 (全文)**:
```
$GOOGL rejecting CPO is a massive structural win for the entire pluggable optics ecosystem.  

Most people missed this in the Needham analyst note on the $LITE $850 PT upgrade today:

Large beneficiaries: $AAOI, $FN, Innolight, transceiver companies. 

Secondary beneficiaries (epiwafers): $IQE, Landmark 

Third Order Beneficiaries (substrate): $AXTI, Sumitomo

Downgrade (CPO): Soitec

Quote:  "LITE sees an unexpected bonus that its primary transceiver module customer (Google) currently has no plans to adopt CPO in its TPU architecture from what we have seen."
```

### [盈利 #24] SOFI long hz=6m — pub=2025-10-04T01:22:20
- entry=2025-10-06, $25.77
- 1m: **resolved_hit** raw=+13.97% bench=+0.54% excess=+13.43%
- 3m: excess=+2.10%  6m: excess=-38.10%
- **条件 label**: ['PRICE_TARGET']
- **if 句**: ["BMNR - Just buy ETH if you believe in it but I wouldn't buy at ETH at $4500"]
- **原文 (全文)**:
```
Friday Market Close, Personal Thoughts and Explanations:

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

Reddit - Dropped 29% off immaterial news that ChatGPT wasn't citing it as much. Nobody visits Reddit through ChatGPT, good recovery buy off $200 support. 

SNAP - Finally they're doing something that's USEFUL for the first time in many years lol. Tons of Capex was spent on storing photos random drawings people saved 12 years ago taking GBs of space for their insane Google Cloud costs. They're finally monetizing it like Apple. Huge tailwind, should improve net income by a ton next year. 

AMZN - Under $220 now, great buy. AMZN prime Oct 8th, good for seasonality in Nov/Dec.

ETOR - I can't believe this is still $41. 33% cash, 1B+ cash pile growing at IBKR rates. Just suffers from tax harvesting I'd assume it goes up next year. 

NBIS - Strong buy until $150+ or new hyperscaler contract repricing. 

LTC - ETF catalyst delayed from Gov shutdown but should be approved anyway. 

Buys

Upwork - Down 4.5% or so for no reason, should recover

MSTR - BTC close to all time highs, MSTR way off ATHs cause of long btc short MSTR but NAV premium should catch up again from the BTC fomo.

ORCL - Standard rise on great forward earnings, drop for short term option chain, then rise because 14B tiktok deal and large future cloud contracts

TGT - Just undervalued great buy under $93, dividend catalyst next month

CIFR - NBIS light with GOOGL deal.

VIRT - VIX doesn't look like it's going down anytime soon but they're trading at like 6.4 or so forward P/E so it's worth.

CRDO - Good buy on correction with hypescaler buildout

WULF - Hasn't gone up as much as the other neoclouds, googl backlog

SOFI - Corrected, might recover back to ATH given macro tailwind

META - Monthly low good DCA, not as good as AMZN

AVGO - Same as ORCL, might end up like NVDA one day with hyperscaler chips

MRVL - Still down 24% YTD. 

SMCI - Good buy on datacenter buildout + server racks

Dell - Good buy on datacenter buildout + server racks

Hold

Nothing changed

Sell

TSLA - Overvalued, better longs like NBIS

CRCL - I will keep making this argument, but just buy COIN instead. You will get the same 50% revenue sharing but with a crypto exchange + ETF holding income too.  

PLTR - Disconnected from reality

BMNR - Just buy ETH if you believe in it but I wouldn't buy at ETH at $4500.

Strong Sell

RGTI - Disconnected from reality lol

All disconnected from reality, wouldn't short though cause all cult stocks. 
OKLO
QBTS
IONQ
```

### [盈利 #25] AXTI long hz=long_term — pub=2026-03-04T11:44:02
- entry=2026-03-05, $38.19
- 1m: **resolved_hit** raw=+9.95% bench=-3.28% excess=+13.24%
- 3m: excess=+166.41%  6m: excess=+0.00%
- **条件 label**: ['PRICE_TARGET']
- **原文 (全文)**:
```
$GOOGL rejecting CPO is a massive structural win for the entire pluggable optics ecosystem.  

Most people missed this in the Needham analyst note on the $LITE $850 PT upgrade today:

Large beneficiaries: $AAOI, $FN, Innolight, transceiver companies. 

Secondary beneficiaries (epiwafers): $IQE, Landmark 

Third Order Beneficiaries (substrate): $AXTI, Sumitomo

Downgrade (CPO): Soitec

Quote:  "LITE sees an unexpected bonus that its primary transceiver module customer (Google) currently has no plans to adopt CPO in its TPU architecture from what we have seen."
```

### [盈利 #26] AMZN long hz=6m — pub=2025-10-04T01:22:20
- entry=2025-10-06, $221.00
- 1m: **resolved_hit** raw=+12.81% bench=+0.54% excess=+12.27%
- 3m: excess=+6.63%  6m: excess=+4.49%
- **条件 label**: ['PRICE_TARGET']
- **if 句**: ["BMNR - Just buy ETH if you believe in it but I wouldn't buy at ETH at $4500"]
- **原文 (全文)**:
```
Friday Market Close, Personal Thoughts and Explanations:

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

Reddit - Dropped 29% off immaterial news that ChatGPT wasn't citing it as much. Nobody visits Reddit through ChatGPT, good recovery buy off $200 support. 

SNAP - Finally they're doing something that's USEFUL for the first time in many years lol. Tons of Capex was spent on storing photos random drawings people saved 12 years ago taking GBs of space for their insane Google Cloud costs. They're finally monetizing it like Apple. Huge tailwind, should improve net income by a ton next year. 

AMZN - Under $220 now, great buy. AMZN prime Oct 8th, good for seasonality in Nov/Dec.

ETOR - I can't believe this is still $41. 33% cash, 1B+ cash pile growing at IBKR rates. Just suffers from tax harvesting I'd assume it goes up next year. 

NBIS - Strong buy until $150+ or new hyperscaler contract repricing. 

LTC - ETF catalyst delayed from Gov shutdown but should be approved anyway. 

Buys

Upwork - Down 4.5% or so for no reason, should recover

MSTR - BTC close to all time highs, MSTR way off ATHs cause of long btc short MSTR but NAV premium should catch up again from the BTC fomo.

ORCL - Standard rise on great forward earnings, drop for short term option chain, then rise because 14B tiktok deal and large future cloud contracts

TGT - Just undervalued great buy under $93, dividend catalyst next month

CIFR - NBIS light with GOOGL deal.

VIRT - VIX doesn't look like it's going down anytime soon but they're trading at like 6.4 or so forward P/E so it's worth.

CRDO - Good buy on correction with hypescaler buildout

WULF - Hasn't gone up as much as the other neoclouds, googl backlog

SOFI - Corrected, might recover back to ATH given macro tailwind

META - Monthly low good DCA, not as good as AMZN

AVGO - Same as ORCL, might end up like NVDA one day with hyperscaler chips

MRVL - Still down 24% YTD. 

SMCI - Good buy on datacenter buildout + server racks

Dell - Good buy on datacenter buildout + server racks

Hold

Nothing changed

Sell

TSLA - Overvalued, better longs like NBIS

CRCL - I will keep making this argument, but just buy COIN instead. You will get the same 50% revenue sharing but with a crypto exchange + ETF holding income too.  

PLTR - Disconnected from reality

BMNR - Just buy ETH if you believe in it but I wouldn't buy at ETH at $4500.

Strong Sell

RGTI - Disconnected from reality lol

All disconnected from reality, wouldn't short though cause all cult stocks. 
OKLO
QBTS
IONQ
```

### [盈利 #27] AMZN long hz=3m — pub=2025-10-06T22:29:49
- entry=2025-10-07, $220.88
- 1m: **resolved_hit** raw=+13.27% bench=+1.26% excess=+12.01%
- 3m: excess=+8.46%  6m: excess=+6.38%
- **条件 label**: ['PRICE_TARGET']
- **if 句**: ["If you have the patience for shares for a year or two, I'd expect a 50%+ return, just whenever the market wants to price it in", "It's genuinely overvalued even if it's highest conviction 5Y long but at this point it might pull a $PLTR", "all these ten or hundred billion dollar deals if they're valued at 500B lol"]
- **原文 (全文)**:
```
Monday October 6th Market Close Thoughts:

- $NBIS extremely good dip buy. Down 2.38% after rising 5.78% in the morning. All other Neoclouds from $IREN to $CIFR held their 4%-14%+ gains. Nebius likely influenced by option flow, should play catchup soon and I stand by $225 PT. 

- $AMZN, $META two Mag7 that should outperform next 2-3 months and play catchup with the rest. Especially Amazon.

-  $SNAP, $RDDT two good recovery plays. Snapchat especially because of the revenue monetization changes. If you have the patience for shares for a year or two, I'd expect a 50%+ return, just whenever the market wants to price it in. Not everyone has patience and opportunity cost using the funds in $SNAP instead of Neoclouds might not be worth. 

Reddit I've maintained that the citations from ChatGPT is a BS reason for a 29% sell-off so I bought into it.

- $SPRB caught everyone's attention. I do expect it to keep rising to a $150-$200m marketcap from $75m but it's like playing Russian Roulette, usually dilution happens 2-3 days after a major event.

- Stuff like $RKLB, just need to hold lol. It's genuinely overvalued even if it's highest conviction 5Y long but at this point it might pull a $PLTR. 

- $AMD x OpenAI deal heavily bullish for semi industry. I expected $TSM, $ASML, energy stocks and Neoclouds to get a boost from AI infra buildout. Main negative ones were $CRWV, because of $NVDA dependencies and obviously NVDA, but Neoclouds aren't locked into one player, and they already have 5-10+ year contracts locked in.

It just puts a tiny dent in the $NVDA moat idea but nothing material yet. 

I personally think AMD might pull an $ORCL where it dips past rally, and then ends up pulling an $AVGO when markets start pricing in forward revenue. 

Then again, I don't know where OpenAI is getting all this money to promise Oracle, AMD, etc. all these ten or hundred billion dollar deals if they're valued at 500B lol. 

- Gold rallying to ATH every day just signals that $BTC is always a good buy, even at $123k, if it ends up becoming a hedge against inflation. It's close to 1/10th the market-cap. 

- $LTC still a great buy because of ETF approval. There's the government shutdown so people just forgot it hasn't happened yet, but should get approved eventually.

- $VIRT great buy at $32.5, I'd cost average around this range (sorry if you bought calls at $36, my positions are down 35% or so). But again it's an asymmetrical hedge to VIX (VIX IV very high for hedging, VIRT is undervalued ~6.3 forward p/e with buybacks an low IV), so even if positions are down, your other stocks should go up to balance it out. 

- Still looking into other beneficiaries of buildouts from energy stocks, small caps like $EOSE, memory like $MU, etc. that followers recommended. I try not to talk about something much until I'm informed myself.  

- If you're on leverage or going long, now is the time to do it until January. 3x rate cut, market probably frontrunning Oct rate cut now.
```

### [盈利 #28] MU long hz=long_term — pub=2025-10-19T18:21:35
- entry=2025-10-20, $209.66
- 1m: **resolved_hit** raw=+8.99% bench=-1.67% excess=+10.66%
- 3m: excess=+87.00%  6m: excess=+124.23%
- **条件 label**: ['PRICE_TARGET']
- **if 句**: ['5T marketcap, AMD has a lot to catch up on even if it takes a small percent share', "BMNR - If I don't like Ethereum at these levels, no point of holding treasury companies"]
- **原文 (全文)**:
```
October 20th, Important Rate Cut Trading Week.

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
$ETH
$BMNR
$PL
$BLSKY
$RGTI
$OKLO
$IONQ
$QBTS

_

So macro wise, we are 9 days away from (~97% or so rate cut). Market is in fear mode. This is the ideal time to go long and not cut positions.

Fire Sale
_

$NBIS - Needs no explanation, I still maintain $400 PT on a bull case 2026 due to 4-6B+ forward revenue off ~60-75% gross margins, and another likely hyperscaler contract (eg. $META)

What happened on the 10%+ drop on Friday was mechanical hedging and MM Pinning. You can see this with the price stuck at $113.5, despite any volatility. 

I'd expect short hedges to unwind Monday (given MMs bought puts and were short calls -> heavy short into expiration) and price to go back up. I ended up buying 6 figures worth of calls on the drop as there was no material changes.

Strong Buy

TSM - Holy crap, please have this in your portfolio. This is a money printer, and scaling your revenue by 38-40% every year WHILE increasing gross margins is just insane. It dipped as well after smashing earnings so it's one of the easiest longs in my life.

AMKR - I don't have this in my portfolio yet but will be looking to add due to TSM's involvement in Arizona and potential to be a big partner in the US supply chain (as America tries to push TSM toward US fab + manufacturing).

WLAC - Neocloud SPAC IPO, large upside. I talk about this a lot recently, but it's probably one of the best valued Neoclouds out there, and already has great profit margins (not a pivot from miners, where it's a bit more uncertain). They work with Fluidstack, and I'd expect a 500%+ re-rating on top of a Mag7 contract.

AMZN - $213 is insane lol. I have no clue how this is down -3% YTD during a bull market.

LTC - Affected by crypto liquidations and government shutdown delaying ETFs. Great time to buy and just wait for ETF to be approved.

RDDT - Great dip to $190. I thought $200 would be a bottom but ended up going lower. The news about ChatGPT citing it less caused a large sell-off which I think was very immaterial.

HIMS - 14%+ drop off CEO share sale. Owners sell shares all the time, it doesn't really affect the fundamentals of the company much, just short term sentiment. I'd expect it to rebound.

IBIT - Bitcoin $108k great entry point, it's been swinging between $110k - $120k for awhile so anything under is usually great.

ALAB - I said this last time but it sold off way too much from news of a new competitor. It's already competing vs AVGO in the market lol, NVDA-like margins, growing hundreds of percent Y/Y, Mag7 using them in data center buildout. 

CRDO - Similar thesis to ALAB, sold off alongside Astera but a bit less.

SMCI - Should get re-rated for 55%+ or so revenue growth into next year. I doubted the projections earlier but with the data center growth, it's looking realistic.

FLY - This was a medium lift payload play. People doubt fly's execution but NOC co-developing medium lift takes a lot of risk off the table (and possible re-rating it 500%+ when it competes vs falcon9)

SNAP - Did the math on Snap monetization of memories in an earlier DD post and it's completely not priced in yet. It's doing $1.3B+ quarterly revenue on a $13B market cap lol, and the amount FCF they would get from increasing their revenue + lowering Google OPEX costs is insane.

ETOR  - Majority cash, growing at IBKR rates, suffering from tax harvesting

LULU - Suffering from tax harvesting + competition from Alo, Vuori, etc. But seasonally should be good, and extremely low p/e now.

Buy
AMD - ChatGPT putting in AMD orders, ORCL building out AMD data centers. Likely going to get a re-rating in the next year as a potential $NVDA competitor. Still think Nvidia will dominate but with it's 4.5T marketcap, AMD has a lot to catch up on even if it takes a small percent share.

HOOD - Looking at a lot better after the 10%+ correction. Could pull a PLTR

RBRK - Did DD on this earlier, looks better on the drop as a cybersecurity company really low multiples in the space. Just needs to cut back on marketing, customers sticky. 

UNH - Healthcare is sht in America but not going anywhere. Think Warren and the others know this 

TGT 🐈 - Dividend next moth, big dividend stock. Around now is a good time to load up IMO

IREN 🐈 - Huge GW, expect mag7 or similar deal. 

WYFI - Any neocloud is a buy (eg. see thesis on mag7 funneling revenue down toward these small 1B-5B companies)

WULF - neocloud play

CIFR - neocloud play

SLNH - neocloud play

BITF - neocloud play

GLXY - neocloud derivative play

FLNC - neocloud energy play

MU - China derisked, memory had a huge market there, memory also likely going to get re-rating in tdata center buildout

_

Sell

ETH - Not a fan of Ethereum at $4k+
BMNR - If I don't like Ethereum at these levels, no point of holding treasury companies 
PL - Low revenue, space stock (extremely high valuation)
BLSKY -Low revenue, space stock (extremely high valuation)
RGTI - Quantum bubble
OKLO - Nuclear bubble
IONQ -Quantum bubble 
QBTS - Quantum bubble

_

Quick macro heads up:
-> Rate cut in 9 days ~97% odds. Frontrunning expected, go long.  That's all.
```

### [盈利 #29] NBIS long hz=event_driven — pub=2025-09-25T21:04:48
- entry=2025-09-26, $109.93
- 1m: **resolved_hit** raw=+14.10% bench=+3.54% excess=+10.56%
- 3m: excess=-25.67%  6m: excess=-3.88%
- **条件 label**: ['PRICE_LEVEL', 'EVENT_GENERIC', 'PRICE_DIP']
- **if 句**: ['So daily thoughts on Sept 25th + market drop if you like my insights:', "5% drop (yet), if I like it I'd probably buy overnight", "That's kinda why I said shares into calls if it drops more"]
- **原文 (全文)**:
```
So daily thoughts on Sept 25th + market drop if you like my insights: 

1. 3x rate cut went from 65% to 56% from data today. This is a lot more material, since people are front-running rate cuts now. 

Either way, any rate cut usually lead to large inflows so it's generally bullish for markets months out. 

Powell's thoughts about market being overvalued holds kind of true for certain stocks. Oklo, Quantum, etc. way too overvalued but never short. Even stuff i love like RKLB, really overvalued. 

But there's too much money flowing on sidelines, nothing else to hold other than stocks, real estate, btc, because of all the inflation. Triple rate cut implies they want to keep musical chairs running for another 8 moths. I'd start to worry around Summer next year. 

2. Market droplast two days, I'd use the opportunity to DCA into $Z after 15% drop, AMZN, or $NBIS after 5%.  I still need to research $CIFR so can't really full conviction recommend it after a 17.5% drop (yet), if I like it I'd probably buy overnight. Lot of fun things to swing trade like RKLB on the side. I'm still waiting next month for 6 figures in TGT calls, cause of Nov dividend. 

Everyone's loading AMZN calls now, but like GOOGL it will might drop to levels like $210 -> $200, where people give up then start some stupid rally. That's kinda why I said shares into calls if it drops more. 

3. Lot of tax harvesting taking place. If you have the patience to wait 4 months, lot of undervalued companies like ETOR, TGT, LULU, will likely recover but obviously won't net 600%+ gains unless you do leverage + options. Great time to stock up if you're a patient investor. 

4. I've always maintained you should buy stuff at the lows when market gives up on it (eg. Ethereum $1600), and when there's a new narrative with Bitmine, it's a good time to sell at $4k+. I wouldn't buy the dip even if it drops to $3.5k. I have a whole thesis on this but I'll save this for another day. 

This is only different if it's less speculative like NBIS, like a literal $17B contract flowing into a 25B marketcap company and it's just a matter of execution + waiting. 

Still waiting for LTC, small marketcap, market still pricing in 90% etf approval. There's likely going to be a new BItmine for Litcoin in a few months, and with a small MC can rally quite a bit. 

5. I've never seen a post get more bookmarks than likes other than thirst traps, so you all must like my portfolio weighting!

You've already seen me day trade here: https://t.co/AjTB69Na65 but it's a little annoying for me to do call-outs every time I change positions so I'd prefer to just post general insights + thesis.

6. Market prices in forward revenue, even if you see stuff like NBIS, TSM and stuff dropping today, they're great fundamentally and will likely keep going up.
```

### [盈利 #30] CIFR long hz=6m — pub=2025-11-20T10:23:51
- entry=2025-11-21, $14.20
- 1m: **resolved_hit** raw=+14.23% bench=+4.76% excess=+9.47%
- 3m: excess=+11.46%  6m: excess=+58.67%
- **条件 label**: ['PRICE_TARGET']
- **if 句**: ["My thesis was that if Mag7 is dependent on a company ($NVDA for GPUs) ( NBIS, IREN, CIFR for DC AI cloud buildout), the company will blow away expections quarter after quarter, and we're seeing this", "A TLDR of my most recent thesis post was that they're cutting their massive opex bloat from memories/videos stored 10 years ago and if you look into their GCP hosting fees, it's cutting in margins", 'Happy to discuss more if you drop your own portfolio + concentrations']
- **原文 (全文)**:
```
Based on the equity ranking table:

Here's a deeper analysis of each stock, alongside how I reposition my portfolio to capitalize on the market reset:

· $NBIS at $92, PT $400 / 1Y
· $RKLB at $43, PT $500 / 5Y
· $CRCL at $72, PT $150 / 8M
· $ALAB at $143.4, PT $250 / 6M
· $SNAP at $8.1, PT $22 / 1Y
· $CIFR at $14.8, PT $28 / 6M
· $RDDT at $185, PT $275 / 8M
· $SMCI at $34, PT $55 / 6M
· $HIMS at $35, PT $60 / 6M

This is in order of concentration weighting from when posted and internal PT speculation based on existing information for mid-cap ($5B+) sections.

Here’s a deeper breakdown on each one and PT timeframe, and a “qualitative”why:

1. Nebius ( $NBIS ): $23B marketcap. Incredibly undervalued and detached from fundamentals.

$7-9B forward ARR, 20-30% EBIT, enterprise contracts from Shopify, Accenture, Cursor, foreign governments and hyperscaler contracts from Meta and Microsoft give Nebius revenue visibility. With $4.8B+ in cash, it's isolated from credit tightening affecting data centers. With 2.5 GW expected capacity contracted 2026, it rivals many others eg. $IREN at 2.8 GW, and defeats many of the capacity/power arguments. With many portfolio companies powering companies like Tesla and Anthropic, it also has higher growth potential (think $MSFT with its portfolio companies for longer defensibility).

We also had stellar $NVDA earnings going into Q4 with their blowout, Jensen clarifying arguments against GPU depreciation, which helps with DC sector sentiment. 

$400 1 year price target, $100B+ valuation given forward revenue/margins.

2. Rocketlab ( $RKLB ): $22B marketcap. Overvalued current term, undervalued long term potential. 

Rocketlab is my highest conviction 5Y long alongside Bitcoin. With Space, it's not winner takes all, and I've maintained $350-500B long term PT to match SpaceX’s most recent valuation/capabilities.

As of now, it's overvalued. But it's an incredible + defensible moat from purely a technological standpoint building reusable rockets and we're early in terms of commercialization of their end-to-end space products at scale (likely ~2028).

However, we're pricing in forward growth with Flatlite commericalization (eg. Starlink), and medium-lift payloads (SpaceX Falcon 9). The market prices in forward growth as well but it’s more about how long in the future with Rocketlab. It's always a solid buy, depending on how patient you are with company execution. 

3. Circle ( $CRCL ) - $16B marketcap, undervalued.

With Circle, I've been bear posting it since it was a $50B marketcap, saying short Circle, long Coinbase, given $COIN has 50% revenue sharing with Circle.

It was overvalued due to float numbers and massive insider lockups 2-3 days after earnings/Dec 2nd led to a sell-off (like $BULL). Float dynamics matter a lot that ETF managers like Cathie Wood seem to not understand (hence my warnings). 

But now we're reaching respectable valuation numbers. I expect USDC commercialization to continue and given a regulatory focus in the digital asset market, I see $CRCL taking over a lot of Tether's marketcap. 

That being said, it's well deserving of a $30B+ marketcap pricing in stablecoin volume growth once we start seeing insider shares redistributed to institutions and long term holders. 

4. Astera Labs ( $ALAB ) - $22B marketcap, reasonable valuation

ALAB was one of my mid-term high conviction picks, due to Mag7 adoption of connectivity for datacenter buildout. 

Incredibly high growth and $NVDA-like margins sitting at ~74%, latest er: $230m/q (101% Y/Y growth). My thesis was that if Mag7 is dependent on a company ($NVDA for GPUs) ( NBIS, IREN, CIFR for DC AI cloud buildout), the company will blow away expections quarter after quarter, and we're seeing this.

There's been a recent sell-off on Astera from $250 back to $140 marks, depsite beating earning expectations across the board and this presents a good buying opportunity.

I maintain a medium term PT $250 for recovery after NVDA earnings and record-high DC buildout from Antrophic's $40B DC to $GOOGL's $50B DC in Texas + connectivity demand.

5. Snapchat ( $SNAP ) $13B marketcap, undervalued. 

$SNAP is one of my least favorite stocks and CEO's (sorry Evan). 

However, I can't argue with fundamental changes. A TLDR of my most recent thesis post was that they're cutting their massive opex bloat from memories/videos stored 10 years ago and if you look into their GCP hosting fees, it's cutting in margins.

Now they're both reducing that OPex cost and increasing revenue from that.  We also have AI deals with perplexity adding $400m+ additional revenue streams like RDDT. 

However, short term it's suffering from tax-harvesting due to underperformance this year relative to AI companies. In 2026 Q1, I expect the market to start pricing in the new fundamentals Hard. and for this company to beat expectation soundly. 

That being said I expect over a 200%+ upside 1Y from here with the market pricing in the new dynamics. 

5. CIFR ( $CIFR ) - Undervalued at $5B marketcap

$CIFR is my second favorite stock in the Neocloud sector. From memory, it holds a lot of Bitcoin on its balance sheet and is materially affected by the selloff in BTC prices from $120k to $90k. 

However I expect crypto asset prices to recover in a few months once cascading margin liqudations finish and instituions buy-in Bitcoin at low prices. 

Nebius is top because it owns the full AI-cloud value chain for higher revenue potential and stronger returns, even though it forces them to handle orchestration, software, and GPU lifecycle risk instead of sticking to colocation.  

However,  $CIFR because it avoids that entire risk surface and has backing from AMZN and GOOGL for long term revenue anchors. It also stays insulated from GPU procurement, management, and depreciation.  

For CIFR's economics we get a a high-margin, annuity structure built on space, power, and cooling for hyperscalers. Risk-adjusted, it’s one of the safest names in the group. But the trade-off is capped upside  Long leases like 10Y, 15Y slow the revenue ramp and mute the payoff relative to full-stack Neocloud operators like NBIS that go from $145m quarterly revenue to $2.1B in a year.

That being said I maintain a $28 PT in 1 month once market prices in $AMZN, $GOOGL Fluidstack revenue and Bitcoin prices recover. 

6. Reddit ( $RDDT ) - Moderate valuation

Coming from the Wendy's dumpsters on WSB subreddit, I am naturally biased toward this platform.

However, the initial sell-off of Reddit at $270 was due to fears over ChatGPT citations, which was immaterial. Now, recent data shows that citations are back, but Reddit's price still sits at $185 (way below that number) + partly due to macro.

Reddit is one of the least bloated, highly profitable social media companies. And it's here to stay due to long term defensibility of the network effect of both younger + older audiences (compared to Snap 900m+ MAU of mostly younger generation).

I expect RDDT to scale up monetization avenues through acquisitions like $HOOD (exchanges) due to their massive FCF and profitability or how Facebook originally acquired WhatsApp, Instagram, built out messenger. It's a low-risk, high growth stock, which is why I maintain a $275 PT in 8 months. 

7. SMCI ( $SMCI ) - Undervalued, $20B marketcap.

$20B marketcap is a joke. Nothing else to say. They're doing $5B quarterly revenue (off lower-margins for sure). However, market is pricing in the company revenue dropping. 

SMCI quoted majority of the backlog delay to Q2 2026, which aligns with a lot of the DC buildout from Neoclouds to Mag7 customers. 

They expect revenue to grow 50%+ Y/Y next year, with at least $36 billion revenue, but judging from DC buildout from blowout NVDA earnings, I expect server rack companies like $DELL and SMCI to outperform Q2  2026. 

This is why I'm taking advantage of revenue lag delays from the current quarter and assigning a $55 PT in 6 months time. 

8. Hims and Her Health ( $HIMS) - Undervalued ( $8B marketcap)

Personally, I've used HIMS just for short term trading breakouts. And I've been one to not long-term hold the stock above $50.  

However, back at $35, it's reset most of the year's growth but grew revenue 49% Y/Y to $500m and is producing a good amount of FCF.

The most under-priced narrative is the Zava acquisition. This adds 1.3M+ users to the HIMS platform and allows the company to expand to the EU market.

Similar to how META acquires companies like Instagram, grows its base + monetizes, I expect HIMS to do the same with Zava + market is pricing in current est. Zava numbers. 

It's probably my least confident stock out of the bunch, especially leaving me with a bad taste with the CEO selling shares after leaving 👀 on SS posts back at $70. 

But that being said it's a great rebound opportunity to $60 in a 6 month timeframe. 

Hope you enjoyed my perspective. There's a lot of x at price posts, but I try to leave a more qualitative breakdown (+ part quantitative but leave out a lot of technical for easier reading) to help retail develop their own conviction and understanding.

Building understanding is important to create internal valuation models yourself rather than blindly following along FinX posters + capitulating when stock prices temporarily drop. 

Happy to discuss more if you drop your own portfolio + concentrations.
```

### [盈利 #31] NBIS long hz=short_term — pub=2025-09-30T19:09:16
- entry=2025-10-01, $111.72
- 1m: **resolved_hit** raw=+11.16% bench=+1.70% excess=+9.46%
- 3m: excess=-21.68%  6m: excess=+2.16%
- **条件 label**: ['PRICE_TARGET']
- **if 句**: ["So I'd use this time to DCA and buy calls/shares even if it's up 1", "If you wanted to build a long term position I'd buy at this level", "If it drops past $273, I'd just DCA and then if it drops further switch to calls"]
- **原文 (全文)**:
```
Lot of inspirational trader mindsets going around X lately like:
 
"It will pay off. Be Patient". All BS. 

Traders consider sector momentum, catalysts, valuation, pullbacks, macro, IV, option flows, etc. 

Here's my mindset for short term trading for various stocks: 

1. $NBIS - $111.91, even though it's up 1.53% on the day, CRWV is up 12% off Meta gives them a $14B contract.

So usually it's bullish for all neoclouds. It spiked to $117 ( i probably would have still held) but pulled back to $111 likely from too much open interest, but we'll likely keep seeing a rally upward. So I'd use this time to DCA and buy calls/shares even if it's up 1.53%

Not "truly a dip" but it's more of a dip during a rally. 

2. $HIMS - $56.4 Down 4.67%, usually people just blindly buy the dip but this was actually caused from something material, which was Trump launching a direct to consumer GOV drug website. Short interest decreased back to 33% on the rise to $60. 

This dip will likely be used for short covering. I did buy $46 support but sold shortly on a bounce after I just felt like it would go down more. But I just personally prefer bottom entry points so that's probably closer to $50. 

I still remember AMZN launching a competitor, HIMS crashed 20% then rose again, I'd expect the same with Trump's program mid term but near term it's a headwind. 

3. $RDDT - $228, down 5.45%, no news. Just probably valuation concerns. We saw similar growth stocks like ALAB, CRED, have random 20% pullbacks. Lot of software/social stocks like SNAP down 8.1% off non-material news. Correction is healthy, stocks don't just keep going up, I'd prefer to wait in the $100+ again, rather than $200+ (just personally), but it's actually a better buy than the rest, given RDDT has larger 5-8% pullbacks on random days, just from historical experiences so 6-7% drop is a good buy intra-day and you'd likely see it recover but we might see a lot of growth stocks have a larger correction into massive rally Nov/Dec so might not be an actual bottom. 

I don't really look at chart RSI nowadays, just do this based on feelings from experience looking at the stock + IV every day for the past year or two. 

4. AMZN - No major macro news, prob government shutdown Oct 1st that might cause some panic for index but it's pretty immaterial. It dropped, 1.35% so I'd buy since it' a good time to cost average. 

5. Klarna - $36, 5.3% drop. Sometimes you just go off gut feeling. Below IPO price, no major news. Most IPOs were down like Gemini, etc. If you wanted to build a long term position I'd buy at this level. 

6. TSM - $277, I've been guilty of swing trading between $273-$279, so I just buy every drop to $273 and sell at $277-$279 for 2% profit purely with shares. So far I've done this ~2 times with shares. If it drops past $273, I'd just DCA and then if it drops further switch to calls. 

There's no True or False way to do this, everyone kind of has their own approach. (also sorry about CRM, bad earnings got that one wrong, I'll probably cost avg if ti declines further). 

But generally this is just what I'm thinking about when I go down the list of every single stock. Once again, everyone thinks differently, I just wanted to write down how I think if it's helpful to others.
```

### [盈利 #32] SGBAF long hz=long_term — pub=2026-04-05T04:56:46
- entry=2026-04-08, $7.35
- 1m: **resolved_hit** raw=+19.05% bench=+9.84% excess=+9.21%
- 3m: excess=+0.00%  6m: excess=+0.00%
- **条件 label**: ['EVENT_VERB']
- **if 句**: ['Then if it fails fallback would be names like:', 'Analysis states that if the optical mesh fails due to clouds or lack of stations, the architecture "falls back to Ka-band RF links"', 'But not quite sure if capex is to the scale of hyperscaler AI buildouts yet to benefit these companies enough']
- **原文 (全文)**:
```
The Space Bottleneck: Optical ground infrastructure.

- "The industry has built roughly 10 percent of the optical ground infrastructure"

Now, who are the beneficiaries?

- $EOS.ASX (operating stations at Mt. Stromlo equipped with "adaptive optics.") 
- $SKPJF (TYO: 9412) |  $NTTYY | Space Compass is JV with NTT and satellite operator SKY Perfect JSAT
- $SGBAF - Works with Cailabs to for terrestrial optical terminals
- $SAFRY - Manufacturer of the optical ground stations

Then if it fails fallback would be names like:
$VSAT, $GILT

Analysis states that if the optical mesh fails due to clouds or lack of stations, the architecture "falls back to Ka-band RF links". 
 
-> Near term capital flows to Relay Providers (Kepler, Space Compass, General Atomics). 

-> Long term structural winners will be the photonics hardware manufacturers (Cailabs, Safran).

-> Then companies like SpaceX wins by default. Many are private. 

"This infrastructure deficit is no longer just an engineering problem but a direct threat to a major White House [Golden Dome] policy objective"

Orbital laser communications market are hard-capped until physical ground infra scales, hence the current bottleneck. 

But not quite sure if capex is to the scale of hyperscaler AI buildouts yet to benefit these companies enough.
```

### [盈利 #33] TGT long hz=1m — pub=2025-09-25T21:04:48
- entry=2025-09-26, $86.84
- 1m: **resolved_hit** raw=+12.59% bench=+3.54% excess=+9.05%
- 3m: excess=+9.03%  6m: excess=+41.30%
- **条件 label**: ['PRICE_LEVEL', 'EVENT_GENERIC', 'PRICE_DIP']
- **if 句**: ['So daily thoughts on Sept 25th + market drop if you like my insights:', "5% drop (yet), if I like it I'd probably buy overnight", "That's kinda why I said shares into calls if it drops more"]
- **原文 (全文)**:
```
So daily thoughts on Sept 25th + market drop if you like my insights: 

1. 3x rate cut went from 65% to 56% from data today. This is a lot more material, since people are front-running rate cuts now. 

Either way, any rate cut usually lead to large inflows so it's generally bullish for markets months out. 

Powell's thoughts about market being overvalued holds kind of true for certain stocks. Oklo, Quantum, etc. way too overvalued but never short. Even stuff i love like RKLB, really overvalued. 

But there's too much money flowing on sidelines, nothing else to hold other than stocks, real estate, btc, because of all the inflation. Triple rate cut implies they want to keep musical chairs running for another 8 moths. I'd start to worry around Summer next year. 

2. Market droplast two days, I'd use the opportunity to DCA into $Z after 15% drop, AMZN, or $NBIS after 5%.  I still need to research $CIFR so can't really full conviction recommend it after a 17.5% drop (yet), if I like it I'd probably buy overnight. Lot of fun things to swing trade like RKLB on the side. I'm still waiting next month for 6 figures in TGT calls, cause of Nov dividend. 

Everyone's loading AMZN calls now, but like GOOGL it will might drop to levels like $210 -> $200, where people give up then start some stupid rally. That's kinda why I said shares into calls if it drops more. 

3. Lot of tax harvesting taking place. If you have the patience to wait 4 months, lot of undervalued companies like ETOR, TGT, LULU, will likely recover but obviously won't net 600%+ gains unless you do leverage + options. Great time to stock up if you're a patient investor. 

4. I've always maintained you should buy stuff at the lows when market gives up on it (eg. Ethereum $1600), and when there's a new narrative with Bitmine, it's a good time to sell at $4k+. I wouldn't buy the dip even if it drops to $3.5k. I have a whole thesis on this but I'll save this for another day. 

This is only different if it's less speculative like NBIS, like a literal $17B contract flowing into a 25B marketcap company and it's just a matter of execution + waiting. 

Still waiting for LTC, small marketcap, market still pricing in 90% etf approval. There's likely going to be a new BItmine for Litcoin in a few months, and with a small MC can rally quite a bit. 

5. I've never seen a post get more bookmarks than likes other than thirst traps, so you all must like my portfolio weighting!

You've already seen me day trade here: https://t.co/AjTB69Na65 but it's a little annoying for me to do call-outs every time I change positions so I'd prefer to just post general insights + thesis.

6. Market prices in forward revenue, even if you see stuff like NBIS, TSM and stuff dropping today, they're great fundamentally and will likely keep going up.
```

### [盈利 #34] RGTI short hz=6m — pub=2025-10-04T01:22:20
- entry=2025-10-06, $38.80
- 1m: **resolved_hit** raw=+9.34% bench=+0.54% excess=+8.80%
- 3m: excess=+32.36%  6m: excess=+61.89%
- **条件 label**: ['PRICE_TARGET']
- **if 句**: ["BMNR - Just buy ETH if you believe in it but I wouldn't buy at ETH at $4500"]
- **原文 (全文)**:
```
Friday Market Close, Personal Thoughts and Explanations:

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

Reddit - Dropped 29% off immaterial news that ChatGPT wasn't citing it as much. Nobody visits Reddit through ChatGPT, good recovery buy off $200 support. 

SNAP - Finally they're doing something that's USEFUL for the first time in many years lol. Tons of Capex was spent on storing photos random drawings people saved 12 years ago taking GBs of space for their insane Google Cloud costs. They're finally monetizing it like Apple. Huge tailwind, should improve net income by a ton next year. 

AMZN - Under $220 now, great buy. AMZN prime Oct 8th, good for seasonality in Nov/Dec.

ETOR - I can't believe this is still $41. 33% cash, 1B+ cash pile growing at IBKR rates. Just suffers from tax harvesting I'd assume it goes up next year. 

NBIS - Strong buy until $150+ or new hyperscaler contract repricing. 

LTC - ETF catalyst delayed from Gov shutdown but should be approved anyway. 

Buys

Upwork - Down 4.5% or so for no reason, should recover

MSTR - BTC close to all time highs, MSTR way off ATHs cause of long btc short MSTR but NAV premium should catch up again from the BTC fomo.

ORCL - Standard rise on great forward earnings, drop for short term option chain, then rise because 14B tiktok deal and large future cloud contracts

TGT - Just undervalued great buy under $93, dividend catalyst next month

CIFR - NBIS light with GOOGL deal.

VIRT - VIX doesn't look like it's going down anytime soon but they're trading at like 6.4 or so forward P/E so it's worth.

CRDO - Good buy on correction with hypescaler buildout

WULF - Hasn't gone up as much as the other neoclouds, googl backlog

SOFI - Corrected, might recover back to ATH given macro tailwind

META - Monthly low good DCA, not as good as AMZN

AVGO - Same as ORCL, might end up like NVDA one day with hyperscaler chips

MRVL - Still down 24% YTD. 

SMCI - Good buy on datacenter buildout + server racks

Dell - Good buy on datacenter buildout + server racks

Hold

Nothing changed

Sell

TSLA - Overvalued, better longs like NBIS

CRCL - I will keep making this argument, but just buy COIN instead. You will get the same 50% revenue sharing but with a crypto exchange + ETF holding income too.  

PLTR - Disconnected from reality

BMNR - Just buy ETH if you believe in it but I wouldn't buy at ETH at $4500.

Strong Sell

RGTI - Disconnected from reality lol

All disconnected from reality, wouldn't short though cause all cult stocks. 
OKLO
QBTS
IONQ
```

### [盈利 #35] AMZN long hz=event_driven — pub=2025-10-01T23:39:48
- entry=2025-10-02, $221.01
- 1m: **resolved_hit** raw=+10.50% bench=+1.92% excess=+8.58%
- 3m: excess=+2.69%  6m: excess=-1.78%
- **条件 label**: ['PRICE_TARGET']
- **if 句**: ["You can do it with stuff like Rocketlab since long term if you hold enough, even if it dips past $40 it will likely recover since it's a strong buy fundamentally albeit a tiny overvalued now", 'If it ever dips past $210, you can do leaps', 'These lines mean nothing if forward revenue falls a lot or industry margins compresses']
- **原文 (全文)**:
```
How I do swing trading with charts, Part 2:  Short term (few week) + Short-Medium Term (few month). 

I'll do long term ones in another post.   

Ex 1: $RKLB. Just going off feels on this, seems like a great buy at $40 support, and $54 sell. Usually lower half (dotted line) like $44 is a good buy too cause risk-reward is good but u wont get the actual bottom.  

You can do it with stuff like Rocketlab since long term if you hold enough, even if it dips past $40 it will likely recover since it's a strong buy fundamentally albeit a tiny overvalued now.   

Example 2: $AMZN - Great buy with shares now. If it ever dips past $210, you can do leaps. Lower than $200 for example, shorter dated calls.   

_ 

Knowing fundamentals, macro, and whether catalysts are material or not is really also important. These lines mean nothing if forward revenue falls a lot or industry margins compresses.   

Lot of time they drop on more irrational things eg. GOOGL with Apple search, or maybe overall market SPY dipping but in those cases they usually rise up again if there's no difference + company keeps growing.   Again different for everyone, you need to analyze more than the charts when timing bottoms. This is just part of what I do.
```

### [盈利 #36] SNAP long hz=long_term — pub=2025-10-19T18:21:35
- entry=2025-10-20, $7.73
- 1m: **resolved_hit** raw=+6.73% bench=-1.67% excess=+8.40%
- 3m: excess=-3.54%  6m: excess=-33.48%
- **条件 label**: ['PRICE_TARGET']
- **if 句**: ['5T marketcap, AMD has a lot to catch up on even if it takes a small percent share', "BMNR - If I don't like Ethereum at these levels, no point of holding treasury companies"]
- **原文 (全文)**:
```
October 20th, Important Rate Cut Trading Week.

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
$ETH
$BMNR
$PL
$BLSKY
$RGTI
$OKLO
$IONQ
$QBTS

_

So macro wise, we are 9 days away from (~97% or so rate cut). Market is in fear mode. This is the ideal time to go long and not cut positions.

Fire Sale
_

$NBIS - Needs no explanation, I still maintain $400 PT on a bull case 2026 due to 4-6B+ forward revenue off ~60-75% gross margins, and another likely hyperscaler contract (eg. $META)

What happened on the 10%+ drop on Friday was mechanical hedging and MM Pinning. You can see this with the price stuck at $113.5, despite any volatility. 

I'd expect short hedges to unwind Monday (given MMs bought puts and were short calls -> heavy short into expiration) and price to go back up. I ended up buying 6 figures worth of calls on the drop as there was no material changes.

Strong Buy

TSM - Holy crap, please have this in your portfolio. This is a money printer, and scaling your revenue by 38-40% every year WHILE increasing gross margins is just insane. It dipped as well after smashing earnings so it's one of the easiest longs in my life.

AMKR - I don't have this in my portfolio yet but will be looking to add due to TSM's involvement in Arizona and potential to be a big partner in the US supply chain (as America tries to push TSM toward US fab + manufacturing).

WLAC - Neocloud SPAC IPO, large upside. I talk about this a lot recently, but it's probably one of the best valued Neoclouds out there, and already has great profit margins (not a pivot from miners, where it's a bit more uncertain). They work with Fluidstack, and I'd expect a 500%+ re-rating on top of a Mag7 contract.

AMZN - $213 is insane lol. I have no clue how this is down -3% YTD during a bull market.

LTC - Affected by crypto liquidations and government shutdown delaying ETFs. Great time to buy and just wait for ETF to be approved.

RDDT - Great dip to $190. I thought $200 would be a bottom but ended up going lower. The news about ChatGPT citing it less caused a large sell-off which I think was very immaterial.

HIMS - 14%+ drop off CEO share sale. Owners sell shares all the time, it doesn't really affect the fundamentals of the company much, just short term sentiment. I'd expect it to rebound.

IBIT - Bitcoin $108k great entry point, it's been swinging between $110k - $120k for awhile so anything under is usually great.

ALAB - I said this last time but it sold off way too much from news of a new competitor. It's already competing vs AVGO in the market lol, NVDA-like margins, growing hundreds of percent Y/Y, Mag7 using them in data center buildout. 

CRDO - Similar thesis to ALAB, sold off alongside Astera but a bit less.

SMCI - Should get re-rated for 55%+ or so revenue growth into next year. I doubted the projections earlier but with the data center growth, it's looking realistic.

FLY - This was a medium lift payload play. People doubt fly's execution but NOC co-developing medium lift takes a lot of risk off the table (and possible re-rating it 500%+ when it competes vs falcon9)

SNAP - Did the math on Snap monetization of memories in an earlier DD post and it's completely not priced in yet. It's doing $1.3B+ quarterly revenue on a $13B market cap lol, and the amount FCF they would get from increasing their revenue + lowering Google OPEX costs is insane.

ETOR  - Majority cash, growing at IBKR rates, suffering from tax harvesting

LULU - Suffering from tax harvesting + competition from Alo, Vuori, etc. But seasonally should be good, and extremely low p/e now.

Buy
AMD - ChatGPT putting in AMD orders, ORCL building out AMD data centers. Likely going to get a re-rating in the next year as a potential $NVDA competitor. Still think Nvidia will dominate but with it's 4.5T marketcap, AMD has a lot to catch up on even if it takes a small percent share.

HOOD - Looking at a lot better after the 10%+ correction. Could pull a PLTR

RBRK - Did DD on this earlier, looks better on the drop as a cybersecurity company really low multiples in the space. Just needs to cut back on marketing, customers sticky. 

UNH - Healthcare is sht in America but not going anywhere. Think Warren and the others know this 

TGT 🐈 - Dividend next moth, big dividend stock. Around now is a good time to load up IMO

IREN 🐈 - Huge GW, expect mag7 or similar deal. 

WYFI - Any neocloud is a buy (eg. see thesis on mag7 funneling revenue down toward these small 1B-5B companies)

WULF - neocloud play

CIFR - neocloud play

SLNH - neocloud play

BITF - neocloud play

GLXY - neocloud derivative play

FLNC - neocloud energy play

MU - China derisked, memory had a huge market there, memory also likely going to get re-rating in tdata center buildout

_

Sell

ETH - Not a fan of Ethereum at $4k+
BMNR - If I don't like Ethereum at these levels, no point of holding treasury companies 
PL - Low revenue, space stock (extremely high valuation)
BLSKY -Low revenue, space stock (extremely high valuation)
RGTI - Quantum bubble
OKLO - Nuclear bubble
IONQ -Quantum bubble 
QBTS - Quantum bubble

_

Quick macro heads up:
-> Rate cut in 9 days ~97% odds. Frontrunning expected, go long.  That's all.
```

### [盈利 #37] GILT long hz=long_term — pub=2026-04-05T04:56:46
- entry=2026-04-06, $17.02
- 1m: **resolved_hit** raw=+17.92% bench=+9.84% excess=+8.08%
- 3m: excess=+0.00%  6m: excess=+0.00%
- **条件 label**: ['EVENT_VERB']
- **if 句**: ['Then if it fails fallback would be names like:', 'Analysis states that if the optical mesh fails due to clouds or lack of stations, the architecture "falls back to Ka-band RF links"', 'But not quite sure if capex is to the scale of hyperscaler AI buildouts yet to benefit these companies enough']
- **原文 (全文)**:
```
The Space Bottleneck: Optical ground infrastructure.

- "The industry has built roughly 10 percent of the optical ground infrastructure"

Now, who are the beneficiaries?

- $EOS.ASX (operating stations at Mt. Stromlo equipped with "adaptive optics.") 
- $SKPJF (TYO: 9412) |  $NTTYY | Space Compass is JV with NTT and satellite operator SKY Perfect JSAT
- $SGBAF - Works with Cailabs to for terrestrial optical terminals
- $SAFRY - Manufacturer of the optical ground stations

Then if it fails fallback would be names like:
$VSAT, $GILT

Analysis states that if the optical mesh fails due to clouds or lack of stations, the architecture "falls back to Ka-band RF links". 
 
-> Near term capital flows to Relay Providers (Kepler, Space Compass, General Atomics). 

-> Long term structural winners will be the photonics hardware manufacturers (Cailabs, Safran).

-> Then companies like SpaceX wins by default. Many are private. 

"This infrastructure deficit is no longer just an engineering problem but a direct threat to a major White House [Golden Dome] policy objective"

Orbital laser communications market are hard-capped until physical ground infra scales, hence the current bottleneck. 

But not quite sure if capex is to the scale of hyperscaler AI buildouts yet to benefit these companies enough.
```

### [盈利 #38] TSM long hz=short_term — pub=2025-09-30T19:09:16
- entry=2025-10-01, $278.44
- 1m: **resolved_hit** raw=+8.90% bench=+1.70% excess=+7.20%
- 3m: excess=+12.59%  6m: excess=+24.17%
- **条件 label**: ['PRICE_TARGET']
- **if 句**: ["So I'd use this time to DCA and buy calls/shares even if it's up 1", "If you wanted to build a long term position I'd buy at this level", "If it drops past $273, I'd just DCA and then if it drops further switch to calls"]
- **原文 (全文)**:
```
Lot of inspirational trader mindsets going around X lately like:
 
"It will pay off. Be Patient". All BS. 

Traders consider sector momentum, catalysts, valuation, pullbacks, macro, IV, option flows, etc. 

Here's my mindset for short term trading for various stocks: 

1. $NBIS - $111.91, even though it's up 1.53% on the day, CRWV is up 12% off Meta gives them a $14B contract.

So usually it's bullish for all neoclouds. It spiked to $117 ( i probably would have still held) but pulled back to $111 likely from too much open interest, but we'll likely keep seeing a rally upward. So I'd use this time to DCA and buy calls/shares even if it's up 1.53%

Not "truly a dip" but it's more of a dip during a rally. 

2. $HIMS - $56.4 Down 4.67%, usually people just blindly buy the dip but this was actually caused from something material, which was Trump launching a direct to consumer GOV drug website. Short interest decreased back to 33% on the rise to $60. 

This dip will likely be used for short covering. I did buy $46 support but sold shortly on a bounce after I just felt like it would go down more. But I just personally prefer bottom entry points so that's probably closer to $50. 

I still remember AMZN launching a competitor, HIMS crashed 20% then rose again, I'd expect the same with Trump's program mid term but near term it's a headwind. 

3. $RDDT - $228, down 5.45%, no news. Just probably valuation concerns. We saw similar growth stocks like ALAB, CRED, have random 20% pullbacks. Lot of software/social stocks like SNAP down 8.1% off non-material news. Correction is healthy, stocks don't just keep going up, I'd prefer to wait in the $100+ again, rather than $200+ (just personally), but it's actually a better buy than the rest, given RDDT has larger 5-8% pullbacks on random days, just from historical experiences so 6-7% drop is a good buy intra-day and you'd likely see it recover but we might see a lot of growth stocks have a larger correction into massive rally Nov/Dec so might not be an actual bottom. 

I don't really look at chart RSI nowadays, just do this based on feelings from experience looking at the stock + IV every day for the past year or two. 

4. AMZN - No major macro news, prob government shutdown Oct 1st that might cause some panic for index but it's pretty immaterial. It dropped, 1.35% so I'd buy since it' a good time to cost average. 

5. Klarna - $36, 5.3% drop. Sometimes you just go off gut feeling. Below IPO price, no major news. Most IPOs were down like Gemini, etc. If you wanted to build a long term position I'd buy at this level. 

6. TSM - $277, I've been guilty of swing trading between $273-$279, so I just buy every drop to $273 and sell at $277-$279 for 2% profit purely with shares. So far I've done this ~2 times with shares. If it drops past $273, I'd just DCA and then if it drops further switch to calls. 

There's no True or False way to do this, everyone kind of has their own approach. (also sorry about CRM, bad earnings got that one wrong, I'll probably cost avg if ti declines further). 

But generally this is just what I'm thinking about when I go down the list of every single stock. Once again, everyone thinks differently, I just wanted to write down how I think if it's helpful to others.
```

### [盈利 #39] AMZN long hz=6m — pub=2025-10-15T07:42:21
- entry=2025-10-16, $215.67
- 1m: **resolved_hit** raw=+8.82% bench=+1.71% excess=+7.11%
- 3m: excess=+4.54%  6m: excess=+9.30%
- **条件 label**: ['PRICE_TARGET']
- **if 句**: ['This would be a $3T company if this were a US company, insane profit margins, insane growth rate for their size', '5T), even if buying at ATHs', "AMZN hitting $213-215 today was a good chance to stock up since it usually floats between $218-$227 if you're short term swing trading but long term I'd expect it to catchup to other mag7"]
- **原文 (全文)**:
```
The Great Soybean/Seed Oil Crash, personal thoughts and explanations:

Strong Buy
$ALAB
$CRDO
$NBIS
$WLAC
$LTC
$TSM
$BTC
(+ same as tax harvest stocks last time)
$AMZN
$SMCI
_

Buy
$AMD
$FLNC
$SEI
$BZAI
$NKLR
$IREN
$WULF
$CIFR
$CRWV
$BITF
$WYFI
$SLNH
$BITF
$RBRK
$GLXY
$GRAB
$SEA
$META
$TGT
$SNAP
$MU
$RKLB
$FLY
$UNH

Hold
$MP
$HOOD
$EOSE
$NVDA
$GOOGL
$DFLI
$SOFI
$VIRT
$RR
$AVGO
$BE
$ASTS

(Hit the ticker maximum but everything else from last post, still sell on Quantum or Oklo)
_

Strong Buys
ALAB - Huge part of datacenter buildout, NVDA like margins, Mag7 customers. Already had competitors from AVGO,  really don't think Arista would be a competitive threat.

CRDO - Same sell-off as ALAB, thought they were both kind of overvalued before, but now they're back in correction territory so good to stock up.

NBIS - $400 PT bull case. We have macro tailwind from government re-opening + rate cut EOM october into earnings, so short term looks promising. Lot of things going for it (eg. meta x crwv, so there's potential for more mag7 clients), sum of parts doing well, eg. clickhouse, and scaling rev from $100m to $1.5B+ a quarter is insane. there's already contracts locked in its just a matter of company execution.

WLAC - Wrote a thesis about this earlier at $13. Even at $14.5 strong because it can re-rate 100%+ easily.

LTC - Affected by leverage traders and government shutdown. The shutdown is predicted to last awhile and the main reason to buy was the ETF getting approved. But a great buy sub <$100 anyway, because it will get approved in due time (~95% chance).

TSM - Holy crap. This would be a $3T company if this were a US company, insane profit margins, insane growth rate for their size. And every post you see about OpenAi X (**sydney sweeney partnership) or AMD buildout/NVDA buildout. TSM is the center of it all and would easily be a $2T+ company (from here at ~$1.5T), even if buying at ATHs.

BTC - $112K good entry point. Goldt keeps hitting ATH, nothing really changed fundamentally, just lot of liquidations recently
(+ same as tax harvest stocks last time)

AMZN - I really don't know how it's still down YTD. I don't think Amazon needs much explaining but still growing  (eg. AWS backlog massive, still going like 24% but not as much as ORCL, GCP and others obviously), but with EOY seasonality and runup to Feb, now is probably the best chance to catch the bottom. AMZN hitting $213-215 today was a good chance to stock up since it usually floats between $218-$227 if you're short term swing trading but long term I'd expect it to catchup to other mag7.

SMCI - Underrated. Markets were looking short term performance, and Charles was quoting like 55%+ Y/Y forward revenue growth which nobody believed + backlog that didnt get realized yet. But now with all the data center buildouts, now it's kinda making sense. So should re-rate in the next two earnings.

_
Buy

AMD - So many deals from OpenAI x AMD, oracle building out with AMD, this is going to re-rate to a potential $1T+ company if it's actually a strong competitive to $NVDA.  I don't think it's winner takes all and you can see a $4.5T+ market cap size with NVDA and some $350B marketcap size with AMD, so we can see a large ramp up (OpenAI is usually the leader in frontier models and if Sam says they can use AMD chips + elon said its' good for small-medium weight models, prboably means something positive)

FLNC - Strong re-rate on energy after AI consumption, great buy.

SEI - Strong re-rate on energy after AI consumption, great buy.

BZAI - Someone else did a DD on this company, just cause of sector and shift to edge compute (eg. Robotics goign to be hot). Because of low MC and runup of similar companies could turn out well.

NKLR - Nuclear stocks like $OKLO have been taking off, this is just follow the lader.

IREN - Needs no introduction, huge GW compute capacity just no announced mag7 deals yet but could come anytime -> strong re-rate. Only reason not a strong buy is because not fully convinced miners can pivot like CRWV and maintain great margins (eg. $ORCL hit piece) but we'll see.

WULF - GOOGL backlog, another $3.6+ or so in funding helps a lot.

CIFR - Lot of info on X about future capacity and strong re-rating. Always liked this company because it was NBIS-lite. You can probably buy any Neocloud and it will go up because the sector is incredibly high potential with Mag7 funneling revenue.

CRWV - Didn't like this as much as others because of debt but because of the seed oil correction much better buy point at $134 (below when META deal was announced)

BITF - Same in Neocloud category

WYFI - Same in Neocloud category

BITF - Same in Neocloud category

GLXY - Same in Neocloud category, helps with their buildout

RBRK - Did a DD on this, great buy for cybersecurity sector in mid term, they just need to scale back marketing and then it looks like they have a lot more FCF because they're spending most OPEX on marketing.

GRAB - Great fundamentally, -6.56% correction good to buy again

SEA - AMZN in SEA, tons of people use them. Just a buy just because of costumer base + monetization potenetial. Fundamentally growing $5B+ rev 38% Y/Y is also great.

META - I really don't like all their expensive capex on AI since they're not really putting out fronteir models like ChatGPT with it, who knows what Zuck is doing. But that aside, down 7.3% over the month, going to $700 support, probably a good buy around here to play catchup.

TGT - Dividend next month good catalyst.

SNAP - The Jenners are coming back (helps with popularity), they're shifting former memory opex to revenue, and this will probably cause a HUGE rerating next year. Just suffers from tax harvesting otherwise would be a strong buy rn. Usually tax harvesting events are kinda done in December.

MU - Now that China fears are kinda less intense, MU is a lot stronger buy just cause of memory use on buildout.

RKLB - Neutron, golden dome contracts, lot of cataylsts

FLY - Medium lift

UNH - Healthcare stock not affected by soybeans but had a correction. Would likely go up one instituions post their ports (eg. warren likely bought more)

Random thoughts
Basically any growth/risk stock that's not named Oklo is great because we have

-> Rate Cut end of month October
-> Government re-opening sometime (likely around end of Oct or early Nov)

Into
-> Rate Cut December.
-> Midterms (Bullish for stocks)

Usually market crashes happen when there's tightening not easing. And your stupid quantum bubbles would likely continue for another 3-12 months afterward. If you're short, then probably wait till next Feb.

Anyway, this is a great time for risk-on, and specially riding trends with neoclouds -> affiliated sectors (eg. energy) -> affiliated companies (eg. smci, tsm, etc).

I half joke-about soybeans because it likely signed escalating tensions, but I'd probably see a run-up into next year. Also I could write up a lot about each one but it's pretty time consuming but I'll put on a thesis post about random ones eg. $RBRK, from time to time.

Space/robotics/energy/quantum/ai/semi/critical top verticals right now, don't fight against momentum. I can think something is overvalued (eg. some critical materials bc. it's still spectulative compared to neoclouds that kinda have guaranteed rev based on execution from mag7) but I wouldn't short it into rate cuts.

Just personal thoughts, NFA
```

### [盈利 #40] CRDO long hz=6m — pub=2025-10-04T01:22:20
- entry=2025-10-06, $152.84
- 1m: **resolved_hit** raw=+7.45% bench=+0.54% excess=+6.91%
- 3m: excess=-10.42%  6m: excess=-30.62%
- **条件 label**: ['PRICE_TARGET']
- **if 句**: ["BMNR - Just buy ETH if you believe in it but I wouldn't buy at ETH at $4500"]
- **原文 (全文)**:
```
Friday Market Close, Personal Thoughts and Explanations:

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

Reddit - Dropped 29% off immaterial news that ChatGPT wasn't citing it as much. Nobody visits Reddit through ChatGPT, good recovery buy off $200 support. 

SNAP - Finally they're doing something that's USEFUL for the first time in many years lol. Tons of Capex was spent on storing photos random drawings people saved 12 years ago taking GBs of space for their insane Google Cloud costs. They're finally monetizing it like Apple. Huge tailwind, should improve net income by a ton next year. 

AMZN - Under $220 now, great buy. AMZN prime Oct 8th, good for seasonality in Nov/Dec.

ETOR - I can't believe this is still $41. 33% cash, 1B+ cash pile growing at IBKR rates. Just suffers from tax harvesting I'd assume it goes up next year. 

NBIS - Strong buy until $150+ or new hyperscaler contract repricing. 

LTC - ETF catalyst delayed from Gov shutdown but should be approved anyway. 

Buys

Upwork - Down 4.5% or so for no reason, should recover

MSTR - BTC close to all time highs, MSTR way off ATHs cause of long btc short MSTR but NAV premium should catch up again from the BTC fomo.

ORCL - Standard rise on great forward earnings, drop for short term option chain, then rise because 14B tiktok deal and large future cloud contracts

TGT - Just undervalued great buy under $93, dividend catalyst next month

CIFR - NBIS light with GOOGL deal.

VIRT - VIX doesn't look like it's going down anytime soon but they're trading at like 6.4 or so forward P/E so it's worth.

CRDO - Good buy on correction with hypescaler buildout

WULF - Hasn't gone up as much as the other neoclouds, googl backlog

SOFI - Corrected, might recover back to ATH given macro tailwind

META - Monthly low good DCA, not as good as AMZN

AVGO - Same as ORCL, might end up like NVDA one day with hyperscaler chips

MRVL - Still down 24% YTD. 

SMCI - Good buy on datacenter buildout + server racks

Dell - Good buy on datacenter buildout + server racks

Hold

Nothing changed

Sell

TSLA - Overvalued, better longs like NBIS

CRCL - I will keep making this argument, but just buy COIN instead. You will get the same 50% revenue sharing but with a crypto exchange + ETF holding income too.  

PLTR - Disconnected from reality

BMNR - Just buy ETH if you believe in it but I wouldn't buy at ETH at $4500.

Strong Sell

RGTI - Disconnected from reality lol

All disconnected from reality, wouldn't short though cause all cult stocks. 
OKLO
QBTS
IONQ
```

### [盈利 #41] SNAP long hz=6m — pub=2025-10-15T07:42:21
- entry=2025-10-16, $7.91
- 1m: **resolved_hit** raw=+8.34% bench=+1.71% excess=+6.63%
- 3m: excess=-9.64%  6m: excess=-35.27%
- **条件 label**: ['PRICE_TARGET']
- **if 句**: ['This would be a $3T company if this were a US company, insane profit margins, insane growth rate for their size', '5T), even if buying at ATHs', "AMZN hitting $213-215 today was a good chance to stock up since it usually floats between $218-$227 if you're short term swing trading but long term I'd expect it to catchup to other mag7"]
- **原文 (全文)**:
```
The Great Soybean/Seed Oil Crash, personal thoughts and explanations:

Strong Buy
$ALAB
$CRDO
$NBIS
$WLAC
$LTC
$TSM
$BTC
(+ same as tax harvest stocks last time)
$AMZN
$SMCI
_

Buy
$AMD
$FLNC
$SEI
$BZAI
$NKLR
$IREN
$WULF
$CIFR
$CRWV
$BITF
$WYFI
$SLNH
$BITF
$RBRK
$GLXY
$GRAB
$SEA
$META
$TGT
$SNAP
$MU
$RKLB
$FLY
$UNH

Hold
$MP
$HOOD
$EOSE
$NVDA
$GOOGL
$DFLI
$SOFI
$VIRT
$RR
$AVGO
$BE
$ASTS

(Hit the ticker maximum but everything else from last post, still sell on Quantum or Oklo)
_

Strong Buys
ALAB - Huge part of datacenter buildout, NVDA like margins, Mag7 customers. Already had competitors from AVGO,  really don't think Arista would be a competitive threat.

CRDO - Same sell-off as ALAB, thought they were both kind of overvalued before, but now they're back in correction territory so good to stock up.

NBIS - $400 PT bull case. We have macro tailwind from government re-opening + rate cut EOM october into earnings, so short term looks promising. Lot of things going for it (eg. meta x crwv, so there's potential for more mag7 clients), sum of parts doing well, eg. clickhouse, and scaling rev from $100m to $1.5B+ a quarter is insane. there's already contracts locked in its just a matter of company execution.

WLAC - Wrote a thesis about this earlier at $13. Even at $14.5 strong because it can re-rate 100%+ easily.

LTC - Affected by leverage traders and government shutdown. The shutdown is predicted to last awhile and the main reason to buy was the ETF getting approved. But a great buy sub <$100 anyway, because it will get approved in due time (~95% chance).

TSM - Holy crap. This would be a $3T company if this were a US company, insane profit margins, insane growth rate for their size. And every post you see about OpenAi X (**sydney sweeney partnership) or AMD buildout/NVDA buildout. TSM is the center of it all and would easily be a $2T+ company (from here at ~$1.5T), even if buying at ATHs.

BTC - $112K good entry point. Goldt keeps hitting ATH, nothing really changed fundamentally, just lot of liquidations recently
(+ same as tax harvest stocks last time)

AMZN - I really don't know how it's still down YTD. I don't think Amazon needs much explaining but still growing  (eg. AWS backlog massive, still going like 24% but not as much as ORCL, GCP and others obviously), but with EOY seasonality and runup to Feb, now is probably the best chance to catch the bottom. AMZN hitting $213-215 today was a good chance to stock up since it usually floats between $218-$227 if you're short term swing trading but long term I'd expect it to catchup to other mag7.

SMCI - Underrated. Markets were looking short term performance, and Charles was quoting like 55%+ Y/Y forward revenue growth which nobody believed + backlog that didnt get realized yet. But now with all the data center buildouts, now it's kinda making sense. So should re-rate in the next two earnings.

_
Buy

AMD - So many deals from OpenAI x AMD, oracle building out with AMD, this is going to re-rate to a potential $1T+ company if it's actually a strong competitive to $NVDA.  I don't think it's winner takes all and you can see a $4.5T+ market cap size with NVDA and some $350B marketcap size with AMD, so we can see a large ramp up (OpenAI is usually the leader in frontier models and if Sam says they can use AMD chips + elon said its' good for small-medium weight models, prboably means something positive)

FLNC - Strong re-rate on energy after AI consumption, great buy.

SEI - Strong re-rate on energy after AI consumption, great buy.

BZAI - Someone else did a DD on this company, just cause of sector and shift to edge compute (eg. Robotics goign to be hot). Because of low MC and runup of similar companies could turn out well.

NKLR - Nuclear stocks like $OKLO have been taking off, this is just follow the lader.

IREN - Needs no introduction, huge GW compute capacity just no announced mag7 deals yet but could come anytime -> strong re-rate. Only reason not a strong buy is because not fully convinced miners can pivot like CRWV and maintain great margins (eg. $ORCL hit piece) but we'll see.

WULF - GOOGL backlog, another $3.6+ or so in funding helps a lot.

CIFR - Lot of info on X about future capacity and strong re-rating. Always liked this company because it was NBIS-lite. You can probably buy any Neocloud and it will go up because the sector is incredibly high potential with Mag7 funneling revenue.

CRWV - Didn't like this as much as others because of debt but because of the seed oil correction much better buy point at $134 (below when META deal was announced)

BITF - Same in Neocloud category

WYFI - Same in Neocloud category

BITF - Same in Neocloud category

GLXY - Same in Neocloud category, helps with their buildout

RBRK - Did a DD on this, great buy for cybersecurity sector in mid term, they just need to scale back marketing and then it looks like they have a lot more FCF because they're spending most OPEX on marketing.

GRAB - Great fundamentally, -6.56% correction good to buy again

SEA - AMZN in SEA, tons of people use them. Just a buy just because of costumer base + monetization potenetial. Fundamentally growing $5B+ rev 38% Y/Y is also great.

META - I really don't like all their expensive capex on AI since they're not really putting out fronteir models like ChatGPT with it, who knows what Zuck is doing. But that aside, down 7.3% over the month, going to $700 support, probably a good buy around here to play catchup.

TGT - Dividend next month good catalyst.

SNAP - The Jenners are coming back (helps with popularity), they're shifting former memory opex to revenue, and this will probably cause a HUGE rerating next year. Just suffers from tax harvesting otherwise would be a strong buy rn. Usually tax harvesting events are kinda done in December.

MU - Now that China fears are kinda less intense, MU is a lot stronger buy just cause of memory use on buildout.

RKLB - Neutron, golden dome contracts, lot of cataylsts

FLY - Medium lift

UNH - Healthcare stock not affected by soybeans but had a correction. Would likely go up one instituions post their ports (eg. warren likely bought more)

Random thoughts
Basically any growth/risk stock that's not named Oklo is great because we have

-> Rate Cut end of month October
-> Government re-opening sometime (likely around end of Oct or early Nov)

Into
-> Rate Cut December.
-> Midterms (Bullish for stocks)

Usually market crashes happen when there's tightening not easing. And your stupid quantum bubbles would likely continue for another 3-12 months afterward. If you're short, then probably wait till next Feb.

Anyway, this is a great time for risk-on, and specially riding trends with neoclouds -> affiliated sectors (eg. energy) -> affiliated companies (eg. smci, tsm, etc).

I half joke-about soybeans because it likely signed escalating tensions, but I'd probably see a run-up into next year. Also I could write up a lot about each one but it's pretty time consuming but I'll put on a thesis post about random ones eg. $RBRK, from time to time.

Space/robotics/energy/quantum/ai/semi/critical top verticals right now, don't fight against momentum. I can think something is overvalued (eg. some critical materials bc. it's still spectulative compared to neoclouds that kinda have guaranteed rev based on execution from mag7) but I wouldn't short it into rate cuts.

Just personal thoughts, NFA
```

### [盈利 #42] QBTS short hz=6m — pub=2025-10-04T01:22:20
- entry=2025-10-06, $32.01
- 1m: **resolved_hit** raw=+7.09% bench=+0.54% excess=+6.55%
- 3m: excess=+2.98%  6m: excess=+55.43%
- **条件 label**: ['PRICE_TARGET']
- **if 句**: ["BMNR - Just buy ETH if you believe in it but I wouldn't buy at ETH at $4500"]
- **原文 (全文)**:
```
Friday Market Close, Personal Thoughts and Explanations:

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

Reddit - Dropped 29% off immaterial news that ChatGPT wasn't citing it as much. Nobody visits Reddit through ChatGPT, good recovery buy off $200 support. 

SNAP - Finally they're doing something that's USEFUL for the first time in many years lol. Tons of Capex was spent on storing photos random drawings people saved 12 years ago taking GBs of space for their insane Google Cloud costs. They're finally monetizing it like Apple. Huge tailwind, should improve net income by a ton next year. 

AMZN - Under $220 now, great buy. AMZN prime Oct 8th, good for seasonality in Nov/Dec.

ETOR - I can't believe this is still $41. 33% cash, 1B+ cash pile growing at IBKR rates. Just suffers from tax harvesting I'd assume it goes up next year. 

NBIS - Strong buy until $150+ or new hyperscaler contract repricing. 

LTC - ETF catalyst delayed from Gov shutdown but should be approved anyway. 

Buys

Upwork - Down 4.5% or so for no reason, should recover

MSTR - BTC close to all time highs, MSTR way off ATHs cause of long btc short MSTR but NAV premium should catch up again from the BTC fomo.

ORCL - Standard rise on great forward earnings, drop for short term option chain, then rise because 14B tiktok deal and large future cloud contracts

TGT - Just undervalued great buy under $93, dividend catalyst next month

CIFR - NBIS light with GOOGL deal.

VIRT - VIX doesn't look like it's going down anytime soon but they're trading at like 6.4 or so forward P/E so it's worth.

CRDO - Good buy on correction with hypescaler buildout

WULF - Hasn't gone up as much as the other neoclouds, googl backlog

SOFI - Corrected, might recover back to ATH given macro tailwind

META - Monthly low good DCA, not as good as AMZN

AVGO - Same as ORCL, might end up like NVDA one day with hyperscaler chips

MRVL - Still down 24% YTD. 

SMCI - Good buy on datacenter buildout + server racks

Dell - Good buy on datacenter buildout + server racks

Hold

Nothing changed

Sell

TSLA - Overvalued, better longs like NBIS

CRCL - I will keep making this argument, but just buy COIN instead. You will get the same 50% revenue sharing but with a crypto exchange + ETF holding income too.  

PLTR - Disconnected from reality

BMNR - Just buy ETH if you believe in it but I wouldn't buy at ETH at $4500.

Strong Sell

RGTI - Disconnected from reality lol

All disconnected from reality, wouldn't short though cause all cult stocks. 
OKLO
QBTS
IONQ
```

### [盈利 #43] CRDO long hz=6m — pub=2025-10-15T07:42:21
- entry=2025-10-16, $134.50
- 1m: **resolved_hit** raw=+8.19% bench=+1.71% excess=+6.48%
- 3m: excess=+11.35%  6m: excess=+29.72%
- **条件 label**: ['PRICE_TARGET']
- **if 句**: ['This would be a $3T company if this were a US company, insane profit margins, insane growth rate for their size', '5T), even if buying at ATHs', "AMZN hitting $213-215 today was a good chance to stock up since it usually floats between $218-$227 if you're short term swing trading but long term I'd expect it to catchup to other mag7"]
- **原文 (全文)**:
```
The Great Soybean/Seed Oil Crash, personal thoughts and explanations:

Strong Buy
$ALAB
$CRDO
$NBIS
$WLAC
$LTC
$TSM
$BTC
(+ same as tax harvest stocks last time)
$AMZN
$SMCI
_

Buy
$AMD
$FLNC
$SEI
$BZAI
$NKLR
$IREN
$WULF
$CIFR
$CRWV
$BITF
$WYFI
$SLNH
$BITF
$RBRK
$GLXY
$GRAB
$SEA
$META
$TGT
$SNAP
$MU
$RKLB
$FLY
$UNH

Hold
$MP
$HOOD
$EOSE
$NVDA
$GOOGL
$DFLI
$SOFI
$VIRT
$RR
$AVGO
$BE
$ASTS

(Hit the ticker maximum but everything else from last post, still sell on Quantum or Oklo)
_

Strong Buys
ALAB - Huge part of datacenter buildout, NVDA like margins, Mag7 customers. Already had competitors from AVGO,  really don't think Arista would be a competitive threat.

CRDO - Same sell-off as ALAB, thought they were both kind of overvalued before, but now they're back in correction territory so good to stock up.

NBIS - $400 PT bull case. We have macro tailwind from government re-opening + rate cut EOM october into earnings, so short term looks promising. Lot of things going for it (eg. meta x crwv, so there's potential for more mag7 clients), sum of parts doing well, eg. clickhouse, and scaling rev from $100m to $1.5B+ a quarter is insane. there's already contracts locked in its just a matter of company execution.

WLAC - Wrote a thesis about this earlier at $13. Even at $14.5 strong because it can re-rate 100%+ easily.

LTC - Affected by leverage traders and government shutdown. The shutdown is predicted to last awhile and the main reason to buy was the ETF getting approved. But a great buy sub <$100 anyway, because it will get approved in due time (~95% chance).

TSM - Holy crap. This would be a $3T company if this were a US company, insane profit margins, insane growth rate for their size. And every post you see about OpenAi X (**sydney sweeney partnership) or AMD buildout/NVDA buildout. TSM is the center of it all and would easily be a $2T+ company (from here at ~$1.5T), even if buying at ATHs.

BTC - $112K good entry point. Goldt keeps hitting ATH, nothing really changed fundamentally, just lot of liquidations recently
(+ same as tax harvest stocks last time)

AMZN - I really don't know how it's still down YTD. I don't think Amazon needs much explaining but still growing  (eg. AWS backlog massive, still going like 24% but not as much as ORCL, GCP and others obviously), but with EOY seasonality and runup to Feb, now is probably the best chance to catch the bottom. AMZN hitting $213-215 today was a good chance to stock up since it usually floats between $218-$227 if you're short term swing trading but long term I'd expect it to catchup to other mag7.

SMCI - Underrated. Markets were looking short term performance, and Charles was quoting like 55%+ Y/Y forward revenue growth which nobody believed + backlog that didnt get realized yet. But now with all the data center buildouts, now it's kinda making sense. So should re-rate in the next two earnings.

_
Buy

AMD - So many deals from OpenAI x AMD, oracle building out with AMD, this is going to re-rate to a potential $1T+ company if it's actually a strong competitive to $NVDA.  I don't think it's winner takes all and you can see a $4.5T+ market cap size with NVDA and some $350B marketcap size with AMD, so we can see a large ramp up (OpenAI is usually the leader in frontier models and if Sam says they can use AMD chips + elon said its' good for small-medium weight models, prboably means something positive)

FLNC - Strong re-rate on energy after AI consumption, great buy.

SEI - Strong re-rate on energy after AI consumption, great buy.

BZAI - Someone else did a DD on this company, just cause of sector and shift to edge compute (eg. Robotics goign to be hot). Because of low MC and runup of similar companies could turn out well.

NKLR - Nuclear stocks like $OKLO have been taking off, this is just follow the lader.

IREN - Needs no introduction, huge GW compute capacity just no announced mag7 deals yet but could come anytime -> strong re-rate. Only reason not a strong buy is because not fully convinced miners can pivot like CRWV and maintain great margins (eg. $ORCL hit piece) but we'll see.

WULF - GOOGL backlog, another $3.6+ or so in funding helps a lot.

CIFR - Lot of info on X about future capacity and strong re-rating. Always liked this company because it was NBIS-lite. You can probably buy any Neocloud and it will go up because the sector is incredibly high potential with Mag7 funneling revenue.

CRWV - Didn't like this as much as others because of debt but because of the seed oil correction much better buy point at $134 (below when META deal was announced)

BITF - Same in Neocloud category

WYFI - Same in Neocloud category

BITF - Same in Neocloud category

GLXY - Same in Neocloud category, helps with their buildout

RBRK - Did a DD on this, great buy for cybersecurity sector in mid term, they just need to scale back marketing and then it looks like they have a lot more FCF because they're spending most OPEX on marketing.

GRAB - Great fundamentally, -6.56% correction good to buy again

SEA - AMZN in SEA, tons of people use them. Just a buy just because of costumer base + monetization potenetial. Fundamentally growing $5B+ rev 38% Y/Y is also great.

META - I really don't like all their expensive capex on AI since they're not really putting out fronteir models like ChatGPT with it, who knows what Zuck is doing. But that aside, down 7.3% over the month, going to $700 support, probably a good buy around here to play catchup.

TGT - Dividend next month good catalyst.

SNAP - The Jenners are coming back (helps with popularity), they're shifting former memory opex to revenue, and this will probably cause a HUGE rerating next year. Just suffers from tax harvesting otherwise would be a strong buy rn. Usually tax harvesting events are kinda done in December.

MU - Now that China fears are kinda less intense, MU is a lot stronger buy just cause of memory use on buildout.

RKLB - Neutron, golden dome contracts, lot of cataylsts

FLY - Medium lift

UNH - Healthcare stock not affected by soybeans but had a correction. Would likely go up one instituions post their ports (eg. warren likely bought more)

Random thoughts
Basically any growth/risk stock that's not named Oklo is great because we have

-> Rate Cut end of month October
-> Government re-opening sometime (likely around end of Oct or early Nov)

Into
-> Rate Cut December.
-> Midterms (Bullish for stocks)

Usually market crashes happen when there's tightening not easing. And your stupid quantum bubbles would likely continue for another 3-12 months afterward. If you're short, then probably wait till next Feb.

Anyway, this is a great time for risk-on, and specially riding trends with neoclouds -> affiliated sectors (eg. energy) -> affiliated companies (eg. smci, tsm, etc).

I half joke-about soybeans because it likely signed escalating tensions, but I'd probably see a run-up into next year. Also I could write up a lot about each one but it's pretty time consuming but I'll put on a thesis post about random ones eg. $RBRK, from time to time.

Space/robotics/energy/quantum/ai/semi/critical top verticals right now, don't fight against momentum. I can think something is overvalued (eg. some critical materials bc. it's still spectulative compared to neoclouds that kinda have guaranteed rev based on execution from mag7) but I wouldn't short it into rate cuts.

Just personal thoughts, NFA
```

### [盈利 #44] HIMS long hz=6m — pub=2025-09-11T16:31:05
- entry=2025-09-12, $51.03
- 1m: **resolved_hit** raw=+7.25% bench=+0.86% excess=+6.39%
- 3m: excess=-30.79%  6m: excess=-53.08%
- **条件 label**: ['PRICE_TARGET']
- **原文 (全文)**:
```
@himshouse This reminds me when everyone gave $HOOD a $12 PT when the stock was trading at $18.  

The 42% short interest are scared when price is holding $50 after they shorted another 6%. 

$HIMS is profitable, acquiring companies,  small 10B market cap, and with new product launches.
```

### [盈利 #45] DELL long hz=6m — pub=2025-10-04T01:22:20
- entry=2025-10-06, $145.52
- 1m: **resolved_hit** raw=+6.27% bench=+0.54% excess=+5.73%
- 3m: excess=-20.16%  6m: excess=+23.46%
- **条件 label**: ['PRICE_TARGET']
- **if 句**: ["BMNR - Just buy ETH if you believe in it but I wouldn't buy at ETH at $4500"]
- **原文 (全文)**:
```
Friday Market Close, Personal Thoughts and Explanations:

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

Reddit - Dropped 29% off immaterial news that ChatGPT wasn't citing it as much. Nobody visits Reddit through ChatGPT, good recovery buy off $200 support. 

SNAP - Finally they're doing something that's USEFUL for the first time in many years lol. Tons of Capex was spent on storing photos random drawings people saved 12 years ago taking GBs of space for their insane Google Cloud costs. They're finally monetizing it like Apple. Huge tailwind, should improve net income by a ton next year. 

AMZN - Under $220 now, great buy. AMZN prime Oct 8th, good for seasonality in Nov/Dec.

ETOR - I can't believe this is still $41. 33% cash, 1B+ cash pile growing at IBKR rates. Just suffers from tax harvesting I'd assume it goes up next year. 

NBIS - Strong buy until $150+ or new hyperscaler contract repricing. 

LTC - ETF catalyst delayed from Gov shutdown but should be approved anyway. 

Buys

Upwork - Down 4.5% or so for no reason, should recover

MSTR - BTC close to all time highs, MSTR way off ATHs cause of long btc short MSTR but NAV premium should catch up again from the BTC fomo.

ORCL - Standard rise on great forward earnings, drop for short term option chain, then rise because 14B tiktok deal and large future cloud contracts

TGT - Just undervalued great buy under $93, dividend catalyst next month

CIFR - NBIS light with GOOGL deal.

VIRT - VIX doesn't look like it's going down anytime soon but they're trading at like 6.4 or so forward P/E so it's worth.

CRDO - Good buy on correction with hypescaler buildout

WULF - Hasn't gone up as much as the other neoclouds, googl backlog

SOFI - Corrected, might recover back to ATH given macro tailwind

META - Monthly low good DCA, not as good as AMZN

AVGO - Same as ORCL, might end up like NVDA one day with hyperscaler chips

MRVL - Still down 24% YTD. 

SMCI - Good buy on datacenter buildout + server racks

Dell - Good buy on datacenter buildout + server racks

Hold

Nothing changed

Sell

TSLA - Overvalued, better longs like NBIS

CRCL - I will keep making this argument, but just buy COIN instead. You will get the same 50% revenue sharing but with a crypto exchange + ETF holding income too.  

PLTR - Disconnected from reality

BMNR - Just buy ETH if you believe in it but I wouldn't buy at ETH at $4500.

Strong Sell

RGTI - Disconnected from reality lol

All disconnected from reality, wouldn't short though cause all cult stocks. 
OKLO
QBTS
IONQ
```

### [盈利 #46] AMZN long hz=long_term — pub=2025-10-19T18:21:35
- entry=2025-10-20, $213.88
- 1m: **resolved_hit** raw=+4.05% bench=-1.67% excess=+5.73%
- 3m: excess=+6.93%  6m: excess=+13.73%
- **条件 label**: ['PRICE_TARGET']
- **if 句**: ['5T marketcap, AMD has a lot to catch up on even if it takes a small percent share', "BMNR - If I don't like Ethereum at these levels, no point of holding treasury companies"]
- **原文 (全文)**:
```
October 20th, Important Rate Cut Trading Week.

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
$ETH
$BMNR
$PL
$BLSKY
$RGTI
$OKLO
$IONQ
$QBTS

_

So macro wise, we are 9 days away from (~97% or so rate cut). Market is in fear mode. This is the ideal time to go long and not cut positions.

Fire Sale
_

$NBIS - Needs no explanation, I still maintain $400 PT on a bull case 2026 due to 4-6B+ forward revenue off ~60-75% gross margins, and another likely hyperscaler contract (eg. $META)

What happened on the 10%+ drop on Friday was mechanical hedging and MM Pinning. You can see this with the price stuck at $113.5, despite any volatility. 

I'd expect short hedges to unwind Monday (given MMs bought puts and were short calls -> heavy short into expiration) and price to go back up. I ended up buying 6 figures worth of calls on the drop as there was no material changes.

Strong Buy

TSM - Holy crap, please have this in your portfolio. This is a money printer, and scaling your revenue by 38-40% every year WHILE increasing gross margins is just insane. It dipped as well after smashing earnings so it's one of the easiest longs in my life.

AMKR - I don't have this in my portfolio yet but will be looking to add due to TSM's involvement in Arizona and potential to be a big partner in the US supply chain (as America tries to push TSM toward US fab + manufacturing).

WLAC - Neocloud SPAC IPO, large upside. I talk about this a lot recently, but it's probably one of the best valued Neoclouds out there, and already has great profit margins (not a pivot from miners, where it's a bit more uncertain). They work with Fluidstack, and I'd expect a 500%+ re-rating on top of a Mag7 contract.

AMZN - $213 is insane lol. I have no clue how this is down -3% YTD during a bull market.

LTC - Affected by crypto liquidations and government shutdown delaying ETFs. Great time to buy and just wait for ETF to be approved.

RDDT - Great dip to $190. I thought $200 would be a bottom but ended up going lower. The news about ChatGPT citing it less caused a large sell-off which I think was very immaterial.

HIMS - 14%+ drop off CEO share sale. Owners sell shares all the time, it doesn't really affect the fundamentals of the company much, just short term sentiment. I'd expect it to rebound.

IBIT - Bitcoin $108k great entry point, it's been swinging between $110k - $120k for awhile so anything under is usually great.

ALAB - I said this last time but it sold off way too much from news of a new competitor. It's already competing vs AVGO in the market lol, NVDA-like margins, growing hundreds of percent Y/Y, Mag7 using them in data center buildout. 

CRDO - Similar thesis to ALAB, sold off alongside Astera but a bit less.

SMCI - Should get re-rated for 55%+ or so revenue growth into next year. I doubted the projections earlier but with the data center growth, it's looking realistic.

FLY - This was a medium lift payload play. People doubt fly's execution but NOC co-developing medium lift takes a lot of risk off the table (and possible re-rating it 500%+ when it competes vs falcon9)

SNAP - Did the math on Snap monetization of memories in an earlier DD post and it's completely not priced in yet. It's doing $1.3B+ quarterly revenue on a $13B market cap lol, and the amount FCF they would get from increasing their revenue + lowering Google OPEX costs is insane.

ETOR  - Majority cash, growing at IBKR rates, suffering from tax harvesting

LULU - Suffering from tax harvesting + competition from Alo, Vuori, etc. But seasonally should be good, and extremely low p/e now.

Buy
AMD - ChatGPT putting in AMD orders, ORCL building out AMD data centers. Likely going to get a re-rating in the next year as a potential $NVDA competitor. Still think Nvidia will dominate but with it's 4.5T marketcap, AMD has a lot to catch up on even if it takes a small percent share.

HOOD - Looking at a lot better after the 10%+ correction. Could pull a PLTR

RBRK - Did DD on this earlier, looks better on the drop as a cybersecurity company really low multiples in the space. Just needs to cut back on marketing, customers sticky. 

UNH - Healthcare is sht in America but not going anywhere. Think Warren and the others know this 

TGT 🐈 - Dividend next moth, big dividend stock. Around now is a good time to load up IMO

IREN 🐈 - Huge GW, expect mag7 or similar deal. 

WYFI - Any neocloud is a buy (eg. see thesis on mag7 funneling revenue down toward these small 1B-5B companies)

WULF - neocloud play

CIFR - neocloud play

SLNH - neocloud play

BITF - neocloud play

GLXY - neocloud derivative play

FLNC - neocloud energy play

MU - China derisked, memory had a huge market there, memory also likely going to get re-rating in tdata center buildout

_

Sell

ETH - Not a fan of Ethereum at $4k+
BMNR - If I don't like Ethereum at these levels, no point of holding treasury companies 
PL - Low revenue, space stock (extremely high valuation)
BLSKY -Low revenue, space stock (extremely high valuation)
RGTI - Quantum bubble
OKLO - Nuclear bubble
IONQ -Quantum bubble 
QBTS - Quantum bubble

_

Quick macro heads up:
-> Rate cut in 9 days ~97% odds. Frontrunning expected, go long.  That's all.
```

### [盈利 #47] NBIS long hz=4m — pub=2025-09-24T15:59:17
- entry=2025-09-25, $108.06
- 1m: **resolved_hit** raw=+8.52% bench=+2.92% excess=+5.60%
- 3m: excess=-23.84%  6m: excess=-10.65%
- **条件 label**: ['PRICE_TARGET']
- **原文 (全文)**:
```
$750K+ in $NBIS, with ~$93K+ in unrealized gains in just 5 days. 

This stock is extremely undervalued. Northland just gave a $206 PT, but I’ve been calling this since it was under $100.

I rarely have high-conviction stocks. But NBIS is one of them. 

$112 -&gt; $200 in 4 months. https://t.co/wHTRGKlupK
```

### [盈利 #48] TSM long hz=long_term — pub=2025-09-25T21:04:48
- entry=2025-09-26, $273.89
- 1m: **resolved_hit** raw=+8.89% bench=+3.54% excess=+5.36%
- 3m: excess=+5.94%  6m: excess=+25.12%
- **条件 label**: ['PRICE_LEVEL', 'EVENT_GENERIC', 'PRICE_DIP']
- **if 句**: ['So daily thoughts on Sept 25th + market drop if you like my insights:', "5% drop (yet), if I like it I'd probably buy overnight", "That's kinda why I said shares into calls if it drops more"]
- **原文 (全文)**:
```
So daily thoughts on Sept 25th + market drop if you like my insights: 

1. 3x rate cut went from 65% to 56% from data today. This is a lot more material, since people are front-running rate cuts now. 

Either way, any rate cut usually lead to large inflows so it's generally bullish for markets months out. 

Powell's thoughts about market being overvalued holds kind of true for certain stocks. Oklo, Quantum, etc. way too overvalued but never short. Even stuff i love like RKLB, really overvalued. 

But there's too much money flowing on sidelines, nothing else to hold other than stocks, real estate, btc, because of all the inflation. Triple rate cut implies they want to keep musical chairs running for another 8 moths. I'd start to worry around Summer next year. 

2. Market droplast two days, I'd use the opportunity to DCA into $Z after 15% drop, AMZN, or $NBIS after 5%.  I still need to research $CIFR so can't really full conviction recommend it after a 17.5% drop (yet), if I like it I'd probably buy overnight. Lot of fun things to swing trade like RKLB on the side. I'm still waiting next month for 6 figures in TGT calls, cause of Nov dividend. 

Everyone's loading AMZN calls now, but like GOOGL it will might drop to levels like $210 -> $200, where people give up then start some stupid rally. That's kinda why I said shares into calls if it drops more. 

3. Lot of tax harvesting taking place. If you have the patience to wait 4 months, lot of undervalued companies like ETOR, TGT, LULU, will likely recover but obviously won't net 600%+ gains unless you do leverage + options. Great time to stock up if you're a patient investor. 

4. I've always maintained you should buy stuff at the lows when market gives up on it (eg. Ethereum $1600), and when there's a new narrative with Bitmine, it's a good time to sell at $4k+. I wouldn't buy the dip even if it drops to $3.5k. I have a whole thesis on this but I'll save this for another day. 

This is only different if it's less speculative like NBIS, like a literal $17B contract flowing into a 25B marketcap company and it's just a matter of execution + waiting. 

Still waiting for LTC, small marketcap, market still pricing in 90% etf approval. There's likely going to be a new BItmine for Litcoin in a few months, and with a small MC can rally quite a bit. 

5. I've never seen a post get more bookmarks than likes other than thirst traps, so you all must like my portfolio weighting!

You've already seen me day trade here: https://t.co/AjTB69Na65 but it's a little annoying for me to do call-outs every time I change positions so I'd prefer to just post general insights + thesis.

6. Market prices in forward revenue, even if you see stuff like NBIS, TSM and stuff dropping today, they're great fundamentally and will likely keep going up.
```

### [盈利 #49] FN long hz=long_term — pub=2026-03-04T11:44:02
- entry=2026-03-05, $543.36
- 1m: **resolved_hit** raw=+2.02% bench=-3.28% excess=+5.31%
- 3m: excess=+20.43%  6m: excess=+0.00%
- **条件 label**: ['PRICE_TARGET']
- **原文 (全文)**:
```
$GOOGL rejecting CPO is a massive structural win for the entire pluggable optics ecosystem.  

Most people missed this in the Needham analyst note on the $LITE $850 PT upgrade today:

Large beneficiaries: $AAOI, $FN, Innolight, transceiver companies. 

Secondary beneficiaries (epiwafers): $IQE, Landmark 

Third Order Beneficiaries (substrate): $AXTI, Sumitomo

Downgrade (CPO): Soitec

Quote:  "LITE sees an unexpected bonus that its primary transceiver module customer (Google) currently has no plans to adopt CPO in its TPU architecture from what we have seen."
```

### [盈利 #50] ETOR long hz=long_term — pub=2025-10-19T18:21:35
- entry=2025-10-20, $38.12
- 1m: **resolved_hit** raw=+2.86% bench=-1.67% excess=+4.53%
- 3m: excess=-21.05%  6m: excess=-8.50%
- **条件 label**: ['PRICE_TARGET']
- **if 句**: ['5T marketcap, AMD has a lot to catch up on even if it takes a small percent share', "BMNR - If I don't like Ethereum at these levels, no point of holding treasury companies"]
- **原文 (全文)**:
```
October 20th, Important Rate Cut Trading Week.

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
$ETH
$BMNR
$PL
$BLSKY
$RGTI
$OKLO
$IONQ
$QBTS

_

So macro wise, we are 9 days away from (~97% or so rate cut). Market is in fear mode. This is the ideal time to go long and not cut positions.

Fire Sale
_

$NBIS - Needs no explanation, I still maintain $400 PT on a bull case 2026 due to 4-6B+ forward revenue off ~60-75% gross margins, and another likely hyperscaler contract (eg. $META)

What happened on the 10%+ drop on Friday was mechanical hedging and MM Pinning. You can see this with the price stuck at $113.5, despite any volatility. 

I'd expect short hedges to unwind Monday (given MMs bought puts and were short calls -> heavy short into expiration) and price to go back up. I ended up buying 6 figures worth of calls on the drop as there was no material changes.

Strong Buy

TSM - Holy crap, please have this in your portfolio. This is a money printer, and scaling your revenue by 38-40% every year WHILE increasing gross margins is just insane. It dipped as well after smashing earnings so it's one of the easiest longs in my life.

AMKR - I don't have this in my portfolio yet but will be looking to add due to TSM's involvement in Arizona and potential to be a big partner in the US supply chain (as America tries to push TSM toward US fab + manufacturing).

WLAC - Neocloud SPAC IPO, large upside. I talk about this a lot recently, but it's probably one of the best valued Neoclouds out there, and already has great profit margins (not a pivot from miners, where it's a bit more uncertain). They work with Fluidstack, and I'd expect a 500%+ re-rating on top of a Mag7 contract.

AMZN - $213 is insane lol. I have no clue how this is down -3% YTD during a bull market.

LTC - Affected by crypto liquidations and government shutdown delaying ETFs. Great time to buy and just wait for ETF to be approved.

RDDT - Great dip to $190. I thought $200 would be a bottom but ended up going lower. The news about ChatGPT citing it less caused a large sell-off which I think was very immaterial.

HIMS - 14%+ drop off CEO share sale. Owners sell shares all the time, it doesn't really affect the fundamentals of the company much, just short term sentiment. I'd expect it to rebound.

IBIT - Bitcoin $108k great entry point, it's been swinging between $110k - $120k for awhile so anything under is usually great.

ALAB - I said this last time but it sold off way too much from news of a new competitor. It's already competing vs AVGO in the market lol, NVDA-like margins, growing hundreds of percent Y/Y, Mag7 using them in data center buildout. 

CRDO - Similar thesis to ALAB, sold off alongside Astera but a bit less.

SMCI - Should get re-rated for 55%+ or so revenue growth into next year. I doubted the projections earlier but with the data center growth, it's looking realistic.

FLY - This was a medium lift payload play. People doubt fly's execution but NOC co-developing medium lift takes a lot of risk off the table (and possible re-rating it 500%+ when it competes vs falcon9)

SNAP - Did the math on Snap monetization of memories in an earlier DD post and it's completely not priced in yet. It's doing $1.3B+ quarterly revenue on a $13B market cap lol, and the amount FCF they would get from increasing their revenue + lowering Google OPEX costs is insane.

ETOR  - Majority cash, growing at IBKR rates, suffering from tax harvesting

LULU - Suffering from tax harvesting + competition from Alo, Vuori, etc. But seasonally should be good, and extremely low p/e now.

Buy
AMD - ChatGPT putting in AMD orders, ORCL building out AMD data centers. Likely going to get a re-rating in the next year as a potential $NVDA competitor. Still think Nvidia will dominate but with it's 4.5T marketcap, AMD has a lot to catch up on even if it takes a small percent share.

HOOD - Looking at a lot better after the 10%+ correction. Could pull a PLTR

RBRK - Did DD on this earlier, looks better on the drop as a cybersecurity company really low multiples in the space. Just needs to cut back on marketing, customers sticky. 

UNH - Healthcare is sht in America but not going anywhere. Think Warren and the others know this 

TGT 🐈 - Dividend next moth, big dividend stock. Around now is a good time to load up IMO

IREN 🐈 - Huge GW, expect mag7 or similar deal. 

WYFI - Any neocloud is a buy (eg. see thesis on mag7 funneling revenue down toward these small 1B-5B companies)

WULF - neocloud play

CIFR - neocloud play

SLNH - neocloud play

BITF - neocloud play

GLXY - neocloud derivative play

FLNC - neocloud energy play

MU - China derisked, memory had a huge market there, memory also likely going to get re-rating in tdata center buildout

_

Sell

ETH - Not a fan of Ethereum at $4k+
BMNR - If I don't like Ethereum at these levels, no point of holding treasury companies 
PL - Low revenue, space stock (extremely high valuation)
BLSKY -Low revenue, space stock (extremely high valuation)
RGTI - Quantum bubble
OKLO - Nuclear bubble
IONQ -Quantum bubble 
QBTS - Quantum bubble

_

Quick macro heads up:
-> Rate cut in 9 days ~97% odds. Frontrunning expected, go long.  That's all.
```
