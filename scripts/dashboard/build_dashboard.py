#!/usr/bin/env python3
"""
build_dashboard.py — 每日生成 dashboard.html
读 DB(signalboard_full.db) + 金融数据库 (Polygon / DB cache) → 注入 dashboard.template.html → 输出 dashboard.html

用法: python3 build_dashboard.py
在 daily cron 里，放在 模块2抽取 之后、gzip+push 之前。

价格查询优化: ticker_prices DB 缓存, 跨 cron 复用 (避免 Polygon 5 req/min 限速导致每次跑 12 分钟).
"""
import json, sqlite3, datetime, pathlib, os, time
import requests

DB = "/workspace/data/signalboard_full.db"
TEMPLATE = pathlib.Path(__file__).with_name("dashboard.template.html")
OUT = pathlib.Path(__file__).with_name("dashboard.html")

SRC2KOL = {  # source_id -> 短名(UI用)
    "tw_jukan05": "jukan", "tw_aleabitoreddit": "serenity",
    "tw_zephyr_z9": "zephyr", "tw_austinsemis": "austin",
}

# ---- 区块1：人物卡（写死，来自能力圈画像 / 04_kol_mapping）----
KOLS = {
 "jukan":{"key":"jukan","name":"Jukan","handle":"@jukan05","type":"signal",
   "typeLabel":"信号源 · signal","desc":"100% 推文带 ticker，会明确喊方向。胜率高，几乎不做空。",
   "strong":["存储","HBM","代工","卡点"],"weak":["看多 AI 龙头(跑输板块)"]},
 "serenity":{"key":"serenity","name":"Serenity","handle":"@aleabitoreddit","type":"cognition",
   "typeLabel":"瓶颈专家 · cognition","desc":"光通信/CPO 瓶颈专家，会喊标的，但顺势押龙头、易追高。",
   "strong":["光通信","CPO","InP","化合物半导体"],"weak":["整体追高","tier_B 清单=板块β"]},
 "zephyr":{"key":"zephyr","name":"zephyr","handle":"@zephyr_z9","type":"cognition",
   "typeLabel":"卡点雷达 · cognition","desc":"产业卡点雷达，看多卡点极准(94.8%)，但看空系统性错。",
   "strong":["存储","光通信","HBM","电力","卡点"],"weak":["看空全错(0/22)","AI 泡沫论盲区"]},
 "austin":{"key":"austin","name":"Austin","handle":"@austinsemis","type":"cognition",
   "typeLabel":"商业格局 · cognition","desc":"AI 芯片商业格局分析，AMD/CUDA 护城河有洞察。认知源非信号源。",
   "strong":["商业格局","AMD/CUDA 护城河","Foundry 模式"],"weak":["看多龙头(跑输板块)","看空全错(1/8)"]},
}

