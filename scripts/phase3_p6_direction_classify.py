"""Phase 3 P3-6 逐条分诊 163 short → A/B/C 类 + 重算

A: 真·反向持仓/明确反向观点(保留 short,正常验证)
B: 风险提示/谨慎/中性(改 neutral,不算盈亏)
C: 明确误判(改回正确方向)

然后:
1. 生成完整分诊报告
2. 改 predictions.direction (B/C 类)
3. 重算 verifications.h_Xm_excess_return (C 类需要 reverse short → long,B 类保持 pending/neutral)
4. 给出新记分牌
"""
from __future__ import annotations
import os, sqlite3, json
from datetime import datetime
from typing import Dict, List
from collections import Counter, defaultdict
import statistics, math

DB = "/workspace/data/signalboard_full.db"
OUT_DIR = "/workspace/outputs"
conn = sqlite3.connect(DB, timeout=30)
c = conn.cursor()


# 手动分诊 — 基于已读原文
# A: 真 short 持仓/明确看空
# B: 风险提示/谨慎/中性
# C: 明确误判(原文中性/看多被抽 short)

CLASSIFY = {
    # === AAOI (3 条,她长期 186 long 中混入) ===
    "4b73f50f-54c5-48b5-b2dd-318e963f263b": "B",   # "bearish near term with PTSD overhang... if drops to 80s, strong yes imo" - 风险提示
    "c8805d70-beff-41a6-b87b-236404150e4c": "B",   # "Short term bearish, long term likely accretive" - 风险提示
    "6dd0479f-a5d8-4511-88ca-7adca1a53e59": "B",   # "Short term... won't go too high... if drops to 80s, strong yes" - 风险提示
    
    # === AXTI (1 条 -156% 大亏,她长期 156 long) ===
    "39e9dee8-a1e6-48e5-9a3d-5a40bc9e7e1d": "B",   # "I personally would not hold... if it fails, I expect a recovery" - hedged 条件性,不是真建仓
    
    # === IREN (24 条全部 A,她真看空 $6B ATM 半年) ===
    # 通过 ticker 集中处理 (见下方 bulk A)
    "e9c6802c": "A",
    "9a915673": "A",
    "bf99d759": "A",
    "dd1f076f": "A",
    "1bd3cadd": "A",
    "f7ef86d9": "A",
    "b4cf7126": "A",
    "faf18c84": "A",
    "1bf402f0": "A",
    "11199127": "A",
    "218c8984": "A",   # "Short $IREN, long $NBIS"
    "24d787dc": "A",
    "1ce00ef5": "A",
    "13098143": "A",
    "ad983690": "A",
    "0324ba16": "A",
    "4e9195b3": "A",
    "195e8440": "A",
    "d2043678": "A",
    "1f41fa44": "A",
    "40862ec7": "A",
    "998837a8": "A",
    "f6ae7b94": "A",
    "834ad06a": "A",
    
    # === CRCL (8 条 A,她看空估值) ===
    "a022dabf": "A",
    "99c9167c": "A",
    "a04629a9": "A",
    "bb41fff1": "A",
    # 待补
    
    # === HIMS (1 条) ===
    "3ca5598b": "A",   # "drop 50-70%+" 明确看空
    
    # === RKLB (2 条) ===
    "98668a95": "A",   # "RKLB definitely most overvalued" 明确看空
    "17caaa8e": "B",   # "Silver crash extending into... $RKLB (High-Beta)" - 风险提示不是建仓
    
    # === RDDT (1 条) ===
    "88118c95": "A",   # "Sell" 列表
    
    # === MU (1 条 C) ===
    "9106c8f1-b7eb-4e5a-9476-43e09dac077a": "C",   # "would dg it to hold" 中性被误抽 short
    
    # === ALAB (2 条) ===
    "fa185bc7": "A",   # "opened up short with CREDO as a hedge" 明确开 short
    "b3da1f01": "B",   # "ALAB is a bit overvalued... closed at a good time" 风险提示
    
    # === ARM (1 条) ===
    "df20f804": "A",   # "I'm actually personally pretty bearish on $ARM and $QLCM" 明确看空
    
    # === AMD (1 条) ===
    "03da89f9": "A",   # "My stance changed on AMD... OpenAI... $1T+..." 立场转变,看空
    
    # === ORCL (6 条) ===
    # 待补
    
    # === NVDA (4 条) ===
    # 待补
    
    # === HOOD (1 条) ===
    # 待补
    
    # === POET (1 条) ===
    # 待补
    
    # === SNDK (1 条) ===
    # 待补
}


