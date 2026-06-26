"""Phase 3 P3-4 结构化 case 抽样 — 4 组证据

第一组:AAOI / AXTI / LITE / NBIS 全部预测明细 + ticker 自身涨幅
第二组:excess 最高 15 / 最低 15
第三组:分领域 hit_rate
第四组:追高 vs 预言 — 5 只大涨票的"她首喊价" vs "起涨价"
"""
from __future__ import annotations
import os, json, sqlite3, time
from datetime import datetime
from typing import Dict, List
from collections import Counter, defaultdict
import math, statistics

DB = "/workspace/data/signalboard_full.db"
OUT_DIR = "/workspace/outputs"

conn = sqlite3.connect(DB, timeout=30)
c = conn.cursor()

# 板块分类 (基于业务常识)
SECTOR = {
    # 光通信 / 半导体
    "AAOI": "光通信", "AXTI": "光通信", "LITE": "光通信", "NBIS": "AI算力/光通信",
    "SIVE": "光通信", "COHR": "光通信", "CRDO": "光通信", "SOI": "半导体",
    "IQE": "光通信", "AEHR": "半导体设备", "TSEM": "半导体", "MU": "半导体",
    "MRVL": "半导体", "AMD": "半导体", "ALAB": "半导体", "TSM": "半导体",
    "SNDK": "半导体", "WOLF": "半导体", "RMBS": "半导体", "NVMI": "半导体设备",
    "VECO": "半导体设备", "NVDA": "AI算力/半导体", "INTC": "半导体", "QCOM": "半导体",
    "CRWV": "AI算力/数据中心", "CRDO": "光通信", "FN": "光通信杠杆ETF", "FNGU": "AI/科技ETF",
    "SOXL": "半导体ETF", "SOXS": "半导体反向ETF", "SMH": "半导体ETF", "SOXX": "半导体ETF",
    "UFO": "AI/科技ETF", "WGMI": "加密矿企ETF", "BITQ": "加密ETF", "IRBT": "防务/消费",
    # AI 算力
    "SMCI": "AI算力/服务器", "CRCL": "AI算力/数据中心", "NBIS": "AI算力",
    # 加密
    "MARA": "加密", "RIOT": "加密", "CLSK": "加密", "HUT": "加密", "BTBT": "加密",
    "IREN": "加密", "WULF": "加密", "CIFR": "加密",
    # 互联网/AI 应用
    "META": "AI应用/互联网", "AMZN": "AI应用/互联网", "RDDT": "AI应用/互联网", "SNAP": "互联网",
    "AAPL": "AI应用/互联网", "GOOG": "AI应用/互联网", "MSFT": "AI应用/互联网", "NVDA": "AI应用/互联网",
    "HIMS": "消费/医疗", "PLTR": "AI应用",
    # 防务
    "AVGR": "防务", "RKLB": "防务/航天", "PL": "防务/航天", "LUNR": "防务/航天",
    "ASTS": "防务/航天", "VRA": "消费", "SGBX": "消费",
    # SPY 类基准
    "SPY": "基准/ETF", "QQQ": "基准/ETF", "IWM": "基准/ETF",
}


def sector_of(t):
    return SECTOR.get(t, "其他")


# ============== 第一组:AAOI/AXTI/LITE/NBIS ==============
print("=" * 80)
print("第一组: 招牌光通信标的 — AAOI / AXTI / LITE / NBIS")
print("=" * 80)

GROUP1 = ["AAOI", "AXTI", "LITE", "NBIS"]

