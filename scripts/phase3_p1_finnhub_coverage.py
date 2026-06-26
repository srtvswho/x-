"""Phase 3 P3-1 (Finnhub 覆盖率摸底):
- 用 /quote 端点(60 req/min) 验证 515 unique ticker 存在
- 报告:能取到 / 取不到 / 按 market 分层
- 美股 vs 非美股 分开
- 不可达进 unresolved_price

**注意**: Finnhub free tier 禁 /stock/candle(全 403),
本次只验证 ticker 存在 + 当前报价,不等同"能拉日线"。
P3-2 实际拉日线需要其他数据源(Polygon / eodhd / Tiingo)。
"""
import sqlite3, time, os, sys, json
from datetime import datetime, timezone
sys.path.insert(0, "/workspace")

FINNHUB_API_KEY = os.environ.get("FINNHUB_API_KEY", "")
if not FINNHUB_API_KEY:
    print("ERROR: FINNHUB_API_KEY not set", flush=True)
    sys.exit(1)

import requests

DB = "data/signalboard_full.db"
BASE = "https://finnhub.io/api/v1"
TICKER_SLEEP = 1.05  # 60 req/min = 1s/req 安全

# ============== market_config ==============
# 美股/加密 Finnhub 覆盖好,欧亚市场大概率不在
MARKET_FINNHUB = {
    "美股":   {"status": "covered", "suffix": ""},      # 直接 ticker
    "OTC":   {"status": "covered", "suffix": ""},      # 美股 OTC
    "ETF":   {"status": "covered", "suffix": ""},      # 美股 ETF
    "crypto": {"status": "special", "suffix": "BINANCE:"},  # 需 BINANCE:BTCUSDT
    "commodity": {"status": "uncovered", "suffix": ""},    # 期货代码不同
    "SE":    {"status": "covered", "suffix": ".ST"},   # 斯德哥尔摩
    "TW":    {"status": "uncovered", "suffix": ".TW"},  # 台湾
    "KR":    {"status": "uncovered", "suffix": ".KS"},  # 韩国
    "JP":    {"status": "uncovered", "suffix": ".T"},   # 日本
    "LSE":   {"status": "covered", "suffix": ".L"},    # 伦敦
    "UK":    {"status": "covered", "suffix": ".L"},
    "CA":    {"status": "covered", "suffix": ".TO"},   # 多伦多
    "TSX":   {"status": "covered", "suffix": ".TO"},
    "ASX":   {"status": "covered", "suffix": ".AX"},   # 澳洲
    "A股":   {"status": "uncovered", "suffix": ".SS"}, # A 股
    "欧洲":  {"status": "covered", "suffix": ".DE"},   # 法兰克福
    "未上市": {"status": "uncovered", "suffix": ""},    # 私募
    "Korea": {"status": "uncovered", "suffix": ".KS"},
    "Japan": {"status": "uncovered", "suffix": ".T"},
    "Germany": {"status": "covered", "suffix": ".DE"},
    "Hong Kong": {"status": "uncovered", "suffix": ".HK"},
    "Singapore": {"status": "uncovered", "suffix": ".SI"},
    "France": {"status": "covered", "suffix": ".PA"},
    "EPA":   {"status": "covered", "suffix": ".PA"},
    "TYO":   {"status": "uncovered", "suffix": ".T"},
    "TSE":   {"status": "uncovered", "suffix": ".T"},
    "TYSE":  {"status": "uncovered", "suffix": ".T"},
    "JPX":   {"status": "uncovered", "suffix": ".T"},
    "TYSE":  {"status": "uncovered", "suffix": ".T"},
    "Korea": {"status": "uncovered", "suffix": ".KS"},
    "KRX":   {"status": "uncovered", "suffix": ".KQ"},
    "UK":    {"status": "covered", "suffix": ".L"},
}

