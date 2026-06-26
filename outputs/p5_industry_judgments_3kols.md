# 3 人产业判断清单 (新标准: 不需 buy/sell 关键词, 只要有方向+可证伪+对应标的)

**抽 199 推文, LLM 抽 49 有效判断 (25%)**
- @fi56622380: 90 抽样 → **24 judgments** (27%)
- @austinsemis: 61 抽样 → **17 judgments** (28%)
- @zephyr_z9: 48 抽样 → **8 judgments** (17%)

**标注** (今天 = 2026-06-25):
- ✅ 已 resolved: 推文 ≥ 90d 前, 已有足够时间让市场反应
- 🟡 部分 resolved: 30-90d, 短期走势可能显示但不稳
- ❌ 仍 pending: < 30d, 完全太新

**市场分布**:
- @fi56622380: 21 US + 2 US/KR (HBM) + 1 KR (Hynix)
- @austinsemis: 17 US 全部
- @zephyr_z9: 5 US + 1 US/HK + 1 DE (Siemens) + 1 US/KR

---

## @fi56622380 (24 judgments)

| # | 日期 | 状态 | 类型 | 方向 | 标的 (市场) | 原文 (核心句) | 推导逻辑 |
|---|---|---|---|---|---|---|---|
| 1 | 2024-01-07 | ✅ resolved | LONG (high) | long | MU (US) | 也许2026之后会升级成主流13B的模型，占用8GB内存（感觉利好存储厂商） | 手机终端升级至13B模型需更大内存，直接利好存储芯片厂商，美股对应美光(MU) |
| 2 | 2024-02-20 | ✅ resolved | SHORT (high) | short | GOOGL (US) | 以后碰到Google的产品都绕着走，CEO拉跨，不看好Google股票 | 推文明确表示将避开Google产品，并因CEO表现看空其股票，直接对应Alphabet (GOOGL/GOOG) |
| 3 | 2024-02-20 | ✅ resolved | LONG (high) | long | AMZN (US) | 还不如买亚马逊 | 原文对比Google后表示更看好亚马逊，直接对应Amazon (AMZN) |
| 4 | 2024-04-04 | ✅ resolved | SHORT (medium) | short | NVDA,AMD (US) | 过去一年，各个公司一共买了50B GPU，产生了3B的营收。看投资人的耐心能到什么时候，一般不超过24个月，除非营收两年翻几倍，那还能继续维持下去 | 暗示若AI投入产出比低，可能导致GPU采购需求下降，利空主要GPU供应商NVDA和AMD。 |
| 5 | 2024-04-20 | ✅ resolved | TECHNICAL (medium) | long | GOOGL (US) | 安卓阵营的语音助理的泛化能力和协同各个app的能力以后必然会大幅拓展 | 安卓生态和AI助手由Google主导，Gemini小模型强化将直接受益于安卓端侧AI能力拓展 |
| 6 | 2024-06-14 | ✅ resolved | LONG (medium) | long | TSLA (US) | optimus人形机器人，在2040年左右是有希望到范式转移质变阶段的 | Optimus is Tesla's humanoid robot project; the judgment impl |
| 7 | 2024-07-29 | ✅ resolved | LONG (medium) | long | AVGO (US) | 猜测多半要跟Broadcom合作 | 推文猜测OpenAI多半会与Broadcom合作，对Broadcom是利好，因此看多Broadcom。 |
| 8 | 2024-10-03 | ✅ resolved | SHORT (high) | short | TSLA (US) | it's going to be postponed again and again, no major improvement on critical eng | 推文暗示特斯拉FSD进展延迟且关键接管率无实质改善，看空特斯拉自动驾驶技术前景，直接利空TSLA股价 |
| 9 | 2025-03-31 | ✅ resolved | SUPPLY/DEMAND (medium) | short | NVDA,AMD (US) | 大厂GPU买的太多导致裁人...东西出来的慢->AI营收上不去，影响买GPU的速度 | 大厂是GPU主要采购方，若因AI营收不及预期而放缓采购，将影响GPU供应商如NVDA、AMD的业绩。 |
| 10 | 2025-06-04 | ✅ resolved | TECHNICAL (medium) | long | QCOM,ARM,2454.TW (US) | 在端侧AI上我认为会比10年要小 | 端侧AI爆发时间差小于10年，利好移动端AI芯片厂商，如高通(QCOM)、ARM(ARM)和联发科(2454.TW) |
| 11 | 2025-06-08 | ✅ resolved | TECHNICAL (medium) | long | QCOM (US) | 2027年之前主流AI眼镜一般都会用高通的AR1gen1方案 | Qualcomm提供AR1gen1芯片，若成为主流AI眼镜方案，高通将受益。 |
| 12 | 2025-08-30 | ✅ resolved | COMPETITIVE (high) | long | AAPL (US) | Apple in AI age is like Microsoft in cloud age, late in the game, but still will | The tweet explicitly states Apple will be competitive in AI  |
| 13 | 2025-11-11 | ✅ resolved | LONG (medium) | long | NVDA (US) | 在算力紧缺供不应求的时代，前代GPU（如H100/A100）得不到利用从而报废的担心，在短期内可能都不是太大问题，残值仍然不错。 | 推文以H100和A100为例，说明老款NVIDIA GPU残值高、租赁需求持续，间接表明NVIDIA产品生命周期长、需求 |
| 14 | 2025-12-01 | ✅ resolved | MACRO (medium) | short | COIN,MSTR,MARA,RIOT (US) | the next BTC bottom could be Q3/Q4 2026 | BTC price bottom prediction implies potential downside press |
| 15 | 2025-12-01 | ✅ resolved | LONG (high) | long | AVGO (US) | 半导体公司里最有希望的就是AVGO了 | 明说 |
| 16 | 2025-12-01 | ✅ resolved | COMPETITIVE (high) | short | MU (US) | 存储里，micron相比起来技术还是差点 | 直接指出Micron技术落后，看空 |
| 17 | 2025-12-01 | ✅ resolved | COMPETITIVE (medium) | long | 000660.KS (KR) | 有希望达到这一点的只有Hynix，但是Hynix是韩国公司，所以估值会有限 | 指出SK Hynix有希望达到技术领先，但估值受市场限制，仍为偏多判断 |
| 18 | 2025-12-02 | ✅ resolved | COMPETITIVE (medium) | short | AVGO,MRVL (US) | 就算NVDA勉强活下来，所谓ASIC也得完蛋 | ASIC完蛋意味着AI ASIC设计公司业务受损，博通(AVGO)和美满电子(MRVL)是主要AI ASIC服务商。 |
| 19 | 2026-01-24 | ✅ resolved | SUPPLY/DEMAND (high) | long | MU,005930.KS,000660.KS (US/KR) | HBM 的容量与带宽是系统里最稀缺、涨价最快、也最难扩的资源 | HBM稀缺和涨价直接利好HBM供应商美光、三星、SK海力士。 |
| 20 | 2026-02-19 | ✅ resolved | LONG (medium) | long | NVDA (US) | 老黄底气太足了 | 老黄指NVIDIA CEO黄仁勋，底气太足暗示NVIDIA业务强劲，因此看多NVDA |
| 21 | 2026-02-25 | ✅ resolved | MACRO (medium) | long | NVDA,AMD,AVGO (US) | compute is eating the world | 'compute is eating the world' 暗示计算需求持续增长，利好计算基础设施供应商如NVDA, A |
| 22 | 2026-03-05 | ✅ resolved | LONG (high) | long | ARM (US) | ARM’s data center revenue CAGR should be at least 50% over the next five years,  | Direct mention of ARM with bullish outlook on data center re |
| 23 | 2026-04-17 | 🟡 30-90d | LONG (high) | long | MU,005930.KS,000660.KS (US/KR) | 现在的HBM，就是24年的NVDA | HBM比作2024年的英伟达，看多HBM需求，受益公司为HBM主要供应商：美光(MU)、三星电子(005930.KS)、 |
| 24 | 2026-05-17 | 🟡 30-90d | LONG (high) | long | NVDA,MU (US) | Nvidia's LPDDR usage for a single product exceeds total smartphone consumption,  | Nvidia's massive LPDDR demand signals strong AI product ramp |

