#!/usr/bin/env python3
"""scripts/dashboard/common.py — Dashboard 共享工具

设计: 时间窗口基于"过去 24 小时滚动", 而不是 UTC 24h 滑动, 也不是北京自然日.

为什么不用北京自然日 00:00:
- 生产顺序: 06:00 抓取 → 06:20 Dashboard
- 06:20 时 "今天 00:00 ~ 06:20" 只覆盖 6 小时 20 分钟, 而不是完整一天
- 用户视角 "今日总结" = "自从昨天 06:20 到现在" 的内容, 而不是 "00:00 ~ 06:20"
- 改用 "24h 滚动" (现在 - 24h ~ 现在), 跟 cron 节奏对齐, 跟 "上次抓取" 边界对齐

为什么不用 UTC 24h 滑动:
- 北京 06:20 = UTC 22:20 (前一天), 跟美东时间更接近
- 用 UTC 24h 滑动会产生奇怪的 "日界", 跟 4 大V 发推节奏对不上
- 用 now - 24h (UTC) 即可, 跟抓取/抽取/Dashboard 一套共用一个 now

约束:
- intel_gen_summaries.py 的 today/0M / build_dashboard.py 的 query_today_stats /
  query_today_records / dashboard.template.html 的 1D 切窗 / consensus[0] /
  person[*][0] 全部基于同一 now (build_metadata) 算出来的 24h 窗口
- 任何地方都不再使用 "北京今日 00:00" 作为窗口起点
"""
from __future__ import annotations
import json
from datetime import datetime, timedelta, timezone

try:
    from zoneinfo import ZoneInfo
    CN_TZ = ZoneInfo("Asia/Shanghai")
except ImportError:  # pragma: no cover
    CN_TZ = timezone(timedelta(hours=8))


def cn_now() -> datetime:
    """当前 UTC datetime (带 tzinfo)."""
    return datetime.now(timezone.utc)


def cn_recent_24h_window_utc(end: datetime | None = None) -> tuple[str, str]:
    """过去 24 小时滚动窗口: [now - 24h, now] UTC ISO.

    生产环境用法:
    - 06:00 抓取 → 06:20 Dashboard, "今日" = [06:20 昨天, 06:20 今天)
    - 跟 cron 节奏对齐, 跟 "上次抓取" 边界对齐
    - 跟 consensus[0] / person[*][0] / 1D 明细 / 顶部今日统计 全部共用

    跟 UTC 24h 滑动的区别:
    - UTC 24h 滑动: 跟 4 大V 发推节奏 (美东盘) 对不齐, 日界奇怪
    - 24h 滚动 (now - 24h): 跟抓取节奏对齐, 跟用户 "我上一次看 dashboard 之后发生了什么" 对齐
    """
    if end is None:
        end = cn_now()
    start = end - timedelta(hours=24)
    return start.isoformat(), end.isoformat()


def cn_window_long_utc(days: int, end: datetime | None = None) -> tuple[str, str]:
    """近 N 天滑动窗口: [now - N days, now] UTC ISO. 用于 1M/3M/6M/12M."""
    if end is None:
        end = cn_now()
    start = end - timedelta(days=days)
    return start.isoformat(), end.isoformat()


def cn_format(utc_dt: datetime, fmt: str = "%Y-%m-%d %H:%M CST") -> str:
    """UTC datetime 转 北京时间格式化字符串."""
    cn = utc_dt.astimezone(CN_TZ)
    return cn.strftime(fmt)


def build_metadata(conn=None) -> dict:
    """返回 build 时需要的元数据: 真实生成时间 + 24h 窗口 + 数据截止.

    conn: 可选, 用于查 MAX(published_at). 不传则 data_until=None.

    24h 窗口 (window_start_utc / window_end_utc) 给 template 显示 "过去 24 小时" 用,
    跟 intel_gen_summaries / query_today_stats / query_today_records 共用同一对值.
    """
    now = cn_now()
    win_start, win_end = cn_recent_24h_window_utc(now)
    data_until = None
    if conn is not None:
        try:
            r = conn.execute("SELECT MAX(published_at) FROM raw_posts").fetchone()
            if r and r[0]:
                data_until = r[0]
        except Exception:
            pass
    return {
        "build_time_utc": now.isoformat(),
        "build_time_label": cn_format(now, "%Y-%m-%d %H:%M CST"),
        "build_time_date_label": cn_format(now, "%Y-%m-%d"),
        "window_start_utc": win_start,        # 24h 窗口起点 (now - 24h)
        "window_end_utc": win_end,             # 24h 窗口终点 (now)
        "window_label": "过去 24 小时",
        "data_until_utc": data_until,
        "data_until_label": cn_format(datetime.fromisoformat(data_until.replace("Z", "+00:00")), "%Y-%m-%d %H:%M CST") if data_until else None,
        "tz_label": "Asia/Shanghai",
    }


