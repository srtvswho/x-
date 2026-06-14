"""scraper 的 mock 测试。不调真实 API。

覆盖:
- FieldMap 默认映射能正确提取字段
- to_utc_iso 处理各种时间格式
- ResponseCache put/get 命中
- scrape_state 进度持久化
- coverage 表写入 / 报告生成
- 月份切片 + 跳过已完成
- item → RawPost 转换
- 跑两次 raw_posts 行数不变(幂等)
- 断点续抓
- 单条解析失败不中断
- 字段映射可覆盖
- 截断检测 + 二分细分(单层 / 多层 / max_depth 兜底)
- _call_actor 指数退避
- CLI 走通
"""
from __future__ import annotations

import io
import contextlib
import json
import sys
import tempfile
import time
from datetime import date, datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Callable, Dict, List

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from signalboard import init_db, list_raw_posts_by_source
from signalboard.scraper import (
    DEFAULT_MAX_PER_MONTH,
    ENV_API_TOKEN,
    FieldMap,
    MAX_SUBDIVISION_DEPTH,
    ResponseCache,
    WindowResult,
    _build_coverage_parser,
    _build_scrape_parser,
    _call_actor,
    _cmd_coverage,
    _cmd_scrape,
    _fetch_window,
    _item_to_raw_post,
    _mid_date,
    _next_month,
    _plan_months,
    build_run_input,
    default_field_map,
    fetch_account_history,
    format_coverage_report,
    get_coverage_report,
    get_scrape_state,
    init_scrape_state,
    record_coverage,
    to_utc_iso,
    update_scrape_state,
    set_coverage_note,
)
from signalboard.models import Platform, RawPost

FIXTURE_PATH = Path(__file__).resolve().parent.parent / "fixtures" / "tweet_response_sample.json"


# ---------------------------------------------------------------------------
# fake Apify client
# ---------------------------------------------------------------------------

class FakeApifyClient:
    """按 run_input 选择性地返回不同 items。scripts 形如:
    - {callable(run_input): items} — 用函数决定
    - {"*": items} — 总是返回
    """

    def __init__(self, scripts: Dict = None):
        self.scripts: Dict = scripts or {"*": []}
        self.actor_calls: List[dict] = []

    def actor(self, actor_id: str):
        self._current_actor_id = actor_id
        return self

    def call(self, *, run_input: dict):
        self.actor_calls.append({"actor_id": self._current_actor_id, "run_input": dict(run_input)})
        items = self._match(run_input)
        ds_id = f"ds_{len(self.actor_calls)}"
        self._pending_items = items
        return {"defaultDatasetId": ds_id, "_items": items}

    def _match(self, run_input: dict) -> List[dict]:
        # callable key 可以直接返回 items 列表(返回 None 视为不匹配)
        # 也可以返回 (matched, items) 元组
        for key, val in self.scripts.items():
            if key == "*":
                continue
            if callable(key):
                result = key(run_input)
                if result is None:
                    continue
                if isinstance(result, tuple) and len(result) == 2:
                    matched, items = result
                    if matched:
                        return items
                else:
                    return result
        return self.scripts.get("*", [])

    def dataset(self, dataset_id: str):
        self._current_dataset_id = dataset_id
        return self

    def iterate_items(self):
        return iter(self._pending_items)


# ---------------------------------------------------------------------------
# helpers
# ---------------------------------------------------------------------------

def _load_fixture() -> dict:
    return json.loads(FIXTURE_PATH.read_text(encoding="utf-8"))


def _make_items(n: int, prefix: str = "t", start_idx: int = 0) -> List[dict]:
    """合成 n 条 item,post_id 用 prefix + idx。"""
    return [
        {
            "id": f"{prefix}{i}",
            "text": f"tweet {i}",
            "createdAt": f"2026-05-{(i % 28) + 1:02d}T00:00:00Z",
            "url": f"https://x.com/u/status/{prefix}{i}",
            "author": {"userName": "u"},
        }
        for i in range(start_idx, start_idx + n)
    ]


# ===========================================================================
# 时间转换
# ===========================================================================

def test_to_utc_iso_z_suffix() -> None:
    assert to_utc_iso("2026-05-28T14:30:00Z") == "2026-05-28T14:30:00+00:00"


def test_to_utc_iso_with_offset() -> None:
    out = to_utc_iso("2026-05-28T22:30:00+08:00")
    assert out == "2026-05-28T14:30:00+00:00"


def test_to_utc_iso_naive_assumes_utc() -> None:
    out = to_utc_iso("2026-05-28T14:30:00")
    assert out == "2026-05-28T14:30:00+00:00"


def test_to_utc_iso_unix_seconds() -> None:
    out = to_utc_iso(1779978600)
    assert out.startswith("2026-05-28T14:30:00")


