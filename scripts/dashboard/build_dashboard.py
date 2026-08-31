#!/usr/bin/env python3
"""
build_dashboard.py — 每日生成 dashboard.html
读 DB(signalboard_full.db) + 金融数据库 (Polygon / DB cache) → 注入 dashboard.template.html → 输出 dashboard.html

用法: python3 build_dashboard.py
在 daily cron 里，放在 模块2抽取 之后、gzip+push 之前。

价格查询优化: ticker_prices DB 缓存, 跨 cron 复用 (避免 Polygon 5 req/min 限速导致每次跑 12 分钟).
"""
import json, sqlite3, datetime, pathlib, os, time
import sys
from pathlib import Path

import requests

# 共享窗口函数 — 跟 intel_gen_summaries.py / dashboard.template.html / query_today_stats 共用同一窗口
# 24h 滚动 (不是北京自然日, 跟生产 06:00 抓取 → 06:20 Dashboard 节奏对齐)
# 同时: 标的筛选逻辑共享 (common.select_dashboard_ticker_targets / is_in_field / KOL_TICKERS / KOLS)
sys.path.insert(0, str(Path(__file__).parent))
from common import (  # noqa: E402
    build_metadata, query_today_stats, query_today_records, cn_recent_24h_window_utc,
    KOL_TICKERS, KOLS, SRC2KOL, is_in_field, parse_json_arr,
    normalize_ticker,
    select_dashboard_ticker_targets, DASHBOARD_TICKER_LIMIT, DASHBOARD_MIN_DAYS,
    query_call_performance_events,
)

DB = os.environ.get("SIGNALBOARD_DB", "/workspace/data/signalboard_full.db")
TEMPLATE = pathlib.Path(__file__).with_name("dashboard.template.html")
OUT = pathlib.Path(__file__).with_name("dashboard.html")
GOLDEN_CASES = Path(__file__).resolve().parents[2] / "tests" / "golden_cases.json"

# SRC2KOL / KOLS / KOL_TICKERS / is_in_field / parse_json_arr 全部 from common import (顶部 import)
# 保持单一来源, 跟 refresh_prices_polygon 共用同个实现, 跟区块04 展示口径一致


# ============================================================
# 价格查询 (接 Polygon 免费 tier: 5 req/min + DB 缓存跨 cron)
# ============================================================
POLYGON_API_KEY = os.environ.get("POLYGON_API_KEY", "")
POLYGON_BASE = "https://api.polygon.io"
SOXX_ETF = "SOXX"  # iShares Semiconductor ETF (默认板块 ETF)

