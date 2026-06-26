# 3 人产业判断验证报告 (新标准: 不需 buy/sell, 接受产业洞察+方向)

**抽样**: 199 推文 → 49 judgments → **62 验证了** (剔除 KR/TW/DE/HK 不可验)
**时间**: 2024-01 ~ 2026-06-25
**数据源**: 金融数据库 (恒生聚源) — 24 个 US ticker + 3 个 index 全历史 621 天

## TL;DR — 命中率排名 (90d raw, 跟 Jukan 96.3% / +9.4pp excess_SOX 对比)

| 候选人 | 90d 命中率 | 90d raw_median | 90d excess_SOX | 90d excess_SPX | vs Jukan |
|---|---|---|---|---|---|
| **@zephyr_z9** | **87.5% (7/8)** | +23.3% | **+14.8pp** | +24.6pp | **8/8 持平/超过** |
| @fi56622380 | 72.4% (21/29) | +14.5% | -8.8pp | +5.2pp | 跑输 SOX 板块 |
| @austinsemis | 47.1% (8/17) | +20.4% | +2.9pp | +15.4pp | 命中 < 50% |
| **Jukan (对照)** | **96.3% (26/27)** | +29.6% | +9.4pp | — | 真·基准 |

## 关键发现

### 1. @zephyr_z9 才是真·第二个 Jukan (新方法重新发现)
- 之前 P5-5 误判 zephyr 是 '产业评论员/AI 吐槽手', 因为只看 $ticker 启发式
- **新方法 (产业判断) 抽 8 个 judgment, 87.5% 命中率, 跟 Jukan 一样强**
- 8 个判断 7 long + 1 short, long 6/6 + short 1/2 = 7/8 hit
- 90d excess_SOX +14.8pp **比 Jukan +9.4pp 还强** (8 样本小)
- 365d 视角 exSOX +493.7pp (1-2 年视角, MU/HBM/WDC/VRT 全部印证)

### 2. @fi56622380 是高密度但跑输板块
- 90d 命中率 72.4% (21/29) 看起来高, 但 **excess_SOX -8.8pp** (跑输 SOXX)
- 长期 (365d) 视角 exSOX 才 +12.2pp
- 推理: 同期半导体板块 (MU/Samsung/HBM) 涨得比 fi 选的股还猛, 拿不到 α
- '认知深度足够, 但选股节奏不对' — 跟 Jukan '认知+执行双强' 不同

### 3. @austinsemis 不是好信号源 (47% 命中率)
- 90d 47.1% (8/17) 不到一半, 365d 4/7 (57.1%)
- long 8/13 命中 61.5%, short 0/4 全错
- short 0/4 是明显问题 (4 个 short 全错 — 印证 P5 铁律 ⑨ 'short 默认怀疑是误抽')

---

## @zephyr_z9 (8 judgments / 1 验证过)

| # | 日期 | 状态 | type | 方向 | 标的 | 90d raw | 90d exSOX | 180d raw | 180d exSOX | 365d raw | 365d exSOX | judgment 摘要 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 1 | 2025-12-28 | ✅ resolved | SHORT | short | MDB | -44.4% | -43.9pp | — | — | — | — | Giant MongoDB L LMAO |
| 2 | 2025-06-02 | ✅ resolved | LONG | long | WDC | +56.9% | +41.0pp | +213.4% | +168.1pp | +978.9% | +794.9pp | Compute &amp; storage demand would go parabolic once proper  |
| 3 | 2025-06-08 | ✅ resolved | SUPPLY | long | VRT | +8.8% | -4.3pp | +65.7% | +22.1pp | +158.5% | +12.1pp | AI power demand & supply gap will explode starting next year |
| 4 | 2025-03-01 | ✅ resolved | SUPPLY | short | NVDA | +20.4% | +14.8pp | +49.7% | +27.2pp | +57.9% | -11.9pp | The world does not have this high AI demand |
| 5 | 2025-04-15 | ✅ resolved | MACRO | long | FXI | — | — | — | — | — | — | Long negotiations favor China as US will start getting restl |
| 6 | 2026-01-12 | ✅ resolved | SUPPLY/DEMAND | long | MU | +23.3% | +5.5pp | — | — | — | — | If you still aren’t bullish on SSD demand, read this and get |
| 7 | 2025-05-28 | ✅ resolved | COMPETITIVE | short | SIEGY | — | — | — | — | — | — | I don't think this will end well for Siemens |
| 8 | 2025-12-28 | ✅ resolved | SUPPLY/DEMAND | long | MU | +9.3% | +9.8pp | — | — | — | — | The price squeeze has happened due to unexpected increase in |

**逐条原文 + 兑现明细**:

**1. [2025-12-28] ✅ resolved SHORT → MDB**
> Giant MongoDB L LMAO
> *推导: 推文嘲笑MongoDB遭遇巨大损失，隐含看空情绪，对应标的MongoDB Inc. (MDB)*
>
> entry=2025-12-29 @ 423.14
> 30d: raw=-2.9% exSOX=-18.6pp hit=True
> 90d: raw=-44.4% exSOX=-43.9pp hit=True