group1_data = {}
for ticker in GROUP1:
    print(f"\n### {ticker} ({sector_of(ticker)})")
    sql = """
    SELECT prediction_id, published_at, direction,
           entry_date_actual, entry_price,
           h_1w_status, h_1w_actual_exit, h_1w_exit_price, h_1w_raw_return, h_1w_excess_return,
           h_1m_status, h_1m_actual_exit, h_1m_exit_price, h_1m_raw_return, h_1m_excess_return,
           h_3m_status, h_3m_actual_exit, h_3m_exit_price, h_3m_raw_return, h_3m_excess_return,
           h_6m_status, h_6m_actual_exit, h_6m_exit_price, h_6m_raw_return, h_6m_excess_return
    FROM verifications
    WHERE ticker=?
    ORDER BY published_at
    """
    rows = c.execute(sql, (ticker,)).fetchall()
    print(f"  总条数: {len(rows)}")
    group1_data[ticker] = rows
    
    # 统计 1m hit_rate / median excess
    h1m_hits, h1m_total = 0, 0
    h1m_excess_vals = []
    h3m_hits, h3m_total = 0, 0
    h3m_excess_vals = []
    entry_dates = []
    for r in rows:
        # 列: 0=pid, 1=pub, 2=dir, 3=edate, 4=eprice
        # 5=h_1w_status, 6=h_1w_actual, 7=h_1w_exit_px, 8=h_1w_raw, 9=h_1w_excess
        # 10=h_1m_status, 11=h_1m_actual, 12=h_1m_exit_px, 13=h_1m_raw, 14=h_1m_excess
        # 15=h_3m_status, 16=h_3m_actual, 17=h_3m_exit_px, 18=h_3m_raw, 19=h_3m_excess
        # 20=h_6m_status, 21=h_6m_actual, 22=h_6m_exit_px, 23=h_6m_raw, 24=h_6m_excess
        if r[10] in ("resolved_hit", "resolved_miss"):
            h1m_total += 1
            if r[10] == "resolved_hit":
                h1m_hits += 1
            if r[14] is not None:
                h1m_excess_vals.append(r[14])
        if r[15] in ("resolved_hit", "resolved_miss"):
            h3m_total += 1
            if r[15] == "resolved_hit":
                h3m_hits += 1
            if r[19] is not None:
                h3m_excess_vals.append(r[19])
        if r[3]:
            entry_dates.append(r[3])
    
    h1m_hr = h1m_hits/h1m_total*100 if h1m_total else 0
    h3m_hr = h3m_hits/h3m_total*100 if h3m_total else 0
    h1m_med = statistics.median(h1m_excess_vals)*100 if h1m_excess_vals else None
    h3m_med = statistics.median(h3m_excess_vals)*100 if h3m_excess_vals else None
    print(f"  1m: n_resolved={h1m_total} hit_rate={h1m_hr:.1f}% median_excess={h1m_med:+.2f}%" if h1m_med is not None else f"  1m: n_resolved={h1m_total} hit_rate={h1m_hr:.1f}%")
    print(f"  3m: n_resolved={h3m_total} hit_rate={h3m_hr:.1f}% median_excess={h3m_med:+.2f}%" if h3m_med is not None else f"  3m: n_resolved={h3m_total} hit_rate={h3m_hr:.1f}%")
    
    # 票自身区间涨幅
    if rows:
        first_pub = rows[0][1][:10]
        last_pub = rows[-1][1][:10]
        print(f"  票自身区间: {first_pub} → {last_pub}")
        
        # 拿票的 first_entry 日期收盘价 vs last_entry 日期收盘价
        sql_p = f"SELECT prediction_id, published_at, entry_date_actual, entry_price FROM verifications WHERE ticker='{ticker}' AND entry_date_actual IS NOT NULL ORDER BY entry_date_actual ASC LIMIT 1"
        r0 = c.execute(sql_p).fetchone()
        sql_p2 = f"SELECT prediction_id, published_at, entry_date_actual, entry_price FROM verifications WHERE ticker='{ticker}' AND entry_date_actual IS NOT NULL ORDER BY entry_date_actual DESC LIMIT 1"
        r1 = c.execute(sql_p2).fetchone()
        if r0 and r1:
            # 简化:用 entry_date_actual first/last + 找该日期收盘价
            print(f"    最早 entry_date: {r0[2]}  entry_price: ${r0[3]:.4f}")
            print(f"    最晚 entry_date: {r1[2]}  entry_price: ${r1[3]:.4f}")


