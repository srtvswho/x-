"""Phase 3 P3-1: 标的→yfinance 解析 + 覆盖率测试

目标:
1. market_config: 市场→后缀/基准/币种
2. ticker→yfinance symbol 解析(加后缀/特判)
3. yfinance 拉 5d 日线(快速存在性测试)
4. 报告:覆盖率 + 按 market 分层 + unresolved 清单

实现:
- 3 worker 并发(yfinance 限流 ~200 req/min,3 worker ≈ 60 req/min 安全)
- 用最近 5 个交易日数据(只验证存在性,不拉全历史)
- 失败 ticker 进 unresolved_price
"""
import sqlite3, json, time, os, sys
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timezone, timedelta
sys.path.insert(0, "/workspace")

DB = "data/signalboard_full.db"

# ============== market_config ==============
MARKET_CONFIG = {
    "美股":   {"suffix": "",     "yfinance": "",     "benchmark": "^GSPC",  "currency": "USD", "tz": "US/Eastern",   "label": "US"},
    "SE":    {"suffix": ".ST",  "yfinance": ".ST",  "benchmark": "^OMX",   "currency": "SEK", "tz": "Europe/Stockholm", "label": "SE"},
    "OTC":   {"suffix": "",     "yfinance": "",     "benchmark": "^SP400", "currency": "USD", "tz": "US/Eastern",   "label": "OTC"},
    "TW":    {"suffix": ".TW",  "yfinance": ".TW",  "benchmark": "^TWII",  "currency": "TWD", "tz": "Asia/Taipei",   "label": "TW"},
    "KR":    {"suffix": ".KS",  "yfinance": ".KS",  "benchmark": "^KS11",  "currency": "KRW", "tz": "Asia/Seoul",    "label": "KR"},
    "KRX":   {"suffix": ".KQ",  "yfinance": ".KQ",  "benchmark": "^KOSDAQ", "currency": "KRW", "tz": "Asia/Seoul",   "label": "KRX"},
    "JP":    {"suffix": ".T",   "yfinance": ".T",   "benchmark": "^N225",  "currency": "JPY", "tz": "Asia/Tokyo",    "label": "JP"},
    "LSE":   {"suffix": ".L",   "yfinance": ".L",   "benchmark": "^FTSE",  "currency": "GBP", "tz": "Europe/London", "label": "LSE"},
    "CA":    {"suffix": ".TO",  "yfinance": ".TO",  "benchmark": "^GSPTSE", "currency": "CAD", "tz": "America/Toronto", "label": "CA"},
    "ASX":   {"suffix": ".AX",  "yfinance": ".AX",  "benchmark": "^AXJO",  "currency": "AUD", "tz": "Australia/Sydney", "label": "ASX"},
    "TYO":   {"suffix": ".T",   "yfinance": ".T",   "benchmark": "^N225",  "currency": "JPY", "tz": "Asia/Tokyo",   "label": "JP"},
    "JPX":   {"suffix": ".T",   "yfinance": ".T",   "benchmark": "^N225",  "currency": "JPY", "tz": "Asia/Tokyo",   "label": "JP"},
    "EPA":   {"suffix": ".PA",  "yfinance": ".PA",  "benchmark": "^FCHI",  "currency": "EUR", "tz": "Europe/Paris", "label": "EPA"},
    "FR":    {"suffix": ".PA",  "yfinance": ".PA",  "benchmark": "^FCHI",  "currency": "EUR", "tz": "Europe/Paris", "label": "EPA"},
    "TSE":   {"suffix": ".T",   "yfinance": ".T",   "benchmark": "^N225",  "currency": "JPY", "tz": "Asia/Tokyo",   "label": "JP"},
    "TYSE":  {"suffix": ".T",   "yfinance": ".T",   "benchmark": "^N225",  "currency": "JPY", "tz": "Asia/Tokyo",   "label": "JP"},
    "A股":   {"suffix": ".SS",  "yfinance": ".SS",  "benchmark": "000300.SS", "currency": "CNY", "tz": "Asia/Shanghai", "label": "AShare"},
    "TSX":   {"suffix": ".TO",  "yfinance": ".TO",  "benchmark": "^GSPTSE", "currency": "CAD", "tz": "America/Toronto", "label": "CA"},
    "UK":    {"suffix": ".L",   "yfinance": ".L",   "benchmark": "^FTSE",  "currency": "GBP", "tz": "Europe/London", "label": "LSE"},
    "欧洲":  {"suffix": ".DE",  "yfinance": ".DE",  "benchmark": "^GDAXI", "currency": "EUR", "tz": "Europe/Berlin", "label": "EU"},
    "未上市": {"suffix": "",     "yfinance": "NONE", "benchmark": "NONE",   "currency": "USD", "tz": "UTC", "label": "Private"},
    "国际":  {"suffix": "",     "yfinance": "NONE", "benchmark": "NONE",   "currency": "USD", "tz": "UTC", "label": "Index"},
    "broad_market": {"suffix": "", "yfinance": "NONE", "benchmark": "NONE", "currency": "USD", "tz": "UTC", "label": "Broad"},
    "sector": {"suffix": "",     "yfinance": "NONE", "benchmark": "NONE",   "currency": "USD", "tz": "UTC", "label": "Sector"},
    "thematic": {"suffix": "",  "yfinance": "NONE", "benchmark": "NONE",   "currency": "USD", "tz": "UTC", "label": "Thematic"},
    "ETF":   {"suffix": "",     "yfinance": "",     "benchmark": "VTI",    "currency": "USD", "tz": "US/Eastern",   "label": "US"},
    "未上市": {"suffix": "",    "yfinance": "NONE", "benchmark": "NONE",   "currency": "USD", "tz": "UTC", "label": "Private"},
    "private": {"suffix": "",   "yfinance": "NONE", "benchmark": "NONE",   "currency": "USD", "tz": "UTC", "label": "Private"},
    "commodity": {"suffix": "=F", "yfinance": "=F", "benchmark": "DBC",  "currency": "USD", "tz": "US/Eastern",   "label": "CME"},
    "crypto": {"suffix": "-USD", "yfinance": "-USD", "benchmark": "BTC-USD", "currency": "USD", "tz": "UTC", "label": "Crypto"},
    "Korea": {"suffix": ".KS",  "yfinance": ".KS",  "benchmark": "^KS11",  "currency": "KRW", "tz": "Asia/Seoul",   "label": "KR"},
    "Germany": {"suffix": ".DE", "yfinance": ".DE", "benchmark": "^GDAXI", "currency": "EUR", "tz": "Europe/Berlin", "label": "EU"},
    "Japan": {"suffix": ".T",   "yfinance": ".T",   "benchmark": "^N225",  "currency": "JPY", "tz": "Asia/Tokyo",    "label": "JP"},
    "Hong Kong": {"suffix": ".HK", "yfinance": ".HK", "benchmark": "^HSI", "currency": "HKD", "tz": "Asia/Hong_Kong", "label": "HK"},
    "Singapore": {"suffix": ".SI", "yfinance": ".SI", "benchmark": "^STI", "currency": "SGD", "tz": "Asia/Singapore", "label": "SG"},
}

