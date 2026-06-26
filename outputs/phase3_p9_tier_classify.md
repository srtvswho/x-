# P3-9 预测质量分层 (tier_A / tier_B / tier_C)

**生成时间**: 2026-06-16T09:19:27.702008Z

## 0. 判定规则

- **tier_A 核心论证型**: 同 post_id 抽出 ≤ 3 个 prediction **AND** thesis_summary > 50 字符 **AND** raw_text > 400 字符
- **tier_B 清单扫货型**: 同 post_id 抽出 ≥ 8 个 prediction (典型 'Strong Buy/Buy/Hold/Sell/Strong Sell' 评级)
- **tier_C 顺带提及**: 中间地带 (post 4-7 个 prediction, 或 thesis 短)

## 1. 总体分档

| Tier | n | 占比 |
|---|---|---|
| **tier_A 核心论证** | 348 | 8.7% |
| tier_B 清单扫货 | 1225 | 30.8% |
| tier_C 顺带提及 | 2410 | 60.5% |
| 总 | 3983 | 100% |

**注**: tier_B 来自 78 篇推文(批量扫货)

## 2. tier_A ticker 分布 (top 30)

| ticker | n |
|---|---|
| SIVE | 92 |
| NBIS | 56 |
| AAOI | 25 |
| AXTI | 20 |
| LITE | 12 |
| VLN | 10 |
| CRCL | 8 |
| RPI | 8 |
| XFAB | 8 |
| HIMS | 6 |
| IREN | 5 |
| LPTH | 5 |
| EWY | 5 |
| RDDT | 4 |
| CIFR | 4 |
| POET | 4 |
| IQE | 4 |
| ETOR | 3 |
| SNAP | 3 |
| FLY | 3 |
| AEHR | 3 |
| XLU | 3 |
| MSS | 3 |
| RKLB | 2 |
| AMD | 2 |
| SPRB | 2 |
| WULF | 2 |
| CRWV | 2 |
| SMCI | 2 |
| AIRO | 2 |

## 3. tier_A per-horizon 统计 (核心论证,真研究能力)

| horizon | n_resolved | hit_rate | median_exc | avg_exc |
|---|---|---|---|---|
| 1w | 315 | 57.1% | +3.82% | +7.42% |
| 1m | 275 | 54.2% | +3.67% | +29.92% |
| 3m | 191 | 65.4% | +12.90% | +38.03% |
| 6m | 76 | 85.5% | +37.67% | +60.28% |

## 4. tier_B per-horizon 统计 (清单扫货,预期 ~50% 接近 beta)

| horizon | n_resolved | hit_rate | median_exc |
|---|---|---|---|
| 1w | 1169 | 48.3% | -0.28% |
| 1m | 1169 | 54.7% | +1.80% |
| 3m | 982 | 46.5% | -2.55% |
| 6m | 539 | 51.4% | +2.34% |

## 5. tier_C per-horizon 统计

| horizon | n_resolved | hit_rate | median_exc |
|---|---|---|---|
| 1w | 2175 | 59.1% | +2.48% |
| 1m | 2054 | 58.9% | +4.86% |
| 3m | 1477 | 55.5% | +4.69% |
| 6m | 727 | 59.3% | +9.45% |

## 6. tier_A 详细列表 (前 50 条,按 published_at 排序)