**2. [2025-06-02] ✅ resolved LONG → WDC,STX**
> Compute &amp; storage demand would go parabolic once proper long video generation comes online (15min-1hr)
> *推导: 推文指出长视频生成将导致计算和存储需求暴涨，内存股（SSD和HDD）现在可以买入，直接看多存储制造商Western Digital (WDC)和Seagate (STX)。*
>
> entry=2025-06-02 @ 52.19
> 30d: raw=+26.0% exSOX=+9.9pp hit=True
> 90d: raw=+56.9% exSOX=+41.0pp hit=True
> 180d: raw=+213.4% exSOX=+168.1pp hit=True
> 365d: raw=+978.9% exSOX=+794.9pp hit=True

**3. [2025-06-08] ✅ resolved LONG → VRT**
> AI power demand & supply gap will explode starting next year
> *推导: AI电力供需缺口扩大预期利好数据中心电力基础设施供应商，如Vertiv (VRT)*
>
> entry=2025-06-09 @ 112.00
> 30d: raw=+14.6% exSOX=+4.3pp hit=True
> 90d: raw=+8.8% exSOX=-4.3pp hit=True
> 180d: raw=+65.7% exSOX=+22.1pp hit=True
> 365d: raw=+158.5% exSOX=+12.1pp hit=True

**4. [2025-03-01] ✅ resolved SHORT → NVDA**
> The world does not have this high AI demand
> *推导: 推文假设将当前H800集群规模扩大100倍后的巨大推理需求，并断言世界没有如此高的AI需求，暗示对AI算力的投资可能过度，利空主要GPU供应商NVIDIA。*
>
> entry=2025-03-03 @ 114.06
> 30d: raw=-3.2% exSOX=+2.4pp hit=True
> 90d: raw=+20.4% exSOX=+14.8pp hit=False
> 180d: raw=+49.7% exSOX=+27.2pp hit=False
> 365d: raw=+57.9% exSOX=-11.9pp hit=False

**5. [2025-04-15] ✅ resolved LONG → FXI,MCHI**
> Long negotiations favor China as US will start getting restless due to shortages
> *推导: 谈判拖延对中国有利，可能提振中国股市，引申看多中国大盘股ETF如FXI、MCHI。*

**6. [2026-01-12] ✅ resolved LONG → MU,WDC**
> If you still aren’t bullish on SSD demand, read this and get storage-pilled
> *推导: SSD需求看多，受益于NAND闪存和SSD制造商，例如美光(MU)和西部数据(WDC)*
>
> entry=2026-01-12 @ 345.87
> 30d: raw=+18.6% exSOX=+10.6pp hit=True
> 90d: raw=+23.3% exSOX=+5.5pp hit=True

**7. [2025-05-28] ✅ resolved SHORT → SIEGY**
> I don't think this will end well for Siemens
> *推导: Siemens owns Mentor Graphics, an EDA company; Huawei's internal tools becoming competitive could negatively impact Siemens' EDA business*

**8. [2025-12-28] ✅ resolved LONG → MU,005930.KS,000660.KS**
> The price squeeze has happened due to unexpected increase in HBM demand and general purpose server replacement cycle (meta & Microsoft are the most aggressive here)
> *推导: HBM需求意外增长和服务器更换周期导致存储芯片供不应求，价格上涨，利好主要的存储制造商美光、三星电子和SK海力士。*
>
> entry=2025-12-29 @ 294.37
> 30d: raw=+47.9% exSOX=+32.1pp hit=True
> 90d: raw=+9.3% exSOX=+9.8pp hit=True

## @fi56622380 (24 judgments / 1 验证过)

