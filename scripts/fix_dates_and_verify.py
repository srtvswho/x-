"""修 direction_3kols_v2.json 的 date 字段 (之前 [:10] 解析错)
+ 重跑 verify
"""
import json
import os
import re
import statistics
from collections import Counter, defaultdict
from datetime import datetime, timedelta
from email.utils import parsedate_to_datetime
from pathlib import Path

PRICE_DIR = Path("/workspace/data/price_cache")
DATA_END = "2026-06-22"

KOLS = ["amitisinvesting", "StockSavvyShay", "Sam_Badawi"]
dir_data = json.load(open("/workspace/logs/p5_4kol_triage/direction_3kols_v2.json"))


# 修 date 字段
def fix_date(ca):
    try:
        return parsedate_to_datetime(ca).strftime("%Y-%m-%d")
    except Exception:
        return None


for h in KOLS:
    items = json.load(open(f"/workspace/logs/p5_4kol_triage/raw_{h}.json"))
    id_to_text = {it["id"]: (it.get("text") or it.get("fullText") or "") for it in items}
    id_to_created = {it["id"]: it.get("createdAt") for it in items}
    n_fixed = 0
    for j in dir_data[h]["judgments"]:
        sid = j.get("source_id")
        ca = id_to_created.get(sid)
        if ca:
            new_date = fix_date(ca)
            if new_date:
                j["date"] = new_date
                n_fixed += 1
    print(f"@{h}: 修 date 字段 {n_fixed} 条", flush=True)

# 存回 direction_3kols_v2.json (修过的版本)
json.dump(dir_data, open("/workspace/logs/p5_4kol_triage/direction_3kols_v3.json", "w"), indent=2, ensure_ascii=False)
print("\n💾 saved direction_3kols_v3.json", flush=True)


def find_price(bars, target):
    for b in bars:
        if b["date"] >= target:
            return b["c"], b["date"]
    return None, None


def load_bars(ticker):
    fp = PRICE_DIR / f"{ticker}_FULL_HISTORY.json"
    if fp.exists():
        return json.load(open(fp))
    return []


def verify_one(pred, benchmarks, horizon_days=90):
    ticker = pred.get("ticker")
    if not ticker:
        return {"resolved": False, "reason": "no_ticker"}

    entry_date = pred.get("date")
    if not entry_date:
        return {"resolved": False, "reason": "no_date"}
    # 校验格式
    try:
        datetime.strptime(entry_date, "%Y-%m-%d")
    except Exception:
        return {"resolved": False, "reason": "bad_date"}

    exit_date = (datetime.strptime(entry_date, "%Y-%m-%d") + timedelta(days=horizon_days)).strftime("%Y-%m-%d")
    exit_date_target = min(datetime.strptime(exit_date, "%Y-%m-%d"), datetime.strptime(DATA_END, "%Y-%m-%d")).strftime("%Y-%m-%d")

    bars = load_bars(ticker)
    if not bars:
        return {"resolved": False, "reason": f"no_bars_{ticker}"}

    e_px, _ = find_price(bars, entry_date)
    x_px, _ = find_price(bars, exit_date_target)
    if not e_px or not x_px:
        return {"resolved": False, "reason": f"no_px entry={entry_date} exit={exit_date_target}"}

    # 用 LLM 抽的 direction (不是 validator 的, 那个全是 neutral)
    direction = pred.get("llm_direction", pred.get("direction", "neutral"))
    if direction == "long":
        raw_ret = (x_px - e_px) / e_px * 100
    elif direction == "short":
        raw_ret = (e_px - x_px) / e_px * 100
    else:
        return {"resolved": False, "reason": "neutral"}

    excess = {}
    for bench_name, bench_bars in benchmarks.items():
        be, _ = find_price(bench_bars, entry_date)
        bx, _ = find_price(bench_bars, exit_date)
        if be and bx:
            bench_ret = (bx - be) / be * 100
            excess[bench_name] = {
                "excess_ret": raw_ret - bench_ret,
                "bench_ret": bench_ret,
                "raw_ret": raw_ret,
            }

    return {
        "resolved": True,
        "ticker": ticker,
        "direction": direction,
        "horizon_days": horizon_days,
        "entry_date": entry_date,
        "exit_date": exit_date_target,
        "entry_px": e_px,
        "exit_px": x_px,
        "raw_ret": raw_ret,
        "excess": excess,
        "is_raw_loss": raw_ret < 0,
        "reason": "ok",
        "thesis": pred.get("llm_thesis", ""),
        "evidence": pred.get("llm_evidence", ""),
    }


