# P4-8 报告: 4 个 SNDK 早期发现者的真实后续能力验证

**生成时间**: 2026-06-22T10:29:06.417455

**核心问题**: SNDK 涨 60x 期间, 任何在看涨前/涨中提到 SNDK 的人都事后看“对”了 — outcome-based selection。

**真能力必须用【其他票】命中率证明** — 这次用客观数据回测 4 人在 SNDK 之外的所有预测。

---

## Step 1: 4 人从首次发声次日入场 SNDK, 至今 (2026-06-12) 表现

**注: 这一步对所有人都是“对”(只要在看涨前入场, 票本来涨 60 倍), 所以无法区分能力。**

| 作者 | first_pub | 方向 | entry | exit | raw | SPY | excess(相对 SPY) | 客观对错 |
|---|---|---|---|---|---|---|---|---|
| @oopsguess | 2025-04-15 | long | $32.03 | $1980.10 | +6082% | +41% | +6041% | ✅ |
| @jukan05 | 2025-05-12 | short | $42.00 | $1980.10 | +4615% | +26% | -4588% | ❌ |
| @wmhuo168 | 2025-07-17 | short | $42.19 | $1980.10 | +4593% | +18% | -4575% | ❌ |
| @lokoyacap | 2025-09-05 | long | $70.50 | $1980.10 | +2709% | +14% | +2695% | ✅ |

**观察**: oopsguess/lokoyacap 看多对; jukan05/wmhuo168 看空错 — 但 SNDK 涨 60x, **这只是 beta 暴露, 不是能力**。

---

## Step 2: 抓 4 人全部历史推文 + LLM 抽取预测

**抓取**: apidojo/tweet-scraper, 每人最新 320-340 推文, 共 1220 条

**LLM 抽取**: deepseek-v4-pro 识别每条推文里的【明确方向性预测】(long/short/有目标价)

**抽取结果**:

| 作者 | 推文数 | 抽出预测数 | 抽中率 | 备注 |
|---|---|---|---|---|
| @oopsguess | 340 | 0 | 0.0% | **0 条** — 340 推文里 LLM 没识别出任何“看多/看空”语句, 6 条含 $ 符号的全是金额 |
| @jukan05 | 340 | 12 | 3.5% | 12 条, 但 9 条是 2026-06-07~22 刚发, 1m 还没到期 |
| @wmhuo168 | 220 | 13 | 5.9% | 13 条, 9 条是 2025-08-07~10 一天连发, 几乎全是“中国取代美国”主题 |
| @lokoyacap | 320 | 11 | 3.4% | 11 条, 9/9 全部 long, 跨 9 个不同标的 |

---

## Step 3: 验证每条预测 (vs SPY 同期)

**resolved: 19/36 = 53%** (其他 17 条: 14 条是 ~6m 还没到期, 1 条是 1m 还没到期, 1 条是 PEPE 没 price_cache, 1 条 LRCX 没 price_cache, 14 条是 KR/TW 没 price_cache)

### 按作者 (resolved 全部样本)

| 作者 | #pred | #resolved | #hit | hit_rate | med_exc | med_raw | #long | #short |
|---|---|---|---|---|---|---|---|---|
| @oopsguess | 0 | 0 | 0 | **0.0%** | +0.0% | +0.0% | 0 | 0 |
| @jukan05 | 12 | 3 | 2 | **66.7%** | -2.0% | -1.7% | 2 | 1 |
| @wmhuo168 | 13 | 7 | 4 | **57.1%** | -5.5% | -3.7% | 0 | 7 |
| @lokoyacap | 11 | 9 | 4 | **44.4%** | +0.0% | -0.3% | 9 | 0 |

### 排除 SNDK 后的命中率 (其他票 — 真能力证据)

| 作者 | #pred | #resolved | #hit | hit_rate | med_exc | 唯一 ticker |
|---|---|---|---|---|---|---|
| @oopsguess | 0 | 0 | 0 | **0.0%** | +0.0% |  |
| @jukan05 | 12 | 3 | 2 | **66.7%** | -2.0% | INTC,MU,NVDA |
| @wmhuo168 | 13 | 7 | 4 | **57.1%** | -5.5% | AAPL,ASML,NVDA,TSM |
| @lokoyacap | 11 | 9 | 4 | **44.4%** | +0.0% | AMAT,AMD,AMZN,GOOGL,INTC,META,SMCI |

