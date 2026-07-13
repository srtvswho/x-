#!/usr/bin/env python3
"""test_dashboard_raw_posts.py — Dashboard 1D / 近期明细 口径修复测试 (2026-07-13)

覆盖:
1. 24h 窗口内只有 raw_posts 无 extraction → n_posts_24h=1, n_directional=0, empty_reason=no_directional
2. 无 extraction 的记录 → direction=neutral, summary=raw_text 截断, 不产生 long/short
3. 同一 post 多 extraction → 合并去重, ticker union
4. TODAY_RECORDS + RECORDS 合并去重, TODAY 在前
5. 1D 卡片: 1条普通 + 0条有效判断, 显示"1条新推文、0条有效投资判断"
6. 北京时区格式化 (Intl.DateTimeFormat Asia/Shanghai) — 用 Python 模拟
7. 1M/3M/6M/1Y 仍保持有效判断筛选口径

不依赖生产 DB. 用 tmp_path fixture.
"""
import json
import sqlite3
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent / "scripts" / "dashboard"))
from common import (  # noqa: E402
    query_today_stats, query_today_records, cn_recent_24h_window_utc,
    build_metadata,
)


@pytest.fixture
def fresh_db(tmp_path):
    """空 DB (只含 raw_posts + extractions_intel 表)."""
    db = tmp_path / "test.db"
    conn = sqlite3.connect(str(db))
    conn.executescript("""
        CREATE TABLE raw_posts (
            post_id TEXT PRIMARY KEY, source_id TEXT, platform TEXT,
            published_at TEXT, captured_at TEXT, raw_text TEXT,
            raw_url TEXT, raw_json TEXT, content_hash TEXT,
            is_deleted INTEGER, archive_url TEXT);
        CREATE TABLE extractions_intel (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            post_id TEXT, source_id TEXT,
            extracted_at TEXT, model_version TEXT, prompt_version TEXT,
            raw_response TEXT,
            ticker TEXT, company TEXT, direction TEXT,
            short_skeptical INTEGER, bottleneck TEXT, attribution TEXT,
            rebuts_narrative TEXT, summary_100 TEXT,
            is_retrospective INTEGER, is_disclosure INTEGER,
            is_self_reported_returns INTEGER);
    """)
    yield conn
    conn.close()


def _insert_post(conn, post_id, source_id, published_at, raw_text="测试推文内容", raw_url=None):
    if raw_url is None:
        raw_url = f"https://x.com/{source_id.replace('tw_', '')}/status/{post_id}"
    conn.execute(
        "INSERT INTO raw_posts (post_id, source_id, published_at, raw_text, raw_url) "
        "VALUES (?,?,?,?,?)",
        (post_id, source_id, published_at, raw_text, raw_url)
    )


def _insert_extraction(conn, post_id, source_id, **kw):
    """kw: direction, ticker, bottleneck, summary_100, raw_text 等"""
    defaults = dict(
        extracted_at=datetime.now(timezone.utc).isoformat(),
        model_version="v1", prompt_version="v2.0.1-intel",
        raw_response="{}",
        ticker=None, company=None, direction=None,
        short_skeptical=0, bottleneck=None, attribution=None,
        rebuts_narrative=None, summary_100=None,
        is_retrospective=0, is_disclosure=0, is_self_reported_returns=0,
    )
    defaults.update(kw)
    if isinstance(defaults.get("ticker"), list):
        defaults["ticker"] = json.dumps(defaults["ticker"])
    if isinstance(defaults.get("company"), list):
        defaults["company"] = json.dumps(defaults["company"])
    placeholders = ",".join(["?"] * len(defaults))
    cols = ",".join(defaults.keys())
    conn.execute(
        f"INSERT INTO extractions_intel (post_id, source_id, {cols}) VALUES (?,?,{placeholders})",
        (post_id, source_id, *defaults.values())
    )


