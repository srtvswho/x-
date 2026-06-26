"""KOL Scoreboard — 验证层规则 (防止误读)

铁律 4 (P4-15): 每条预测同时输出 raw_return (绝对涨跌) 和 excess_return (相对板块超额)
铁律 5 (P4-15): 真亏只看 raw_return < 0, 不看 excess
铁律 6 (P4-15): 报告禁止 "5 大赢/5 大输" 模糊说法, 必须拆成 4 类
铁律 7 (P4-15): 基准分层 — vs SPY / SOXX/SMH / 对应国别 ETF
铁律 8 (P4-15): 核心指标 raw 选股命中率 (raw>0 比例), 不依赖任何 benchmark
"""
from __future__ import annotations
import json
import os
import statistics
from collections import Counter, defaultdict
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Optional


PRICE_DIR = "/workspace/data/price_cache"
TODAY = "2026-06-12"  # 默认, 可改


def load_bars(ticker: str) -> list[dict]:
    """加载 ticker 的 bar 数据。处理 SIVE 镜像。"""
    p = f"{PRICE_DIR}/{ticker}_FULL_HISTORY.json"
    if not os.path.exists(p) and ticker == "SIVE":
        p = f"{PRICE_DIR}/SIVEF_FULL_HISTORY.json"
    if os.path.exists(p):
        return json.load(open(p))
    return []


def find_price(bars: list[dict], target: str) -> tuple[Optional[float], Optional[str]]:
    """找 >= target 的第一个 close。"""
    for b in bars:
        if b["date"] >= target:
            return b["c"], b["date"]
    return None, None


def parse_twitter_date(s: str) -> Optional[datetime]:
    """parse Twitter / ISO 日期。"""
    if not s:
        return None
    try:
        return datetime.strptime(s, "%a %b %d %H:%M:%S %z %Y").date()
    except (ValueError, TypeError):
        pass
    try:
        return datetime.fromisoformat(s.replace("Z", "+00:00")).date()
    except Exception:
        pass
    try:
        return datetime.strptime(s[:10], "%Y-%m-%d").date()
    except Exception:
        return None


# === 验证层铁律 4-7: 双列输出 + 三层基准 ===
def verify_prediction(
    prediction: dict,
    benchmarks: dict[str, list[dict]],
    max_horizon: int = 180,
    today: str = TODAY,
) -> dict:
    """验证单条预测, 返回双列 (raw_ret + excess_ret) 三层基准。

    Args:
        prediction: {ticker, direction, source_date, horizon_days, ...}
        benchmarks: {"SPY": bars, "SOXX": bars, "SMH": bars, "KOSPI": bars, ...}
        max_horizon: 最大 horizon 限制
        today: 数据截止日

    Returns:
        {
          "resolved": bool,
          "entry_date", "exit_date", "entry_px", "exit_px", "horizon_days",
          "raw_ret": <float, %>,
          "excess": {bench_name: {excess_ret, hit}, ...},
          "is_raw_loss": raw_ret < 0,
          "reason": "no_ticker" / "no_bars" / "no_px" / "no_bench" / "ok"
        }
    """
    d = parse_twitter_date(prediction.get("source_date", ""))
    if not d:
        return {"resolved": False, "reason": "bad_date"}
    ed = (d + timedelta(days=1)).strftime("%Y-%m-%d")
    horizon = min(int(prediction.get("horizon_days", 30) or 30), max_horizon)
    xd = min((d + timedelta(days=horizon + 1)).strftime("%Y-%m-%d"), today)

    ticker = prediction.get("ticker")
    if not ticker:
        return {"resolved": False, "reason": "no_ticker"}

    bars = load_bars(ticker)
    if not bars:
        return {"resolved": False, "reason": f"no_bars_{ticker}"}
    e_px, _ = find_price(bars, ed)
    x_px, _ = find_price(bars, xd)
    if not e_px or not x_px:
        return {"resolved": False, "reason": "no_px"}

    # raw_ret (绝对涨跌)
    if prediction["direction"] == "long":
        raw_ret = (x_px - e_px) / e_px * 100
    elif prediction["direction"] == "short":
        raw_ret = (e_px - x_px) / e_px * 100
    else:
        return {"resolved": False, "reason": "neutral"}

    # excess_ret 三层基准
    excess_results = {}
    for bench_name, bench_bars in benchmarks.items():
        if not bench_bars:
            continue
        be, _ = find_price(bench_bars, ed)
        bx, _ = find_price(bench_bars, xd)
        if not be or not bx:
            continue
        bench_ret = (bx - be) / be * 100
        excess = raw_ret - bench_ret
        # hit: long excess>0 / short excess<0
        hit = (excess > 0 and prediction["direction"] == "long") or (
            excess < 0 and prediction["direction"] == "short"
        )
        excess_results[bench_name] = {
            "bench_ret": bench_ret,
            "excess_ret": excess,
            "hit": hit,
        }

    if not excess_results:
        return {"resolved": False, "reason": "no_bench"}

    return {
        "resolved": True,
        "ticker": ticker,
        "direction": prediction["direction"],
        "horizon_days": horizon,
        "entry_date": ed,
        "exit_date": xd,
        "entry_px": e_px,
        "exit_px": x_px,
        "raw_ret": raw_ret,           # 铁律 4: 必须有
        "excess": excess_results,      # 铁律 4: 必须有 (双列)
        "is_raw_loss": raw_ret < 0,   # 铁律 5: 真亏只看 raw<0
        "reason": "ok",
    }