def test_to_utc_iso_unix_milliseconds() -> None:
    out = to_utc_iso(1779978600000)
    assert out.startswith("2026-05-28T14:30:00")


def test_to_utc_iso_empty() -> None:
    assert to_utc_iso("") == ""
    assert to_utc_iso(None) == ""


def test_to_utc_iso_twitter_ctime() -> None:
    """Twitter API 标准 ctime 格式:`Fri Jun 05 00:03:15 +0000 2026`
    这是 apidojo tweet-scraper V2 真实输出(Phase 1 实际跑出确认)。"""
    assert to_utc_iso("Fri Jun 05 00:03:15 +0000 2026") == "2026-06-05T00:03:15+00:00"
    assert to_utc_iso("Tue Jun 09 12:01:06 +0000 2026") == "2026-06-09T12:01:06+00:00"
    assert to_utc_iso("Mon Jun 01 10:15:05 +0000 2026") == "2026-06-01T10:15:05+00:00"


def test_to_utc_iso_twitter_ctime_non_utc() -> None:
    """带 +0800 offset 的 ctime 也该转 UTC。"""
    out = to_utc_iso("Fri Jun 05 08:03:15 +0800 2026")
    assert out == "2026-06-05T00:03:15+00:00"


# ===========================================================================
# FieldMap
# ===========================================================================

def test_default_field_map_extracts_all() -> None:
    """FieldMap.extract 只负责从 item 提取原始字段;时间格式转换在 _item_to_raw_post 调 to_utc_iso 完成。"""
    fixture = _load_fixture()
    item = fixture["items"][0]
    fm = default_field_map()
    out = fm.extract(item)
    assert out["post_id"] == str(item.get("id"))
    assert out["raw_text"]  # 非空
    assert "x.com" in out["raw_url"] or "twitter.com" in out["raw_url"]
    assert out["author_handle"] == "aleabitoreddit"
    # published_at 在 extract 阶段是原值(可能是 ctime 或 ISO 8601),由 _item_to_raw_post 转换
    assert out["published_at"]  # 非空


def test_item_to_raw_post_converts_ctime_published_at() -> None:
    """_item_to_raw_post 必须把 ctime 转 ISO 8601(这是 v2 的关键修复)。"""
    item = {
        "id": "1",
        "text": "t",
        "url": "https://x.com/u/1",
        "createdAt": "Fri Jun 05 00:03:15 +0000 2026",  # Twitter ctime
    }
    post = _item_to_raw_post(item, default_field_map(), "tw_u", "2026-06-12T00:00:00+00:00")
    assert post.published_at == "2026-06-05T00:03:15+00:00"


def test_field_map_handles_missing_keys() -> None:
    fm = default_field_map()
    out = fm.extract({})
    assert out["post_id"] == ""
    assert out["raw_text"] == ""


def test_custom_field_map_override() -> None:
    fm = FieldMap({
        "post_id": lambda x: str(x.get("tweet_id", "")),
        "raw_text": lambda x: x.get("content", ""),
    })
    out = fm.extract({"tweet_id": "999", "content": "hello"})
    assert out["post_id"] == "999"
    assert out["raw_text"] == "hello"


# ===========================================================================
# ResponseCache
# ===========================================================================

def test_response_cache_put_get(tmp_dir: Path) -> None:
    cache = ResponseCache(tmp_dir / "cache", enabled=True)
    inp = {"searchTerms": ["x"], "maxItems": 5}
    assert cache.get(inp) is None
    cache.put(inp, {"items": [{"id": "1"}]})
    out = cache.get(inp)
    assert out is not None
    assert out["items"][0]["id"] == "1"


def test_response_cache_disabled(tmp_dir: Path) -> None:
    cache = ResponseCache(tmp_dir / "cache", enabled=False)
    inp = {"x": 1}
    cache.put(inp, {"items": [1, 2, 3]})
    assert cache.get(inp) is None


def test_response_cache_key_deterministic(tmp_dir: Path) -> None:
    cache = ResponseCache(tmp_dir / "cache", enabled=True)
    a = {"a": 1, "b": 2}
    b = {"b": 2, "a": 1}
    assert cache.path_for(a) == cache.path_for(b)


# ===========================================================================
# 月份切片 + 二分日期
# ===========================================================================

def test_plan_months_12_back() -> None:
    months = _plan_months(12, skip=set())
    assert len(months) == 12
    assert months == sorted(months)


def test_plan_months_skips_done() -> None:
    today = datetime.now(timezone.utc).date().replace(day=1)
    skip = {today.strftime("%Y-%m")}
    months = _plan_months(3, skip=skip)
    assert all(m.strftime("%Y-%m") not in skip for m in months)


