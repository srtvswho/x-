"""Phase 3 P3-2 单条验证函数 + 10 条人工算例

严格按 5 条铁律:
1. entry_date = next_trading_day(prediction.published_at) ← 绝不用 captured_at
2. 币种自洽(美股 USD 用 ^GSPC/SPY 美元基准)
3. 双层基准:宽基 ^GSPC + 行业 ETF (半导体=SOXX)
4. exit_date > today → status='pending', 不计入胜率
5. 聚合优先:本文件是单条,聚合留给 P3-2 第三步

entry_price:open 优先, close 兜底;若 entry_date 当日全无数据(停牌/退市/holiday),
    顺延到下一交易日,记录 entry_slippage_days。
"""
from __future__ import annotations
import os, json, time
import sqlite3
import requests
from datetime import datetime, timedelta, timezone, date
from typing import Optional, Tuple, List, Dict, Any

POLY = os.environ.get("POLYGON_API_KEY", "")
if not POLY:
    raise SystemExit("POLYGON_API_KEY not set")
TODAY = date(2026, 6, 15)  # 验证日(实际可改成 date.today())

# ============== 交易日历(简化版) ==============
# 美股 2025-2026 已知 holiday(只列过去 + 未来几个)
US_HOLIDAYS_2025_2026 = {
    # 2025
    date(2025, 1, 1),  # New Year
    date(2025, 1, 20),  # MLK
    date(2025, 2, 17),  # Presidents Day
    date(2025, 4, 18),  # Good Friday
    date(2025, 5, 26),  # Memorial Day
    date(2025, 6, 19),  # Juneteenth
    date(2025, 7, 4),   # Independence Day
    date(2025, 7, 3),   # 7/4 落在 Friday 提前 closed
    date(2025, 9, 1),   # Labor Day
    date(2025, 11, 27), # Thanksgiving
    date(2025, 11, 28), # Black Friday(半日, 但视作 closed)
    date(2025, 12, 25), # Christmas
    # 2026
    date(2026, 1, 1),
    date(2026, 1, 19),
    date(2026, 2, 16),
    date(2026, 4, 3),   # Good Friday
    date(2026, 5, 25),
    date(2026, 6, 19),
    date(2026, 7, 3),   # 7/4 周六,Friday closed
    date(2026, 9, 7),
    date(2026, 11, 26),
    date(2026, 12, 25),
}

def is_us_trading_day(d: date) -> bool:
    if d.weekday() >= 5:  # Sat/Sun
        return False
    if d in US_HOLIDAYS_2025_2026:
        return False
    return True

def next_trading_day(d: date, max_lookahead: int = 10) -> Tuple[date, int]:
    """返回 d 之后的第一个交易日(严格 d+1 起)。返回 (date, slippage_days)."""
    cur = d + timedelta(days=1)
    slip = 0
    while slip < max_lookahead:
        if is_us_trading_day(cur):
            return cur, slip
        cur += timedelta(days=1)
        slip += 1
    raise ValueError(f"couldn't find trading day after {d} within {max_lookahead} days")

def add_trading_days(start: date, n: int) -> date:
    """从 start 起,加 n 个交易日。"""
    if n == 0:
        return start
    cur = start
    added = 0
    while added < n:
        cur += timedelta(days=1)
        if is_us_trading_day(cur):
            added += 1
    return cur

# ============== Horizon 配置 ==============
# 1w = 5 trading days, 1m ≈ 21, 3m ≈ 63, 6m ≈ 126
HORIZONS = {
    "1w":  5,
    "1m":  21,
    "3m":  63,
    "6m":  126,
}

# 行业 ETF 映射(简化版 — 只覆盖常见)
SECTOR_ETF = {
    # 半导体/光通讯
    "semiconductor": "SOXX",  # iShares Semiconductor
    "photonics":     "SOXX",
    "cpo":           "SOXX",
    "ai_infra":      "SOXX",
    # 加密挖矿/算力
    "crypto_miner":  "WGMI",  # Valkyrie Bitcoin Miners
    "neocloud":      "WGMI",  # 也算
    "ai_compute":    "SMH",   # VanEck Semiconductor
    # 太空/火箭
    "space":         "UFO",   # Procure Space ETF
    "aerospace":     "UFO",
    # 电商/社媒
    "social":        "SPY",
    "ecommerce":     "SPY",
    # 通用 fallback
    "default":       "SPY",
}