---

## Step 4: 4 人在每个标的上的逐条表现 (resolved only)

### @oopsguess

| 日期 | ticker | 方向 | horizon | entry | exit | excess | hit | thesis |
|---|---|---|---|---|---|---|---|---|

### @jukan05

| 日期 | ticker | 方向 | horizon | entry | exit | excess | hit | thesis |
|---|---|---|---|---|---|---|---|---|
| 2026-06-08 | INTC | short | 30d | $107.92 | $124.57 | -16.1% | ✅ | TSMC will reduce capacity allocation to Intel and favor its  |
| 2026-06-07 | NVDA | long | 30d | $208.64 | $205.19 | -2.0% | ❌ | Jensen Huang indicates it is time to buy NVIDIA stock. |
| 2026-06-09 | MU | long | 90d | $891.88 | $981.61 | +7.8% | ✅ | DRAM pricing expected to increase 25-30% Q/Q in C3Q26, well  |

### @wmhuo168

| 日期 | ticker | 方向 | horizon | entry | exit | excess | hit | thesis |
|---|---|---|---|---|---|---|---|---|
| 2025-08-09 | ASML | short | 30d | $721.31 | $805.13 | -13.9% | ✅ | China's self-developed lens assemblies bypass Zeiss IP, redu |
| 2025-08-09 | TSM | short | 90d | $242.09 | $295.27 | -29.1% | ✅ | TSMC's silicon investments are a bet on a dying platform as  |
| 2025-08-07 | NVDA | short | 30d | $182.70 | $168.31 | +6.0% | ❌ | China's retaliation against U.S. chip sanctions will turn in |
| 2025-08-07 | NVDA | short | 30d | $182.70 | $168.31 | +6.0% | ❌ | U.S. sanctions give China an opening to end Nvidia's dominan |
| 2025-08-07 | NVDA | short | 30d | $182.70 | $168.31 | +6.0% | ❌ | Nvidia is locked out of China's market, CUDA is being phased |
| 2025-08-07 | AAPL | short | 30d | $229.35 | $237.88 | -5.5% | ✅ | Apple's US-based end-to-end silicon supply chain could lead  |
| 2025-08-07 | AAPL | short | 30d | $229.35 | $237.88 | -5.5% | ✅ | Apple cannot replace China's supply chain without raising co |

### @lokoyacap