def test_next_month() -> None:
    assert _next_month(date(2026, 1, 1)) == date(2026, 2, 1)
    assert _next_month(date(2026, 12, 1)) == date(2027, 1, 1)


def test_mid_date() -> None:
    # 31 天整月 → 中点 = 第 15 天
    assert _mid_date(date(2026, 1, 1), date(2026, 2, 1)) == date(2026, 1, 16)
    # 2 天窗口 → 中点 = 第 1 天
    assert _mid_date(date(2026, 1, 1), date(2026, 1, 3)) == date(2026, 1, 2)


def test_build_run_input_uses_max_per_month() -> None:
    inp = build_run_input("alice", date(2026, 1, 1), date(2026, 2, 1), max_per_month=3000)
    assert inp["maxItems"] == 3000
    assert "from:alice" in inp["searchTerms"][0]
    assert "since:2026-01-01" in inp["searchTerms"][0]
    assert "until:2026-02-01" in inp["searchTerms"][0]
    assert inp["sort"] == "Latest"
    # 2026-06 踩坑:必须 disableMaximization=true,否则 actor 自己 maximize
    # 行为非确定(同输入 11 月返 393/60 差 5x,见 README 踩坑章节)
    assert inp["disableMaximization"] is True


def test_build_run_input_disable_maximization_default() -> None:
    """默认 disable_maximization=True,翻页行为才稳。"""
    inp = build_run_input("alice", date(2026, 1, 1), date(2026, 2, 1))
    assert inp["disableMaximization"] is True
    # 显式传 False 也支持(escape hatch,但 README 不推荐)
    inp2 = build_run_input("alice", date(2026, 1, 1), date(2026, 2, 1), disable_maximization=False)
    assert inp2["disableMaximization"] is False


# ===========================================================================
# scrape_state
# ===========================================================================

def test_scrape_state_init_and_update(db: Path) -> None:
    init_scrape_state(db)
    state = get_scrape_state("alice", db)
    assert state["months_done"] == []
    assert state["total_scraped"] == 0

    update_scrape_state("alice", db, month="2026-01", total_scraped=10)
    state = get_scrape_state("alice", db)
    assert state["months_done"] == ["2026-01"]
    assert state["total_scraped"] == 10

    update_scrape_state("alice", db, month="2026-02", total_scraped=25)
    state = get_scrape_state("alice", db)
    assert state["months_done"] == ["2026-01", "2026-02"]
    assert state["total_scraped"] == 25


# ===========================================================================
# coverage 表
# ===========================================================================

def test_record_coverage_basic(db: Path) -> None:
    init_scrape_state(db)
    record_coverage(
        "alice", db,
        window_start=date(2026, 1, 1), window_end=date(2026, 2, 1),
        items_returned=10, items_persisted=10,
        from_cache=False, subdivided=False, depth=0,
    )
    rows = get_coverage_report("alice", db)
    assert len(rows) == 1
    assert rows[0].window_start == "2026-01-01"
    assert rows[0].items_returned == 10
    assert rows[0].subdivided is False


def test_record_coverage_upsert(db: Path) -> None:
    """同一窗口二次写入会更新而非新增。"""
    init_scrape_state(db)
    record_coverage(
        "alice", db,
        window_start=date(2026, 1, 1), window_end=date(2026, 2, 1),
        items_returned=10, items_persisted=10,
        from_cache=False, subdivided=False, depth=0,
    )
    record_coverage(
        "alice", db,
        window_start=date(2026, 1, 1), window_end=date(2026, 2, 1),
        items_returned=12, items_persisted=12,
        from_cache=False, subdivided=False, depth=0,
    )
    rows = get_coverage_report("alice", db)
    assert len(rows) == 1
    assert rows[0].items_returned == 12


def test_coverage_report_warns_zero(db: Path) -> None:
    init_scrape_state(db)
    for m in range(1, 6):
        record_coverage(
            "bob", db,
            window_start=date(2026, m, 1), window_end=date(2026, m + 1, 1),
            items_returned=10, items_persisted=10,
            from_cache=False, subdivided=False, depth=0,
        )
    # 加一个 0 条
    record_coverage(
        "bob", db,
        window_start=date(2026, 6, 1), window_end=date(2026, 7, 1),
        items_returned=0, items_persisted=0,
        from_cache=False, subdivided=False, depth=0,
    )
    report = format_coverage_report("bob", db)
    assert "WARNING" in report
    assert "0 tweets" in report