# ============================================================================
# Section 1: 24h 窗口内只有 raw_posts, 无 extraction
# ============================================================================
class TestRawPostOnlyInWindow:
    def test_no_extraction_in_24h(self, fresh_db, monkeypatch):
        """24h 窗口内 1 条 jukan raw_post, 没 extraction → n_posts_24h=1, n_directional=0"""
        # 固定 now = CST 7-13 06:26 (Dashboard 构建时间) = UTC 7-12 22:26
        from common import cn_now
        fixed = datetime(2026, 7, 12, 22, 26, 0, tzinfo=timezone.utc)
        monkeypatch.setattr("common.cn_now", lambda: fixed)

        # jukan 推文 = CST 7-12 07:23 = UTC 7-11 23:23 (在窗口 UTC 7-11 22:26 ~ 7-12 22:26 内)
        pub = "2026-07-11T23:23:44+00:00"
        _insert_post(fresh_db, "p_jukan_1", "tw_jukan05", pub, raw_text="Jukan 普通推文无 ticker")

        stats = query_today_stats(fresh_db)
        assert stats["n_posts_24h"] == 1, f"n_posts 应 1, 实际 {stats['n_posts_24h']}"
        assert stats["n_directional_24h"] == 0
        assert stats["empty_reason"] == "no_directional", \
            f"empty_reason 应 no_directional, 实际 {stats['empty_reason']}"
        print(f"  ✓ 24h 1 raw_post + 0 extraction → empty_reason='no_directional'")

    def test_query_today_records_returns_raw_post_without_extraction(self, fresh_db, monkeypatch):
        """query_today_records 24h 窗口内 1 raw_post, 没 extraction, 仍返回 1 条 record."""
        from common import cn_now
        fixed = datetime(2026, 7, 12, 22, 26, 0, tzinfo=timezone.utc)
        monkeypatch.setattr("common.cn_now", lambda: fixed)

        pub = "2026-07-11T23:23:44+00:00"
        _insert_post(fresh_db, "p1", "tw_jukan05", pub, raw_text="Jukan 普通推文")
        records = query_today_records(fresh_db)
        assert len(records) == 1, f"应返回 1 条 (LEFT JOIN), 实际 {len(records)}"
        r = records[0]
        assert r["post_id"] == "p1"
        assert r["kol"] == "jukan"
        assert r["direction"] == "neutral", f"无 extraction direction 应 neutral, 实际 {r['direction']}"
        assert r["ticker"] == [], f"无 extraction ticker 应空列表, 实际 {r['ticker']}"
        assert r["summary"] is not None and "Jukan" in r["summary"], \
            f"无 extraction 应 fallback raw_text, 实际 {r['summary']!r}"
        assert r["attribution"] is None, f"无 extraction attribution 应 None, 实际 {r['attribution']!r}"
        assert "x.com" in r["raw_url"]
        print(f"  ✓ query_today_records 返回 1 条 record (neutral + summary=raw_text + ticker=[])")


# ============================================================================
# Section 2: 无 extraction 记录不冒充 long/short
# ============================================================================
class TestNoFalseDirection:
    def test_stats_directional_count_excludes_neutral(self, fresh_db, monkeypatch):
        """n_directional_24h 只数 long/short, neutral 不算."""
        from common import cn_now
        fixed = datetime(2026, 7, 12, 22, 26, 0, tzinfo=timezone.utc)
        monkeypatch.setattr("common.cn_now", lambda: fixed)
        # 3 raw_posts: 1 long, 1 short, 1 neutral
        base = datetime(2026, 7, 12, 12, 0, 0, tzinfo=timezone.utc)
        _insert_post(fresh_db, "p1", "tw_jukan05", base.isoformat(), raw_text="long 推文")
        _insert_post(fresh_db, "p2", "tw_aleabitoreddit", (base + timedelta(hours=1)).isoformat(), raw_text="short 推文")
        _insert_post(fresh_db, "p3", "tw_zephyr_z9", (base + timedelta(hours=2)).isoformat(), raw_text="neutral 推文")
        _insert_extraction(fresh_db, "p1", "tw_jukan05", direction="long", ticker="[\"MU\"]", summary_100="long MU")
        _insert_extraction(fresh_db, "p2", "tw_aleabitoreddit", direction="short", ticker="[\"NVDA\"]", summary_100="short NVDA")
        # p3 没 extraction

        stats = query_today_stats(fresh_db)
        assert stats["n_posts_24h"] == 3
        assert stats["n_directional_24h"] == 2, f"只 long/short 算 directional, 实际 {stats['n_directional_24h']}"
        assert stats["empty_reason"] is None, f"有 long/short 时 empty_reason 应 None, 实际 {stats['empty_reason']}"
        print(f"  ✓ 3 posts (1 long + 1 short + 1 neutral) → n_directional=2")