**逐条原文 (含上下文)**:

**1. [2024-01-07] ✅ resolved LONG → MU (US)**
> 也许2026之后会升级成主流13B的模型，占用8GB内存（感觉利好存储厂商）
>
> *推导: 手机终端升级至13B模型需更大内存，直接利好存储芯片厂商，美股对应美光(MU)*
>
> type=LONG confidence=high

**2. [2024-02-20] ✅ resolved SHORT → GOOGL (US)**
> 以后碰到Google的产品都绕着走，CEO拉跨，不看好Google股票
>
> *推导: 推文明确表示将避开Google产品，并因CEO表现看空其股票，直接对应Alphabet (GOOGL/GOOG)*
>
> type=SHORT confidence=high

**3. [2024-02-20] ✅ resolved LONG → AMZN (US)**
> 还不如买亚马逊
>
> *推导: 原文对比Google后表示更看好亚马逊，直接对应Amazon (AMZN)*
>
> type=LONG confidence=high

**4. [2024-04-04] ✅ resolved SHORT → NVDA,AMD (US)**
> 过去一年，各个公司一共买了50B GPU，产生了3B的营收。看投资人的耐心能到什么时候，一般不超过24个月，除非营收两年翻几倍，那还能继续维持下去
>
> *推导: 暗示若AI投入产出比低，可能导致GPU采购需求下降，利空主要GPU供应商NVDA和AMD。*
>
> type=SHORT confidence=medium

