"""3 KOL 完整胜率验证 (amitisinvesting / StockSavvyShay / Sam_Badawi)

严格按用户规则:
- 用 attribution_results.json 的 ORIGINAL only (剔除 news/RELAYED)
- raw 选股命中率 + vs SPY/SOXX 超额
- 能力圈 (哪些标的/板块准)
- 不下"可不可跟"结论
- Sam_Badawi 标 pending 比例 (1 个月数据)
- 三人一起给, 不下结论

时间窗: 各自的数据时间窗 (maxItems=1000 限制)
验证窗口: 默认 90d (可调整)
基准: SPY, SOXX (半导体 ETF)
"""
import json
import os
import re
import statistics
from collections import Counter, defaultdict
from datetime import datetime, timedelta
from pathlib import Path

PRICE_DIR = Path("/workspace/data/price_cache")
DATA_END = "2026-06-22"

KOLS = [
    ("amitisinvesting", 156),
    ("StockSavvyShay", 333),
    ("Sam_Badawi", 107),
]

ATTRIBUTION_RESULTS = json.load(open("/workspace/logs/p5_4kol_triage/attribution_results.json"))


def find_price(bars, target):
    for b in bars:
        if b["date"] >= target:
            return b["c"], b["date"]
    return None, None


def parse_signal_date(s):
    if not s:
        return None
    try:
        d = datetime.strptime(s, "%Y-%m-%d")
        while d.weekday() >= 5:
            d += timedelta(days=1)
        return d.strftime("%Y-%m-%d")
    except Exception:
        return None


def load_bars(ticker):
    fp = PRICE_DIR / f"{ticker}_FULL_HISTORY.json"
    if fp.exists():
        return json.load(open(fp))
    return []


def verify_one(pred, benchmarks, horizon_days=90):
    """验证单条预测."""
    ticker = pred.get("ticker")
    if not ticker:
        return {"resolved": False, "reason": "no_ticker"}

    entry_date = parse_signal_date(pred.get("date"))
    if not entry_date:
        return {"resolved": False, "reason": "bad_date"}

    exit_date = (datetime.strptime(entry_date, "%Y-%m-%d") + timedelta(days=horizon_days)).strftime("%Y-%m-%d")
    exit_date = min(exit_date, DATA_END)  # 数据截止

    bars = load_bars(ticker)
    if not bars:
        return {"resolved": False, "reason": f"no_bars_{ticker}"}

    e_px, _ = find_price(bars, entry_date)
    x_px, _ = find_price(bars, exit_date)
    if not e_px or not x_px:
        return {"resolved": False, "reason": "no_px"}

    # raw
    if pred["direction"] == "long":
        raw_ret = (x_px - e_px) / e_px * 100
    elif pred["direction"] == "short":
        raw_ret = (e_px - x_px) / e_px * 100
    else:
        return {"resolved": False, "reason": "neutral"}

    # excess vs benchmarks
    excess = {}
    for bench_name, bench_bars in benchmarks.items():
        be, _ = find_price(bench_bars, entry_date)
        bx, _ = find_price(bench_bars, exit_date)
        if be and bx:
            bench_ret = (bx - be) / be * 100
            excess[bench_name] = raw_ret - bench_ret

    return {
        "resolved": True,
        "ticker": ticker,
        "direction": pred["direction"],
        "horizon_days": horizon_days,
        "entry_date": entry_date,
        "exit_date": exit_date,
        "entry_px": e_px,
        "exit_px": x_px,
        "raw_ret": raw_ret,
        "excess": excess,
        "is_raw_loss": raw_ret < 0,
        "reason": "ok",
    }


def categorize(verified):
    """4 分类."""
    rw = sorted([v for v in verified if v["raw_ret"] > 0], key=lambda x: -x["raw_ret"])
    rl = sorted([v for v in verified if v["raw_ret"] < 0], key=lambda x: x["raw_ret"])
    ew = sorted(verified, key=lambda x: -x["excess"].get("SOXX", {}).get("excess_ret", 0))
    el = sorted(verified, key=lambda x: x["excess"].get("SOXX", {}).get("excess_ret", 0))
    return {"raw_win": rw, "raw_loss": rl, "excess_win": ew, "excess_loss": el}


