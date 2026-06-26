"""3 KOL 完整胜率验证 v6
- 用 direction_3kols_v4.json (修对方向)
- 严格分 resolved/pending
- 小样本明示
- 跟 Jukan 对照 (重点不是命中率, 是已到期判断里选对选最弱)
"""
import json
import statistics
from collections import Counter, defaultdict
from datetime import datetime, timedelta
from pathlib import Path

PRICE_DIR = Path("/workspace/data/price_cache")
DATA_END = "2026-06-22"
HORIZON_DAYS = 90

KOLS = ["amitisinvesting", "StockSavvyShay", "Sam_Badawi"]
dir_data = json.load(open("/workspace/logs/p5_4kol_triage/direction_3kols_v4.json"))


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


def verify_one(pred, benchmarks):
    ticker = pred.get("ticker")
    if not ticker:
        return {"resolved": False, "reason": "no_ticker"}

    entry_date = pred.get("date")
    if not entry_date:
        return {"resolved": False, "reason": "no_date"}

    # 检查 entry_date 是否还在 Polygon cache 内
    bars = load_bars(ticker)
    if not bars:
        return {"resolved": False, "reason": f"no_bars_{ticker}"}

    e_px, _ = find_price(bars, entry_date)
    if not e_px:
        return {"resolved": False, "reason": f"entry_no_px ({entry_date})"}

    # 计算 exit_date (entry + 90d)
    exit_date_target = (datetime.strptime(entry_date, "%Y-%m-%d") + timedelta(days=HORIZON_DAYS)).strftime("%Y-%m-%d")
    exit_date_actual = min(datetime.strptime(exit_date_target, "%Y-%m-%d"), datetime.strptime(DATA_END, "%Y-%m-%d")).strftime("%Y-%m-%d")
    x_px, _ = find_price(bars, exit_date_actual)
    if not x_px:
        return {"resolved": False, "reason": f"exit_no_px ({exit_date_actual})"}

    direction = pred.get("llm_direction", "neutral")
    if direction == "long":
        raw_ret = (x_px - e_px) / e_px * 100
    elif direction == "short":
        raw_ret = (e_px - x_px) / e_px * 100
    else:
        return {"resolved": False, "reason": "neutral"}

    # 计算 pending vs resolved
    # resolved = exit_date_actual == exit_date_target (即 90d 完整到期)
    # pending = exit_date_actual < exit_date_target (即被数据截止截断)
    if exit_date_actual == exit_date_target:
        status = "resolved"
    else:
        status = "pending"

    excess = {}
    for bench_name, bench_bars in benchmarks.items():
        be, _ = find_price(bench_bars, entry_date)
        bx, _ = find_price(bench_bars, exit_date_actual)
        if be and bx:
            bench_ret = (bx - be) / be * 100
            excess[bench_name] = {
                "excess_ret": raw_ret - bench_ret,
                "bench_ret": bench_ret,
                "raw_ret": raw_ret,
            }

    return {
        "resolved": True,
        "status": status,
        "ticker": ticker,
        "direction": direction,
        "horizon_days": HORIZON_DAYS,
        "entry_date": entry_date,
        "exit_date_target": exit_date_target,
        "exit_date_actual": exit_date_actual,
        "entry_px": e_px,
        "exit_px": x_px,
        "raw_ret": raw_ret,
        "excess": excess,
        "is_raw_loss": raw_ret < 0,
        "thesis": pred.get("llm_thesis", ""),
    }


def raw_metrics(verified_list):
    if not verified_list:
        return {"n": 0, "hit_rate": 0, "med_raw": 0, "n_pos": 0, "n_neg": 0}
    n = len(verified_list)
    n_pos = sum(1 for v in verified_list if v["raw_ret"] > 0)
    n_neg = sum(1 for v in verified_list if v["raw_ret"] < 0)
    return {
        "n": n,
        "n_pos": n_pos,
        "n_neg": n_neg,
        "hit_rate": n_pos / n * 100 if n > 0 else 0,
        "med_raw": statistics.median([v["raw_ret"] for v in verified_list]) if verified_list else 0,
    }


def excess_metrics(verified_list, bench):
    sub = [v for v in verified_list if bench in v["excess"]]
    if not sub:
        return {"n": 0, "med_excess": 0, "hit_rate": 0}
    n = len(sub)
    exs = [v["excess"][bench]["excess_ret"] for v in sub]
    hits = sum(1 for v in sub if v["excess"][bench]["excess_ret"] > 0)
    return {
        "n": n,
        "med_excess": statistics.median(exs),
        "hit_rate": hits / n * 100 if n > 0 else 0,
    }


