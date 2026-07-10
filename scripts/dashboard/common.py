#!/usr/bin/env python3
"""scripts/dashboard/common.py — Dashboard 共享工具

设计: 全部时间窗口基于 Asia/Shanghai 北京自然日, 不是 UTC 滑动 24h.
- 北京自然日 = [今日 00:00 CST, 明日 00:00 CST)
- 窗口函数返回 (start_utc_iso, end_utc_iso), 都用 UTC ISO 字符串
- build_metadata() 返回 build 真实时间 + 今日窗口 + 数据截止 (供 template 显示)

为什么必须统一:
- intel_gen_summaries.py today/0M 跟 dashboard 1D 必须用同一窗口, 不然总结跟明细对不上
- 北京 23:00 UTC 是次日 07:00, 不一刀切时会出现 "now 07:00 总结里说昨天, 明细里说今天"
"""
from __future__ import annotations
from datetime import datetime, timedelta, timezone

try:
    from zoneinfo import ZoneInfo
    CN_TZ = ZoneInfo("Asia/Shanghai")
except ImportError:  # pragma: no cover
    CN_TZ = timezone(timedelta(hours=8))  # Python 3.8 兜底


def cn_now() -> datetime:
    """当前 UTC datetime (带 tzinfo)."""
    return datetime.now(timezone.utc)


def cn_today_window_utc(end: datetime | None = None) -> tuple[str, str]:
    """[北京今日 00:00, 北京明日 00:00) 转 UTC ISO 字符串.

    例: 北京 2026-07-10 18:00 → [UTC 2026-07-09 16:00, UTC 2026-07-10 16:00)
    """
    if end is None:
        end = cn_now()
    cn = end.astimezone(CN_TZ)
    cn_start = cn.replace(hour=0, minute=0, second=0, microsecond=0)
    cn_end = cn_start + timedelta(days=1)
    start_utc = cn_start.astimezone(timezone.utc).isoformat()
    end_utc = cn_end.astimezone(timezone.utc).isoformat()
    return start_utc, end_utc


def cn_window_utc(days: int, end: datetime | None = None) -> tuple[str, str]:
    """[end-days 天前 (北京自然日 00:00), end (北京自然日 00:00)) 转 UTC ISO.

    days=1 是"今日"; days=30 是"近 30 个北京自然日".
    注意: end 是开区间 (不包含), SQL 用 [start, end).
    """
    if end is None:
        end = cn_now()
    cn = end.astimezone(CN_TZ)
    cn_end = cn.replace(hour=0, minute=0, second=0, microsecond=0) + timedelta(days=1)
    cn_start = cn_end - timedelta(days=days)
    start_utc = cn_start.astimezone(timezone.utc).isoformat()
    end_utc = cn_end.astimezone(timezone.utc).isoformat()
    return start_utc, end_utc


def cn_window_long_utc(days: int, end: datetime | None = None) -> tuple[str, str]:
    """近 N 天 (相对滑动窗口, 用于 1M/3M/6M/12M 这种"近 N 天"语义).

    区别于 cn_window_utc: 后者按"北京自然日对齐", 前者按"今天往前推 N 天".
    - 1M (近 1 月) = cn_window_long_utc(30): 今天 06:00 → 北京 6 月 11 日 06:00
    - 1D (今日) = cn_today_window_utc(): 北京今日 00:00 → 明日 00:00 (必须是自然日)
    """
    if end is None:
        end = cn_now()
    end_iso = end.isoformat()
    start = end - timedelta(days=days)
    start_iso = start.isoformat()
    return start_iso, end_iso


def cn_format(utc_dt: datetime, fmt: str = "%Y-%m-%d %H:%M CST") -> str:
    """UTC datetime 转 北京时间格式化字符串."""
    cn = utc_dt.astimezone(CN_TZ)
    return cn.strftime(fmt)


def build_metadata(conn=None) -> dict:
    """返回 build 时需要的元数据: 真实生成时间 + 今日窗口 + 数据截止.

    conn: 可选, 用于查 MAX(published_at). 不传则 data_until=None.
    """
    now = cn_now()
    today_start, today_end = cn_today_window_utc(now)
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
        "today_window_start_utc": today_start,
        "today_window_end_utc": today_end,
        "today_date_label": cn_format(now, "%Y-%m-%d"),
        "data_until_utc": data_until,
        "data_until_label": cn_format(datetime.fromisoformat(data_until.replace("Z", "+00:00")), "%Y-%m-%d %H:%M CST") if data_until else None,
        "tz_label": "Asia/Shanghai",
    }


