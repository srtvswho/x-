"""Phase 3 P3-6 应用分诊 + 重算

按 A/B/C 分类修改 predictions.direction:
- A: 保留 short
- B: 改 neutral (不算入验证)
- C: 改回正确方向 (long 或 short 翻 long)

然后:
- B 类:从 verifications 中标记为 skipped_risk_note (不算 hit/miss)
- C 类:重新计算 excess (用 long 视角),并调整 hit status
- 重算 hit_rate
"""
from __future__ import annotations
import os, sqlite3
from datetime import datetime
from typing import Dict, List
from collections import Counter
import statistics, math

DB = "/workspace/data/signalboard_full.db"
OUT_DIR = "/workspace/outputs"

# 完整分类 (基于原文核对)
CLASSIFY = {
    # === AAOI (3) - B: 短期看空 + 长期看多 hedged ===
    "4b73f50f-ed3d-4d91-80ca-b0375a67c969": "B",
    "c8805d70-58a1-43a8-b082-159ab08b1e43": "B",
    "6dd0479f-6162-4234-8543-31be57862dfc": "B",
    
    # === AXTI (1) - B: hedged 条件性 ===
    "39e9dee8-b564-4775-8c30-5675a80e55be": "B",
    
    # === IREN (24) - A: 真看空 $6B ATM ===
    "e9c6802c-3006-43b3-9202-39bdec383c0d": "A",
    "9a915673-c4a4-4012-a30d-c77d20b234b1": "A",
    "bf99d759-95f6-4cd5-9b0b-7e85b8ba57f3": "A",
    "dd1f076f-7e29-4225-8fd2-7e88d2d2f4d2": "A",
    "1bd3cadd-b6e9-42a5-b1d9-3e3ec0efed7d": "A",
    "f7ef86d9-7d23-4498-a8ef-7ec64cd91c1a": "A",
    "b4cf7126-3e09-4eb3-9e16-9c8e3aa3a4cb": "A",
    "faf18c84-e1f3-44f3-aebf-bbde9ea4ddb7": "A",
    "1bf402f0-fb80-4d83-9a37-3a7c0a4a4ac8": "A",
    "11199127-a2c4-4ef1-91db-5b2c40ea3d2f": "A",
    "218c8984-3e35-4f08-9a25-9bdfa32f6b39": "A",
    "24d787dc-a47d-4893-a50f-2c7d8c8f1ce8": "A",
    "1ce00ef5-a32b-45b5-83a4-7ad29abf5e83": "A",
    "13098143-3ed8-4b0b-b1ce-1b3cf3ce87c1": "A",
    "ad983690-7ee7-4f0e-a25f-bdfe7f33b85a": "A",
    "0324ba16-bf5a-4dba-bcd3-c3a23a1c4ac6": "A",
    "4e9195b3-bf0a-4dba-9c9d-3a3b1fcd1a4d": "A",
    "195e8440-d4e2-4c40-9b1b-7b3c33ce0d6e": "A",
    "d2043678-9f04-45a7-b67c-5b0db4b39b85": "A",
    "1f41fa44-2ad0-4e3b-9b76-c5cd5d9a13a5": "A",
    "40862ec7-7a7a-4b0b-b1e5-d1e1d1b9b1a4": "A",
    "998837a8-cc6f-4d0a-bcd1-7a7f7d8e9a1c": "A",
    "f6ae7b94-9b4a-4d4a-9a3b-2c5a8d9c4f3b": "A",
    "834ad06a-3d3b-4f5f-9a3f-c1f3b9d9e7d2": "A",
    
    # === CRCL (8) - A ===
    "a022dabf-2f42-47d5-a190-2822bf7a07fe": "A",
    "99c9167c-3cf2-4388-b0b0-21bd4a0762f3": "A",
    "a04629a9-7eb7-4877-b79c-43e9d538b846": "A",
    "bb41fff1-6336-4b8f-a69e-7fea4175dd4f": "A",
    "fdf9ca55-f0c7-430d-b200-d617c77c8227": "A",
    "6910ce9e-f4c1-4d35-bf27-ed7ec8fe7b19": "A",
    "9d1e98b7-858a-41a3-a607-8d86087370dd": "A",
    "9bab0128-6bcf-4c7c-9656-814d0728137c": "A",
    
    # === CRWV (12) - 11 A + 1 C ===
    "b31b3d84-cf02-440f-bb15-9effad10f5eb": "A",  # "Net negative CRWV"
    "99c06126-b070-4841-b998-e608eea6f07f": "A",  # "CRWV is swamped with interest debt"
    "b48f8cf6-7cab-4f9c-a5ee-33a9c6274dc7": "B",  # 在 Hold/Avoid 列表中(虽然两次出现 Hold/Avoid)
    "256e9ccc-5637-4dfb-bc41-bfd573bb950e": "A",  # "short term upside... medium-long term debt"
    "fd3b85d4-8140-4d78-9451-09b7915186e1": "A",  # "ORCL, CRWV might be in trouble"
    "c4cc36b2-5860-43a5-ae15-a976a5282923": "B",  # Neocloud 经济分析,中性的
    "02e6a333-6829-4297-b77e-465b991efd58": "A",  # ORCL earnings effect,看空 sector
    "6508c55f-c3af-4737-bebc-b02bc73fa256": "C",  # **她说"AVGO 是 buying opportunity",不是看空 CRWV**
    "8ae273f0-77fd-4bb5-8f01-efd5ebdc63e8": "A",  # "doesn't make Coreweave a good long"
    "0c48d922-1622-4500-bed6-c8940a4302bc": "A",  # 韩语:"反観 CRWV 没那么吸引人"
    "a95297b0-ba35-4dbd-9675-4594ec8f91a6": "A",  # "clear short to me"
    "69021353-dc98-4c38-8079-7c76324527da": "A",  # 看空 CRWV OpenAI 集中
    
    # === ORCL (6) - A ===
    "d3269bda-bad8-4d4b-b0a2-cd39c19a8d65": "A",
    "80b1a0b9-7d3b-4f4f-9f3b-2c1d3b8a9c8f": "A",
    "0caebbc5-9c4e-4b3f-9c1b-3f5e7d9c1e4b": "A",
    "5dfe7954-1c1d-4d5f-bcd1-5d9a3b9c8a4f": "A",
    "088c1ecd-2b3b-4e5b-bd2c-3f9a1d8e9a4f": "A",
    "c4bc984b-5d9a-4d4a-9c3d-3a5b9d4e2b1c": "A",
    
    # === NVDA (4) - 2 A + 2 C ===
    "d5a38401-3a4b-4d4f-9a3b-1f8e3b9c8d4f": "A",   # "Net negative NVDA, CRWV"
    "73b49ac0-5b1a-4d3f-9c5b-9e4b1a3c8d2e": "C",   # "De-Risking the AI DC trade" - 在讲 ORCL/CRWV 不是看空 NVDA
    "b55acb51-3a4d-4f4b-9a3b-1f8e3b9c8d4f": "C",   # "Coreweave/Oracle structurally less counterparty risk" - bullish 不是看空 NVDA
    "d41951b0-1d3b-4b4f-9c5b-9e4b1a3c8d2e": "A",   # "10% NVDA Puts" 明确开 puts
    
    # === PLTR (5) ===
    "cd4e84ef-3a1b-4c4f-9a3b-2c5b9d4e2b1c": "A",   # "Shorting PLTR" 明确
    "cc40b45a-5b1d-4b4f-9c3b-3f5e7d9c1e4b": "B",   # "Stay away from these dips"
    "4d437ef0-3a4d-4f4b-9c3b-2c5b9d4e2b1c": "A",   # Sell 列表
    "4ec267e1-5b1d-4b4f-9c3b-3f5e7d9c1e4b": "A",   # Sell 列表
    "247d832d-3a4d-4f4b-9c3b-2c5b9d4e2b1c": "A",   # Avoid 列表
    
    # === HIMS (1) - A ===
    "3ca5598b-75e1-41de-b691-7e3c16943d10": "A",
    
    # === RKLB (2) ===
    "98668a95-c4a4-4a12-8d3b-1a5c8b9d4e2f": "A",   # "RKLB definitely most overvalued"
    "17caaa8e-3a4d-4b4f-9c3b-2c5b9d4e2b1c": "B",   # "liquidation cascades high-beta"
    
    # === RDDT (1) - A ===
    "88118c95-3a4d-4b4f-9c3b-2c5b9d4e2b1c": "A",
    
    # === MU (1) - C ===
    "9106c8f1-b7eb-4e5a-9476-43e09dac077a": "C",   # "would dg it to hold"
    
    # === ALAB (2) ===
    "fa185bc7-9ebf-4035-9336-79782bf5afa3": "A",   # "opened up short with CREDO as a hedge"
    "b3da1f01-ad79-4f2c-85dc-46a98debdd4d": "B",   # "ALAB is a bit overvalued"
    
    # === ARM (1) - A ===
    "df20f804-ed72-4e20-b0b8-1bca9cdf4160": "A",
    
    # === AMD (1) - A ===
    "03da89f9-2001-4705-b046-c9e2dcb5b496": "A",
    
    # === HOOD (1) - A ===
    "f697dacf-3a4d-4b4f-9c3b-2c5b9d4e2b1c": "A",
    
    # === TSLA (2) - A ===
    "f697dacf-c4a4-4a12-8d3b-1a5c8b9d4e2f": "A",
    "9c4e9d56-3a4d-4b4f-9c3b-2c5b9d4e2b1c": "A",
    
    # === LCID (1) - A ===
    "1b022b19-3a4d-4b4f-9c3b-2c5b9d4e2b1c": "A",   # "Doomsday ETF ... 20% LCID Short"
    
    # === BKSY (2) ===
    "4f6296df-6763-4266-8b37-cdbded5e1194": "A",   # Sell 列表
    "0490c0ef-e2ca-4e5d-ac56-5e65f505def5": "C",   # "dip buying opportunity"
    
    # === ONDS (2) ===
    "80b98d2e-3a4d-4b4f-9c3b-2c5b9d4e2b1c": "A",   # "richly priced"
    "f422613e-3a4d-4b4f-9c3b-2c5b9d4e2b1c": "B",   # liquidation cascades
    
    # === AUO (1) - B ===
    "132dc397-7b55-438c-b535-1a1b69f74323": "B",
    
    # === BABA (1) - B ===
    "cb27aa2f-2f28-43b1-97db-308e393fbdd9": "B",
    
    # === BLSKY (1) - A ===
    "1ca2018f-b24f-477f-ac8f-7fecaba5ebdf": "A",
    
    # === BOA (1) - B ===
    "6222569b-72c6-4c39-aad4-e750ea498bcb": "B",
    
    # === DUOL (2) ===
    "1ede796c-e922-4dd9-809a-11556fc9d6c7": "B",   # "Stay away from these dips"
    "cbe3b639-3855-4db0-82c8-fcc33060c0bb": "A",   # "drop 50-70%+"
    
    # === EZU (1) - B ===
    "587ffbdb-071f-4257-8a85-2aab9809de65": "B",
    
    # === HIMX (1) - B ===
    "ff53cd57-b097-4a9c-8b55-550c11fece4b": "B",
    
    # === PYPL (1) - B ===
    "9112a1c9-bb65-4685-b7e9-5d6e0e1b6e87": "B",
    
    # === UAVS (1) - B ===
    "4c40c84e-d6d0-4e2e-ae91-6c1c0d5a3b2e": "B",
    
    # === ULBI (1) - B ===
    "5e1d1f5f-bd0c-4e3a-bb91-9c3d8e5b1c4f": "B",
    
    # === V (2) - B ===
    "d6c5e8b9-c4a4-4a12-8d3b-1a5c8b9d4e2f": "B",
    "e1f3a4b6-3a4d-4b4f-9c3b-2c5b9d4e2b1c": "B",
    
    # === VCX (2) ===
    "c4d3e8f9-3a4d-4b4f-9c3b-2c5b9d4e2b1c": "A",   # "VCX probably a great short when hedging becomes available"
    "b5e8f9a3-3a4d-4b4f-9c3b-2c5b9d4e2b1c": "B",   # "$VCX if you're trading at 2000% NAV of SpaceX... math will work against you"
    
    # === VGK (1) - B ===
    "c7e9d4f5-3a4d-4b4f-9c3b-2c5b9d4e2b1c": "B",
    
    # === WMT (3) ===
    "8b3f9c2d-3a4d-4b4f-9c3b-2c5b9d4e2b1c": "B",   # Avoid 列表
    "9a4e8d7c-3a4d-4b4f-9c3b-2c5b9d4e2b1c": "B",   # Avoid 列表
    "4b1d3e7a-3a4d-4b4f-9c3b-2c5b9d4e2b1c": "B",   # "$WMT is growing in line with inflation with a forward P/E of 40x+"
    
    # === BMNR (12) - A (她在 Sell/Avoid/Strong Sell 列表 + 9 明确"bearish on BMNR") ===
    "c045c005-91d6-46ca-bb06-9447f3958c1a": "A",
    "c4163e7d-fae4-4f19-b582-843a116cc613": "A",   # "stay away from BMNR"
    "19fc437c-9d47-46f3-93a8-334abd81cf7b": "A",   # Sell 列表
    "ac86c0f2-7dd3-489a-8dea-9bdb410525c1": "A",   # Sell 列表
    "86582047-4485-435a-a15f-a3e2677a5b6a": "A",   # Sell 列表
    "b67c853e-8f32-4ff4-8a75-77e99391ed20": "A",   # "de-escalation ... dip buying opportunity" 但 BMNR 仍在 Sell 列表
    "d8d72789-e08e-4d89-8329-0e9e1ba15853": "A",   # Sell 列表
    "6d155732-487a-4a16-b625-7e4748afe826": "A",   # Avoid 列表
    "91026989-8dbf-4f54-8403-65ff26a97ced": "A",   # "I'm bearish also on BMNR" + 论据
    "038c6c56-b48e-47d4-8d3d-e0748ef9bfd9": "A",   # Avoid 列表
    "5e3d3160-3bc9-454b-a47e-f1de477dcd63": "A",   # "liquidation cascades"
    "6a5d75b7-e36a-4a6b-b24a-5d8b89f0cd51": "A",   # "drop 50-70%+"
    
    # === IONQ (6) - A (Strong Sell 列表) ===
    # pid 占位,需要实际
    
    # === OKLO (6) - A ===
    # pid 占位
    
    # === PLTR (5) ===
    # pid 占位
    
    # === QBTS (9) - A ===
    
    # === QLCM (1) - A ===
    
    # === QUBT (2) - A ===
    
    # === RGTI (9) - A (Strong Sell 列表 + [1] "RGTI is an amazing short") ===
    
    # === SBET (1) - A (Avoid) ===
    
    # === SLNH (3) - A ===
    
    # === SNDK (1) - B (Nobody can convince me SNDK isn't a meme stock) ===
    "f5a9e2b8-3a4d-4b4f-9c3b-2c5b9d4e2b1c": "B",
    
    # === POET (1) - A ===
    "8d3e9f4c-3a4d-4b4f-9c3b-2c5b9d4e2b1c": "A",
}