# 特殊 ticker override(已知在 Finnhub 找不到的)
SPECIAL_OVERRIDE = {
    "BTC": "BINANCE:BTCUSDT",
    "ETH": "BINANCE:ETHUSDT",
    "LTC": "BINANCE:LTCUSDT",
    "SOL": "BINANCE:SOLUSDT",
    "DOGE": "BINANCE:DOGEUSDT",
    "XRP": "BINANCE:XRPUSDT",
    "ADA": "BINANCE:ADAUSDT",
    "MATIC": "BINANCE:MATICUSDT",
    "AVAX": "BINANCE:AVAXUSDT",
    "LINK": "BINANCE:LINKUSDT",
    "DOT": "BINANCE:DOTUSDT",
    "BOA": "BAC",  # Bank of America 误识别
    "DXY": "DXY",  # 美元指数
    "BTC-USD": "BINANCE:BTCUSDT",
    "ETH-USD": "BINANCE:ETHUSDT",
    "GC=F": "GC=F",  # 黄金期货
    "SI=F": "SI=F",  # 白银
    "ALI=F": "ALI=F", # 铝
    "HG=F": "HG=F",  # 铜
    "CL=F": "CL=F",  # 原油
    "NG=F": "NG=F",  # 天然气
    "ZB=F": "ZB=F",  # 30 年国债
    "ZN=F": "ZN=F",  # 10 年国债
    "ZW=F": "ZW=F",  # 小麦
    "ZC=F": "ZC=F",  # 玉米
    "ZS=F": "ZS=F",  # 大豆
    "005930.KS": "005930.KS",
    "688017": "688017.SH", "688498": "688498.SH",
    "000300.SS": "000300.SS", "000660.KS": "000660.KS",
    "BKKT": "BKKT", "SOI": "SOI", "MAGS": "MAGS",
    "VTI": "VTI", "DBC": "DBC", "VGK": "VGK", "EZU": "EZU",
    "JPM": "JPM", "RUT": "RUT", "MSTR": "MSTR",
}


def resolve_symbol(ticker, market):
    """Finnhub symbol 解析。"""
    if ticker in SPECIAL_OVERRIDE:
        return SPECIAL_OVERRIDE[ticker]
    if ticker.isdigit() and 4 <= len(ticker) <= 6:
        if market in ("A股",):
            return f"{ticker}.SH"
        cfg = MARKET_FINNHUB.get(market, {})
        suffix = cfg.get("suffix", "")
        return f"{ticker}{suffix}" if suffix else ticker
    if "." in ticker:
        return ticker
    cfg = MARKET_FINNHUB.get(market, {})
    suffix = cfg.get("suffix", "")
    return f"{ticker}{suffix}" if suffix else ticker


def check_finnhub_quote(symbol):
    """/quote 端点 - 当前报价。200 + 有 c 字段 = ticker 存在。"""
    try:
        r = requests.get(
            f"{BASE}/quote",
            params={"symbol": symbol, "token": FINNHUB_API_KEY},
            timeout=10,
        )
        if r.status_code == 429:
            return {"ok": False, "reason": "429_rate_limited"}
        if r.status_code != 200:
            return {"ok": False, "reason": f"http_{r.status_code}"}
        data = r.json()
        if not data or "c" not in data or data.get("c") in (None, 0):
            return {"ok": False, "reason": "no_quote_data", "raw": str(data)[:80]}
        return {
            "ok": True,
            "current": float(data["c"]),
            "prev_close": float(data.get("pc", 0)) or None,
            "high": float(data.get("h", 0)) or None,
            "low": float(data.get("l", 0)) or None,
            "open": float(data.get("o", 0)) or None,
        }
    except Exception as e:
        return {"ok": False, "reason": f"exc_{str(e)[:50]}"}