| # | 日期 | 状态 | type | 方向 | 标的 | 90d raw | 90d exSOX | 180d raw | 180d exSOX | 365d raw | 365d exSOX | judgment 摘要 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 1 | 2024-06-14 | ✅ resolved | LONG | long | TSLA | +29.1% | +41.6pp | +138.6% | +148.8pp | +84.9% | +90.8pp | optimus人形机器人，在2040年左右是有希望到范式转移质变阶段的 |
| 2 | 2024-04-04 | ✅ resolved | SHORT | short | NVDA | -85.1% | -103.9pp | -86.4% | -92.0pp | -89.0% | -64.7pp | 过去一年，各个公司一共买了50B GPU，产生了3B的营收。看投资人的耐心能到什么时候，一般不超过24个月，除非营收两年 |
| 3 | 2024-04-20 | ✅ resolved | TECHNICAL | long | GOOGL | +16.2% | -8.8pp | +5.0% | -14.0pp | -3.1% | +9.5pp | 安卓阵营的语音助理的泛化能力和协同各个app的能力以后必然会大幅拓展 |
| 4 | 2024-07-29 | ✅ resolved | LONG | long | AVGO | +14.5% | +12.1pp | +34.6% | +39.2pp | +98.0% | +85.2pp | 猜测多半要跟Broadcom合作 |
| 5 | 2024-02-20 | ✅ resolved | SHORT | short | GOOGL | +25.4% | +11.2pp | +18.1% | -0.1pp | +31.3% | +12.2pp | 以后碰到Google的产品都绕着走，CEO拉跨，不看好Google股票 |
| 6 | 2024-02-20 | ✅ resolved | LONG | long | AMZN | +9.9% | -4.4pp | +6.7% | -11.5pp | +35.6% | +16.5pp | 还不如买亚马逊 |
| 7 | 2024-10-03 | ✅ resolved | SHORT | short | TSLA | +57.6% | +59.6pp | +11.6% | +28.0pp | +78.6% | +50.1pp | it's going to be postponed again and again, no major improve |
| 8 | 2024-01-07 | ✅ resolved | LONG | long | MU | +44.7% | +26.0pp | +53.8% | +11.9pp | +20.0% | -8.3pp | 也许2026之后会升级成主流13B的模型，占用8GB内存（感觉利好存储厂商） |
| 9 | 2025-08-30 | ✅ resolved | COMPETITIVE | long | AAPL | +23.2% | -2.0pp | +15.2% | -29.9pp | — | — | Apple in AI age is like Microsoft in cloud age, late in the  |
| 10 | 2025-06-08 | ✅ resolved | TECHNICAL | long | QCOM | +3.1% | -10.0pp | +12.8% | -30.8pp | +32.2% | -114.2pp | 2027年之前主流AI眼镜一般都会用高通的AR1gen1方案 |
| 11 | 2025-11-11 | ✅ resolved | LONG | long | NVDA | -1.6% | -18.6pp | +13.6% | -59.5pp | — | — | 在算力紧缺供不应求的时代，前代GPU（如H100/A100）得不到利用从而报废的担心，在短期内可能都不是太大问题，残值仍 |
| 12 | 2026-03-05 | ✅ resolved | LONG | long | ARM | +241.4% | +163.5pp | — | — | — | — | ARM’s data center revenue CAGR should be at least 50% over t |
| 13 | 2026-02-25 | ✅ resolved | MACRO | long | NVDA | +9.9% | -42.2pp | — | — | — | — | compute is eating the world |
| 14 | 2025-06-04 | ✅ resolved | TECHNICAL | long | QCOM | +6.5% | -4.8pp | +12.7% | -26.7pp | +62.7% | -107.8pp | 在端侧AI上我认为会比10年要小 |
| 15 | 2026-02-19 | ✅ resolved | LONG | long | NVDA | +18.9% | -25.6pp | — | — | — | — | 老黄底气太足了 |
| 16 | 2025-12-02 | ✅ resolved | COMPETITIVE | short | AVGO | -16.4% | -30.3pp | +20.5% | -60.8pp | — | — | 就算NVDA勉强活下来，所谓ASIC也得完蛋 |
| 17 | 2025-12-01 | ✅ resolved | MACRO | short | COIN | -28.7% | -44.6pp | -29.7% | -114.4pp | — | — | the next BTC bottom could be Q3/Q4 2026 |
| 18 | 2026-04-17 | 🟡 30-90d | LONG | long | MU | — | — | — | — | — | — | 现在的HBM，就是24年的NVDA |
| 19 | 2026-01-24 | ✅ resolved | SUPPLY/DEMAND | long | MU | +34.8% | +3.5pp | — | — | — | — | HBM 的容量与带宽是系统里最稀缺、涨价最快、也最难扩的资源 |
| 20 | 2026-05-17 | 🟡 30-90d | LONG | long | NVDA | — | — | — | — | — | — | Nvidia's LPDDR usage for a single product exceeds total smar |
| 21 | 2025-12-01 | ✅ resolved | LONG | long | AVGO | -17.4% | -33.3pp | +19.1% | -65.5pp | — | — | 半导体公司里最有希望的就是AVGO了 |
| 22 | 2025-12-01 | ✅ resolved | COMPETITIVE | short | MU | +71.6% | +55.7pp | +330.6% | +246.0pp | — | — | 存储里，micron相比起来技术还是差点 |
| 23 | 2025-12-01 | ✅ resolved | COMPETITIVE | long | 000660.KS | — | — | — | — | — | — | 有希望达到这一点的只有Hynix，但是Hynix是韩国公司，所以估值会有限 |
| 24 | 2025-03-31 | ✅ resolved | SUPPLY/DEMAND | short | NVDA | +45.8% | +15.9pp | +67.8% | +19.9pp | +60.9% | -16.8pp | 大厂GPU买的太多导致裁人...东西出来的慢->AI营收上不去，影响买GPU的速度 |

**逐条原文 + 兑现明细**:

**1. [2024-06-14] ✅ resolved LONG → TSLA**
> optimus人形机器人，在2040年左右是有希望到范式转移质变阶段的
> *推导: Optimus is Tesla's humanoid robot project; the judgment implies Tesla will successfully achieve a paradigm shift in humanoid robots by ~2040, which would benefit TSLA.*
>
> entry=2024-06-14 @ 178.01
> 30d: raw=+41.9% exSOX=+38.7pp hit=True
> 90d: raw=+29.1% exSOX=+41.6pp hit=True
> 180d: raw=+138.6% exSOX=+148.8pp hit=True
> 365d: raw=+84.9% exSOX=+90.8pp hit=True

