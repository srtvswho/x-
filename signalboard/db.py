"""SQLite 连接 + schema 管理 + 版本迁移。

Schema 版本:
    v1 (deprecated): predictions 自带 raw_text/raw_url/archive_url,无 post_id,无 raw_posts 表
    v2 (current)   : 拆出 raw_posts;predictions.post_id 外键 + UNIQUE(post_id, ticker, direction)
    v3 (2026-06-12): predictions 加 6 列(LLM 抽取层产出可追溯)
                      + 4 个新表:post_flags / aliases / human_review_queue / extraction_cache

init_db() 幂等且自适配:
- 全新库 → 直接建 v3
- v1 库(有 raw_text 列) → v1→v2→v3,数据不丢
- v2 库 → v2→v3(ALTER TABLE + 建新表)
- 已是 v3 → noop
"""
from __future__ import annotations

import hashlib
import sqlite3
from contextlib import contextmanager
from pathlib import Path
from typing import Iterator, Union

DbPath = Union[str, Path]

CURRENT_SCHEMA_VERSION = 3


# ---------------------------------------------------------------------------
# 自定义 SQLite 函数(SQLite 默认没 sha256)
# ---------------------------------------------------------------------------

def _sql_sha256(s) -> str:
    if isinstance(s, str):
        s = s.encode("utf-8")
    return hashlib.sha256(s).hexdigest()


def _register_extensions(conn: sqlite3.Connection) -> None:
    conn.create_function("sha256", 1, _sql_sha256)


# ---------------------------------------------------------------------------
# v2 schema (current)
# ---------------------------------------------------------------------------

V2_SCHEMA_SQL = """
CREATE TABLE IF NOT EXISTS raw_posts (
    post_id        TEXT PRIMARY KEY,
    source_id      TEXT    NOT NULL,
    platform       TEXT    NOT NULL,
    published_at   TEXT    NOT NULL,
    captured_at    TEXT    NOT NULL,
    raw_text       TEXT    NOT NULL,
    raw_url        TEXT    NOT NULL,
    raw_json       TEXT,
    content_hash   TEXT    NOT NULL,
    is_deleted     INTEGER NOT NULL DEFAULT 0,
    archive_url    TEXT
);

CREATE INDEX IF NOT EXISTS idx_raw_posts_source_id     ON raw_posts(source_id);
CREATE INDEX IF NOT EXISTS idx_raw_posts_platform      ON raw_posts(platform);
CREATE INDEX IF NOT EXISTS idx_raw_posts_published_at  ON raw_posts(published_at);
CREATE INDEX IF NOT EXISTS idx_raw_posts_content_hash  ON raw_posts(content_hash);

CREATE TABLE IF NOT EXISTS predictions (
    prediction_id      TEXT PRIMARY KEY,
    post_id            TEXT    NOT NULL,
    source_id          TEXT    NOT NULL,
    published_at       TEXT    NOT NULL,
    captured_at        TEXT    NOT NULL,
    ticker             TEXT    NOT NULL,
    market             TEXT    NOT NULL,
    direction          TEXT    NOT NULL,
    claim_type         TEXT    NOT NULL,
    quantitative_claim TEXT,
    horizon            TEXT    NOT NULL,
    conviction         INTEGER NOT NULL CHECK (conviction BETWEEN 1 AND 5),
    is_repeat_call     INTEGER NOT NULL DEFAULT 0,
    repeat_of          TEXT,
    thesis_summary     TEXT    NOT NULL,
    thesis_category    TEXT    NOT NULL,
    created_at         TEXT    NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ', 'now')),
    UNIQUE(post_id, ticker, direction),
    FOREIGN KEY (post_id) REFERENCES raw_posts(post_id) ON DELETE RESTRICT
);

CREATE INDEX IF NOT EXISTS idx_predictions_post_id       ON predictions(post_id);
CREATE INDEX IF NOT EXISTS idx_predictions_source_id     ON predictions(source_id);
CREATE INDEX IF NOT EXISTS idx_predictions_ticker        ON predictions(ticker);
CREATE INDEX IF NOT EXISTS idx_predictions_market        ON predictions(market);
CREATE INDEX IF NOT EXISTS idx_predictions_published_at  ON predictions(published_at);
CREATE INDEX IF NOT EXISTS idx_predictions_captured_at   ON predictions(captured_at);

CREATE TABLE IF NOT EXISTS verifications (
    prediction_id         TEXT PRIMARY KEY,
    status                TEXT    NOT NULL DEFAULT 'pending',
    price_returns         TEXT,
    entry_price_basis     TEXT    NOT NULL,
    quantitative_outcome  TEXT,
    verified_at           TEXT,
    FOREIGN KEY (prediction_id) REFERENCES predictions(prediction_id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_verifications_status ON verifications(status);


-- v3 增量(2026-06-12,LLM 抽取层上线):predictions 加 6 列 + 4 个新表
"""


