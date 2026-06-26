"""Phase 3 P3-2 全量验证脚本(分批 + 持久化 log 版)

修复 sandbox 重启导致脚本死问题:
1. Log 输出到 /workspace/logs/(NFS 持久)
2. 分批跑:每 30 ticker 写一次 verifications 表 + commit
3. 如果中途死,重启脚本能从 cache 继续(只拉 missing)
4. 分阶段 commit verifications 表(防止大批 insert 中断丢失)
"""
from __future__ import annotations
import os, json, time, sys
import sqlite3
import requests
from datetime import datetime, timedelta, timezone, date
from typing import Optional, Tuple, List, Dict, Any

POLY = os.environ.get("POLYGON_API_KEY", "")
if not POLY:
    print("ERROR: POLYGON_API_KEY not set", flush=True)
    sys.exit(1)

TODAY = date.today()  # 动态取值,2026-06-15 改为动态获取
LOG_PATH = "/workspace/logs/p3p2_verify_all.log"
os.makedirs(os.path.dirname(LOG_PATH), exist_ok=True)

# 重新打开 log 到 file + stdout
_log = open(LOG_PATH, "a", buffering=1)  # line buffered
def log(msg):
    _log.write(f"[{datetime.now(timezone.utc).isoformat()}] {msg}\n")
    _log.flush()
    print(msg, flush=True)

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

def fetch_polygon_daily(symbol: str) -> List[Dict]:
    cache_file = os.path.join(CACHE_DIR, f"{symbol}_FULL_HISTORY.json")
    if os.path.exists(cache_file):
        return json.load(open(cache_file))
    url = f"https://api.polygon.io/v2/aggs/ticker/{symbol}/range/1/day/2024-06-17/2026-06-15"
    params = {"adjusted": "true", "sort": "asc", "limit": 50000, "apiKey": POLY}
    try:
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
    except Exception as e:
        log(f"  fetch_polygon_daily error {symbol}: {e}")
        return []

def get_bar_on_or_after(bars: List[Dict], target_date: str) -> Optional[Dict]:
    for bar in bars:
        if bar["date"] >= target_date:
            return bar
    return None


def verify_one(pred: Dict, asset_bars, bench_bars, sector_bars, sector_symbol) -> Dict:
    if not pred.get("published_at"):
        return {"_all": "skipped_no_published_at", "horizons": {h: {"status": "skipped_no_published_at"} for h in HORIZONS}}
    
    ticker = pred["ticker"]
    direction = pred["direction"]
    pub_at = pred["published_at"]
    cat = pred.get("thesis_category") or "default"
    asset_symbol = "SIVEF" if ticker == "SIVE" else ticker
    
    pub_dt = datetime.fromisoformat(pub_at.replace("Z", "+00:00")).date()
    
    try:
        entry_date = next_trading_day(pub_dt)
    except ValueError:
        return {"_all": "skipped_invalid_pub", "horizons": {h: {"status": "skipped_invalid_pub"} for h in HORIZONS}}
    
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
        
        exit_bar = get_bar_on_or_after(asset_bars, exit_date.isoformat())
        if not exit_bar:
            horizons_results[h_name] = {"status": "skipped_no_price", "exit_date": exit_date.isoformat()}
            continue
        
        bench_entry_bar = get_bar_on_or_after(bench_bars, entry_date.isoformat())
        bench_exit_bar = get_bar_on_or_after(bench_bars, exit_date.isoformat())
        
        if not bench_entry_bar or not bench_exit_bar:
            horizons_results[h_name] = {"status": "unverifiable_no_benchmark", "exit_date": exit_date.isoformat(), "actual_exit_date": exit_bar["date"]}
            continue
        
        bench_return = (bench_exit_bar["c"] - bench_entry_bar["c"]) / bench_entry_bar["c"]
        
        if sector_symbol == BROAD_BENCHMARK or sector_bars is bench_bars:
            sector_return = bench_return
        else:
            sec_entry = get_bar_on_or_after(sector_bars, entry_date.isoformat())
            sec_exit = get_bar_on_or_after(sector_bars, exit_date.isoformat())
            if sec_entry and sec_exit:
                sector_return = (sec_exit["c"] - sec_entry["c"]) / sec_entry["c"]
            else:
                sector_return = None
        
        raw_return = (exit_bar["c"] - entry_price) / entry_price
        if direction == "short":
            raw_return = -raw_return
        if direction == "neutral":
            horizons_results[h_name] = {"status": "skipped_neutral", "exit_date": exit_date.isoformat()}
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