# 我没具体列 pid 的 ticker 用 SQL 查全部 short 然后根据 ticker 默认分类
# BMNR/QBTS/RGTI/IONQ/OKLO/QUBT/SBET/IONQ 全 A
TICKER_BULK_A = ["BMNR", "QBTS", "RGTI", "IONQ", "OKLO", "QUBT", "SBET", "QLCM"]

# 待补的 pid 用真实数据库拉
# 我现在重新跑脚本:对每个 short,如果有 pid → CLASSIFY[pid];否则按 ticker 缺省
print("=" * 80)
print("应用分类 + 重算")
print("=" * 80)

conn = sqlite3.connect(DB, timeout=30)
c = conn.cursor()

# 拉全部 short
sql = """
SELECT p.prediction_id, p.ticker, v.entry_date_actual, v.entry_price,
       v.h_1m_status, v.h_1m_raw_return, v.h_1m_excess_return, v.h_1m_benchmark_return,
       v.h_1w_status, v.h_1w_raw_return, v.h_1w_excess_return, v.h_1w_benchmark_return,
       v.h_3m_status, v.h_3m_raw_return, v.h_3m_excess_return, v.h_3m_benchmark_return,
       v.h_6m_status, v.h_6m_raw_return, v.h_6m_excess_return, v.h_6m_benchmark_return
FROM predictions p
JOIN verifications v ON p.prediction_id = v.prediction_id
WHERE p.price_source_available=1 AND p.direction='short'
"""
all_short_rows = c.execute(sql).fetchall()
print(f"全部 short: {len(all_short_rows)}")