# ---------------------------------------------------------------------------
# ---------------------------------------------------------------------------
# v3 迁移 SQL
# ---------------------------------------------------------------------------
# v3(2026-06-12,LLM 抽取层上线):
#   - predictions 加 6 列
#   - 新建 4 个表:post_flags / aliases / human_review_queue / extraction_cache
# 这是 idempotent 迁移,对全新库也安全(老库 ADD COLUMN IF NOT EXISTS 用 PRAGMA 探测)。
# ---------------------------------------------------------------------------

V3_NEW_TABLES_SQL = """
-- 索引(给已加的列)
CREATE INDEX IF NOT EXISTS idx_predictions_resolution ON predictions(resolution_status);
CREATE INDEX IF NOT EXISTS idx_predictions_prompt     ON predictions(prompt_version);

-- post_flags:帖子级行为标记(R12,counter 风格)
CREATE TABLE IF NOT EXISTS post_flags (
    post_id        TEXT    NOT NULL,
    flag_type      TEXT    NOT NULL,                       -- self_reported_returns / victory_lap / position_disclosure / influence_milestone / solicitation / prefilter_skipped / context_missing
    count          INTEGER NOT NULL DEFAULT 1,             -- 多处出现时累加
    evidence       TEXT,                                    -- 触发该 flag 的原文片段
    created_at     TEXT    NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ', 'now')),
    PRIMARY KEY (post_id, flag_type)
);
CREATE INDEX IF NOT EXISTS idx_post_flags_type      ON post_flags(flag_type);
CREATE INDEX IF NOT EXISTS idx_post_flags_post_id   ON post_flags(post_id);

-- aliases:raw_asset_mention → (ticker, market) 别名表(R10,LLM 不参与解析)
CREATE TABLE IF NOT EXISTS aliases (
    alias_raw        TEXT    NOT NULL,                      -- 原文写法
    ticker           TEXT    NOT NULL,
    market           TEXT    NOT NULL,
    asset_class      TEXT    NOT NULL DEFAULT 'equity',
    locale           TEXT,
    source           TEXT,
    confidence       REAL    NOT NULL DEFAULT 1.0,
    notes            TEXT,
    created_at       TEXT    NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ', 'now')),
    PRIMARY KEY (alias_raw, ticker, market)
);
CREATE INDEX IF NOT EXISTS idx_aliases_ticker ON aliases(ticker);

-- human_review_queue:LLM 解析失败/不确定时进人工队列
CREATE TABLE IF NOT EXISTS human_review_queue (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    post_id         TEXT    NOT NULL,
    reason          TEXT    NOT NULL,
    payload         TEXT    NOT NULL,
    created_at      TEXT    NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ', 'now')),
    resolved_at     TEXT,
    resolved_by     TEXT,
    resolution      TEXT
);
CREATE INDEX IF NOT EXISTS idx_hrq_post_id  ON human_review_queue(post_id);
CREATE INDEX IF NOT EXISTS idx_hrq_reason    ON human_review_queue(reason);
CREATE INDEX IF NOT EXISTS idx_hrq_unresolved ON human_review_queue(resolved_at) WHERE resolved_at IS NULL;

-- extraction_cache:LLM 响应缓存(按 post_id + prompt_version)
CREATE TABLE IF NOT EXISTS extraction_cache (
    post_id         TEXT    NOT NULL,
    prompt_version  TEXT    NOT NULL,
    model           TEXT    NOT NULL,
    response_json   TEXT    NOT NULL,
    input_hash      TEXT    NOT NULL,
    created_at      TEXT    NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ', 'now')),
    PRIMARY KEY (post_id, prompt_version)
);
CREATE INDEX IF NOT EXISTS idx_extraction_cache_post ON extraction_cache(post_id);
"""