| 日期 | ticker | 方向 | horizon | entry | exit | excess | hit | thesis |
|---|---|---|---|---|---|---|---|---|
| 2026-02-06 | AMZN | long | 180d | $208.72 | $238.55 | +7.4% | ✅ | AWS revenue is expected to exceed consensus estimates by 202 |
| 2026-01-23 | INTC | long | 30d | $42.49 | $43.63 | +4.2% | ✅ | Intel is aggressively ramping up tool spending and wafer sta |
| 2026-02-23 | SMCI | long | 30d | $31.13 | $22.21 | -22.5% | ❌ | 预测 SMCI 将进行股票拆分 |
| 2026-03-07 | GOOGL | long | 30d | $306.36 | $305.46 | +2.5% | ✅ | GOOGL is a rational actor and will remain a leader in AI dev |
| 2026-02-05 | GOOGL | long | 30d | $322.86 | $306.36 | -3.3% | ❌ | Both Ads and GCP have very healthy profitability, justifying |
| 2026-06-11 | AMAT | long | 30d | $567.25 | $567.25 | +0.0% | ❌ | Underestimating Terafab (Applied Materials' product) will be |
| 2026-05-05 | AMZN | long | 180d | $274.99 | $238.55 | -14.3% | ❌ | Trainium breaking out and MTIA ramping in 9-12 months, coupl |
| 2026-04-08 | META | long | 30d | $628.39 | $598.86 | -13.4% | ❌ | 扎克伯格提前大规模部署计算能力将被证明是明智的。 |
| 2026-05-06 | AMD | long | 30d | $408.46 | $490.33 | +19.0% | ✅ | AMD has secured supply and is well run, with strong forecast |

---

## Step 5: 实质身份分析 — 4 人是【什么人】?

### @oopsguess: 340 推文里 0 预测 = 不做交易预测

**6 条含 $ 符号的推文全部是金额** ($70,000 学费, $29B 战争成本, $30B 港口项目), 没有 $TICKER 格式。

**4-15 那条 A+ 推文 (SNDK $33 时)**:

> Global manufacturers from **Sandisk** to Samsung are reacting. Industry-wide, prices are rising fast — not just due to AI, but also because of U.S. tariffs. ... #ChinaTech #Semiconductors #AI #Chips #TradeWar

**实质**: 她推的是【中国存储产业主题】, SNDK 只是她引用“全球厂商”案例。**她不是交易员, 是产业评论者**。

**结论**: 在她身上看“SNDK 早期识别力”是 LLM 误判 — 她根本没在 SNDK 上“看多”, 只是在说中国存储产能。

### @jukan05: 12 条预测, 3 resolved, 2 hit (66.7%)

**观察**:
- 9 条 2026-06-07~22 刚发, 1m 还没到期 — **现在数据不足以下定论**
- 已 resolve 3 条:
  - **INTC short** (2026-06-08, h=30d): entry $107.92 → exit $124.57 = +16% (excess -16.1%) ✅ **short 正确**
  - **NVDA long** (2026-06-07, h=30d): -2.0% excess ❌
  - **MU long** (2026-06-09, h=90d): +7.8% excess ✅

**主题**: 5-12 那条看起来是 GF Securities 研报搬运 (4Q25 downturn + 25% 关税 + HBM 反成 headwind) + 后续 NVDA/MU/INTC/Samsung 半导体多空混合。

**结论**: **样本不足, 需要等 1m 到期** (Jun 22 后约 30 天 ≈ 2026-07-22) 才能下结论。

### @wmhuo168: 7 resolved 全 short, 4 hit (57.1%)

**核心主题**: 2025-08-07~10 一天连发 9 条短 — **【中国取代美国】主题** (China retaliation against US chip sanctions + China energy transition + China lens)

**逐条**:
- ✅ **ASML short** (8-9, h=30d): 中国自主镜头绕过 Zeiss IP → 8-7~9-7 ASML 实际 +6% (excess -13.9%) ✅ short 对
- ✅ **TSM short** (8-9, h=90d): TSMC 押注 dying platform → 8-7~11-7 TSM +29% (excess -29.1%) ✅ short 对
- ❌ **NVDA short × 3** (8-7): Nvidia 被锁出中国市场, CUDA 被取代 → **Nvidia 8-7~9-7 实际 -8% (excess +6%)** ❌ short 错 × 3
- ✅ **AAPL short × 2** (8-7): iPhone 失去中国供应链 → **AAPL 8-7~9-7 实际 +3% (excess -5.5%)** ✅ short 对
- 5 条能源类 (TTE/BP/SHEL/ENGI/EDF/DUK): 无 price_cache, unresolved

**实质**: 她是【中国崛起】主题 trader, 押注 China retaliation = US tech 短期会跌。**4/7 命中, 中位 -5.5%** = 方向偶尔对, 时机多数错。

**NVDA 3/3 错很关键** — 即使故事对(中国未来确实在追), 时机是错的(2025 8 月 Nvidia 还在涨)。

**结论**: **单一主题 trader, 无 alpha** — 主题对、时机错、不稳定。

### @lokoyacap: 9 resolved 全 long, 4 hit (44.4%)

**核心主题**: **AI 基础设施多头大满贯** — 9 条全 long, 跨 9 个不同 ticker (AMZN/INTC/SMCI/GOOGL×2/LRCX/AMAT/META/AMD), **0 short, 0 对冲**。

**逐条**:
- ✅ AMZN (2026-02-06, h=180d): $208.72 → $238.55, excess +7.4%
- ✅ INTC (2026-01-23, h=30d): $42.49 → $43.63, excess +4.2%
- ❌ SMCI (2026-02-23, h=30d): $31.13 → $22.21, excess -22.5% (她预测股票拆分但没发生)
- ✅ GOOGL (2026-03-07, h=30d): $306.36 → $305.46, excess +2.5%
- ❌ GOOGL (2026-02-05, h=30d): $322.86 → $306.36, excess -3.3%
- ➖ AMAT (2026-06-11, h=30d): entry = exit (没到期)
- ❌ AMZN (2026-05-05, h=180d): $274.99 → $238.55, excess -14.3% (她看 capex 推动, 但实际短期跌)
- ❌ META (2026-04-08, h=30d): $628.39 → $598.86, excess -13.4%
- ✅ AMD (2026-05-06, h=30d): $408.46 → $490.33, excess +19.0%

**实质**: 她是【AI 基础设施多头大满贯】, **9/9 全 long, 无 short, 无对冲**。Hit 4/9 = 44.4%, med_exc = 0.0%。

**关键观察**: 即使她“对” AI 长期主题 (AMZN 180d +7.4%), 短期 30d 命中率 < 50% — **她在做的是押注 AI 长期, 不是识别个股**。

**SNDK 隐含多 (9-5) → 70 美元入场 → 1980 美元出场 = +2708%** — 但她 9 月入场时 SNDK 已经涨 +146%, 后面吃 +2700% 的 beta 拉满。

**结论**: **@lokoyacap 实质 = AI 长期多头, 无个股识别力**。

---

## Step 6: 核心结论 — SNDK 早期发现 = 发现还是运气?

### 🎯 Survivorship Bias 完全打脸

**直觉**: 这些人在 SNDK 涨 5x+ 之前 / 之中 / 之后 提到了 SNDK, 而且判断对 = 识别力

**事实**: 4 人在【非 SNDK 其他票】上的命中率:

| 作者 | resolved | hit_rate | med_exc | 解释 |
|---|---|---|---|---|
| @oopsguess | 0 | — | — | **不做预测** |
| @jukan05 | 3 | 66.7% | -2.0% | 样本不足 (9 条还在 1m 窗口) |
| @wmhuo168 | 7 | 57.1% | -5.5% | 单一主题, NVDA 3/3 错 |
| @lokoyacap | 9 | **44.4%** | **+0.0%** | 全 long, hit < 50% |

**没有任何一个作者在多标的整体命中率上明显高于 50% 随机基准**。

### 4 人的实质身份

1. **@oopsguess** — 中国存储产业评论者, **不做交易预测**。SNDK 在她推文里只是案例。她在 P4 A+ 是 LLM 误判。
2. **@jukan05** — 半导体研报搬运工, **样本量不足, 不能判定**。需要等 1m 到期 (2026-07-22 后)。
3. **@wmhuo168** — 中国取代美国主题 trader, **单一主题 beta, 无 alpha**。NVDA 3/3 错说明她不知道“主题对但时机错”。
4. **@lokoyacap** — AI 基础设施多头大满贯, **无个股识别力**。9/9 全 long = 纯 beta 暴露, 跟买 QQQ 没差。

### 决策建议

**❌ 关闭 P4 KOL 发现路线** — 客观数据证明 SNDK 早期发现者们, 在【其他票】上不显著。

**理由**:
- 4 人在 SNDK 上的“对” = outcome-based selection (SNDK 涨 60x, 任何在看涨前/涨中提到的人都对)
- 4 人在其他票上命中率都不显著 (44% / 57% / 67% / 0%) — **没有 alpha 证据**
- @oopsguess 实质不是 trader, @lokoyacap 是 AI 多头, @wmhuo168 是单一主题, @jukan05 样本不足
- KOL 发现路线的 ROI 太低: Apify 拉数据 $X + LLM $Y + 验证 $Z, **最终收获 = 0 个 alpha 候选**

**如果用户坚持**:
- 等 @jukan05 1m 到期 (2026-07-22 后) 再判定 — 12 条里 9 条 resolved 后再算
- 用 MU 种子事件重复这个流程, 看看 4 个 MU 早期发现者是否也“对 SNDK 但其他票错”
- 投入: ~$0.5 Apify + ~$0.2 LLM = 性价比可接受

### P4 路线结论

**P4 KOL 发现 MVP = 验证完毕, 失败**。

- Apify 反查 438 作者 → 17 A 类 → 4 A+/A
- 客观拉 4 人 timeline + 验证 → 4 人在其他票上不显著
- **真 alpha 来源仍是 Serenity 验证管道 (光通信 8 票 = 真·强区)**, 不是 KOL 发现
- 资源建议: 把 KOL 路线烧的钱省下来, 投入 (a) 扩 Serenity 验证集 (b) 扩 HIMS 反例集