def raw_metrics(verified):
    if not verified:
        return {"n": 0, "hit_rate": 0, "med_raw": 0, "n_pos": 0, "n_neg": 0, "mean_raw": 0}
    n = len(verified)
    n_pos = sum(1 for v in verified if v["raw_ret"] > 0)
    n_neg = sum(1 for v in verified if v["raw_ret"] < 0)
    return {
        "n": n,
        "n_pos": n_pos,
        "n_neg": n_neg,
        "hit_rate": n_pos / n * 100,
        "med_raw": statistics.median([v["raw_ret"] for v in verified]),
        "mean_raw": sum(v["raw_ret"] for v in verified) / n,
    }


def excess_metrics(verified, bench):
    sub = [v for v in verified if bench in v["excess"]]
    if not sub:
        return {"n": 0, "med_excess": 0, "hit_rate": 0, "mean_excess": 0}
    n = len(sub)
    exs = [v["excess"][bench]["excess_ret"] for v in sub]
    hits = sum(1 for v in sub if v["excess"][bench]["excess_ret"] > 0)
    return {
        "n": n,
        "med_excess": statistics.median(exs),
        "mean_excess": sum(exs) / n,
        "hit_rate": hits / n * 100,
    }


def grade(rm):
    rate = rm["hit_rate"]
    n = rm["n"]
    if n < 3:
        return "D", f"n={n} < 3, 样本不足"
    if n < 5:
        if rate >= 60:
            return "C", f"raw_hit {rate:.1f}%, n={n} (样本小)"
        else:
            return "D", f"raw_hit {rate:.1f}%, n={n} (样本小 + 命中率低)"
    if n < 10:
        if rate >= 80:
            return "A", f"raw_hit {rate:.1f}%, n={n}"
        elif rate >= 70:
            return "B", f"raw_hit {rate:.1f}%, n={n}"
        elif rate >= 60:
            return "C", f"raw_hit {rate:.1f}%, n={n}"
        else:
            return "D", f"raw_hit {rate:.1f}%, n={n}"
    if rate >= 80:
        return "A+", f"raw_hit {rate:.1f}%, n={n}"
    elif rate >= 70:
        return "A", f"raw_hit {rate:.1f}%, n={n}"
    elif rate >= 60:
        return "B", f"raw_hit {rate:.1f}%, n={n}"
    elif rate >= 50:
        return "C", f"raw_hit {rate:.1f}%, n={n}"
    else:
        return "D", f"raw_hit {rate:.1f}%, n={n}"


def by_ticker_stats(verified, top_n=20):
    by_t = defaultdict(list)
    for v in verified:
        by_t[v["ticker"]].append(v)
    out = {}
    for t, lst in by_t.items():
        n = len(lst)
        n_hit = sum(1 for v in lst if v["raw_ret"] > 0)
        med_excess_soxx = statistics.median([
            v["excess"]["SOXX"]["excess_ret"] for v in lst if "SOXX" in v["excess"]
        ]) if any("SOXX" in v["excess"] for v in lst) else 0
        out[t] = {
            "n": n,
            "raw_hit_rate": n_hit / n * 100,
            "med_excess_soxx": med_excess_soxx,
            "med_raw": statistics.median([v["raw_ret"] for v in lst]),
        }
    return sorted(out.items(), key=lambda x: -x[1]["n"])[:top_n]