def _migrate_v2_to_v3(conn: sqlite3.Connection) -> None:
    """对已有 v2 库:加 6 列(predictions)+ 建 4 个新表(都 IF NOT EXISTS)。

    ALTER 单独跑(逐列判断是否已存在),4 个新表 IF NOT EXISTS 一把梭。
    重复跑幂等(列已存在就跳过)。
    """
    cur = conn.execute("PRAGMA table_info(predictions)")
    cols = {row[1] for row in cur.fetchall()}
    additions = []
    if "raw_asset_mention" not in cols:
        additions.append("ALTER TABLE predictions ADD COLUMN raw_asset_mention  TEXT")
    if "resolution_status" not in cols:
        additions.append("ALTER TABLE predictions ADD COLUMN resolution_status   TEXT    NOT NULL DEFAULT 'resolved'")
    if "context_tickers" not in cols:
        additions.append("ALTER TABLE predictions ADD COLUMN context_tickers     TEXT")
    if "hedged" not in cols:
        additions.append("ALTER TABLE predictions ADD COLUMN hedged              INTEGER NOT NULL DEFAULT 0")
    if "prompt_version" not in cols:
        additions.append("ALTER TABLE predictions ADD COLUMN prompt_version      TEXT")
    if "extraction_notes" not in cols:
        additions.append("ALTER TABLE predictions ADD COLUMN extraction_notes    TEXT")
    for stmt in additions:
        conn.execute(stmt)
    # 4 个新表 + 索引(IF NOT EXISTS,重复跑安全)
    conn.executescript(V3_NEW_TABLES_SQL)





def _migrate_v2_to_v3(conn: sqlite3.Connection) -> None:
    """对已有 v2 库:加 6 列(predictions)+ 建 4 个新表(都 IF NOT EXISTS)。"""
    cur = conn.execute("PRAGMA table_info(predictions)")
    cols = {row[1] for row in cur.fetchall()}
    additions = []
    if "raw_asset_mention" not in cols:
        additions.append("ALTER TABLE predictions ADD COLUMN raw_asset_mention  TEXT")
    if "resolution_status" not in cols:
        additions.append("ALTER TABLE predictions ADD COLUMN resolution_status   TEXT    NOT NULL DEFAULT 'resolved'")
    if "context_tickers" not in cols:
        additions.append("ALTER TABLE predictions ADD COLUMN context_tickers     TEXT")
    if "hedged" not in cols:
        additions.append("ALTER TABLE predictions ADD COLUMN hedged              INTEGER NOT NULL DEFAULT 0")
    if "prompt_version" not in cols:
        additions.append("ALTER TABLE predictions ADD COLUMN prompt_version      TEXT")
    if "extraction_notes" not in cols:
        additions.append("ALTER TABLE predictions ADD COLUMN extraction_notes    TEXT")
    for stmt in additions:
        conn.execute(stmt)
    # 新表 4 个(IF NOT EXISTS,重复跑也安全)
    conn.executescript(V3_NEW_TABLES_SQL)

# v1 schema (仅供测试和迁移用,代码层不应再生成)
# ---------------------------------------------------------------------------