# 把第一组详细明细落文件
group1_md = ["# 第一组: 光通信标的 AAOI / AXTI / LITE / NBIS 全部预测明细", ""]
for ticker in GROUP1:
    rows = group1_data[ticker]
    group1_md.append(f"## {ticker} ({sector_of(ticker)})")
    group1_md.append("")
    group1_md.append(f"**总条数**: {len(rows)}")
    group1_md.append("")
    group1_md.append("| # | pub_date | dir | cv | entry_date | entry_px | 1m_status | 1m_exit | 1m_px | 1m_raw | 1m_excess | 3m_status | 3m_raw | 3m_excess |")
    group1_md.append("|---|---|---|---|---|---|---|---|---|---|---|---|---|---|")
    for i, r in enumerate(rows, 1):
        # 列: 0=pid, 1=pub, 2=dir, 3=edate, 4=eprice
        # 5=h_1w_status, 6=h_1w_actual, 7=h_1w_exit_px, 8=h_1w_raw, 9=h_1w_excess
        # 10=h_1m_status, 11=h_1m_actual, 12=h_1m_exit_px, 13=h_1m_raw, 14=h_1m_excess
        # 15=h_3m_status, 16=h_3m_actual, 17=h_3m_exit_px, 18=h_3m_raw, 19=h_3m_excess
        # 20=h_6m_status, 21=h_6m_actual, 22=h_6m_exit_px, 23=h_6m_raw, 24=h_6m_excess
        pub, direction, edate, eprice = r[1], r[2], r[3], r[4]
        s1m, ae1m, ep1m, r1m, e1m = r[10], r[11], r[12], r[13], r[14]
        s3m, ae3m, ep3m, r3m, e3m = r[15], r[16], r[17], r[18], r[19]
        pub_s = pub[:10] if pub else "NULL"
        edate_s = edate or "NULL"
        eprice_s = f"${eprice:.4f}" if eprice else "N/A"
        s1m_s = s1m[:10] if s1m and "resolved" in s1m else (s1m or "NULL")
        ae1m_s = ae1m or "NULL"
        ep1m_s = f"${ep1m:.4f}" if ep1m else "N/A"
        r1m_s = f"{r1m*100:+.1f}%" if r1m is not None else "N/A"
        e1m_s = f"{e1m*100:+.1f}%" if e1m is not None else "N/A"
        s3m_s = s3m[:10] if s3m and "resolved" in s3m else (s3m or "NULL")
        r3m_s = f"{r3m*100:+.1f}%" if r3m is not None else "N/A"
        e3m_s = f"{e3m*100:+.1f}%" if e3m is not None else "N/A"
        group1_md.append(f"| {i} | {pub_s} | {direction} | - | {edate_s} | {eprice_s} | {s1m_s} | {ae1m_s} | {ep1m_s} | {r1m_s} | {e1m_s} | {s3m_s} | {r3m_s} | {e3m_s} |")
    group1_md.append("")

with open(os.path.join(OUT_DIR, "phase3_p4_group1_optoelec.md"), "w", encoding="utf-8") as f:
    f.write("\n".join(group1_md))
print(f"\n✅ 落 outputs/phase3_p4_group1_optoelec.md")


# ============== 第二组:最大赢家 / 最大输家 ==============
print()
print("=" * 80)
print("第二组: 她的最大赢家 & 最大输家")
print("=" * 80)