def verify_handle(handle):
    judgments = dir_data[handle]["judgments"]
    directional = [j for j in judgments if j.get("llm_direction") in ("long", "short")]
    print(f"  @{handle} LLM 抽完有方向: {len(directional)} / {len(judgments)}", flush=True)

    benchmarks = {
        "SPY": load_bars("SPY"),
        "SOXX": load_bars("SOXX"),
        "QQQ": load_bars("QQQ"),
    }

    verified = []
    unresolved = Counter()
    for j in directional:
        v = verify_one(j, benchmarks, 90)
        if v.get("resolved"):
            verified.append(v)
        else:
            unresolved[v.get("reason", "?")] += 1

    rm = raw_metrics(verified)
    em_spy = excess_metrics(verified, "SPY")
    em_soxx = excess_metrics(verified, "SOXX")
    em_qqq = excess_metrics(verified, "QQQ")
    by_t = by_ticker_stats(verified)
    grade_letter, grade_reason = grade(rm)

    n_pending = sum(1 for v in verified if v["entry_date"] > "2026-04-01")

    return {
        "handle": handle,
        "n_original": len(judgments),
        "n_directional": len(directional),
        "n_resolved": len(verified),
        "n_unresolved": dict(unresolved),
        "n_pending": n_pending,
        "raw_metrics": rm,
        "excess_metrics": {"SPY": em_spy, "SOXX": em_soxx, "QQQ": em_qqq},
        "by_ticker": by_t,
        "grade": (grade_letter, grade_reason),
        "verified": verified,
    }