def query_today_stats(conn) -> dict:
    """24h 滚动窗口内的 posts / 方向性判断 / 卡点统计.

    返回结构 (供 build_dashboard 注入 __TODAY_STATS__):
    {
      "n_posts_24h": int,            # raw_posts 数 (过去 24 小时)
      "n_directional_24h": int,      # 有效方向性判断 (long/short) 数
      "n_neutral_24h": int,           # neutral 但有 ticker/bottleneck 的
      "n_bottlenecks_24h": int,       # 涉及的不同卡点数
      "hot_bottlenecks_24h": [{"name": str, "count": int}, ...],
      "by_kol_24h": {kol: int, ...},  # 各 KOL 24h 内 posts 数
      "window_start_utc": str, "window_end_utc": str, "window_label": "过去 24 小时",
      "empty_reason": str | None,
    }

    empty_reason 语义:
    - "no_posts": 24h 窗口 raw_posts = 0 (过去 24h 没抓到新推文)
    - "no_directional": 有 posts 但 long/short 判断 = 0 (有推文但没方向性投资判断)
    - None: 有 posts 也有 directional
    """
    start, end = cn_recent_24h_window_utc()
    rows = conn.execute("""
        SELECT r.post_id, r.source_id, r.published_at,
               e.direction, e.bottleneck, e.ticker, e.is_retrospective, e.is_disclosure
        FROM raw_posts r
        LEFT JOIN extractions_intel e ON r.post_id = e.post_id
        WHERE r.published_at >= ? AND r.published_at < ?
    """, (start, end)).fetchall()

    posts_seen: dict = {}
    for r in rows:
        pid, src, pub, direction, bk, ticker, retro, disc = r
        if pid not in posts_seen:
            posts_seen[pid] = {"src": src, "pub": pub,
                                "direction": direction, "bk": bk, "ticker": ticker,
                                "retro": retro or 0, "disc": disc or 0}

    n_posts = len(posts_seen)

    SRC2KOL = {
        "tw_jukan05": "jukan", "tw_aleabitoreddit": "serenity",
        "tw_zephyr_z9": "zephyr", "tw_austinsemis": "austin",
    }

    directional = 0
    neutral_with_signal = 0
    by_kol = {"jukan": 0, "serenity": 0, "zephyr": 0, "austin": 0}
    bk_count: dict[str, int] = {}

    for pid, p in posts_seen.items():
        kol = SRC2KOL.get(p["src"], p["src"].replace("tw_", ""))
        if kol in by_kol:
            by_kol[kol] += 1
        if p["direction"] and p["direction"] in ("long", "short") and not p["retro"] and not p["disc"]:
            directional += 1
        elif p["direction"] == "neutral" and (p["bk"] or p["ticker"]):
            neutral_with_signal += 1
        if p["bk"] and not p["retro"] and not p["disc"]:
            bk_count[p["bk"]] = bk_count.get(p["bk"], 0) + 1

    hot_bk = sorted(bk_count.items(), key=lambda x: -x[1])[:3]
    hot_bk_out = [{"name": b, "count": n} for b, n in hot_bk]

    if n_posts == 0:
        empty_reason = "no_posts"
    elif directional == 0:
        empty_reason = "no_directional"
    else:
        empty_reason = None

    return {
        "n_posts_24h": n_posts,
        "n_directional_24h": directional,
        "n_neutral_with_signal_24h": neutral_with_signal,
        "n_bottlenecks_24h": len(bk_count),
        "hot_bottlenecks_24h": hot_bk_out,
        "by_kol_24h": by_kol,
        "window_start_utc": start,
        "window_end_utc": end,
        "window_label": "过去 24 小时",
        "empty_reason": empty_reason,
    }