**5. [2024-04-20] ✅ resolved LONG → GOOGL (US)**
> 安卓阵营的语音助理的泛化能力和协同各个app的能力以后必然会大幅拓展
>
> *推导: 安卓生态和AI助手由Google主导，Gemini小模型强化将直接受益于安卓端侧AI能力拓展*
>
> type=TECHNICAL confidence=medium

**6. [2024-06-14] ✅ resolved LONG → TSLA (US)**
> optimus人形机器人，在2040年左右是有希望到范式转移质变阶段的
>
> *推导: Optimus is Tesla's humanoid robot project; the judgment implies Tesla will successfully achieve a paradigm shift in humanoid robots by ~2040, which would benefit TSLA.*
>
> type=LONG confidence=medium

**7. [2024-07-29] ✅ resolved LONG → AVGO (US)**
> 猜测多半要跟Broadcom合作
>
> *推导: 推文猜测OpenAI多半会与Broadcom合作，对Broadcom是利好，因此看多Broadcom。*
>
> type=LONG confidence=medium

**8. [2024-10-03] ✅ resolved SHORT → TSLA (US)**
> it's going to be postponed again and again, no major improvement on critical engagement rate, still an order of magnitude away, unless he hires a lot of safety driver behind the scene
>
> *推导: 推文暗示特斯拉FSD进展延迟且关键接管率无实质改善，看空特斯拉自动驾驶技术前景，直接利空TSLA股价*
>
> type=SHORT confidence=high

**9. [2025-03-31] ✅ resolved SHORT → NVDA,AMD (US)**
> 大厂GPU买的太多导致裁人...东西出来的慢->AI营收上不去，影响买GPU的速度
>
> *推导: 大厂是GPU主要采购方，若因AI营收不及预期而放缓采购，将影响GPU供应商如NVDA、AMD的业绩。*
>
> type=SUPPLY/DEMAND confidence=medium

**10. [2025-06-04] ✅ resolved LONG → QCOM,ARM,2454.TW (US)**
> 在端侧AI上我认为会比10年要小
>
> *推导: 端侧AI爆发时间差小于10年，利好移动端AI芯片厂商，如高通(QCOM)、ARM(ARM)和联发科(2454.TW)*
>
> type=TECHNICAL confidence=medium

**11. [2025-06-08] ✅ resolved LONG → QCOM (US)**
> 2027年之前主流AI眼镜一般都会用高通的AR1gen1方案
>
> *推导: Qualcomm提供AR1gen1芯片，若成为主流AI眼镜方案，高通将受益。*
>
> type=TECHNICAL confidence=medium

**12. [2025-08-30] ✅ resolved LONG → AAPL (US)**
> Apple in AI age is like Microsoft in cloud age, late in the game, but still will be competitive later because of the huge advantage in ecosystem distribution compare to Android market(fragmented NPU HW and poor SDK support)
>
> *推导: The tweet explicitly states Apple will be competitive in AI due to ecosystem advantages, directly implying a bullish view on Apple (AAPL).*
>
> type=COMPETITIVE confidence=high

**13. [2025-11-11] ✅ resolved LONG → NVDA (US)**
> 在算力紧缺供不应求的时代，前代GPU（如H100/A100）得不到利用从而报废的担心，在短期内可能都不是太大问题，残值仍然不错。
>
> *推导: 推文以H100和A100为例，说明老款NVIDIA GPU残值高、租赁需求持续，间接表明NVIDIA产品生命周期长、需求强劲，利好NVDA。*
>
> type=LONG confidence=medium