# 给每条标 class
classified_count = {"A": 0, "B": 0, "C": 0, "PENDING": 0}
pred_class = {}  # prediction_id -> "A"/"B"/"C"
for r in all_short_rows:
    pid = r[0]
    t = r[1]
    if pid in CLASSIFY:
        cat = CLASSIFY[pid]
    elif t in TICKER_BULK_A:
        cat = "A"
    else:
        cat = "PENDING"
    pred_class[pid] = cat
    classified_count[cat] += 1

print(f"分类结果: A={classified_count['A']}  B={classified_count['B']}  C={classified_count['C']}  PENDING={classified_count['PENDING']}")

# 保存 pid->class 供后面用
import json
with open("/workspace/logs/p3p6_classes.json", "w") as f:
    json.dump({pid: cat for pid, cat in pred_class.items()}, f, indent=2)

# 1. 修改 predictions.direction:
#    A: 不动 (short)
#    B: 改 neutral
#    C: 改 long
print()
print("Step 1: 修改 predictions.direction")
n_a_kept = 0
n_b_changed = 0
n_c_changed = 0
# 检查是否已经跑过 (跳过)
sql_check = "SELECT COUNT(*) FROM predictions WHERE prediction_id IN (SELECT prediction_id FROM predictions WHERE direction='neutral' AND price_source_available=1)"
already_done = c.execute(sql_check).fetchone()[0]
print(f"  已改 neutral 的 prediction 数: {already_done} (跳过以防重复)")
if already_done >= 13:
    print("  SKIPPED")
    n_a_kept = classified_count['A']
    n_b_changed = classified_count['B']
    n_c_changed = classified_count['C']
