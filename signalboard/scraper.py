"""signalboard.scraper — Apify apidojo/tweet-scraper V2 抓取层。

设计:
- 数据源:Apify 平台上的 apidojo/tweet-scraper V2(actor ID = "apidojo/tweet-scraper")
- 调用:官方 Python 客户端 apify-client(`pip install apify-client`)
- Token:从环境变量 APIFY_TOKEN 读取
- 翻页策略:按月切片 → 触发截断检测时二分细分,直到每窗口返回 < maxItems
- 字段映射:可配置 FieldMap,默认基于 Twitter 高级搜索式输出
- 本地缓存:.cache/ 目录,按 run_input 的 hash 命名,避免重复扣费
- 进度:scrape_state 表(月份完成情况)+ coverage 表(每次窗口抓取的明细)
- 幂等:复用 signalboard.repository.upsert_raw_post,按 post_id 去重

⚠️ 首次使用前:用 `python -m signalboard.scraper --handle X --record 1` 跑一次
真实 API,把响应存到 fixtures/tweet_response_sample.json,然后校准
default_field_map() 里的字段名(如果 actor 输出 schema 跟默认假设不同)。
"""
from __future__ import annotations

import hashlib
import json
import logging
import os
import statistics
import time
from dataclasses import asdict, dataclass, field
from datetime import date, datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Callable, Dict, Iterable, List, Optional, Sequence, Set, Tuple, Union

from .db import DbPath, get_conn, init_db
from .models import Platform, RawPost
from .repository import upsert_raw_post

log = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# 常量
# ---------------------------------------------------------------------------

ACTOR_ID = "apidojo/tweet-scraper"

# ⚠️ v2:不再设 50 条采样上限;目标是全量。
#   3000 是 apidojo tweet-scraper V2 单次 run 的合理上限
#   (再高就要更长 wait time,二分细分兜底)
DEFAULT_MAX_PER_MONTH = 3000
MAX_SUBDIVISION_DEPTH = 6   # 2^6=64 段,每段 ~0.5 天,够细

ENV_API_TOKEN = "APIFY_TOKEN"
DEFAULT_CACHE_DIR = ".cache"
DEFAULT_DB_PATH = "data/signalboard.db"

# scrape_state 表:断点续抓(只到月份级别)
SCRAPE_STATE_TABLE_SQL = """
CREATE TABLE IF NOT EXISTS scrape_state (
    handle         TEXT PRIMARY KEY,
    last_run_id    TEXT,
    months_done    TEXT    NOT NULL DEFAULT '[]',   -- JSON list of "YYYY-MM"
    total_scraped  INTEGER NOT NULL DEFAULT 0,
    last_updated   TEXT    NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ', 'now'))
);
CREATE INDEX IF NOT EXISTS idx_scrape_state_updated ON scrape_state(last_updated);
"""

# coverage 表:每个窗口的抓取明细(细到天级别)
# 用窗口起止日期作为主键的一部分,细分后父窗口也会留下一行(标 subdivided=1)
COVERAGE_TABLE_SQL = """
CREATE TABLE IF NOT EXISTS coverage (
    handle           TEXT    NOT NULL,
    window_start     TEXT    NOT NULL,                  -- ISO date "YYYY-MM-DD"
    window_end       TEXT    NOT NULL,                  -- ISO date "YYYY-MM-DD"
    items_returned   INTEGER NOT NULL,
    items_persisted  INTEGER NOT NULL,
    from_cache       INTEGER NOT NULL DEFAULT 0,
    subdivided       INTEGER NOT NULL DEFAULT 0,        -- 此窗口曾被二分(父窗口用 1)
    depth            INTEGER NOT NULL DEFAULT 0,
    sentinel_count   INTEGER NOT NULL DEFAULT 0,        -- 被过滤的 noResults 哨兵数
    note             TEXT,                              -- 人工备注
    scraped_at       TEXT    NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ', 'now')),
    PRIMARY KEY (handle, window_start, window_end)
);
CREATE INDEX IF NOT EXISTS idx_coverage_handle ON coverage(handle);
"""


# ===========================================================================
# 字段映射
# ===========================================================================

class FieldMap:
    """从 actor 输出 item 提取 raw_posts 字段的可配置映射。

    默认值基于 Twitter / apidojo tweet-scraper 常见命名约定;真实字段名
    以用户首次 --record 1 的输出为准,可以通过 FieldMap({...}) 自定义。
    """

    def __init__(self, extractors: Dict[str, Callable[[dict], Any]]):
        self.extractors = extractors

    def extract(self, item: dict) -> Dict[str, Any]:
        out: Dict[str, Any] = {}
        for k, fn in self.extractors.items():
            try:
                out[k] = fn(item)
            except Exception as e:
                log.debug("field %s extraction failed: %s", k, e)
                out[k] = None
        return out


