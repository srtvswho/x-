"""P4-1 找 SNDK / MU 的"起涨初期"窗口 (+30% ~ +150%)

逻辑:
1. 找局部低点 (60 天 rolling low)
2. 从低点算 +30% 是窗口起点
3. 从低点算 +150% 是窗口终点
4. 起点到终点就是"起飞初期"窗口
"""
import os, json
from datetime import date, datetime, timedelta
import statistics

def find_surge_windows(bars, lookback_low=60, low_threshold_pct=0.30, high_threshold_pct=1.50):
    """找所有"从局部低点反弹 +30%~+150%"的窗口。

    返回 list of (start_date, end_date, low_date, low_price, peak_date, peak_price, pct_peak)
    """
    windows = []
    i = 0
    n = len(bars)
    used = set()  # 标记已用过的低点,避免重复窗口

    while i < n - lookback_low:
        # 当前 bar 作为候选低点
        cand_idx = i
        # 在 cand_idx 之后 60 天内有没有更低的?
        local_low_idx = cand_idx
        local_low = bars[cand_idx]["l"]
        for j in range(cand_idx, min(cand_idx + lookback_low, n)):
            if bars[j]["l"] < local_low:
                local_low = bars[j]["l"]
                local_low_idx = j

        # 用 local_low 作为低点
        low_px = local_low
        low_date = bars[local_low_idx]["date"]
        if low_date in used:
            i += 1
            continue

        # 计算 +30% 起点
        target_start = low_px * (1 + low_threshold_pct)
        target_end = low_px * (1 + high_threshold_pct)

        # 找价格首次触及 target_start 的日期
        start_idx = None
        for j in range(local_low_idx, n):
            if bars[j]["h"] >= target_start:
                start_idx = j
                break
        if start_idx is None:
            i += 1
            continue

        # 找价格首次触及 target_end 的日期 (或之后回撤 -15% 提前结束)
        end_idx = None
        for j in range(start_idx, n):
            if bars[j]["h"] >= target_end:
                end_idx = j
                break
            # 或者从最高点回撤 15% (确认涨势结束)
            peak_in_window = max(bars[k]["h"] for k in range(start_idx, j+1))
            if peak_in_window >= target_start and bars[j]["c"] < peak_in_window * 0.85:
                end_idx = j
                break
        if end_idx is None:
            # 没到 +150%,只用最大涨幅
            max_high_in_window = max(bars[j]["h"] for j in range(start_idx, n))
            if max_high_in_window >= target_start * 1.05:  # 至少涨到 35%
                end_idx = n - 1

        if end_idx is None:
            i += 1
            continue

        peak_px = max(bars[j]["h"] for j in range(start_idx, end_idx+1))
        peak_idx = next(j for j in range(start_idx, end_idx+1) if bars[j]["h"] == peak_px)
        pct_peak = (peak_px - low_px) / low_px * 100

        windows.append({
            "low_date": low_date,
            "low_px": low_px,
            "start_date": bars[start_idx]["date"],
            "start_px": bars[start_idx]["c"],
            "end_date": bars[end_idx]["date"],
            "peak_date": bars[peak_idx]["date"],
            "peak_px": peak_px,
            "pct_peak": pct_peak,
        })
        used.add(low_date)
        # 跳过这个窗口
        i = end_idx + 1

    return windows


# 跑 SNDK
for ticker in ["SNDK", "MU"]:
    path = f"/workspace/data/price_cache/{ticker}_FULL_HISTORY.json"
    if not os.path.exists(path):
        print(f"{ticker}: bars 缺失")
        continue
    bars = json.load(open(path))
    print(f"\n{'=' * 60}")
    print(f"{ticker}: {len(bars)} bars, {bars[0]['date']} ~ {bars[-1]['date']}")
    print(f"{'=' * 60}")
    windows = find_surge_windows(bars, lookback_low=60, low_threshold_pct=0.30, high_threshold_pct=1.50)
    print(f"\n找到 {len(windows)} 个 +30%~+150% 窗口:")
    for i, w in enumerate(windows, 1):
        print(f"  #{i}: low {w['low_date']} ${w['low_px']:.2f}")
        print(f"       start {w['start_date']} ${w['start_px']:.2f} (+30%)")
        print(f"       peak {w['peak_date']} ${w['peak_px']:.2f} ({w['pct_peak']:+.1f}% from low)")
        print(f"       end {w['end_date']}")
        print(f"       窗口天数: {(date(*map(int, w['end_date'].split('-'))) - date(*map(int, w['start_date'].split('-')))).days} 天")
        print()

    # 也打印价格走势简图 (按月)
    print(f"\n{ticker} 月度 close:")
    monthly = {}
    for b in bars:
        ym = b["date"][:7]
        monthly.setdefault(ym, []).append(b["c"])
    for ym in sorted(monthly.keys()):
        cs = monthly[ym]
        print(f"  {ym}: open={cs[0]:.2f} close={cs[-1]:.2f} ({len(cs)} bars)")