def test_coverage_report_warns_abnormally_low(db: Path) -> None:
    init_scrape_state(db)
    # 5 个月平均 100 条,第 6 个月 1 条 → 异常低
    for m in range(1, 6):
        record_coverage(
            "carol", db,
            window_start=date(2026, m, 1), window_end=date(2026, m + 1, 1),
            items_returned=100, items_persisted=100,
            from_cache=False, subdivided=False, depth=0,
        )
    record_coverage(
        "carol", db,
        window_start=date(2026, 6, 1), window_end=date(2026, 7, 1),
        items_returned=1, items_persisted=1,
        from_cache=False, subdivided=False, depth=0,
    )
    report = format_coverage_report("carol", db)
    assert "WARNING" in report


def test_coverage_report_no_warning_when_uniform(db: Path) -> None:
    init_scrape_state(db)
    for m in range(1, 6):
        record_coverage(
            "dave", db,
            window_start=date(2026, m, 1), window_end=date(2026, m + 1, 1),
            items_returned=50, items_persisted=50,
            from_cache=False, subdivided=False, depth=0,
        )
    report = format_coverage_report("dave", db)
    assert "WARNING" not in report


def test_coverage_report_empty(db: Path) -> None:
    init_scrape_state(db)
    report = format_coverage_report("nobody", db)
    assert "no coverage data" in report


def test_coverage_report_marks_subdivided_months(db: Path) -> None:
    init_scrape_state(db)
    # 整月 subdivided=1,加几个子窗口
    record_coverage(
        "eve", db,
        window_start=date(2026, 1, 1), window_end=date(2026, 2, 1),
        items_returned=3000, items_persisted=0,
        from_cache=False, subdivided=True, depth=0,
    )
    record_coverage(
        "eve", db,
        window_start=date(2026, 1, 1), window_end=date(2026, 1, 16),
        items_returned=1500, items_persisted=1500,
        from_cache=False, subdivided=False, depth=1,
    )
    record_coverage(
        "eve", db,
        window_start=date(2026, 1, 16), window_end=date(2026, 2, 1),
        items_returned=1500, items_persisted=1500,
        from_cache=False, subdivided=False, depth=1,
    )
    report = format_coverage_report("eve", db)
    assert "subdivided" in report
    # 拿 per-month 表的月份行,看 subdivided 列是 'Y'
    lines = report.splitlines()
    in_month_section = False
    month_line_found = False
    for line in lines:
        if line.startswith("## per-month"):
            in_month_section = True
            continue
        if not in_month_section:
            continue
        if line.startswith("2026-01"):
            month_line_found = True
            cols = line.split()
            # 列: month, items, subdivided, flag...
            assert cols[3] == "Y", f"expected subdivided=Y, got {cols[3]!r}, line={line!r}"
    assert month_line_found, "per-month line for 2026-01 not found"


def test_coverage_report_excludes_sentinels_from_histogram(db: Path) -> None:
    """窗口返 5 条 (3 推 + 2 哨兵)  → histogram 应只算 3 推文。"""
    init_scrape_state(db)
    record_coverage(
        "alice", db,
        window_start=date(2026, 1, 1), window_end=date(2026, 2, 1),
        items_returned=5, items_persisted=3,
        from_cache=False, subdivided=False, depth=0,
        sentinel_count=2,
    )
    report = format_coverage_report("alice", db)
    assert "WARNING" not in report
    assert "real" in report
    in_per_month = False
    for line in report.splitlines():
        if line.startswith("## per-month"):
            in_per_month = True
            continue
        if in_per_month and line.startswith("2026-01"):
            cols = line.split()
            assert cols[1] == "3", f"expected real=3, got {cols[1]!r}"
            return


def test_coverage_report_flags_sentinel_only_month(db: Path) -> None:
    """窗口返 2 个哨兵(账户静默期),per-month 不应报 WARNING,应标 ○ 哨兵。"""
    init_scrape_state(db)
    for m in range(1, 6):
        record_coverage(
            "alice", db,
            window_start=date(2026, m, 1), window_end=date(2026, m + 1, 1),
            items_returned=100, items_persisted=100,
            from_cache=False, subdivided=False, depth=0,
        )
    record_coverage(
        "alice", db,
        window_start=date(2026, 6, 1), window_end=date(2026, 7, 1),
        items_returned=2, items_persisted=0,
        from_cache=False, subdivided=False, depth=0,
        sentinel_count=2,
    )
    report = format_coverage_report("alice", db)
    in_per_month = False
    for line in report.splitlines():
        if line.startswith("## per-month"):
            in_per_month = True
            continue
        if in_per_month and line.startswith("2026-06"):
            assert "哨兵" in line, f"expected 哨兵 flag, got: {line!r}"
            assert "WARNING" not in line, f"should not be WARNING, got: {line!r}"
            return