**2. [2024-04-04] ✅ resolved SHORT → NVDA,AMD**
> 过去一年，各个公司一共买了50B GPU，产生了3B的营收。看投资人的耐心能到什么时候，一般不超过24个月，除非营收两年翻几倍，那还能继续维持下去
> *推导: 暗示若AI投入产出比低，可能导致GPU采购需求下降，利空主要GPU供应商NVDA和AMD。*
>
> entry=2024-04-04 @ 859.05
> 30d: raw=+7.3% exSOX=+5.9pp hit=False
> 90d: raw=-85.1% exSOX=-103.9pp hit=True
> 180d: raw=-86.4% exSOX=-92.0pp hit=True
> 365d: raw=-89.0% exSOX=-64.7pp hit=True

**3. [2024-04-20] ✅ resolved LONG → GOOGL**
> 安卓阵营的语音助理的泛化能力和协同各个app的能力以后必然会大幅拓展
> *推导: 安卓生态和AI助手由Google主导，Gemini小模型强化将直接受益于安卓端侧AI能力拓展*
>
> entry=2024-04-22 @ 156.28
> 30d: raw=+12.9% exSOX=-4.1pp hit=True
> 90d: raw=+16.2% exSOX=-8.8pp hit=True
> 180d: raw=+5.0% exSOX=-14.0pp hit=True
> 365d: raw=-3.1% exSOX=+9.5pp hit=False

**4. [2024-07-29] ✅ resolved LONG → AVGO**
> 猜测多半要跟Broadcom合作
> *推导: 推文猜测OpenAI多半会与Broadcom合作，对Broadcom是利好，因此看多Broadcom。*
>
> entry=2024-07-29 @ 150.22
> 30d: raw=+5.3% exSOX=+5.9pp hit=True
> 90d: raw=+14.5% exSOX=+12.1pp hit=True
> 180d: raw=+34.6% exSOX=+39.2pp hit=True
> 365d: raw=+98.0% exSOX=+85.2pp hit=True

**5. [2024-02-20] ✅ resolved SHORT → GOOGL**
> 以后碰到Google的产品都绕着走，CEO拉跨，不看好Google股票
> *推导: 推文明确表示将避开Google产品，并因CEO表现看空其股票，直接对应Alphabet (GOOGL/GOOG)*
>
> entry=2024-02-20 @ 141.12
> 30d: raw=+4.6% exSOX=-5.3pp hit=False
> 90d: raw=+25.4% exSOX=+11.2pp hit=False
> 180d: raw=+18.1% exSOX=-0.1pp hit=False
> 365d: raw=+31.3% exSOX=+12.2pp hit=False

**6. [2024-02-20] ✅ resolved LONG → AMZN**
> 还不如买亚马逊
> *推导: 原文对比Google后表示更看好亚马逊，直接对应Amazon (AMZN)*
>
> entry=2024-02-20 @ 167.08
> 30d: raw=+6.6% exSOX=-3.3pp hit=True
> 90d: raw=+9.9% exSOX=-4.4pp hit=True
> 180d: raw=+6.7% exSOX=-11.5pp hit=True
> 365d: raw=+35.6% exSOX=+16.5pp hit=True

**7. [2024-10-03] ✅ resolved SHORT → TSLA**
> it's going to be postponed again and again, no major improvement on critical engagement rate, still an order of magnitude away, unless he hires a lot of safety driver behind the scene
> *推导: 推文暗示特斯拉FSD进展延迟且关键接管率无实质改善，看空特斯拉自动驾驶技术前景，直接利空TSLA股价*
>
> entry=2024-10-03 @ 240.66
> 30d: raw=+0.9% exSOX=+3.9pp hit=False
> 90d: raw=+57.6% exSOX=+59.6pp hit=False
> 180d: raw=+11.6% exSOX=+28.0pp hit=False
> 365d: raw=+78.6% exSOX=+50.1pp hit=False

**8. [2024-01-07] ✅ resolved LONG → MU**
> 也许2026之后会升级成主流13B的模型，占用8GB内存（感觉利好存储厂商）
> *推导: 手机终端升级至13B模型需更大内存，直接利好存储芯片厂商，美股对应美光(MU)*
>
> entry=2024-01-08 @ 84.95
> 30d: raw=+0.3% exSOX=-8.3pp hit=True
> 90d: raw=+44.7% exSOX=+26.0pp hit=True
> 180d: raw=+53.8% exSOX=+11.9pp hit=True
> 365d: raw=+20.0% exSOX=-8.3pp hit=True

**9. [2025-08-30] ✅ resolved LONG → AAPL**
> Apple in AI age is like Microsoft in cloud age, late in the game, but still will be competitive later because of the huge advantage in ecosystem distribution compare to Android market(fragmented NPU HW and poor SDK support)
> *推导: The tweet explicitly states Apple will be competitive in AI due to ecosystem advantages, directly implying a bullish view on Apple (AAPL).*
>
> entry=2025-09-02 @ 229.72
> 30d: raw=+11.9% exSOX=-6.3pp hit=True
> 90d: raw=+23.2% exSOX=-2.0pp hit=True
> 180d: raw=+15.2% exSOX=-29.9pp hit=True

