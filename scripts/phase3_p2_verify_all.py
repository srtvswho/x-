"""Phase 3 P3-2 全量验证脚本(3983 predictions / 414 ticker)

完整状态分类(每个 horizon 必须落到明确状态之一):
- resolved_hit: 已到期 + 基准齐 + excess > 0
- resolved_miss: 已到期 + 基准齐 + excess <= 0
- pending: exit_date > today
- unverifiable_no_benchmark: 已到期 + 基准缺(SPY/SOXX/SMH 拉不到)
- skipped_no_price: 个股行情拉不到(asset_bars 为空)

绝不把 unverifiable / skipped 当作 miss。
跑完先出"可验证性体检"报告,等 user 确认再聚合记分牌。
"""
from __future__ import annotations
import os, json, time
import sqlite3
import requests
from datetime import datetime, timedelta, timezone, date
from typing import Optional, Tuple, List, Dict, Any
from collections import Counter, defaultdict

POLY = os.environ.get("POLYGON_API_KEY", "")
if not POLY:
    raise SystemExit("POLYGON_API_KEY not set")
TODAY = date(2026, 6, 15)

US_HOLIDAYS = {
    date(2024, 1, 1), date(2024, 1, 15), date(2024, 2, 19), date(2024, 3, 29),
    date(2024, 5, 27), date(2024, 6, 19), date(2024, 7, 4), date(2024, 9, 2),
    date(2024, 11, 28), date(2024, 12, 25),
    date(2025, 1, 1), date(2025, 1, 20), date(2025, 2, 17), date(2025, 4, 18),
    date(2025, 5, 26), date(2025, 6, 19), date(2025, 7, 3), date(2025, 7, 4),
    date(2025, 9, 1), date(2025, 11, 27), date(2025, 11, 28), date(2025, 12, 25),
    date(2026, 1, 1), date(2026, 1, 19), date(2026, 2, 16), date(2026, 4, 3),
    date(2026, 5, 25), date(2026, 6, 19), date(2026, 7, 3), date(2026, 9, 7),
    date(2026, 11, 26), date(2026, 12, 25),
}

def is_trading_day(d: date) -> bool:
    return d.weekday() < 5 and d not in US_HOLIDAYS

def next_trading_day(d: date) -> date:
    cur = d + timedelta(days=1)
    for _ in range(10):
        if is_trading_day(cur):
            return cur
        cur += timedelta(days=1)
    raise ValueError(f"no trading day after {d}")

def add_trading_days(start: date, n: int) -> date:
    cur = start
    added = 0
    while added < n:
        cur += timedelta(days=1)
        if is_trading_day(cur):
            added += 1
    return cur

HORIZONS = {"1w": 5, "1m": 21, "3m": 63, "6m": 126}
BROAD_BENCHMARK = "SPY"

SECTOR_ETF = {
    "semiconductor": "SOXX", "photonics": "SOXX", "cpo": "SOXX",
    "ai_infra": "SOXX", "ai_compute": "SMH",
    "crypto_miner": "WGMI", "neocloud": "WGMI",
    "space": "UFO", "aerospace": "UFO",
    "social": "SPY", "ecommerce": "SPY",
    "default": "SPY",
}

CACHE_DIR = "/workspace/data/price_cache"
os.makedirs(CACHE_DIR, exist_ok=True)

# ============== 拉数据 ==============
def fetch_polygon_daily(symbol: str) -> List[Dict]:
    """拉 ticker 全历史(从 2024-06-17 起,Polygon Free 2 年深度)。
    缓存到 {symbol}_FULL_HISTORY.json。"""
    cache_file = os.path.join(CACHE_DIR, f"{symbol}_FULL_HISTORY.json")
    if os.path.exists(cache_file):
        return json.load(open(cache_file))
    url = f"https://api.polygon.io/v2/aggs/ticker/{symbol}/range/1/day/2024-06-17/2026-06-15"
    params = {"adjusted": "true", "sort": "asc", "limit": 50000, "apiKey": POLY}
    r = requests.get(url, params=params, timeout=30)
    data = r.json()
    if data.get("status") not in ("OK", "DELAYED") or not data.get("results"):
        return []
    bars = [{
        "date": datetime.fromtimestamp(b["t"]/1000, tz=timezone.utc).strftime("%Y-%m-%d"),
        "o": b["o"], "c": b["c"], "h": b["h"], "l": b["l"], "v": b["v"],
    } for b in data["results"]]
    with open(cache_file, "w") as f:
        json.dump(bars, f)
    return bars