def test_set_coverage_note(db: Path) -> None:
    init_scrape_state(db)
    record_coverage(
        "alice", db,
        window_start=date(2026, 1, 1), window_end=date(2026, 2, 1),
        items_returned=10, items_persisted=10,
        from_cache=False, subdivided=False, depth=0,
    )
    set_coverage_note("alice", db, "2026-01-01", "人工复查:是真实低产,不是抓取缺口")
    rows = get_coverage_report("alice", db)
    assert rows[0].note == "人工复查:是真实低产,不是抓取缺口"
    set_coverage_note("alice", db, "2026-01-01", "改:已确认 APIfy 未抓到,需手动补充")
    rows = get_coverage_report("alice", db)
    assert "手动补充" in rows[0].note


# ===========================================================================
# item → RawPost
# ===========================================================================

def test_item_to_raw_post_normal() -> None:
    item = {
        "id": "111",
        "text": "看好 NVDA",
        "createdAt": "2026-05-28T14:30:00Z",
        "url": "https://x.com/u/status/111",
        "author": {"userName": "u"},
    }
    post = _item_to_raw_post(item, default_field_map(), "tw_u", "2026-06-01T00:00:00+00:00")
    assert post.post_id == "111"
    assert post.raw_text == "看好 NVDA"
    assert post.published_at == "2026-05-28T14:30:00+00:00"
    assert post.platform == Platform.TWITTER.value
    assert "111" in post.raw_json


def test_item_to_raw_post_missing_id_raises() -> None:
    item = {"text": "no id"}
    try:
        _item_to_raw_post(item, default_field_map(), "tw_u", "2026-06-01T00:00:00+00:00")
    except ValueError as e:
        assert "post_id" in str(e)
        return
    raise AssertionError("expected ValueError for missing post_id")


def test_item_to_raw_post_published_at_fallback() -> None:
    item = {"id": "1", "text": "t", "url": "u"}
    post = _item_to_raw_post(item, default_field_map(), "tw_u", "2026-06-01T00:00:00+00:00")
    assert post.published_at == "2026-06-01T00:00:00+00:00"


def test_item_to_raw_post_skips_noResults_sentinel() -> None:
    """apidojo/tweet-scraper V2 子窗口无推文时返 `{"noResults": true}` 哨兵,
    应当静默跳过(抛 _NoTweetSentinel),不能算 parse 错误。"""
    from signalboard.scraper import _NoTweetSentinel
    item = {"noResults": True}
    try:
        _item_to_raw_post(item, default_field_map(), "tw_u", "2026-06-01T00:00:00+00:00")
    except _NoTweetSentinel:
        pass  # 预期
    else:
        raise AssertionError("expected _NoTweetSentinel for noResults sentinel")


def test_item_to_raw_post_handles_non_dict_item() -> None:
    """防御:item 不是 dict 时也走 _NoTweetSentinel(不是 ValueError)。"""
    from signalboard.scraper import _NoTweetSentinel
    try:
        _item_to_raw_post("not a dict", default_field_map(), "tw_u", "2026-06-01T00:00:00+00:00")
    except _NoTweetSentinel:
        pass
    else:
        raise AssertionError("expected _NoTweetSentinel for non-dict item")


# ===========================================================================
# _fetch_window:截断检测 + 二分细分
# ===========================================================================

def test_no_subdivision_under_limit(db: Path) -> None:
    """返回条数 < max_per_month,不细分。"""
    init_scrape_state(db)
    cache = ResponseCache(db.parent / "cache_nsd", enabled=False)
    client = FakeApifyClient(scripts={"*": _make_items(10, "a")})

    result = _fetch_window(
        "u", db,
        start=date(2026, 1, 1), end=date(2026, 2, 1),
        max_per_month=50, cache=cache, field_map=default_field_map(),
        apify_client=client,
        captured_at="2026-06-01T00:00:00+00:00", source_id="tw_u", depth=0,
    )
    assert result.items_returned == 10
    assert result.subdivided is False
    assert len(result.posts) == 10
    # coverage 表只一行
    rows = get_coverage_report("u", db)
    assert len(rows) == 1
    assert rows[0].subdivided is False


def test_subdivision_one_level(db: Path) -> None:
    """返回条数 == max_per_month,触发一次细分(2 个子窗口)。"""
    init_scrape_state(db)
    cache = ResponseCache(db.parent / "cache_sub1", enabled=False)

    # 整月 [01-01, 02-01) 返回 50 条 → 触发细分
    # 两个子窗口各自返回 30 条 → 不再细分
    def script_for(ri):
        st = ri["searchTerms"][0]
        if "since:2026-01-01" in st and "until:2026-02-01" in st:
            return _make_items(50, "x")
        return _make_items(30, "x")

    client = FakeApifyClient(scripts={script_for: None})

    result = _fetch_window(
        "u", db,
        start=date(2026, 1, 1), end=date(2026, 2, 1),
        max_per_month=50, cache=cache, field_map=default_field_map(),
        apify_client=client,
        captured_at="2026-06-01T00:00:00+00:00", source_id="tw_u", depth=0,
    )
    assert result.items_returned == 50
    assert result.subdivided is True
    assert result.items_persisted == 60  # 30 + 30
    # coverage 表:父(subdivided) + 2 子
    rows = get_coverage_report("u", db)
    assert len(rows) == 3
    parent = [r for r in rows if r.subdivided]
    children = [r for r in rows if not r.subdivided]
    assert len(parent) == 1
    assert len(children) == 2