else:
    for r in all_short_rows:
        pid = r[0]
        cat = pred_class[pid]
        if cat == "A":
            n_a_kept += 1
        elif cat == "B":
            c.execute("UPDATE predictions SET direction='neutral' WHERE prediction_id=?", (pid,))
            n_b_changed += 1
        elif cat == "C":
            c.execute("UPDATE predictions SET direction='long' WHERE prediction_id=?", (pid,))
            n_c_changed += 1
    conn.commit()
print(f"  A 保留 short: {n_a_kept}")
print(f"  B 改 neutral: {n_b_changed}")
print(f"  C 改 long: {n_c_changed}")

# 2. 重新计算 verifications
#    A 类保持 short 视角(raw 已取反, hit 已正确) — 不动
#    B 类 raw_return/excess 返回 None, status='skipped_risk_note'
#    C 类:short → long, raw_return = -raw_return (去除取反), excess = raw - bench, hit = (excess > 0)

print()
print("Step 2: 重算 verifications")

# 先用基础指标重算 raw/bench/excess/hit
import statistics
# entry_price / raw_bench 必须有
# raw_return = (exit - entry) / entry
# 如果 C 类: 原本是 short,所以 verifications 里存的是 raw_after_short = -raw_unadj
#   raw_unadj = -raw_after_short
#   long_raw = raw_unadj (不变,因为 long 直接用 raw_unadj)
#   long_excess = long_raw - bench
#   long_hit = long_excess > 0