def query_today_records(conn) -> list[dict]:
    """24h 滚动窗口内的 raw_posts + extractions 完整 records, 供 renderFeed(1D) / renderStance(1D) 用.

    口径修复 (2026-07-13):
    - 主表是 raw_posts (LEFT JOIN extractions_intel) — 24h 内每条推文都返回一条
    - 没有 extraction 的推文仍会出现, direction="neutral", summary=raw_text
    - 同一 post_id 多条 extraction → 合并为一条 (ticker union, 优先保留 long/short)
    - 跟 build_dashboard.query_extractions 同结构 (post_id, kol, direction, ticker, ...)

    返回 list[dict]:
    {
        "post_id", "kol", "source_id", "published_at", "raw_text", "raw_url",
        "direction", "ticker" (list), "company" (list), "bottleneck" (str|None),
        "attribution" (str|None), "rebuts" (str|None), "summary" (str|None),
        "is_retro", "is_disc", "is_selfret" (int),
    }
    """
    import json as _json
    start, end = cn_recent_24h_window_utc()
    # LEFT JOIN: raw_posts 为主, 没有 extraction 也有记录
    rows = conn.execute("""
        SELECT r.post_id, r.source_id, r.published_at, r.raw_text, r.raw_url,
               e.direction, e.ticker, e.company, e.bottleneck, e.attribution,
               e.rebuts_narrative, e.summary_100,
               e.is_retrospective, e.is_disclosure, e.is_self_reported_returns
        FROM raw_posts r
        LEFT JOIN extractions_intel e ON r.post_id = e.post_id
        WHERE r.published_at >= ? AND r.published_at < ?
        ORDER BY r.published_at DESC
    """, (start, end)).fetchall()

    SRC2KOL = {
        "tw_jukan05": "jukan", "tw_aleabitoreddit": "serenity",
        "tw_zephyr_z9": "zephyr", "tw_austinsemis": "austin",
    }

    # 按 post_id 合并 (同一 post 可能多条 extraction, 例如同一推文被不同 LLM prompt 提取多次)
    by_post: dict = {}
    for x in rows:
        (post_id, src, pub, raw_text, raw_url,
         direction, ticker, company, bk, attr, rebuts, summ,
         retro, disc, selfret) = x
        if post_id not in by_post:
            by_post[post_id] = {
                "post_id": post_id,
                "kol": SRC2KOL.get(src, src.replace("tw_", "")),
                "source_id": src,
                "published_at": pub,
                "raw_text": raw_text or "",
                "raw_url": raw_url or f"https://x.com/{src.replace('tw_', '')}/status/{post_id}",
                "_directions": [],
                "_tickers": [],
                "_companies": [],
                "_bottlenecks": [],
                "_attrs": [],
                "_rebuts": [],
                "_summaries": [],
                "_retro": 0, "_disc": 0, "_selfret": 0,
            }
        rec = by_post[post_id]
        if direction:
            rec["_directions"].append(direction)
        if ticker:
            try:
                rec["_tickers"].extend(_json.loads(ticker) if ticker.startswith("[") else [ticker])
            except Exception:
                rec["_tickers"].append(ticker)
        if company:
            try:
                rec["_companies"].extend(_json.loads(company) if company.startswith("[") else [company])
            except Exception:
                rec["_companies"].append(company)
        if bk: rec["_bottlenecks"].append(bk)
        if attr: rec["_attrs"].append(attr)
        if rebuts: rec["_rebuts"].append(rebuts)
        if summ: rec["_summaries"].append(summ)
        rec["_retro"] = max(rec["_retro"], retro or 0)
        rec["_disc"] = max(rec["_disc"], disc or 0)
        rec["_selfret"] = max(rec["_selfret"], selfret or 0)

    out = []
    for post_id, rec in by_post.items():
        # 合并 direction: 优先 long/short, 没有就 neutral
        directions = rec["_directions"]
        if "long" in directions:
            direction = "long"
        elif "short" in directions:
            direction = "short"
        elif directions:
            direction = directions[0]  # neutral 或其他
        else:
            direction = "neutral"
        # ticker / company / bottleneck / attribution / rebuts / summary 去重
        tickers = list(dict.fromkeys(rec["_tickers"]))  # 保序去重
        companies = list(dict.fromkeys(rec["_companies"]))
        bottleneck = rec["_bottlenecks"][0] if rec["_bottlenecks"] else None
        attribution = rec["_attrs"][0] if rec["_attrs"] else None
        rebuts = rec["_rebuts"][0] if rec["_rebuts"] else None
        # summary 优先 LLM 抽取的, 没有就用 raw_text 截断
        summary = rec["_summaries"][0] if rec["_summaries"] else (rec["raw_text"][:200] if rec["raw_text"] else None)
        out.append({
            "post_id": post_id,
            "kol": rec["kol"],
            "source_id": rec["source_id"],
            "published_at": rec["published_at"],
            "direction": direction,
            "ticker": tickers,
            "company": companies,
            "bottleneck": bottleneck,
            "attribution": attribution,
            "rebuts": rebuts,
            "summary": summary,
            "is_retro": rec["_retro"],
            "is_disc": rec["_disc"],
            "is_selfret": rec["_selfret"],
            "raw_text": rec["raw_text"],
            "raw_url": rec["raw_url"],
        })
    # 再次按 published_at 降序 (合并可能打乱顺序)
    out.sort(key=lambda r: r["published_at"], reverse=True)
    return out