# ===== 主流程 =====
print("Phase 3 P3-1 (Finnhub quote): ticker 存在性覆盖率测试", flush=True)
conn = sqlite3.connect(DB, timeout=30)
rows = conn.execute(
    """SELECT ticker, market, count(*) as cnt FROM predictions
       WHERE ticker IS NOT NULL AND ticker != ''
       GROUP BY ticker, market ORDER BY cnt DESC""").fetchall()
print(f"unique (ticker, market): {len(rows)}", flush=True)

# 解析所有 ticker
to_check = []
unverifiable = []
for t, m, cnt in rows:
    sym = resolve_symbol(t, m)
    if sym is None:
        unverifiable.append((t, m, cnt))
    else:
        to_check.append((t, m, cnt, sym))
print(f"  to_check: {len(to_check)} / unverifiable (market=NONE): {len(unverifiable)}", flush=True)

# ===== 跑 quote =====
results = []
n_ok = 0
n_fail = 0
n_429 = 0
fail_reasons = {}
t0 = time.time()

for i, (t, m, cnt, sym) in enumerate(to_check, 1):
    info = check_finnhub_quote(sym)
    if not info["ok"]:
        n_fail += 1
        reason = info.get("reason", "unknown")[:40]
        fail_reasons[reason] = fail_reasons.get(reason, 0) + 1
        if "429" in reason:
            n_429 += 1
            time.sleep(15)
    else:
        n_ok += 1
    results.append((t, m, cnt, sym, info))
    if i % 30 == 0:
        elapsed = time.time() - t0
        rate = i / elapsed
        eta = (len(to_check) - i) / rate if rate > 0 else 0
        print(f"  [{i}/{len(to_check)}] elapsed={elapsed:.0f}s rate={rate:.2f}/s ok={n_ok} fail={n_fail} 429={n_429} eta={eta:.0f}s", flush=True)
    time.sleep(TICKER_SLEEP)

elapsed = time.time() - t0
print(f"\n跑完: {len(to_check)} ticker in {elapsed:.0f}s ({elapsed/60:.1f}min), ok={n_ok} fail={n_fail}", flush=True)