# 找 1m 和 3m excess 排序的极值
# 用 1m excess (样本最多)
sql = """
SELECT prediction_id, ticker, direction, published_at,
       entry_date_actual, entry_price,
       h_1m_status, h_1m_excess_return, h_1m_raw_return, h_1m_benchmark_return,
       h_3m_status, h_3m_excess_return, h_3m_raw_return, h_3m_benchmark_return
FROM verifications
WHERE h_1m_status IN ('resolved_hit', 'resolved_miss')
ORDER BY h_1m_excess_return DESC
LIMIT 15
"""
print("\n1m excess 最高 15 条 (她最神的预测):")
winners = c.execute(sql).fetchall()
for r in winners:
    pid, t, d, pub, ed, ep, s, ex, r_raw, b, s3, ex3, r3, b3 = r
    ex3_s = f"{ex3*100:+.2f}%" if ex3 is not None else "N/A"
    print(f"  {t:6s} {d:6s} pub={pub[:10]} entry={ed} px=${ep:.4f} 1m_excess={ex*100:+.2f}% raw={r_raw*100:+.2f}% bench={b*100:+.2f}% 3m_excess={ex3_s}")

sql = """
SELECT prediction_id, ticker, direction, published_at,
       entry_date_actual, entry_price,
       h_1m_status, h_1m_excess_return, h_1m_raw_return, h_1m_benchmark_return,
       h_3m_status, h_3m_excess_return, h_3m_raw_return, h_3m_benchmark_return
FROM verifications
WHERE h_1m_status IN ('resolved_hit', 'resolved_miss')
ORDER BY h_1m_excess_return ASC
LIMIT 15
"""
print("\n1m excess 最低 15 条 (她最惨的预测):")
losers = c.execute(sql).fetchall()
for r in losers:
    pid, t, d, pub, ed, ep, s, ex, r_raw, b, s3, ex3, r3, b3 = r
    ex3_s = f"{ex3*100:+.2f}%" if ex3 is not None else "N/A"
    print(f"  {t:6s} {d:6s} pub={pub[:10]} entry={ed} px=${ep:.4f} 1m_excess={ex*100:+.2f}% raw={r_raw*100:+.2f}% bench={b*100:+.2f}% 3m_excess={ex3_s}")


# ============== 第三组:分领域 ==============
print()
print("=" * 80)
print("第三组: 分领域 — 板块 hit_rate / 中位 excess")
print("=" * 80)

# 拉所有 verifications,分 sector,只算 long
sql = """
SELECT ticker, direction, h_1m_status, h_1m_excess_return, h_1m_raw_return,
       h_3m_status, h_3m_excess_return, h_3m_raw_return
FROM verifications
"""
all_v = c.execute(sql).fetchall()

sector_stats = defaultdict(lambda: {
    "long_1m_hits": 0, "long_1m_total": 0, "long_1m_excess": [],
    "long_3m_hits": 0, "long_3m_total": 0, "long_3m_excess": [],
    "all_1m_hits": 0, "all_1m_total": 0,
    "tickers": set(),
    "n_predictions": 0,
})

for r in all_v:
    t, d, s1m, e1m, r1m, s3m, e3m, r3m = r
    sec = sector_of(t)
    sector_stats[sec]["tickers"].add(t)
    sector_stats[sec]["n_predictions"] += 1
    if s1m in ("resolved_hit", "resolved_miss"):
        sector_stats[sec]["all_1m_total"] += 1
        if s1m == "resolved_hit":
            sector_stats[sec]["all_1m_hits"] += 1
    if d == "long":
        if s1m in ("resolved_hit", "resolved_miss"):
            sector_stats[sec]["long_1m_total"] += 1
            if s1m == "resolved_hit":
                sector_stats[sec]["long_1m_hits"] += 1
            if e1m is not None:
                sector_stats[sec]["long_1m_excess"].append(e1m)
        if s3m in ("resolved_hit", "resolved_miss"):
            sector_stats[sec]["long_3m_total"] += 1
            if s3m == "resolved_hit":
                sector_stats[sec]["long_3m_hits"] += 1
            if e3m is not None:
                sector_stats[sec]["long_3m_excess"].append(e3m)