# 特殊 ticker(非标后缀的):ticker→yfinance symbol 直接映射
SPECIAL_OVERRIDE = {
    "BTC":  "BTC-USD",  "ETH":  "ETH-USD",  "LTC":  "LTC-USD",
    "GC=F": "GC=F",     "SI=F": "SI=F",     "CL=F": "CL=F",
    "ALI=F":"ALI=F",
    "005930.KS": "005930.KS",  # 已含后缀
    "688017": "688017.SH",        # A 股纯数字补 .SH
    "688498": "688498.SH",
    "000300.SS": "000300.SS",    # 已含
    "000660.KS": "000660.KS",
    "BKKT": "BKKT",
    "SOI":  "SOI",                # 法 paca 实际是 SOI.PA,但 SOI 美股 OTC 也可
    "MAGS": "MAGS",  # Roundhill Magnificent Seven ETF
    "VTI":  "VTI",  # 已含
    "DBC":  "DBC",  # 已含
    "VGK":  "VGK",
    "EZU":  "EZU",
    "BOA":  "BAC",  # 估计 BAC (Bank of America),不是 BOA
    "JPM":  "JPM",
    "RUT":  "RUT",  # Russell 2000 ETF
    "MSTR": "MSTR",
    "VGK":  "VGK",
    "BOA":  "BAC",  # 重做一遍,BAC 比 BOA 通用
}

