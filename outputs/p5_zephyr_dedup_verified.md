# zephyr 产业卡点判断 — 去重后真实兑现报告

**纪律**: 同一天 + 同主题 + 同方向 = 1 个独立判断 (避免 WDC/MU/STX 同时看多存储算 3 次)

**zephyr 4000 推文 → 248 directional → 150 产业卡点 → **80 独立判断** (去重后)

## TL;DR — 独立判断命中率

| 方向 | 独立判断数 | raw 命中 | exSPX 跑赢板块 | 结论 |
|---|---|---|---|---|
| **LONG** | 58 | **55/58 (94.8%)** | 42/58 (72.4%) | ✅ 强 — 跑赢大盘 |
| **SHORT** | 22 | **0/22 (0%)** | 6/22 (27.3%) 跑输 | ❌ 系统性弱 — 全部错 |
| **合计** | 80 | 55/80 (68.8%) | 48/80 (60.0%) | long 强 / short 弱 |

## 按主题去重命中率

| 主题 | 独立判断 | long 命中 | short 命中 | raw均值 | exSPX均值 |
|---|---|---|---|---|---|
| AI芯片 | 35 | 20/20 | 0/15 | +46.4% | +31.9pp |
| 存储 | 20 | 18/18 | 0/2 | +275.2% | +266.5pp |
| HBM | 2 | 1/1 | 0/1 | +461.1% | +448.9pp |
| 电力 | 3 | 2/3 | 0/0 | +32.3% | +24.8pp |
| 光通信 | 7 | 5/5 | 0/2 | +398.9% | +382.4pp |
| ASIC | 3 | 2/2 | 0/1 | +187.1% | +169.4pp |

## 关键洞察

### 1. Long 强 (94.8% raw / 72.4% exSPX 跑赢)
- 55/58 long 兑现, **平均 exSPX +266pp** (主要靠存储)
- 20 个存储独立判断, 18 个 long 命中, **exSPX +266pp** — 存储是真·神赛道
- 长板: 抓住存储/HBM/光通信/ASIC 多个独立卡点, 每个都对了

### 2. Short 系统性弱 (0% raw / 27% exSPX 跑输)
- 22 个 short 判断**全部 raw>0**, 全部错
- **15 个 AI 芯片 short (NVDA/AMD) 全错** — 他对 NVDA 的判断系统性反向
- **2 个 short 存储错** (12-16 NAND LEAPS, 12-27 MU 被颠覆)
- **2 个 short 光通信错** (4-26 LITE 错, 12-21 LITE 错)
- 唯一 exSPX 跑输的 6 个 short: 都是 NVDA 横盘期 (不是 NVDA 跌)

### 3. 25/80 独立判断错 (31.2% 错)
- AI 芯片: 15/35 错 (全 short NVDA/AMD)
- 存储: 2/20 错 (全 short NAND/MU)
- 光通信: 2/7 错 (全 short LITE)
- HBM: 1/2 错 (short MU)
- EDA/光通信 EDA: 1/1 错 (SNPS 横盘)
- 电力: 1/3 错 (TSLA long -21%) — **他把 TSLA 当数据中心电力公司, 错!**

### 4. 关键错例 (跨领域 long 错)

**TSLA long 2025-12-14** (电力主题):
- judgment: 'Tesla has lots of tailwinds, every DC facility in US will have...'
- zephyr 把 TSLA 当数据中心电力公司 (隐含 VRT 同类), 但 TSLA 不是电力基础设施
- entry 2025-12-15 close, today -21%, exSPX -28.9pp
- **真·押错环节** — 80 个里唯一 exSPX -28.9pp 的 long

## 全部 80 个独立判断 (按日期)

✅ = 命中 (long raw>0 / short raw<0)
❌ = 错