# 宽基 = SPY (Proxy for ^GSPC, 两者几乎同价差 0.01%)
BROAD_BENCHMARK = "SPY"

# 缓存 — 用文件存日线(避免重复拉)
CACHE_DIR = "/workspace/data/price_cache"
os.makedirs(CACHE_DIR, exist_ok=True)

def fetch_polygon_daily(symbol: str, start: str, end: str) -> List[Dict]:
    """Polygon 拉日线。返回 [{date, o, c, h, l, v}].

    优先级:
    1. 特定窗口 cache (例如 RKLB_2025-11-19_2026-06-03.json)
    2. FULL_HISTORY cache (例如 SPY_FULL_HISTORY.json, 覆盖全 Polygon 2 年历史)
    3. 实时 Polygon API
    """
    cache_file = os.path.join(CACHE_DIR, f"{symbol}_{start}_{end}.json")
    if os.path.exists(cache_file):
        return json.load(open(cache_file))
    # 尝试 FULL_HISTORY cache
    full_file = os.path.join(CACHE_DIR, f"{symbol}_FULL_HISTORY.json")
    if os.path.exists(full_file):
        return json.load(open(full_file))
    url = f"https://api.polygon.io/v2/aggs/ticker/{symbol}/range/1/day/{start}/{end}"
    params = {"adjusted": "true", "sort": "asc", "limit": 50000, "apiKey": POLY}
    r = requests.get(url, params=params, timeout=30)
    data = r.json()
    if data.get("status") not in ("OK", "DELAYED") or not data.get("results"):
        return []
    bars = []
    for b in data["results"]:
        bars.append({
            "date": datetime.fromtimestamp(b["t"]/1000, tz=timezone.utc).strftime("%Y-%m-%d"),
            "o": b["o"], "c": b["c"], "h": b["h"], "l": b["l"], "v": b["v"],
        })
    # 缓存
    with open(cache_file, "w") as f:
        json.dump(bars, f)
    time.sleep(0.5)  # 节流
    return bars

def get_bar_on_or_after(bars: List[Dict], target_date: str, max_lookahead: int = 10) -> Tuple[Optional[Dict], int]:
    """在 bars 中找 >= target_date 的第一个 bar。返回 (bar, slippage_days)."""
    target_dt = datetime.fromisoformat(target_date).date()
    for bar in bars:
        bar_dt = datetime.fromisoformat(bar["date"]).date()
        if bar_dt >= target_dt:
            slip = (bar_dt - target_dt).days
            if slip > max_lookahead:
                return None, slip
            return bar, slip
    return None, 999