def test_subdivision_three_levels(db: Path) -> None:
    """深度细分,父 + 2 子(subdivided) + 4 孙子 = 7 行 coverage。"""
    init_scrape_state(db)
    cache = ResponseCache(db.parent / "cache_sub3", enabled=False)

    # max_per_month=20,前两层(整月+半月)返回 20 触发细分,第三层(7 天)返回 < 20
    def script_for(ri):
        st = ri["searchTerms"][0]
        # 第三层子窗口:起止在 1 月 1-16 半月内的更细分
        if "since:2026-01-01" in st and "until:2026-01-08" in st:
            return _make_items(10, "z")
        if "since:2026-01-08" in st and "until:2026-01-16" in st:
            return _make_items(10, "z")
        if "since:2026-01-16" in st and "until:2026-01-24" in st:
            return _make_items(10, "z")
        if "since:2026-01-24" in st and "until:2026-02-01" in st:
            return _make_items(10, "z")
        return _make_items(20, "z")  # 父/子 → 触发细分

    client = FakeApifyClient(scripts={script_for: None})

    result = _fetch_window(
        "u", db,
        start=date(2026, 1, 1), end=date(2026, 2, 1),
        max_per_month=20, cache=cache, field_map=default_field_map(),
        apify_client=client,
        captured_at="2026-06-01T00:00:00+00:00", source_id="tw_u", depth=0,
    )
    assert result.subdivided is True
    # 深度 0(父 subdivided)+ 1(2 子 subdivided)+ 2(4 孙不 subdivided)= 7
    rows = get_coverage_report("u", db)
    assert len(rows) == 7, f"expected 7, got {len(rows)}"
    subdivided = [r for r in rows if r.subdivided]
    assert len(subdivided) == 3  # 父 + 2 子


def test_subdivision_hits_max_depth(db: Path) -> None:
    """达到 max_depth 仍截断 → 报错但不崩。"""
    init_scrape_state(db)
    cache = ResponseCache(db.parent / "cache_submax", enabled=False)
    # max_per_month=2,需要细分 ~6 层才能停下,但每窗口都返回 2 条 → 截断
    client = FakeApifyClient(scripts={"*": _make_items(2, "q")})

    # 用小窗口(< 2^MAX_SUBDIVISION_DEPTH 天)以避免无限递归
    result = _fetch_window(
        "u", db,
        start=date(2026, 1, 1), end=date(2026, 1, 10),  # 9 天
        max_per_month=2, cache=cache, field_map=default_field_map(),
        apify_client=client,
        captured_at="2026-06-01T00:00:00+00:00", source_id="tw_u", depth=0,
    )
    # 9 天 / 2^depth,depth=3 → 9/8=1.1 天,可能再分
    # 关键是不要崩,且能拿到结果
    assert result.items_returned >= 0


# ===========================================================================
# 端到端:fetch_account_history 跑两次,行数不变
# ===========================================================================

def test_idempotency_run_twice(tmp_dir: Path) -> None:
    db = tmp_dir / "test.db"
    cache_dir = tmp_dir / "cache"
    # 用 _make_items 而不是 fixture:fixture 是 --record 1 拿的真实样本(1 条)
    items = _make_items(5, "id")

    client1 = FakeApifyClient(scripts={"*": items})
    s1 = fetch_account_history(
        handle="aleabitoreddit", db_path=db,
        max_per_month=10, months_back=1,
        cache_dir=cache_dir, use_cache=False, apify_client=client1,
    )
    assert s1.total_scraped == 5
    rows = list_raw_posts_by_source("tw_aleabitoreddit", db)
    assert len(rows) == 5

    # 第二次:months_done 已包含,跳过该月;即便 cache=False 也不调 actor
    calls_before = len(client1.actor_calls)
    s2 = fetch_account_history(
        handle="aleabitoreddit", db_path=db,
        max_per_month=10, months_back=1,
        cache_dir=cache_dir, use_cache=False, apify_client=client1,
    )
    assert s2.total_scraped == 5
    rows2 = list_raw_posts_by_source("tw_aleabitoreddit", db)
    assert len(rows2) == 5
    assert len(client1.actor_calls) == calls_before  # 没新调