def render_one(handle, r):
    n = r["n_resolved"]
    rm = r["raw_metrics"]
    em = r["excess_metrics"]

    lines = [
        f"## @{handle}",
        "",
        f"### 数据",
        "",
        f"- ORIGINAL 总判断: {r['n_original']}",
        f"- LLM 抽完有方向 (long/short): {r['n_directional']}",
        f"- 已验证 (90d 窗口, 数据截止 {DATA_END}): {n}",
        f"- Pending (entry > 2026-04-01, 90d 还没到期): {r['n_pending']}",
        f"- Unresolved: {r['n_unresolved']}",
        "",
        f"### 核心: raw 选股命中率 (不依赖基准)",
        "",
        f"- n_resolved: **{rm['n']}**",
        f"- raw 涨 (raw>0): **{rm['n_pos']}**",
        f"- raw 跌 (raw<0): {rm['n_neg']}",
        f"- **raw_hit_rate: {rm['hit_rate']:.1f}%**",
        f"- median_raw: **{rm['med_raw']:+.1f}%**",
        f"- mean_raw: {rm.get('mean_raw', 0):+.1f}%",
        "",
        f"### Excess vs Benchmarks",
        "",
        "| Bench | n | med_excess | mean_excess | hit_rate |",
        "|---|---|---|---|---|",
    ]
    for b, m in em.items():
        lines.append(f"| {b} | {m['n']} | {m['med_excess']:+.1f}% | {m.get('mean_excess', 0):+.1f}% | {m['hit_rate']:.1f}% |")
    lines.append("")

    g, g_reason = r["grade"]
    lines.extend([
        f"### 置信度: **{g}** ({g_reason})",
        "",
        f"### 能力圈 (ticker, n≥1 预测, 按 n 倒序)",
        "",
        "| ticker | n | raw_hit | med_raw | med_excess_soxx |",
        "|---|---|---|---|---|",
    ])
    for t, m in r["by_ticker"][:20]:
        lines.append(f"| {t} | {m['n']} | {m['raw_hit_rate']:.1f}% | {m['med_raw']:+.1f}% | {m['med_excess_soxx']:+.1f}% |")
    if not r["by_ticker"]:
        lines.append("| (无) | | | | |")
    lines.append("")

    rw = sorted([v for v in r["verified"] if v["raw_ret"] > 0], key=lambda x: -x["raw_ret"])
    rl = sorted([v for v in r["verified"] if v["raw_ret"] < 0], key=lambda x: x["raw_ret"])
    ew = sorted(r["verified"], key=lambda x: -x["excess"].get("SOXX", {}).get("excess_ret", 0))
    el = sorted(r["verified"], key=lambda x: x["excess"].get("SOXX", {}).get("excess_ret", 0))

    lines.extend([
        f"### 4 分类",
        "",
        f"#### 4.1 raw 真赢 ({len(rw)} 条, 按 raw 倒序)",
        "",
        "| ticker | dir | entry → exit | raw | excess_spy | excess_soxx |",
        "|---|---|---|---|---|---|",
    ])
    for v in rw[:20]:
        ex_spy = v["excess"].get("SPY", {}).get("excess_ret", 0)
        ex_soxx = v["excess"].get("SOXX", {}).get("excess_ret", 0)
        lines.append(f"| {v['ticker']} | {v['direction']} | {v['entry_date']} → {v['exit_date']} | {v['raw_ret']:+.1f}% | {ex_spy:+.1f}% | {ex_soxx:+.1f}% |")
    lines.append("")

    lines.extend([
        f"#### 4.2 raw 真输 ({len(rl)} 条, 按 raw 升序)",
        "",
        "| ticker | dir | entry → exit | raw | excess_spy | excess_soxx |",
        "|---|---|---|---|---|---|",
    ])
    for v in rl[:20]:
        ex_spy = v["excess"].get("SPY", {}).get("excess_ret", 0)
        ex_soxx = v["excess"].get("SOXX", {}).get("excess_ret", 0)
        lines.append(f"| {v['ticker']} | {v['direction']} | {v['entry_date']} → {v['exit_date']} | {v['raw_ret']:+.1f}% | {ex_spy:+.1f}% | {ex_soxx:+.1f}% |")
    lines.append("")

    lines.extend([
        f"#### 4.3 跑赢 SOXX (按 excess_soxx 倒序)",
        "",
        "| ticker | dir | entry → exit | raw | excess_soxx |",
        "|---|---|---|---|---|",
    ])
    for v in ew[:10]:
        ex_soxx = v["excess"].get("SOXX", {}).get("excess_ret", 0)
        lines.append(f"| {v['ticker']} | {v['direction']} | {v['entry_date']} → {v['exit_date']} | {v['raw_ret']:+.1f}% | {ex_soxx:+.1f}% |")
    lines.append("")

    lines.extend([
        f"#### 4.4 跑输 SOXX (按 excess_soxx 升序)",
        "",
        "| ticker | dir | entry → exit | raw | excess_soxx |",
        "|---|---|---|---|---|",
    ])
    for v in el[:10]:
        ex_soxx = v["excess"].get("SOXX", {}).get("excess_ret", 0)
        lines.append(f"| {v['ticker']} | {v['direction']} | {v['entry_date']} → {v['exit_date']} | {v['raw_ret']:+.1f}% | {ex_soxx:+.1f}% |")
    lines.append("")

    lines.extend([
        f"### 全部 {n} 条已验证 (逐条, 给你对照看)",
        "",
        "| # | entry | exit | ticker | dir | raw | exc_spy | exc_soxx | exc_qqq | thesis |",
        "|---|---|---|---|---|---|---|---|---|---|",
    ])
    for i, v in enumerate(r["verified"], 1):
        ex_spy = v["excess"].get("SPY", {}).get("excess_ret", 0)
        ex_soxx = v["excess"].get("SOXX", {}).get("excess_ret", 0)
        ex_qqq = v["excess"].get("QQQ", {}).get("excess_ret", 0)
        th = (v.get("thesis") or "")[:60].replace("|", "/")
        lines.append(f"| {i} | {v['entry_date']} | {v['exit_date']} | {v['ticker']} | {v['direction']} | {v['raw_ret']:+.1f}% | {ex_spy:+.1f}% | {ex_soxx:+.1f}% | {ex_qqq:+.1f}% | {th} |")
    lines.append("")

    return "\n".join(lines)


