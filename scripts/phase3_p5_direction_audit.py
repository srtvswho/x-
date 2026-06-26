"""Phase 3 P3-5 direction 审计

1. 列所有 163 short 预测,每条带 raw_text + LLM direction + excess
2. 重点:"同 ticker 大量 long 中混 short"的,逐条打印原文
3. 统计 short 集中度
4. 量化翻转影响(把可疑 short 改 long 后,excess 变化)
"""
from __future__ import annotations
import os, sqlite3
from datetime import datetime
from typing import Dict, List
from collections import Counter, defaultdict
import statistics, math

DB = "/workspace/data/signalboard_full.db"
OUT_DIR = "/workspace/outputs"
conn = sqlite3.connect(DB, timeout=30)
c = conn.cursor()

# 重点:同 ticker 大量 long 中混 short 的 ticker
SUSPECT_TICKERS = ["AAOI", "AXTI", "HIMS", "MU", "ARM", "POET", "ALAB", "RKLB", "SNDK", "AMD", "RDDT", "HOOD", "SLNH", "TSLA", "ONDS", "NVDA", "IREN", "CRWV", "CRCL", "ORCL"]


# 1. 全部 163 short 预测
print("=" * 80)
print("1. 全部 163 short 预测(按 ticker 集中度排序)")
print("=" * 80)

sql = """
SELECT p.prediction_id, p.ticker, p.direction, p.conviction,
       p.horizon, p.thesis_category, p.is_repeat_call, p.quantitative_claim, p.hedged, p.extraction_notes,
       v.published_at, v.entry_date_actual, v.entry_price,
       v.h_1m_status, v.h_1m_raw_return, v.h_1m_excess_return,
       v.h_1w_status, v.h_1w_raw_return, v.h_1w_excess_return,
       v.h_3m_status, v.h_3m_raw_return, v.h_3m_excess_return
FROM predictions p
JOIN verifications v ON p.prediction_id = v.prediction_id
WHERE p.price_source_available=1 AND p.direction='short'
ORDER BY p.ticker, v.published_at
"""
all_shorts = c.execute(sql).fetchall()
print(f"总共 {len(all_shorts)} short 预测")
print()

# 按 ticker 分组
shorts_by_ticker = defaultdict(list)
for r in all_shorts:
    shorts_by_ticker[r[1]].append(r)

# 找 long vs short 同 ticker 矛盾
print("### 矛盾 ticker 嫌疑表(同 ticker 大量 long 中混 short)")
sql_long_count = """
SELECT ticker, SUM(CASE WHEN direction='long' THEN 1 ELSE 0 END) n_long
FROM predictions
WHERE price_source_available=1
GROUP BY ticker
"""
long_counts = {t: n for t, n in c.execute(sql_long_count)}

# 按 short 集中度 + long 占比排
print(f"{'ticker':8s}  {'long':4s}  {'short':5s}  {'short_pct':10s}  嫌疑")
suspicious_short_data = {}
for t, rows in sorted(shorts_by_ticker.items(), key=lambda x: -len(x[1])):
    n_long = long_counts.get(t, 0)
    n_short = len(rows)
    short_pct = n_short / (n_long + n_short) * 100 if (n_long + n_short) else 0
    susp = ""
    if n_long >= 30 and n_short >= 1:
        susp = "⚠️ 高度可疑"
    elif n_long >= 10 and n_short >= 2:
        susp = "⚠ 可疑"
    print(f"  {t:8s}  {n_long:4d}  {n_short:5d}  {short_pct:8.1f}%  {susp}")
    if susp:
        suspicious_short_data[t] = rows
print()

# 2. 重点:逐条打印 suspect ticker 的 short 预测原文
print("=" * 80)
print("2. 嫌疑 ticker 的 short 预测 — 逐条原文 (LLM 是否误判)")
print("=" * 80)