**14. [2025-12-01] ✅ resolved SHORT → COIN,MSTR,MARA,RIOT (US)**
> the next BTC bottom could be Q3/Q4 2026
>
> *推导: BTC price bottom prediction implies potential downside pressure on crypto-related stocks such as Coinbase, MicroStrategy, and mining companies.*
>
> type=MACRO confidence=medium

**15. [2025-12-01] ✅ resolved LONG → AVGO (US)**
> 半导体公司里最有希望的就是AVGO了
> *推导: *
>
> type=LONG confidence=high

**16. [2025-12-01] ✅ resolved SHORT → MU (US)**
> 存储里，micron相比起来技术还是差点
>
> *推导: 直接指出Micron技术落后，看空*
>
> type=COMPETITIVE confidence=high

**17. [2025-12-01] ✅ resolved LONG → 000660.KS (KR)**
> 有希望达到这一点的只有Hynix，但是Hynix是韩国公司，所以估值会有限
>
> *推导: 指出SK Hynix有希望达到技术领先，但估值受市场限制，仍为偏多判断*
>
> type=COMPETITIVE confidence=medium

**18. [2025-12-02] ✅ resolved SHORT → AVGO,MRVL (US)**
> 就算NVDA勉强活下来，所谓ASIC也得完蛋
>
> *推导: ASIC完蛋意味着AI ASIC设计公司业务受损，博通(AVGO)和美满电子(MRVL)是主要AI ASIC服务商。*
>
> type=COMPETITIVE confidence=medium

**19. [2026-01-24] ✅ resolved LONG → MU,005930.KS,000660.KS (US/KR)**
> HBM 的容量与带宽是系统里最稀缺、涨价最快、也最难扩的资源
>
> *推导: HBM稀缺和涨价直接利好HBM供应商美光、三星、SK海力士。*
>
> type=SUPPLY/DEMAND confidence=high

**20. [2026-02-19] ✅ resolved LONG → NVDA (US)**
> 老黄底气太足了
>
> *推导: 老黄指NVIDIA CEO黄仁勋，底气太足暗示NVIDIA业务强劲，因此看多NVDA*
>
> type=LONG confidence=medium

**21. [2026-02-25] ✅ resolved LONG → NVDA,AMD,AVGO (US)**
> compute is eating the world
>
> *推导: 'compute is eating the world' 暗示计算需求持续增长，利好计算基础设施供应商如NVDA, AMD, AVGO等。*
>
> type=MACRO confidence=medium

**22. [2026-03-05] ✅ resolved LONG → ARM (US)**
> ARM’s data center revenue CAGR should be at least 50% over the next five years, and its share of hyperscaler server CPU will only go up.
>
> *推导: Direct mention of ARM with bullish outlook on data center revenue growth and server CPU share increase.*
>
> type=LONG confidence=high

**23. [2026-04-17] 🟡 30-90d LONG → MU,005930.KS,000660.KS (US/KR)**
> 现在的HBM，就是24年的NVDA
>
> *推导: HBM比作2024年的英伟达，看多HBM需求，受益公司为HBM主要供应商：美光(MU)、三星电子(005930.KS)、SK海力士(000660.KS)*
>
> type=LONG confidence=high

**24. [2026-05-17] 🟡 30-90d LONG → NVDA,MU (US)**
> Nvidia's LPDDR usage for a single product exceeds total smartphone consumption, invest only in silicon-based consumption
>
> *推导: Nvidia's massive LPDDR demand signals strong AI product ramp, directly benefiting NVDA and memory suppliers like MU; broader silicon investment theme also bullish for semi stocks.*
>
> type=LONG confidence=high

## @austinsemis (17 judgments)