def get_bar_on_or_after(bars: List[Dict], target_date: str) -> Optional[Dict]:
    for bar in bars:
        if bar["date"] >= target_date:
            return bar
    return None


# ============== 单条预测验证 ==============
def verify_one(pred: Dict, asset_bars: List[Dict], bench_bars: List[Dict],
               sector_bars: List[Dict], sector_symbol: str) -> Dict:
    """返回每个 horizon 的完整状态分类。"""
    if not pred.get("published_at"):
        return {"_all": "skipped_no_published_at", "horizons": {
            h: {"status": "skipped_no_published_at"} for h in HORIZONS
        }}
    
    ticker = pred["ticker"]
    direction = pred["direction"]
    pub_at = pred["published_at"]
    cat = pred.get("thesis_category") or "default"
    
    # SIVE 走 SIVEF
    asset_symbol = "SIVEF" if ticker == "SIVE" else ticker
    
    pub_dt = datetime.fromisoformat(pub_at.replace("Z", "+00:00")).date()
    
    # entry_date
    try:
        entry_date = next_trading_day(pub_dt)
    except ValueError:
        return {"_all": "skipped_invalid_pub", "horizons": {h: {"status": "skipped_invalid_pub"} for h in HORIZONS}}
    
    # entry_price
    if not asset_bars:
        return {"_all": "skipped_no_price", "horizons": {h: {"status": "skipped_no_price"} for h in HORIZONS}}
    
    entry_bar = get_bar_on_or_after(asset_bars, entry_date.isoformat())
    if not entry_bar:
        return {"_all": "skipped_no_price", "entry_date": entry_date.isoformat(), "horizons": {h: {"status": "skipped_no_price"} for h in HORIZONS}}
    
    entry_price = entry_bar["o"] if entry_bar["o"] is not None else entry_bar["c"]
    actual_entry_date = entry_bar["date"]
    entry_slip = (datetime.fromisoformat(actual_entry_date).date() - entry_date).days
    
    horizons_results = {}
    for h_name, h_days in HORIZONS.items():
        exit_date = add_trading_days(entry_date, h_days)
        is_pending = exit_date > TODAY
        
        if is_pending:
            horizons_results[h_name] = {
                "status": "pending",
                "exit_date": exit_date.isoformat(),
                "days_to_exit": (exit_date - TODAY).days,
            }
            continue
        
        # exit_price
        exit_bar = get_bar_on_or_after(asset_bars, exit_date.isoformat())
        if not exit_bar:
            horizons_results[h_name] = {
                "status": "skipped_no_price",
                "exit_date": exit_date.isoformat(),
            }
            continue
        
        # benchmark
        bench_entry_bar = get_bar_on_or_after(bench_bars, entry_date.isoformat())
        bench_exit_bar = get_bar_on_or_after(bench_bars, exit_date.isoformat())
        
        if not bench_entry_bar or not bench_exit_bar:
            horizons_results[h_name] = {
                "status": "unverifiable_no_benchmark",
                "exit_date": exit_date.isoformat(),
                "actual_exit_date": exit_bar["date"],
            }
            continue
        
        bench_return = (bench_exit_bar["c"] - bench_entry_bar["c"]) / bench_entry_bar["c"]
        
        # sector
        if sector_symbol == BROAD_BENCHMARK or sector_bars is bench_bars:
            sector_return = bench_return
        else:
            sec_entry = get_bar_on_or_after(sector_bars, entry_date.isoformat())
            sec_exit = get_bar_on_or_after(sector_bars, exit_date.isoformat())
            if sec_entry and sec_exit:
                sector_return = (sec_exit["c"] - sec_entry["c"]) / sec_entry["c"]
            else:
                sector_return = None
        
        # raw_return
        raw_return = (exit_bar["c"] - entry_price) / entry_price
        if direction == "short":
            raw_return = -raw_return
        if direction == "neutral":
            horizons_results[h_name] = {
                "status": "skipped_neutral",
                "exit_date": exit_date.isoformat(),
            }
            continue
        
        excess = raw_return - bench_return
        excess_sector = (raw_return - sector_return) if sector_return is not None else None
        hit = (excess > 0)
        hit_abs = (raw_return > 0)
        
        status = "resolved_hit" if hit else "resolved_miss"
        horizons_results[h_name] = {
            "status": status,
            "exit_date": exit_date.isoformat(),
            "actual_exit_date": exit_bar["date"],
            "exit_price": exit_bar["c"],
            "raw_return": round(raw_return, 6),
            "benchmark_return": round(bench_return, 6),
            "excess_return": round(excess, 6),
            "excess_vs_sector": round(excess_sector, 6) if excess_sector is not None else None,
            "hit": hit,
            "hit_absolute": hit_abs,
        }
    
    return {
        "entry_date": entry_date.isoformat(),
        "actual_entry_date": actual_entry_date,
        "entry_slip_days": entry_slip,
        "entry_price": entry_price,
        "asset_symbol": asset_symbol,
        "sector_benchmark": sector_symbol,
        "horizons": horizons_results,
    }