print(f"\n{'板块':18s}  {'long预测':8s}  {'1m_n':6s}  {'1m_hit':8s}  {'1m_med_exc':10s}  {'3m_n':6s}  {'3m_hit':8s}  {'3m_med_exc':10s}  {'tickers':40s}")
sector_rows = []
for sec, st in sorted(sector_stats.items(), key=lambda x: -x[1]["n_predictions"]):
    n_long = st["n_predictions"]  # 简化:实际只统计了 all
    n1 = st["long_1m_total"]
    h1 = st["long_1m_hits"]
    hr1 = h1/n1*100 if n1 else 0
    me1 = statistics.median(st["long_1m_excess"])*100 if st["long_1m_excess"] else None
    n3 = st["long_3m_total"]
    h3 = st["long_3m_hits"]
    hr3 = h3/n3*100 if n3 else 0
    me3 = statistics.median(st["long_3m_excess"])*100 if st["long_3m_excess"] else None
    me1_s = f"{me1:+.2f}%" if me1 is not None else "N/A"
    me3_s = f"{me3:+.2f}%" if me3 is not None else "N/A"
    tickers_s = ", ".join(sorted(st["tickers"]))
    print(f"  {sec:18s}  {n_long:8d}  {n1:6d}  {hr1:6.1f}%  {me1_s:10s}  {n3:6d}  {hr3:6.1f}%  {me3_s:10s}  {tickers_s}")
    sector_rows.append((sec, n_long, n1, hr1, me1_s, n3, hr3, me3_s, tickers_s))


# ============== 第四组:追高 vs 预言 ==============
print()
print("=" * 80)
print("第四组: 追高 vs 预言 — 5 只大涨票")
print("=" * 80)

# 选她喊最多 / 该票这段时间大涨的 5 个 ticker
# NBIS 364 / SIVE 346 / AAOI 186 / AXTI 156 / LITE 106 — 选这 5 只
# 票的"起涨点" = 该票 entry_date_actual 最早的预测对应 entry_date
# "她首喊" = 她首次 published_at

BIG_WINNERS = ["NBIS", "SIVE", "AAOI", "AXTI", "LITE"]

import requests
POLY = os.environ.get("POLYGON_API_KEY", "")

def fetch_polygon(symbol, start, end):
    r = requests.get(
        f"https://api.polygon.io/v2/aggs/ticker/{symbol}/range/1/day/{start}/{end}",
        params={"adjusted": "true", "sort": "asc", "limit": 500, "apiKey": POLY},
        timeout=30
    )
    return r.json().get("results", [])

def find_first_above(bars, ref_price, ratio):
    """找到 bars 中第一次 close > ref_price * (1+ratio) 的 bar"""
    for b in bars:
        if b["c"] >= ref_price * (1 + ratio):
            return b
    return None