# 4 大V 真正强项领域的 ticker 白名单 (LLM bottleneck 误抽太多, 改用 ticker 黑/白名单二次过滤)
KOL_TICKERS = {
  "jukan": {  # 信号源, 100% 推文带 ticker, 强存储/HBM/代工
    "in_field": ["MU","SNDK","DRAM","AXTI","ASTS","RKLB","TSM","NVDA","AMD","AVGO","NBIS"],
  },
  "serenity": {  # 光通信/CPO/InP/化合物半导体专家
    "in_field": ["AAOI","SIVE","COHR","LITE","POET","AEVA","AEHR","MRVL","JBL","GFS","AOSL","POWI","IQE","SOI","XFAB","TSEM","WOLF","NVTS","TSM","NOK"],
    "out_of_field": ["TSLA","MSFT","META","GOOGL","AMZN","AVGO","BRK.A","ASML","SPY","DELL","CRM","PLTR","SNAP","INTC","AAPL","NVDA","AMD","RKLB","NBIS","ASTS","AXTI","MU","093370","6324","2454","688017","AIXA","LPK","SPCX"],  # 这些 LLM 错塞进 serenity 的, 实际是 AI 龙头/海外/私募
  },
  "zephyr": {  # 存储/光通信/HBM/电力/卡点
    "in_field": ["MU","SNDK","DRAM","NBIS","AAOI","LITE","POET","SIVE","JBL","COHR","AEVA","AEHR","TSM","VPG","INTC","AMD","MRVL"],
    "out_of_field": ["TSLA","MSFT","META","GOOGL","AMZN","AVGO","BRK.A","ASML","SPY","DELL","CRM","PLTR","SNAP","AAPL","AOSL","POWI","IQE","SOI","XFAB","TSEM","WOLF","NVTS","NOK","RKLB","ASTS","AXTI","093370","6324","2454","688017","AIXA","LPK","SPCX","GFS"],
  },
  "austin": {  # 商业洞察, 看多 AI 龙头 (但跑输板块). 主要认知源, 信号弱
    "in_field": ["AMD","NVDA","MU","AVGO","TSM","INTC","MRVL","GOOGL","META","MSFT","AMZN"],
    "out_of_field": ["TSLA","BRK.A","ASML","SPY","DELL","CRM","PLTR","SNAP","AAPL","AOSL","POWI","IQE","SOI","XFAB","TSEM","WOLF","NVTS","NOK","SIVE","JBL","GFS","RKLB","ASTS","AXTI","AEVA","AEHR","COHR","LITE","POET","AAOI","093370","6324","2454","688017","AIXA","LPK","SPCX","NBIS","SNDK","DRAM","VPG"],
  },
}


def is_in_field(kol: str, ticker: str, bottleneck: str | None) -> bool:
    """判定 (kol, ticker) 是否在 KOL 真正强项领域.

    优先用 ticker 白名单 (LLM bottleneck 误抽太多, 白名单更可靠):
    1. ticker 在 KOL_TICKERS[kol]['in_field'] → True
    2. ticker 在 KOL_TICKERS[kol]['out_of_field'] → False
    3. 没匹配 → fallback 到 LLM bottleneck (bottleneck in strong)
    """
    if kol not in KOL_TICKERS:
        return False
    spec = KOL_TICKERS[kol]
    if ticker in spec.get("in_field", []):
        return True
    if ticker in spec.get("out_of_field", []):
        return False
    # fallback: bottleneck 字段匹配 strong
    if bottleneck:
        for s in KOLS.get(kol, {}).get("strong", []):
            if s in bottleneck or bottleneck in s:
                return True
    return False

def parse_json_arr(s):
    if not s or not isinstance(s, str): return []
    s = s.strip()
    if s.startswith('['):
        try: return json.loads(s)
        except Exception: return []
    # 兼容单 ticker 字符串 ("NVDA", "688017")
    if s: return [s]
    return []


# ============================================================
# 价格查询 (接 Polygon 免费 tier: 5 req/min + DB 缓存跨 cron)
# ============================================================
POLYGON_API_KEY = os.environ.get("POLYGON_API_KEY", "")
POLYGON_BASE = "https://api.polygon.io"
SOXX_ETF = "SOXX"  # iShares Semiconductor ETF (默认板块 ETF)

PRICE_CACHE_TABLE_DDL = """
CREATE TABLE IF NOT EXISTS ticker_prices (
    ticker TEXT NOT NULL,
    pub_date TEXT NOT NULL,
    call_price REAL,
    now_price REAL,
    now_date TEXT,
    sector_pct REAL,
    fetched_at TEXT NOT NULL,
    PRIMARY KEY (ticker, pub_date)
);
"""


def init_price_cache(con):
    """建表. 用 executescript + commit + 单独建 sector_snapshots 保证成功."""
    con.executescript(PRICE_CACHE_TABLE_DDL)
    con.commit()
    # 单独建 sector_snapshots (executescript 在某些环境不识别多 statement)
    con.execute("""
        CREATE TABLE IF NOT EXISTS sector_snapshots (
            sector_etf TEXT NOT NULL,
            snap_date TEXT NOT NULL,
            pct_30d REAL, pct_90d REAL, pct_180d REAL, pct_365d REAL,
            fetched_at TEXT NOT NULL,
            PRIMARY KEY (sector_etf, snap_date)
        )
    """)
    con.commit()