# 拉 raw_post text
for ticker in sorted(suspicious_short_data.keys(), key=lambda t: -long_counts.get(t, 0)):
    try:
        rows = suspicious_short_data[ticker]
    except KeyError as e:
        print(f"KeyError for {ticker}")
        continue
    n_long = long_counts.get(t, 0)
    print(f"\n### {ticker}  (n_long={n_long}  n_short={len(rows)})")
    print("=" * 80)
    
    for i, r in enumerate(rows, 1):
        pid, t, dir_pred, conv, hz, thesis, is_repeat, qc, hedged, notes, \
        pub, edate, eprice, s1m, r1m, e1m, s1w, r1w, e1w, s3m, r3m, e3m = r
        # 拉原文
        sql_t = """
        SELECT rp.raw_text FROM predictions p
        JOIN raw_posts rp ON p.post_id = rp.post_id
        WHERE p.prediction_id = ?
        """
        text = c.execute(sql_t, (pid,)).fetchone()
        text_str = text[0] if text else "(no text)"
        # 截断长文
        if len(text_str) > 600:
            text_str = text_str[:600] + "...(truncated)"
        
        e1m_s = f"{e1m*100:+.2f}%" if e1m is not None else "N/A"
        e3m_s = f"{e3m*100:+.2f}%" if e3m is not None else "N/A"
        r1m_s = f"{r1m*100:+.2f}%" if r1m is not None else "N/A"
        r3m_s = f"{r3m*100:+.2f}%" if r3m is not None else "N/A"
        
        print(f"\n  [{i}] pred_id={pid[:8]}  pub={pub[:19]}  entry={edate}  px=${eprice}")
        print(f"      LLM 抽: dir={dir_pred}  conv={conv}  hz={hz}  thesis='{thesis}'  is_repeat={is_repeat}  hedged={hedged}")
        print(f"             qc='{qc}'  notes='{notes}'")
        print(f"      1m: status={s1m} raw={r1m_s} excess={e1m_s}")
        print(f"      3m: status={s3m} raw={r3m_s} excess={e3m_s}")
        print(f"      原文 ({len(text_str)} chars):")
        for line in text_str.split("\n"):
            print(f"        | {line}")


# 3. 全部 163 short 集中度(降序)+ 短头寸输赢分析
print()
print("=" * 80)
print("3. 全部 163 short 集中度排序")
print("=" * 80)

ticker_short_stats = {}
for t, rows in shorts_by_ticker.items():
    n_long = long_counts.get(t, 0)
    n_short = len(rows)
    n_1m_resolved = sum(1 for r in rows if r[11] in ("resolved_hit", "resolved_miss"))
    n_1m_hit = sum(1 for r in rows if r[11] == "resolved_hit")
    n_1m_miss = sum(1 for r in rows if r[11] == "resolved_miss")
    hr_1m = n_1m_hit/n_1m_resolved*100 if n_1m_resolved else 0
    # raw_return (short 后 = -raw, 但 raw 是 short 算后负的)
    raw_1m_vals = [r[12] for r in rows if r[12] is not None and r[11] in ("resolved_hit", "resolved_miss")]
    excess_1m_vals = [r[13] for r in rows if r[13] is not None and r[11] in ("resolved_hit", "resolved_miss")]
    median_excess = statistics.median(excess_1m_vals)*100 if excess_1m_vals else None
    ticker_short_stats[t] = {
        "n_long": n_long, "n_short": n_short, "n_1m_resolved": n_1m_resolved,
        "n_1m_hit": n_1m_hit, "n_1m_miss": n_1m_miss, "hr_1m": hr_1m,
        "median_excess": median_excess,
    }

print(f"\n{'ticker':8s}  {'n_long':6s}  {'n_short':7s}  {'1m_n':5s}  {'1m_hit':7s}  {'1m_med_exc':10s}")
for t, st in sorted(ticker_short_stats.items(), key=lambda x: -x[1]["n_short"]):
    me_s = f"{st['median_excess']:+.2f}%" if st['median_excess'] is not None else "N/A"
    print(f"  {t:8s}  {st['n_long']:6d}  {st['n_short']:7d}  {st['n_1m_resolved']:5d}  {st['hr_1m']:5.1f}%  {me_s:10s}")


# 4. 量化翻转影响
print()
print("=" * 80)
print("4. 翻转影响:把 suspect ticker 的 short 改 long 后,excess 重算")
print("=" * 80)

# 拿所有 short 预测的 1m raw_return(原始未取反的)
# 然后 short 改 long 后: excess_flip = -raw_return - bench
# 原来 short 算的: excess_short = -raw_return - bench
# 所以 excess_flip = excess_short (没变!因为 short 算的 raw_return 已经取反了)
# 
# 真正变的是 status: short 改 long 后:
#   如果 raw_return 原始 < 0 (跌): short 算 raw_return > 0 (hit), long 算 raw_return < 0 (miss)
#   如果 raw_return 原始 > 0 (涨): short 算 raw_return < 0 (miss), long 算 raw_return < 0 (miss)... wait 不对
#
# 短头寸: profit = -(exit-entry)/entry
#   如果 asset 跌, profit > 0
# 长头寸: profit = (exit-entry)/entry
#   如果 asset 涨, profit > 0
# 两者 raw_return 数值互为相反 (除了 short 取负)
#
# excess = raw_return - bench
# short 算的: excess_short = -(raw_unadj) - bench
# long 算的:  excess_long = (raw_unadj) - bench
# 差: excess_long - excess_short = 2 * (raw_unadj)
#
# 翻转后 excess_long = excess_short + 2 * raw_unadj
# 
# 翻转后 status 也要改:
# 原来 short 算的 status = "resolved_hit" if excess_short > 0 else "resolved_miss"
# 翻转后: status_long = "resolved_hit" if excess_long > 0 else "resolved_miss"