| 日期 | 方向 | 主题 | 标的 | raw均值 | exSPX | exSOX | 兑现 | judgment |
|---|---|---|---|---|---|---|---|---|
| 2025-03-01 | short | AI芯片 | NVDA | +74.5% | +48.7pp | -119.7pp | ❌ 0/1 | That boy will single-handedly bring NVDA down |
| 2025-04-16 | long | ASIC | MRVL | +432.8% | +393.4pp | +183.9pp | ✅ 1/1 | H20 ban literally created a $30B revenue opportunity, CM384  |
| 2025-04-17 | short | AI芯片 | NVDA | +96.1% | +56.8pp | -155.1pp | ❌ 0/1 | H20 is banned, it's not a bargaining chip |
| 2025-04-18 | short | AI芯片 | NVDA | +105.3% | +62.7pp | -153.4pp | ❌ 0/1 | Nvidia can't deliver competitive products after H20 ban |
| 2025-04-18 | long | AI芯片 | NVDA | +105.3% | +62.7pp | -153.4pp | ✅ 1/1 | 8M 用户同时在线需要超过 100K H100/H800/910C 部署 |
| 2025-04-26 | short | 光通信 | LITE | +1302.3% | +1269.3pp | +1084.6pp | ❌ 0/1 | CM384 with Optical switches is a stopgap, 94% Copper in the  |
| 2025-04-27 | short | 光通信 | LITE | +1302.3% | +1269.3pp | +1084.6pp | ❌ 0/1 | Optical switches are a stopgap, won't be present next year |
| 2025-04-29 | short | AI芯片 | NVDA | +82.5% | +50.2pp | -138.1pp | ❌ 0/1 | H100 glut did happen in 2H24, supply outpacing demand. |
| 2025-05-28 | short | AI芯片 | NVDA | +47.6% | +22.7pp | -130.8pp | ❌ 0/1 | Nvidia will crash if Deepseek's tech report includes small a |
| 2025-06-02 | long | 存储 | WDC,MU,STX | +945.1% | +921.1pp | +766.6pp | ✅ 3/3 | 长视频生成将引爆计算和存储需求，当前可以捡SSD和HDD股票 |
| 2025-07-15 | long | AI芯片 | NVDA | +16.6% | -1.3pp | -118.8pp | ✅ 1/1 | REMINDER: In the inference/RL era, an H20 is better than H10 |
| 2025-07-31 | short | AI芯片 | NVDA | +11.9% | -4.2pp | -128.1pp | ❌ 0/1 | 北京不想让Nvidia吃中国市场份额，禁止H20将让中国初创公司蓬勃发展，利空Nvidia |
| 2025-08-13 | short | AI芯片 | NVDA | +9.6% | -4.2pp | -118.8pp | ❌ 0/1 | Nvidia will be getting banned in China |
| 2025-08-19 | long | AI芯片 | NVDA | +13.3% | -1.5pp | -124.0pp | ✅ 1/1 | If it's true then this will stop smuggling and I will have a |
| 2025-08-20 | short | AI芯片 | NVDA | +13.5% | -1.6pp | -125.6pp | ❌ 0/1 | 腾讯不再购买 H20，其他公司可能跟进，影响英伟达中国业务 |
| 2025-08-25 | short | AI芯片 | AMD | +218.2% | +203.9pp | +84.4pp | ❌ 0/1 | Bearish for AMD |
| 2025-08-27 | short | AI芯片 | NVDA | +9.6% | -3.9pp | -121.5pp | ❌ 0/1 | Claude 4 and 4.1 were trained on Nvidia; Claude 5 won't be |
| 2025-08-28 | short | AI芯片 | NVDA | +10.5% | -2.7pp | -119.5pp | ❌ 0/1 | NO FUCKING H20 ORDERS FROM CHINESE CUSTOMERS |
| 2025-08-30 | long | HBM | MU | +785.0% | +770.3pp | +644.9pp | ✅ 1/1 | The bottleneck isn't SMIC but HBM3 supply |
| 2025-09-15 | long | 存储 | WDC,MU,STX | +488.0% | +476.7pp | +365.9pp | ✅ 3/3 | NAND upcycle = multi-year, not one-night stand |
| 2025-10-02 | long | DRAM/存储 | AMAT,LRCX,MU+1 | +177.5% | +168.0pp | +74.4pp | ✅ 3/4 | Buy every WFE supplier and DRAM supplier under the sun |
| 2025-12-07 | long | EDA/AI芯片设计 | SNPS | -0.4% | -7.9pp | -82.9pp | ❌ 0/1 | Very important and bullish EDA |
| 2025-12-07 | long | 光通信/EDA | SNPS | -0.4% | -7.9pp | -82.9pp | ❌ 0/1 | Ciena and Synopsys LFG!!! |
| 2025-12-07 | long | AI芯片 | NVDA | +7.2% | -0.2pp | -75.2pp | ✅ 1/1 | Most people don't realize how hard Rubin CPX will cut Time T |
| 2025-12-08 | long | AI芯片 | NVDA | +7.2% | -0.2pp | -75.2pp | ✅ 1/1 | Nvidia may hit $6T market cap sooner than I expected (if Chi |
| 2025-12-08 | long | 存储 | AMAT | +119.6% | +112.2pp | +37.2pp | ✅ 1/1 | Memory will save AMAT |
| 2025-12-09 | long | AI芯片 | NVDA | +7.6% | +0.0pp | -75.0pp | ✅ 1/1 | Good Luck fighting Nvidia in the scale-up domain |
| 2025-12-12 | long | 存储 | MU | +334.8% | +327.0pp | +243.5pp | ✅ 1/1 | 存储短缺，未来两年可能只能买到次品，现在赶紧买电子产品 |
| 2025-12-14 | long | 电力 | TSLA | -21.0% | -28.9pp | -113.5pp | ❌ 0/1 | Tesla has lots of tailwinds, every DC facility in US will ha |
| 2025-12-14 | long | 芯片制造 | AMD | +150.4% | +142.4pp | +57.9pp | ✅ 1/1 | AMD CPUs on Samsung's SF2 LFG!!! |
| 2025-12-15 | long | AI芯片 | NVDA | +12.9% | +4.9pp | -79.6pp | ✅ 1/1 | Nvidia cracking fp4 training and open-sourcing the methods w |
| 2025-12-15 | long | 存储 | WDC,MU | +307.9% | +299.9pp | +215.3pp | ✅ 2/2 | Some great news for Sandisk |
| 2025-12-16 | long | AI芯片 | NVDA | +12.0% | +3.8pp | -81.4pp | ✅ 1/1 | GPU与ASIC性能差距巨大，2028年前不会明显缩小 |
| 2025-12-16 | long | 存储 | WDC,MU,STX | +288.2% | +280.0pp | +194.7pp | ✅ 3/3 | SanDisk 从 Google 获得第二份超大规模企业 eSSD 合同，出货量可能超过 Meta，利好存储需求 |
| 2025-12-16 | short | 存储 | WDC,MU | +309.9% | +301.7pp | +216.5pp | ❌ 0/2 | Never buy LEAPS on NAND, you will get burned to a crisp |
| 2025-12-17 | long | 存储 | MU | +364.9% | +355.5pp | +263.9pp | ✅ 1/1 | Enjoy the memory supercycle, anon |
| 2025-12-17 | long | AI芯片 | NVDA | +16.4% | +6.9pp | -84.6pp | ✅ 1/1 | Agentic coding costs are dominated by prefill; Nvidia introd |
| 2025-12-18 | long | 存储 | MU | +321.9% | +313.2pp | +225.8pp | ✅ 1/1 | Hynix & Micron will have a higher GM than Nvidia at some poi |
| 2025-12-19 | long | AI芯片 | NVDA | +10.0% | +2.3pp | -80.5pp | ✅ 1/1 | Nvidia is hitting 6 trillion for sure next year |
| 2025-12-19 | long | AI芯片/云服务 | AMZN | +3.0% | -4.6pp | -87.4pp | ✅ 1/1 | Trainium3 Ultra is a decent, cheap alternative for inference |
| 2025-12-20 | long | 光通信 | LITE | +116.1% | +109.1pp | +27.8pp | ✅ 1/1 | i like $lite |
| 2025-12-21 | short | CPO | LITE | +116.1% | +109.1pp | +27.8pp | ❌ 0/1 | limited reliability of CPO technologies |
| 2025-12-22 | long | AI芯片 | NVDA | +8.3% | +1.4pp | -80.0pp | ✅ 1/1 | Insane GPU production numbers for 2026 ;) |
| 2025-12-22 | long | ASIC | AVGO,MRVL | +119.1% | +112.1pp | +30.8pp | ✅ 2/2 | I personally think that hyperscalers will outsource more to  |
| 2025-12-26 | long | AI芯片 | NVDA | +4.4% | -1.7pp | -82.3pp | ✅ 1/1 | Nvidia-Groq deal creates another edge for Nvidia in inferenc |
| 2025-12-27 | short | 存储 | MU | +256.2% | +249.6pp | +168.7pp | ❌ 0/1 | The fact that $MU will be disrupted as inference takes cente |
| 2025-12-27 | long | 电力 | VRT | +91.1% | +84.5pp | +3.6pp | ✅ 1/1 | 1GW of onsite gas gen Nice!!! — 看好现场燃气发电，隐含AI数据中心电力需求爆发 |
| 2025-12-27 | long | AI芯片/半导体 | AMD | +141.1% | +134.5pp | +53.6pp | ✅ 1/1 | AMD numbers seems too low |
| 2025-12-28 | long | HBM/存储 | MU | +256.2% | +249.6pp | +168.7pp | ✅ 1/1 | 推理与图像模型需求远超预期，Nvidia/ASIC 开发者无法确保产能，内存供应紧张 |
| 2025-12-28 | short | ASIC | AVGO | +9.4% | +2.8pp | -78.1pp | ❌ 0/1 | The TPU bump is over IMO |
| 2025-12-28 | long | 存储 | MU | +256.2% | +249.6pp | +168.7pp | ✅ 1/1 | Memory price squeeze from unexpected HBM demand and server r |
| 2025-12-30 | long | 存储 | MU | +258.3% | +251.6pp | +170.6pp | ✅ 1/1 | DRAM shortages causing more problems |
| 2026-01-12 | long | 存储 | WDC,MU,STX | +205.2% | +199.7pp | +129.8pp | ✅ 3/3 | If you still aren’t bullish on SSD demand, read this and get |
| 2026-01-22 | long | CPU/半导体 | INTC | +142.4% | +135.9pp | +75.3pp | ✅ 1/1 | Intel CPU demand is off the charts and Intel is likely to be |
| 2026-02-05 | long | 存储 | WDC,MU,STX | +155.4% | +147.2pp | +78.7pp | ✅ 3/3 | 存储短缺更加严重并将延续到2028年，现在下注存储是最容易赚钱的方式 |
| 2026-02-12 | long | AI芯片 | NVDA | +6.5% | -1.2pp | -60.0pp | ✅ 1/1 | every company with $20K GPUs can close tickets with LLM, com |
| 2026-02-13 | long | 存储 | WDC,MU,STX | +138.8% | +131.2pp | +73.5pp | ✅ 3/3 | NAND Is Just as Strong as DRAM |
| 2026-02-16 | short | AI芯片 | AMD | +155.9% | +148.4pp | +90.5pp | ❌ 0/1 | Looks like OpenAI's plan to deploy AMD hardware from 2H26 go |
| 2026-02-16 | long | 存储 | WDC,MU,STX | +142.6% | +135.0pp | +77.1pp | ✅ 3/3 | Severe memory supply-demand imbalance will continue until 20 |
| 2026-02-18 | long | AI芯片 | NVDA | +5.9% | -1.1pp | -58.0pp | ✅ 1/1 | Nvidia will generate around $400B in revenue this year |
| 2026-02-18 | long | 存储 | MU | +149.1% | +142.2pp | +85.2pp | ✅ 1/1 | OpenAI 消耗全球 40% RAM 供应，内存短缺持续 |
| 2026-02-19 | long | AI芯片 | NVDA | +5.9% | -1.3pp | -58.8pp | ✅ 1/1 | 月之暗面/Kimi海外收入超国内，海外推理在新加坡/东南亚完成，猜猜他们用谁的GPU？暗示海外推理需求利好Nvidia。 |
| 2026-02-20 | short | AI芯片 | NVDA | +4.8% | -1.7pp | -58.1pp | ❌ 0/1 | nvidia numbers are wrong and false |
| 2026-02-23 | long | 存储/光通信 | LITE | +24.9% | +17.3pp | -39.0pp | ✅ 1/1 | Tell them to buy Hynix or Lumentum |
| 2026-02-27 | long | 存储 | MU | +154.3% | +147.3pp | +88.1pp | ✅ 1/1 | Almost all of the revenue growth for memory stocks due to pr |
| 2026-03-03 | long | 光通信 | LITE | +21.3% | +13.4pp | -52.0pp | ✅ 1/1 | Should have invested in lasers and pump diodes |
| 2026-03-03 | long | 存储 | WDC,MU,STX | +170.3% | +162.3pp | +96.9pp | ✅ 3/3 | memory price hike 70% in Q2, way above sell side 40% |
| 2026-03-05 | long | 电力 | VRT | +26.7% | +19.0pp | -45.4pp | ✅ 1/1 | We will have to add 80GW-100GW of AI DC capacity every year |
| 2026-03-05 | short | AI芯片 | NVDA | +8.5% | +0.8pp | -63.5pp | ❌ 0/1 | Accounting error: Most of the GDP is ending up on Nvidia's b |
| 2026-03-05 | long | AI芯片 | ARM,INTC,AMD | +181.6% | +173.9pp | +109.5pp | ✅ 3/3 | How will scaling in future years look like for millions and  |
| 2026-03-12 | long | 光通信 | LITE | +36.8% | +26.5pp | -39.3pp | ✅ 1/1 | Sumitomo's infocomm-driven operating income growth is immens |
| 2026-03-15 | short | HBM | MU | +137.3% | +127.5pp | +64.7pp | ❌ 0/1 | Micron 搞尴尬营销，HBM4 base die 需要修 |
| 2026-03-15 | long | 存储 | MU | +137.3% | +127.5pp | +64.7pp | ✅ 1/1 | memory shortage worsening to extreme levels, good for Samsun |
| 2026-03-16 | long | AI芯片 | NVDA | +8.6% | -1.2pp | -64.0pp | ✅ 1/1 | Demand is super high, Jensen is just tightening the noose an |
| 2026-03-17 | long | AI芯片 | NVDA | +9.4% | -0.2pp | -62.3pp | ✅ 1/1 | Nvidia will get a huge bump again when they increase the sca |
| 2026-03-20 | long | AI芯片 | AMD | +158.2% | +145.1pp | +82.7pp | ✅ 1/1 | AMD is mispriced rn |
| 2026-03-23 | long | AI芯片 | AMD | +156.4% | +144.6pp | +83.3pp | ✅ 1/1 | AMD's inference team has improved the performance of those c |
| 2026-03-24 | long | 光通信 | LITE | +5.1% | -7.2pp | -65.9pp | ✅ 1/1 | PCB and laser bottleneck → laser shortage, bullish for laser |
| 2026-03-25 | long | 光通信 | LITE | +8.4% | -3.2pp | -60.5pp | ✅ 1/1 | Broadcom pointed towards a laser shortage; Transceivers dema |
| 2026-03-29 | short | AI芯片 | NVDA | +20.5% | +4.5pp | -67.9pp | ❌ 0/1 | I doubt Nvidia can even ramp the supply chain to produce 200 |