def default_field_map() -> FieldMap:
    return FieldMap({
        "post_id": lambda x: str(
            x.get("id") or x.get("tweet_id") or x.get("id_str") or x.get("tweetId") or ""
        ),
        "raw_text": lambda x: (
            x.get("text") or x.get("full_text") or x.get("rawContent")
            or x.get("fullText") or ""
        ),
        "raw_url": lambda x: (
            x.get("url") or x.get("twitterUrl") or x.get("tweetUrl")
            or x.get("permalink") or ""
        ),
        "published_at": lambda x: (
            x.get("createdAt") or x.get("created_at") or x.get("date")
            or x.get("timestamp") or ""
        ),
        "author_handle": lambda x: (
            (x.get("author") or {}).get("userName")
            if isinstance(x.get("author"), dict)
            else None
        ) or x.get("userName") or x.get("screen_name") or "",
    })


# ===========================================================================
# 时间转换
# ===========================================================================

def to_utc_iso(timestamp: Any) -> str:
    """把 actor 输出的时间字段归一为 UTC ISO-8601 字符串。

    支持:
    - ISO 8601 字符串(带 Z / +00:00 offset / 无时区)
    - Twitter API ctime 格式:`Fri Jun 05 00:03:15 +0000 2026`
    - int / float Unix timestamp(秒或毫秒,>1e12 视为毫秒)
    - 空值返回空字符串
    - 解析失败原样返回
    """
    if timestamp is None or timestamp == "":
        return ""
    if isinstance(timestamp, (int, float)):
        ts = float(timestamp)
        if ts > 1e12:
            ts = ts / 1000.0
        return datetime.fromtimestamp(ts, tz=timezone.utc).isoformat()
    if isinstance(timestamp, str):
        s = timestamp.strip()
        if not s:
            return ""
        if s.endswith("Z"):
            s = s[:-1] + "+00:00"
        try:
            dt = datetime.fromisoformat(s)
        except ValueError:
            pass
        else:
            if dt.tzinfo is None:
                dt = dt.replace(tzinfo=timezone.utc)
            return dt.astimezone(timezone.utc).isoformat()
        # Twitter API ctime:`Fri Jun 05 00:03:15 +0000 2026`
        try:
            dt = datetime.strptime(s, "%a %b %d %H:%M:%S %z %Y")
        except ValueError:
            return timestamp
        return dt.astimezone(timezone.utc).isoformat()
    return str(timestamp)


# ===========================================================================
# 本地响应缓存
# ===========================================================================

