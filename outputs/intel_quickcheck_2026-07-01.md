# 大V情报 — 每日健康速查 (2026-07-01 UTC)

_生成时间: 2026-07-01T08:37:27.766733+00:00_

## ❌ 状态: 2 类异常

## 1️⃣ Cron 跑没跑 (4 大V last_fetched_at)

  ✅ tw_jukan05: last_fetch 08:36Z (今天)
  ✅ tw_aleabitoreddit: last_fetch 08:36Z (今天)
  ✅ tw_zephyr_z9: last_fetch 08:36Z (今天)
  ✅ tw_austinsemis: last_fetch 08:36Z (今天)

## 2️⃣ 数据增长 (raw_posts + extractions_intel)

  raw_posts: 6,881 (24h 增量: 509, 7d 推文: 417)
  extractions_intel: 453 (24h 抽取: 453)
  ⚠  24h raw_posts 增长 509 (异常暴增, 可能重复抓)
  by source_id (24h new):
    tw_jukan05                     175
    tw_aleabitoreddit              107
    tw_zephyr_z9                   208
    tw_austinsemis                  19

## 3️⃣ 自检 (重复/KOL 活跃/ISO 格式)

  ✅ 4 大V 内部 0 重复
  ✅ 全 DB published_at ISO 格式

## 4️⃣ GitHub push 状态 (远端最新 commit)

  ⚠  Local 1af36fb8 != Remote 2cdb4868
  ✅ 远端最新 commit: 0.0h 前 (今天)
  ✅ 最新 commit 是 Daily DB backup

## 异常详情

- **HIGH_GROWTH** raw_posts (509)
- **DIVERGED** git (0)

---

**用法**: `python3 scripts/intel_quickcheck.py` (每早跑一次, 一眼看完)