# ============== 单条验证函数 ==============
def verify_one(pred: Dict) -> Dict:
    """单条 prediction 验证。

    Args:
        pred: 包含 prediction_id, post_id, ticker, direction, horizon (per-row)
              published_at, thesis_category 等
    
    Returns:
        dict with: status_per_horizon, entry_date, entry_price, 
                   raw_return_per_horizon, benchmark_return_per_horizon, 
                   excess_return_per_horizon, sector_benchmark_used
    """
    ticker = pred["ticker"]
    direction = pred["direction"]
    pub_at = pred["published_at"]
    cat = pred.get("thesis_category") or "default"

    # 1. 检查 published_at 必须有值(空 → 跳过)
    if not pub_at:
        return {"error": "missing_published_at", "skipped": True, "reason": "未来增量抓取时 X API 漏 createdAt,published_at 留空"}
    
    pub_dt = datetime.fromisoformat(pub_at.replace("Z", "+00:00")).date()
    
    # 2. SIVE 走 SIVEF(美股 OTC, USD)
    asset_symbol = "SIVEF" if ticker == "SIVE" else ticker
    
    # 3. entry_date = next_trading_day(pub_at)
    entry_date, entry_slip = next_trading_day(pub_dt)
    
    # 4. exit_date = entry_date + horizon trading days
    # 但 P3-2 验证函数对所有 4 个 horizon 算(不是 pred.horizon 单一)
    exits = {}
    for h_name, h_days in HORIZONS.items():
        exits[h_name] = add_trading_days(entry_date, h_days)
    
    # 5. 拉数据(asset + benchmark + sector ETF)
    # 拉一段覆盖 entry_date 到最大 exit_date + 一些 buffer
    max_exit = max(exits.values())
    start = (entry_date - timedelta(days=5)).strftime("%Y-%m-%d")
    end = (max_exit + timedelta(days=5)).strftime("%Y-%m-%d")
    
    asset_bars = fetch_polygon_daily(asset_symbol, start, end)
    bench_bars = fetch_polygon_daily(BROAD_BENCHMARK, start, end)
    sector_symbol = SECTOR_ETF.get(cat, SECTOR_ETF["default"])
    sector_bars = fetch_polygon_daily(sector_symbol, start, end) if sector_symbol != BROAD_BENCHMARK else bench_bars
    
    # 6. 取 entry_price
    entry_bar, entry_slip_actual = get_bar_on_or_after(asset_bars, entry_date.isoformat())
    if not entry_bar:
        return {
            "error": "no_entry_bar", 
            "entry_date": entry_date.isoformat(),
            "entry_slip": entry_slip_actual,
            "skipped": True,
        }
    # entry_price: open 优先, close 兜底
    entry_price = entry_bar["o"] if entry_bar["o"] is not None else entry_bar["c"]
    actual_entry_date = entry_bar["date"]
    entry_slip_actual = (datetime.fromisoformat(actual_entry_date).date() - entry_date).days
    
    # 7. 4 horizons 验证
    results_per_h = {}
    for h_name in HORIZONS:
        exit_date = exits[h_name]
        is_pending = exit_date > TODAY
        
        if is_pending:
            results_per_h[h_name] = {
                "status": "pending",
                "exit_date": exit_date.isoformat(),
                "exit_price": None,
                "raw_return": None,
                "benchmark_return": None,
                "excess_return": None,
                "excess_vs_sector": None,
                "hit": None,
                "hit_absolute": None,
            }
            continue
        
        # exit_price
        exit_bar, exit_slip = get_bar_on_or_after(asset_bars, exit_date.isoformat())
        if not exit_bar:
            results_per_h[h_name] = {
                "status": "no_exit_bar",
                "exit_date": exit_date.isoformat(),
            }
            continue
        
        # benchmark exit
        bench_exit_bar, _ = get_bar_on_or_after(bench_bars, exit_date.isoformat())
        bench_entry_bar, _ = get_bar_on_or_after(bench_bars, entry_date.isoformat())
        
        if not bench_exit_bar or not bench_entry_bar:
            bench_return = None
            excess = None
        else:
            bench_return = (bench_exit_bar["c"] - bench_entry_bar["c"]) / bench_entry_bar["c"]
        
        # sector exit
        if sector_symbol == BROAD_BENCHMARK:
            sector_return = bench_return
        else:
            sector_exit_bar, _ = get_bar_on_or_after(sector_bars, exit_date.isoformat())
            sector_entry_bar, _ = get_bar_on_or_after(sector_bars, entry_date.isoformat())
            if sector_exit_bar and sector_entry_bar:
                sector_return = (sector_exit_bar["c"] - sector_entry_bar["c"]) / sector_entry_bar["c"]
            else:
                sector_return = None
        
        # raw_return
        raw_return = (exit_bar["c"] - entry_price) / entry_price
        # direction 处理:short 取负
        if direction == "short":
            raw_return = -raw_return
            if bench_return is not None:
                # short: 资产跌赚, 基准涨就难对冲, 仍按 (raw - bench) 算 excess
                # 但 raw 已经取负了, 公式不变
                pass
        # neutral: 不计
        if direction == "neutral":
            results_per_h[h_name] = {
                "status": "neutral",
                "exit_date": exit_date.isoformat(),
            }
            continue
        
        excess = (raw_return - bench_return) if bench_return is not None else None
        excess_sector = (raw_return - sector_return) if sector_return is not None else None
        hit = (excess > 0) if excess is not None else None
        hit_abs = (raw_return > 0)
        
        results_per_h[h_name] = {
            "status": "resolved",
            "exit_date": exit_date.isoformat(),
            "actual_exit_date": exit_bar["date"],
            "exit_slip_days": (datetime.fromisoformat(exit_bar["date"]).date() - exit_date).days,
            "exit_price": exit_bar["c"],
            "raw_return": round(raw_return, 6),
            "benchmark_return": round(bench_return, 6) if bench_return is not None else None,
            "excess_return": round(excess, 6) if excess is not None else None,
            "excess_vs_sector": round(excess_sector, 6) if excess_sector is not None else None,
            "hit": hit,
            "hit_absolute": hit_abs,
        }
    
    return {
        "prediction_id": pred["prediction_id"],
        "ticker": ticker,
        "asset_symbol_used": asset_symbol,
        "published_at": pub_at,
        "entry_date_planned": entry_date.isoformat(),
        "entry_date_actual": actual_entry_date,
        "entry_slip_days": entry_slip_actual,
        "entry_price": entry_price,
        "sector_benchmark": sector_symbol,
        "direction": direction,
        "horizons": results_per_h,
    }