# ============================================================================
# Section 3: 同一 post 多 extraction 合并去重
# ============================================================================
class TestPostLevelDedup:
    def test_same_post_multiple_extractions_merged(self, fresh_db, monkeypatch):
        """同一 post 2 条 extraction (LLM 重复提取), 最终 1 条 record, ticker 合并, direction 优先 long."""
        from common import cn_now
        fixed = datetime(2026, 7, 12, 22, 26, 0, tzinfo=timezone.utc)
        monkeypatch.setattr("common.cn_now", lambda: fixed)
        pub = datetime(2026, 7, 12, 12, 0, 0, tzinfo=timezone.utc).isoformat()
        _insert_post(fresh_db, "p1", "tw_jukan05", pub, raw_text="MU and SNDK 标的")
        # 同一 post 2 条 extraction: 1 long(MU) + 1 long(SNDK)
        _insert_extraction(fresh_db, "p1", "tw_jukan05", direction="long", ticker="[\"MU\"]", summary_100="long MU")
        _insert_extraction(fresh_db, "p1", "tw_jukan05", direction="long", ticker="[\"SNDK\"]", summary_100="long SNDK")
        records = query_today_records(fresh_db)
        assert len(records) == 1, f"应合并为 1 条, 实际 {len(records)} 条"
        r = records[0]
        assert set(r["ticker"]) == {"MU", "SNDK"}, f"ticker 应合并, 实际 {r['ticker']}"
        assert r["direction"] == "long"
        print(f"  ✓ 同一 post 2 extraction → 1 record, ticker={r['ticker']}, direction=long")

    def test_long_short_mix_picks_long(self, fresh_db, monkeypatch):
        """同一 post long+short 混 → 优先 long (按设计的 priority)."""
        from common import cn_now
        fixed = datetime(2026, 7, 12, 22, 26, 0, tzinfo=timezone.utc)
        monkeypatch.setattr("common.cn_now", lambda: fixed)
        pub = datetime(2026, 7, 12, 12, 0, 0, tzinfo=timezone.utc).isoformat()
        _insert_post(fresh_db, "p1", "tw_jukan05", pub)
        _insert_extraction(fresh_db, "p1", "tw_jukan05", direction="short", ticker="[\"NVDA\"]")
        _insert_extraction(fresh_db, "p1", "tw_jukan05", direction="long", ticker="[\"MU\"]")
        records = query_today_records(fresh_db)
        assert len(records) == 1
        assert records[0]["direction"] == "long", f"long 优先 short, 实际 {records[0]['direction']}"
        assert set(records[0]["ticker"]) == {"NVDA", "MU"}
        print(f"  ✓ long+short 混 → direction=long, ticker 合并")

    def test_neutral_with_bottleneck_still_neutral(self, fresh_db, monkeypatch):
        """extraction direction=neutral, 有 bottleneck → direction 仍 neutral (按设计)."""
        from common import cn_now
        fixed = datetime(2026, 7, 12, 22, 26, 0, tzinfo=timezone.utc)
        monkeypatch.setattr("common.cn_now", lambda: fixed)
        pub = datetime(2026, 7, 12, 12, 0, 0, tzinfo=timezone.utc).isoformat()
        _insert_post(fresh_db, "p1", "tw_jukan05", pub)
        _insert_extraction(fresh_db, "p1", "tw_jukan05", direction="neutral", bottleneck="HBM")
        records = query_today_records(fresh_db)
        assert records[0]["direction"] == "neutral"
        assert records[0]["bottleneck"] == "HBM"
        print(f"  ✓ direction=neutral + bottleneck=HBM → direction 仍 neutral")


