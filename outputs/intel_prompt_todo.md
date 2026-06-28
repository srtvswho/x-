# 大V情报 — prompt v2.0.x 待修清单

不阻塞当前 daily cron 跑. 等攒到 3-5 条一起修, 升 v2.0.2-intel.

---

## 待修 #1: zephyr MRVL "指控式贬低 + 反讽收尾" 边界 case

**post_id**: 2069181208412721377
**KOL**: zephyr_z9
**方向**: short (v2.0.1-intel 抽)
**应该是**: neutral (误抽)

**原文**:
> "Marvell which you would think should be competing is just a pump and dump by the management team to take your money and put it in their pockets and wall street is pricing them as an asic design house not realizing the asic design business is just IT outsourcing."
> 
> "My sweet summer child..."

**误抽原因**:
- "pump and dump by management" — 指控式贬低, 不是建仓
- "put it in their pockets" — 金钱指控
- "My sweet summer child..." — 反讽/嘲弄收尾
- 没有明确 "I'm shorting" / "做空" / "我会建仓做空" 关键词

**修法 (v2.0.2)**:
在"5 类 short 误抽铁律"后加第 6 类:

> 6. 【指控式贬低 + 反讽收尾】 → neutral
>    - "X is just a pump and dump" / "Y 是个骗局"
>    - "put money in their pockets" / "垃圾" / "骗局"
>    - 反讽收尾 ("My sweet summer child..." / "lol if you like losing money")
>    - 【但】如 "I'm shorting X" / "我做空 X" (作者明确建仓) → 可 short

**验证**: 重抽这条 + 全量 1424 条, 看是否修对.

---

## 待修 #2 (低优先级): LLM 偶尔返回 summary_100 空字符串

**现象**: 1424 条抽取里 1 条 summary_100 空字符串 (LLM 返回空)
**位置**: extractions_intel 表, prompt_version='v2.0.1-intel'
**修法**: 脚本层防御 — persist_extraction 检测空, 重新跑这条
**影响**: 1/1424 = 0.07%, 可忽略

---

## 待修 #3 (观察中): zephyr HBM3E 边缘 AI 真 short

**post_id**: 2063839743432176085
**方向**: short (正确, 不算误抽)
**原文**: "$85k for 250 Gigs of HBM3E... super bearish on edge AI/self-hosting"

**观察**: 这是真 short, 标的是概念 (edge AI/self-hosting) 不是具体股票. 模块 3 首次检测可能不需要 (没具体 ticker). 但 summary 里应该明确"概念 short 不是个股 short"。

---

## v2.0.1-intel 已修复的 (不需要再修)

| 类别 | v2.0.0 → v2.0.1 修复 |
|---|---|
| 5 类 short 误抽铁律 | ✅ 加 (反问 / 持仓披露 / 含蓄+调侃 / 朋友仓位 / 讽刺幽默) |
| R12 flag (victory_lap / position_disclosure / self_reported_returns) | ✅ 加 (88 + 76 + 13 条全部正确标记) |
| short_skeptical=1 误用 | ✅ 修 (从 10 → 0) |
| short 抽取数 | ✅ 4 → 2 (50% 修复) |