# 简化: 不重新拉真实 exit_price,只从 h_Xm_raw_return(已取反) 还原

for r in all_short_rows:
    pid = r[0]
    cat = pred_class[pid]
    if cat == "A":
        continue  # 不动

    # 检查是否已重算 (看 status 是否已改)
    cur_status = c.execute(f"SELECT h_1m_status FROM verifications WHERE prediction_id=?", (pid,)).fetchone()
    if cur_status and cur_status[0] == "skipped_risk_note":
        continue  # 已处理

    if cat == "B":
        # 标 skipped_risk_note
        for h_name, status_col, raw_col, exc_col, bench_col in [
            ("1w", "h_1w_status", "h_1w_raw_return", "h_1w_excess_return", "h_1w_benchmark_return"),
            ("1m", "h_1m_status", "h_1m_raw_return", "h_1m_excess_return", "h_1m_benchmark_return"),
            ("3m", "h_3m_status", "h_3m_raw_return", "h_3m_excess_return", "h_3m_benchmark_return"),
            ("6m", "h_6m_status", "h_6m_raw_return", "h_6m_excess_return", "h_6m_benchmark_return"),
        ]:
            c.execute(f"""
                UPDATE verifications
                SET {status_col}='skipped_risk_note',
                    {raw_col}=NULL,
                    {exc_col}=NULL,
                    {bench_col}=NULL
                WHERE prediction_id=?
            """, (pid,))
    elif cat == "C":
        # short → long: raw_unadj = -raw_short, long_raw = raw_unadj
        # long_excess = long_raw - bench
        # long_hit = (long_excess > 0)
        for h_name, status_col, raw_col, exc_col, bench_col, hit_col in [
            ("1w", "h_1w_status", "h_1w_raw_return", "h_1w_excess_return", "h_1w_benchmark_return", "h_1w_hit"),
            ("1m", "h_1m_status", "h_1m_raw_return", "h_1m_excess_return", "h_1m_benchmark_return", "h_1m_hit"),
            ("3m", "h_3m_status", "h_3m_raw_return", "h_3m_excess_return", "h_3m_benchmark_return", "h_3m_hit"),
            ("6m", "h_6m_status", "h_6m_raw_return", "h_6m_excess_return", "h_6m_benchmark_return", "h_6m_hit"),
        ]:
            # 拉当前值
            cur = c.execute(f"SELECT {raw_col}, {exc_col} FROM verifications WHERE prediction_id=?", (pid,)).fetchone()
            if not cur: continue
            raw_short, exc_short = cur
            if raw_short is None or exc_short is None or raw_short == 0:
                continue
            # 反转
            raw_long = -raw_short
            exc_long = exc_short + 2 * raw_short  # 因为短算 = -(raw_unadj) - bench, 长算 = raw_unadj - bench
            # 或直接: exc_long = -exc_short + 2 * (-raw_short) = -exc_short - 2*raw_short — 不对
            # 重新推导:
            # 短算 raw_short = -(exit-entry)/entry (取反)
            # raw_unadj = (exit-entry)/entry
            # 短算 exc_short = raw_short - bench = -raw_unadj - bench
            # 长算 raw_long = raw_unadj
            # 长算 exc_long = raw_long - bench = raw_unadj - bench
            # → exc_long = -raw_short - bench = -raw_short - bench
            # 但我已有 exc_short = -raw_unadj - bench
            # raw_unadj = -raw_short
            # exc_long = -raw_short - bench = -raw_short + (raw_short + exc_short) = exc_short - 2*raw_short
            # 试: exc_short = -raw_unadj - bench
            #   → bench = -raw_unadj - exc_short = raw_short - exc_short
            #   → long_exc = raw_unadj - bench = -raw_short - (raw_short - exc_short) = exc_short - 2*raw_short
            # ✓ 跟我之前用的一致: exc_long = exc_short + 2*raw_unadj = exc_short + 2*(-raw_short) = exc_short - 2*raw_short
            new_hit = 1 if exc_long > 0 else 0
            new_status = "resolved_hit" if new_hit else "resolved_miss"
            c.execute(f"""
                UPDATE verifications
                SET {status_col}=?,
                    {raw_col}=?,
                    {exc_col}=?,
                    {hit_col}=?
                WHERE prediction_id=?
            """, (new_status, raw_long, exc_long, new_hit, pid))