| # | 日期 | 状态 | 类型 | 方向 | 标的 (市场) | 原文 (核心句) | 推导逻辑 |
|---|---|---|---|---|---|---|---|
| 1 | 2024-03-18 | ✅ resolved | LONG (high) | long | NVDA (US) | Nvidia is solving for more of the customer’s job-to-be-done here. This expansion | Nvidia's platform expansion creates lock-in and switching co |
| 2 | 2024-04-02 | ✅ resolved | COMPETITIVE (high) | long | AMD,NVDA (US) | Nvidia CUDA’s moat is surmountable &amp; how AMD can overcome their software woe | 推文明确表示AMD将能克服软件问题并与Nvidia竞争，直接看好AMD，同时暗示Nvidia的CUDA护城河不再牢不可破 |
| 3 | 2025-03-05 | ✅ resolved | LONG (high) | long | NVDA (US) | Long lifespans could mean better TCO as Blackwell dominates. | 推文直接提及$NVDA，并称Blackwell（Nvidia新架构）主导，长寿命带来更好TCO，对Nvidia是利好。 |
| 4 | 2025-03-18 | ✅ resolved | COMPETITIVE (medium) | long | MRVL,AVGO,NVDA (US) | Custom ASICs can be tailored to have lower latency or higher throughput and ther | ASICs gaining advantage over GPUs would benefit custom ASIC  |
| 5 | 2025-07-11 | ✅ resolved | LONG (high) | long | DELL (US) | Dell can innovate to differentiate and avoid being stuck in low-margin, commodit | 推文直接提及 @Dell，判断为看好 Dell 创新并提升价值链，对应标的 DELL。 |
| 6 | 2025-07-21 | ✅ resolved | SHORT (medium) | short | OCI (US) | Could be a sign the $OCI $30B per year deal won’t deliver either. | 如果$30B per year deal无法实现，将直接负面影响到标的公司$OCI。$OCI可能指Oracle Clou |
| 7 | 2025-08-12 | ✅ resolved | LONG (medium) | long | CRWV (US) | $CRWV seeing a "massive increase" in inference workloads, as validated by watchi | 直接提到 $CRWV 推理工作负载大幅增长，利好公司 |
| 8 | 2025-08-17 | ✅ resolved | SUPPLY/DEMAND (medium) | short | AMAT,LRCX,KLAC (US) | AMAT softening guide due to a leading edge foundry pulling back, indicating lowe | AMAT's softened guidance is attributed to a leading-edge fou |
| 9 | 2025-08-29 | ✅ resolved | SHORT (medium) | short | GOOGL (US) | $GOOGL knows how to sell ads and rent servers. Selling merchant silicon chips is | The tweet questions Google's ability to succeed in the merch |
| 10 | 2025-11-18 | ✅ resolved | LONG (medium) | long | INTC (US) | This stability gives Intel confidence in Panther Lake launch | Direct mention of $INTC and positive outlook on 18A yield st |
| 11 | 2025-12-01 | ✅ resolved | LONG (high) | long | NVDA (US) | Meta, Google, Amazon, and Microsoft all guided higher 2026 AI CapEx. These dolla | Direct mention of Nvidia benefiting from higher capex from m |
| 12 | 2026-01-22 | ✅ resolved | COMPETITIVE (medium) | long | INVZ (US) | The LiDAR market is consolidating to 1-2 Western suppliers and 1-2 Eastern, and  | The tweet specifically mentions talking to Innoviz CEO about |
| 13 | 2026-03-11 | ✅ resolved | LONG (medium) | long | SNPS (US) | Ever more chip design and physical systems design over the next decade. | 推文来自$SNPS Converge会议，明确指出未来十年将有更多芯片设计与物理系统设计，利好EDA工具龙头Synops |
| 14 | 2026-04-28 | 🟡 30-90d | SHORT (medium) | short | POET (US) | Also POET... pump and get dumped? | POET is directly mentioned, likely referring to POET Technol |
| 15 | 2026-05-06 | 🟡 30-90d | LONG (medium) | long | NVDA,AMD (US) | Old training datacenter is now more valuable as incremental inference cluster | 旧数据中心转用于推理，表明推理硬件需求持续，利好GPU供应商如NVDA和AMD，亦可能提振数据中心基础设施相关标的。 |
| 16 | 2026-06-08 | ❌ pending | LONG (high) | long | NVDA (US) | Bullish $NVDA | 直接提及 $NVDA |
| 17 | 2026-06-15 | ❌ pending | SUPPLY/DEMAND (medium) | long | LITE,COHR (US) | Maybe lots of VCSEL wafers go to interconnect and consumers get crushed again by | VCSEL晶圆产能转移到利润更高的互连市场，导致消费电子供应受限，平均售价上升，消费者受压。类似内存行业，VCSEL制造 |

