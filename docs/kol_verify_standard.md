# KOL 标准信号源验证流程 v1.0

> 输入一个 handle,管道自动输出: attribution 比例 / raw 命中率 / 板块 α / 能力圈 / 可跟性 / 置信度分级

---

## 1. 快速开始

### 1.1 完整跑

```bash
python -m scripts.kol_verify_standard --handle jukan05 \
  --db /workspace/data/signalboard_full.db \
  --out /workspace/outputs/scoreboard_jukan05.md
```

### 1.2 外部数据 (回归 / 第三方数据)

```python
from scripts.kol_verify_standard import verify_from_verified
import json

# 已经是 verified 格式的 json (e.g. p4p18 canonical)
verified = json.load(open("/workspace/logs/p4p18_strict_verified.json"))["his_predictions_verified"]
result = verify_from_verified(verified, handle="jukan05", output_path="/workspace/outputs/jukan_his.md")
print(f"grade = {result['grade']['grade']} — {result['grade']['reason']}")
```

### 1.3 回归测试 (已固化)

```bash
python -m scripts.jukan_regression       # 跑 jukan, expected 27/96.3%/A+
python -m scripts.serenity_regression    # 跑 serenity 光通信, expected 687/70.2%/A
```

---

## 2. 8 步管道

| 步 | 模块 | 输入 → 输出 |
|---|---|---|
| 1 | DB 拉取 | `handle` → `[predictions]` (raw list) |
| 2 | directional_validator | raw → `kept` + `dropped` (industry fact / product 预测 / 消费建议全部 drop) |
| 3 | attribution classifier | kept → `ORIGINAL/RELAYED/RELAYED+COMMENT` (启发式 + LLM fallback) |
| 4 | 加载 benchmarks | `tickers` → `{SPY, SOXX, SMH, KOSPI, TWSE, CSI300}` bars |
| 5 | scoreboard 验证 | kept + benchmarks → `raw_ret` + `excess` 双列 |
| 6 | 能力圈分析 | by_ticker → `strong_areas` + `weak_areas` (n≥3 + raw_hit 阈值) |
| 7 | 置信度分级 | raw_hit + Wilson + n → `A+/A/B/C/D` |
| 8 | 输出 markdown | 完整 scoreboard 报告 (4 分类 + 能力圈 + 跟单建议) |

---

## 3. 抽取层铁律 (自动拦截,不再靠人工事后抓)

### 铁律 1: directional 关键词必须出现
- **Long 关键词** (任一): `buy / long / 看多 / 做多 / 推荐 / 加仓 / strong buy / I will buy / I'll buy / bullish / undervalued / target price / call`
- **Short 关键词** (任一): `sell / short / 看空 / 做空 / 不推荐 / 减仓 / clear / put / overvalued / I don't recommend / avoid / I will sell / I'll sell / bearish`
- **都没有** → `direction=neutral` + `action=mark_commentary`

### 铁律 2: 对象必须是"股票/标的",不是产品/供应/消费品
- ❌ `buy electronics` ≠ `buy stock`
- ❌ `VR 不会出` 是 product launch 预测 ≠ `short 公司股票`
- ❌ `为什么 CEO 不宣布 sold-out` 是产业 fact ≠ `short 票`
- 命中 `NON_STOCK_OBJECT_PATTERNS` 或 `INDUSTRY_FACT_PATTERNS` → `mark_commentary`

### 铁律 3: 区分判断归属
- **ORIGINAL** (他/她自己的判断): 有 `I think / in my view / my take / 我认为 / 我判断` 关键词
- **RELAYED** (搬运机构): 引用 `Goldman Sachs / Morgan Stanley / GF Securities / 据彭博 / TrendForce` 等
- **RELAYED+COMMENT**: 既有搬运,又有 `However, I disagree / 但是我认为 / 我不同意`
- **只有 ORIGINAL + RELAYED+COMMENT 里他自己的部分计入能力分**; 纯 RELAYED 单独统计,不算他的能力

### Jukan 案例 (实测)
| 原文 | LLM 抽 | Validator 改后 | 命中规则 |
|---|---|---|---|
| MU 6-26: "Why MU CEO didn't announce HBM sold-out... Most industry insiders probably know about it." | short MU 180d | neutral (drop) | INDUSTRY_FACT |
| QCOM 5-22: "I still don't recommend Qualcomm stock. It's way overvalued." | short QCOM | short (keep) | SHORT_KEYWORDS |
| AAPL 12-26: "Apple VR 不会出 by end of 2025" | short AAPL | neutral (drop) | NON_STOCK_OBJECT |
| AAPL 12-13: "If you are planning to buy electronics, buy them right now" | short AAPL | neutral (drop) | NON_STOCK_OBJECT |
| "I am buying NVDA. Strong conviction long." | long NVDA | long (keep) | LONG_KEYWORDS |

---

## 4. 验证层铁律 (双列显示,永不许混)

### 铁律 4: 双列输出
每条预测同时输出 **`raw_ret` (绝对涨跌)** 和 **`excess_ret` (相对板块超额)** 两列,严格分开。

### 铁律 5: 真亏只看 raw
- **真亏 = `raw_ret < 0`** (跟 benchmark 无关)
- `raw > 0` 但 `excess < 0` → 标 "raw 涨, 跑输板块", **不算亏**