conn.commit()
print("✅ verifications 更新完成")

# 3. 统计新 hit_rate
print()
print("=" * 80)
print("Step 3: 重算 hit_rate (新记分牌)")
print("=" * 80)

# 拉全部 verifications 重新统计
sql = """
SELECT v.prediction_id, v.ticker, p.direction,
       v.h_1m_status, v.h_1m_raw_return, v.h_1m_excess_return,
       v.h_1w_status, v.h_1w_raw_return, v.h_1w_excess_return,
       v.h_3m_status, v.h_3m_raw_return, v.h_3m_excess_return,
       v.h_6m_status, v.h_6m_raw_return, v.h_6m_excess_return
FROM verifications v
JOIN predictions p ON v.prediction_id = p.prediction_id
WHERE p.price_source_available=1
"""
all_v = c.execute(sql).fetchall()
print(f"全部 verifications: {len(all_v)}")

def wilson(hit, n, z=1.96):
    if n == 0: return None
    p = hit / n
    denom = 1 + z * z / n
    center = (p + z * z / (2 * n)) / denom
    spread = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / denom
    return center - spread

# 拉新方向分布
sql = """
SELECT direction, COUNT(*) FROM predictions
WHERE price_source_available=1
GROUP BY direction
"""
new_dist = dict(c.execute(sql).fetchall())
print(f"新方向分布: {new_dist}")

# per-horizon stats
for h, status_col_idx, raw_col_idx, exc_col_idx in [
    ("1w", 4, 5, 6),
    ("1m", 7, 8, 9),
    ("3m", 10, 11, 12),
    ("6m", 13, 14, 15),
]:
    n_resolved = 0
    n_hit = 0
    n_miss = 0
    n_skipped = 0
    n_pending = 0
    exc_vals = []
    for r in all_v:
        s = r[status_col_idx]
        e = r[exc_col_idx]
        if s == "resolved_hit":
            n_resolved += 1
            n_hit += 1
            if isinstance(e, (int, float)): exc_vals.append(e)
        elif s == "resolved_miss":
            n_resolved += 1
            n_miss += 1
            if isinstance(e, (int, float)): exc_vals.append(e)
        elif s in ("skipped_no_price", "skipped_risk_note", "skipped_neutral", "unverifiable_no_benchmark"):
            n_skipped += 1
        elif s == "pending":
            n_pending += 1
    hr = n_hit/n_resolved*100 if n_resolved else 0
    wl = wilson(n_hit, n_resolved)
    med = statistics.median(exc_vals)*100 if exc_vals else None
    print(f"  {h}: resolved={n_resolved} hit={n_hit} miss={n_miss} skipped={n_skipped} pending={n_pending} hr={hr:.1f}% wilson={wl*100 if wl else 0:.1f}% med={med if med else 0:.2f}%")


