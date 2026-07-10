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

    返回跟 build_dashboard.query_extractions 同结构 (post_id, kol, direction, ticker, ...)
    """
    start, end = cn_recent_24h_window_utc()
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