# ============================================================================
# 标的筛选共享函数 (区块04 展示口径)
# ============================================================================
# Source ID → KOL 短名 (跟 raw_posts / extractions_intel 一致)
SRC2KOL = {
    "tw_jukan05": "jukan", "tw_aleabitoreddit": "serenity",
    "tw_zephyr_z9": "zephyr", "tw_austinsemis": "austin",
}

# 4 大V 能力圈画像 (跟 build_dashboard.py KOLS 同步)
KOLS = {
    "jukan": {"key": "jukan", "name": "Jukan", "handle": "@jukan05", "type": "signal",
              "typeLabel": "信号源 · signal",
              "desc": "100% 推文带 ticker，会明确喊方向。胜率高，几乎不做空。",
              "strong": ["存储", "HBM", "代工", "卡点"],
              "weak": ["看多 AI 龙头(跑输板块)"]},
    "serenity": {"key": "serenity", "name": "Serenity", "handle": "@aleabitoreddit", "type": "cognition",
              "typeLabel": "瓶颈专家 · cognition",
              "desc": "光通信/CPO 瓶颈专家，会喊标的，但顺势押龙头、易追高。",
              "strong": ["光通信", "CPO", "InP", "化合物半导体"],
              "weak": ["整体追高", "tier_B 清单=板块β"]},
    "zephyr": {"key": "zephyr", "name": "zephyr", "handle": "@zephyr_z9", "type": "cognition",
              "typeLabel": "卡点雷达 · cognition",
              "desc": "产业卡点雷达，看多卡点极准(94.8%)，但看空系统性错。",
              "strong": ["存储", "光通信", "HBM", "电力", "卡点"],
              "weak": ["看空全错(0/22)", "AI 泡沫论盲区"]},
    "austin": {"key": "austin", "name": "Austin", "handle": "@austinsemis", "type": "cognition",
              "typeLabel": "商业格局 · cognition",
              "desc": "AI 芯片商业格局分析，AMD/CUDA 护城河有洞察。认知源非信号源。",
              "strong": ["商业格局", "AMD/CUDA 护城河", "Foundry 模式"],
              "weak": ["看多龙头(跑输板块)", "看空全错(1/8)"]},
}