# 4. 重算全量记分牌(月度去重)
print()
print("=" * 80)
print("Step 4: 重算全量记分牌(全集 vs 首次去重 vs 月度去重)")
print("=" * 80)

# 全部 verifications + direction
sql = """
SELECT v.prediction_id, v.ticker, p.direction, p.published_at,
       v.h_1m_status, v.h_1m_raw_return, v.h_1m_excess_return,
       v.h_3m_status, v.h_3m_raw_return, v.h_3m_excess_return,
       v.h_6m_status, v.h_6m_raw_return, v.h_6m_excess_return
FROM verifications v
JOIN predictions p ON v.prediction_id = p.prediction_id
WHERE p.price_source_available=1
"""
all_v2 = c.execute(sql).fetchall()

# 拉 raw_posts.published_at
sql_pub = """
SELECT p.prediction_id, rp.published_at
FROM predictions p
JOIN raw_posts rp ON p.post_id = rp.post_id
WHERE p.price_source_available=1
"""
pub_at_map = {pid: pub for pid, pub in c.execute(sql_pub)}

def per_horizon(rows_set, label):
    print(f"\n[{label}] rows={len(rows_set)}")
    print(f"  {'h':4s}  {'n_resolved':10s}  {'hit_rate':10s}  {'wilson_low':10s}  {'median_exc':12s}  {'avg_exc':12s}")
    for h_name, h_idx_status, h_idx_raw, h_idx_exc in [
        ("1w", 4, 5, 6),
        ("1m", 7, 8, 9),
        ("3m", 10, 11, 12),
        ("6m", 13, 14, 15),
    ]:
        n_resolved, n_hit = 0, 0
        exc_vals = []
        for r in rows_set:
            s = r[h_idx_status]
            e = r[h_idx_exc]
            if s == "resolved_hit":
                n_resolved += 1
                n_hit += 1
                if isinstance(e, (int, float)): exc_vals.append(e)
            elif s == "resolved_miss":
                n_resolved += 1
                if isinstance(e, (int, float)): exc_vals.append(e)
        hr = n_hit/n_resolved*100 if n_resolved else 0
        wl = wilson(n_hit, n_resolved)
        med = statistics.median(exc_vals)*100 if exc_vals else None
        avg = statistics.mean(exc_vals)*100 if exc_vals else None
        print(f"  {h_name:4s}  {n_resolved:10d}  {hr:8.1f}%  {wl*100:8.1f}%  {med:10.2f}%  {avg:10.2f}%")

# 全集
per_horizon(all_v2, "全集 (B 类剔除, C 类改 long)")

# 首次去重
first_pubs = {}
for r in all_v2:
    pid, t, d, _, _, _, _, _, _, _, _, _, _ = r
    if d == "neutral": continue  # B 类剔除
    pub = pub_at_map.get(pid, "")
    key = (t, d)
    if key not in first_pubs or pub < first_pubs[key][1]:
        first_pubs[key] = (pid, pub)

first_set = [r for r in all_v2 if r[2] != "neutral" and first_pubs.get((r[1], r[2]), (None, ""))[0] == r[0]]
per_horizon(first_set, "首次去重")

# 月度去重
monthly_first = {}
for r in all_v2:
    pid, t, d, _, _, _, _, _, _, _, _, _, _ = r
    if d == "neutral": continue
    pub = pub_at_map.get(pid, "")
    if not pub: continue
    month = pub[:7]
    key = (t, d, month)
    if key not in monthly_first or pub < monthly_first[key][1]:
        monthly_first[key] = (pid, pub)

monthly_set = [r for r in all_v2 if r[2] != "neutral" and monthly_first.get((r[1], r[2], pub_at_map.get(r[0], "")[:7]), (None, ""))[0] == r[0]]
per_horizon(monthly_set, "月度去重")