# ticker_prices schema 必须跟 refresh_prices_polygon.py TICKER_PRICES_DDL 完全一致.
# 端到端测试: refresh_prices_polygon.ensure_tables 建的表, build_dashboard.query_tickers
# 查 sector_pct / call_price / now_price / now_date 不会因缺字段失败.
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
CREATE TABLE IF NOT EXISTS sector_snapshots (
    sector_etf TEXT NOT NULL,
    snap_date TEXT NOT NULL,
    pct_30d REAL, pct_90d REAL, pct_180d REAL, pct_365d REAL,
    fetched_at TEXT NOT NULL,
    PRIMARY KEY (sector_etf, snap_date)
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
        ticker_context = f"{company or ''} {raw_text or ''}"
        out.append({
            "post_id":post_id,"kol":SRC2KOL.get(src,handle),"source_id":src,
            "published_at":pub,"direction":direction,
            "ticker":[normalize_ticker(t, ticker_context) for t in parse_json_arr(ticker)],
            "company":parse_json_arr(company),
            "bottleneck":bk,"attribution":attr,"rebuts":rebuts,"summary":summ,
            "is_retro":retro or 0,"is_disc":disc or 0,"is_selfret":selfret or 0,
            "raw_text":raw_text,
            "raw_url":f"https://x.com/{handle}/status/{post_id}",
        })
    return out


def query_thesis_changes(conn, limit=12):
    """首页第一屏：增量 Thesis Change + Terra Analyst，绝不输出 BUY/SELL。"""
    table = conn.execute(
        "SELECT 1 FROM sqlite_master WHERE type='table' AND name='thesis_analyses'"
    ).fetchone()
    if not table:
        return []
    out=[]
    allowed={"NOT_ACTIONABLE","WATCH","RESEARCH","BUY_CANDIDATE","HEDGE_CANDIDATE","AVOID"}

    case_table = conn.execute(
        "SELECT 1 FROM sqlite_master WHERE type='table' AND name='research_case_analyses'"
    ).fetchone()
    case_specs = json.loads(GOLDEN_CASES.read_text(encoding="utf-8")) if GOLDEN_CASES.exists() else {}
    validation_table = conn.execute(
        "SELECT 1 FROM sqlite_master WHERE type='table' AND name='golden_validations'"
    ).fetchone()
    if case_table:
        case_sql = (
            """SELECT r.case_id,r.title,r.analysis_json,r.updated_at,g.status,g.mode,
                      g.validation_timestamp,g.additional_ai_calls
               FROM research_case_analyses r LEFT JOIN golden_validations g ON g.case_id=r.case_id
               ORDER BY r.updated_at DESC LIMIT 4"""
            if validation_table else
            """SELECT case_id,title,analysis_json,updated_at,NULL,NULL,NULL,NULL
               FROM research_case_analyses ORDER BY updated_at DESC LIMIT 4"""
        )
        for case_id,title,analysis_raw,updated_at,golden_status,validation_mode,validation_timestamp,additional_ai_calls in conn.execute(case_sql).fetchall():
            analysis=json.loads(analysis_raw)
            spec=case_specs.get(case_id,{})
            post_ids=spec.get("seed_post_ids",[])
            social_count=independent_count=0
            links=[]
            if post_ids:
                ph=",".join("?" for _ in post_ids)
                social_count,independent_count=conn.execute(
                    f"""SELECT COUNT(DISTINCT mention_post_id),COUNT(DISTINCT underlying_source_id)
                         FROM source_memberships WHERE mention_post_id IN ({ph})""", post_ids
                ).fetchone()
                links=[{"title":r[0] or r[1],"url":r[1],"source_class":r[2]}
                       for r in conn.execute(
                    f"""SELECT DISTINCT us.title,us.canonical_url,us.source_class
                         FROM source_memberships sm JOIN underlying_sources us USING(underlying_source_id)
                         WHERE sm.mention_post_id IN ({ph}) AND us.canonical_url IS NOT NULL
                         ORDER BY CASE us.source_class WHEN 'PRIMARY' THEN 0 WHEN 'SECONDARY' THEN 1 ELSE 2 END
                         LIMIT 8""", post_ids).fetchall()]
            action=analysis.get("actionability","NOT_ACTIONABLE")
            if action not in allowed:
                action="NOT_ACTIONABLE"
            authors=[x.get("author","").replace("tw_","") for x in analysis.get("author_views",[]) if x.get("author")]
            scores=analysis.get("scores",{})
            out.append({
                "change_id":case_id,"thesis_id":case_id,"theme":title,"authors":authors,
                "change_type":"RESEARCH_CASE","change_score":scores.get("thesis_quality",0),
                "detected_at":updated_at,"previous_view":"跨主题研究案例首次建立",
                "new_view":analysis.get("ai_assessment") or "待独立分析",
                "new_evidence":[{"text":x,"status":"VERIFIED_EVIDENCE","post_id":None,"source_url":None}
                                for x in analysis.get("verified_evidence",[])[:6]],
                "ai_assessment":analysis.get("ai_assessment") or "待独立分析",
                "consensus":[],"disagreement":analysis.get("contradictions") or [],
                "positive_exposure":analysis.get("beneficiaries") or [],
                "negative_exposure":analysis.get("negative_exposure") or [],
                "confidence":scores.get("evidence_quality",0)/10,"actionability":action,
                "social_mentions":social_count or 0,"independent_evidence":independent_count or 0,
                "is_research_case":True,"author_views":analysis.get("author_views") or [],
                "facts":analysis.get("facts") or [],"logic_chain":analysis.get("logic_chain") or [],
                "corrections":analysis.get("corrections") or [],"counter_case":analysis.get("counter_case") or [],
                "second_order_effects":analysis.get("second_order_effects") or [],
                "risks":analysis.get("risks") or [],"unknowns":analysis.get("unknowns") or [],
                "catalysts":analysis.get("catalysts") or [],
                "invalidation_conditions":analysis.get("invalidation_conditions") or [],
                "supporting_sources":links,"scores":scores,
                "golden_status":golden_status,"validation_mode":validation_mode,
                "validation_timestamp":validation_timestamp,"additional_ai_calls":additional_ai_calls,
            })

    rows = conn.execute("""
        SELECT tc.change_id, tc.change_type, tc.change_score, tc.summary, tc.detected_at,
               th.thesis_id, th.author_id, t.name, tc.from_version, tc.to_version,
               prev.snapshot_json, curr.snapshot_json, ta.analysis_json, cat.analysis_json
        FROM thesis_changes tc
        JOIN theses th ON th.thesis_id=tc.thesis_id
        JOIN themes t ON t.theme_id=th.theme_id
        JOIN thesis_versions curr ON curr.thesis_id=tc.thesis_id AND curr.version_number=tc.to_version
        LEFT JOIN thesis_versions prev ON prev.thesis_id=tc.thesis_id AND prev.version_number=tc.from_version
        JOIN thesis_analyses ta ON ta.thesis_id=tc.thesis_id AND ta.thesis_version=tc.to_version
        LEFT JOIN cross_author_theses cat ON cat.theme_id=t.theme_id
        WHERE t.parent_theme_id IS NULL
          AND tc.change_score >= 10
        ORDER BY tc.detected_at DESC, tc.change_score DESC LIMIT ?
    """, (max(0,limit-len(out)),)).fetchall()
    for row in rows:
        (change_id,ctype,score,summary,detected,thesis_id,author,theme,from_v,to_v,prev_raw,curr_raw,analysis_raw,cross_raw)=row
        prev=json.loads(prev_raw) if prev_raw else {}
        curr=json.loads(curr_raw) if curr_raw else {}
        analysis=json.loads(analysis_raw) if analysis_raw else {}
        cross=json.loads(cross_raw) if cross_raw else {}
        author_rows=conn.execute("""SELECT th.author_id FROM theses th JOIN themes t ON t.theme_id=th.theme_id
                                    WHERE t.name=? AND th.current_version>0 ORDER BY th.author_id""",(theme,)).fetchall()
        action=analysis.get("actionability","NOT_ACTIONABLE")
        if action not in allowed:
            action="NOT_ACTIONABLE"
        evidence=conn.execute("""
            SELECT c.claim_text,c.verification_status,c.source_post_id,
                   (SELECT us.canonical_url FROM source_memberships sm
                    JOIN underlying_sources us USING(underlying_source_id)
                    WHERE sm.mention_post_id=c.source_post_id AND us.canonical_url IS NOT NULL
                    ORDER BY CASE us.source_class WHEN 'PRIMARY' THEN 0 WHEN 'SECONDARY' THEN 1 ELSE 2 END
                    LIMIT 1)
            FROM thesis_evidence te JOIN claims c ON c.claim_id=te.claim_id
            WHERE te.thesis_id=? AND te.version_number=?
            ORDER BY c.point_in_time DESC LIMIT 6
        """,(thesis_id,to_v)).fetchall()
        source_counts=conn.execute("""
            SELECT COUNT(DISTINCT c.source_post_id),COUNT(DISTINCT sm.underlying_source_id)
            FROM thesis_evidence te JOIN claims c ON c.claim_id=te.claim_id
            LEFT JOIN source_memberships sm ON sm.mention_post_id=c.source_post_id
            WHERE te.thesis_id=? AND te.version_number=?
        """,(thesis_id,to_v)).fetchone()
        out.append({
            "change_id":change_id,"thesis_id":thesis_id,"theme":theme,
            "authors":[x[0].replace("tw_","") for x in author_rows] or [author.replace("tw_","")],"change_type":ctype,"change_score":score,
            "detected_at":detected,"previous_view":prev.get("thesis_summary") or "首次建立",
            "new_view":curr.get("thesis_summary") or curr.get("current_thesis") or summary,
            "new_evidence":[{"text":x[0],"status":x[1],"post_id":x[2],"source_url":x[3]} for x in evidence],
            "ai_assessment":cross.get("ai_synthesis") or analysis.get("ai_assessment") or "待独立分析",
            "consensus":cross.get("consensus") or [],"disagreement":cross.get("disagreement") or [],
            "positive_exposure":analysis.get("beneficiaries") or curr.get("companies_positive") or [],
            "negative_exposure":analysis.get("negative_exposure") or curr.get("companies_negative") or [],
            "confidence":curr.get("confidence"),"actionability":action,
            "social_mentions":source_counts[0] or 0,"independent_evidence":source_counts[1] or 0,
        })
    return out


def query_opportunities(conn, limit=20):
    """Decision-first Opportunity objects; Thesis remains the evidence layer."""
    table = conn.execute(
        "SELECT 1 FROM sqlite_master WHERE type='table' AND name='investment_opportunities'"
    ).fetchone()
    if not table:
        return []
    rows = conn.execute(
        """SELECT opportunity_id,title,theme_ids_json,companies_json,primary_company,direction,time_horizon,
                  driver,industry_change,bottleneck,earnings_mechanism,valuation_question,market_expectations,
                  mispricing_hypothesis,catalysts_json,risks_json,invalidation_conditions_json,
                  missing_evidence_json,actionability,chain_completeness,opportunity_score,
                  thesis_quality_score,evidence_quality_score,earnings_impact_score,mispricing_score,
                  catalyst_score,risk_reward_score,one_line_thesis,why_now,ai_verdict,next_trigger,
                  positive_exposure_json,negative_exposure_json,authors_json,source_roots_json,
                  social_mention_count,independent_evidence_count,valuation_json,synthesis_json,
                  source_candidate_id,updated_at
           FROM investment_opportunities
           ORDER BY opportunity_score DESC, evidence_quality_score DESC, updated_at DESC LIMIT ?""",
        (limit,),
    ).fetchall()
    json_indexes = {2, 3, 14, 15, 16, 17, 31, 32, 33, 34, 37, 38}
    keys = [
        "opportunity_id", "title", "themes", "companies", "primary_company", "direction", "time_horizon",
        "driver", "industry_change", "bottleneck", "earnings_mechanism", "valuation_question",
        "market_expectations", "mispricing_hypothesis", "catalysts", "risks", "invalidation",
        "missing_evidence", "actionability", "chain_completeness", "opportunity_score",
        "thesis_quality_score", "evidence_quality_score", "earnings_impact_score", "mispricing_score",
        "catalyst_score", "risk_reward_score", "one_line_thesis", "why_now", "ai_verdict", "next_trigger",
        "positive_exposure", "negative_exposure", "authors", "source_roots", "social_mention_count",
        "independent_evidence_count", "valuation", "synthesis", "source_candidate_id", "updated_at",
    ]
    out = []
    has_best_expression = conn.execute(
        "SELECT 1 FROM sqlite_master WHERE type='table' AND name='opportunity_best_expressions'"
    ).fetchone()
    has_odds = conn.execute(
        "SELECT 1 FROM sqlite_master WHERE type='table' AND name='opportunity_odds'"
    ).fetchone()
    for row in rows:
        item = {}
        for index, key in enumerate(keys):
            item[key] = json.loads(row[index] or ("{}" if key in {"valuation", "synthesis"} else "[]")) if index in json_indexes else row[index]
        item["score_components"] = {
            "Thesis": item["thesis_quality_score"], "Evidence": item["evidence_quality_score"],
            "Earnings": item["earnings_impact_score"], "Mispricing": item["mispricing_score"],
            "Catalyst": item["catalyst_score"], "Risk / Reward": item["risk_reward_score"],
        }
        best = conn.execute(
            "SELECT analysis_json FROM opportunity_best_expressions WHERE opportunity_id=?",
            (item["opportunity_id"],),
        ).fetchone() if has_best_expression else None
        item["best_expression"] = json.loads(best[0]) if best and best[0] else None
        odds_rows = conn.execute(
            """SELECT ticker,company,currency,best_expression_rank,current_price,bear_fair_value,
                      base_fair_value,bull_fair_value,base_upside,bear_downside,reward_risk,
                      expected_return,earnings_gap,expectations_gap,odds_band,odds_score,
                      odds_status,valuation_confidence,thesis_confidence,analysis_json,as_of_date
               FROM opportunity_odds WHERE opportunity_id=?
               ORDER BY odds_score IS NULL,odds_score DESC,best_expression_rank""",
            (item["opportunity_id"],),
        ).fetchall() if has_odds else []
        item["odds"] = []
        for odds_row in odds_rows:
            analysis = json.loads(odds_row[19] or "{}")
            item["odds"].append({
                "ticker": odds_row[0], "company": odds_row[1], "currency": odds_row[2],
                "best_expression_rank": odds_row[3], "current_price": odds_row[4],
                "bear_fair_value": odds_row[5], "base_fair_value": odds_row[6],
                "bull_fair_value": odds_row[7], "base_upside": odds_row[8],
                "bear_downside": odds_row[9], "reward_risk": odds_row[10],
                "expected_return": odds_row[11], "earnings_gap": odds_row[12],
                "expectations_gap": odds_row[13], "odds_band": odds_row[14],
                "odds_score": odds_row[15], "odds_status": odds_row[16],
                "valuation_confidence": odds_row[17], "thesis_confidence": odds_row[18],
                "market_expectations": analysis.get("market_expectations") or {},
                "market_data": analysis.get("market_data") or {},
                "earnings_bridge": analysis.get("earnings_bridge") or {},
                "scenarios": analysis.get("scenarios") or [],
                "why_not_buy_now": analysis.get("why_not_buy_now") or "",
                "verdict": analysis.get("verdict") or "",
                "catalyst": analysis.get("catalyst") or "",
                "invalidation": analysis.get("invalidation") or "",
                "data_gaps": analysis.get("data_gaps") or [],
                "buy_gate_blockers": (analysis.get("computed") or {}).get("buy_gate_blockers") or [],
                "as_of_date": odds_row[20],
            })
        item["best_odds"] = item["odds"][0] if item["odds"] else None
        expression_ticker = ((item["best_expression"] or {}).get("best_expression") or {}).get("ticker")
        item["best_expression_vs_best_odds"] = {
            "best_expression": expression_ticker,
            "best_odds": item["best_odds"]["ticker"] if item["best_odds"] else None,
            "same_security": bool(expression_ticker and item["best_odds"] and expression_ticker == item["best_odds"]["ticker"]),
        }
        out.append(item)
    return out


def query_opportunity_funnel(conn):
    """Latest auditable funnel snapshot; definitions travel with the counts."""
    table = conn.execute(
        "SELECT 1 FROM sqlite_master WHERE type='table' AND name='opportunity_funnel_snapshots'"
    ).fetchone()
    if not table:
        return {"counts": {}, "definitions": {}, "created_at": None}
    row = conn.execute(
        "SELECT counts_json,definitions_json,created_at FROM opportunity_funnel_snapshots ORDER BY created_at DESC LIMIT 1"
    ).fetchone()
    if not row:
        return {"counts": {}, "definitions": {}, "created_at": None}
    return {"counts": json.loads(row[0]), "definitions": json.loads(row[1]), "created_at": row[2]}


def query_ai_cost_panel(conn):
    """Risk-aware cost summary. PENDING rows remain visible and reserve estimated cost."""
    enabled = os.getenv("AI_ENABLED", "false").strip().lower() in {"1", "true", "yes", "on"}
    expensive = os.getenv("ALLOW_EXPENSIVE_AI_JOB", "false").strip().lower() in {"1", "true", "yes", "on"}
    panel = {
        "today_cost": 0.0, "days_7_cost": 0.0, "days_30_cost": 0.0, "calls_today": 0,
        "by_stage": [], "by_model": [], "pending_unknown_calls": 0, "pending_unknown_risk": 0.0,
        "daily_budget": float(os.getenv("AI_MAX_DAILY_COST_USD", "1.00")),
        "run_budget": float(os.getenv("AI_MAX_COST_PER_RUN_USD", "0.50")),
        "call_limit": int(os.getenv("AI_MAX_CALLS_PER_RUN", "20")),
        "ai_enabled": enabled, "expensive_jobs_enabled": expensive,
    }
    table = conn.execute("SELECT 1 FROM sqlite_master WHERE type='table' AND name='ai_usage_ledger'").fetchone()
    if not table:
        return panel
    risk_expr = "CASE WHEN actual_cost_if_available IS NOT NULL THEN actual_cost_if_available ELSE estimated_cost END"
    for key, modifier in (("today_cost", "start of day"), ("days_7_cost", "-6 days"), ("days_30_cost", "-29 days")):
        panel[key] = round(float(conn.execute(
            f"""SELECT COALESCE(SUM({risk_expr}),0) FROM ai_usage_ledger
                WHERE request_started_at>=strftime('%Y-%m-%dT00:00:00Z','now',?)
                  AND status IN ('PENDING','SUCCESS','FAILED','CANCELLED','UNKNOWN_COST')""",
            (modifier,),
        ).fetchone()[0]), 8)
    panel["calls_today"] = int(conn.execute(
        """SELECT COUNT(*) FROM ai_usage_ledger WHERE request_started_at>=strftime('%Y-%m-%dT00:00:00Z','now')
           AND status IN ('PENDING','SUCCESS','FAILED','CANCELLED','UNKNOWN_COST')"""
    ).fetchone()[0])
    panel["by_stage"] = [
        {"name": row[0], "cost": round(float(row[1]), 8), "calls": int(row[2])}
        for row in conn.execute(
            f"""SELECT stage,COALESCE(SUM({risk_expr}),0),COUNT(*) FROM ai_usage_ledger
                WHERE request_started_at>=strftime('%Y-%m-%dT00:00:00Z','now')
                  AND status IN ('PENDING','SUCCESS','FAILED','CANCELLED','UNKNOWN_COST')
                GROUP BY stage ORDER BY 2 DESC"""
        ).fetchall()
    ]
    panel["by_model"] = [
        {"name": row[0], "cost": round(float(row[1]), 8), "calls": int(row[2])}
        for row in conn.execute(
            f"""SELECT model,COALESCE(SUM({risk_expr}),0),COUNT(*) FROM ai_usage_ledger
                WHERE request_started_at>=strftime('%Y-%m-%dT00:00:00Z','now')
                  AND status IN ('PENDING','SUCCESS','FAILED','CANCELLED','UNKNOWN_COST')
                GROUP BY model ORDER BY 2 DESC"""
        ).fetchall()
    ]
    pending = conn.execute(
        """SELECT COUNT(*),COALESCE(SUM(estimated_cost),0) FROM ai_usage_ledger
           WHERE status IN ('PENDING','UNKNOWN_COST')"""
    ).fetchone()
    panel["pending_unknown_calls"] = int(pending[0])
    panel["pending_unknown_risk"] = round(float(pending[1]), 8)
    return panel


def query_tickers(conn):
    """区块3 用. 包装 select_dashboard_ticker_targets (共享函数) + 查价格 + 排序.

    复现口径跟 select_dashboard_ticker_targets 一致 (保证区块04 展示跟 refresh 同步).
    1. direction IN ('long','short') 排除 neutral/retro/disc
    2. 按 (kol, ticker) 聚合, latest_pub + earliest_pub + n_calls
    3. 排除 < DASHBOARD_MIN_DAYS (5d) 跟太近的喊单
    4. 强项标的 (in_field=True) 优先, 圈外 (in_field=False) 标 '圈外·追高'
    5. 无价格 (call_price=None) 归最后
    6. 截 DASHBOARD_TICKER_LIMIT (30)
    """
    targets = select_dashboard_ticker_targets(conn, limit=DASHBOARD_TICKER_LIMIT)
    rows_out = []
    for t in targets:
        call_price, now_price, raw_pct, excess_pct = get_prices(conn, t["ticker"], t["call_date"])
        in_field = t["in_field"]
        has_price = call_price is not None and now_price is not None
        rows_out.append({
            "ticker": t["ticker"], "kol": t["kol"],
            "direction": t["direction"],
            "called_at": t["earliest_pub"],
            "earliest_call": t["earliest_pub"],
            "days_since": t["days_since"],
            "call_price": call_price, "now_price": now_price,
            "raw_pct": raw_pct, "excess_pct": excess_pct,
            "in_field": in_field,
            "has_price": has_price,
            "n_calls": t["n_calls"],
            "priority": (
                0 if in_field and has_price else
                1 if in_field else
                2 if has_price else
                3  # 圈外无价格 → 最后
            ),
        })

    # 排序: 强项+有价格 → 强项无价格 → 圈外有价格 → 圈外无价格 (然后按 called_at desc)
    rows_out.sort(key=lambda r: (r["priority"], -r["days_since"]))
    out = rows_out[:DASHBOARD_TICKER_LIMIT]

    for i, t in enumerate(out, 1):
        marker = "✓" if t["in_field"] else "⚠️"
        pmark = "💰" if t["has_price"] else "❓"
        print(f"    {i:2d}. {marker}{pmark} {t['kol']:10s} {t['ticker']:8s} {t['direction']:5s} "
              f"called={t['called_at'][:10]} ({t['days_since']}d ago) "
              f"call={t['call_price']} now={t['now_price']} raw={t['raw_pct']} exc={t['excess_pct']}", flush=True)
    return out


def query_call_performance(conn):
    """返回人物×标的首次喊单的方向收益，供前端汇总。

    一条推文包含多个 ticker 时拆开；同一人物重复提及同一 ticker 只计一次，
    方向和起始价格取窗口内第一次明确喊单，后续仅累计提及次数。
    long 方向收益 = 标的涨跌幅，short 方向收益 = -标的涨跌幅。
    只读 ticker_prices 缓存，不在 build 阶段发起额外行情请求。
    """
    events = query_call_performance_events(conn, days=370)
    grouped = {}
    for event in events:
        post_id = event["post_id"]
        src = event["source_id"]
        direction = event["direction"]
        ticker = event["ticker"]
        bottleneck = event["bottleneck"]
        published_at = event["published_at"]
        raw_text = event["raw_text"]
        raw_url = event["raw_url"]
        kol = SRC2KOL.get(src, src.replace("tw_", ""))
        key = (kol, ticker)
        if key not in grouped:
            grouped[key] = {
                "post_id": post_id, "kol": kol, "ticker": ticker,
                "direction": direction, "published_at": published_at,
                "latest_published_at": published_at, "bottleneck": bottleneck,
                "n_mentions": 1,
                "raw_text": raw_text or "",
                "raw_url": raw_url or f"https://x.com/{src.replace('tw_', '')}/status/{post_id}",
            }
        else:
            grouped[key]["latest_published_at"] = published_at
            grouped[key]["n_mentions"] += 1
    out = []
    for row in grouped.values():
            ticker = row["ticker"]
            call_date = row["published_at"][:10]
            cached = conn.execute("""
                SELECT call_price, now_price, now_date
                FROM ticker_prices WHERE ticker=? AND pub_date=?
            """, (ticker, call_date)).fetchone()
            call_price = cached[0] if cached else None
            now_price = cached[1] if cached else None
            now_date = cached[2] if cached else None
            raw_return = None
            directional_return = None
            if call_price not in (None, 0) and now_price is not None:
                raw_return = round((now_price / call_price - 1) * 100, 2)
                directional_return = raw_return if row["direction"] == "long" else -raw_return
            row.update({
                "call_date": call_date,
                "call_price": call_price, "now_price": now_price,
                "now_date": now_date, "raw_return": raw_return,
                "directional_return": directional_return,
                "in_field": is_in_field(row["kol"], ticker, row["bottleneck"]),
            })
            out.append(row)
    return out


def validate_call_performance_coverage(rows):
    """禁止人物表现全无行情时仍发布看似成功的页面。"""
    if not rows:
        return
    covered = sum(
        1 for row in rows
        if row.get("call_price") not in (None, 0)
        and row.get("now_price") is not None
    )
    coverage = covered / len(rows)
    print(f"  call performance price coverage: "
          f"{covered}/{len(rows)} ({coverage:.1%})", flush=True)
    if covered == 0:
        raise RuntimeError(
            "人物表现行情覆盖为 0，停止构建与发布；请先刷新逐笔喊单价格")


def load_summaries():
    """读取 intel_gen_summaries.py 预生成的 26 段总结.

    检查 summaries.json 是否存在 + 是否过期:
    - 不存在 → 报错退出 (不让 build 用空数据冒充)
    - 存在但 generated_at 距今 > 36h → 警告 (旧总结仍写入, 但前端显示过期标志)
    """
    p = pathlib.Path(__file__).with_name("summaries.json")
    if not p.exists():
        print("  ✗ summaries.json 不存在 — 请先跑 intel_gen_summaries.py", flush=True)
        print("    不可用空数据冒充今日总结", flush=True)
        raise SystemExit(2)
    try:
        data = json.loads(p.read_text(encoding="utf-8"))
    except Exception as e:
        print(f"  ✗ summaries.json 解析失败: {e}", flush=True)
        raise SystemExit(2)
    # 检查 generated_at 过期 (soft warning)
    gen_at = data.get("generated_at")
    if gen_at:
        try:
            gen_dt = datetime.datetime.fromisoformat(gen_at.replace("Z", "+00:00"))
            age_h = (datetime.datetime.now(datetime.timezone.utc) - gen_dt).total_seconds() / 3600
            if age_h > 36:
                print(f"  ⚠ summaries.json 已生成 {age_h:.1f}h (>36h), 前端会标过期", flush=True)
        except Exception:
            pass
    return data


def _safe_pct(value, decimals=1):
    """格式化百分比, None → '—'. 不输出 'null%' / 'None%'."""
    if value is None:
        return "—"
    try:
        return f"{float(value):+.{decimals}f}"
    except (TypeError, ValueError):
        return "—"


def _safe_pp(value, decimals=1):
    """格式化百分点差 (excess_pct, 单位 pp). None → '—'."""
    if value is None:
        return "—"
    try:
        return f"{float(value):+.{decimals}f}pp"
    except (TypeError, ValueError):
        return "—"


def _safe_price(value):
    """格式化价格, None → '—'. 不输出 '$null' / '$None'."""
    if value is None:
        return "—"
    try:
        return f"${float(value):.2f}"
    except (TypeError, ValueError):
        return "—"


def _annotate_tickers(tickers):
    """给 tickers 加渲染友好的 *_str 字段, 防止前端出现 null 字样.

    输入: tickers 列表 (来自 query_tickers), 含 raw_pct/excess_pct/call_price/now_price (可能 None)
    输出: 同样列表, 加 price_call_str / price_now_str / raw_pct_str / excess_pct_str
    """
    for t in tickers:
        t["price_call_str"] = _safe_price(t.get("call_price"))
        t["price_now_str"] = _safe_price(t.get("now_price"))
        t["raw_pct_str"] = _safe_pct(t.get("raw_pct"))
        t["excess_pct_str"] = _safe_pp(t.get("excess_pct"))
        # direction 不能 None (query_tickers 已过滤 long/short)
    return tickers


def main():
    try:
        conn=sqlite3.connect(DB, timeout=30)
        init_price_cache(conn)
        refresh_sector_snapshots(conn)
        data = query_extractions(conn)
        print(f"  extractions: {len(data)}", flush=True)
        tickers = query_tickers(conn)
        print(f"  tickers: {len(tickers)}", flush=True)
        call_performance = query_call_performance(conn)
        validate_call_performance_coverage(call_performance)
        print(f"  call performance: {len(call_performance)}", flush=True)
        # 今日窗口 (北京自然日) 统计 + records + 真实 build metadata
        today_stats = query_today_stats(conn)
        today_records = query_today_records(conn)
        build_meta = build_metadata(conn)
        thesis_changes = query_thesis_changes(conn)
        opportunities = query_opportunities(conn)
        opportunity_funnel = query_opportunity_funnel(conn)
        ai_cost_panel = query_ai_cost_panel(conn)
        print(f"  24h window: {build_meta['window_label']} "
              f"posts={today_stats['n_posts_24h']} "
              f"directional={today_stats['n_directional_24h']} "
              f"empty_reason={today_stats['empty_reason']!r}", flush=True)
        print(f"  build time:  {build_meta['build_time_label']} "
              f"(data_until={build_meta.get('data_until_label')})", flush=True)
        conn.close()
        summaries = load_summaries()
        tickers = _annotate_tickers(tickers)
        html = TEMPLATE.read_text(encoding="utf-8")
        html = html.replace("__RECORDS__",   json.dumps(data, ensure_ascii=False))
        html = html.replace("__KOLS__",      json.dumps(KOLS, ensure_ascii=False))
        html = html.replace("__TICKERS__",   json.dumps(tickers, ensure_ascii=False))
        html = html.replace("__CALL_PERFORMANCE__", json.dumps(call_performance, ensure_ascii=False))
        html = html.replace("__SUMMARIES__", json.dumps(summaries, ensure_ascii=False))
        html = html.replace("__TODAY_STATS__",   json.dumps(today_stats, ensure_ascii=False))
        html = html.replace("__TODAY_RECORDS__", json.dumps(today_records, ensure_ascii=False))
        html = html.replace("__BUILD_META__",    json.dumps(build_meta, ensure_ascii=False))
        html = html.replace("__THESIS_CHANGES__", json.dumps(thesis_changes, ensure_ascii=False))
        html = html.replace("__OPPORTUNITIES__", json.dumps(opportunities, ensure_ascii=False))
        html = html.replace("__OPPORTUNITY_FUNNEL__", json.dumps(opportunity_funnel, ensure_ascii=False))
        html = html.replace("__AI_COST_PANEL__", json.dumps(ai_cost_panel, ensure_ascii=False))
        OUT.write_text(html, encoding="utf-8")
        # 检查 null 字样没渲染到 HTML (兜底, 即使前端处理对了)
        with open(OUT, 'r', encoding='utf-8') as f:
            html_text = f.read()
        bad_patterns = ['$null', 'null%', 'nullpp', 'null USD', '$None']
        for pat in bad_patterns:
            if pat in html_text:
                print(f"  ✗ dashboard.html 包含禁用字样: {pat!r}", flush=True)
                raise SystemExit(3)
        print(f"dashboard.html: {len(data)} extractions, {len(tickers)} tickers, summaries=real", flush=True)
        hit = sum(1 for t in tickers if t['raw_pct'] is not None)
        print(f"  price hit: {hit}/{len(tickers)} ({hit*100//max(1,len(tickers))}%)", flush=True)
    except SystemExit:
        raise
    except Exception as e:
        import traceback
        traceback.print_exc()
        print(f"ERROR: {e}", flush=True)
        raise

if __name__=="__main__":
    main()