# 拿全部 suspect ticker 的 short 预测
total_flip_excess_change = 0
total_short_old_excess = 0
n_flip_from_miss_to_hit = 0
n_flip_from_hit_to_miss = 0

print(f"\n{'ticker':8s}  {'short#':6s}  {'1m_n':5s}  {'old_hit':7s}  {'new_hit':7s}  {'Δ_hit':7s}  {'med_exc_old':11s}  {'med_exc_new':11s}")

suspicious_total = {}
for t in sorted(suspicious_short_data.keys(), key=lambda x: -long_counts.get(x, 0)):
    rows = suspicious_short_data[t]
    n_short = len(rows)
    n_resolved = 0
    old_hits = 0
    new_hits = 0
    old_excess_vals = []
    new_excess_vals = []
    for r in rows:
        # r[12] = h_1m_raw_return (short 算的,取反后)
        # r[13] = h_1m_excess_return (short 算的)
        # 真实 raw_unadj = -h_1m_raw_return (因为 short 取反)
        # bench 不用,excess_long = excess_short + 2 * raw_unadj
        s1m, r1m, e1m = r[11], r[12], r[13]
        if s1m in ("resolved_hit", "resolved_miss"):
            n_resolved += 1
            if s1m == "resolved_hit":
                old_hits += 1
            old_excess_vals.append(e1m)
            # 翻转: raw_unadj = -r1m
            raw_unadj = -r1m if r1m is not None else None
            if r1m is not None:
                e_long = e1m + 2 * raw_unadj
                new_excess_vals.append(e_long)
                if e_long > 0 and e1m <= 0:
                    n_flip_from_miss_to_hit += 1
                elif e_long <= 0 and e1m > 0:
                    n_flip_from_hit_to_miss += 1
                if e_long > 0:
                    new_hits += 1
    
    old_hr = old_hits/n_resolved*100 if n_resolved else 0
    new_hr = new_hits/n_resolved*100 if n_resolved else 0
    med_old = statistics.median(old_excess_vals)*100 if old_excess_vals else None
    med_new = statistics.median(new_excess_vals)*100 if new_excess_vals else None
    med_old_s = f"{med_old:+.2f}%" if med_old is not None else "N/A"
    med_new_s = f"{med_new:+.2f}%" if med_new is not None else "N/A"
    print(f"  {t:8s}  {n_short:6d}  {n_resolved:5d}  {old_hr:5.1f}%  {new_hr:5.1f}%  {new_hr-old_hr:+5.1f}pp  {med_old_s:10s}  {med_new_s:10s}")
    suspicious_total[t] = {
        "n_short": n_short, "n_resolved": n_resolved,
        "old_hits": old_hits, "new_hits": new_hits,
        "med_old": med_old, "med_new": med_new,
    }

# 整体翻转影响
print(f"\n翻转后 (suspect ticker 全部 short→long):")
print(f"  miss→hit (原亏损变盈利): {n_flip_from_miss_to_hit} 条")
print(f"  hit→miss (原盈利变亏损): {n_flip_from_hit_to_miss} 条")
print(f"  净翻转: {n_flip_from_miss_to_hit - n_flip_from_hit_to_miss}")


# 5. 落报告
print()
print("=" * 80)
print("落报告")
print("=" * 80)

content = []
content.append("# Phase 3 P3-5 direction 审计: 怀疑 LLM 方向抽取系统性误判")
content.append("")
content.append(f"**运行时间**: {datetime.utcnow().isoformat()}Z")
content.append("")
content.append("## 0. 总览")
content.append("")
content.append("| 方向 | n | 占比 |")
content.append("|---|---|---|")
content.append("| long | 3808 | 95.6% |")
content.append("| short | 163 | 4.1% |")
content.append("| neutral | 12 | 0.3% |")
content.append("")
content.append("**用户怀疑**: short 抽取准确率从未被校准,可能系统性毒化'输家'榜。")
content.append("如果她长期看多的票(AAOI/AXTI/MU)被误标为 short,真实涨幅会变成 short 视角的暴亏。")
content.append("")
content.append("## 1. 全部 163 short 集中度 + 嫌疑表")
content.append("")
content.append("| ticker | n_long | n_short | short_pct | 嫌疑 |")
content.append("|---|---|---|---|---|")
for t, rows in sorted(shorts_by_ticker.items(), key=lambda x: -len(x[1])):
    n_long = long_counts.get(t, 0)
    n_short = len(rows)
    short_pct = n_short / (n_long + n_short) * 100 if (n_long + n_short) else 0
    susp = ""
    if n_long >= 30 and n_short >= 1:
        susp = "⚠️ 高度可疑"
    elif n_long >= 10 and n_short >= 2:
        susp = "⚠ 可疑"
    content.append(f"| {t} | {n_long} | {n_short} | {short_pct:.1f}% | {susp} |")