def raw_metrics(verified):
    if not verified:
        return {"n": 0, "hit_rate": 0, "med_raw": 0}
    n = len(verified)
    n_pos = sum(1 for v in verified if v["raw_ret"] > 0)
    return {
        "n": n,
        "n_pos": n_pos,
        "n_neg": sum(1 for v in verified if v["raw_ret"] < 0),
        "hit_rate": n_pos / n * 100,
        "med_raw": statistics.median([v["raw_ret"] for v in verified]),
    }


def excess_metrics(verified, bench):
    sub = [v for v in verified if bench in v["excess"]]
    if not sub:
        return {"n": 0, "med_excess": 0, "hit_rate": 0}
    n = len(sub)
    exs = [v["excess"][bench]["excess_ret"] for v in sub]
    hits = sum(1 for v in sub if (v["direction"] == "long" and v["excess"][bench]["excess_ret"] > 0) or
                                     (v["direction"] == "short" and v["excess"][bench]["excess_ret"] < 0))
    return {
        "n": n,
        "med_excess": statistics.median(exs),
        "hit_rate": hits / n * 100,
    }


def grade(raw_m, n_total, n_unresolved, pending_pct):
    """置信度分级 (P5 固化的 5 级)."""
    rate = raw_m["hit_rate"]
    n_resolved = raw_m["n"]
    if n_resolved < 3:
        return "D", f"resolved {n_resolved} < 3 (待验证样本不足)"
    elif n_resolved < 5:
        return "C", f"resolved {n_resolved} 较小, raw_hit {rate:.1f}%"
    elif n_resolved < 10:
        if rate >= 70:
            return "B", f"raw_hit {rate:.1f}%, n={n_resolved}"
        elif rate >= 60:
            return "C", f"raw_hit {rate:.1f}%, n={n_resolved}"
        else:
            return "D", f"raw_hit {rate:.1f}%, n={n_resolved}, 较弱"
    else:  # n >= 10
        if rate >= 80:
            return "A", f"raw_hit {rate:.1f}%, n={n_resolved}"
        elif rate >= 70:
            return "A", f"raw_hit {rate:.1f}%, n={n_resolved}"
        elif rate >= 60:
            return "B", f"raw_hit {rate:.1f}%, n={n_resolved}"
        elif rate >= 50:
            return "C", f"raw_hit {rate:.1f}%, n={n_resolved}"
        else:
            return "D", f"raw_hit {rate:.1f}%, n={n_resolved}, 不显著"


def by_ticker_stats(verified, top_n=10):
    """能力圈: 按 ticker 统计 (≥3 预测)."""
    by_t = defaultdict(list)
    for v in verified:
        by_t[v["ticker"]].append(v)
    out = {}
    for t, lst in by_t.items():
        n = len(lst)
        if n < 3:
            continue
        n_hit = sum(1 for v in lst if v["raw_ret"] > 0)
        med_excess = statistics.median([
            v["excess"].get("SOXX", {}).get("excess_ret", 0)
            for v in lst if "SOXX" in v["excess"]
        ]) if any("SOXX" in v["excess"] for v in lst) else 0
        out[t] = {
            "n": n,
            "raw_hit_rate": n_hit / n * 100,
            "med_excess_soxx": med_excess,
        }
    return sorted(out.items(), key=lambda x: -x[1]["n"])[:top_n]