# ============== 主流程 ==============
def main():
    conn = sqlite3.connect("/workspace/data/signalboard_full.db")
    c = conn.cursor()
    
    # 1. 拉所有 414 unique ticker FULL_HISTORY
    print("=" * 80)
    print(f"P3-2 全量验证 (414 ticker + 3983 predictions + 4 horizons = ~16000 verify cells)")
    print("=" * 80)
    
    sql = """SELECT DISTINCT p.ticker 
             FROM predictions p 
             WHERE p.price_source_available = 1"""
    tickers = [r[0] for r in c.execute(sql).fetchall()]
    print(f"unique tickers (price_source_available=1): {len(tickers)}")
    
    # 拉每个 ticker FULL_HISTORY
    asset_bars_cache = {}  # symbol → bars
    n_ok = 0
    n_fail = 0
    t0 = time.time()
    for i, t in enumerate(tickers, 1):
        # SIVE → SIVEF
        sym = "SIVEF" if t == "SIVE" else t
        bars = fetch_polygon_daily(sym)
        asset_bars_cache[sym] = bars
        if bars:
            n_ok += 1
        else:
            n_fail += 1
        if i % 30 == 0:
            elapsed = time.time() - t0
            rate = i / elapsed
            eta = (len(tickers) - i) / rate if rate > 0 else 0
            print(f"  [{i}/{len(tickers)}] elapsed={elapsed:.0f}s rate={rate:.2f}/s ok={n_ok} fail={n_fail} eta={eta:.0f}s", flush=True)
        time.sleep(12.5)  # 5 req/min
    
    # 拉 benchmark FULL_HISTORY
    bench_symbols = set([BROAD_BENCHMARK]) | set(SECTOR_ETF.values())
    print(f"\n拉 {len(bench_symbols)} 基准 FULL_HISTORY: {bench_symbols}")
    bench_bars_cache = {}
    for s in bench_symbols:
        bars = fetch_polygon_daily(s)
        bench_bars_cache[s] = bars
        print(f"  {s:6s}: {len(bars)} bars")
        time.sleep(12.5)
    
    # 2. 拉所有 predictions
    print()
    print("=" * 80)
    print("拉 predictions + 验证")
    print("=" * 80)
    
    sql = """
    SELECT p.prediction_id, p.post_id, p.ticker, p.direction, p.horizon,
           p.thesis_category, p.thesis_summary, p.conviction, 
           rp.published_at
    FROM predictions p JOIN raw_posts rp ON p.post_id = rp.post_id
    WHERE p.price_source_available = 1
    """
    rows = c.execute(sql).fetchall()
    print(f"待验证 predictions: {len(rows)}")
    
    # 准备 verifications 表 upsert
    c.execute("""
    CREATE TABLE IF NOT EXISTS verifications (
        prediction_id         TEXT PRIMARY KEY,
        ticker                TEXT,
        direction             TEXT,
        horizon_input         TEXT,
        thesis_category       TEXT,
        published_at          TEXT,
        asset_symbol          TEXT,
        entry_date_planned    TEXT,
        entry_date_actual     TEXT,
        entry_slip_days       INTEGER,
        entry_price           REAL,
        sector_benchmark      TEXT,
        h_1w_status           TEXT,
        h_1w_exit_date        TEXT,
        h_1w_actual_exit      TEXT,
        h_1w_exit_price       REAL,
        h_1w_raw_return       REAL,
        h_1w_benchmark_return REAL,
        h_1w_excess_return    REAL,
        h_1w_sector_excess    REAL,
        h_1w_hit              INTEGER,
        h_1m_status           TEXT,
        h_1m_exit_date        TEXT,
        h_1m_actual_exit      TEXT,
        h_1m_exit_price       REAL,
        h_1m_raw_return       REAL,
        h_1m_benchmark_return REAL,
        h_1m_excess_return    REAL,
        h_1m_sector_excess    REAL,
        h_1m_hit              INTEGER,
        h_3m_status           TEXT,
        h_3m_exit_date        TEXT,
        h_3m_actual_exit      TEXT,
        h_3m_exit_price       REAL,
        h_3m_raw_return       REAL,
        h_3m_benchmark_return REAL,
        h_3m_excess_return    REAL,
        h_3m_sector_excess    REAL,
        h_3m_hit              INTEGER,
        h_6m_status           TEXT,
        h_6m_exit_date        TEXT,
        h_6m_actual_exit      TEXT,
        h_6m_exit_price       REAL,
        h_6m_raw_return       REAL,
        h_6m_benchmark_return REAL,
        h_6m_excess_return    REAL,
        h_6m_sector_excess    REAL,
        h_6m_hit              INTEGER,
        verified_at           TEXT
    )
    """)
    c.execute("DELETE FROM verifications")
    conn.commit()
    
    # 跑 3983
    n_done = 0
    t_start = time.time()
    
    for row in rows:
        pid, post_id, ticker, direction, horizon_input, cat, thesis, conv, pub_at = row
        pred = {
            "prediction_id": pid, "post_id": post_id, "ticker": ticker,
            "direction": direction, "thesis_category": cat, "published_at": pub_at,
        }
        
        asset_sym = "SIVEF" if ticker == "SIVE" else ticker
        asset_bars = asset_bars_cache.get(asset_sym, [])
        sector_sym = SECTOR_ETF.get(cat, SECTOR_ETF["default"])
        sector_bars = bench_bars_cache.get(sector_sym, bench_bars_cache[BROAD_BENCHMARK])
        
        result = verify_one(pred, asset_bars, bench_bars_cache[BROAD_BENCHMARK], sector_bars, sector_sym)
        
        # 写表
        rec = {"prediction_id": pid, "ticker": ticker, "direction": direction, 
               "horizon_input": horizon_input, "thesis_category": cat, "published_at": pub_at,
               "asset_symbol": asset_sym, "sector_benchmark": sector_sym,
               "entry_date_planned": result.get("entry_date"),
               "entry_date_actual": result.get("actual_entry_date"),
               "entry_slip_days": result.get("entry_slip_days"),
               "entry_price": result.get("entry_price"),
               "verified_at": datetime.now(timezone.utc).isoformat()}
        
        for h_name in HORIZONS:
            h = result["horizons"].get(h_name, {})
            rec[f"h_{h_name}_status"] = h.get("status")
            rec[f"h_{h_name}_exit_date"] = h.get("exit_date")
            rec[f"h_{h_name}_actual_exit"] = h.get("actual_exit_date")
            rec[f"h_{h_name}_exit_price"] = h.get("exit_price")
            rec[f"h_{h_name}_raw_return"] = h.get("raw_return")
            rec[f"h_{h_name}_benchmark_return"] = h.get("benchmark_return")
            rec[f"h_{h_name}_excess_return"] = h.get("excess_return")
            rec[f"h_{h_name}_sector_excess"] = h.get("excess_vs_sector")
            rec[f"h_{h_name}_hit"] = h.get("hit")
        
        # 写一行
        cols = list(rec.keys())
        placeholders = ",".join("?" for _ in cols)
        col_names = ",".join(cols)
        try:
            c.execute(f"INSERT INTO verifications ({col_names}) VALUES ({placeholders})", [rec[c] for c in cols])
        except Exception as e:
            print(f"  insert fail {pid}: {e}")
        
        n_done += 1
        if n_done % 500 == 0:
            elapsed = time.time() - t_start
            rate = n_done / elapsed
            eta = (len(rows) - n_done) / rate if rate > 0 else 0
            print(f"  [{n_done}/{len(rows)}] elapsed={elapsed:.0f}s rate={rate:.0f}/s eta={eta:.0f}s", flush=True)
    
    conn.commit()
    elapsed = time.time() - t0
    print(f"\n✅ 写 verifications {n_done} 行 (耗时 {elapsed:.0f}s)")
    
    # 3. 可验证性体检报告
    print()
    print("=" * 80)
    print("可验证性体检报告")
    print("=" * 80)
    
    # 各 horizon 状态分布
    print("\n各 horizon 状态分布:")
    print(f"{'horizon':6s}  {'resolved_hit':14s}  {'resolved_miss':14s}  {'pending':10s}  {'unverifiable':14s}  {'skipped':10s}  {'total'}")
    for h_name in HORIZONS:
        sql = f"SELECT h_{h_name}_status, count(*) FROM verifications GROUP BY h_{h_name}_status"
        dist = dict(c.execute(sql).fetchall())
        rh = dist.get("resolved_hit", 0)
        rm = dist.get("resolved_miss", 0)
        pe = dist.get("pending", 0)
        un = dist.get("unverifiable_no_benchmark", 0)
        sk = sum(v for k, v in dist.items() if k.startswith("skipped_"))
        total = sum(dist.values())
        print(f"  {h_name:4s}  {rh:14d}  {rm:14d}  {pe:10d}  {un:14d}  {sk:10d}  {total}")
    
    # 总计:resolved / pending / unverifiable / skipped
    print()
    print("总状态(所有 horizon 求和):")
    
    # 用 SQL UNION ALL
    total_resolved_hit = 0
    total_resolved_miss = 0
    total_pending = 0
    total_unverifiable = 0
    total_skipped = 0
    for h_name in HORIZONS:
        sql = f"SELECT h_{h_name}_status, count(*) FROM verifications GROUP BY h_{h_name}_status"
        for s, n in c.execute(sql).fetchall():
            if s == "resolved_hit":
                total_resolved_hit += n
            elif s == "resolved_miss":
                total_resolved_miss += n
            elif s == "pending":
                total_pending += n
            elif s == "unverifiable_no_benchmark":
                total_unverifiable += n
            elif s and s.startswith("skipped_"):
                total_skipped += n
    
    total_cells = total_resolved_hit + total_resolved_miss + total_pending + total_unverifiable + total_skipped
    print(f"  resolved_hit:           {total_resolved_hit:5d}")
    print(f"  resolved_miss:          {total_resolved_miss:5d}")
    print(f"  pending:                {total_pending:5d}")
    print(f"  unverifiable_no_bench:  {total_unverifiable:5d}")
    print(f"  skipped (any):          {total_skipped:5d}")
    print(f"  TOTAL:                  {total_cells:5d}")
    print()
    print(f"  predictions 总数: {len(rows)}")
    print(f"  cells 总数(4 horizon × pred): {len(rows) * 4}")
    print(f"  实际可验证(计入胜率,resolved_hit+miss): {total_resolved_hit + total_resolved_miss} ({ (total_resolved_hit+total_resolved_miss)/total_cells*100:.1f}%)")
    print(f"  全量 hit_rate(excess>0): {total_resolved_hit/(total_resolved_hit+total_resolved_miss)*100:.1f}%" if (total_resolved_hit+total_resolved_miss) else "  全量 hit_rate: N/A")
    
    # skipped_no_price ticker 清单
    print()
    print("skipped_no_price 的 ticker 清单(按 predictions 数降序):")
    sql = """
    SELECT ticker, count(*) as n,
        sum(CASE WHEN h_1w_status='skipped_no_price' THEN 1 ELSE 0 END) as h_1w,
        sum(CASE WHEN h_1m_status='skipped_no_price' THEN 1 ELSE 0 END) as h_1m,
        sum(CASE WHEN h_3m_status='skipped_no_price' THEN 1 ELSE 0 END) as h_3m,
        sum(CASE WHEN h_6m_status='skipped_no_price' THEN 1 ELSE 0 END) as h_6m
    FROM verifications
    WHERE h_1w_status='skipped_no_price' OR h_1m_status='skipped_no_price' 
       OR h_3m_status='skipped_no_price' OR h_6m_status='skipped_no_price'
    GROUP BY ticker
    ORDER BY n DESC
    """
    skipped_tickers = c.execute(sql).fetchall()
    print(f"  共 {len(skipped_tickers)} ticker")
    for r in skipped_tickers[:30]:
        print(f"    {r[0]:10s}  pred={r[1]:3d}  1w={r[2]:3d}  1m={r[3]:3d}  3m={r[4]:3d}  6m={r[5]:3d}")
    if len(skipped_tickers) > 30:
        print(f"    ... (还有 {len(skipped_tickers)-30} 个)")
    
    # benchmark 缺失的细节
    print()
    print("unverifiable_no_benchmark 的 ticker 清单:")
    sql = """
    SELECT ticker, count(*) as n
    FROM verifications
    WHERE h_1w_status='unverifiable_no_benchmark' OR h_1m_status='unverifiable_no_benchmark'
       OR h_3m_status='unverifiable_no_benchmark' OR h_6m_status='unverifiable_no_benchmark'
    GROUP BY ticker ORDER BY n DESC
    """
    unb_tickers = c.execute(sql).fetchall()
    print(f"  共 {len(unb_tickers)} ticker")
    for r in unb_tickers[:20]:
        print(f"    {r[0]:10s}  cells={r[1]}")
    
    # 落报告
    report = []
    report.append("# Phase 3 P3-2 全量验证 - 可验证性体检报告")
    report.append("")
    report.append(f"**运行时间**: {datetime.now(timezone.utc).isoformat()}")
    report.append(f"**耗时**: {elapsed:.0f}s ({elapsed/60:.1f}min)")
    report.append(f"**polygon full history**: 2024-06-17 ~ 2026-06-12")
    report.append("")
    report.append("## 1. 各 horizon 状态分布")
    report.append("")
    report.append("| horizon | resolved_hit | resolved_miss | pending | unverifiable | skipped | total |")
    report.append("|---|---|---|---|---|---|---|")
    for h_name in HORIZONS:
        sql = f"SELECT h_{h_name}_status, count(*) FROM verifications GROUP BY h_{h_name}_status"
        dist = dict(c.execute(sql).fetchall())
        rh = dist.get("resolved_hit", 0)
        rm = dist.get("resolved_miss", 0)
        pe = dist.get("pending", 0)
        un = dist.get("unverifiable_no_benchmark", 0)
        sk = sum(v for k, v in dist.items() if k.startswith("skipped_"))
        total = sum(dist.values())
        report.append(f"| **{h_name}** | {rh} | {rm} | {pe} | {un} | {sk} | {total} |")
    report.append("")
    report.append("## 2. 总状态(4 horizon × 3983 predictions = 15932 cells)")
    report.append("")
    report.append("| 状态 | cells | 占比 |")
    report.append("|---|---|---|")
    report.append(f"| resolved_hit | {total_resolved_hit} | {total_resolved_hit/total_cells*100:.1f}% |")
    report.append(f"| resolved_miss | {total_resolved_miss} | {total_resolved_miss/total_cells*100:.1f}% |")
    report.append(f"| pending | {total_pending} | {total_pending/total_cells*100:.1f}% |")
    report.append(f"| unverifiable_no_benchmark | {total_unverifiable} | {total_unverifiable/total_cells*100:.1f}% |")
    report.append(f"| skipped (any) | {total_skipped} | {total_skipped/total_cells*100:.1f}% |")
    report.append(f"| **TOTAL** | **{total_cells}** | **100%** |")
    report.append("")
    report.append("## 3. 关键统计")
    report.append("")
    report.append(f"- **可验证(计入胜率,resolved_hit+miss)**: {total_resolved_hit + total_resolved_miss} cells / {len(rows)} predictions ({(total_resolved_hit+total_resolved_miss)/total_cells*100:.1f}%)")
    if total_resolved_hit + total_resolved_miss:
        report.append(f"- **全量 hit_rate**(excess>0): **{total_resolved_hit/(total_resolved_hit+total_resolved_miss)*100:.1f}%**")
    report.append(f"- predictions 总数: {len(rows)}")
    report.append(f"- tickers 拉全历史: {n_ok} OK / {n_fail} fail")
    report.append("")
    report.append("## 4. skipped_no_price ticker 清单")
    report.append("")
    if skipped_tickers:
        report.append(f"共 {len(skipped_tickers)} ticker 至少 1 个 horizon 缺个股行情:")
        report.append("")
        report.append("| ticker | pred 总数 | 1w | 1m | 3m | 6m |")
        report.append("|---|---|---|---|---|---|")
        for r in skipped_tickers:
            report.append(f"| `{r[0]}` | {r[1]} | {r[2]} | {r[3]} | {r[4]} | {r[5]} |")
    else:
        report.append("无 skipped_no_price ticker。")
    report.append("")
    report.append("## 5. unverifiable_no_benchmark ticker 清单")
    report.append("")
    if unb_tickers:
        report.append(f"共 {len(unb_tickers)} ticker 至少 1 个 horizon 缺基准(SPY/SOXX/SMH 拉不到):")
        report.append("")
        report.append("| ticker | cells |")
        report.append("|---|---|")
        for r in unb_tickers:
            report.append(f"| `{r[0]}` | {r[1]} |")
    else:
        report.append("**零 unverifiable**。所有 horizon 都有基准,意味着 FULL_HISTORY cache 完整。")
    report.append("")
    report.append("## 6. 结论")
    report.append("")
    n_resolved = total_resolved_hit + total_resolved_miss
    if n_resolved < 1000:
        report.append(f"⚠️ **可验证样本量偏低**({n_resolved} cells)。建议:")
        report.append("- 接受 0% 系统性缺失即可出记分牌,但分母小,统计意义弱")
        report.append("- 等更多 horizon 自然到期(1m 变 3m, 3m 变 6m)再出最终记分牌")
    else:
        report.append(f"✅ **可验证样本量 {n_resolved} cells 健康**。可进 P3-3 记分牌聚合。")
    report.append("")
    
    content = "\n".join(report)
    with open("/workspace/outputs/phase3_p2_verify_all_health.md", "w", encoding="utf-8") as f:
        f.write(content)
    print()
    print(f"✅ 落 outputs/phase3_p2_verify_all_health.md ({len(content)} chars)")
    conn.close()

if __name__ == "__main__":
    main()