import yfinance as yf

def resolve_symbol(ticker, market):
    """把 prediction 的 (ticker, market) 解析为 yfinance symbol。"""
    # 1) SPECIAL_OVERRIDE 优先
    if ticker in SPECIAL_OVERRIDE:
        return SPECIAL_OVERRIDE[ticker]
    # 2) 数字 ticker 4-6 位(TW/KRX 6位)
    if ticker.isdigit() and 4 <= len(ticker) <= 6:
        # 6 位 A股 → .SH
        if market in ("A股", "AShare"):
            return f"{ticker}.SH"
        # 6 位数字可能也是 TW 4位 + 2位 — 默认 TW
        if market == "TW":
            return f"{ticker}.TW"
        if market == "KR":
            return f"{ticker}.KS"
        if market == "JP":
            return f"{ticker}.T"
        # 默认:加上 market 后缀
        cfg = MARKET_CONFIG.get(market, {})
        suffix = cfg.get("yfinance", "")
        return f"{ticker}{suffix}"
    # 3) 已是 NNNN.SYMBOL 形式(688017.SH, 000660.KS 等)
    if "." in ticker:
        return ticker  # 直接用
    # 4) 普通 ticker
    cfg = MARKET_CONFIG.get(market, {})
    suffix = cfg.get("yfinance", "")
    if suffix == "NONE":
        return None  # 不可查
    return f"{ticker}{suffix}"


def check_symbol(symbol, max_retries=4):
    """yfinance 拉 5d 日线, 验证可查 + 返回最近价格/日期。

    加重试退避(429/限流): 5s, 15s, 45s, 90s
    """
    for attempt in range(max_retries):
        try:
            t = yf.Ticker(symbol)
            h = t.history(period="5d", auto_adjust=False)
            if h is None or len(h) == 0:
                return {"ok": False, "reason": "no_history", "last_close": None, "last_date": None, "attempts": attempt+1}
            last = h.iloc[-1]
            return {
                "ok": True,
                "last_close": float(last["Close"]) if last["Close"] is not None else None,
                "last_date": str(h.index[-1].date()),
                "rows": len(h),
                "attempts": attempt+1,
            }
        except Exception as e:
            err = str(e)[:120]
            is_rate_limit = ("429" in err or "Too Many Requests" in err or "Rate limited" in err)
            if attempt < max_retries - 1 and is_rate_limit:
                wait = 5 * (3 ** attempt)  # 5, 15, 45
                time.sleep(wait)
                continue
            return {"ok": False, "reason": err, "last_close": None, "last_date": None, "attempts": attempt+1}
    return {"ok": False, "reason": "max_retries", "last_close": None, "last_date": None, "attempts": max_retries}


# ============== 主流程 ==============
print("Phase 3 P3-1: 标的→yfinance 解析 + 覆盖率测试", flush=True)

conn = sqlite3.connect(DB, timeout=30)
rows = conn.execute(
    """SELECT ticker, market, count(*) as cnt FROM predictions
       WHERE ticker IS NOT NULL AND ticker != ''
       GROUP BY ticker, market ORDER BY cnt DESC""").fetchall()
print(f"unique (ticker, market): {len(rows)}", flush=True)

# 也看未解析(无法查)
unverifiable = []
for t, m, _ in rows:
    sym = resolve_symbol(t, m)
    if sym is None:
        unverifiable.append((t, m))

print(f"  unverifiable (market='NONE'): {len(unverifiable)}")
for t, m in unverifiable[:20]:
    print(f"    {m}: {t}")

# 待查的 (symbol 不为 None)
to_check = []
for t, m, cnt in rows:
    sym = resolve_symbol(t, m)
    if sym is not None:
        to_check.append((t, m, cnt, sym))

print(f"  to_check (有 yfinance symbol): {len(to_check)}", flush=True)