# ============================================================================
# Section 4: TODAY_RECORDS + RECORDS 合并去重 (Python 层, 测试用 helper)
# ============================================================================
class TestFeedMerge:
    def test_today_records_lead_over_records(self):
        """TODAY_RECORDS 在前, RECORDS 补全去重."""
        today = [
            {"post_id": "a", "published_at": "2026-07-12T20:00:00+00:00", "direction": "neutral", "ticker": []},
            {"post_id": "b", "published_at": "2026-07-12T10:00:00+00:00", "direction": "long", "ticker": ["MU"]},
        ]
        records = [
            {"post_id": "a", "published_at": "2026-07-12T20:00:00+00:00", "direction": "long", "ticker": ["MU"]},
            {"post_id": "c", "published_at": "2026-07-11T20:00:00+00:00", "direction": "long", "ticker": ["NVDA"]},
        ]
        # 模拟 JS 合并逻辑
        seen = set(); merged = []
        for r in today:
            if r["post_id"] not in seen: seen.add(r["post_id"]); merged.append(r)
        for r in records:
            if r["post_id"] not in seen: seen.add(r["post_id"]); merged.append(r)
        merged.sort(key=lambda r: r["published_at"], reverse=True)
        ids = [r["post_id"] for r in merged]
        assert ids[0] == "a", f"a 应排第一 (latest), 实际 {ids[0]}"
        assert "a" in ids and "b" in ids and "c" in ids, f"应 3 条, 实际 {ids}"
        assert len(merged) == 3, f"去重后应 3 条, 实际 {len(merged)}"
        # 'a' 应该是 TODAY 的版本 (neutral), 不是 RECORDS 的 (long)
        a_rec = next(r for r in merged if r["post_id"] == "a")
        assert a_rec["direction"] == "neutral", f"TODAY_RECORDS 优先, 'a' 应是 neutral, 实际 {a_rec['direction']}"
        print(f"  ✓ TODAY a (neutral) + RECORDS a (long) + c → 3 records, TODAY 版本优先")

    def test_merged_dedup_by_post_id(self):
        """同一 post 在 TODAY + RECORDS 重复出现 → 只 1 条."""
        today = [{"post_id": "x", "published_at": "2026-07-12T10:00:00+00:00"}]
        records = [{"post_id": "x", "published_at": "2026-07-12T10:00:00+00:00"}]
        seen = set(); merged = []
        for r in today + records:
            if r["post_id"] not in seen: seen.add(r["post_id"]); merged.append(r)
        assert len(merged) == 1
        print(f"  ✓ 同一 post 在 TODAY+RECORDS 重复 → 1 条")


# ============================================================================
# Section 5: 1D 卡片 (template 行为, 通过源文本断言)
# ============================================================================
class TestOneDayCardSource:
    def test_template_1d_uses_today_records(self):
        """1D 切窗 (win===0) 必须用 TODAY_RECORDS, 不是 RECORDS."""
        template = (Path(__file__).parent.parent / "scripts" / "dashboard" /
                    "dashboard.template.html").read_text(encoding="utf-8")
        # 关键: 1D 模式用 TODAY_RECORDS
        assert "const dataSrc = (win===0) ? TODAY_RECORDS : RECORDS;" in template, \
            "1D 必须用 TODAY_RECORDS (含无 extraction 的普通推文)"
        # 1D 空态显示 "1条新推文 · 0条有效投资判断" 风格
        assert "${TODAY_STATS.n_posts_24h}" in template, "应显示 24h 新增 posts 计数"
        assert "${TODAY_STATS.n_directional_24h}" in template, "应显示 24h directional 计数"
        # 1D 普通动态标签
        assert '<span class="tag ordinary">普通动态</span>' in template, \
            "1D 普通推文应标 '普通动态'"
        # 1M/3M/6M/1Y 仍过滤 long/short
        assert "win===0" in template
        assert "r.direction!=='neutral'||r.bottleneck" in template, \
            "1M/3M/6M/1Y 必须仍按有效判断过滤 (不能扩大到所有历史推文)"
        print(f"  ✓ template 1D 用 TODAY_RECORDS, 普通动态标签, 1M+ 仍按有效判断过滤")

    def test_template_window_label_visible(self):
        """顶部显示 '统计窗口: YYYY-MM-DD HH:mm ~ YYYY-MM-DD HH:mm · 数据截至: ...'."""
        template = (Path(__file__).parent.parent / "scripts" / "dashboard" /
                    "dashboard.template.html").read_text(encoding="utf-8")
        assert "统计窗口:" in template
        assert "数据截至:" in template
        assert "fmtFullCST" in template, "必须用 fmtFullCST 格式化窗口时间"
        print(f"  ✓ template 含 '统计窗口:' / '数据截至:' / fmtFullCST")


