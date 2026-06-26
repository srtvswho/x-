# 大V情报 — 模块 2 (v2.0.0-intel) 抽取测试结果

**测试时间**: 2026-06-26 (北京)
**测试范围**: 12 条样本 (4 大V 各 3 条, 覆盖 long/short/neutral/消费误抽/反驳叙事)
**LLM**: `deepseek-v4-pro` (跨项目硬规则)
**Prompt 版本**: `v2.0.0-intel` (独立, 不混 v1.4.1)

---

## 1. 抽取质量总览

| 维度 | 数值 |
|---|---|
| 成功抽取 | 12/12 (100%) |
| 方向 short 抽取 | 0 (符合实际, 12 条里没明确 short) |
| **误抽率** | **0%** (Malbec 消费建议正确归 neutral, AAOI 估值正确归 long) |
| Tokens 总耗 | ~32,200 (avg 2,683/条) |
| 估算成本 | ~$0.04 (12 条) |

---

## 2. 12 条逐条评估

### 1️⃣ jukan: TSM 涨价 (RELAYED) ✅ 完美
**原文**: "Culpium: TSMC is pushing for a 5–10% price increase across all advanced nodes, including 7nm. ... $TSM"
- direction=`neutral` ✓ (转发产业 fact, 非作者判断)
- ticker=`[TSM]` ✓
- bottleneck=`晶圆代工` ✓
- attribution=`RELAYED` ✓
- summary="转推 Culpium: TSMC 计划对 7nm 等先进制程涨价 5-10%, 因管理层看到内存厂高定价后想跟进."

### 2️⃣ jukan: TPU/Substrate 卡点 ✅ 完美
**原文**: "FundaAI: TPU Update ... Substrate remains the primary bottleneck, but Google is actively pushing substrate manufacturers to expand more capacity. ..."
- direction=`neutral` ✓
- bottleneck=`Substrate` ✓ (卡点识别准)
- attribution=`RELAYED` ✓
- summary=... (50+ 字细节: Pumafish, Triggerfish, SRAM 增量, 联发科参与)

### 3️⃣ jukan: Samsung HBM4 收入 ✅ 完美
**原文**: "Samsung Electronics HBM4 Revenue Tops $1 Billion, Just Four Months After Becoming First to Mass Produce"
- direction=`neutral` ✓
- bottleneck=`HBM` ✓
- summary 准

### 4️⃣ serenity: 自嘲 + MU/SNDK ✅ 完美
**原文**: "Nah, gonna fill out the job application for $WEN ... Even $MU and $SNDK ridiculous performance today couldn't save my port. ... hoping Sweden gets mogged with a 2-0 to represent the 20% drop."
- direction=`neutral` ✓ (自嘲, 不是真方向)
- ticker=`[WEN, MU, SNDK]` ✓ (3 ticker 全抓到)
- attribution=`ORIGINAL` ✓
- summary="作者自嘲投资组合亏损, 戏称要去 Wendy's 打工, 即使 MU 和 SNDK 当日暴涨也未能挽救"

### 5️⃣ serenity: AAOI 估值 (历史回顾+押注) ✅ 准
**原文**: "@hobielandrith I posted about $AAOI at $2.1B MC when someone called photonics 'late'. Then at $5.3B after earnings. Then $11B now. Unless their projections are wrong, doing $5.4B annual revenue ($471m/m) as a photonics company probably commands higher valuations."
- direction=`long` ✓ ("commands higher valuations" = 隐含 long)
- ticker=`[AAOI]` ✓
- bottleneck=`光通信` ✓
- summary 准 (提到 21亿→53亿→110亿 市值轨迹)

### 6️⃣ serenity: SIVE fabless 比较 ⚠️ 略弱
**原文**: "Do you mean InP fab? I'm not sure why people are trying to compare InP fabs, $SIVE is not mass producing lasers in-house. They're using Win Semi and foundries, Sivers is a fabless designer so they don't need capex."
- direction=`neutral` ✓
- ticker=`[SIVE]` ✓
- bottleneck=`InP` ✓
- **rebuts_narrative=`null`** ⚠️ — 原文明显反驳"用 InP fab 比较 SIVE"的做法, 没抽到 (下次可强化 prompt 例)

### 7️⃣ zephyr: Anthropic 算账 ✅ 完美
**原文**: "Actually pretty small ($72M) Anthropic identified 25M interactions ... 25 trillion Tokens ... So it's nearly around $72M and around $160M if no caching is assumed"
- direction=`neutral` ✓ (算账, 不是方向)
- summary 准 (详细复述了 token 假设)