# 4 大V 真正强项领域的 ticker 白名单 (LLM bottleneck 误抽太多, 改用 ticker 黑/白名单二次过滤)
KOL_TICKERS = {
    "jukan": {  # 信号源, 100% 推文带 ticker, 强存储/HBM/代工
        "in_field": ["MU", "SNDK", "DRAM", "AXTI", "ASTS", "RKLB", "TSM", "NVDA", "AMD", "AVGO", "NBIS"],
    },
    "serenity": {  # 光通信/CPO/InP/化合物半导体专家
        "in_field": ["AAOI", "SIVE", "COHR", "LITE", "POET", "AEVA", "AEHR", "MRVL", "JBL", "GFS", "AOSL", "POWI",
                     "IQE", "SOI", "XFAB", "TSEM", "WOLF", "NVTS", "TSM", "NOK"],
        "out_of_field": ["TSLA", "MSFT", "META", "GOOGL", "AMZN", "AVGO", "BRK.A", "ASML", "SPY", "DELL", "CRM",
                         "PLTR", "SNAP", "INTC", "AAPL", "NVDA", "AMD", "RKLB", "NBIS", "ASTS", "AXTI", "MU",
                         "093370", "6324", "2454", "688017", "AIXA", "LPK", "SPCX"],
    },
    "zephyr": {  # 存储/光通信/HBM/电力/卡点
        "in_field": ["MU", "SNDK", "DRAM", "NBIS", "AAOI", "LITE", "POET", "SIVE", "JBL", "COHR", "AEVA", "AEHR",
                     "TSM", "VPG", "INTC", "AMD", "MRVL"],
        "out_of_field": ["TSLA", "MSFT", "META", "GOOGL", "AMZN", "AVGO", "BRK.A", "ASML", "SPY", "DELL", "CRM",
                         "PLTR", "SNAP", "AAPL", "AOSL", "POWI", "IQE", "SOI", "XFAB", "TSEM", "WOLF", "NVTS",
                         "NOK", "RKLB", "ASTS", "AXTI", "093370", "6324", "2454", "688017", "AIXA", "LPK",
                         "SPCX", "GFS"],
    },
    "austin": {  # 商业洞察, 看多 AI 龙头 (但跑输板块). 主要认知源, 信号弱
        "in_field": ["AMD", "NVDA", "MU", "AVGO", "TSM", "INTC", "MRVL", "GOOGL", "META", "MSFT", "AMZN"],
        "out_of_field": ["TSLA", "BRK.A", "ASML", "SPY", "DELL", "CRM", "PLTR", "SNAP", "AAPL", "AOSL", "POWI",
                         "IQE", "SOI", "XFAB", "TSEM", "WOLF", "NVTS", "NOK", "SIVE", "JBL", "GFS", "RKLB",
                         "ASTS", "AXTI", "AEVA", "AEHR", "COHR", "LITE", "POET", "AAOI", "093370", "6324",
                         "2454", "688017", "AIXA", "LPK", "SPCX", "NBIS", "SNDK", "DRAM", "VPG"],
    },
}

# Dashboard 标的展示参数 (跟区块04 一致)
DASHBOARD_TICKER_LIMIT = 30  # 最终展示条数
DASHBOARD_MIN_DAYS = 5  # 排除 < 5d 的喊单 (还没涨跌)


def parse_json_arr(s):
    """跟 build_dashboard.py parse_json_arr 一致. 解析 JSON 数组字符串, 兼容单 ticker."""
    if not s or not isinstance(s, str):
        return []
    s = s.strip()
    if s.startswith("["):
        try:
            return json.loads(s)
        except Exception:
            return []
    if s:
        return [s]
    return []


def is_in_field(kol: str, ticker: str, bottleneck: str | None) -> bool:
    """跟 build_dashboard.is_in_field 一致. 判定 (kol, ticker) 是否在 KOL 强项领域.

    1. ticker 在 KOL_TICKERS[kol]['in_field'] → True
    2. ticker 在 KOL_TICKERS[kol]['out_of_field'] → False
    3. fallback: LLM bottleneck 匹配 strong 字段
    """
    if kol not in KOL_TICKERS:
        return False
    spec = KOL_TICKERS[kol]
    if ticker in spec.get("in_field", []):
        return True
    if ticker in spec.get("out_of_field", []):
        return False
    if bottleneck:
        for s in KOLS.get(kol, {}).get("strong", []):
            if s in bottleneck or bottleneck in s:
                return True
    return False