| # | ticker | dir | pub | entry | n_post_preds | thesis_len | raw_text_len | 1m | 1m_excess |
|---|---|---|---|---|---|---|---|---|---|
| 1 | HIMS | long | 2025-09-10 | 1 | 1 | 87 | 509 | resolved_hit | +11.2% |
| 2 | ETOR | long | 2025-09-16 | 1 | 1 | 61 | 622 | resolved_miss | -11.8% |
| 3 | CRCL | short | 2025-09-16 | 1 | 1 | 54 | 1182 | resolved_hit | +4.6% |
| 4 | NBIS | long | 2025-09-19 | 1 | 1 | 58 | 3976 | resolved_hit | +1.6% |
| 5 | NBIS | long | 2025-09-19 | 1 | 1 | 81 | 1271 | resolved_hit | +1.6% |
| 6 | NBIS | long | 2025-09-21 | 1 | 1 | 76 | 638 | resolved_hit | +1.6% |
| 7 | NBIS | long | 2025-09-21 | 2 | 2 | 61 | 688 | resolved_hit | +1.6% |
| 8 | NBIS | long | 2025-09-27 | 1 | 1 | 91 | 404 | resolved_hit | +7.9% |
| 9 | RKLB | long | 2025-10-01 | 2 | 2 | 57 | 1233 | resolved_hit | +27.6% |
| 10 | NBIS | long | 2025-10-02 | 1 | 1 | 68 | 607 | resolved_miss | -7.4% |
| 11 | AMD | long | 2025-10-06 | 1 | 1 | 52 | 589 | resolved_hit | +18.0% |
| 12 | SNAP | long | 2025-10-06 | 1 | 1 | 136 | 4044 | resolved_miss | -16.0% |
| 13 | SPRB | long | 2025-10-06 | 1 | 1 | 62 | 696 | resolved_miss | -44.6% |
| 14 | SPRB | long | 2025-10-06 | 1 | 1 | 52 | 1044 | resolved_miss | -44.6% |
| 15 | VIRT | long | 2025-10-06 | 1 | 1 | 66 | 550 | resolved_hit | +4.4% |
| 16 | SNAP | long | 2025-10-10 | 1 | 1 | 78 | 451 | resolved_hit | +6.1% |
| 17 | FLY | long | 2025-10-10 | 1 | 1 | 70 | 3722 | resolved_miss | -36.2% |
| 18 | RBRK | long | 2025-10-13 | 1 | 1 | 57 | 1933 | resolved_miss | -12.7% |
| 19 | FLY | long | 2025-10-18 | 1 | 1 | 76 | 810 | resolved_miss | -23.4% |
| 20 | TE | long | 2025-10-20 | 1 | 1 | 51 | 956 | resolved_miss | -37.2% |
| 21 | NBIS | long | 2025-10-21 | 1 | 1 | 60 | 3067 | resolved_miss | -18.4% |
| 22 | NBIS | long | 2025-10-22 | 1 | 1 | 60 | 508 | resolved_miss | -15.1% |
| 23 | NBIS | long | 2025-10-22 | 1 | 1 | 57 | 787 | resolved_miss | -15.1% |
| 24 | NBIS | long | 2025-10-23 | 1 | 1 | 111 | 4146 | resolved_miss | -16.1% |
| 25 | NBIS | long | 2025-10-23 | 1 | 1 | 58 | 904 | resolved_miss | -16.1% |
| 26 | NBIS | long | 2025-10-25 | 1 | 1 | 100 | 1389 | resolved_miss | -25.0% |
| 27 | NBIS | long | 2025-10-25 | 1 | 1 | 55 | 1387 | resolved_miss | -25.0% |
| 28 | NBIS | long | 2025-10-26 | 1 | 1 | 103 | 4330 | resolved_miss | -25.0% |
| 29 | NBIS | long | 2025-10-26 | 1 | 1 | 52 | 1141 | resolved_miss | -25.0% |
| 30 | NBIS | long | 2025-10-27 | 2 | 2 | 67 | 4086 | resolved_miss | -24.0% |
| 31 | IREN | short | 2025-10-27 | 2 | 2 | 79 | 4086 | resolved_hit | +25.0% |
| 32 | NBIS | long | 2025-10-27 | 1 | 1 | 64 | 487 | resolved_miss | -24.0% |
| 33 | NBIS | long | 2025-10-28 | 1 | 1 | 52 | 658 | resolved_miss | -18.4% |
| 34 | FLY | long | 2025-10-29 | 1 | 1 | 70 | 657 | resolved_miss | -27.2% |
| 35 | NBIS | long | 2025-11-01 | 1 | 1 | 93 | 554 | resolved_miss | -23.4% |
| 36 | RDDT | long | 2025-11-05 | 1 | 1 | 75 | 627 | resolved_hit | +18.6% |
| 37 | AMD | long | 2025-11-05 | 1 | 1 | 67 | 477 | resolved_miss | -14.5% |
| 38 | NBIS | long | 2025-11-07 | 1 | 1 | 65 | 575 | resolved_miss | -19.3% |
| 39 | WULF | long | 2025-11-11 | 2 | 2 | 57 | 2261 | resolved_miss | -0.1% |
| 40 | CRWV | long | 2025-11-11 | 2 | 2 | 57 | 2261 | resolved_miss | -20.8% |
| 41 | NBIS | long | 2025-11-11 | 1 | 1 | 83 | 733 | resolved_miss | -21.7% |
| 42 | NBIS | long | 2025-11-12 | 1 | 1 | 68 | 1249 | resolved_miss | -12.0% |
| 43 | NBIS | long | 2025-11-12 | 1 | 1 | 58 | 532 | resolved_miss | -12.0% |
| 44 | NBIS | long | 2025-11-12 | 1 | 1 | 72 | 742 | resolved_miss | -12.0% |
| 45 | NBIS | long | 2025-11-13 | 1 | 1 | 67 | 1362 | resolved_miss | -8.3% |
| 46 | NBIS | long | 2025-11-14 | 3 | 3 | 52 | 935 | resolved_miss | -8.5% |
| 47 | NBIS | long | 2025-11-14 | 1 | 1 | 62 | 447 | resolved_miss | -8.5% |
| 48 | TSSI | long | 2025-11-14 | 1 | 1 | 51 | 493 | resolved_miss | -15.0% |
| 49 | NBIS | long | 2025-11-16 | 1 | 1 | 64 | 966 | resolved_miss | -8.5% |
| 50 | NBIS | long | 2025-11-17 | 1 | 1 | 62 | 1012 | resolved_hit | +3.7% |

## 7. tier_A 时间分布

| 时期 | n |
|---|---|
| 2025 (前期) | 106 |
| 2026 (后期) | 242 |