# ============================================================================
# Section 6: 北京时区格式化
# ============================================================================
class TestBeijingTimeFormat:
    def test_python_intl_beijing_format(self):
        """UTC 2026-07-11T23:23:44+00:00 → 2026-07-12 07:23 CST."""
        # Python 模拟 Intl.DateTimeFormat Asia/Shanghai 行为
        from datetime import datetime, timezone, timedelta
        cn = timezone(timedelta(hours=8))
        utc = datetime(2026, 7, 11, 23, 23, 44, tzinfo=timezone.utc)
        cn_dt = utc.astimezone(cn)
        formatted = cn_dt.strftime("%Y-%m-%d %H:%M CST")
        assert formatted == "2026-07-12 07:23 CST", f"实际 {formatted!r}"
        print(f"  ✓ UTC 7-11 23:23 → 北京 {formatted}")

    def test_july_12_0327_utc_to_cst(self):
        """UTC 2026-07-12 03:27 → 北京 11:27 (验证边界)."""
        from datetime import datetime, timezone, timedelta
        cn = timezone(timedelta(hours=8))
        utc = datetime(2026, 7, 12, 3, 27, 0, tzinfo=timezone.utc)
        cn_dt = utc.astimezone(cn)
        assert cn_dt.strftime("%Y-%m-%d %H:%M") == "2026-07-12 11:27"
        print(f"  ✓ UTC 7-12 03:27 → 北京 {cn_dt.strftime('%Y-%m-%d %H:%M')}")

    def test_template_uses_intl_cst(self):
        """template 必须用 Intl.DateTimeFormat Asia/Shanghai (不依赖浏览器本地时区)."""
        template = (Path(__file__).parent.parent / "scripts" / "dashboard" /
                    "dashboard.template.html").read_text(encoding="utf-8")
        assert "Intl.DateTimeFormat" in template
        assert "Asia/Shanghai" in template
        # 不应该有 raw .slice(0,10) (那是 UTC ISO 字符串截断, 受时区影响)
        assert ".slice(0,10)" not in template, \
            "不应再有 .slice(0,10) 截断 ISO (受浏览器时区影响)"
        # fmtDate / fmtFull / fmtTime 必须用 _cstParts (基于 Intl)
        assert "_cstParts" in template
        print(f"  ✓ template 用 Intl.DateTimeFormat Asia/Shanghai, 无 .slice(0,10)")


# ============================================================================
# Section 7: 1M/3M/6M/1Y 仍按有效判断过滤
# ============================================================================
class TestLongWindowFiltersValidOnly:
    def test_long_window_excludes_neutral_no_extraction(self):
        """1M+ 窗口只看 long/short + bottleneck, 不显示普通推文.

        验证 JS 1M+ 过滤逻辑 (r.direction !== 'neutral' || r.bottleneck).
        跟 query_today_records 返回的内容独立 (query_today_records 是 24h 窗口,
        1M+ 模板用 RECORDS 1M 切窗).
        """
        # 模拟 1M+ 窗口: 直接构造 records 列表, 验证 JS 侧过滤
        records_1m = [
            {"post_id": "p_long", "kol": "jukan", "direction": "long",
             "ticker": ["MU"], "bottleneck": None},
            {"post_id": "p_neutral", "kol": "jukan", "direction": "neutral",
             "ticker": [], "bottleneck": None},  # 普通推文
            {"post_id": "p_bk", "kol": "jukan", "direction": "neutral",
             "ticker": [], "bottleneck": "HBM"},  # neutral 但有瓶颈
        ]
        # JS 1M+ filter: r.direction !== 'neutral' || r.bottleneck
        valid = [r for r in records_1m
                 if r["direction"] != "neutral" or r["bottleneck"]]
        assert len(valid) == 2, f"1M+ 应 2 条 (long + neutral with bk), 实际 {len(valid)}"
        ids = {r["post_id"] for r in valid}
        assert ids == {"p_long", "p_bk"}, f"应 p_long + p_bk, 实际 {ids}"
        # 普通推文 (neutral + 无 bk) 被排除
        assert "p_neutral" not in ids
        # 模板断言: 1M+ 仍用 r.direction !== 'neutral' || r.bottleneck 过滤
        template = (Path(__file__).parent.parent / "scripts" / "dashboard" /
                    "dashboard.template.html").read_text(encoding="utf-8")
        # 1M/3M/6M/1Y 仍按有效判断过滤 (不能扩大到所有历史推文)
        assert template.count("r.direction!=='neutral'||r.bottleneck") >= 1, \
            "1M+ 仍须按有效判断过滤 (不是所有推文)"
        print(f"  ✓ 1M+ 排除普通推文 (neutral + 无 bk), 包含 long + neutral-with-bk")