def query_today_stats(conn) -> dict:
    """北京今日窗口内的 posts / 方向性判断 / 卡点统计.

    返回结构 (供 build_dashboard 注入 __TODAY_STATS__):
    {
      "n_posts_today": int,        # raw_posts 数 (北京今日窗口内)
      "n_directional_today": int,   # 有效方向性判断 (long/short) 数
      "n_neutral_today": int,        # neutral 但有 ticker/bottleneck 的
      "n_bottlenecks_today": int,    # 涉及的不同卡点数
      "hot_bottlenecks_today": [{"name": str, "count": int}, ...],
      "by_kol_today": {kol: int, ...},    # 各 KOL 今日 posts 数
      "window_start_utc": str, "window_end_utc": str,
      "empty_reason": str | None,  # "no_posts" | "no_directional" | None
    }

    empty_reason 语义:
    - "no_posts": 今日窗口 raw_posts = 0 (没抓到新推文)
    - "no_directional": 有 posts 但 long/short 判断 = 0 (有推文但没方向性投资判断)
    - None: 有 posts 也有 directional
    """
    start, end = cn_today_window_utc()
    rows = conn.execute("""
        SELECT r.post_id, r.source_id, r.published_at,
               e.direction, e.bottleneck, e.ticker, e.is_retrospective, e.is_disclosure
        FROM raw_posts r
        LEFT JOIN extractions_intel e ON r.post_id = e.post_id
        WHERE r.published_at >= ? AND r.published_at < ?
    """, (start, end)).fetchall()

    # raw_posts 去重 (post_id)
    posts_seen = {}
    for r in rows:
        pid, src, pub, direction, bk, ticker, retro, disc = r
        if pid not in posts_seen:
            posts_seen[pid] = {"src": src, "pub": pub,
                                "direction": direction, "bk": bk, "ticker": ticker,
                                "retro": retro or 0, "disc": disc or 0}

    n_posts_today = len(posts_seen)

    SRC2KOL = {
        "tw_jukan05": "jukan", "tw_aleabitoreddit": "serenity",
        "tw_zephyr_z9": "zephyr", "tw_austinsemis": "austin",
    }

    # 方向性判断 (long/short), 排除 R12 (retrospective / disclosure)
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

    # empty_reason
    if n_posts_today == 0:
        empty_reason = "no_posts"
    elif directional == 0:
        empty_reason = "no_directional"
    else:
        empty_reason = None

    return {
        "n_posts_today": n_posts_today,
        "n_directional_today": directional,
        "n_neutral_with_signal_today": neutral_with_signal,
        "n_bottlenecks_today": len(bk_count),
        "hot_bottlenecks_today": hot_bk_out,
        "by_kol_today": by_kol,
        "window_start_utc": start,
        "window_end_utc": end,
        "empty_reason": empty_reason,
    }


def query_today_records(conn) -> list[dict]:
    """北京今日窗口内的 raw_posts + extractions 完整 records, 供 renderFeed(1D) 用.

    返回跟 build_dashboard.query_extractions 同结构 (post_id, kol, direction, ticker, ...)
    """
    start, end = cn_today_window_utc()
    rows = conn.execute("""
        SELECT e.post_id, e.source_id, e.direction, e.ticker, e.company,
               e.bottleneck, e.attribution, e.rebuts_narrative, e.summary_100,
               e.is_retrospective, e.is_disclosure, e.is_self_reported_returns,
               r.published_at, r.raw_text
        FROM extractions_intel e
        JOIN raw_posts r ON r.post_id = e.post_id
        WHERE r.published_at >= ? AND r.published_at < ?
        ORDER BY r.published_at DESC
    """, (start, end)).fetchall()

    SRC2KOL = {
        "tw_jukan05": "jukan", "tw_aleabitoreddit": "serenity",
        "tw_zephyr_z9": "zephyr", "tw_austinsemis": "austin",
    }

    out = []
    for x in rows:
        (post_id, src, direction, ticker, company, bk, attr, rebuts, summ,
         retro, disc, selfret, pub, raw_text) = x
        handle = src.replace("tw_", "")
        out.append({
            "post_id": post_id, "kol": SRC2KOL.get(src, handle), "source_id": src,
            "published_at": pub, "direction": direction,
            "ticker": ticker, "company": company,
            "bottleneck": bk, "attribution": attr, "rebuts": rebuts, "summary": summ,
            "is_retro": retro or 0, "is_disc": disc or 0, "is_selfret": selfret or 0,
            "raw_text": raw_text,
            "raw_url": f"https://x.com/{handle}/status/{post_id}",
        })
    return out