# === 验证层铁律 6: 4 分类 (禁止 "5 大赢/5 大输" 模糊说法) ===
def categorize_predictions(verified: list[dict]) -> dict:
    """把验证后的预测分成 4 类 (铁律 6)。

    Returns:
        {
          "raw_win": [...],   # raw_ret > 0 排序 (前 5 = 5 大 raw 真赢)
          "raw_loss": [...],  # raw_ret < 0 排序 (前 5 = 5 大 raw 真输)
          "excess_win": [...], # excess_ret 排序 (前 5 = 5 大跑赢板块)
          "excess_loss": [...],# excess_ret 排序 (前 5 = 5 大跑输板块)
        }
    """
    raw_win = sorted(
        [v for v in verified if v["raw_ret"] > 0],
        key=lambda x: -x["raw_ret"],
    )
    raw_loss = sorted(
        [v for v in verified if v["raw_ret"] < 0],
        key=lambda x: x["raw_ret"],
    )
    excess_win = sorted(
        verified,
        key=lambda x: -x["excess"].get("SOXX", {}).get("excess_ret", 0),
    )
    excess_loss = sorted(
        verified,
        key=lambda x: x["excess"].get("SOXX", {}).get("excess_ret", 0),
    )
    return {
        "raw_win": raw_win,
        "raw_loss": raw_loss,
        "excess_win": excess_win,
        "excess_loss": excess_loss,
    }


# === 验证层铁律 8: raw 选股命中率 (核心指标) ===
def raw_hit_rate(verified: list[dict]) -> dict:
    """核心指标: raw 选股命中率 (不依赖任何 benchmark)。

    Returns:
        {
          "n_total": int,
          "n_raw_pos": int (raw_ret > 0),
          "n_raw_neg": int (raw_ret < 0),
          "n_raw_zero": int (raw_ret == 0),
          "raw_hit_rate": n_raw_pos / n_total * 100,
          "median_raw_ret": float,
        }
    """
    if not verified:
        return {"n_total": 0, "raw_hit_rate": 0, "median_raw_ret": 0}
    n = len(verified)
    n_pos = sum(1 for v in verified if v["raw_ret"] > 0)
    n_neg = sum(1 for v in verified if v["raw_ret"] < 0)
    n_zero = sum(1 for v in verified if v["raw_ret"] == 0)
    raws = [v["raw_ret"] for v in verified]
    return {
        "n_total": n,
        "n_raw_pos": n_pos,
        "n_raw_neg": n_neg,
        "n_raw_zero": n_zero,
        "raw_hit_rate": n_pos / n * 100,
        "median_raw_ret": statistics.median(raws),
    }