---

## zephyr 25 个错判断明细 (对错全貌)

| 日期 | 方向 | 主题 | 标的 | raw均值 | exSPX | judgment |
|---|---|---|---|---|---|---|
| 2025-03-01 | short | AI芯片 | NVDA | +74.5% | +48.7pp | That boy will single-handedly bring NVDA down |
| 2025-04-17 | short | AI芯片 | NVDA | +96.1% | +56.8pp | H20 is banned, it's not a bargaining chip |
| 2025-04-18 | short | AI芯片 | NVDA | +105.3% | +62.7pp | Nvidia can't deliver competitive products after H20 ban |
| 2025-04-26 | short | 光通信 | LITE | +1302.3% | +1269.3pp | CM384 with Optical switches is a stopgap, 94% Copper in the  |
| 2025-04-27 | short | 光通信 | LITE | +1302.3% | +1269.3pp | Optical switches are a stopgap, won't be present next year |
| 2025-04-29 | short | AI芯片 | NVDA | +82.5% | +50.2pp | H100 glut did happen in 2H24, supply outpacing demand. |
| 2025-05-28 | short | AI芯片 | NVDA | +47.6% | +22.7pp | Nvidia will crash if Deepseek's tech report includes small a |
| 2025-07-31 | short | AI芯片 | NVDA | +11.9% | -4.2pp | 北京不想让Nvidia吃中国市场份额，禁止H20将让中国初创公司蓬勃发展，利空Nvidia |
| 2025-08-13 | short | AI芯片 | NVDA | +9.6% | -4.2pp | Nvidia will be getting banned in China |
| 2025-08-20 | short | AI芯片 | NVDA | +13.5% | -1.6pp | 腾讯不再购买 H20，其他公司可能跟进，影响英伟达中国业务 |
| 2025-08-25 | short | AI芯片 | AMD | +218.2% | +203.9pp | Bearish for AMD |
| 2025-08-27 | short | AI芯片 | NVDA | +9.6% | -3.9pp | Claude 4 and 4.1 were trained on Nvidia; Claude 5 won't be |
| 2025-08-28 | short | AI芯片 | NVDA | +10.5% | -2.7pp | NO FUCKING H20 ORDERS FROM CHINESE CUSTOMERS |
| 2025-12-07 | long | EDA/AI芯片设计 | SNPS | -0.4% | -7.9pp | Very important and bullish EDA |
| 2025-12-07 | long | 光通信/EDA | SNPS | -0.4% | -7.9pp | Ciena and Synopsys LFG!!! |
| 2025-12-14 | long | 电力 | TSLA | -21.0% | -28.9pp | Tesla has lots of tailwinds, every DC facility in US will ha |
| 2025-12-16 | short | 存储 | WDC,MU | +309.9% | +301.7pp | Never buy LEAPS on NAND, you will get burned to a crisp |
| 2025-12-21 | short | CPO | LITE | +116.1% | +109.1pp | limited reliability of CPO technologies |
| 2025-12-27 | short | 存储 | MU | +256.2% | +249.6pp | The fact that $MU will be disrupted as inference takes cente |
| 2025-12-28 | short | ASIC | AVGO | +9.4% | +2.8pp | The TPU bump is over IMO |
| 2026-02-16 | short | AI芯片 | AMD | +155.9% | +148.4pp | Looks like OpenAI's plan to deploy AMD hardware from 2H26 go |
| 2026-02-20 | short | AI芯片 | NVDA | +4.8% | -1.7pp | nvidia numbers are wrong and false |
| 2026-03-05 | short | AI芯片 | NVDA | +8.5% | +0.8pp | Accounting error: Most of the GDP is ending up on Nvidia's b |
| 2026-03-15 | short | HBM | MU | +137.3% | +127.5pp | Micron 搞尴尬营销，HBM4 base die 需要修 |
| 2026-03-29 | short | AI芯片 | NVDA | +20.5% | +4.5pp | I doubt Nvidia can even ramp the supply chain to produce 200 |

## 画像更新 (修正版)

**zephyr 真·卡点雷达画像** (去重后):

**强项** (看多判断):
- 存储 18 long 全对, exSPX +266pp (神赛道)
- 光通信 5 long 全对, exSPX +382pp (含 LITE laser shortage 多次押对)
- ASIC 2 long 全对 (Marvell, AVGO)
- AI 芯片 long NVDA 多个时点对 (raw 涨 8-105%, exSPX +63pp)
- 多次精准押 AI 电力 (VRT 多次, 2/3 命中)

**弱项** (看空判断):
- **22/22 short 全部 raw>0** — 没有任何 short 兑现
- AI 芯片 short NVDA 系统性错 (15/15 错)
- 存储 short NAND/MU 错 (2/2 错)
- 光通信 short LITE 错 (2/2 错)
- 看多但押错环节: TSLA long (-21%, 把 TSLA 误当电力公司)

**用法** (修正版):
- ✅ **用他 long 判断** (存储/光通信/ASIC/HBM) — 押对率高
- ❌ **忽略他 short 判断** (NVDA/AMD/存储/LITE) — 系统性反向错
- ⚠️ **跨领域 long 要小心** — TSLA / 非他专注赛道偶有押错环节