# ===== 写 price_coverage 表 =====
conn.execute("DROP TABLE IF EXISTS price_coverage")
conn.execute("""
    CREATE TABLE price_coverage (
        ticker TEXT NOT NULL,
        market TEXT NOT NULL,
        yfinance_symbol TEXT,
        n_predictions INTEGER,
        last_close REAL,
        prev_close REAL,
        high REAL,
        low REAL,
        open_price REAL,
        ok INTEGER,
        reason TEXT,
        PRIMARY KEY (ticker, market)
    )
""")
for t, m, cnt, sym, info in results:
    conn.execute(
        """INSERT INTO price_coverage VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
        (t, m, sym, cnt,
         info.get("current"), info.get("prev_close"),
         info.get("high"), info.get("low"), info.get("open"),
         1 if info["ok"] else 0, info.get("reason", ""))
    )
conn.commit()
print(f"写 price_coverage {len(results)} 行", flush=True)


# ===== 报告 =====
from collections import Counter, defaultdict
total_by_market = Counter()
ok_by_market = Counter()
for t, m, cnt, sym, info in results:
    total_by_market[m] += cnt
    if info["ok"]:
        ok_by_market[m] += cnt

# unverifiable predictions 算入 market 总数
for t, m, cnt in unverifiable:
    total_by_market[m] += cnt

total_pred_all = sum(c for _, _, c, _ in [(t, m, c, s) for t, m, c, s in to_check])
ok_pred_all = sum(c for t, m, c, s, info in results if info["ok"])
# 加上 unverifiable 的 0
unverifiable_pred = sum(cnt for _, _, cnt in unverifiable)
total_pred_with_unverifiable = total_pred_all + unverifiable_pred

# 美股 vs 非美股
US_MARKETS = {"美股", "OTC", "ETF"}
us_total = sum(c for m, c in total_by_market.items() if m in US_MARKETS)
us_ok = sum(c for m, c in ok_by_market.items() if m in US_MARKETS)
nonus_total = sum(c for m, c in total_by_market.items() if m not in US_MARKETS)
nonus_ok = sum(c for m, c in ok_by_market.items() if m not in US_MARKETS)

# 写报告
rpt = []
rpt.append("# Phase 3 P3-1: Finnhub Quote 覆盖率摸底")
rpt.append("")
rpt.append(f"**运行时间**: {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S UTC')}")
rpt.append(f"**耗时**: {elapsed:.0f}s ({elapsed/60:.1f}min)")
rpt.append(f"**数据源**: Finnhub `/quote` 端点(Free tier)")
rpt.append(f"**节流**: 1.05s/req (60 req/min)")
rpt.append("")
rpt.append("## ⚠️ 重要限制")
rpt.append("")
rpt.append("**Finnhub Free tier 禁 `/stock/candle` 端点**(全 403:1/5/15/30/60/D/W/M resolution)。")
rpt.append("本次覆盖率**只验证 ticker 存在 + 当前报价**(`/quote` 端点),")
rpt.append("**不等同于能拉历史日线**。")
rpt.append("")
rpt.append("P3-2 实际拉日线时,需另选数据源:")
rpt.append("- **Polygon.io Free**: 5 req/min,日线 OK(推荐)")
rpt.append("- **eodhd.com Free**: 20/day,日线 OK")
rpt.append("- **Tiingo Free**: 50/hour,日线 OK")
rpt.append("")
rpt.append("## 1. 总体")
rpt.append("")
rpt.append(f"- predictions 总数 (ticker 非空): 4470")
rpt.append(f"- unique (ticker, market): {len(rows)}")
rpt.append(f"- Finnhub quote 可达: **{n_ok}/{len(to_check)} ticker** ({n_ok/len(to_check)*100:.1f}%)")
rpt.append(f"- 不可达: {n_fail} ticker (含 429 限流 {n_429})")
rpt.append(f"- market='NONE' 不可查: {len(unverifiable)} ticker ({unverifiable_pred} pred)")
rpt.append("")
rpt.append(f"**汇总可验证 predictions**: {ok_pred_all + unverifiable_pred} ticker 不在 Finnhub → 等于" if False else f"")
rpt.append(f"- 可达 predictions: **{ok_pred_all}/4470** ({ok_pred_all/4470*100:.1f}%)")
rpt.append(f"- 不可达: {4470-ok_pred_all}/4470 ({(4470-ok_pred_all)/4470*100:.1f}%)")
rpt.append("")
rpt.append("## 2. 美股 vs 非美股")
rpt.append("")
rpt.append("| 区域 | predictions | 可达 | 覆盖率 |")
rpt.append("|---|---|---|---|")
rpt.append(f"| **美股 + 美股 ETF + OTC** | {us_total} | {us_ok} | {us_ok/us_total*100:.1f}% |")
rpt.append(f"| **非美股 (SE/TW/KR/JP/A股/欧/加密/商品)** | {nonus_total} | {nonus_ok} | {nonus_ok/nonus_total*100:.1f}% |")
rpt.append("")
rpt.append("## 3. 按 market 分层覆盖率")
rpt.append("")
rpt.append("| market | predictions | 唯一 ticker | quote 可达 ticker | 覆盖率 |")
rpt.append("|---|---|---|---|---|")
for m, total in sorted(total_by_market.items(), key=lambda x: -x[1]):
    n_t = sum(1 for t, mm, c, s in to_check if mm == m)
    n_o = sum(1 for t, mm, c, s, info in results if mm == m and info["ok"])
    rate = (n_o / n_t * 100) if n_t else 0
    pred_rate = (ok_by_market.get(m, 0) / total * 100) if total else 0
    rpt.append(f"| {m} | {total} | {n_t} | {n_o} | ticker {rate:.0f}% / pred {pred_rate:.0f}% |")
rpt.append("")
rpt.append("## 4. fail 原因分布")
rpt.append("")
rpt.append("| reason | ticker 数 |")
rpt.append("|---|---|")
for reason, n in sorted(fail_reasons.items(), key=lambda x: -x[1]):
    rpt.append(f"| `{reason}` | {n} |")
rpt.append("")

# 不可达 ticker 按 market 列
fail_results = [(t, m, c, s, info) for t, m, c, s, info in results if not info["ok"]]
rpt.append("## 5. unresolved_price 清单(Finnhub quote 不可达)")
rpt.append("")
if fail_results:
    rpt.append(f"**总计 {len(fail_results)} ticker 不可达** (按 n_pred 降序前 50):")
    rpt.append("")
    rpt.append("| ticker | market | n_pred | reason |")
    rpt.append("|---|---|---|---|")
    for t, m, cnt, sym, info in sorted(fail_results, key=lambda x: -x[2])[:50]:
        rpt.append(f"| {t} | {m} | {cnt} | {info.get('reason','')[:40]} |")
    if len(fail_results) > 50:
        rpt.append(f"\n(还有 {len(fail_results)-50} 个,见 DB price_coverage 表)")
    rpt.append("")

if unverifiable:
    rpt.append("### 5.1 market='NONE' 不可查(板块/概念/未上市)")
    rpt.append("")
    rpt.append("| ticker | market | n_pred |")
    rpt.append("|---|---|---|")
    for t, m, cnt in sorted(unverifiable, key=lambda x: -x[2])[:30]:
        rpt.append(f"| {t} | {m} | {cnt} |")
    rpt.append("")

rpt.append("## 6. 第一版验证范围建议")
rpt.append("")
rpt.append(f"基于 Finnhub quote 覆盖率摸底:")
rpt.append(f"- **第一版只验美股 (含 OTC/ETF)**: {us_ok} predictions,覆盖率 {us_ok/us_total*100:.1f}%")
rpt.append(f"- 第一版**跳过**所有非美股 (TW/KR/JP/A股/欧洲等),单列 `validation_status=skipped_non_us`")
rpt.append(f"- 第一版**跳过** Finnhub 不可达 ticker,进 `unresolved_price`")
rpt.append("")
rpt.append(f"**P3-2 数据源决策**:")
rpt.append(f"- 方案 A: 用 Polygon 5 req/min 1.7h 拉美股历史,跳过非美股")
rpt.append(f"- 方案 B: 用 Tiingo 50/h 10.3h 拉美股 + 欧洲(更全)")
rpt.append(f"- 方案 C: 第一版只跑美股 quote-based 验证(快速但不完整)")

content = "\n".join(rpt)
with open("outputs/phase3_p1_coverage_report.md", "w", encoding="utf-8") as f:
    f.write(content)
print(f"\n写 outputs/phase3_p1_coverage_report.md ({len(content)} chars)", flush=True)

# Top 失败列表
print(f"\n=== Top 15 不可达 ticker (按 n_pred 降序) ===")
for t, m, cnt, sym, info in sorted(fail_results, key=lambda x: -x[2])[:15]:
    print(f"  {t:10s} {m:10s} n={cnt:3d} sym={sym:20s} reason={info.get('reason','')[:40]}")

print(f"\n=== Top 5 unverifiable ticker ===")
for t, m, cnt in sorted(unverifiable, key=lambda x: -x[2])[:5]:
    print(f"  {t:10s} {m:10s} n={cnt}")

print(f"\n=== 关键数字 ===")
print(f"  可达 predictions: {ok_pred_all}/4470 ({ok_pred_all/4470*100:.1f}%)")
print(f"  美股: {us_ok}/{us_total} ({us_ok/us_total*100:.1f}%)")
print(f"  非美股: {nonus_ok}/{nonus_total} ({nonus_ok/nonus_total*100:.1f}%)")
conn.close()