content.append("")

content.append("## 2. 嫌疑 ticker 逐条原文(LLM 是否误判)")
content.append("")
for ticker in sorted(suspicious_short_data.keys(), key=lambda t: -long_counts.get(t, 0)):
    rows = suspicious_short_data[ticker]
    n_long = long_counts.get(ticker, 0)
    content.append(f"### {ticker} (n_long={n_long}  n_short={len(rows)})")
    content.append("")
    for i, r in enumerate(rows, 1):
        pid, t, dir_pred, conv, hz, thesis, is_repeat, qc, hedged, notes, \
        pub, edate, eprice, s1m, r1m, e1m, s1w, r1w, e1w, s3m, r3m, e3m = r
        # 拉原文
        sql_t = """
        SELECT rp.raw_text FROM predictions p
        JOIN raw_posts rp ON p.post_id = rp.post_id
        WHERE p.prediction_id = ?
        """
        text = c.execute(sql_t, (pid,)).fetchone()
        text_str = text[0] if text else "(no text)"
        if len(text_str) > 600:
            text_str = text_str[:600] + "...(truncated)"
        e1m_s = f"{e1m*100:+.2f}%" if e1m is not None else "N/A"
        e3m_s = f"{e3m*100:+.2f}%" if e3m is not None else "N/A"
        r1m_s = f"{r1m*100:+.2f}%" if r1m is not None else "N/A"
        r3m_s = f"{r3m*100:+.2f}%" if r3m is not None else "N/A"
        
        content.append(f"\n**[{i}]** `{pid[:8]}` pub={pub[:19]} entry={edate} px=${eprice}")
        content.append(f"- LLM 抽: dir={dir_pred} conv={conv} hz={hz} thesis='{thesis}' is_repeat={is_repeat} hedged={hedged}")
        content.append(f"- qc='{qc}' notes='{notes}'")
        content.append(f"- 1m: status={s1m} raw={r1m_s} excess={e1m_s}")
        content.append(f"- 3m: status={s3m} raw={r3m_s} excess={e3m_s}")
        content.append(f"- 原文 ({len(text_str)} chars):")
        content.append("```")
        for line in text_str.split("\n"):
            content.append(f"| {line}")
        content.append("```")
    content.append("")

content.append("## 3. 全部 163 short 集中度 + 1m hit_rate")
content.append("")
content.append("| ticker | n_long | n_short | 1m_n | 1m_hit | 1m_med_exc |")
content.append("|---|---|---|---|---|---|")
for t, st in sorted(ticker_short_stats.items(), key=lambda x: -x[1]["n_short"]):
    me_s = f"{st['median_excess']:+.2f}%" if st['median_excess'] is not None else "N/A"
    content.append(f"| {t} | {st['n_long']} | {st['n_short']} | {st['n_1m_resolved']} | {st['hr_1m']:.1f}% | {me_s} |")
content.append("")

content.append("## 4. 翻转影响(把 suspect ticker 的 short 改 long 后,excess 重算)")
content.append("")
content.append("**注意**: excess_long = excess_short + 2 × raw_unadj (因为 short 把 raw 取反)")
content.append("")
content.append("| ticker | n_short | 1m_n | old_hit | new_hit | Δ_hit | med_exc_old | med_exc_new |")
content.append("|---|---|---|---|---|---|---|---|")
for t, st in sorted(suspicious_total.items(), key=lambda x: -x[1]["n_short"]):
    me_old_s = f"{st['med_old']:+.2f}%" if st['med_old'] is not None else "N/A"
    me_new_s = f"{st['med_new']:+.2f}%" if st['med_new'] is not None else "N/A"
    content.append(f"| {t} | {st['n_short']} | {st['n_resolved']} | {st['old_hits']} | {st['new_hits']} | {st['new_hits']-st['old_hits']:+d} | {me_old_s} | {me_new_s} |")
content.append("")
content.append(f"**净翻转影响**: miss→hit {n_flip_from_miss_to_hit} 条, hit→miss {n_flip_from_hit_to_miss} 条")
content.append("")

content.append("## 5. 追溯根因(待)")
content.append("")
content.append("待查:")
content.append("1. LLM 抽取 prompt 对 direction 的判定规则")
content.append("2. few-shot 里有没有 short 例子")
content.append("3. 校准阶段是否覆盖 short (20 金 + 30 盲几乎全 long)")

with open(os.path.join(OUT_DIR, "phase3_p5_direction_audit.md"), "w", encoding="utf-8") as f:
    f.write("\n".join(content))
print(f"✅ 落 outputs/phase3_p5_direction_audit.md")
conn.close()
print("=== DONE ===")