def get_cached_price(con, ticker, pub_date):
    """从 DB 读缓存. now_date < 今天-1 天视为过期, 强制重查."""
    row = con.execute("""
        SELECT call_price, now_price, now_date, sector_pct, fetched_at
        FROM ticker_prices WHERE ticker=? AND pub_date=?
    """, (ticker, pub_date)).fetchone()
    if not row:
        return None
    cp, np_, nd, sec, fa = row
    today = today_str()
    if nd:
        try:
            nd_dt = datetime.datetime.fromisoformat(nd)
            today_dt = datetime.datetime.fromisoformat(today)
            # 过期阈值 7 天 (周末 2-3 天 + 节假日, 价格变化慢 5 天内误差 < 2%)
            if (today_dt - nd_dt).days > 7:
                return None  # 过期 (>3 天强制重查)
        except Exception:
            pass
    return cp, np_, nd, sec


def save_cached_price(con, ticker, pub_date, call_p, now_p, now_d, sec):
    """写缓存. call_price 和 now_price 都为 None 时不写 (避免污染 cache)."""
    if call_p is None and now_p is None:
        return  # 跳过 (cache miss, 不要污染)
    fa = datetime.datetime.now(datetime.timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")
    con.execute("""
        INSERT OR REPLACE INTO ticker_prices
        (ticker, pub_date, call_price, now_price, now_date, sector_pct, fetched_at)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    """, (ticker, pub_date, call_p, now_p, now_d, sec, fa))
    con.commit()


def _polygon_get(url, params, retries=2):
    """GET with 限速 + 重试. 429/403 内部等久一点 (遵守 5 req/min)."""
    for attempt in range(retries + 1):
        try:
            r = requests.get(url, params=params, timeout=15)
            if r.status_code in (429, 403):
                wait = 12 + attempt * 12  # 12s, 24s
                time.sleep(wait)
                continue
            r.raise_for_status()
            return r.json()
        except Exception:
            if attempt < retries:
                time.sleep(2)
                continue
            return None
    return None


def get_call_price(ticker, pub_date):
    """Polygon: 拿 ticker 在 pub_date 当日 或之前最近的 收盘价."""
    pub_dt = datetime.datetime.fromisoformat(pub_date)
    from_d = (pub_dt - datetime.timedelta(days=7)).strftime("%Y-%m-%d")
    to_d = (pub_dt + datetime.timedelta(days=2)).strftime("%Y-%m-%d")
    url = f"{POLYGON_BASE}/v2/aggs/ticker/{ticker}/range/1/day/{from_d}/{to_d}"
    data = _polygon_get(url, {"apiKey": POLYGON_API_KEY, "sort": "desc", "limit": 10})
    if not data or not data.get("results"):
        return None
    for bar in data["results"]:
        bar_t = bar.get("t")
        if bar_t is None: continue
        if isinstance(bar_t, int):
            bar_date = datetime.datetime.utcfromtimestamp(bar_t / 1000).strftime("%Y-%m-%d")
        else:
            bar_date = str(bar_t)[:10]
        if bar_date <= pub_date:
            return bar.get("c")
    return data["results"][0].get("c")


def get_now_price(ticker):
    """Polygon: 拿 ticker 最新收盘价 + 日期."""
    today = datetime.datetime.now()
    from_d = (today - datetime.timedelta(days=10)).strftime("%Y-%m-%d")
    to_d = today.strftime("%Y-%m-%d")
    url = f"{POLYGON_BASE}/v2/aggs/ticker/{ticker}/range/1/day/{from_d}/{to_d}"
    data = _polygon_get(url, {"apiKey": POLYGON_API_KEY, "sort": "desc", "limit": 5})
    if not data or not data.get("results"):
        return None, None
    bar = data["results"][0]
    bar_t = bar.get("t")
    if bar_t is None:
        return bar.get("c"), None
    if isinstance(bar_t, int):
        bar_date = datetime.datetime.utcfromtimestamp(bar_t / 1000).strftime("%Y-%m-%d")
    else:
        bar_date = str(bar_t)[:10]
    return bar.get("c"), bar_date


def get_sector_pct(from_date, to_date, sector_etf=SOXX_ETF):
    """Polygon: 算板块 ETF (默认 SOXX) 区间涨跌幅 %."""
    url = f"{POLYGON_BASE}/v2/aggs/ticker/{sector_etf}/range/1/day/{from_date}/{to_date}"
    data = _polygon_get(url, {"apiKey": POLYGON_API_KEY, "sort": "asc", "limit": 250})
    if not data or not data.get("results") or len(data["results"]) < 2:
        return None
    bars = data["results"]
    first_close = bars[0]["c"]
    last_close = bars[-1]["c"]
    return round((last_close - first_close) / first_close * 100, 1)


def get_sector_pct_from_cache(con, from_date, to_date, sector_etf=SOXX_ETF):
    """从 sector_snapshots 取区间涨跌幅. 没有就 return None (跳过 excess_pct)."""
    # 找最新 snap_date, 算 (now_date - from_date) 区间内的累计 pct
    # 简化: snap_date 通常是今天, 算 (today - from_date) / 30/90/180/365 区间
    row = con.execute("""
        SELECT snap_date, pct_30d, pct_90d, pct_180d, pct_365d
        FROM sector_snapshots WHERE sector_etf=? ORDER BY snap_date DESC LIMIT 1
    """, (sector_etf,)).fetchone()
    if not row:
        return None
    snap_date, p30, p90, p180, p365 = row
    try:
        from_dt = datetime.datetime.fromisoformat(from_date)
        snap_dt = datetime.datetime.fromisoformat(snap_date)
        days = (snap_dt - from_dt).days
    except Exception:
        return None
    # 阈值放宽: 32 天的 ticker 走 30d (而不是 90d 累计, 避免 -118pp 那种离谱值)
    if days <= 45 and p30 is not None:
        return p30  # 0-45 天用 pct_30d (snap_date-30 → snap_date 累计, 近似 30 天涨幅)
    if days <= 100 and p90 is not None:
        return p90  # 45-100 天用 pct_90d
    if days <= 200 and p180 is not None:
        return p180  # 100-200 天用 pct_180d
    if days <= 365 and p365 is not None:
        return p365  # 200-365 天用 pct_365d
    return None


def get_prices(con, ticker, pub_date):
    """查 call_price, now_price, raw_pct, excess_pct. 带 DB 缓存.

    优化: sector_pct 从 sector_snapshots 读 (cron 阶段预生成), 不每次查 Polygon.
    返回: (call_price, now_price, raw_pct, excess_pct)
    缓存命中 → 0 API call; 缓存 miss → 2 call (call/now).
    """
    if not POLYGON_API_KEY:
        return None, None, None, None
    pub_date = pub_date[:10]
    cached = get_cached_price(con, ticker, pub_date)
    if cached is not None:
        cp, np_, nd, sec = cached
        if cp and np_ and cp > 0:
            raw_pct = round((np_ - cp) / cp * 100, 1)
            # excess_pct 优先从 sector_snapshots 算 (最新的 SOXX ETF 区间累计)
            sec_from_snap = get_sector_pct_from_cache(con, pub_date, nd or today_str())
            if sec_from_snap is not None:
                excess_pct = round(raw_pct - sec_from_snap, 1)
            elif sec is not None:
                excess_pct = round(raw_pct - sec, 1)  # cache miss 时存的 sector_pct (Polygon 算的)
            else:
                excess_pct = None
            return cp, np_, raw_pct, excess_pct
        return cp, np_, None, None
    # 默认数据源: 金融数据库 (恒生聚源 connector) 通过 ticker_prices cache.
    # Polygon 仅作为 fallback (不在线查, 避免 5 req/min 限速).
    # cache miss → return None, dashboard 显示 "—"
    return None, None, None, None


def refresh_sector_snapshots(con, sector_etf=SOXX_ETF):
    """cron 跑前算一次: 算 ETF 30/90/180/365 天累计, 存 sector_snapshots.

    优先 ticker_prices cache (如果有 SOXX 历史), fallback Polygon (1 API call).
    """
    if not POLYGON_API_KEY:
        return False
    today = today_str()
    # 1. 优先 cache (金融数据库可能没 SOXX, 失败 fallback)
    # 直接 Polygon: SOXX/SMH 等 ETF 金融数据库没覆盖
    url = f"{POLYGON_BASE}/v2/aggs/ticker/{sector_etf}/range/1/day/2024-12-01/{today}"
    data = _polygon_get(url, {"apiKey": POLYGON_API_KEY, "sort": "asc", "limit": 500})
    if not data or not data.get("results") or len(data["results"]) < 2:
        return False
    bars = data["results"]
    today_close = bars[-1]["c"]
    def pct(days_ago):
        target = (datetime.datetime.now() - datetime.timedelta(days=days_ago)).strftime("%Y-%m-%d")
        for b in reversed(bars):
            bar_t = b.get("t")
            if isinstance(bar_t, int):
                bd = datetime.datetime.utcfromtimestamp(bar_t / 1000).strftime("%Y-%m-%d")
            else:
                bd = str(bar_t)[:10]
            if bd <= target:
                return round((today_close - b["c"]) / b["c"] * 100, 1)
        return None
    p30 = pct(30)
    p90 = pct(90)
    p180 = pct(180)
    p365 = pct(365)
    fa = datetime.datetime.now(datetime.timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")
    con.execute("""
        INSERT OR REPLACE INTO sector_snapshots
        (sector_etf, snap_date, pct_30d, pct_90d, pct_180d, pct_365d, fetched_at)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    """, (sector_etf, today, p30, p90, p180, p365, fa))
    con.commit()
    print(f"  sector_snapshots: {sector_etf} @ {today} → 30d={p30}% 90d={p90}% 180d={p180}% 365d={p365}%", flush=True)
    return True
    # 查现价 + 1y 前价
    url = f"{POLYGON_BASE}/v2/aggs/ticker/{sector_etf}/range/1/day/2024-01-01/{today}"
    data = _polygon_get(url, {"apiKey": POLYGON_API_KEY, "sort": "asc", "limit": 500})
    if not data or not data.get("results") or len(data["results"]) < 2:
        return False
    bars = data["results"]
    today_close = bars[-1]["c"]
    def pct(days_ago):
        # 找 pub_date 当天或之前最近的 bar
        target = (datetime.datetime.now() - datetime.timedelta(days=days_ago)).strftime("%Y-%m-%d")
        for b in reversed(bars):
            bar_t = b.get("t")
            if isinstance(bar_t, int):
                bd = datetime.datetime.utcfromtimestamp(bar_t / 1000).strftime("%Y-%m-%d")
            else:
                bd = str(bar_t)[:10]
            if bd <= target:
                return round((today_close - b["c"]) / b["c"] * 100, 1)
        return None
    p30 = pct(30)
    p90 = pct(90)
    p180 = pct(180)
    p365 = pct(365)
    fa = datetime.datetime.now(datetime.timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")
    con.execute("""
        INSERT OR REPLACE INTO sector_snapshots
        (sector_etf, snap_date, pct_30d, pct_90d, pct_180d, pct_365d, fetched_at)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    """, (sector_etf, today, p30, p90, p180, p365, fa))
    con.commit()
    print(f"  sector_snapshots: {sector_etf} @ {today} → 30d={p30}% 90d={p90}% 180d={p180}% 365d={p365}%", flush=True)
    return True


def today_str():
    return datetime.datetime.now().strftime("%Y-%m-%d")


def query_extractions(conn):
    """区块2/4 用。返回最近1年的有效判断（有ticker或bottleneck或非neutral）。"""
    cutoff = (datetime.datetime.utcnow() - datetime.timedelta(days=370)).isoformat()
    rows = conn.execute("""
        SELECT e.post_id, e.source_id, e.direction, e.ticker, e.company,
               e.bottleneck, e.attribution, e.rebuts_narrative, e.summary_100,
               e.is_retrospective, e.is_disclosure, e.is_self_reported_returns,
               r.published_at, r.raw_text
        FROM extractions_intel e
        JOIN raw_posts r ON r.post_id = e.post_id
        WHERE r.published_at >= ?
          AND (e.ticker IS NOT NULL OR e.bottleneck IS NOT NULL OR e.direction != 'neutral')
        ORDER BY r.published_at DESC
    """, (cutoff,)).fetchall()
    out=[]
    for x in rows:
        (post_id,src,direction,ticker,company,bk,attr,rebuts,summ,
         retro,disc,selfret,pub,raw_text)=x
        handle = src.replace("tw_","")
        out.append({
            "post_id":post_id,"kol":SRC2KOL.get(src,handle),"source_id":src,
            "published_at":pub,"direction":direction,
            "ticker":parse_json_arr(ticker),"company":parse_json_arr(company),
            "bottleneck":bk,"attribution":attr,"rebuts":rebuts,"summary":summ,
            "is_retro":retro or 0,"is_disc":disc or 0,"is_selfret":selfret or 0,
            "raw_text":raw_text,
            "raw_url":f"https://x.com/{handle}/status/{post_id}",
        })
    return out


def query_tickers(conn):
    """区块3 用。每个 (kol, ticker) 取【最近一次距今 ≥ 3 天】喊单 + 算涨跌.

    修 (2026-06-29 v3):
    1. 按 (kol, ticker) 去重 (不是只按 ticker — Jukan 的 MU 和 Serenity 的 MU 是两条独立记录)
    2. 取每个 (kol, ticker) 组合的最近一次喊单
    3. 但排除 < 3 天的 (今天喊的还没涨跌, 不显示)
    4. 强项标的 (in_field=True) 优先, 圈外 (in_field=False) 标 '圈外·追高'
    5. 无价格 (call_price=None) 归最后
    """
    print("  query_tickers: 开始", flush=True)
    rows = conn.execute("""
        SELECT e.source_id, e.ticker, e.direction, e.bottleneck, r.published_at
        FROM extractions_intel e
        JOIN raw_posts r ON r.post_id = e.post_id
        WHERE e.direction IN ('long','short')
          AND e.is_retrospective = 0 AND e.is_disclosure = 0
          AND e.ticker IS NOT NULL
        ORDER BY r.published_at DESC
    """).fetchall()

    # (kol, ticker) 维度聚合 → 最近一次喊单 (rows 已 DESC)
    by_kol_tk = {}  # (kol, tk) → {pub, direction, bottleneck, n_calls, earliest_pub}
    for src, ticker_json, direction, bk, pub in rows:
        kol = SRC2KOL.get(src, src.replace("tw_",""))
        for tk in parse_json_arr(ticker_json):
            key = (kol, tk)
            if key not in by_kol_tk:
                by_kol_tk[key] = {
                    "latest_pub": pub, "latest_direction": direction,
                    "latest_bottleneck": bk, "earliest_pub": pub,
                    "n_calls": 1,
                }
            else:
                rec = by_kol_tk[key]
                rec["n_calls"] += 1
                if pub < rec["earliest_pub"]:
                    rec["earliest_pub"] = pub
                # latest_pub 自动是第一个 (rows DESC)

    print(f"  query_tickers: {len(by_kol_tk)} unique (kol, ticker)", flush=True)

    today_d = datetime.datetime.now().date()
    MIN_DAYS = 5  # 最近 5 天内的不算 (还没涨跌, 6-29→6-26 = 3d 跳过)

    # 筛 + 算
    rows_out = []
    skipped_too_recent = []
    for (kol, tk), rec in by_kol_tk.items():
        pub_date = rec["latest_pub"][:10]
        try:
            days_since = (today_d - datetime.datetime.fromisoformat(pub_date).date()).days
        except Exception:
            days_since = 0
        # 太近 (< 3 天) 跳过, 但记录下来 (其实这种 ticker 应该很少, 因为要 4-30 天前喊的才有意义)
        if days_since < MIN_DAYS:
            skipped_too_recent.append((kol, tk, pub_date, days_since))
            continue

        call_price, now_price, raw_pct, excess_pct = (None, None, None, None)
        call_price, now_price, raw_pct, excess_pct = get_prices(conn, tk, pub_date)

        bk = rec["latest_bottleneck"]
        direction = rec["latest_direction"]
        in_field = is_in_field(kol, tk, bk)
        has_price = call_price is not None and now_price is not None

        rows_out.append({
            "ticker": tk, "kol": kol,
            "direction": direction,
            "called_at": rec["latest_pub"],
            "earliest_call": rec["earliest_pub"],
            "days_since": days_since,
            "call_price": call_price, "now_price": now_price,
            "raw_pct": raw_pct, "excess_pct": excess_pct,
            "in_field": in_field,
            "has_price": has_price,
            "n_calls": rec["n_calls"],
            "priority": (
                0 if in_field and has_price else
                1 if in_field else
                2 if has_price else
                3  # 圈外无价格 → 最后
            ),
        })

    # 排序: 强项+有价格 → 强项无价格 → 圈外有价格 → 圈外无价格 (然后按 called_at desc)
    rows_out.sort(key=lambda r: (r["priority"], -r["days_since"]))
    out = rows_out[:30]

    print(f"  query_tickers: 跳过太近 (< {MIN_DAYS}d): {len(skipped_too_recent)}, 显示: {len(out)}", flush=True)
    for i, t in enumerate(out, 1):
        marker = "✓" if t["in_field"] else "⚠️"
        pmark = "💰" if t["has_price"] else "❓"
        print(f"    {i:2d}. {marker}{pmark} {t['kol']:10s} {t['ticker']:8s} {t['direction']:5s} "
              f"called={t['called_at'][:10]} ({t['days_since']}d ago) "
              f"call={t['call_price']} now={t['now_price']} raw={t['raw_pct']} exc={t['excess_pct']}", flush=True)
    return out


def load_summaries():
    """读取 intel_gen_summaries.py 预生成的 21 段总结."""
    p = pathlib.Path(__file__).with_name("summaries.json")
    if p.exists():
        return json.loads(p.read_text(encoding="utf-8"))
    empty_win = {"1":"","3":"","6":"","12":""}
    return {"today":"（今日总结待生成）",
            "consensus":dict(empty_win),
            "person":{k:dict(empty_win) for k in ["jukan","serenity","zephyr","austin"]}}


def main():
    try:
        conn=sqlite3.connect(DB, timeout=30)
        init_price_cache(conn)
        refresh_sector_snapshots(conn)
        data = query_extractions(conn)
        print(f"  extractions: {len(data)}", flush=True)
        tickers = query_tickers(conn)
        print(f"  tickers: {len(tickers)}", flush=True)
        conn.close()
        summaries = load_summaries()
        html = TEMPLATE.read_text(encoding="utf-8")
        html = html.replace("__RECORDS__",   json.dumps(data, ensure_ascii=False))
        html = html.replace("__KOLS__",      json.dumps(KOLS, ensure_ascii=False))
        html = html.replace("__TICKERS__",   json.dumps(tickers, ensure_ascii=False))
        html = html.replace("__SUMMARIES__", json.dumps(summaries, ensure_ascii=False))
        OUT.write_text(html, encoding="utf-8")
        have_summaries = pathlib.Path(__file__).with_name('summaries.json').exists()
        print(f"dashboard.html: {len(data)} extractions, {len(tickers)} tickers, summaries={'real' if have_summaries else 'placeholder'}", flush=True)
        hit = sum(1 for t in tickers if t['raw_pct'] is not None)
        print(f"  price hit: {hit}/{len(tickers)} ({hit*100//max(1,len(tickers))}%)", flush=True)
    except Exception as e:
        import traceback
        traceback.print_exc()
        print(f"ERROR: {e}", flush=True)
        raise

if __name__=="__main__":
    main()