**逐条原文 (含上下文)**:

**1. [2024-03-18] ✅ resolved LONG → NVDA (US)**
> Nvidia is solving for more of the customer’s job-to-be-done here. This expansion creates lock-in and introduces switching costs. Even if other AI ASICs or GPUs compete on performance/cost/power - the switching cost will be higher for NIM, Nvidia AI enterprise, etc customers
>
> *推导: Nvidia's platform expansion creates lock-in and switching costs, which strengthens its competitive moat, directly positive for NVDA.*
>
> type=LONG confidence=high

**2. [2024-04-02] ✅ resolved LONG → AMD,NVDA (US)**
> Nvidia CUDA’s moat is surmountable &amp; how AMD can overcome their software woes and compete.
>
> *推导: 推文明确表示AMD将能克服软件问题并与Nvidia竞争，直接看好AMD，同时暗示Nvidia的CUDA护城河不再牢不可破，对AMD构成利好。*
>
> type=COMPETITIVE confidence=high

**3. [2025-03-05] ✅ resolved LONG → NVDA (US)**
> Long lifespans could mean better TCO as Blackwell dominates.
>
> *推导: 推文直接提及$NVDA，并称Blackwell（Nvidia新架构）主导，长寿命带来更好TCO，对Nvidia是利好。*
>
> type=LONG confidence=high

**4. [2025-03-18] ✅ resolved LONG → MRVL,AVGO,NVDA (US)**
> Custom ASICs can be tailored to have lower latency or higher throughput and therefore push this curve out further, hence Jensen needing to tie it back to 'why GPUs'
>
> *推导: ASICs gaining advantage over GPUs would benefit custom ASIC designers like Marvell and Broadcom, while threatening NVIDIA's GPU dominance.*
>
> type=COMPETITIVE confidence=medium

**5. [2025-07-11] ✅ resolved LONG → DELL (US)**
> Dell can innovate to differentiate and avoid being stuck in low-margin, commodity territory
>
> *推导: 推文直接提及 @Dell，判断为看好 Dell 创新并提升价值链，对应标的 DELL。*
>
> type=LONG confidence=high

**6. [2025-07-21] ✅ resolved SHORT → OCI (US)**
> Could be a sign the $OCI $30B per year deal won’t deliver either.
>
> *推导: 如果$30B per year deal无法实现，将直接负面影响到标的公司$OCI。$OCI可能指Oracle Cloud Infrastructure，对应股票$ORCL，但推文明确写$OCI，取$OCI为标的。*
>
> type=SHORT confidence=medium

**7. [2025-08-12] ✅ resolved LONG → CRWV (US)**
> $CRWV seeing a "massive increase" in inference workloads, as validated by watching the power meter lol.
>
> *推导: 直接提到 $CRWV 推理工作负载大幅增长，利好公司*
>
> type=LONG confidence=medium

**8. [2025-08-17] ✅ resolved SHORT → AMAT,LRCX,KLAC (US)**
> AMAT softening guide due to a leading edge foundry pulling back, indicating lower equipment demand and monopsony risk.
>
> *推导: AMAT's softened guidance is attributed to a leading-edge foundry cutting capex, signaling reduced demand for wafer fab equipment. This directly impacts AMAT and likely extends to peers like LRCX and KLAC.*
>
> type=SUPPLY/DEMAND confidence=medium

**9. [2025-08-29] ✅ resolved SHORT → GOOGL (US)**
> $GOOGL knows how to sell ads and rent servers. Selling merchant silicon chips is a different ballgame. Just because you could, doesn't mean you should.
>
> *推导: The tweet questions Google's ability to succeed in the merchant silicon chip business, implying a negative outlook for GOOGL in this venture, which could be detrimental to the stock.*
>
> type=SHORT confidence=medium

**10. [2025-11-18] ✅ resolved LONG → INTC (US)**
> This stability gives Intel confidence in Panther Lake launch
>
> *推导: Direct mention of $INTC and positive outlook on 18A yield stability leading to Panther Lake confidence*
>
> type=LONG confidence=medium

**11. [2025-12-01] ✅ resolved LONG → NVDA (US)**
> Meta, Google, Amazon, and Microsoft all guided higher 2026 AI CapEx. These dollars flow straight into Nvidia's backlog.
>
> *推导: Direct mention of Nvidia benefiting from higher capex from major customers.*
>
> type=LONG confidence=high