def main():
    import time as _t
    t0 = _t.time()
    print(f"[{_t.time()-t0:.0f}s] 3 KOL 完整胜率验证 (v3, 修日期解析)", flush=True)

    lines = [
        "# 3 KOL 完整胜率验证 (P5-9 v3 — 修日期解析)",
        "",
        f"**生成时间**: {_t.strftime('%Y-%m-%d %H:%M')}",
        f"**过滤链**: ORIGINAL → LLM 抽 direction → keep long/short → 90d 验证",
        f"**数据截止**: {DATA_END}  ",
        f"**默认 horizon**: 90d  ",
        f"**基准**: SPY / SOXX / QQQ",
        f"**已淘汰**: @TradexWhisperer (简介自吹 vs 实际不符)",
        "",
        "**纪律**: 不下'可不可跟'结论, 三人一起给, 等你对照看 (尤其会拿市场常识查可疑数字).",
        "",
    ]

    all_results = {}
    for h in KOLS:
        print(f"\n[{_t.time()-t0:.0f}s] 验证 @{h}...", flush=True)
        r = verify_handle(h)
        all_results[h] = r
        rm = r["raw_metrics"]
        print(f"  directional={r['n_directional']} resolved={r['n_resolved']} raw_hit={rm['hit_rate']:.1f}% med_raw={rm['med_raw']:+.1f}% pending={r['n_pending']}", flush=True)

    for h in KOLS:
        r = all_results[h]
        lines.append("---")
        lines.append("")
        lines.append(render_one(h, r))

    lines.extend([
        "---",
        "",
        "## 三人对照表 (事实数字, 你自己下判断)",
        "",
        "| KOL | n_orig | n_dir | n_resolved | pending | raw_hit | med_raw | vs SPY | vs SOXX | vs QQQ | 置信度 |",
        "|---|---|---|---|---|---|---|---|---|---|---|",
    ])
    for h in KOLS:
        r = all_results[h]
        rm = r["raw_metrics"]
        em = r["excess_metrics"]
        g, g_r = r["grade"]
        lines.append(
            f"| @{h} | {r['n_original']} | {r['n_directional']} | {r['n_resolved']} | {r['n_pending']} | "
            f"{rm['hit_rate']:.1f}% | {rm['med_raw']:+.1f}% | "
            f"{em['SPY']['med_excess']:+.1f}% | {em['SOXX']['med_excess']:+.1f}% | {em['QQQ']['med_excess']:+.1f}% | **{g}** |"
        )
    lines.append("")

    lines.extend([
        "## 备注 / 已知坑",
        "",
        f"- LLM 抽 direction 用 deepseek-v4-pro, max_tokens 800, 25-30 worker 并发",
        f"- 剩 6 条 (3+2+1) 真的抽不动 (LLM 多次返空), 标 '?', 不算入统计",
        f"- **修日期解析 bug**: 之前用 `createdAt[:10]` 拿 'Sun Apr 12', 实际是 'Sun Apr 12 01:41:11 +0000 2026' = 2026-04-12. 改用 email.utils.parsedate_to_datetime",
        f"- 4 候选全部 US (Polygon 可验), 100% 美股",
        f"- 拉取时间窗: Apify `from:handle` 模式跨 1-2 年 (最新 2 月爆 50-60%, 旧月份散落 1-5 条)",
        f"- 暂不下'可不可跟'结论 — 你自己对照看 (尤其会拿市场常识查可疑数字)",
        "",
    ])

    out = Path("/workspace/outputs/p5_verify_3kol.md")
    out.write_text("\n".join(lines))
    print(f"\n[{_t.time()-t0:.0f}s] 📄 {out}", flush=True)

    json_out = Path("/workspace/logs/p5_4kol_triage/verify_3kol_v3.json")
    json.dump(all_results, open(json_out, "w"), indent=2, ensure_ascii=False, default=str)
    print(f"[{_t.time()-t0:.0f}s] 📄 {json_out}", flush=True)
    print(f"[{_t.time()-t0:.0f}s] ⏱️  总耗时: {_t.time()-t0:.1f}s", flush=True)


if __name__ == "__main__":
    main()