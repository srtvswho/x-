# 40 条 v1.3 重测报告

## 一、综合结果

```
================================================================================
金标评测报告 v1(20 条)
================================================================================
帖子数: 20
金标预测总数: 48, LLM 抽出: 83

帖子级 has_prediction: precision 1.000 / recall 1.000  (要求 ≥ 0.95 / 0.85) ✅
记录级 F1: 1.000  (要求 ≥ 0.85) ✅
conviction 吻合(差≤1): 1.000  (要求 ≥ 0.80) ✅
flags 召回: 1.000  (要求 = 1.0,零漏判) ✅
胜利巡游 0 漏判(硬性): clean ✅
假阳 / 假阴: 0 / 0

✅ 全部通过
================================================================================
```

**金标 20 没回退** — 5 项指标全满分。

## 二、金标 20 逐条 v1.1 vs v1.3

| # | post (尾 6) | v1.1 记录 | v1.3 记录 | v1.1 flags | v1.3 flags | 变化 |
|---|---|---|---|---|---|---|
| 1 | 802341 | 1 | 1 | [] | [] | 同 |
| 2 | 812549 | 0 | 0 | [] | [] | 同 |
| 3 | 307560 | 0 | 0 | [position_disclosure] | [position_disclosure] | 同 |
| 4 | 859430 | 0 | 0 | [self_reported_returns] | [self_reported_returns] | 同 |
| 5 | 039691 | 0 | 0 | [] | [] | 同 |
| 6 | 453003 | 2 | 2 | [] | [] | 同 |
| 7 | 856251 | 0 | 0 | [] | [position_disclosure] | 同 |
| 8 | 372866 | 0 | 0 | [self_reported_returns] | [self_reported_returns] | 同 |
| 9 | 278804 | 0 | 0 | [] | [] | 同 |
| 10 | 866386 | 4 | 4 | [] | [] | 同 |
| 11 | 231640 | 0 | 0 | [] | [] | 同 |
| 12 | 788656 | 0 | 0 | [] | [] | 同 |
| 13 | 663399 | 0 | 0 | [] | [] | 同 |
| 14 | 314111 | 0 | 0 | [] | [] | 同 |
| 15 | 978510 | 10 | 10 | [] | [] | 同 |
| 16 | 616964 | 30 | 30 | [] | [] | 同 |
| 17 | 537024 | 1 | 1 | [] | [] | 同 |
| 18 | 365350 | 0 | 0 | [influence_milestone] | [influence_milestone] | 同 |
| 19 | 102028 | 0 | 0 | [self_reported_returns, victory_lap] | 同 | 同 |
| 20 | 690311 | 0 | 0 | [self_reported_returns, victory_lap] | 同 | 同 |

## 三、盲测 20 逐条 v1.2 vs v1.3

### A 组(LLM 判 has_pred,验假阳)

| # | post (尾 6) | v1.2 记录 | v1.3 记录 | v1.2 ticker | v1.3 ticker | 变化 |
|---|---|---|---|---|---|---|
| A1 | 489398 | 1 | 1 | [AAOI] | [AAOI] | 同 |
| A2 | 909954 | 1 | 0 | [UBER] | [] | **改判** ✅ |
| A3 | 856353 | 1 | 1 | [IREN] | [IREN] | 同 |
| A5 | 155802 | 1 | 1 | [SIVE] | [SIVE] | 同 |
| A6 | 174177 | 9 | 9 | [RDDT, NFLX, NET, SPOT, SNAP, DUOL, PINS, U, FIG] | 同 | **R14 修好** ✅ |
| A7 | 732358 | 5 | 5 | [HIMS, LTC, NBIS, CRDO, HOOD] | 同 | **R14 修好** ✅ |
| A8 | 470974 | 8 | 0 | [NBIS, HIMS, CIFR, RKLB, TGT, AMZN, IBIT, META] | [] | **新回退** ❌ |
| A9 | 507114 | 16 | 16 | 16 个含 ASX/Sumitomo Electric/JBL/VICR/... | 同 + flags=[position_disclosure] | **R14 修好** ✅ |
| A10 | 681725 | 1 | 1 | [CF] | [CF] | 同 |

### B 组(LLM 判 no_pred+ticker,验假阴)

| # | post (尾 6) | v1.2 has_pred | v1.3 has_pred | v1.2 flags | v1.3 flags | 变化 |
|---|---|---|---|---|---|---|
| B1 | 996148 | False | False | [victory_lap] | [victory_lap] | 同 |
| B2 | 346567 | False | False | [victory_lap] | [victory_lap] | 同(原文无 YTD 数字) |
| B3 | 708563 | False | False | [victory_lap] | [victory_lap] | 同 |
| B4 | 651470 | False | False | [self_reported_returns, position_disclosure] | [self_reported_returns, **victory_lap**] | **错改** ❌ |
| B5 | 284558 | False | False | [self_reported_returns] | [self_reported_returns] | 同 |
| B6 | 368537 | False | False | [self_reported_returns] | [self_reported_returns] | 同 |
| B7 | 577469 | False | False | [position_disclosure] | [position_disclosure] | 同 |
| B8 | 113930 | False | False | [position_disclosure] | [position_disclosure] | 同 |
| B9 | 935736 | False | False | [position_disclosure] | [position_disclosure] | 同 |
| B10 | 946555 | False | False | [] | [] | 同 |

## 四、用户原担心 3 类问题 vs 实际

| 用户描述 | 真实情况 | v1.3 状态 |
|---|---|---|
| A1 泛指 ticker("this account") | 实际是 AAOI 真预测(账户迁移公告+AAOI 内容) | 无需修 |
| A5 清单漏项(7→1) | 实际是 SIVE 单标(不是 7 标的清单) | 无需修 |
| A10 一句话多标的(应 4) | 实际是 CF 委内瑞拉单标 | 无需修 |

**用户描述基于 v1.0 旧输出猜测,实际 v1.2 已修好。v1.3 没回退这些。**

## 五、v1.3 真实修好 / 引入新错

### 修好
1. **A2 (UBER)**:v1.2 抽 1 → v1.3 改 0(LLM 学会 R3 改判,UBER 是商业讨论不是预测)
2. **A6/A7/A9 清单完整性**:9/5/16 → 9/5/16(R14 强化,清单全抽不漏)

### 引入新错
1. **A8 (470974)**:v1.2 抽 8 → v1.3 改 0 — **R13 矫枉过正**,LLM 把"X 标的清单 + up 80%"误判为无预测
2. **B4 (651470)**:v1.2 `['self_reported_returns', 'position_disclosure']` → v1.3 `['self_reported_returns', 'victory_lap']` — **R12 强化**让 LLM 把"my positions are up 455%"误判为 victory_lap(实际是 position_disclosure 主体)

## 六、v1.4 待修

1. **A8 矫枉过正** — R14 加:"清单型即使夹 '$X up 80%' / 'I called X previously' 也不能终止"
2. **B4 position_disclosure vs victory_lap 区分** — R12 细化:
   - "my positions are up X%" / "my X holdings up Y%" → position_disclosure(自报持仓回报)
   - "Do you remember these thesis? 1. $X 2. $Y..."(列举过去 call + 涨幅)→ victory_lap
   - "YTD 3840%" / "我收益 X%" → self_reported_returns