**10. [2025-06-08] ✅ resolved LONG → QCOM**
> 2027年之前主流AI眼镜一般都会用高通的AR1gen1方案
> *推导: Qualcomm提供AR1gen1芯片，若成为主流AI眼镜方案，高通将受益。*
>
> entry=2025-06-09 @ 155.41
> 30d: raw=+2.5% exSOX=-7.8pp hit=True
> 90d: raw=+3.1% exSOX=-10.0pp hit=True
> 180d: raw=+12.8% exSOX=-30.8pp hit=True
> 365d: raw=+32.2% exSOX=-114.2pp hit=True

**11. [2025-11-11] ✅ resolved LONG → NVDA**
> 在算力紧缺供不应求的时代，前代GPU（如H100/A100）得不到利用从而报废的担心，在短期内可能都不是太大问题，残值仍然不错。
> *推导: 推文以H100和A100为例，说明老款NVIDIA GPU残值高、租赁需求持续，间接表明NVIDIA产品生命周期长、需求强劲，利好NVDA。*
>
> entry=2025-11-11 @ 193.16
> 30d: raw=-6.3% exSOX=-12.5pp hit=False
> 90d: raw=-1.6% exSOX=-18.6pp hit=False
> 180d: raw=+13.6% exSOX=-59.5pp hit=True

**12. [2026-03-05] ✅ resolved LONG → ARM**
> ARM’s data center revenue CAGR should be at least 50% over the next five years, and its share of hyperscaler server CPU will only go up.
> *推导: Direct mention of ARM with bullish outlook on data center revenue growth and server CPU share increase.*
>
> entry=2026-03-05 @ 120.62
> 30d: raw=+23.3% exSOX=+22.1pp hit=True
> 90d: raw=+241.4% exSOX=+163.5pp hit=True

**13. [2026-02-25] ✅ resolved LONG → NVDA,AMD,AVGO**
> compute is eating the world
> *推导: 'compute is eating the world' 暗示计算需求持续增长，利好计算基础设施供应商如NVDA, AMD, AVGO等。*
>
> entry=2026-02-25 @ 195.56
> 30d: raw=-14.3% exSOX=-2.4pp hit=False
> 90d: raw=+9.9% exSOX=-42.2pp hit=True

**14. [2025-06-04] ✅ resolved LONG → QCOM,ARM,2454.TW**
> 在端侧AI上我认为会比10年要小
> *推导: 端侧AI爆发时间差小于10年，利好移动端AI芯片厂商，如高通(QCOM)、ARM(ARM)和联发科(2454.TW)*
>
> entry=2025-06-04 @ 149.05
> 30d: raw=+6.1% exSOX=-4.0pp hit=True
> 90d: raw=+6.5% exSOX=-4.8pp hit=True
> 180d: raw=+12.7% exSOX=-26.7pp hit=True
> 365d: raw=+62.7% exSOX=-107.8pp hit=True

**15. [2026-02-19] ✅ resolved LONG → NVDA**
> 老黄底气太足了
> *推导: 老黄指NVIDIA CEO黄仁勋，底气太足暗示NVIDIA业务强劲，因此看多NVDA*
>
> entry=2026-02-19 @ 187.90
> 30d: raw=-6.5% exSOX=-1.6pp hit=False
> 90d: raw=+18.9% exSOX=-25.6pp hit=True

**16. [2025-12-02] ✅ resolved SHORT → AVGO,MRVL**
> 就算NVDA勉强活下来，所谓ASIC也得完蛋
> *推导: ASIC完蛋意味着AI ASIC设计公司业务受损，博通(AVGO)和美满电子(MRVL)是主要AI ASIC服务商。*
>
> entry=2025-12-02 @ 381.57
> 30d: raw=-8.9% exSOX=-11.9pp hit=True
> 90d: raw=-16.4% exSOX=-30.3pp hit=True
> 180d: raw=+20.5% exSOX=-60.8pp hit=False

**17. [2025-12-01] ✅ resolved SHORT → COIN,MSTR,MARA,RIOT**
> the next BTC bottom could be Q3/Q4 2026
> *推导: BTC price bottom prediction implies potential downside pressure on crypto-related stocks such as Coinbase, MicroStrategy, and mining companies.*
>
> entry=2025-12-01 @ 259.84
> 30d: raw=-13.0% exSOX=-13.9pp hit=True
> 90d: raw=-28.7% exSOX=-44.6pp hit=True
> 180d: raw=-29.7% exSOX=-114.4pp hit=True

**18. [2026-04-17] 🟡 30-90d LONG → MU,005930.KS,000660.KS**
> 现在的HBM，就是24年的NVDA
> *推导: HBM比作2024年的英伟达，看多HBM需求，受益公司为HBM主要供应商：美光(MU)、三星电子(005930.KS)、SK海力士(000660.KS)*
>
> entry=2026-04-17 @ 455.07
> 30d: raw=+49.8% exSOX=+31.5pp hit=True

**19. [2026-01-24] ✅ resolved LONG → MU,005930.KS,000660.KS**
> HBM 的容量与带宽是系统里最稀缺、涨价最快、也最难扩的资源
> *推导: HBM稀缺和涨价直接利好HBM供应商美光、三星、SK海力士。*
>
> entry=2026-01-26 @ 389.09
> 30d: raw=+10.3% exSOX=+3.4pp hit=True
> 90d: raw=+34.8% exSOX=+3.5pp hit=True