def verify_handle(handle):
    judgments = dir_data[handle]["judgments"]
    directional = [j for j in judgments if j.get("llm_direction") in ("long", "short")]
    print(f"  @{handle}: directional={len(directional)}")

    benchmarks = {
        "SPY": load_bars("SPY"),
        "SOXX": load_bars("SOXX"),
        "QQQ": load_bars("QQQ"),
    }

    resolved = []
    pending = []
    unresolved = Counter()
    for j in directional:
        v = verify_one(j, benchmarks)
        if not v.get("resolved"):
            unresolved[v.get("reason", "?")] += 1
        elif v.get("status") == "pending":
            pending.append(v)
        else:
            resolved.append(v)

    rm_res = raw_metrics(resolved)
    rm_pend = raw_metrics(pending)
    rm_all = raw_metrics(resolved + pending)

    em_spy = excess_metrics(resolved + pending, "SPY")
    em_soxx = excess_metrics(resolved + pending, "SOXX")
    em_qqq = excess_metrics(resolved + pending, "QQQ")

    return {
        "handle": handle,
        "n_directional": len(directional),
        "n_resolved": len(resolved),
        "n_pending": len(pending),
        "n_unresolved": dict(unresolved),
        "resolved": resolved,
        "pending": pending,
        "rm_resolved": rm_res,
        "rm_pending": rm_pend,
        "rm_all": rm_all,
        "em_spy": em_spy,
        "em_soxx": em_soxx,
        "em_qqq": em_qqq,
    }


def render_one(r):
    h = r["handle"]
    rm_r = r["rm_resolved"]
    rm_p = r["rm_pending"]
    rm_a = r["rm_all"]
    em_spy = r["em_spy"]
    em_soxx = r["em_soxx"]

    lines = [
        f"## @{h}",
        "",
        f"### 数据规模",
        "",
        f"- directional (LLM 抽完 long/short): **{r['n_directional']}**",
        f"- 已到期 (resolved, 90d 完整): **{r['n_resolved']}**",
        f"- 未到期 (pending, entry 在 2026-03-23 之后): **{r['n_pending']}**",
        f"- unresolved: {r['n_unresolved']}",
        "",
    ]

    # 已到期核心指标
    lines.extend([
        f"### 已到期 {r['n_resolved']} 条 — 严格分 resolved/pending",
        "",
    ])
    if r["n_resolved"] < 5:
        lines.extend([
            f"⚠️ **样本严重不足 (resolved={r['n_resolved']})**, 无法得出有意义的命中率结论",
            f"  - raw_hit_rate: **{rm_r['hit_rate']:.1f}%** ({rm_r['n_pos']}/{rm_r['n']})",
            f"  - med_raw: **{rm_r['med_raw']:+.1f}%**",
            "",
            f"### Pending {r['n_pending']} 条 (entry 还没到 90d, 不算)",
            "",
            f"- 这些只是参考, 不能算'命中' (时间还没到)",
            f"- med_raw (含 pending): {rm_a['med_raw']:+.1f}%",
            "",
        ])
    else:
        lines.extend([
            f"raw_hit_rate: **{rm_r['hit_rate']:.1f}%** ({rm_r['n_pos']}/{rm_r['n']})",
            f"med_raw: **{rm_r['med_raw']:+.1f}%**",
            "",
        ])

    # Excess
    lines.extend([
        f"### Excess (resolved + pending 合计, n={em_spy['n']})",
        "",
        "| Bench | n | med_excess | hit_rate |",
        "|---|---|---|---|",
        f"| SPY | {em_spy['n']} | {em_spy['med_excess']:+.1f}% | {em_spy['hit_rate']:.1f}% |",
        f"| SOXX | {em_soxx['n']} | {em_soxx['med_excess']:+.1f}% | {em_soxx['hit_rate']:.1f}% |",
        f"| QQQ | {r['em_qqq']['n']} | {r['em_qqq']['med_excess']:+.1f}% | {r['em_qqq']['hit_rate']:.1f}% |",
        "",
    ])

    # 选对选最弱分析 — 仅 resolved
    lines.append(f"### 已到期 {r['n_resolved']} 条逐条 (raw + excess_soxx, 不混)")
    lines.append("")
    if r["n_resolved"] == 0:
        lines.append("  (无已到期判断)")
    else:
        lines.append("| # | entry → exit | ticker | dir | raw | excess_spy | excess_soxx |")
        lines.append("|---|---|---|---|---|---|---|")
        for i, v in enumerate(r["resolved"], 1):
            ex_spy = v["excess"].get("SPY", {}).get("excess_ret", 0)
            ex_soxx = v["excess"].get("SOXX", {}).get("excess_ret", 0)
            lines.append(f"| {i} | {v['entry_date']} → {v['exit_date_target']} | {v['ticker']} | {v['direction']} | {v['raw_ret']:+.1f}% | {ex_spy:+.1f}% | {ex_soxx:+.1f}% |")
    lines.append("")

    # Pending 列
    lines.append(f"### Pending {r['n_pending']} 条逐条 (不算命中, 仅参考)")
    lines.append("")
    if r["n_pending"] == 0:
        lines.append("  (无)")
    else:
        lines.append("| entry → 截止 | ticker | dir | raw |")
        lines.append("|---|---|---|---|")
        for v in r["pending"][:30]:
            lines.append(f"| {v['entry_date']} → {v['exit_date_actual']} | {v['ticker']} | {v['direction']} | {v['raw_ret']:+.1f}% |")
        if len(r["pending"]) > 30:
            lines.append(f"| ... 还有 {len(r['pending'])-30} 条 | | | |")
    lines.append("")

    return "\n".join(lines)