def verify_handle(handle):
    judgments = ATTRIBUTION_RESULTS[handle]["judgments"]
    original_judgments = [j for j in judgments if j.get("attribution") == "ORIGINAL"]

    benchmarks = {
        "SPY": load_bars("SPY"),
        "SOXX": load_bars("SOXX"),
        "QQQ": load_bars("QQQ"),
    }

    horizon = 90  # 默认 90 天窗口

    verified = []
    unresolved = Counter()
    for j in original_judgments:
        v = verify_one(j, benchmarks, horizon)
        if v.get("resolved"):
            verified.append(v)
        else:
            unresolved[v.get("reason", "?")] += 1

    rm = raw_metrics(verified)
    em_spy = excess_metrics(verified, "SPY")
    em_soxx = excess_metrics(verified, "SOXX")
    em_qqq = excess_metrics(verified, "QQQ")
    cat = categorize(verified)
    by_ticker = by_ticker_stats(verified)

    n_total_original = len(original_judgments)
    n_pending = sum(1 for v in verified if v["entry_date"] > "2026-04-01")  # 3 月后 entry, 90d 还没到
    pending_pct = n_pending / max(n_total_original, 1) * 100

    grade_letter, grade_reason = grade(rm, n_total_original, unresolved, pending_pct)

    return {
        "handle": handle,
        "n_original": n_total_original,
        "n_resolved": len(verified),
        "n_unresolved": dict(unresolved),
        "n_pending": n_pending,
        "pending_pct": pending_pct,
        "raw_metrics": rm,
        "excess_metrics": {"SPY": em_spy, "SOXX": em_soxx, "QQQ": em_qqq},
        "categorized": cat,
        "by_ticker": by_ticker,
        "grade": (grade_letter, grade_reason),
        "verified": verified,
        "all_judgments": original_judgments,
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
        f"- 已验证: {n}",
        f"- 未验证: {r['n_unresolved']}",
        f"- **Pending 比例**: {r['n_pending']} / {r['n_original']} = **{r['pending_pct']:.1f}%** (entry > 2026-04-01, 90d 窗口未到期)",
        "",
        f"### 核心: raw 选股命中率 (不依赖基准)",
        "",
        f"- n_resolved: **{rm['n']}**",
        f"- raw 涨 (raw>0): **{rm['n_pos']}**",
        f"- raw 跌 (raw<0): {rm['n_neg']}",
        f"- **raw_hit_rate: {rm['hit_rate']:.1f}%**",
        f"- median_raw: **{rm['med_raw']:+.1f}%**",
        "",
        f"### Excess vs Benchmarks",
        "",
        "| Bench | n | med_excess | hit_rate |",
        "|---|---|---|---|",
    ]
    for b, m in em.items():
        lines.append(f"| {b} | {m['n']} | {m['med_excess']:+.1f}% | {m['hit_rate']:.1f}% |")
    lines.append("")

    # 能力圈
    lines.extend([
        "### 能力圈 (ticker ≥3 预测)",
        "",
        "| ticker | n | raw_hit | med_excess_soxx |",
        "|---|---|---|---|",
    ])
    for t, m in r["by_ticker"][:15]:
        lines.append(f"| {t} | {m['n']} | {m['raw_hit_rate']:.1f}% | {m['med_excess_soxx']:+.1f}% |")
    if not r["by_ticker"]:
        lines.append("| (无 ≥3 预测的 ticker) | | | |")
    lines.append("")

    # 4 分类
    cat = r["categorized"]
    lines.extend([
        "### 4 分类 (按 raw / excess 分开)",
        "",
        f"#### 4.1 raw 真赢 ({len(cat['raw_win'])} 条)",
        "",
        "| ticker | direction | horizon | raw | excess_soxx |",
        "|---|---|---|---|---|",
    ])
    for v in cat["raw_win"][:10]:
        ex = v["excess"].get("SOXX", {}).get("excess_ret", 0)
        lines.append(f"| {v['ticker']} | {v['direction']} | {v['horizon_days']}d | {v['raw_ret']:+.1f}% | {ex:+.1f}% |")
    lines.append("")

    lines.extend([
        f"#### 4.2 raw 真输 ({len(cat['raw_loss'])} 条)",
        "",
        "| ticker | direction | horizon | raw | excess_soxx |",
        "|---|---|---|---|---|",
    ])
    for v in cat["raw_loss"][:10]:
        ex = v["excess"].get("SOXX", {}).get("excess_ret", 0)
        lines.append(f"| {v['ticker']} | {v['direction']} | {v['horizon_days']}d | {v['raw_ret']:+.1f}% | {ex:+.1f}% |")
    lines.append("")

    # 全部逐条 (让用户对着看)
    lines.extend([
        f"### 全部 {n} 条已验证逐条 (你对照看)",
        "",
        "| # | entry | exit | ticker | direction | raw | excess_spy | excess_soxx | excess_qqq |",
        "|---|---|---|---|---|---|---|---|---|",
    ])
    for i, v in enumerate(r["verified"], 1):
        ex_spy = v["excess"].get("SPY", {}).get("excess_ret", 0)
        ex_soxx = v["excess"].get("SOXX", {}).get("excess_ret", 0)
        ex_qqq = v["excess"].get("QQQ", {}).get("excess_ret", 0)
        lines.append(f"| {i} | {v['entry_date']} | {v['exit_date']} | {v['ticker']} | {v['direction']} | {v['raw_ret']:+.1f}% | {ex_spy:+.1f}% | {ex_soxx:+.1f}% | {ex_qqq:+.1f}% |")
    lines.append("")

    # 注意: 我不下"可不可跟"结论
    lines.extend([
        "### 备注",
        "",
        f"- 数据截止: {DATA_END}",
        f"- 默认 horizon: 90d (entry + 90d → exit, 受数据截止限制)",
        f"- ⚠️ 暂不下'可不可跟'结论 — 你看完 3 人一起核对",
        "",
    ])
    return "\n".join(lines)