def excess_metrics(verified: list[dict], bench: str = "SOXX") -> dict:
    """excess vs benchmark 中位数 + hit_rate。"""
    if not verified:
        return {"n": 0, "med_excess": 0, "hit_rate": 0}
    n = len(verified)
    excesses = [v["excess"][bench]["excess_ret"] for v in verified if bench in v["excess"]]
    hits = sum(1 for v in verified if v["excess"].get(bench, {}).get("hit", False))
    return {
        "n": len(excesses),
        "med_excess": statistics.median(excesses) if excesses else 0,
        "hit_rate": hits / n * 100 if n else 0,
    }


def wilson_lower(p_hits: int, n: int, z: float = 1.96) -> float:
    """95% CI 下界。"""
    if n == 0:
        return 0
    phat = p_hits / n
    denom = 1 + z**2 / n
    center = (phat + z**2 / (2 * n)) / denom
    margin = z * ((phat * (1 - phat) + z**2 / (4 * n)) / n) ** 0.5 / denom
    return (center - margin) * 100


# === 主入口: 标准 scoreboard ===
def build_scoreboard(
    predictions: list[dict],
    benchmarks: dict[str, list[dict]],
    attribution_filter: list[str] | None = None,
    today: str = TODAY,
) -> dict:
    """build 标准 KOL scoreboard。

    Args:
        predictions: [{ticker, direction, source_date, horizon_days, attribution, thesis}, ...]
        benchmarks: {"SPY": bars, "SOXX": bars, ...}
        attribution_filter: 只算这些 attribution ("ORIGINAL", "RELAYED+COMMENT")
            None = 算全部
        today: 数据截止日

    Returns:
        {
          "n_total": 预测总数 (filtered),
          "n_resolved": 验证成功的,
          "n_unresolved": {"no_ticker": n, "no_bars": n, ...},
          "raw_metrics": raw 选股命中率 (铁律 8),
          "excess_metrics": {SPY: {...}, SOXX: {...}},
          "categorized": 4 分类 (铁律 6),
          "by_horizon": {30d, 90d, 180d},
          "by_direction": {long, short},
          "by_ticker": {ticker: n, hit, med_excess, raw_hit_rate},
        }
    """
    # 1. attribution 过滤
    if attribution_filter is None:
        filtered = predictions
    else:
        filtered = [p for p in predictions if p.get("attribution") in attribution_filter]

    # 2. verify 每条
    verified = []
    unresolved_counter = Counter()
    for p in filtered:
        v = verify_prediction(p, benchmarks, today=today)
        if v.get("resolved"):
            verified.append(v)
        else:
            unresolved_counter[v.get("reason", "?")] += 1

    # 3. raw metrics (铁律 8)
    raw_m = raw_hit_rate(verified)

    # 4. excess metrics
    excess_m = {}
    for bench in benchmarks.keys():
        if bench in ["SPY", "SOXX", "SMH", "KOSPI"]:
            excess_m[bench] = excess_metrics(verified, bench=bench)

    # 5. categorized (铁律 6)
    cat = categorize_predictions(verified)

    # 6. by horizon
    by_h = {}
    for h in [30, 90, 180]:
        sub = [v for v in verified if v["horizon_days"] == h]
        if sub:
            by_h[f"{h}d"] = {
                "n": len(sub),
                "raw_hit_rate": raw_hit_rate(sub)["raw_hit_rate"],
                "med_raw": statistics.median([v["raw_ret"] for v in sub]),
                "med_excess_soxx": statistics.median([
                    v["excess"].get("SOXX", {}).get("excess_ret", 0)
                    for v in sub if "SOXX" in v["excess"]
                ]) if any("SOXX" in v["excess"] for v in sub) else 0,
            }

    # 7. by direction
    by_d = {}
    for d in ["long", "short"]:
        sub = [v for v in verified if v["direction"] == d]
        if sub:
            by_d[d] = {
                "n": len(sub),
                "raw_hit_rate": raw_hit_rate(sub)["raw_hit_rate"],
                "med_raw": statistics.median([v["raw_ret"] for v in sub]),
                "med_excess_soxx": statistics.median([
                    v["excess"].get("SOXX", {}).get("excess_ret", 0)
                    for v in sub if "SOXX" in v["excess"]
                ]) if any("SOXX" in v["excess"] for v in sub) else 0,
            }

    # 8. by ticker
    by_t = defaultdict(list)
    for v in verified:
        by_t[v["ticker"]].append(v)
    by_ticker = {}
    for t, lst in by_t.items():
        n = len(lst)
        n_hit = sum(1 for v in lst if v["excess"].get("SOXX", {}).get("hit", False))
        n_raw_pos = sum(1 for v in lst if v["raw_ret"] > 0)
        med_excess = statistics.median([
            v["excess"].get("SOXX", {}).get("excess_ret", 0)
            for v in lst if "SOXX" in v["excess"]
        ]) if any("SOXX" in v["excess"] for v in lst) else 0
        by_ticker[t] = {
            "n": n,
            "hit_rate_soxx": n_hit / n * 100 if n else 0,
            "raw_hit_rate": n_raw_pos / n * 100 if n else 0,
            "med_excess_soxx": med_excess,
        }

    return {
        "n_total": len(filtered),
        "n_resolved": len(verified),
        "n_unresolved": dict(unresolved_counter),
        "raw_metrics": raw_m,
        "excess_metrics": excess_m,
        "categorized": cat,
        "by_horizon": by_h,
        "by_direction": by_d,
        "by_ticker": dict(by_ticker),
        "wilson_lower_raw_hit_rate": wilson_lower(raw_m["n_raw_pos"], raw_m["n_total"]),
    }