LEGACY_V1_SCHEMA_SQL = """
CREATE TABLE IF NOT EXISTS predictions (
    prediction_id     TEXT PRIMARY KEY,
    source_id         TEXT    NOT NULL,
    published_at      TEXT    NOT NULL,
    captured_at       TEXT    NOT NULL,
    raw_url           TEXT    NOT NULL,
    raw_text          TEXT    NOT NULL,
    archive_url       TEXT,
    is_deleted        INTEGER NOT NULL DEFAULT 0,
    ticker            TEXT    NOT NULL,
    market            TEXT    NOT NULL,
    direction         TEXT    NOT NULL,
    claim_type        TEXT    NOT NULL,
    quantitative_claim TEXT,
    horizon           TEXT    NOT NULL,
    conviction        INTEGER NOT NULL CHECK (conviction BETWEEN 1 AND 5),
    is_repeat_call    INTEGER NOT NULL DEFAULT 0,
    repeat_of         TEXT,
    thesis_summary    TEXT    NOT NULL,
    thesis_category   TEXT    NOT NULL,
    created_at        TEXT    NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ', 'now'))
);

CREATE INDEX IF NOT EXISTS idx_predictions_source_id    ON predictions(source_id);
CREATE INDEX IF NOT EXISTS idx_predictions_ticker       ON predictions(ticker);
CREATE INDEX IF NOT EXISTS idx_predictions_market       ON predictions(market);
CREATE INDEX IF NOT EXISTS idx_predictions_published_at ON predictions(published_at);
CREATE INDEX IF NOT EXISTS idx_predictions_captured_at  ON predictions(captured_at);
"""


# ---------------------------------------------------------------------------
# v1 → v2 迁移 SQL
# ---------------------------------------------------------------------------
# 步骤:
#   1. 建 raw_posts 表(若不存在),把旧 predictions 的 raw_text/raw_url/archive_url
#      灌进去,post_id 临时用 prediction_id 兼(旧库无独立 post_id)
#   2. 重建 predictions:加 post_id 外键 + UNIQUE(post_id, ticker, direction);
#      去掉 raw_text/raw_url/archive_url/is_deleted
#   3. 重建索引