class ResponseCache:
    """按 run_input 的规范 JSON + sha256 命名。"""

    def __init__(self, cache_dir: Union[str, Path] = DEFAULT_CACHE_DIR, enabled: bool = True):
        self.cache_dir = Path(cache_dir)
        self.enabled = enabled

    @staticmethod
    def _key(run_input: dict) -> str:
        canonical = json.dumps(run_input, sort_keys=True, ensure_ascii=False)
        return hashlib.sha256(canonical.encode("utf-8")).hexdigest()[:32]

    def path_for(self, run_input: dict) -> Path:
        return self.cache_dir / f"{self._key(run_input)}.json"

    def get(self, run_input: dict) -> Optional[dict]:
        if not self.enabled:
            return None
        p = self.path_for(run_input)
        if not p.exists():
            return None
        try:
            return json.loads(p.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError) as e:
            log.warning("cache read failed for %s: %s", p, e)
            return None

    def put(self, run_input: dict, data: dict) -> None:
        if not self.enabled:
            return
        p = self.path_for(run_input)
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(
            json.dumps(data, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )


# ===========================================================================
# 进度表 + coverage 表
# ===========================================================================

def init_scrape_state(db_path: DbPath) -> None:
    """建 scrape_state + coverage 表,顺带 init_db(幂等),并自动迁移旧表(加 sentinel_count / note)。"""
    init_db(db_path)
    with get_conn(db_path) as conn:
        conn.executescript(SCRAPE_STATE_TABLE_SQL)
        conn.executescript(COVERAGE_TABLE_SQL)
        # 兼容旧 coverage 表(Phase 1 之前建的没 sentinel_count / note 列)
        cur = conn.execute("PRAGMA table_info(coverage)")
        cols = {row[1] for row in cur.fetchall()}
        if "sentinel_count" not in cols:
            conn.execute("ALTER TABLE coverage ADD COLUMN sentinel_count INTEGER NOT NULL DEFAULT 0")
        if "note" not in cols:
            conn.execute("ALTER TABLE coverage ADD COLUMN note TEXT")


def get_scrape_state(handle: str, db_path: DbPath) -> dict:
    with get_conn(db_path) as conn:
        row = conn.execute(
            "SELECT * FROM scrape_state WHERE handle = ?", (handle,)
        ).fetchone()
        if not row:
            return {"handle": handle, "months_done": [], "total_scraped": 0, "last_run_id": None}
        return {
            "handle": row["handle"],
            "months_done": json.loads(row["months_done"] or "[]"),
            "total_scraped": int(row["total_scraped"]),
            "last_run_id": row["last_run_id"],
        }


def update_scrape_state(
    handle: str,
    db_path: DbPath,
    *,
    month: Optional[str] = None,
    total_scraped: Optional[int] = None,
    run_id: Optional[str] = None,
) -> None:
    state = get_scrape_state(handle, db_path)
    months = set(state["months_done"])
    if month:
        months.add(month)
    months_list = sorted(months)
    new_total = total_scraped if total_scraped is not None else state["total_scraped"]
    new_run_id = run_id if run_id is not None else state["last_run_id"]
    with get_conn(db_path) as conn:
        conn.execute(
            """
            INSERT INTO scrape_state (handle, last_run_id, months_done, total_scraped, last_updated)
            VALUES (?, ?, ?, ?, strftime('%Y-%m-%dT%H:%M:%fZ', 'now'))
            ON CONFLICT(handle) DO UPDATE SET
                last_run_id   = excluded.last_run_id,
                months_done   = excluded.months_done,
                total_scraped = excluded.total_scraped,
                last_updated  = excluded.last_updated
            """,
            (handle, new_run_id, json.dumps(months_list), new_total),
        )


def record_coverage(
    handle: str,
    db_path: DbPath,
    *,
    window_start: date,
    window_end: date,
    items_returned: int,
    items_persisted: int,
    from_cache: bool,
    subdivided: bool,
    depth: int,
    sentinel_count: int = 0,
    note: Optional[str] = None,
) -> None:
    """记录一次窗口抓取的明细。"""
    with get_conn(db_path) as conn:
        # 已有 note 不覆盖(只初次写入)
        if note is None:
            conn.execute(
                """
                INSERT INTO coverage (handle, window_start, window_end,
                                      items_returned, items_persisted,
                                      from_cache, subdivided, depth, sentinel_count)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(handle, window_start, window_end) DO UPDATE SET
                    items_returned  = excluded.items_returned,
                    items_persisted = excluded.items_persisted,
                    from_cache      = excluded.from_cache,
                    subdivided      = excluded.subdivided,
                    depth           = excluded.depth,
                    sentinel_count  = excluded.sentinel_count,
                    scraped_at      = strftime('%Y-%m-%dT%H:%M:%fZ', 'now')
                """,
                (
                    handle,
                    window_start.isoformat(),
                    window_end.isoformat(),
                    items_returned,
                    items_persisted,
                    int(from_cache),
                    int(subdivided),
                    depth,
                    sentinel_count,
                ),
            )
        else:
            conn.execute(
                """
                INSERT INTO coverage (handle, window_start, window_end,
                                      items_returned, items_persisted,
                                      from_cache, subdivided, depth, sentinel_count, note)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(handle, window_start, window_end) DO UPDATE SET
                    items_returned  = excluded.items_returned,
                    items_persisted = excluded.items_persisted,
                    from_cache      = excluded.from_cache,
                    subdivided      = excluded.subdivided,
                    depth           = excluded.depth,
                    sentinel_count  = excluded.sentinel_count,
                    note            = COALESCE(coverage.note, excluded.note),
                    scraped_at      = strftime('%Y-%m-%dT%H:%M:%fZ', 'now')
                """,
                (
                    handle,
                    window_start.isoformat(),
                    window_end.isoformat(),
                    items_returned,
                    items_persisted,
                    int(from_cache),
                    int(subdivided),
                    depth,
                    sentinel_count,
                    note,
                ),
            )


def set_coverage_note(
    handle: str,
    db_path: DbPath,
    window_start: str,
    note: str,
) -> None:
    """给某窗口加/覆盖人工备注(Phase 1 调试用)。"""
    with get_conn(db_path) as conn:
        conn.execute(
            "UPDATE coverage SET note = ? WHERE handle = ? AND window_start = ?",
            (note, handle, window_start),
        )


@dataclass
class CoverageRow:
    window_start: str
    window_end: str
    items_returned: int
    items_persisted: int
    from_cache: bool
    subdivided: bool
    depth: int
    sentinel_count: int = 0
    note: Optional[str] = None
    scraped_at: str = ""

    def month_key(self) -> str:
        return self.window_start[:7]

    @property
    def real_tweet_count(self) -> int:
        """实际推文数(items_returned - sentinel_count),不包含 actor 的空窗口哨兵。"""
        return max(0, self.items_returned - self.sentinel_count)


def get_coverage_report(handle: str, db_path: DbPath) -> List[CoverageRow]:
    """返回某 handle 的所有 coverage 行,按 window_start 升序。"""
    with get_conn(db_path) as conn:
        rows = conn.execute(
            "SELECT * FROM coverage WHERE handle = ? ORDER BY window_start",
            (handle,),
        ).fetchall()
    return [
        CoverageRow(
            window_start=r["window_start"],
            window_end=r["window_end"],
            items_returned=r["items_returned"],
            items_persisted=r["items_persisted"],
            from_cache=bool(r["from_cache"]),
            subdivided=bool(r["subdivided"]),
            depth=r["depth"],
            sentinel_count=r["sentinel_count"] or 0,
            note=r["note"],
            scraped_at=r["scraped_at"],
        )
        for r in rows
    ]


def format_coverage_report(handle: str, db_path: DbPath) -> str:
    """渲染可读报告 + 异常窗口 WARNING(只看真实推文数,排除 noResults 哨兵)。"""
    rows = get_coverage_report(handle, db_path)
    if not rows:
        return f"handle={handle}: no coverage data yet. 跑一次 scrape 后再查。"

    # 用 real_tweet_count(= items_returned - sentinel_count)算 histogram
    real_counts = [r.real_tweet_count for r in rows]
    nonzero = [c for c in real_counts if c > 0]
    median_nonzero = statistics.median(nonzero) if nonzero else 0
    low_threshold = max(1, median_nonzero * 0.2)  # < 全部非零中位数的 20% 视为异常

    # 按月聚合(真实推文数)
    monthly: Dict[str, List[CoverageRow]] = {}
    for r in rows:
        monthly.setdefault(r.month_key(), []).append(r)
    month_real_totals = {m: sum(r.real_tweet_count for r in rs) for m, rs in monthly.items()}
    month_returned_totals = {m: sum(r.items_returned for r in rs) for m, rs in monthly.items()}
    month_sentinel_totals = {m: sum(r.sentinel_count for r in rs) for m, rs in monthly.items()}
    month_subdivided = {m: any(r.subdivided for r in rs) for m, rs in monthly.items()}

    lines: List[str] = []
    lines.append(f"# coverage report for handle={handle}")
    lines.append(f"# {len(rows)} windows, {len(monthly)} months")
    lines.append(f"# total items_returned:  {sum(r.items_returned for r in rows)}")
    lines.append(f"# total sentinels:       {sum(r.sentinel_count for r in rows)}")
    lines.append(f"# total real tweets:     {sum(real_counts)}")
    lines.append(f"# median non-zero (real): {median_nonzero}")
    lines.append(f"# low-window threshold:  < {low_threshold:.0f}")
    lines.append("")
    lines.append("## per-window")
    lines.append(f"{'window_start':<12} {'window_end':<12} {'returned':>9} {'sentinels':>10} {'real':>5} {'persisted':>10} {'cache':>5} {'subdiv':>6}  {'note'}")
    for r in rows:
        note = (r.note or "")[:30]
        lines.append(
            f"{r.window_start:<12} {r.window_end:<12} "
            f"{r.items_returned:>9} {r.sentinel_count:>10} {r.real_tweet_count:>5} "
            f"{r.items_persisted:>10} "
            f"{'Y' if r.from_cache else 'N':>5} "
            f"{'Y' if r.subdivided else 'N':>6}  {note}"
        )
    lines.append("")
    lines.append("## per-month (histogram, real_tweet_count = returned - sentinels)")
    lines.append(f"{'month':<8} {'real':>6} {'sentinels':>10} {'subdivided':>11}  {'flag'}")
    for m in sorted(monthly):
        real = month_real_totals[m]
        sent = month_sentinel_totals[m]
        sub = "Y" if month_subdivided[m] else "N"
        flag = ""
        if real == 0 and sent == 0:
            flag = "⚠ WARNING: 0 tweets"
        elif real == 0 and sent > 0:
            flag = "○ 哨兵(账户静默期,可能没发推)"
        elif median_nonzero > 0 and real < low_threshold:
            flag = f"⚠ WARNING: < {low_threshold:.0f} (median real tweets)"
        lines.append(f"{m:<8} {real:>6} {sent:>10} {sub:>11}  {flag}")
    return "\n".join(lines)


# ===========================================================================
# 月份切片 + run_input 构造
# ===========================================================================

def _plan_months(months_back: int, skip: Set[str]) -> List[date]:
    """从本月往回数 months_back 个月,跳过 skip 集合里已完成的 YYYY-MM。
    返回早→晚(让 fetch 顺序按时间正向推进)。"""
    today = datetime.now(timezone.utc).date().replace(day=1)
    out: List[date] = []
    for i in range(months_back):
        year = today.year
        month = today.month - i
        while month <= 0:
            month += 12
            year -= 1
        d = date(year, month, 1)
        if d.strftime("%Y-%m") not in skip:
            out.append(d)
    out.reverse()  # 早 → 晚
    return out


def _next_month(d: date) -> date:
    if d.month == 12:
        return date(d.year + 1, 1, 1)
    return date(d.year, d.month + 1, 1)


def _mid_date(start: date, end: date) -> date:
    """返回 (start, end) 的中点(向下取整到天)。"""
    delta_days = (end - start).days
    return start + timedelta(days=delta_days // 2)


def build_run_input(
    handle: str,
    start: date,
    end: date,
    max_per_month: Optional[int] = None,
    sort: str = "Latest",
    disable_maximization: bool = True,
) -> dict:
    """构造 actor run input,完全照用户在控制台验证过的样例 + 时间窗。

    时间窗用 Twitter 高级搜索语法(since/until)嵌在 searchTerms 里。

    ⚠️ 2026-06-12 坑总结(见 tests/test_pagination_modes.py 基准测试):
      - sort=Latest 不设 disableMaximization:actor 会自己 maximize,但行为
        **非确定性** (同输入 393/60 两次差 5x)。首次重抓 2025-11 返 393,
        第二次 60。**不可用**。
      - sort=Top + maxItems=3000:actor 跑 6 页就停 (返 93)。**截断**。
      - sort=Latest + disableMaximization=true + maxItems=3000:稳定返 ~381
        (跟 393 差 12 是边界推文 published_at 跨月)。**采用这个**。
    disable_maximization=True 强制 actor 显式分页(每页 20),直到 maxItems
    触发 cap 或 Twitter 返 0。
    """
    return {
        "customMapFunction": "(object) => { return {...object} }",
        "includeSearchTerms": False,
        "maxItems": max_per_month or DEFAULT_MAX_PER_MONTH,
        "onlyImage": False,
        "onlyQuote": False,
        "onlyTwitterBlue": False,
        "onlyVerifiedUsers": False,
        "onlyVideo": False,
        "searchTerms": [
            f"from:{handle} since:{start.isoformat()} until:{end.isoformat()}"
        ],
        "sort": sort,
        "disableMaximization": disable_maximization,
    }


# ===========================================================================
# Apify 调用
# ===========================================================================

def _call_actor(
    run_input: dict,
    token: str,
    client: Any = None,
    *,
    max_retries: int = 3,
    backoff_base: float = 2.0,
) -> List[dict]:
    """同步调 actor + 拉 dataset items,带 429/5xx 指数退避重试。

    apify-client 本身已自动重试 8 次(指数退避),这里再加一道保险。
    """
    if client is None:
        from apify_client import ApifyClient
        client = ApifyClient(token)

    last_exc: Optional[Exception] = None
    for attempt in range(1, max_retries + 1):
        try:
            run = client.actor(ACTOR_ID).call(run_input=run_input)
            # 兼容:apify-client 3.x 返回 pydantic Run,测试 fake client 可能返回 dict
            if hasattr(run, "get"):
                dataset_id = run.get("defaultDatasetId") or run.get("default_dataset_id")
            else:
                dataset_id = (
                    getattr(run, "default_dataset_id", None)
                    or getattr(run, "defaultDatasetId", None)
                )
            if not dataset_id:
                log.warning("actor run returned no defaultDatasetId: %s", run)
                return []
            items: List[dict] = []
            for item in client.dataset(dataset_id).iterate_items():
                items.append(item)
            return items
        except Exception as e:
            last_exc = e
            sleep_s = backoff_base ** attempt
            log.warning(
                "actor call failed (attempt %d/%d): %s; sleeping %.1fs",
                attempt, max_retries, e, sleep_s,
            )
            if attempt < max_retries:
                time.sleep(sleep_s)
    assert last_exc is not None
    raise last_exc


# ===========================================================================
# item → RawPost
# ===========================================================================

def _item_to_raw_post(
    item: dict,
    field_map: FieldMap,
    source_id: str,
    captured_at: str,
) -> RawPost:
    # apidojo tweet-scraper V2 会返 `{"noResults": true}` 当子窗口无推文时
    # (Phase 1 真实运行已验证,见 fixtures/tweet_response_sample.json 旁注)
    # 这种"哨兵对象"必须静默跳过(不算 parse 错误)
    if not isinstance(item, dict) or item.get("noResults") is True:
        raise _NoTweetSentinel(f"item is a noResults sentinel or non-dict: {item!r}")

    extracted = field_map.extract(item)
    post_id = str(extracted.get("post_id") or "").strip()
    raw_text = (extracted.get("raw_text") or "").strip()
    raw_url = (extracted.get("raw_url") or "").strip()
    published_at = to_utc_iso(extracted.get("published_at"))
    # ⚠️ 保险:缺 createdAt 不静默 fallback 到 captured_at(那是抓取时间,不是推文时间)
    # 验证层(P3-2)用 published_at 算 entry_date,塞进 captured_at 会导致未来增量抓取时
    # 整条预测错位。所以缺时间 → WARNING 日志 + 留空,让验证层跳过,绝不用处理时间冒充。
    if not published_at:
        log.warning(
            "scraper missing publish time: post_id=%s source=%s — published_at 留空,不入 future_time 路径",
            post_id or "<no_post_id>", source_id,
        )
        # published_at 保持空字符串

    if not post_id or not raw_text:
        raise ValueError(f"missing post_id ({post_id!r}) or raw_text (empty)")

    return RawPost(
        post_id=post_id,
        source_id=source_id,
        platform=Platform.TWITTER.value,
        published_at=published_at,  # 缺时为 ""(验证层会跳过,见 phase3 verification)
        captured_at=captured_at,
        raw_text=raw_text,
        raw_url=raw_url,
        raw_json=json.dumps(item, ensure_ascii=False),
    )


class _NoTweetSentinel(Exception):
    """内部 sentinel:item 是 actor 的 noResults 哨兵,调用者应静默跳过。"""


# ===========================================================================
# 递归窗口抓取(带截断检测 + 二分细分)
# ===========================================================================

@dataclass
class WindowResult:
    """单个窗口的抓取结果。"""
    window_start: date
    window_end: date
    items_returned: int
    items_persisted: int
    from_cache: bool
    subdivided: bool
    depth: int
    posts: List[RawPost] = field(default_factory=list)
    errors: List[dict] = field(default_factory=list)


def _fetch_window(
    handle: str,
    db_path: DbPath,
    start: date,
    end: date,
    max_per_month: int,
    cache: ResponseCache,
    field_map: FieldMap,
    *,
    apify_token: Optional[str] = None,
    apify_client: Any = None,
    captured_at: str,
    source_id: str,
    depth: int = 0,
) -> WindowResult:
    """递归抓取 [start, end) 窗口的推文,触发截断时二分。

    截断判定:`len(items_returned) >= max_per_month`(恰好打满)。
    """
    # 终止:窗口 < 1 天,不再细分
    if (end - start).days < 1:
        log.error("window [%s, %s) is < 1 day at depth=%d; cannot subdivide further", start, end, depth)
        # 仍要入库已抓到的
        items: List[dict] = []
        return WindowResult(
            window_start=start, window_end=end,
            items_returned=0, items_persisted=0,
            from_cache=False, subdivided=False, depth=depth,
            posts=[],
        )

    run_input = build_run_input(handle, start, end, max_per_month)
    cached_payload = cache.get(run_input)
    if cached_payload is not None:
        items = cached_payload.get("items", [])
        from_cache = True
    else:
        from_cache = False
        if apify_client is not None:
            items = _call_actor(run_input, "", client=apify_client)
        else:
            items = _call_actor(run_input, apify_token)  # type: ignore[arg-type]
        cache.put(run_input, {"items": items, "run_input": run_input})

    log.info(
        "window=[%s, %s) items=%d (cache=%s, depth=%d, max=%d)",
        start, end, len(items), from_cache, depth, max_per_month,
    )

    # 截断检测
    truncated = len(items) >= max_per_month
    if truncated and depth < MAX_SUBDIVISION_DEPTH:
        log.warning(
            "⚠ window [%s, %s) hit maxItems=%d → subdividing (depth %d → %d)",
            start, end, max_per_month, depth, depth + 1,
        )
        mid = _mid_date(start, end)
        # 先记父窗口 subdivided=1(items_returned 是父窗口观测值,sentinel_count 算实际哨兵数)
        _sentinels = sum(1 for it in items if isinstance(it, dict) and it.get('noResults') is True)
        record_coverage(
            handle, db_path,
            window_start=start, window_end=end,
            items_returned=len(items), items_persisted=0,
            from_cache=from_cache, subdivided=True, depth=depth,
            sentinel_count=_sentinels,
        )
        left = _fetch_window(
            handle, db_path, start, mid, max_per_month, cache, field_map,
            apify_token=apify_token, apify_client=apify_client,
            captured_at=captured_at, source_id=source_id, depth=depth + 1,
        )
        right = _fetch_window(
            handle, db_path, mid, end, max_per_month, cache, field_map,
            apify_token=apify_token, apify_client=apify_client,
            captured_at=captured_at, source_id=source_id, depth=depth + 1,
        )
        return WindowResult(
            window_start=start, window_end=end,
            items_returned=len(items),
            items_persisted=left.items_persisted + right.items_persisted,
            from_cache=from_cache, subdivided=True, depth=depth,
            posts=left.posts + right.posts,
            errors=left.errors + right.errors,
        )

    if truncated:
        # 已达 max_depth 还截断 → 警告
        log.error(
            "⚠ window [%s, %s) STILL truncated at max_depth=%d, items=%d; 人工介入",
            start, end, MAX_SUBDIVISION_DEPTH, len(items),
        )

    # 不截断(或不细分了),入库
    posts: List[RawPost] = []
    errors: List[dict] = []
    for item in items:
        try:
            post = _item_to_raw_post(item, field_map, source_id, captured_at)
        except _NoTweetSentinel:
            # actor 返的 noResults 哨兵对象,静默跳过(不计入 errors)
            continue
        except Exception as e:
            log.warning("parse item failed: %s; item_keys=%s", e, list(item.keys()) if isinstance(item, dict) else type(item))
            errors.append({"phase": "parse", "error": str(e)})
            continue
        try:
            upsert_raw_post(post, db_path)
            posts.append(post)
        except Exception as e:
            log.warning("upsert failed for post_id=%s: %s", post.post_id, e)
            errors.append({"phase": "upsert", "post_id": post.post_id, "error": str(e)})

    _sentinels = sum(1 for it in items if isinstance(it, dict) and it.get('noResults') is True)
    record_coverage(
        handle, db_path,
        window_start=start, window_end=end,
        items_returned=len(items), items_persisted=len(posts),
        from_cache=from_cache, subdivided=False, depth=depth,
        sentinel_count=_sentinels,
    )

    return WindowResult(
        window_start=start, window_end=end,
        items_returned=len(items), items_persisted=len(posts),
        from_cache=from_cache, subdivided=False, depth=depth,
        posts=posts, errors=errors,
    )


# ===========================================================================
# 主流程
# ===========================================================================

@dataclass
class FetchSummary:
    handle: str
    months_planned: List[str]
    months_done: List[str]
    months_skipped: List[str] = field(default_factory=list)
    runs: List[dict] = field(default_factory=list)
    errors: List[dict] = field(default_factory=list)
    total_scraped: int = 0
    interrupted_at: Optional[str] = None
    windows_subdivided: int = 0

    def to_dict(self) -> dict:
        return asdict(self)


def fetch_account_history(
    handle: str,
    db_path: DbPath = DEFAULT_DB_PATH,
    *,
    max_per_month: Optional[int] = None,
    months_back: int = 12,
    cache_dir: Union[str, Path] = DEFAULT_CACHE_DIR,
    use_cache: bool = True,
    field_map: Optional[FieldMap] = None,
    apify_token: Optional[str] = None,
    apify_client: Any = None,
) -> FetchSummary:
    """拉一个 handle 的所有推文,按月切片 + 截断时二分细分,逐条 upsert。

    进度通过 scrape_state 表追踪:已完成的"月份"会跳过,断点续抓安全。
    但 coverage 表记录每次窗口(细到天),不参与跳过逻辑 —— 即细分后
    子窗口不需要在 scrape_state 登记,父月份登记后整月就跳过了。

    Args:
        handle: 推特 handle(不带 @)
        db_path: SQLite 路径
        max_per_month: 每月 actor run 的最大条数(默认 3000,目标全量)
        months_back: 往回抓几个月
        cache_dir: 本地响应缓存目录
        use_cache: True 时相同 run_input 不会重复调 API
        field_map: 字段映射,默认用 default_field_map()
        apify_token: 覆盖 APIFY_TOKEN 环境变量
        apify_client: 测试时注入 mock client
    """
    init_db(db_path)
    init_scrape_state(db_path)

    if apify_client is None:
        apify_token = apify_token or os.environ.get(ENV_API_TOKEN)
        if not apify_token:
            raise RuntimeError(
                f"set {ENV_API_TOKEN} env var, pass apify_token=, or apify_client="
            )

    field_map = field_map or default_field_map()
    cache = ResponseCache(cache_dir, enabled=use_cache)
    source_id = f"tw_{handle}"
    captured_at = datetime.now(timezone.utc).isoformat()

    state = get_scrape_state(handle, db_path)
    months_done: Set[str] = set(state["months_done"])
    total_scraped = state["total_scraped"]

    months_to_fetch = _plan_months(months_back, skip=months_done)
    summary = FetchSummary(
        handle=handle,
        months_planned=[m.strftime("%Y-%m") for m in months_to_fetch],
        months_done=sorted(months_done),
        total_scraped=total_scraped,
    )

    if not months_to_fetch:
        log.info("handle=%s: nothing to do, all %d months already done", handle, len(months_done))
        return summary

    for month_start in months_to_fetch:
        month_end = _next_month(month_start)
        month_key = month_start.strftime("%Y-%m")

        # 抓这个月(可能细分)
        try:
            result = _fetch_window(
                handle, db_path,
                start=month_start, end=month_end,
                max_per_month=max_per_month or DEFAULT_MAX_PER_MONTH,
                cache=cache, field_map=field_map,
                apify_token=apify_token, apify_client=apify_client,
                captured_at=captured_at, source_id=source_id,
                depth=0,
            )
        except KeyboardInterrupt:
            log.info("interrupted at month %s; 已完成的窗口已写盘", month_key)
            summary.interrupted_at = month_key
            break
        except Exception as e:
            log.error("month %s failed: %s", month_key, e)
            summary.errors.append({"phase": "run", "month": month_key, "error": str(e)})
            continue

        summary.runs.append({
            "month": month_key,
            "items_returned": result.items_returned,
            "items_persisted": result.items_persisted,
            "from_cache": result.from_cache,
            "subdivided": result.subdivided,
            "depth": result.depth,
        })
        if result.subdivided:
            summary.windows_subdivided += 1
        summary.errors.extend(result.errors)

        # 即使没新抓到(可能整月都空)也标记完成
        months_done.add(month_key)
        total_scraped += result.items_persisted
        try:
            update_scrape_state(
                handle, db_path,
                month=month_key,
                total_scraped=total_scraped,
            )
        except Exception as e:
            log.warning("scrape_state update failed: %s", e)

        summary.total_scraped = total_scraped
        summary.months_done = sorted(months_done)
        log.info(
            "handle=%s month=%s persisted=%d (subdivided=%s)",
            handle, month_key, result.items_persisted, result.subdivided,
        )

    return summary


# ===========================================================================
# CLI
# ===========================================================================

def _record_fixture(
    handle: str,
    db_path: DbPath,
    n: int,
    out_path: Path,
    apify_client: Any = None,
) -> int:
    if apify_client is None:
        token = os.environ.get(ENV_API_TOKEN)
        if not token:
            raise SystemExit(f"need {ENV_API_TOKEN} env var to record")
    init_db(db_path)
    init_scrape_state(db_path)

    today = datetime.now(timezone.utc).date().replace(day=1)
    last_month_start = date(today.year, today.month - 1, 1) if today.month > 1 else date(today.year - 1, 12, 1)
    last_month_end = today
    run_input = build_run_input(handle, last_month_start, last_month_end, max_per_month=n)

    if apify_client is not None:
        items = _call_actor(run_input, "", client=apify_client)
    else:
        items = _call_actor(run_input, token)  # type: ignore[arg-type]

    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(
        json.dumps({"run_input": run_input, "items": items}, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    print(f"recorded {len(items)} items to {out_path}")
    if items:
        sample = items[0]
        if isinstance(sample, dict):
            print("first item keys:", list(sample.keys()))
    print()
    print("Next:校准 default_field_map() 里的字段名(如果解析报错)。")
    print("用 fixtures/tweet_response_sample.json 跑 mock 测试:")
    print("  python tests/test_scraper.py")
    return 0


def _build_scrape_parser() -> "argparse.ArgumentParser":
    import argparse
    p = argparse.ArgumentParser(
        prog="python -m signalboard.scraper scrape",
        description="Apify apidojo/tweet-scraper → raw_posts(按月切片 + 截断细分 + 断点续抓 + 缓存)",
    )
    p.add_argument("--handle", required=True, help="twitter handle,不要带 @")
    p.add_argument("--db", default=DEFAULT_DB_PATH, help="SQLite 路径")
    p.add_argument(
        "--max-per-month", type=int, default=DEFAULT_MAX_PER_MONTH,
        help=f"每月 actor run 的最大条数(默认 {DEFAULT_MAX_PER_MONTH},Apify 按条计费;触顶会自动二分细分)",
    )
    p.add_argument("--months-back", type=int, default=12, help="往回抓几个月")
    p.add_argument("--cache-dir", default=DEFAULT_CACHE_DIR, help="本地响应缓存目录")
    p.add_argument("--no-cache", action="store_true", help="跳过本地响应缓存,直接调 API")
    p.add_argument(
        "--record", type=int, metavar="N", default=0,
        help="只拉 N 条真实响应写到 fixtures/,不写 db(会扣费)",
    )
    p.add_argument("--fixtures-dir", default="fixtures", help="--record 写到哪里")
    p.add_argument("--verbose", "-v", action="store_true")
    return p


def _build_coverage_parser() -> "argparse.ArgumentParser":
    import argparse
    p = argparse.ArgumentParser(
        prog="python -m signalboard.scraper coverage",
        description="打印某 handle 的覆盖率报告(per-window + per-month histogram + 异常低警告)",
    )
    p.add_argument("--handle", required=True)
    p.add_argument("--db", default=DEFAULT_DB_PATH)
    return p


def _cmd_scrape(args) -> int:
    logging.basicConfig(
        level=logging.DEBUG if args.verbose else logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    )

    if args.record:
        out = Path(args.fixtures_dir) / "tweet_response_sample.json"
        return _record_fixture(
            handle=args.handle,
            db_path=args.db,
            n=args.record,
            out_path=out,
        )

    summary = fetch_account_history(
        handle=args.handle,
        db_path=args.db,
        max_per_month=args.max_per_month,
        months_back=args.months_back,
        cache_dir=args.cache_dir,
        use_cache=not args.no_cache,
    )
    print(json.dumps(summary.to_dict(), indent=2, ensure_ascii=False, default=str))
    # 顺手打印覆盖率报告
    print()
    print(format_coverage_report(args.handle, args.db))
    return 0


def _cmd_coverage(args) -> int:
    print(format_coverage_report(args.handle, args.db))
    return 0


def main(argv: Optional[Sequence[str]] = None) -> int:
    """CLI 入口。两种调用方式都支持:
    - 老形式:python -m signalboard.scraper --handle X ...
    - subcommand:python -m signalboard.scraper coverage --handle X
    """
    import argparse

    if argv is None:
        argv = sys.argv[1:]

    # 优先识别 subcommand / coverage flag
    has_coverage_flag = "--coverage-report" in argv
    if has_coverage_flag:
        argv = [a for a in argv if a != "--coverage-report"]
        cov_args = _build_coverage_parser().parse_args(argv)
        return _cmd_coverage(cov_args)

    if argv and argv[0] == "coverage":
        cov_args = _build_coverage_parser().parse_args(argv[1:])
        return _cmd_coverage(cov_args)

    if argv and argv[0] == "scrape":
        scrape_args = _build_scrape_parser().parse_args(argv[1:])
        return _cmd_scrape(scrape_args)

    # 老形式:直接 scrape 参数
    scrape_args = _build_scrape_parser().parse_args(argv)
    return _cmd_scrape(scrape_args)


if __name__ == "__main__":
    import sys
    sys.exit(main())