# ===========================================================================
# 端到端:断点续抓
# ===========================================================================

def test_resume_after_interruption(tmp_dir: Path) -> None:
    db = tmp_dir / "test.db"
    items = _make_items(5, "r")

    now = datetime.now(timezone.utc).date()
    this_month = now.strftime("%Y-%m")
    prev_month = date(
        now.year if now.month > 1 else now.year - 1,
        12 if now.month == 1 else now.month - 1,
        1,
    ).strftime("%Y-%m")
    next_month_iso = date(
        now.year if now.month < 12 else now.year + 1,
        1 if now.month == 12 else now.month + 1,
        1,
    ).isoformat()

    def script_for(run_input):
        if f"until:{next_month_iso}" in run_input["searchTerms"][0]:
            return items
        return []

    client = FakeApifyClient(scripts={script_for: items})
    s1 = fetch_account_history(
        handle="bob", db_path=db,
        max_per_month=10, months_back=1,
        cache_dir=tmp_dir / "cache", use_cache=False, apify_client=client,
    )
    assert s1.total_scraped == 5
    state = get_scrape_state("bob", db)
    assert this_month in state["months_done"]

    s2 = fetch_account_history(
        handle="bob", db_path=db,
        max_per_month=10, months_back=2,
        cache_dir=tmp_dir / "cache2", use_cache=False, apify_client=client,
    )
    assert this_month not in s2.months_planned
    assert s2.total_scraped == 5
    state2 = get_scrape_state("bob", db)
    assert prev_month in state2["months_done"]


# ===========================================================================
# 端到端:触发细分的全量跑
# ===========================================================================

def test_full_run_with_subdivision(tmp_dir: Path) -> None:
    """整月 1 次返回 == max_per_month → 触发细分 → 月份完成。"""
    db = tmp_dir / "test.db"
    cache = ResponseCache(tmp_dir / "cache", enabled=False)
    # max_per_month=20 触发细分
    client = FakeApifyClient(scripts={"*": _make_items(20, "f")})

    s = fetch_account_history(
        handle="frank", db_path=db,
        max_per_month=20, months_back=1,
        cache_dir=tmp_dir / "cache", use_cache=False, apify_client=client,
    )
    assert s.windows_subdivided == 1
    assert s.total_scraped > 0
    # coverage 表应有 1 个父(subdivided) + 多个子
    rows = get_coverage_report("frank", db)
    assert any(r.subdivided for r in rows)


# ===========================================================================
# 单条解析失败不中断
# ===========================================================================

def test_one_bad_item_continues(tmp_dir: Path) -> None:
    db = tmp_dir / "test.db"
    items = _make_items(5, "good") + [
        {"id": "", "text": "missing id"},
        {"text": "missing id and url"},
    ]
    client = FakeApifyClient(scripts={"*": items})
    s = fetch_account_history(
        handle="charlie", db_path=db,
        max_per_month=10, months_back=1,
        cache_dir=tmp_dir / "cache", use_cache=False, apify_client=client,
    )
    assert s.total_scraped == 5
    assert any(e["phase"] == "parse" for e in s.errors)


# ===========================================================================
# 指数退避
# ===========================================================================

def test_call_actor_retries_with_backoff() -> None:
    class AlwaysFailClient:
        def __init__(self):
            self.calls = 0
        def actor(self, _id):
            return self
        def call(self, **kw):
            self.calls += 1
            raise RuntimeError("simulated 5xx")
        def dataset(self, _id):
            return self
        def iterate_items(self):
            return iter([])

    c = AlwaysFailClient()
    t0 = time.time()
    try:
        _call_actor({"x": 1}, "", client=c, max_retries=3, backoff_base=1.0)
    except RuntimeError:
        pass
    elapsed = time.time() - t0
    assert c.calls == 3
    assert elapsed >= 1.5, f"expected at least 1.5s backoff, got {elapsed:.2f}"


# ===========================================================================
# CLI
# ===========================================================================

def test_cli_scrape_help() -> None:
    p = _build_scrape_parser()
    buf = io.StringIO()
    try:
        with contextlib.redirect_stdout(buf):
            p.parse_args(["--help"])
    except SystemExit:
        pass
    out = buf.getvalue()
    assert "--handle" in out
    assert "--max-per-month" in out  # v2 改名了
    assert "--months-back" in out


def test_cli_coverage_help() -> None:
    p = _build_coverage_parser()
    buf = io.StringIO()
    try:
        with contextlib.redirect_stdout(buf):
            p.parse_args(["--help"])
    except SystemExit:
        pass
    out = buf.getvalue()
    assert "--handle" in out
    assert "--db" in out