for t in BIG_WINNERS:
    print(f"\n### {t}")
    # 她首次喊的日期 + entry_price
    sql = f"SELECT published_at, entry_date_actual, entry_price FROM verifications WHERE ticker='{t}' AND entry_date_actual IS NOT NULL ORDER BY published_at ASC LIMIT 1"
    r0 = c.execute(sql).fetchone()
    if not r0:
        print(f"  没数据")
        continue
    her_first_pub = r0[0][:10] if r0[0] else None
    her_first_entry_date = r0[1]
    her_first_entry_price = r0[2]
    print(f"  她首次喊: pub={her_first_pub}  entry={her_first_entry_date}  entry_price=${her_first_entry_price:.4f}")
    
    # 拿她首次喊之前 + 之后的 bar 数据 (从 2024-06-17 到 2026-06-12 整个 2 年)
    cache_path = f"/workspace/data/price_cache/{t}_FULL_HISTORY.json"
    if not os.path.exists(cache_path) and t == "SIVE":
        cache_path = "/workspace/data/price_cache/SIVEF_FULL_HISTORY.json"
    if os.path.exists(cache_path):
        with open(cache_path) as f:
            data = json.load(f)
            bars = data if isinstance(data, list) else data.get("bars", [])
    else:
        bars = fetch_polygon(t, "2024-06-17", "2026-06-15")
    
    if not bars:
        print(f"  无 bars 数据")
        continue
    
    # 票的"区间起涨点" — 找 her_first_entry_date 之前 30 天最低收盘价 → 第一个回升点
    her_entry_idx = None
    for i, b in enumerate(bars):
        if b["date"] >= her_first_entry_date:
            her_entry_idx = i
            break
    if her_entry_idx is None:
        print(f"  entry_date 超出数据范围")
        continue
    
    # her_entry 之前 60 天的最低价 (作为"起涨前" 锚点)
    window = bars[max(0, her_entry_idx - 60):her_entry_idx + 1]
    if not window:
        # 数据从 entry 开始,没 60 天
        window = bars[:her_entry_idx + 1]
    if not window:
        continue
    pre_low = min(b["l"] for b in window)
    pre_high = max(b["h"] for b in window)
    pre_low_date = [b["date"] for b in window if b["l"] == pre_low][0]
    pre_high_date = [b["date"] for b in window if b["h"] == pre_high][0]
    
    # 当前价 (2026-06-12 之前最后 close)
    cur = bars[-1]
    
    print(f"  她 entry 之前 60 天: low ${pre_low:.4f} ({pre_low_date})  high ${pre_high:.4f} ({pre_high_date})")
    print(f"  票当前: ${cur['c']:.4f} ({cur['date']})")
    
    # 算"起涨点" = 区间最低点 (假设是起涨前的低)
    # 算 her entry 价相对 pre_low 的位置
    pct_above_low = (her_first_entry_price - pre_low) / pre_low * 100
    pct_below_high = (pre_high - her_first_entry_price) / pre_high * 100
    print(f"  她的 entry 价相对 pre_low: +{pct_above_low:.1f}%  相对 pre_high: -{pct_below_high:.1f}%")
    
    # 票从 her entry 到当前的涨幅
    pct_to_cur = (cur["c"] - her_first_entry_price) / her_first_entry_price * 100
    print(f"  票从 her entry 到当前: {pct_to_cur:+.1f}%")
    
    # 票从 pre_low 到当前的涨幅
    pct_from_low = (cur["c"] - pre_low) / pre_low * 100
    print(f"  票从 pre_low 到当前: {pct_from_low:+.1f}%")
    
    # 她的平均入场点 vs pre_low
    sql_avg = f"SELECT AVG(entry_price), MIN(entry_price), MAX(entry_price) FROM verifications WHERE ticker='{t}' AND entry_date_actual IS NOT NULL"
    avg, mn, mx = c.execute(sql_avg).fetchone()
    pct_avg_above_low = (avg - pre_low) / pre_low * 100
    print(f"  她的平均入场: ${avg:.4f} (min=${mn:.4f}, max=${mx:.4f})  相对 pre_low: +{pct_avg_above_low:.1f}%")
    
    time.sleep(13)  # polygon rate limit


# ============== 落报告 ==============
print()
print("=" * 80)
print("落报告")
print("=" * 80)

content = []
content.append("# Phase 3 P3-4 结构化 case 抽样 — 4 组证据")
content.append("")
content.append(f"**运行时间**: {datetime.utcnow().isoformat()}Z")
content.append("")
content.append("## 第一组: 招牌光通信标的 — AAOI / AXTI / LITE / NBIS")
content.append("")
content.append("明细见 `outputs/phase3_p4_group1_optoelec.md`")
content.append("")
content.append("汇总 hit_rate / median_excess:")
for ticker in GROUP1:
    rows = group1_data[ticker]
    h1m_hits, h1m_total = 0, 0
    h1m_excess_vals = []
    h3m_hits, h3m_total = 0, 0
    h3m_excess_vals = []
    for r in rows:
        if r[7] in ("resolved_hit", "resolved_miss"):
            h1m_total += 1
            if r[7] == "resolved_hit":
                h1m_hits += 1
            if r[12] is not None:
                h1m_excess_vals.append(r[12])
        if r[17] in ("resolved_hit", "resolved_miss"):
            h3m_total += 1
            if r[17] == "resolved_hit":
                h3m_hits += 1
            if r[22] is not None:
                h3m_excess_vals.append(r[22])
    h1m_hr = h1m_hits/h1m_total*100 if h1m_total else 0
    h3m_hr = h3m_hits/h3m_total*100 if h3m_total else 0
    h1m_med = statistics.median(h1m_excess_vals)*100 if h1m_excess_vals else None
    h3m_med = statistics.median(h3m_excess_vals)*100 if h3m_excess_vals else None
    h1m_med_s = f"{h1m_med:+.2f}%" if h1m_med is not None else "N/A"
    h3m_med_s = f"{h3m_med:+.2f}%" if h3m_med is not None else "N/A"
    content.append(f"- **{ticker}** ({sector_of(ticker)}): 1m n={h1m_total} hit={h1m_hr:.1f}% med={h1m_med_s} | 3m n={h3m_total} hit={h3m_hr:.1f}% med={h3m_med_s}")