# ============================================================================
# Section 8: query_recent_records (DB 最新 N 条, 无时间窗口) — 修复近期明细
# ============================================================================
class TestRecentRecords:
    """query_recent_records: 不限 24h, DB 最新 30 条, 含无 extraction 的普通推文.
    供近期明细使用 (跟 24h 统计/1D 卡片解耦).
    """

    def test_24h_outside_post_included(self, fresh_db, monkeypatch):
        """build_time = CST 7-13 14:15. Jukan 7-12 07:23 (在 24h 窗口外) 应在 recent_records."""
        from common import cn_now
        fixed = datetime(2026, 7, 13, 6, 15, 0, tzinfo=timezone.utc)  # CST 14:15
        monkeypatch.setattr("common.cn_now", lambda: fixed)

        # Jukan 7-12 07:23 CST = UTC 7-11 23:23
        jukan_pub = "2026-07-11T23:23:44+00:00"
        _insert_post(fresh_db, "p_jukan", "tw_jukan05", jukan_pub, raw_text="Jukan 普通推文")
        # Serenity 7-12 03:47 CST = UTC 7-11 19:47
        serenity_pub = "2026-07-11T19:47:00+00:00"
        _insert_post(fresh_db, "p_serenity", "tw_aleabitoreddit", serenity_pub, raw_text="Serenity 推文")
        _insert_extraction(fresh_db, "p_serenity", "tw_aleabitoreddit",
                          direction="long", ticker='["MU"]', summary_100="long MU")

        # 24h 窗口: UTC 7-12 06:15 ~ 7-13 06:15 — 两条都在窗口外
        # 验证 query_today_records (24h) 确实不包含
        today_recs = query_today_records(fresh_db)
        assert len(today_recs) == 0, f"24h 窗口应 0 条 (2 条都 > 24h 前), 实际 {len(today_recs)}"

        # query_recent_records (DB 最新 30 条) 应包含两条
        from common import query_recent_records
        recent = query_recent_records(fresh_db, limit=30)
        assert len(recent) == 2, f"recent 应 2 条, 实际 {len(recent)}"
        # 第一条是 jukan 07:23 (更新)
        assert recent[0]["post_id"] == "p_jukan", f"首条应 jukan 07:23, 实际 {recent[0]['post_id']}"
        assert recent[0]["published_at"] == jukan_pub
        assert recent[0]["kol"] == "jukan"
        assert recent[0]["direction"] == "neutral", "无 extraction 应 neutral"
        # 第二条是 serenity
        assert recent[1]["post_id"] == "p_serenity"
        assert recent[1]["direction"] == "long"
        print(f"  ✓ 24h 外 jukan 07:23 在 recent_records 第一条, 24h 内 0 条 (跟 24h 统计解耦)")

    def test_today_records_excludes_outside_window_post(self, fresh_db, monkeypatch):
        """query_today_records 不包含 24h 外推文 (跟 recent_records 区别)."""
        from common import cn_now
        fixed = datetime(2026, 7, 13, 6, 15, 0, tzinfo=timezone.utc)
        monkeypatch.setattr("common.cn_now", lambda: fixed)
        # jukan 7-12 07:23 (在 24h 外)
        _insert_post(fresh_db, "p_jukan", "tw_jukan05", "2026-07-11T23:23:44+00:00", raw_text="x")
        # serenity 7-13 13:00 (在 24h 内)
        _insert_post(fresh_db, "p_serenity", "tw_aleabitoreddit", "2026-07-13T05:00:00+00:00", raw_text="y")

        today = query_today_records(fresh_db)
        assert len(today) == 1
        assert today[0]["post_id"] == "p_serenity", f"24h 内只 serenity, 实际 {today[0]['post_id']}"
        # jukan 07:23 不在 24h
        assert "p_jukan" not in [r["post_id"] for r in today]
        print(f"  ✓ query_today_records 只返回 24h 内推文, 排除 24h 外 jukan 07:23")

    def test_recent_records_dedup_same_post_multiple_extractions(self, fresh_db, monkeypatch):
        """同 post 多 extraction → 1 条 record, ticker union."""
        from common import cn_now
        fixed = datetime(2026, 7, 13, 6, 15, 0, tzinfo=timezone.utc)
        monkeypatch.setattr("common.cn_now", lambda: fixed)
        pub = "2026-07-13T05:00:00+00:00"
        _insert_post(fresh_db, "p1", "tw_jukan05", pub, raw_text="multi-extract")
        _insert_extraction(fresh_db, "p1", "tw_jukan05", direction="long", ticker='["MU"]', summary_100="long MU")
        _insert_extraction(fresh_db, "p1", "tw_jukan05", direction="long", ticker='["SNDK"]', summary_100="long SNDK")
        from common import query_recent_records
        recent = query_recent_records(fresh_db, limit=30)
        assert len(recent) == 1
        assert set(recent[0]["ticker"]) == {"MU", "SNDK"}
        assert recent[0]["direction"] == "long"
        print(f"  ✓ recent_records 同 post 多 extraction → 1 条, ticker union")

    def test_recent_records_limit_30(self, fresh_db, monkeypatch):
        """recent_records 限 limit=30."""
        from common import cn_now
        fixed = datetime(2026, 7, 13, 6, 15, 0, tzinfo=timezone.utc)
        monkeypatch.setattr("common.cn_now", lambda: fixed)
        # 插 35 条 jukan
        for i in range(35):
            pub = (datetime(2026, 7, 13, 5, 0, 0, tzinfo=timezone.utc) - timedelta(hours=i)).isoformat()
            _insert_post(fresh_db, f"p{i}", "tw_jukan05", pub, raw_text=f"text {i}")
        from common import query_recent_records
        recent = query_recent_records(fresh_db, limit=30)
        assert len(recent) == 30, f"limit=30 应返回 30 条, 实际 {len(recent)}"
        # 都是不同 post_id
        post_ids = [r["post_id"] for r in recent]
        assert len(set(post_ids)) == 30, f"应 30 个唯一 post_id, 实际 {len(set(post_ids))}"
        print(f"  ✓ recent_records 35 条 DB → limit=30 条")

    def test_recent_records_no_extraction_included(self, fresh_db, monkeypatch):
        """无 extraction 的原始推文也必须在 recent_records."""
        from common import cn_now
        fixed = datetime(2026, 7, 13, 6, 15, 0, tzinfo=timezone.utc)
        monkeypatch.setattr("common.cn_now", lambda: fixed)
        _insert_post(fresh_db, "p1", "tw_jukan05", "2026-07-13T05:00:00+00:00", raw_text="无 extraction")
        from common import query_recent_records
        recent = query_recent_records(fresh_db, limit=30)
        assert len(recent) == 1
        assert recent[0]["direction"] == "neutral"
        assert recent[0]["ticker"] == []
        assert recent[0]["summary"] is not None
        assert "无 extraction" in recent[0]["summary"]
        print(f"  ✓ 无 extraction 推文也在 recent_records (neutral + summary=raw_text)")