def select_dashboard_ticker_targets(conn, limit: int = DASHBOARD_TICKER_LIMIT) -> list[dict]:
    """Dashboard 区块04 展示的标的 = refresh 同步的目标. 共享函数 (build_dashboard / refresh_prices_polygon 都调).

    筛选口径 (跟 build_dashboard.query_tickers 完全一致):
    1. direction IN ('long', 'short') — 排除 neutral
    2. is_retrospective = 0, is_disclosure = 0
    3. ticker NOT NULL
    4. 按 (kol, ticker) 聚合, 保留 latest_pub / earliest_pub / n_calls
    5. 排除 < DASHBOARD_MIN_DAYS (5d) 的喊单 (没涨跌)
    6. 排序: 强项+有价格 (priority 0) > 强项无价格 (1) > 圈外有价格 (2) > 圈外无价格 (3)
    7. 二级排序: -days_since (最近的在前)
    8. 截 limit (默认 30 条)

    返回 list[dict], 每个元素:
    {
        "ticker": str, "kol": str, "source_id": str,
        "direction": "long"|"short", "bottleneck": str|None,
        "latest_pub": ISO 8601, "earliest_pub": ISO 8601, "call_date": "YYYY-MM-DD",
        "n_calls": int, "days_since": int, "in_field": bool,
    }
    """
    print("  select_dashboard_ticker_targets: 开始", flush=True)
    rows = conn.execute("""
        SELECT e.source_id, e.ticker, e.direction, e.bottleneck, r.published_at
        FROM extractions_intel e
        JOIN raw_posts r ON r.post_id = e.post_id
        WHERE e.direction IN ('long', 'short')
          AND e.is_retrospective = 0 AND e.is_disclosure = 0
          AND e.ticker IS NOT NULL
        ORDER BY r.published_at DESC
    """).fetchall()

    # (kol, ticker) 维度聚合
    by_kol_tk: dict = {}
    for src, ticker_json, direction, bk, pub in rows:
        kol = SRC2KOL.get(src, src.replace("tw_", ""))
        for tk in parse_json_arr(ticker_json):
            key = (kol, tk)
            if key not in by_kol_tk:
                by_kol_tk[key] = {
                    "ticker": tk, "kol": kol, "source_id": src,
                    "direction": direction, "bottleneck": bk,
                    "latest_pub": pub, "earliest_pub": pub,
                    "n_calls": 1,
                }
            else:
                rec = by_kol_tk[key]
                rec["n_calls"] += 1
                if pub < rec["earliest_pub"]:
                    rec["earliest_pub"] = pub

    today = datetime.now(timezone.utc).date()

    # 筛 + 算
    rows_out = []
    skipped_recent = 0
    for key, rec in by_kol_tk.items():
        pub_date = rec["latest_pub"][:10]
        try:
            days_since = (today - datetime.fromisoformat(pub_date).date()).days
        except Exception:
            days_since = 0
        if days_since < DASHBOARD_MIN_DAYS:
            skipped_recent += 1
            continue
        in_field = is_in_field(rec["kol"], rec["ticker"], rec["bottleneck"])
        rec["call_date"] = pub_date
        rec["days_since"] = days_since
        rec["in_field"] = in_field
        # has_price 这里不计算 (不查 DB cache), priority 用 in_field 近似
        rec["priority"] = 0 if in_field else 2
        rows_out.append(rec)

    rows_out.sort(key=lambda r: (r["priority"], -r["days_since"]))
    out = rows_out[:limit]

    print(f"  select_dashboard_ticker_targets: 总 (kol, ticker) {len(by_kol_tk)} | "
          f"跳过太近 (< {DASHBOARD_MIN_DAYS}d) {skipped_recent} | "
          f"展示 {len(out)} 条", flush=True)
    return out


def group_targets_by_ticker(targets: list[dict]) -> dict[str, list[dict]]:
    """把 select 输出按 ticker 聚合, 用于 refresh 按 ticker 去重 fetch.

    返回: {ticker: [target1, target2, ...]}
    - 一个 ticker 可能有多个 (kol, ticker) 行 (如 Jukan 的 MU 跟 Serenity 的 MU)
    - 同一 ticker 的多个行共享 now_price (从同一次 range API 拿)
    - 多个行的 call_price 各自计算 (各自的 latest_pub)
    """
    by_tk: dict[str, list[dict]] = {}
    for t in targets:
        by_tk.setdefault(t["ticker"], []).append(t)
    return by_tk