def main():
    log(f"=== P3-2 全量验证 启动 ===")
    log(f"log path: {LOG_PATH}")
    
    conn = sqlite3.connect("/workspace/data/signalboard_full.db", timeout=30)
    c = conn.cursor()
    
    sql = "SELECT DISTINCT ticker FROM predictions WHERE price_source_available=1"
    tickers = sorted([r[0] for r in c.execute(sql)])
    log(f"unique tickers: {len(tickers)}")
    
    # 1. 拉所有 ticker FULL_HISTORY(已有 cache 跳过)
    asset_bars_cache = {}
    n_ok = 0
    n_fail = 0
    n_cached = 0
    t0 = time.time()
    for i, t in enumerate(tickers, 1):
        sym = "SIVEF" if t == "SIVE" else t
        cache_file = os.path.join(CACHE_DIR, f"{sym}_FULL_HISTORY.json")
        if os.path.exists(cache_file):
            asset_bars_cache[sym] = json.load(open(cache_file))
            n_cached += 1
            continue
        bars = fetch_polygon_daily(sym)
        asset_bars_cache[sym] = bars
        if bars:
            n_ok += 1
        else:
            n_fail += 1
        if i % 20 == 0:
            elapsed = time.time() - t0
            eta = (len(tickers) - i) * 12.5
            log(f"  [{i}/{len(tickers)}] elapsed={elapsed:.0f}s cached={n_cached} new_ok={n_ok} new_fail={n_fail} eta={eta:.0f}s")
        time.sleep(12.5)
    
    log(f"asset_bars_cache: {len(asset_bars_cache)} ticker (cached={n_cached}, new={n_ok+ n_fail})")
    
    # 2. 拉 benchmark
    bench_symbols = set([BROAD_BENCHMARK]) | set(SECTOR_ETF.values())
    bench_bars_cache = {}
    for s in bench_symbols:
        bars = fetch_polygon_daily(s)
        bench_bars_cache[s] = bars
        log(f"  benchmark {s}: {len(bars)} bars")
        time.sleep(12.5)
    
    # 3. 拉 predictions + 验证 + 分批写表
    sql = """
    SELECT p.prediction_id, p.post_id, p.ticker, p.direction, p.horizon,
           p.thesis_category, p.thesis_summary, p.conviction, rp.published_at
    FROM predictions p JOIN raw_posts rp ON p.post_id = rp.post_id
    WHERE p.price_source_available=1
    """
    rows = c.execute(sql).fetchall()
    log(f"待验证 predictions: {len(rows)}")
    
    # 建表 + 清空(只跑一次)
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
    log("verifications 表重建完成")
    
    n_done = 0
    t_start = time.time()
    BATCH_SIZE = 100  # 每 100 条 commit 一次
    
    for row in rows:
        pid, post_id, ticker, direction, horizon_input, cat, thesis, conv, pub_at = row
        pred = {
            "prediction_id": pid, "post_id": post_id, "ticker": ticker,
            "direction": direction, "thesis_category": cat, "published_at": pub_at,
        }
        
        asset_sym = "SIVEF" if ticker == "SIVE" else ticker
        asset_bars = asset_bars_cache.get(asset_sym, [])
        sector_sym = SECTOR_ETF.get(cat, SECTOR_ETF["default"])
        sector_bars = bench_bars_cache.get(sector_sym, bench_bars_cache.get(BROAD_BENCHMARK, []))
        
        result = verify_one(pred, asset_bars, bench_bars_cache.get(BROAD_BENCHMARK, []), sector_bars, sector_sym)
        
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
        
        cols = list(rec.keys())
        placeholders = ",".join("?" for _ in cols)
        col_names = ",".join(cols)
        try:
            c.execute(f"INSERT INTO verifications ({col_names}) VALUES ({placeholders})", [rec[c] for c in cols])
        except Exception as e:
            log(f"  insert fail {pid}: {e}")
        
        n_done += 1
        if n_done % BATCH_SIZE == 0:
            conn.commit()
            elapsed = time.time() - t_start
            log(f"  [{n_done}/{len(rows)}] committed batch, elapsed={elapsed:.0f}s")
    
    conn.commit()
    elapsed = time.time() - t0
    log(f"✅ verifications 写入完成 {n_done} 行 (耗时 {elapsed:.0f}s)")
    
    # 4. 体检报告
    log("=== 生成体检报告 ===")
    
    print("\n" + "=" * 80)
    print("可验证性体检报告")
    print("=" * 80)
    
    # 各 horizon 状态分布
    print("\n各 horizon 状态分布:")
    print(f"{'horizon':8s}  {'hit':6s}  {'miss':6s}  {'pending':8s}  {'unverif':8s}  {'skipped':8s}  {'total'}")
    summary = {}
    for h_name in HORIZONS:
        sql = f"SELECT h_{h_name}_status, count(*) FROM verifications GROUP BY h_{h_name}_status"
        dist = dict(c.execute(sql).fetchall())
        rh = dist.get("resolved_hit", 0)
        rm = dist.get("resolved_miss", 0)
        pe = dist.get("pending", 0)
        un = dist.get("unverifiable_no_benchmark", 0)
        sk = sum(v for k, v in dist.items() if k and k.startswith("skipped_"))
        total = sum(dist.values())
        summary[h_name] = {"hit": rh, "miss": rm, "pending": pe, "unverifiable": un, "skipped": sk, "total": total}
        print(f"  {h_name:6s}  {rh:6d}  {rm:6d}  {pe:8d}  {un:8d}  {sk:8d}  {total}")
    
    # 总状态
    total_hit = sum(s["hit"] for s in summary.values())
    total_miss = sum(s["miss"] for s in summary.values())
    total_pending = sum(s["pending"] for s in summary.values())
    total_unverifiable = sum(s["unverifiable"] for s in summary.values())
    total_skipped = sum(s["skipped"] for s in summary.values())
    total_cells = sum(s["total"] for s in summary.values())
    
    print()
    print(f"总状态({total_cells} cells):")
    print(f"  resolved_hit:           {total_hit:5d} ({total_hit/total_cells*100:.1f}%)")
    print(f"  resolved_miss:          {total_miss:5d} ({total_miss/total_cells*100:.1f}%)")
    print(f"  pending:                {total_pending:5d} ({total_pending/total_cells*100:.1f}%)")
    print(f"  unverifiable_no_bench:  {total_unverifiable:5d} ({total_unverifiable/total_cells*100:.1f}%)")
    print(f"  skipped (any):          {total_skipped:5d} ({total_skipped/total_cells*100:.1f}%)")
    print()
    print(f"  predictions 总数: {len(rows)}")
    n_resolved = total_hit + total_miss
    print(f"  可验证(计入胜率,resolved_hit+miss): {n_resolved} cells ({n_resolved/total_cells*100:.1f}%)")
    if n_resolved:
        print(f"  全量 hit_rate(excess>0): {total_hit/n_resolved*100:.1f}%")
    
    # skipped_no_price ticker 清单
    print("\nskipped_no_price ticker 清单:")
    sql = """
    SELECT ticker, count(*) as n,
        sum(CASE WHEN h_1w_status='skipped_no_price' THEN 1 ELSE 0 END) as h_1w,
        sum(CASE WHEN h_1m_status='skipped_no_price' THEN 1 ELSE 0 END) as h_1m,
        sum(CASE WHEN h_3m_status='skipped_no_price' THEN 1 ELSE 0 END) as h_3m,
        sum(CASE WHEN h_6m_status='skipped_no_price' THEN 1 ELSE 0 END) as h_6m
    FROM verifications
    WHERE h_1w_status='skipped_no_price' OR h_1m_status='skipped_no_price' 
       OR h_3m_status='skipped_no_price' OR h_6m_status='skipped_no_price'
    GROUP BY ticker ORDER BY n DESC
    """
    skipped_tickers = c.execute(sql).fetchall()
    print(f"  共 {len(skipped_tickers)} ticker")
    for r in skipped_tickers[:30]:
        print(f"    {r[0]:10s}  pred={r[1]:3d}  1w={r[2]:3d}  1m={r[3]:3d}  3m={r[4]:3d}  6m={r[5]:3d}")
    
    # unverifiable_no_benchmark
    print("\nunverifiable_no_benchmark ticker:")
    sql = """
    SELECT ticker, count(*) as n
    FROM verifications
    WHERE h_1w_status='unverifiable_no_benchmark' OR h_1m_status='unverifiable_no_benchmark'
       OR h_3m_status='unverifiable_no_benchmark' OR h_6m_status='unverifiable_no_benchmark'
    GROUP BY ticker ORDER BY n DESC
    """
    unb_tickers = c.execute(sql).fetchall()
    print(f"  共 {len(unb_tickers)} ticker")
    for r in unb_tickers[:30]:
        print(f"    {r[0]:10s}  cells={r[1]}")
    
    # 落报告 markdown
    report = []
    report.append("# Phase 3 P3-2 全量验证 - 可验证性体检报告")
    report.append("")
    report.append(f"**运行时间**: {datetime.now(timezone.utc).isoformat()}")
    report.append(f"**耗时**: {elapsed:.0f}s ({elapsed/60:.1f}min)")
    report.append("")
    report.append("## 1. 各 horizon 状态分布")
    report.append("")
    report.append("| horizon | resolved_hit | resolved_miss | pending | unverifiable | skipped | total |")
    report.append("|---|---|---|---|---|---|---|")
    for h_name in HORIZONS:
        s = summary[h_name]
        report.append(f"| **{h_name}** | {s['hit']} | {s['miss']} | {s['pending']} | {s['unverifiable']} | {s['skipped']} | {s['total']} |")
    report.append("")
    report.append("## 2. 总状态(4 horizon × 3983 predictions = 15932 cells)")
    report.append("")
    report.append("| 状态 | cells | 占比 |")
    report.append("|---|---|---|")
    report.append(f"| resolved_hit | {total_hit} | {total_hit/total_cells*100:.1f}% |")
    report.append(f"| resolved_miss | {total_miss} | {total_miss/total_cells*100:.1f}% |")
    report.append(f"| pending | {total_pending} | {total_pending/total_cells*100:.1f}% |")
    report.append(f"| unverifiable_no_benchmark | {total_unverifiable} | {total_unverifiable/total_cells*100:.1f}% |")
    report.append(f"| skipped (any) | {total_skipped} | {total_skipped/total_cells*100:.1f}% |")
    report.append(f"| **TOTAL** | **{total_cells}** | **100%** |")
    report.append("")
    report.append("## 3. 关键统计")
    report.append("")
    report.append(f"- **可验证(计入胜率,resolved_hit+miss)**: {n_resolved} cells ({n_resolved/total_cells*100:.1f}%)")
    if n_resolved:
        report.append(f"- **全量 hit_rate**(excess>0): **{total_hit/n_resolved*100:.1f}%**")
    report.append(f"- predictions 总数: {len(rows)}")
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
        report.append(f"共 {len(unb_tickers)} ticker 至少 1 个 horizon 缺基准:")
        report.append("")
        report.append("| ticker | cells |")
        report.append("|---|---|")
        for r in unb_tickers:
            report.append(f"| `{r[0]}` | {r[1]} |")
    else:
        report.append("**零 unverifiable**。")
    report.append("")
    
    content = "\n".join(report)
    with open("/workspace/outputs/phase3_p2_verify_all_health.md", "w", encoding="utf-8") as f:
        f.write(content)
    log(f"✅ 落 outputs/phase3_p2_verify_all_health.md ({len(content)} chars)")
    
    conn.close()
    log("=== DONE ===")

if __name__ == "__main__":
    main()