### 8️⃣ zephyr: $5B-10B ARR scenario ✅ 准
**原文**: "Depends. They have a huge on-prem government-related biz. Could they win $2B-$3B in government contracts and reach $2B ARR thru their cloud biz ... hitting $5B ARR can happen ... To hit $10B/yr they will need to adopt Anthropic/OAI tactics and serve tokens at 5x the current price (95% GM)"
- direction=`neutral` ✓
- summary="纯业务讨论, 无股票判断." 准 (LLM 主动识别"无股票判断")

### 9️⃣ zephyr: CXMT IPO 转发 ✅ 完美
**原文**: "Great post from SemiAnalysis CXMT will generate nearly $55B in revenue this year They will IPO at nearly $50B market cap GM is easily over 75% Will be the most explosive IPO of China ever"
- direction=`neutral` ✓ (转推, 不算作者判断)
- bottleneck=`存储` ✓ (CXMT 是长存, 国产 DRAM 龙头)
- attribution=`RELAYED` ✓

### 🔟 austin: Intel Foundry good Thu ⚠️ 模糊
**原文**: "Intel Foundry had a very good Thursday. $INTC"
- direction=`neutral` (LLM: "客观描述, 未明确给出投资方向")
- 但 austin 之前 7/8 商业洞察都对, "had a very good Thursday" 隐含 long
- **这是边界 case**, LLM 保守归 neutral, 合理 (没 "bullish" / "buy" 关键词)
- 如果用户想"含蓄 long 也算 long", 可调 prompt 放宽

### 1️⃣1️⃣ austin: Malbec 红酒消费 ✅ 完美
**原文**: "Yo @vikramskr I bought a $7 Malbec from Costco (under the Kirkland label) and it was surprisingly decent lol"
- direction=`neutral` ✓ (**没误抽 short**! 消费建议正确归 neutral)
- ticker=`null` ✓ (Malbec 是酒名不是公司)
- **关键**: 触发 P5 误抽陷阱 #4 (消费建议), LLM 正确识别

### 1️⃣2️⃣ austin: Bullish NVDA ✅ 完美
**原文**: "Bullish $NVDA"
- direction=`long` ✓
- ticker=`[NVDA]` ✓
- attribution=`ORIGINAL` ✓
- summary="作者明确表态 bullish NVDA (1 词短句, 强烈方向性)." 准

---

## 3. 关键质量指标

### 抽得准的 (10/12, 83%)
- ✅ TSM/Samsung HBM4/Anthropic/CXMT/Malbec/Bullish NVDA (6 条产业 fact + 明确 long)
- ✅ AAOI 估值 (隐含 long 抓到)
- ✅ MU/SNDK 自嘲 (没误抽 short)
- ✅ TPU 卡点 (Substrate 卡点识别)
- ✅ $5B-10B ARR (主动识别"无股票判断")

### 略弱 (2/12, 17%)
- ⚠️ SIVE 反驳 InP fab (rebuts_narrative 漏抽)
- ⚠️ Intel Foundry good Thu (隐含 long 没抓到, 归 neutral)

### 没误抽 (12/12, 100%) ✓
- ✅ Malbec 消费建议正确归 neutral (P5 误抽陷阱 #4 没踩)
- ✅ 自嘲没误抽 short
- ✅ 12 条没一条 long 误抽

---

## 4. 评估结论

**质量**: **8.5/10**
- 0 误抽 (12 条都干净)
- 0 short 误抽 (8/8 short 误抽教训守住)
- 卡点分类准 (HBM/Substrate/光通信/InP/晶圆代工/存储 全部对)
- attribution 准 (RELAYED/NA/ORIGINAL 区分到位)
- 隐含 long 多数抓到 (AAOI 估值 抓到了)

**可改进点** (下次扩到全量前可微调):
1. rebuts_narrative 加 prompt 例: "我反驳..." / "我不同意..." 显式触发
2. "had a very good" 这类含蓄 long 是否归 long — 需要拍板

---

## 5. 下一步建议

1. **扩到全量**: 给最近 30 天 1519 条全跑 (4 大V), 估算 $0.04 × 1519 / 12 ≈ $5
2. **入库**: 加 `extractions_intel` 表 (FK → raw_posts), 落库 + 幂等
3. **接进 daily cron**: 模块1 + 模块2 串行, 每日 06:00 北京时间跑
4. **先小扩**: 先跑最近 7 天 (austin 17 条) 验证入库逻辑, 再扩到 30 天 → 全量