content.append("")
content.append("## 第二组: 最大赢家 & 最大输家")
content.append("")
content.append("### 1m excess 最高 15 条")
content.append("")
content.append("| # | ticker | dir | pub | entry_date | entry_px | 1m_excess | 1m_raw | bench | 3m_excess |")
content.append("|---|---|---|---|---|---|---|---|---|---|")
for i, r in enumerate(winners, 1):
    pid, t, d, pub, ed, ep, s, ex, r_raw, b, s3, ex3, r3, b3 = r
    pub_s = pub[:10]
    ed_s = ed or "NULL"
    ep_s = f"${ep:.4f}" if ep else "N/A"
    ex3_s = f"{ex3*100:+.2f}%" if ex3 is not None else "N/A"
    content.append(f"| {i} | {t} | {d} | {pub_s} | {ed_s} | {ep_s} | {ex*100:+.2f}% | {r_raw*100:+.2f}% | {b*100:+.2f}% | {ex3_s} |")

content.append("")
content.append("### 1m excess 最低 15 条")
content.append("")
content.append("| # | ticker | dir | pub | entry_date | entry_px | 1m_excess | 1m_raw | bench | 3m_excess |")
content.append("|---|---|---|---|---|---|---|---|---|---|")
for i, r in enumerate(losers, 1):
    pid, t, d, pub, ed, ep, s, ex, r_raw, b, s3, ex3, r3, b3 = r
    pub_s = pub[:10]
    ed_s = ed or "NULL"
    ep_s = f"${ep:.4f}" if ep else "N/A"
    ex3_s = f"{ex3*100:+.2f}%" if ex3 is not None else "N/A"
    content.append(f"| {i} | {t} | {d} | {pub_s} | {ed_s} | {ep_s} | {ex*100:+.2f}% | {r_raw*100:+.2f}% | {b*100:+.2f}% | {ex3_s} |")

content.append("")
content.append("## 第三组: 分领域 — 板块 hit_rate / 中位 excess (long 头寸)")
content.append("")
content.append("| 板块 | n预测 | 1m_n | 1m_hit | 1m_med_excess | 3m_n | 3m_hit | 3m_med_excess | tickers |")
content.append("|---|---|---|---|---|---|---|---|---|")
for sec, n_long, n1, hr1, me1_s, n3, hr3, me3_s, tickers_s in sector_rows:
    content.append(f"| {sec} | {n_long} | {n1} | {hr1:.1f}% | {me1_s} | {n3} | {hr3:.1f}% | {me3_s} | {tickers_s} |")

content.append("")
content.append("## 第四组: 追高 vs 预言 (5 只大涨票)")
content.append("")
content.append("(实际值见终端输出,见上)")

with open(os.path.join(OUT_DIR, "phase3_p4_case_study.md"), "w", encoding="utf-8") as f:
    f.write("\n".join(content))
print(f"✅ 落 outputs/phase3_p4_case_study.md")

conn.close()
print("=== DONE ===")