# Bulk A: 一些 ticker 全部 short 且论点明确,统一标 A
BULK_A_TICKERS = [
    # BMNR 12 / QBTS 9 / RGTI 9 / IONQ 6 / OKLO 6 / PLTR 5
    # 这些 ticker 她在别处 long 几乎没有 (1-2 条),看她原文都是明确看空
    # 待单独看
]

BULK_NEUTRAL_TICKERS = [
    # 一些 ticker 全部 short 但 LLM 倾向过度解读
    # 待确认
]


# 拉所有 short 预测的 prediction_id
print("=" * 80)
print("拉全部 163 short 预测 + 原文")
print("=" * 80)

sql = """
SELECT p.prediction_id, p.ticker, p.direction, p.conviction, p.horizon,
       p.quantitative_claim, p.thesis_category, p.hedged, p.extraction_notes,
       v.published_at, v.entry_date_actual, v.entry_price,
       v.h_1m_status, v.h_1m_raw_return, v.h_1m_excess_return,
       v.h_1w_status, v.h_1w_raw_return, v.h_1w_excess_return,
       v.h_3m_status, v.h_3m_raw_return, v.h_3m_excess_return,
       v.h_6m_status, v.h_6m_raw_return, v.h_6m_excess_return
FROM predictions p
JOIN verifications v ON p.prediction_id = v.prediction_id
WHERE p.price_source_available=1 AND p.direction='short'
ORDER BY p.ticker, v.published_at
"""
all_shorts = c.execute(sql).fetchall()
print(f"总共 {len(all_shorts)} short 预测")
print()

# 看哪些 prediction_id 还没分类
unclassified = []
classified = []
for r in all_shorts:
    pid = r[0]
    if pid in CLASSIFY:
        classified.append((pid, CLASSIFY[pid], r))
    else:
        unclassified.append(r)

print(f"已分类: {len(classified)} 条")
print(f"未分类: {len(unclassified)} 条")
print()

# 把未分类的全部原文拉出来,让用户和我都能看
print("=" * 80)
print("未分类 short 预测 — 原文")
print("=" * 80)

# 输出按 ticker 分组
unclassified_by_ticker = defaultdict(list)
for r in unclassified:
    unclassified_by_ticker[r[1]].append(r)

for t, rs in sorted(unclassified_by_ticker.items()):
    n_long = c.execute("SELECT COUNT(*) FROM predictions WHERE ticker=? AND direction='long' AND price_source_available=1", (t,)).fetchone()[0]
    print(f"\n### {t} (n_long={n_long}  n_short={len(rs)})")
    for i, r in enumerate(rs, 1):
        pid = r[0]
        sql_t = 'SELECT rp.raw_text FROM predictions p JOIN raw_posts rp ON p.post_id = rp.post_id WHERE p.prediction_id = ?'
        text = c.execute(sql_t, (pid,)).fetchone()
        text_str = text[0] if text else "(no text)"
        if len(text_str) > 500:
            text_str = text_str[:500] + '...'
        
        s1m = r[11]
        r1m = r[12]
        e1m = r[13]
        r1m_s = f"{r1m*100:+.2f}%" if isinstance(r1m, (int, float)) else "N/A"
        e1m_s = f"{e1m*100:+.2f}%" if isinstance(e1m, (int, float)) else "N/A"
        ep_s = f"${r[11]:.2f}" if isinstance(r[11], (int, float)) else "NULL"
        
        print(f"\n  [{i}] pred={pid}  pub={r[9][:10]} entry={r[10]} px={ep_s}")
        print(f"      LLM: dir=short conv={r[3]} hz={r[4]} qc={r[5]} hedged={r[7]}")
        print(f"      1m: {s1m} raw={r1m_s} excess={e1m_s}")
        print(f"      原文: {text_str!r}")


# 把已分类的也打印
print("\n" + "=" * 80)
print("已分类的 short 预测 — 我的初判")
print("=" * 80)

classified_by_class = defaultdict(list)
for pid, cat, r in classified:
    classified_by_class[cat].append(r)

for cat in ["A", "B", "C"]:
    if cat not in classified_by_class:
        continue
    print(f"\n### 类别 {cat}: {len(classified_by_class[cat])} 条")
    for r in classified_by_class[cat]:
        pid = r[0]
        s1m = r[11]
        r1m = r[12]
        e1m = r[13]
        r1m_s = f"{r1m*100:+.2f}%" if isinstance(r1m, (int, float)) else "N/A"
        e1m_s = f"{e1m*100:+.2f}%" if isinstance(e1m, (int, float)) else "N/A"
        ep_s = f"${r[11]:.2f}" if isinstance(r[11], (int, float)) else "NULL"
        print(f"  {r[1]:6s}  pred={pid[:8]}  pub={r[9][:10]}  entry={r[10]}  px={ep_s}  1m: {s1m} raw={r1m_s} excess={e1m_s}")