def test_cli_main_subcommand_coverage(tmp_dir: Path, capsys=None) -> None:
    """python -m signalboard.scraper coverage --handle X 应该打印报告。"""
    from signalboard.scraper import main
    db = tmp_dir / "test.db"
    init_scrape_state(db)
    record_coverage(
        "gina", db,
        window_start=date(2026, 1, 1), window_end=date(2026, 2, 1),
        items_returned=10, items_persisted=10,
        from_cache=False, subdivided=False, depth=0,
    )
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        rc = main(["coverage", "--handle", "gina", "--db", str(db)])
    assert rc == 0
    out = buf.getvalue()
    assert "coverage report" in out
    assert "2026-01" in out


def test_cli_main_legacy_form(tmp_dir: Path) -> None:
    """老调用形式 python -m signalboard.scraper --handle X --db Y ... 仍能用。"""
    from signalboard.scraper import main
    db = tmp_dir / "test.db"
    client = FakeApifyClient(scripts={"*": _make_items(2, "L")})
    # 直接用 _cmd_scrape 模拟,避免日志污染
    args = _build_scrape_parser().parse_args([
        "--handle", "legacy",
        "--db", str(db),
        "--max-per-month", "3",  # > items 数,避免触发细分
        "--months-back", "1",
        "--cache-dir", str(tmp_dir / "cache"),
    ])
    # apify_client 必须传给 fetch_account_history
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        s = fetch_account_history(
            handle=args.handle, db_path=args.db,
            max_per_month=args.max_per_month, months_back=args.months_back,
            cache_dir=args.cache_dir, use_cache=False, apify_client=client,
        )
    assert s.total_scraped == 2


# ===========================================================================
# main
# ===========================================================================

def main() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        tmp_dir = Path(tmp)
        # 时间转换
        test_to_utc_iso_z_suffix()
        test_to_utc_iso_with_offset()
        test_to_utc_iso_naive_assumes_utc()
        test_to_utc_iso_unix_seconds()
        test_to_utc_iso_unix_milliseconds()
        test_to_utc_iso_empty()
        test_to_utc_iso_twitter_ctime()
        test_to_utc_iso_twitter_ctime_non_utc()
        # FieldMap
        test_default_field_map_extracts_all()
        test_field_map_handles_missing_keys()
        test_custom_field_map_override()
        # Cache
        test_response_cache_put_get(tmp_dir)
        test_response_cache_disabled(tmp_dir)
        test_response_cache_key_deterministic(tmp_dir)
        # 月份 + 二分日期
        test_plan_months_12_back()
        test_plan_months_skips_done()
        test_next_month()
        test_mid_date()
        test_build_run_input_uses_max_per_month()
        # state
        test_scrape_state_init_and_update(tmp_dir / "state.db")
        # coverage
        test_record_coverage_basic(tmp_dir / "cov.db")
        test_record_coverage_upsert(tmp_dir / "cov_up.db")
        test_coverage_report_warns_zero(tmp_dir / "cov0.db")
        test_coverage_report_warns_abnormally_low(tmp_dir / "covlow.db")
        test_coverage_report_no_warning_when_uniform(tmp_dir / "covu.db")
        test_coverage_report_empty(tmp_dir / "cove.db")
        test_coverage_report_marks_subdivided_months(tmp_dir / "covsub.db")
        test_coverage_report_excludes_sentinels_from_histogram(tmp_dir / "covs.db")
        test_coverage_report_flags_sentinel_only_month(tmp_dir / "covs2.db")
        test_set_coverage_note(tmp_dir / "note.db")
        # item → RawPost
        test_item_to_raw_post_normal()
        test_item_to_raw_post_missing_id_raises()
        test_item_to_raw_post_published_at_fallback()
        test_item_to_raw_post_converts_ctime_published_at()
        test_item_to_raw_post_skips_noResults_sentinel()
        test_item_to_raw_post_handles_non_dict_item()
        # _fetch_window
        test_no_subdivision_under_limit(tmp_dir / "nsd.db")
        test_subdivision_one_level(tmp_dir / "sub1.db")
        test_subdivision_three_levels(tmp_dir / "sub3.db")
        test_subdivision_hits_max_depth(tmp_dir / "submax.db")
        # 端到端
        test_idempotency_run_twice(tmp_dir / "idem.db")
        test_resume_after_interruption(tmp_dir / "resume.db")
        test_full_run_with_subdivision(tmp_dir / "full.db")
        test_one_bad_item_continues(tmp_dir / "bad.db")
        # 重试
        test_call_actor_retries_with_backoff()
        # CLI
        test_cli_scrape_help()
        test_cli_coverage_help()
        test_cli_main_subcommand_coverage(tmp_dir / "cli1.db")
        test_cli_main_legacy_form(tmp_dir / "cli2.db")
    print("\nAll scraper tests passed ✅")


if __name__ == "__main__":
    main()