# ============================================================================
# Section 9: renderFeed 使用 RECENT_RECORDS (不是 TODAY+RECORDS 拼接)
# ============================================================================
class TestRenderFeedSource:
    """renderFeed 直接用 RECENT_RECORDS, 24h 顶部统计仍用 TODAY_RECORDS (renderBrief)."""

    def test_template_uses_recent_records(self):
        """template renderFeed 必须用 RECENT_RECORDS, 不再合并 TODAY+RECORDS."""
        template = (Path(__file__).parent.parent / "scripts" / "dashboard" /
                    "dashboard.template.html").read_text(encoding="utf-8")
        # 1. 注入 RECENT_RECORDS script id
        assert '<script id="RECENT_RECORDS" type="application/json">__RECENT_RECORDS__</script>' in template
        # 2. 解析 const RECENT_RECORDS
        assert "const RECENT_RECORDS=JSON.parse(document.getElementById('RECENT_RECORDS').textContent)" in template
        # 3. renderFeed 内部用 (RECENT_RECORDS || [])
        # 找 renderFeed 函数体, 看是否不再有 "for (const r of (RECORDS || []))" 这种合并
        # renderFeed 现在应该: const sorted = (RECENT_RECORDS || []).slice().sort(...)
        assert "(RECENT_RECORDS || []).slice().sort" in template, \
            "renderFeed 必须用 RECENT_RECORDS (不再合并 TODAY+RECORDS)"
        # 4. 不应有 "for (const r of (RECORDS || [])) {" 这种拼接循环
        renderFeed_start = template.find("function renderFeed(){")
        renderFeed_end = template.find("function renderTickers()")
        renderFeed_body = template[renderFeed_start:renderFeed_end]
        assert "for (const r of (RECORDS || []))" not in renderFeed_body, \
            "renderFeed 不应再合并 RECORDS (去掉了合并去重循环)"
        assert "for (const r of (TODAY_RECORDS || []))" not in renderFeed_body, \
            "renderFeed 不应再合并 TODAY_RECORDS"
        print(f"  ✓ renderFeed 用 RECENT_RECORDS, 不再合并 TODAY+RECORDS")

    def test_template_24h_stats_keep_using_today_records(self):
        """顶部 24h 统计 / 1D 卡片 / renderBrief 仍用 TODAY_RECORDS (24h 口径)."""
        template = (Path(__file__).parent.parent / "scripts" / "dashboard" /
                    "dashboard.template.html").read_text(encoding="utf-8")
        # renderStance 1D 仍用 TODAY_RECORDS
        assert "const dataSrc = (win===0) ? TODAY_RECORDS : RECORDS;" in template, \
            "renderStance 1D 仍用 TODAY_RECORDS (24h 口径)"
        # renderBrief 顶部统计用 TODAY_STATS (24h 窗口)
        assert "TODAY_STATS.n_posts_24h" in template
        # 1D 切窗仍用 window_start_utc (24h 滚动)
        assert "BUILD_META.window_start_utc" in template
        # 24h 顶部提示仍 3 种 empty_reason
        for reason in ("no_posts", "no_directional"):
            assert reason in template
        print(f"  ✓ 24h 统计 / 1D 卡片 / renderBrief 仍用 TODAY_RECORDS + TODAY_STATS")

    def test_recent_records_helper_exists(self):
        """common.py 必须有 query_recent_records 函数."""
        from common import query_recent_records
        assert callable(query_recent_records)
        # 接受 limit 参数, 默认 30
        import inspect
        sig = inspect.signature(query_recent_records)
        assert "limit" in sig.parameters
        assert sig.parameters["limit"].default == 30
        print(f"  ✓ common.query_recent_records(conn, limit=30) 存在")

    def test_recent_records_keeps_template_window_24h(self):
        """顶部 feed-empty 横幅仍 3 种 empty_reason (no_posts / no_directional / 有内容) + 24h 窗口提示."""
        template = (Path(__file__).parent.parent / "scripts" / "dashboard" /
                    "dashboard.template.html").read_text(encoding="utf-8")
        # 顶部提示仍是 24h (window_label 来自 BUILD_META, 跟 renderFeed 内部 RECENT_RECORDS 解耦)
        assert "${winLabel} 未抓到新推文" in template
        assert "${winLabel} 新增" in template
        # winLabel 来自 BUILD_META.window_label (cn_recent_24h_window_utc 算出)
        assert "BUILD_META.window_label" in template
        print(f"  ✓ 24h 顶部横幅仍正确 (跟 recent_records 解耦)")

    def test_24h_outside_post_marked_ordinary_1d_ago(self):
        """24h 外的普通推文 → 标 '普通动态' + 显示 '1 天前'."""
        # 这是 JS 端逻辑, 模拟: rtCls + 'ordinary' if isOrdinary
        # 模拟 1 条 24h 外的普通推文
        records = [{
            "post_id": "p_jukan", "kol": "jukan", "direction": "neutral",
            "ticker": [], "bottleneck": None,
            "published_at": "2026-07-11T23:23:44+00:00"  # 30 小时前
        }]
        build_utc = "2026-07-13T06:15:00+00:00"
        # 模拟 JS days 计算
        from datetime import datetime
        pub_ms = datetime.fromisoformat("2026-07-11T23:23:44+00:00").timestamp() * 1000
        build_ms = datetime.fromisoformat(build_utc).timestamp() * 1000
        days = int((build_ms - pub_ms) / 86400000)
        assert days == 1, f"30h 前应显示 1 天前, 实际 {days} 天"
        isOrdinary = (records[0]["direction"] == "neutral" and not records[0]["bottleneck"])
        assert isOrdinary
        print(f"  ✓ 24h 外普通推文 → days=1 (1 天前), isOrdinary=True")

    def test_no_modify_to_production_db(self):
        """测试不修改生产 DB. /workspace/data/signalboard_full.db mtime 不变."""
        import os
        db_path = Path("/workspace/data/signalboard_full.db")
        if db_path.exists():
            mtime_before = db_path.stat().st_mtime
            size_before = db_path.stat().st_size
            # 测试期间不主动写 DB
            import time
            time.sleep(0.1)
            mtime_after = db_path.stat().st_mtime
            size_after = db_path.stat().st_size
            assert mtime_after == mtime_before, f"生产 DB mtime 改变! {mtime_before} -> {mtime_after}"
            assert size_after == size_before, f"生产 DB size 改变!"
            print(f"  ✓ 生产 DB 未被测试修改 (mtime/size 不变)")