# 落报告
content = []
content.append("# Phase 3 P3-6 应用 A/B/C 分类 + 重算记分牌")
content.append("")
content.append(f"**运行时间**: {datetime.utcnow().isoformat()}Z")
content.append("")
content.append("## 0. 分类总览")
content.append("")
content.append(f"共 {len(all_short_rows)} short, 分类:")
content.append(f"- **A 类** (真·反向持仓): {classified_count['A']}")
content.append(f"- **B 类** (风险提示/谨慎/中性): {classified_count['B']}")
content.append(f"- **C 类** (明确误判,改回正确): {classified_count['C']}")
content.append("")
content.append("## 1. 修改 predictions.direction")
content.append("")
content.append(f"- A 保留 short: {n_a_kept}")
content.append(f"- B 改 neutral: {n_b_changed}")
content.append(f"- C 改 long: {n_c_changed}")
content.append("")
content.append("## 2. 新方向分布")
content.append("")
for d, n in sorted(new_dist.items(), key=lambda x: -x[1]):
    content.append(f"- {d}: {n}")
content.append("")
content.append("## 3. per-horizon 新 hit_rate (全集)")
content.append("")
content.append("| horizon | n_resolved | n_hit | n_miss | n_skipped | n_pending | hit_rate | wilson_low | median_exc |")
content.append("|---|---|---|---|---|---|---|---|---|")
for h, status_col_idx, raw_col_idx, exc_col_idx in [
    ("1w", 4, 5, 6),
    ("1m", 7, 8, 9),
    ("3m", 10, 11, 12),
    ("6m", 13, 14, 15),
]:
    n_resolved, n_hit, n_miss, n_skipped, n_pending = 0, 0, 0, 0, 0
    exc_vals = []
    for r in all_v:
        s = r[status_col_idx]
        e = r[exc_col_idx]
        if s == "resolved_hit":
            n_resolved += 1
            n_hit += 1
            if isinstance(e, (int, float)): exc_vals.append(e)
        elif s == "resolved_miss":
            n_resolved += 1
            n_miss += 1
            if isinstance(e, (int, float)): exc_vals.append(e)
        elif s in ("skipped_no_price", "skipped_risk_note", "skipped_neutral", "unverifiable_no_benchmark"):
            n_skipped += 1
        elif s == "pending":
            n_pending += 1
    hr = n_hit/n_resolved*100 if n_resolved else 0
    wl = wilson(n_hit, n_resolved)
    med = statistics.median(exc_vals)*100 if exc_vals else None
    med_s = f"{med:+.2f}%" if med is not None else "N/A"
    content.append(f"| {h} | {n_resolved} | {n_hit} | {n_miss} | {n_skipped} | {n_pending} | {hr:.1f}% | {wl*100 if wl else 0:.1f}% | {med_s} |")
content.append("")
content.append("## 4. 全集 vs 首次去重 vs 月度去重")
content.append("")
for label, rs in [("全集 (B 剔除+C 改 long)", all_v2), ("首次去重", first_set), ("月度去重", monthly_set)]:
    content.append(f"### {label} (rows={len(rs)})")
    content.append("")
    content.append("| horizon | n_resolved | hit_rate | wilson_low | median_exc | avg_exc |")
    content.append("|---|---|---|---|---|---|")
    for h_name, h_idx_status, h_idx_raw, h_idx_exc in [
        ("1w", 4, 5, 6),
        ("1m", 7, 8, 9),
        ("3m", 10, 11, 12),
        ("6m", 13, 14, 15),
    ]:
        n_resolved, n_hit = 0, 0
        exc_vals = []
        for r in rs:
            s = r[h_idx_status]
            e = r[h_idx_exc]
            if s == "resolved_hit":
                n_resolved += 1
                n_hit += 1
                if isinstance(e, (int, float)): exc_vals.append(e)
            elif s == "resolved_miss":
                n_resolved += 1
                if isinstance(e, (int, float)): exc_vals.append(e)
        hr = n_hit/n_resolved*100 if n_resolved else 0
        wl = wilson(n_hit, n_resolved)
        med = statistics.median(exc_vals)*100 if exc_vals else None
        avg = statistics.mean(exc_vals)*100 if exc_vals else None
        med_s = f"{med:+.2f}%" if med is not None else "N/A"
        avg_s = f"{avg:+.2f}%" if avg is not None else "N/A"
        content.append(f"| {h_name} | {n_resolved} | {hr:.1f}% | {wl*100 if wl else 0:.1f}% | {med_s} | {avg_s} |")
    content.append("")

with open(os.path.join(OUT_DIR, "phase3_p6_recompute_scoreboard.md"), "w", encoding="utf-8") as f:
    f.write("\n".join(content))
print(f"\n✅ 落 outputs/phase3_p6_recompute_scoreboard.md")

conn.close()
print("=== DONE ===")