# 落报告
print()
print("=" * 80)
print("落报告")
print("=" * 80)

content = []
content.append("# Phase 3 P3-6 逐条分诊 — 163 short → A/B/C 类")
content.append("")
content.append(f"**运行时间**: {datetime.utcnow().isoformat()}Z")
content.append("")
content.append("## 分类规则")
content.append("")
content.append("- **A 类**: 真·反向持仓/明确反向观点(有论据、有时间、有目标价或催化剂)。保留 short 验证。")
content.append("- **B 类**: 风险提示/谨慎/中性,不是建仓。改 neutral,不当 short 头寸算盈亏。")
content.append("- **C 类**: 明确误判(原文中性/看多被抽 short)。改回正确方向。")
content.append("")
content.append("## 1. 总体分类统计")
content.append("")
n_A = sum(1 for _, c, _ in classified if c == "A")
n_B = sum(1 for _, c, _ in classified if c == "B")
n_C = sum(1 for _, c, _ in classified if c == "C")
n_pending = len(unclassified)
content.append(f"- 已分类: {len(classified)} 条 (A={n_A}  B={n_B}  C={n_C})")
content.append(f"- 待分类: {n_pending} 条")
content.append("")
content.append("## 2. 已分类逐条")
content.append("")
for cat, label in [("A", "A 类 — 真·反向持仓"), ("B", "B 类 — 风险提示"), ("C", "C 类 — 明确误判")]:
    if cat not in classified_by_class:
        continue
    content.append(f"\n### {label} ({len(classified_by_class[cat])} 条)")
    content.append("")
    content.append("| ticker | pred_id | pub | entry | px | 1m_status | 1m_excess |")
    content.append("|---|---|---|---|---|---|---|")
    for r in classified_by_class[cat]:
        pid = r[0]
        s1m = r[11]
        e1m = r[13]
        e1m_s = f"{e1m*100:+.2f}%" if isinstance(e1m, (int, float)) else "N/A"
        ep_s = f"${r[11]:.2f}" if isinstance(r[11], (int, float)) else "NULL"
        content.append(f"| {r[1]} | `{pid[:8]}` | {r[9][:10]} | {r[10]} | {ep_s} | {s1m} | {e1m_s} |")
    content.append("")

content.append("## 3. 待分类(等你确认)")
content.append("")
content.append("以下 ticker 的 short 我还没看原文,需要你确认分类:")
content.append("")
for t, rs in sorted(unclassified_by_ticker.items()):
    n_long = c.execute("SELECT COUNT(*) FROM predictions WHERE ticker=? AND direction='long' AND price_source_available=1", (t,)).fetchone()[0]
    content.append(f"\n### {t} (n_long={n_long}  n_short={len(rs)})")
    content.append("")
    for i, r in enumerate(rs, 1):
        pid = r[0]
        sql_t = 'SELECT rp.raw_text FROM predictions p JOIN raw_posts rp ON p.post_id = rp.post_id WHERE p.prediction_id = ?'
        text = c.execute(sql_t, (pid,)).fetchone()
        text_str = text[0] if text else "(no text)"
        if len(text_str) > 500:
            text_str = text_str[:500] + '...'
        s1m = r[11]
        r1m = r[12]
        e1m = r[13]
        r1m_s = f"{r1m*100:+.2f}%" if isinstance(r1m, (int, float)) else "N/A"
        e1m_s = f"{e1m*100:+.2f}%" if isinstance(e1m, (int, float)) else "N/A"
        ep_s = f"${r[11]:.2f}" if isinstance(r[11], (int, float)) else "NULL"
        content.append(f"\n**[{i}]** pred=`{pid}` pub={r[9][:10]} entry={r[10]} px={ep_s}")
        content.append(f"- LLM: dir=short conv={r[3]} hz={r[4]} qc={r[5]} hedged={r[7]}")
        content.append(f"- 1m: {s1m} raw={r1m_s} excess={e1m_s}")
        content.append(f"- 原文: `{text_str}`")
    content.append("")

with open(os.path.join(OUT_DIR, "phase3_p6_direction_classify_v1.md"), "w", encoding="utf-8") as f:
    f.write("\n".join(content))
print(f"✅ 落 outputs/phase3_p6_direction_classify_v1.md")
conn.close()
print("=== DONE ===")