# === 测试 ===
def _test_scoreboard():
    """跑几个 sanity 测试。"""
    # mock predictions
    mock_preds = [
        {"ticker": "NVDA", "direction": "long", "source_date": "2025-04-15",
         "horizon_days": 180, "attribution": "ORIGINAL"},
        {"ticker": "MU", "direction": "long", "source_date": "2025-04-15",
         "horizon_days": 180, "attribution": "ORIGINAL"},
        {"ticker": "MU", "direction": "short", "source_date": "2025-06-26",
         "horizon_days": 180, "attribution": "ORIGINAL"},
        {"ticker": "QCOM", "direction": "short", "source_date": "2025-05-22",
         "horizon_days": 180, "attribution": "ORIGINAL"},
    ]
    # mock benchmarks (用 SOXX/SPY 全 FULL_HISTORY)
    benchmarks = {
        "SPY": load_bars("SPY"),
        "SOXX": load_bars("SOXX"),
        "SMH": load_bars("SMH"),
    }
    sb = build_scoreboard(mock_preds, benchmarks)
    print(f"n_resolved: {sb['n_resolved']}/4")
    print(f"raw_metrics: {sb['raw_metrics']}")
    print(f"excess_metrics (SOXX): {sb['excess_metrics']['SOXX']}")
    print(f"categorized (前 5 raw_loss):")
    for v in sb["categorized"]["raw_loss"][:5]:
        print(f"  {v['ticker']} {v['direction']} {v['horizon_days']}d: raw={v['raw_ret']:+.1f}%")
    print(f"categorized (前 5 excess_loss):")
    for v in sb["categorized"]["excess_loss"][:5]:
        ex = v["excess"].get("SOXX", {}).get("excess_ret", 0)
        print(f"  {v['ticker']} {v['direction']} {v['horizon_days']}d: raw={v['raw_ret']:+.1f}% excess={ex:+.1f}%")


if __name__ == "__main__":
    _test_scoreboard()