### 铁律 6: 4 分类 (禁止 "5 大赢/5 大输" 模糊说法)
- **raw 真赢**: `raw_ret > 0` 排序 (前 5 = "5 大 raw 真赢")
- **raw 真输**: `raw_ret < 0` 排序 (前 5 = "5 大 raw 真输")
- **跑赢板块**: `excess_ret > 0` 排序
- **跑输板块**: `excess_ret < 0` 排序 (含 raw 涨的)

### 铁律 7: 基准分层
- **vs SPY**: 大盘
- **vs SOXX / SMH**: 半导体板块 ETF
- **vs KOSPI / TWSE / CSI300**: 国别 (韩/台/中)
- 核心看 vs 板块 ETF (才是真 α)

### 铁律 8: 核心指标 raw 选股命中率
- `raw_hit_rate = n(raw>0) / n_total` (不依赖任何 benchmark)
- **跨 ticker 通用**, 适合作为 KOL 第一个看的指标

---

## 5. 置信度分级 (5 级)

| Grade | 条件 | 含义 |
|---|---|---|
| **A+** | raw_hit ≥ 80% + n ≥ 10 + Wilson ≥ 70% | 强信号, 可跟单 |
| **A** | raw_hit ≥ 70% + n ≥ 5 (n≥10 时 Wilson ≥ 60%) | 信号稳健, 可跟单 |
| **B** | raw_hit ≥ 60% + n ≥ 3 | 谨慎跟单 |
| **C** | raw_hit 50-60% 或样本不足 (3-4) | 仅供参考, 不可跟 |
| **D** | raw_hit < 50% 或样本严重不足 (< 3) | 不显著, 不可跟 |

---

## 6. 输出报告结构 (markdown)

```markdown
# {handle} — KOL Standard Scoreboard

**置信度**: **A+** — raw_hit 96.3%, Wilson 70.5%, n=27
**入参**: n_total=144 | n_resolved=27 | dropped=3

## 1. 核心指标 (raw 选股命中率 — 不依赖任何基准)
| 指标 | 值 |
|---|---|
| n_resolved | 27 |
| raw 涨 | 26 |
| raw 跌 | 1 |
| **raw 选股命中率** | **96.3%** |
| raw 中位 | +29.6% |
| Wilson 95% 下界 | 70.5% |

## 2. Excess vs Benchmarks
| Bench | n | med_excess | hit_rate |
|---|---|---|---|
| SPY | 27 | +5.4% | 81.5% |
| SOXX | 27 | +9.4% | 70.4% |
| SMH | 27 | +5.4% | 70.4% |

## 3. Attribution 分布 (铁律 3)
| 类型 | 计数 | 比例 |
|---|---|---|
| ORIGINAL | 26 | 96.3% |
| RELAYED+COMMENT | 1 | 3.7% |

## 4. 4 分类 (铁律 6)
### 4.1 raw 真赢
### 4.2 raw 真输
### 4.3 跑赢板块
### 4.4 跑输板块

## 5. 能力圈 (ticker cluster)
### 5.1 强项 (raw_hit ≥ 60% + n ≥ 3)
### 5.2 弱项 (raw_hit < 50% + n ≥ 3)

## 6. Dropped 误抽 (铁律 1+2 自动拦截)
[3 条 short 因 directional validator 自动 drop]

## 7. 跟单建议
✅ 可跟单 — 跟 A+ 信号
- 能力圈: MU, INTC, SNDK, ASML
- 避开: NVDA (3/9 hit)
- ⚠️ 样本 27 < 50, 建议加观察期
```

---

## 7. 回归测试 (确认管道可信)

```bash
# Jukan 回归 (P4-19 v4 canonical, 27/96.3%)
python -m scripts.jukan_regression
# expected: 27/96.3%/+29.6%/A+

# Serenity 光通信 8 票 3m 回归 (P3-12 canonical)
python -m scripts.serenity_regression
# expected: 687/70.2%/+0.5%/A, 强 6 (LITE/COHR/AAOI/AXTI/AEHR/SIVE), 弱 1 (NBIS)
```

两个回归都通过 = 管道 0 偏差, 可以批量跑后续 9 人。

---

## 8. 模块文件清单

| 文件 | 作用 |
|---|---|
| `signalboard/extract/directional_validator.py` | 铁律 1+2 (关键词 + 对象区分) |
| `signalboard/extract/attribution.py` | 铁律 3 (attribution 启发式 + LLM) |
| `signalboard/quality/scoreboard.py` | 铁律 4-8 (双列 + 4 分类 + raw 核心) |
| `scripts/kol_verify_standard.py` | 8 步主流程, 接受 handle / DB / external predictions |
| `scripts/jukan_regression.py` | Jukan 回归 (P4-19 v4) |
| `scripts/serenity_regression.py` | Serenity 光通信 8 票 3m 回归 (P3-12) |

---

## 9. 已知限制 (跟 9 个新 KOL 跑前要确认)

- **韩股 .KS / 台股 .TW / 深股 .SZ** — Polygon free 不支持, 17 条 Jukan 韩股数据无法 verify
- **Polygon price 滞后 ~10 天** — 短期 horizon (1m, 1w) 数据可能不全
- **LLM attribution fallback** — 启发式无 marker 时走 LLM, 偶尔误判 (测试覆盖 5/5)
- **direction 关键词英中混合** — 长仓有 16 个, 短仓 14 个; 罕见拼写变体可能漏
- **Wilson 95% 下界 < 50%** — 严格不显著, 需要 n 大才升级 A+