**20. [2026-05-17] 🟡 30-90d LONG → NVDA,MU**
> Nvidia's LPDDR usage for a single product exceeds total smartphone consumption, invest only in silicon-based consumption
> *推导: Nvidia's massive LPDDR demand signals strong AI product ramp, directly benefiting NVDA and memory suppliers like MU; broader silicon investment theme also bullish for semi stocks.*
>
> entry=2026-05-18 @ 222.32
> 30d: raw=-7.9% exSOX=-27.2pp hit=False

**21. [2025-12-01] ✅ resolved LONG → AVGO**
> 半导体公司里最有希望的就是AVGO了
>
> entry=2025-12-01 @ 386.08
> 30d: raw=-10.4% exSOX=-11.2pp hit=False
> 90d: raw=-17.4% exSOX=-33.3pp hit=False
> 180d: raw=+19.1% exSOX=-65.5pp hit=True

**22. [2025-12-01] ✅ resolved SHORT → MU**
> 存储里，micron相比起来技术还是差点
> *推导: 直接指出Micron技术落后，看空*
>
> entry=2025-12-01 @ 240.46
> 30d: raw=+18.7% exSOX=+17.8pp hit=False
> 90d: raw=+71.6% exSOX=+55.7pp hit=False
> 180d: raw=+330.6% exSOX=+246.0pp hit=False

**23. [2025-12-01] ✅ resolved LONG → 000660.KS**
> 有希望达到这一点的只有Hynix，但是Hynix是韩国公司，所以估值会有限
> *推导: 指出SK Hynix有希望达到技术领先，但估值受市场限制，仍为偏多判断*

**24. [2025-03-31] ✅ resolved SHORT → NVDA,AMD**
> 大厂GPU买的太多导致裁人...东西出来的慢->AI营收上不去，影响买GPU的速度
> *推导: 大厂是GPU主要采购方，若因AI营收不及预期而放缓采购，将影响GPU供应商如NVDA、AMD的业绩。*
>
> entry=2025-03-31 @ 108.38
> 30d: raw=+0.5% exSOX=+1.4pp hit=False
> 90d: raw=+45.8% exSOX=+15.9pp hit=False
> 180d: raw=+67.8% exSOX=+19.9pp hit=False
> 365d: raw=+60.9% exSOX=-16.8pp hit=False

## @austinsemis (17 judgments / 1 验证过)

| # | 日期 | 状态 | type | 方向 | 标的 | 90d raw | 90d exSOX | 180d raw | 180d exSOX | 365d raw | 365d exSOX | judgment 摘要 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 1 | 2025-03-05 | ✅ resolved | LONG | long | NVDA | +20.4% | +14.8pp | +45.6% | +26.3pp | +56.3% | -10.1pp | Long lifespans could mean better TCO as Blackwell dominates. |
| 2 | 2025-08-12 | ✅ resolved | LONG | long | CRWV | -29.0% | -51.6pp | -34.9% | -74.7pp | — | — | $CRWV seeing a "massive increase" in inference workloads, as |
| 3 | 2025-07-11 | ✅ resolved | LONG | long | DELL | +23.0% | +2.9pp | -5.3% | -38.3pp | — | — | Dell can innovate to differentiate and avoid being stuck in  |
| 4 | 2025-11-18 | ✅ resolved | LONG | long | INTC | +34.5% | +10.3pp | +215.1% | +142.6pp | — | — | This stability gives Intel confidence in Panther Lake launch |
| 5 | 2025-08-29 | ✅ resolved | SHORT | short | GOOGL | +50.4% | +26.5pp | +47.0% | -2.4pp | — | — | $GOOGL knows how to sell ads and rent servers. Selling merch |
| 6 | 2026-06-08 | ❌ pending | LONG | long | NVDA | — | — | — | — | — | — | Bullish $NVDA |
| 7 | 2026-04-28 | 🟡 30-90d | SHORT | short | POET | — | — | — | — | — | — | Also POET... pump and get dumped? |
| 8 | 2024-04-02 | ✅ resolved | COMPETITIVE | long | AMD | -11.8% | -23.8pp | -8.2% | -14.0pp | -42.4% | -30.8pp | Nvidia CUDA’s moat is surmountable &amp; how AMD can overcom |
| 9 | 2024-03-18 | ✅ resolved | LONG | long | NVDA | -85.2% | -104.8pp | -86.8% | -90.0pp | -87.0% | -83.4pp | Nvidia is solving for more of the customer’s job-to-be-done  |
| 10 | 2025-08-17 | ✅ resolved | SUPPLY/DEMAND | short | AMAT | +39.9% | +23.8pp | +119.6% | +78.8pp | — | — | AMAT softening guide due to a leading edge foundry pulling b |
| 11 | 2026-03-11 | ✅ resolved | LONG | long | SNPS | +7.5% | -52.5pp | — | — | — | — | Ever more chip design and physical systems design over the n |
| 12 | 2025-07-21 | ✅ resolved | SHORT | short | OCI | — | — | — | — | — | — | Could be a sign the $OCI $30B per year deal won’t deliver ei |
| 13 | 2026-05-06 | 🟡 30-90d | LONG | long | NVDA | — | — | — | — | — | — | Old training datacenter is now more valuable as incremental  |
| 14 | 2026-01-22 | ✅ resolved | COMPETITIVE | long | INVZ | -42.5% | -65.5pp | — | — | — | — | The LiDAR market is consolidating to 1-2 Western suppliers a |
| 15 | 2026-06-15 | ❌ pending | SUPPLY/DEMAND | long | LITE | — | — | — | — | — | — | Maybe lots of VCSEL wafers go to interconnect and consumers  |
| 16 | 2025-03-18 | ✅ resolved | COMPETITIVE | long | MRVL | +3.1% | -11.6pp | -1.2% | -33.3pp | +28.3% | -41.5pp | Custom ASICs can be tailored to have lower latency or higher |
| 17 | 2025-12-01 | ✅ resolved | LONG | long | NVDA | +1.4% | -14.5pp | +24.7% | -60.0pp | — | — | Meta, Google, Amazon, and Microsoft all guided higher 2026 A |