**12. [2026-01-22] ✅ resolved LONG → INVZ (US)**
> The LiDAR market is consolidating to 1-2 Western suppliers and 1-2 Eastern, and the next 2 years are a land grab.
>
> *推导: The tweet specifically mentions talking to Innoviz CEO about why most competitors are already gone, implying Innoviz is positioned as a surviving Western LiDAR supplier. Thus, the industry consolidation likely benefits Innoviz.*
>
> type=COMPETITIVE confidence=medium

**13. [2026-03-11] ✅ resolved LONG → SNPS (US)**
> Ever more chip design and physical systems design over the next decade.
>
> *推导: 推文来自$SNPS Converge会议，明确指出未来十年将有更多芯片设计与物理系统设计，利好EDA工具龙头Synopsys ($SNPS)。*
>
> type=LONG confidence=medium

**14. [2026-04-28] 🟡 30-90d SHORT → POET (US)**
> Also POET... pump and get dumped?
>
> *推导: POET is directly mentioned, likely referring to POET Technologies, implying potential price drop after a pump.*
>
> type=SHORT confidence=medium

**15. [2026-05-06] 🟡 30-90d LONG → NVDA,AMD (US)**
> Old training datacenter is now more valuable as incremental inference cluster
>
> *推导: 旧数据中心转用于推理，表明推理硬件需求持续，利好GPU供应商如NVDA和AMD，亦可能提振数据中心基础设施相关标的。*
>
> type=LONG confidence=medium

**16. [2026-06-08] ❌ pending LONG → NVDA (US)**
> Bullish $NVDA
>
> *推导: 直接提及 $NVDA*
>
> type=LONG confidence=high

**17. [2026-06-15] ❌ pending LONG → LITE,COHR (US)**
> Maybe lots of VCSEL wafers go to interconnect and consumers get crushed again by ASPs just like memory
>
> *推导: VCSEL晶圆产能转移到利润更高的互连市场，导致消费电子供应受限，平均售价上升，消费者受压。类似内存行业，VCSEL制造商(LITE, COHR)将受益于更高ASP，因此看多。*
>
> type=SUPPLY/DEMAND confidence=medium

## @zephyr_z9 (8 judgments)

| # | 日期 | 状态 | 类型 | 方向 | 标的 (市场) | 原文 (核心句) | 推导逻辑 |
|---|---|---|---|---|---|---|---|
| 1 | 2025-03-01 | ✅ resolved | SUPPLY (medium) | short | NVDA (US) | The world does not have this high AI demand | 推文假设将当前H800集群规模扩大100倍后的巨大推理需求，并断言世界没有如此高的AI需求，暗示对AI算力的投资可能过度 |
| 2 | 2025-04-15 | ✅ resolved | MACRO (medium) | long | FXI,MCHI (US/HK) | Long negotiations favor China as US will start getting restless due to shortages | 谈判拖延对中国有利，可能提振中国股市，引申看多中国大盘股ETF如FXI、MCHI。 |
| 3 | 2025-05-28 | ✅ resolved | COMPETITIVE (high) | short | SIEGY (DE) | I don't think this will end well for Siemens | Siemens owns Mentor Graphics, an EDA company; Huawei's inter |
| 4 | 2025-06-02 | ✅ resolved | LONG (high) | long | WDC,STX (US) | Compute &amp; storage demand would go parabolic once proper long video generatio | 推文指出长视频生成将导致计算和存储需求暴涨，内存股（SSD和HDD）现在可以买入，直接看多存储制造商Western Di |
| 5 | 2025-06-08 | ✅ resolved | SUPPLY (medium) | long | VRT (US) | AI power demand & supply gap will explode starting next year | AI电力供需缺口扩大预期利好数据中心电力基础设施供应商，如Vertiv (VRT) |
| 6 | 2025-12-28 | ✅ resolved | SHORT (medium) | short | MDB (US) | Giant MongoDB L LMAO | 推文嘲笑MongoDB遭遇巨大损失，隐含看空情绪，对应标的MongoDB Inc. (MDB) |
| 7 | 2025-12-28 | ✅ resolved | SUPPLY/DEMAND (medium) | long | MU,005930.KS,000660.KS (US/KR) | The price squeeze has happened due to unexpected increase in HBM demand and gene | HBM需求意外增长和服务器更换周期导致存储芯片供不应求，价格上涨，利好主要的存储制造商美光、三星电子和SK海力士。 |
| 8 | 2026-01-12 | ✅ resolved | SUPPLY/DEMAND (high) | long | MU,WDC (US) | If you still aren’t bullish on SSD demand, read this and get storage-pilled | SSD需求看多，受益于NAND闪存和SSD制造商，例如美光(MU)和西部数据(WDC) |