def main():
    import time as _t
    t0 = _t.time()
    print(f"[{_t.time()-t0:.0f}s] 3 KOL 完整胜率验证 (ORIGINAL only, 90d horizon)", flush=True)

    lines = [
        "# 3 KOL 完整胜率验证 (P5-9)",
        "",
        f"**生成时间**: {_t.strftime('%Y-%m-%d %H:%M')}  ",
        f"**过滤**: attribution = ORIGINAL only (剔除 news/RELAYED/commentary)",
        f"**Horizon**: 90d 默认 (entry+90d → exit, 数据截止 2026-06-22)",
        f"**基准**: SPY / SOXX / QQQ",
        f"**已淘汰**: @TradexWhisperer (简介自吹 vs 实际不符)",
        "",
        "**纪律**: 不下'可不可跟'结论, 三人一起给, 等你对照看.",
        "",
    ]

    all_results = {}
    for handle, _ in KOLS:
        print(f"\n[{_t.time()-t0:.0f}s] 验证 @{handle}...", flush=True)
        r = verify_handle(handle)
        all_results[handle] = r
        print(f"  n_original={r['n_original']} n_resolved={r['n_resolved']} n_pending={r['n_pending']} raw_hit={r['raw_metrics']['hit_rate']:.1f}%", flush=True)

    # 输出
    for handle, _ in KOLS:
        r = all_results[handle]
        lines.append("---")
        lines.append("")
        lines.append(render_one(handle, r))

    # 整体对照表 (不放"可不可跟"判断, 只放事实数字)
    lines.extend([
        "---",
        "",
        "## 三人对照表 (事实数字, 你自己看)",
        "",
        "| KOL | n_orig | n_resolved | pending% | raw_hit | med_raw | vs SPY med | vs SOXX med | vs QQQ med |",
        "|---|---|---|---|---|---|---|---|---|",
    ])
    for handle, _ in KOLS:
        r = all_results[handle]
        rm = r["raw_metrics"]
        em = r["excess_metrics"]
        lines.append(
            f"| @{handle} | {r['n_original']} | {r['n_resolved']} | {r['pending_pct']:.0f}% | "
            f"{rm['hit_rate']:.1f}% | {rm['med_raw']:+.1f}% | "
            f"{em['SPY']['med_excess']:+.1f}% | {em['SOXX']['med_excess']:+.1f}% | {em['QQQ']['med_excess']:+.1f}% |"
        )
    lines.append("")

    out = Path("/workspace/outputs/p5_verify_3kol.md")
    out.write_text("\n".join(lines))
    print(f"\n[{_t.time()-t0:.0f}s] 📄 {out}", flush=True)

    # 保存 JSON
    json_out = Path("/workspace/logs/p5_4kol_triage/verify_3kol.json")
    json.dump({
        h: {**r, "verified": r["verified"]}  # include full
        for h, r in all_results.items()
    }, open(json_out, "w"), indent=2, ensure_ascii=False, default=str)
    print(f"[{_t.time()-t0:.0f}s] 📄 {json_out}", flush=True)
    print(f"[{_t.time()-t0:.0f}s] ⏱️  总耗时: {_t.time()-t0:.1f}s", flush=True)


if __name__ == "__main__":
    main()