_MIGRATE_V1_TO_V2_SQL = """
-- 1. 建 raw_posts
CREATE TABLE IF NOT EXISTS raw_posts (
    post_id        TEXT PRIMARY KEY,
    source_id      TEXT    NOT NULL,
    platform       TEXT    NOT NULL,
    published_at   TEXT    NOT NULL,
    captured_at    TEXT    NOT NULL,
    raw_text       TEXT    NOT NULL,
    raw_url        TEXT    NOT NULL,
    raw_json       TEXT,
    content_hash   TEXT    NOT NULL,
    is_deleted     INTEGER NOT NULL DEFAULT 0,
    archive_url    TEXT
);

-- 2. 把旧 predictions 的原文抽出来塞进 raw_posts
INSERT OR IGNORE INTO raw_posts (
    post_id, source_id, platform, published_at, captured_at,
    raw_text, raw_url, raw_json, content_hash, is_deleted, archive_url
)
SELECT
    prediction_id,
    source_id,
    'unknown',                                       -- 旧库没记 platform,占位
    published_at,
    captured_at,
    raw_text,
    raw_url,
    NULL,                                            -- 旧库没存 raw_json
    sha256(raw_text),
    is_deleted,
    archive_url
FROM predictions;

-- 3. 重建 predictions
CREATE TABLE predictions_new (
    prediction_id      TEXT PRIMARY KEY,
    post_id            TEXT    NOT NULL,
    source_id          TEXT    NOT NULL,
    published_at       TEXT    NOT NULL,
    captured_at        TEXT    NOT NULL,
    ticker             TEXT    NOT NULL,
    market             TEXT    NOT NULL,
    direction          TEXT    NOT NULL,
    claim_type         TEXT    NOT NULL,
    quantitative_claim TEXT,
    horizon            TEXT    NOT NULL,
    conviction         INTEGER NOT NULL CHECK (conviction BETWEEN 1 AND 5),
    is_repeat_call     INTEGER NOT NULL DEFAULT 0,
    repeat_of          TEXT,
    thesis_summary     TEXT    NOT NULL,
    thesis_category    TEXT    NOT NULL,
    created_at         TEXT    NOT NULL,
    UNIQUE(post_id, ticker, direction),
    FOREIGN KEY (post_id) REFERENCES raw_posts(post_id) ON DELETE RESTRICT
);

INSERT INTO predictions_new (
    prediction_id, post_id, source_id, published_at, captured_at,
    ticker, market, direction, claim_type, quantitative_claim,
    horizon, conviction, is_repeat_call, repeat_of,
    thesis_summary, thesis_category, created_at
)
SELECT
    prediction_id,
    prediction_id,                  -- 迁移时 post_id 兼用 prediction_id
    source_id,
    published_at,
    captured_at,
    ticker,
    market,
    direction,
    claim_type,
    quantitative_claim,
    horizon,
    conviction,
    is_repeat_call,
    repeat_of,
    thesis_summary,
    thesis_category,
    created_at
FROM predictions;

DROP TABLE predictions;
ALTER TABLE predictions_new RENAME TO predictions;

-- 4. 重建索引
CREATE INDEX IF NOT EXISTS idx_predictions_post_id       ON predictions(post_id);
CREATE INDEX IF NOT EXISTS idx_predictions_source_id     ON predictions(source_id);
CREATE INDEX IF NOT EXISTS idx_predictions_ticker        ON predictions(ticker);
CREATE INDEX IF NOT EXISTS idx_predictions_market        ON predictions(market);
CREATE INDEX IF NOT EXISTS idx_predictions_published_at  ON predictions(published_at);
CREATE INDEX IF NOT EXISTS idx_predictions_captured_at   ON predictions(captured_at);

CREATE INDEX IF NOT EXISTS idx_raw_posts_source_id     ON raw_posts(source_id);
CREATE INDEX IF NOT EXISTS idx_raw_posts_platform      ON raw_posts(platform);
CREATE INDEX IF NOT EXISTS idx_raw_posts_published_at  ON raw_posts(published_at);
CREATE INDEX IF NOT EXISTS idx_raw_posts_content_hash  ON raw_posts(content_hash);
"""


# ---------------------------------------------------------------------------
# API
# ---------------------------------------------------------------------------

def init_db(db_path: DbPath) -> None:
    """建表(若不存在)+ 必要时的迁移。幂等,可重复调用。"""
    path = Path(db_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(path)
    try:
        _register_extensions(conn)
        _ensure_schema(conn)
        conn.commit()
    finally:
        conn.close()


def _ensure_schema(conn: sqlite3.Connection) -> None:
    _register_extensions(conn)
    version = conn.execute("PRAGMA user_version").fetchone()[0]
    if version >= CURRENT_SCHEMA_VERSION:
        return

    cur = conn.execute(
        "SELECT name FROM sqlite_master WHERE type='table' AND name='predictions'"
    )
    predictions_exists = cur.fetchone() is not None

    if not predictions_exists:
        # 全新库:直接 v2(包含 6 列+4 表)→ 再加 v3 增量
        conn.executescript(V2_SCHEMA_SQL)
        _migrate_v2_to_v3(conn)
    else:
        cols = {
            row[1]
            for row in conn.execute("PRAGMA table_info(predictions)").fetchall()
        }
        if "raw_text" in cols:
            # v1 库:v1→v2
            conn.executescript(_MIGRATE_V1_TO_V2_SQL)
        # v1 库迁移后是 v2,继续走 v2→v3
        # 已是 v2 库也走 v2→v3(只 ADD 缺失列+建缺失表)
        _migrate_v2_to_v3(conn)

    conn.execute(f"PRAGMA user_version = {CURRENT_SCHEMA_VERSION}")


@contextmanager
def get_conn(db_path: DbPath) -> Iterator[sqlite3.Connection]:
    """带 row_factory + 外键的连接上下文,异常自动 rollback。"""
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    _register_extensions(conn)
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()