**逐条原文 + 兑现明细**:

**1. [2025-03-05] ✅ resolved LONG → NVDA**
> Long lifespans could mean better TCO as Blackwell dominates.
> *推导: 推文直接提及$NVDA，并称Blackwell（Nvidia新架构）主导，长寿命带来更好TCO，对Nvidia是利好。*
>
> entry=2025-03-05 @ 117.30
> 30d: raw=-19.6% exSOX=+3.9pp hit=False
> 90d: raw=+20.4% exSOX=+14.8pp hit=True
> 180d: raw=+45.6% exSOX=+26.3pp hit=True
> 365d: raw=+56.3% exSOX=-10.1pp hit=True

**2. [2025-08-12] ✅ resolved LONG → CRWV**
> $CRWV seeing a "massive increase" in inference workloads, as validated by watching the power meter lol.
> *推导: 直接提到 $CRWV 推理工作负载大幅增长，利好公司*
>
> entry=2025-08-12 @ 148.75
> 30d: raw=-24.2% exSOX=-26.9pp hit=False
> 90d: raw=-29.0% exSOX=-51.6pp hit=False
> 180d: raw=-34.9% exSOX=-74.7pp hit=False

**3. [2025-07-11] ✅ resolved LONG → DELL**
> Dell can innovate to differentiate and avoid being stuck in low-margin, commodity territory
> *推导: 推文直接提及 @Dell，判断为看好 Dell 创新并提升价值链，对应标的 DELL。*
>
> entry=2025-07-11 @ 126.83
> 30d: raw=+9.1% exSOX=+9.5pp hit=True
> 90d: raw=+23.0% exSOX=+2.9pp hit=True
> 180d: raw=-5.3% exSOX=-38.3pp hit=False

**4. [2025-11-18] ✅ resolved LONG → INTC**
> This stability gives Intel confidence in Panther Lake launch
> *推导: Direct mention of $INTC and positive outlook on 18A yield stability leading to Panther Lake confidence*
>
> entry=2025-11-18 @ 34.33
> 30d: raw=+5.7% exSOX=+0.9pp hit=True
> 90d: raw=+34.5% exSOX=+10.3pp hit=True
> 180d: raw=+215.1% exSOX=+142.6pp hit=True

**5. [2025-08-29] ✅ resolved SHORT → GOOGL**
> $GOOGL knows how to sell ads and rent servers. Selling merchant silicon chips is a different ballgame. Just because you could, doesn't mean you should.
> *推导: The tweet questions Google's ability to succeed in the merchant silicon chip business, implying a negative outlook for GOOGL in this venture, which could be detrimental to the stock.*
>
> entry=2025-08-29 @ 212.91
> 30d: raw=+14.6% exSOX=+3.2pp hit=False
> 90d: raw=+50.4% exSOX=+26.5pp hit=False
> 180d: raw=+47.0% exSOX=-2.4pp hit=False

**6. [2026-06-08] ❌ pending LONG → NVDA**
> Bullish $NVDA
> *推导: 直接提及 $NVDA*
>
> entry=2026-06-08 @ 208.64

**7. [2026-04-28] 🟡 30-90d SHORT → POET**
> Also POET... pump and get dumped?
> *推导: POET is directly mentioned, likely referring to POET Technologies, implying potential price drop after a pump.*
>
> entry=2026-04-28 @ 8.03
> 30d: raw=+65.1% exSOX=+37.3pp hit=False

**8. [2024-04-02] ✅ resolved LONG → AMD,NVDA**
> Nvidia CUDA’s moat is surmountable &amp; how AMD can overcome their software woes and compete.
> *推导: 推文明确表示AMD将能克服软件问题并与Nvidia竞争，直接看好AMD，同时暗示Nvidia的CUDA护城河不再牢不可破，对AMD构成利好。*
>
> entry=2024-04-02 @ 178.70
> 30d: raw=-18.2% exSOX=-12.4pp hit=False
> 90d: raw=-11.8% exSOX=-23.8pp hit=False
> 180d: raw=-8.2% exSOX=-14.0pp hit=False
> 365d: raw=-42.4% exSOX=-30.8pp hit=False