**逐条原文 (含上下文)**:

**1. [2025-03-01] ✅ resolved SHORT → NVDA (US)**
> The world does not have this high AI demand
>
> *推导: 推文假设将当前H800集群规模扩大100倍后的巨大推理需求，并断言世界没有如此高的AI需求，暗示对AI算力的投资可能过度，利空主要GPU供应商NVIDIA。*
>
> type=SUPPLY confidence=medium

**2. [2025-04-15] ✅ resolved LONG → FXI,MCHI (US/HK)**
> Long negotiations favor China as US will start getting restless due to shortages
>
> *推导: 谈判拖延对中国有利，可能提振中国股市，引申看多中国大盘股ETF如FXI、MCHI。*
>
> type=MACRO confidence=medium

**3. [2025-05-28] ✅ resolved SHORT → SIEGY (DE)**
> I don't think this will end well for Siemens
>
> *推导: Siemens owns Mentor Graphics, an EDA company; Huawei's internal tools becoming competitive could negatively impact Siemens' EDA business*
>
> type=COMPETITIVE confidence=high

**4. [2025-06-02] ✅ resolved LONG → WDC,STX (US)**
> Compute &amp; storage demand would go parabolic once proper long video generation comes online (15min-1hr)
>
> *推导: 推文指出长视频生成将导致计算和存储需求暴涨，内存股（SSD和HDD）现在可以买入，直接看多存储制造商Western Digital (WDC)和Seagate (STX)。*
>
> type=LONG confidence=high

**5. [2025-06-08] ✅ resolved LONG → VRT (US)**
> AI power demand & supply gap will explode starting next year
>
> *推导: AI电力供需缺口扩大预期利好数据中心电力基础设施供应商，如Vertiv (VRT)*
>
> type=SUPPLY confidence=medium

**6. [2025-12-28] ✅ resolved SHORT → MDB (US)**
> Giant MongoDB L LMAO
>
> *推导: 推文嘲笑MongoDB遭遇巨大损失，隐含看空情绪，对应标的MongoDB Inc. (MDB)*
>
> type=SHORT confidence=medium

**7. [2025-12-28] ✅ resolved LONG → MU,005930.KS,000660.KS (US/KR)**
> The price squeeze has happened due to unexpected increase in HBM demand and general purpose server replacement cycle (meta & Microsoft are the most aggressive here)
>
> *推导: HBM需求意外增长和服务器更换周期导致存储芯片供不应求，价格上涨，利好主要的存储制造商美光、三星电子和SK海力士。*
>
> type=SUPPLY/DEMAND confidence=medium

**8. [2026-01-12] ✅ resolved LONG → MU,WDC (US)**
> If you still aren’t bullish on SSD demand, read this and get storage-pilled
>
> *推导: SSD需求看多，受益于NAND闪存和SSD制造商，例如美光(MU)和西部数据(WDC)*
>
> type=SUPPLY/DEMAND confidence=high

---

## 球给用户

请读这 49 条判断, 评估他们的产业洞察质量:

**关键看:**
1. **@fi56622380 的 HBM 24 年 NVDA 类比** (#18) — 2026-04-17, 2 个月前, HBM/MU/Samsung/SK Hynix 是否印证
2. **@fi56622380 的 Micron 存储技术差** (#22) — 2025-12-01, 7 个月, MU 同期涨跌
3. **@fi56622380 的 ARM CAGR 50%** (#12) — 2026-03-05, 3.5 个月
4. **@austinsemis 的 NVDA 锁定效应** (#9) + **CUDA 护城河可破** (#8) — 2024-03/04, 2 年多, 已可完整验
5. **@zephyr_z9 的长视频存储需求爆发** (#2) — 2025-06-02, 1 年, WDC/STX 同期

如果 @fi56622380 通过产业洞察质量测试, 立刻拉 1m/3m/6m 全量 + 跑 Polygon 验证 (跟 Jukan 同管道).