def main():
    import time as _t
    t0 = _t.time()
    print(f"[{_t.time()-t0:.0f}s] 3 KOL verify v6 (修对方向 + 严格分 resolved/pending)", flush=True)

    lines = [
        "# 3 KOL 胜率验证 (P5-9 v6 — 修方向 + 严格分 resolved/pending)",
        "",
        "**生成时间**: " + _t.strftime("%Y-%m-%d %H:%M"),
        f"**Horizon**: {HORIZON_DAYS}d  ",
        f"**数据截止**: {DATA_END}",
        f"**已淘汰**: @TradexWhisperer (简介自吹 vs 实际不符)",
        "",
        "**P5 短期修正** (5 条 short 全是误抽):",
        "- amitis HOOD 2026-05-19: short → long (作者说 long term intact)",
        "- amitis MU 2026-05-11: short → neutral (fomo warning, 不是方向)",
        "- amitis IREN 2026-05-07: short → neutral (commentary 回复)",
        "- Sam NBIS 2026-06-17: short → neutral (事件预测, 不是建仓)",
        "- Sam SNAP 2026-06-16: short → neutral (讽刺/搞笑)",
        "",
        "**Jukan 对照基准**: raw_hit 96.3% (his 27 条) / +29.6% med_raw / +27pp vs SOXX",
        "",
        "---",
        "",
    ]

    all_results = {}
    for h in KOLS:
        print(f"\n[{_t.time()-t0:.0f}s] 验证 @{h}...", flush=True)
        r = verify_handle(h)
        all_results[h] = r
        print(f"  resolved={r['n_resolved']} pending={r['n_pending']} unresolved={r['n_unresolved']}", flush=True)

    # 输出每个人
    for h in KOLS:
        r = all_results[h]
        lines.append(render_one(r))
        lines.append("---")
        lines.append("")

    # 对照表
    lines.extend([
        "## 三人对照表 (事实数字)",
        "",
        "| KOL | directional | **resolved** | pending | unresolved | raw_hit (resolved only) | med_raw (resolved) | med_excess_soxx |",
        "|---|---|---|---|---|---|---|---|",
    ])
    for h in KOLS:
        r = all_results[h]
        rm_r = r["rm_resolved"]
        em_soxx = r["em_soxx"]
        # unresolved sum
        n_unres = sum(r["n_unresolved"].values())
        lines.append(
            f"| @{h} | {r['n_directional']} | **{r['n_resolved']}** | {r['n_pending']} | {n_unres} | "
            f"**{rm_r['hit_rate']:.1f}%** ({rm_r['n_pos']}/{rm_r['n']}) | {rm_r['med_raw']:+.1f}% | {em_soxx['med_excess']:+.1f}% |"
        )
    lines.append("")

    lines.extend([
        "## Jukan 对照基准",
        "",
        "| | n_resolved | raw_hit | med_raw | med_excess_soxx |",
        "|---|---|---|---|---|",
        "| **Jukan his (P4-19 v4)** | **27** | **96.3%** | **+29.6%** | **+27pp** |",
        "",
        "**3 人的 resolved 样本都太小**, raw_hit 不构成有意义的命中率指标. 重点看逐条 raw/excess_soxx:",
        "- **raw 涨 + excess_soxx 正**: 选对且跑赢板块 (强)",
        "- **raw 涨 + excess_soxx 负**: 选对但跑输板块 (= P4-15 LinQingV 同款 bug)",
        "- **raw 跌**: 选错",
        "",
        "## 备注 / 已知坑",
        "",
        "- 3 人 ORIGINAL 推文 70%+ 是 commentary/news (long/short 只 22-30%)",
        "- 推文 90%+ 集中在 2026-04 ~ 2026-06 (爆火), entry 大量在 2026-03 之后",
        "- 90d 验证窗口 = 大部分判断还在 pending",
        "- 我没自动修 short — 5 条 short 修对是我手动逐条查原文判断的",
        "",
    ])

    out = Path("/workspace/outputs/p5_verify_3kol_v6.md")
    out.write_text("\n".join(lines))
    print(f"\n[{_t.time()-t0:.0f}s] 📄 {out}", flush=True)

    json_out = Path("/workspace/logs/p5_4kol_triage/verify_3kol_v6.json")
    json.dump(all_results, open(json_out, "w"), indent=2, ensure_ascii=False, default=str)
    print(f"[{_t.time()-t0:.0f}s] 📄 {json_out}", flush=True)


if __name__ == "__main__":
    main()