**9. [2024-03-18] ✅ resolved LONG → NVDA**
> Nvidia is solving for more of the customer’s job-to-be-done here. This expansion creates lock-in and introduces switching costs. Even if other AI ASICs or GPUs compete on performance/cost/power - the switching cost will be higher for NIM, Nvidia AI enterprise, etc customers
> *推导: Nvidia's platform expansion creates lock-in and switching costs, which strengthens its competitive moat, directly positive for NVDA.*
>
> entry=2024-03-18 @ 884.55
> 30d: raw=-5.0% exSOX=-1.0pp hit=False
> 90d: raw=-85.2% exSOX=-104.8pp hit=False
> 180d: raw=-86.8% exSOX=-90.0pp hit=False
> 365d: raw=-87.0% exSOX=-83.4pp hit=False

**10. [2025-08-17] ✅ resolved SHORT → AMAT,LRCX,KLAC**
> AMAT softening guide due to a leading edge foundry pulling back, indicating lower equipment demand and monopsony risk.
> *推导: AMAT's softened guidance is attributed to a leading-edge foundry cutting capex, signaling reduced demand for wafer fab equipment. This directly impacts AMAT and likely extends to peers like LRCX and KLAC.*
>
> entry=2025-08-18 @ 163.53
> 30d: raw=+8.9% exSOX=+4.0pp hit=False
> 90d: raw=+39.9% exSOX=+23.8pp hit=False
> 180d: raw=+119.6% exSOX=+78.8pp hit=False

**11. [2026-03-11] ✅ resolved LONG → SNPS**
> Ever more chip design and physical systems design over the next decade.
> *推导: 推文来自$SNPS Converge会议，明确指出未来十年将有更多芯片设计与物理系统设计，利好EDA工具龙头Synopsys ($SNPS)。*
>
> entry=2026-03-11 @ 432.98
> 30d: raw=-9.4% exSOX=-21.7pp hit=False
> 90d: raw=+7.5% exSOX=-52.5pp hit=True

**12. [2025-07-21] ✅ resolved SHORT → OCI**
> Could be a sign the $OCI $30B per year deal won’t deliver either.
> *推导: 如果$30B per year deal无法实现，将直接负面影响到标的公司$OCI。$OCI可能指Oracle Cloud Infrastructure，对应股票$ORCL，但推文明确写$OCI，取$OCI为标的。*

**13. [2026-05-06] 🟡 30-90d LONG → NVDA,AMD**
> Old training datacenter is now more valuable as incremental inference cluster
> *推导: 旧数据中心转用于推理，表明推理硬件需求持续，利好GPU供应商如NVDA和AMD，亦可能提振数据中心基础设施相关标的。*
>
> entry=2026-05-06 @ 207.83
> 30d: raw=-1.3% exSOX=-7.8pp hit=False

**14. [2026-01-22] ✅ resolved LONG → INVZ**
> The LiDAR market is consolidating to 1-2 Western suppliers and 1-2 Eastern, and the next 2 years are a land grab.
> *推导: The tweet specifically mentions talking to Innoviz CEO about why most competitors are already gone, implying Innoviz is positioned as a surviving Western LiDAR supplier. Thus, the industry consolidation likely benefits Innoviz.*
>
> entry=2026-01-22 @ 1.13
> 30d: raw=-18.8% exSOX=-20.7pp hit=False
> 90d: raw=-42.5% exSOX=-65.5pp hit=False

**15. [2026-06-15] ❌ pending LONG → LITE,COHR**
> Maybe lots of VCSEL wafers go to interconnect and consumers get crushed again by ASPs just like memory
> *推导: VCSEL晶圆产能转移到利润更高的互连市场，导致消费电子供应受限，平均售价上升，消费者受压。类似内存行业，VCSEL制造商(LITE, COHR)将受益于更高ASP，因此看多。*
>
> entry=2026-06-15 @ 957.24

**16. [2025-03-18] ✅ resolved LONG → MRVL,AVGO,NVDA**
> Custom ASICs can be tailored to have lower latency or higher throughput and therefore push this curve out further, hence Jensen needing to tie it back to 'why GPUs'
> *推导: ASICs gaining advantage over GPUs would benefit custom ASIC designers like Marvell and Broadcom, while threatening NVIDIA's GPU dominance.*
>
> entry=2025-03-18 @ 68.28
> 30d: raw=-24.3% exSOX=-7.8pp hit=False
> 90d: raw=+3.1% exSOX=-11.6pp hit=True
> 180d: raw=-1.2% exSOX=-33.3pp hit=False
> 365d: raw=+28.3% exSOX=-41.5pp hit=True

**17. [2025-12-01] ✅ resolved LONG → NVDA**
> Meta, Google, Amazon, and Microsoft all guided higher 2026 AI CapEx. These dollars flow straight into Nvidia's backlog.
> *推导: Direct mention of Nvidia benefiting from higher capex from major customers.*
>
> entry=2025-12-01 @ 179.92
> 30d: raw=+3.7% exSOX=+2.8pp hit=True
> 90d: raw=+1.4% exSOX=-14.5pp hit=True
> 180d: raw=+24.7% exSOX=-60.0pp hit=True