# ============== 跑 10 条 ==============
def main():
    # 加载 10 条样本
    samples = []
    with open("/tmp/p3p2_10_samples.txt") as f:
        for line in f:
            name, pid = line.strip().split("\t")
            samples.append((name, pid))
    
    conn = sqlite3.connect("/workspace/data/signalboard_full.db")
    
    # 报告
    print("=" * 80)
    print(f"Phase 3 P3-2: 单条验证函数 + 10 条人工算例")
    print(f"=" * 80)
    print(f"验证日: {TODAY}")
    print(f"基准宽基: {BROAD_BENCHMARK}")
    print(f"行业 ETF 映射: {SECTOR_ETF}")
    print()
    
    all_results = []
    for name, pid in samples:
        # 查 prediction + raw_post
        sql = """SELECT p.prediction_id, p.post_id, p.ticker, p.direction, p.horizon, 
                p.thesis_category, p.thesis_summary, p.conviction, 
                rp.published_at, substr(rp.raw_text, 1, 80) as raw_text
            FROM predictions p JOIN raw_posts rp ON p.post_id = rp.post_id
            WHERE p.prediction_id = ?"""
        row = conn.execute(sql, (pid,)).fetchone()
        if not row:
            print(f"  {name}: NOT FOUND pid={pid}")
            continue
        pred = {
            "prediction_id": row[0], "post_id": row[1], "ticker": row[2],
            "direction": row[3], "horizon": row[4], "thesis_category": row[5],
            "thesis_summary": row[6], "conviction": row[7], "published_at": row[8],
        }
        print(f"\n[{name}]  {row[2]} {row[3]} {row[4]}  pub={row[8][:10]}")
        print(f"  thesis: {row[6][:80]}")
        print(f"  raw: {row[9]}")
        
        result = verify_one(pred)
        all_results.append((name, pred, result))
        
        # 打印结果
        if result.get("skipped"):
            print(f"  ⚠️  SKIPPED: {result.get('reason', 'unknown')}")
            continue
        if result.get("error"):
            print(f"  ⚠️  ERROR: {result.get('error')}")
            continue
        
        print(f"  entry_date: planned={result['entry_date_planned']}  actual={result['entry_date_actual']} (slip={result['entry_slip_days']}d)")
        print(f"  entry_price: ${result['entry_price']:.4f}")
        print(f"  asset_symbol: {result['asset_symbol_used']}  sector_bench: {result['sector_benchmark']}")
        for h_name, h_res in result["horizons"].items():
            status = h_res["status"]
            print(f"  [{h_name}] {status:10s}", end="")
            if status == "resolved":
                ep = h_res.get('exit_price')
                br = h_res.get('benchmark_return')
                er = h_res.get('excess_return')
                rr = h_res.get('raw_return')
                hit = h_res.get('hit')
                ep_s = f"${ep:.4f}" if ep is not None else "N/A"
                rr_s = f"{rr:+.2%}" if rr is not None else "N/A"
                br_s = f"{br:+.2%}" if br is not None else "N/A"
                er_s = f"{er:+.2%}" if er is not None else "N/A"
                hit_s = str(hit) if hit is not None else "N/A"
                print(f"  exit={h_res['actual_exit_date']}  exit_px={ep_s}  raw={rr_s}  bench={br_s}  excess={er_s}  hit={hit_s}")
            elif status == "pending":
                print(f"  exit_date={h_res['exit_date']}  pending (not yet)")
            else:
                print(f"  exit_date={h_res.get('exit_date', 'N/A')}  ({status})")
    
    # 落 JSON 报告
    with open("/workspace/outputs/phase3_p2_10_samples_verify.json", "w", encoding="utf-8") as f:
        json.dump([{"name": n, "pred": p, "result": r} for n, p, r in all_results], f, indent=2, ensure_ascii=False)
    print()
    print(f"✅ 落 outputs/phase3_p2_10_samples_verify.json")
    conn.close()

if __name__ == "__main__":
    main()