# ==== 并发查(single thread + retry,避免 yfinance 限流) ====
t0 = time.time()
results = []
n_done = 0
n_ok = 0
n_fail = 0
import random
for t, m, cnt, sym in to_check:
    info = check_symbol(sym)
    n_done += 1
    if info["ok"]:
        n_ok += 1
    else:
        n_fail += 1
    results.append((t, m, cnt, sym, info))
    if n_done % 50 == 0:
        elapsed = time.time() - t0
        print(f"  [{n_done}/{len(to_check)}] elapsed={elapsed:.0f}s rate={n_done/elapsed:.1f}/s ok={n_ok} fail={n_fail}", flush=True)
    time.sleep(0.5)  # 节流,避免 yfinance 限流

# ==== 写表 ====
# 写一张 price_coverage 表(每 ticker 一行)
conn.execute("DROP TABLE IF EXISTS price_coverage")
conn.execute("""
    CREATE TABLE price_coverage (
        ticker TEXT NOT NULL,
        market TEXT NOT NULL,
        yfinance_symbol TEXT,
        n_predictions INTEGER,
        last_close REAL,
        last_date TEXT,
        rows_fetched INTEGER,
        ok INTEGER,
        reason TEXT,
        PRIMARY KEY (ticker, market)
    )
""")
ok_results = [r for r in results if r[4]["ok"]]
fail_results = [r for r in results if not r[4]["ok"]]
for t, m, cnt, sym, info in results:
    conn.execute(
        """INSERT INTO price_coverage
           (ticker, market, yfinance_symbol, n_predictions, last_close, last_date, rows_fetched, ok, reason)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
        (t, m, sym, cnt, info.get("last_close"), info.get("last_date"),
         info.get("rows"), 1 if info["ok"] else 0, info.get("reason", ""))
    )
conn.commit()
print(f"\n写 price_coverage {len(results)} 行", flush=True)


# ==== 按 market 覆盖率 ====
from collections import Counter, defaultdict
total_by_market = Counter()
ok_by_market = Counter()
for t, m, cnt, sym, info in results:
    total_by_market[m] += cnt
    if info["ok"]:
        ok_by_market[m] += cnt

# 加上 unverifiable (market='NONE')
for t, m in unverifiable:
    total_by_market[m] += conn.execute("SELECT count(*) FROM predictions WHERE ticker=? AND market=?", (t, m)).fetchone()[0]


# ==== 写报告 ====
elapsed = time.time() - t0
report = []
report.append("# Phase 3 P3-1: 行情覆盖率报告")
report.append("")
report.append(f"**运行时间**: {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S UTC')}")
report.append(f"**耗时**: {elapsed:.0f}s ({elapsed/60:.1f}min)")
report.append(f"**并发**: 3 worker")
report.append(f"**数据源**: yfinance 1.4.1")
report.append("")
report.append("## 1. 总体统计")
report.append("")
total_pred = sum(cnt for _, _, cnt, _ in [(t, m, c, s) for t, m, c, s in to_check] for cnt in [cnt])
report.append(f"- predictions 总数 (ticker 非空): 4470")
report.append(f"- unique (ticker, market) 组合: {len(rows)}")
report.append(f"- 有 yfinance symbol 的: {len(to_check)}")
report.append(f"- 不可查 (market=NONE,无 yfinance): {len(unverifiable)}")
report.append(f"- 实际可查 (yfinance 返 5d 历史): {n_ok} / {len(to_check)} ({n_ok/len(to_check)*100:.1f}%)")
total_unverifiable_pred = sum(conn.execute("SELECT count(*) FROM predictions WHERE ticker=? AND market=?", (t, m)).fetchone()[0] for t, m in unverifiable)
report.append(f"- 行情不可达 predictions 数(可查失败 + market=NONE): {n_fail + total_unverifiable_pred} / 4470 ({(n_fail + total_unverifiable_pred)/4470*100:.1f}%)")
report.append("")
report.append("## 2. 按 market 分层覆盖率")
report.append("")
report.append("| market | predictions | 唯一 ticker | yfinance 可查 | 覆盖率 |")
report.append("|---|---|---|---|---|")
for m, total in sorted(total_by_market.items(), key=lambda x: -x[1]):
    n_t = sum(1 for t, mm, c, s in to_check if mm == m)
    n_o = ok_by_market.get(m, 0)
    rate = n_o / total * 100 if total else 0
    report.append(f"| {m} | {total} | {n_t} | {n_o} | {rate:.1f}% |")
report.append("")
report.append("## 3. unresolved_price 清单(yfinance 不可查)")
report.append("")
if fail_results:
    report.append("### 3.1 查但失败(yfinance 返 0 行)")
    report.append("")
    fail_by_reason = Counter()
    for t, m, cnt, sym, info in fail_results:
        fail_by_reason[info.get("reason", "")[:40]] += 1
    for reason, n in fail_by_reason.most_common(10):
        report.append(f"- `{reason}`: {n} ticker")
    report.append("")
    report.append("**前 30 个 failed ticker (按 n_pred 降序)**:")
    report.append("")
    report.append("| ticker | market | n_pred | reason |")
    report.append("|---|---|---|---|")
    for t, m, cnt, sym, info in sorted(fail_results, key=lambda x: -x[2])[:30]:
        report.append(f"| {t} | {m} | {cnt} | {info.get('reason', '')[:60]} |")
    if len(fail_results) > 30:
        report.append(f"\n(还有 {len(fail_results)-30} 个)")
    report.append("")

if unverifiable:
    report.append("### 3.2 market='NONE' 不可查(板块/概念/未上市)")
    report.append("")
    report.append("| ticker | market | n_pred |")
    report.append("|---|---|---|")
    for t, m in sorted(unverifiable, key=lambda x: -conn.execute("SELECT count(*) FROM predictions WHERE ticker=? AND market=?", (x[0], x[1])).fetchone()[0])[:20]:
        cnt = conn.execute("SELECT count(*) FROM predictions WHERE ticker=? AND market=?", (t, m)).fetchone()[0]
        report.append(f"| {t} | {m} | {cnt} |")
    report.append("")

report.append("## 4. 结论")
report.append("")
total_unreachable = n_fail + total_unverifiable_pred
report.append(f"- **可验证 predictions** (yfinance OK): {n_ok}/4470 (**{n_ok/4470*100:.1f}%**)")
report.append(f"- 行情不可达: {total_unreachable}/4470 (**{total_unreachable/4470*100:.1f}%**)")
report.append("")
report.append("### 已知缺口")
report.append("- **SE / OTC / TW / KR / JP / LSE 等小市场**:yfinance 覆盖不稳,部分 ticker 需手动补")
report.append("- **A 股 (17)**: 数字 6 位 + .SH/.SZ 格式,部分无数据")
report.append("- **commodity (15)**: 期货代码 (GC=F/SI=F) 单独处理,可能延迟")
report.append("- **板块/概念 (small caps, memory, photonics theme)**: market='NONE',不入 P3 验证,单独列")

# 落报告
content = '\n'.join(report)
with open("outputs/phase3_p1_coverage_report.md", "w", encoding="utf-8") as f:
    f.write(content)
print(f"\n写 outputs/phase3_p1_coverage_report.md ({len(content)} chars)", flush=True)

# 打印 top 20 失败 ticker
print(f"\n=== Top 10 failed ticker(按 n_pred 降序) ===")
for t, m, cnt, sym, info in sorted(fail_results, key=lambda x: -x[2])[:10]:
    print(f"  {t:10s} {m:8s} n={cnt:3d} reason={info.get('reason','')[:60]}")
print(f"\n=== Top 10 unverifiable ticker ===")
for t, m in sorted(unverifiable, key=lambda x: -conn.execute("SELECT count(*) FROM predictions WHERE ticker=? AND market=?", (x[0], x[1])).fetchone()[0])[:10]:
    cnt = conn.execute("SELECT count(*) FROM predictions WHERE ticker=? AND market=?", (t, m)).fetchone()[0]
    print(f"  {t:10s} {m:8s} n={cnt}")
conn.close()
print(f"\nDONE. {n_ok}/{len(to_check)} yfinance OK ({n_ok/len(to_check)*100:.1f}%)", flush=True)
