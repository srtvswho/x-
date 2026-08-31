"""SQLite 连接 + schema 管理 + 版本迁移。

Schema 版本:
    v1 (deprecated): predictions 自带 raw_text/raw_url/archive_url,无 post_id,无 raw_posts 表
    v2 (current)   : 拆出 raw_posts;predictions.post_id 外键 + UNIQUE(post_id, ticker, direction)
    v3 (2026-06-12): predictions 加 6 列(LLM 抽取层产出可追溯)
                      + 4 个新表:post_flags / aliases / human_review_queue / extraction_cache
    v4 (2026-08-30): Research Thesis Engine 基础表(Post Graph / Media /
                      External Source / Claim / Theme / Thesis / AI usage)
    v5 (2026-08-30): 可审计的 Theme canonicalization / Underlying Source /
                      Claim Verification / AI Analyst 增量层
    v6 (2026-08-30): 跨 Theme Research Case 综合分析
    v7 (2026-08-31): AI 请求前置费用账本 + Golden 确认状态
    v8 (2026-08-31): Investment Opportunity / Candidate Logic Chain 独立层
    v9 (2026-08-31): Candidate Coverage / Best Expression / Funnel 审计层
    v10 (2026-08-31): Opportunity Odds / Market Expectations / Scenario Valuation 层

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

CURRENT_SCHEMA_VERSION = 10


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


# ---------------------------------------------------------------------------
# v4 Research Thesis Engine schema
# ---------------------------------------------------------------------------
# 这里同时预留 P1-P3 的版本表，避免 P0 上线后再次重构主键和证据关系。
# 所有表均为 append/upsert 友好设计；raw_posts 继续是原始 Post 的唯一事实源。

V4_RESEARCH_ENGINE_SQL = """
CREATE TABLE IF NOT EXISTS post_references (
    source_post_id     TEXT    NOT NULL,
    target_post_id     TEXT    NOT NULL,
    reference_type     TEXT    NOT NULL CHECK (reference_type IN ('quote','reply','repost','referenced')),
    target_url         TEXT,
    fetch_status       TEXT    NOT NULL DEFAULT 'pending',
    discovered_at      TEXT    NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ', 'now')),
    last_attempt_at    TEXT,
    last_error         TEXT,
    PRIMARY KEY (source_post_id, target_post_id, reference_type)
);
CREATE INDEX IF NOT EXISTS idx_post_references_target ON post_references(target_post_id);
CREATE INDEX IF NOT EXISTS idx_post_references_status ON post_references(fetch_status);

CREATE TABLE IF NOT EXISTS post_graph_memberships (
    root_post_id       TEXT    NOT NULL,
    post_id            TEXT    NOT NULL,
    parent_post_id     TEXT,
    depth              INTEGER NOT NULL CHECK (depth BETWEEN 0 AND 10),
    reference_type     TEXT    NOT NULL DEFAULT 'original',
    crawl_status       TEXT    NOT NULL DEFAULT 'complete',
    crawled_at         TEXT    NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ', 'now')),
    last_error         TEXT,
    PRIMARY KEY (root_post_id, post_id)
);
CREATE INDEX IF NOT EXISTS idx_graph_membership_post ON post_graph_memberships(post_id);
CREATE INDEX IF NOT EXISTS idx_graph_membership_status ON post_graph_memberships(crawl_status);

CREATE TABLE IF NOT EXISTS media_assets (
    media_id           TEXT PRIMARY KEY,
    post_id            TEXT    NOT NULL,
    source_url         TEXT    NOT NULL,
    storage_url        TEXT,
    media_type         TEXT    NOT NULL DEFAULT 'image',
    mime_type          TEXT,
    content_hash       TEXT,
    width              INTEGER,
    height             INTEGER,
    raw_payload        TEXT,
    download_status    TEXT    NOT NULL DEFAULT 'pending',
    analysis_status    TEXT    NOT NULL DEFAULT 'pending',
    created_at         TEXT    NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ', 'now')),
    updated_at         TEXT    NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ', 'now')),
    UNIQUE(post_id, source_url)
);
CREATE INDEX IF NOT EXISTS idx_media_post ON media_assets(post_id);
CREATE INDEX IF NOT EXISTS idx_media_analysis_status ON media_assets(analysis_status);
CREATE INDEX IF NOT EXISTS idx_media_hash ON media_assets(content_hash);

CREATE TABLE IF NOT EXISTS media_analyses (
    media_id           TEXT PRIMARY KEY,
    prompt_version     TEXT    NOT NULL,
    provider           TEXT    NOT NULL,
    model              TEXT    NOT NULL,
    input_hash         TEXT    NOT NULL,
    analysis_json      TEXT    NOT NULL,
    created_at         TEXT    NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ', 'now')),
    FOREIGN KEY (media_id) REFERENCES media_assets(media_id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS external_sources (
    source_id          TEXT PRIMARY KEY,
    source_type        TEXT    NOT NULL DEFAULT 'unknown',
    publisher          TEXT,
    title              TEXT,
    url                TEXT    NOT NULL UNIQUE,
    published_at       TEXT,
    content_summary    TEXT,
    primary_or_secondary TEXT,
    reliability_score REAL,
    content_hash       TEXT,
    crawl_status       TEXT    NOT NULL DEFAULT 'pending',
    created_at         TEXT    NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ', 'now')),
    updated_at         TEXT    NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ', 'now'))
);

CREATE TABLE IF NOT EXISTS post_external_sources (
    post_id            TEXT NOT NULL,
    source_id          TEXT NOT NULL,
    relation_type      TEXT NOT NULL DEFAULT 'linked',
    PRIMARY KEY (post_id, source_id),
    FOREIGN KEY (source_id) REFERENCES external_sources(source_id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS claims (
    claim_id           TEXT PRIMARY KEY,
    claim_text         TEXT    NOT NULL,
    claim_type         TEXT    NOT NULL CHECK (claim_type IN ('FACT','FORECAST','OPINION','INFERENCE','VALUATION','CATALYST','RISK','POSITION','QUESTION')),
    author_id          TEXT,
    companies_json     TEXT    NOT NULL DEFAULT '[]',
    themes_json        TEXT    NOT NULL DEFAULT '[]',
    time_horizon       TEXT,
    source_post_id     TEXT,
    source_media_id    TEXT,
    source_external_id TEXT,
    evidence_ids_json  TEXT    NOT NULL DEFAULT '[]',
    confidence         REAL    NOT NULL DEFAULT 0.5 CHECK (confidence BETWEEN 0 AND 1),
    verification_status TEXT  NOT NULL DEFAULT 'UNVERIFIED',
    point_in_time      TEXT,
    content_hash       TEXT    NOT NULL,
    created_at         TEXT    NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ', 'now'))
);
CREATE INDEX IF NOT EXISTS idx_claims_post ON claims(source_post_id);
CREATE INDEX IF NOT EXISTS idx_claims_author ON claims(author_id);
CREATE INDEX IF NOT EXISTS idx_claims_verification ON claims(verification_status);

CREATE TABLE IF NOT EXISTS themes (
    theme_id           TEXT PRIMARY KEY,
    name               TEXT    NOT NULL UNIQUE,
    description        TEXT,
    parent_theme_id    TEXT,
    aliases_json       TEXT    NOT NULL DEFAULT '[]',
    created_by         TEXT    NOT NULL DEFAULT 'llm',
    created_at         TEXT    NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ', 'now')),
    updated_at         TEXT    NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ', 'now'))
);

CREATE TABLE IF NOT EXISTS claim_themes (
    claim_id           TEXT NOT NULL,
    theme_id           TEXT NOT NULL,
    confidence         REAL NOT NULL DEFAULT 0.5,
    PRIMARY KEY (claim_id, theme_id),
    FOREIGN KEY (claim_id) REFERENCES claims(claim_id) ON DELETE CASCADE,
    FOREIGN KEY (theme_id) REFERENCES themes(theme_id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS theses (
    thesis_id          TEXT PRIMARY KEY,
    author_id          TEXT    NOT NULL,
    theme_id           TEXT    NOT NULL,
    current_version    INTEGER NOT NULL DEFAULT 0,
    current_thesis     TEXT,
    thesis_summary     TEXT,
    confidence         REAL,
    first_seen         TEXT,
    last_updated       TEXT,
    UNIQUE(author_id, theme_id),
    FOREIGN KEY (theme_id) REFERENCES themes(theme_id) ON DELETE RESTRICT
);

CREATE TABLE IF NOT EXISTS thesis_versions (
    thesis_id          TEXT    NOT NULL,
    version_number     INTEGER NOT NULL,
    snapshot_json      TEXT    NOT NULL,
    change_type        TEXT    NOT NULL DEFAULT 'NO_CHANGE',
    thesis_change_score REAL   NOT NULL DEFAULT 0,
    evidence_digest    TEXT,
    model              TEXT,
    created_at         TEXT    NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ', 'now')),
    PRIMARY KEY (thesis_id, version_number),
    FOREIGN KEY (thesis_id) REFERENCES theses(thesis_id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS thesis_evidence (
    thesis_id          TEXT NOT NULL,
    version_number     INTEGER NOT NULL,
    claim_id           TEXT NOT NULL,
    evidence_weight    REAL NOT NULL DEFAULT 1,
    PRIMARY KEY (thesis_id, version_number, claim_id),
    FOREIGN KEY (thesis_id, version_number) REFERENCES thesis_versions(thesis_id, version_number) ON DELETE CASCADE,
    FOREIGN KEY (claim_id) REFERENCES claims(claim_id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS thesis_changes (
    change_id          TEXT PRIMARY KEY,
    thesis_id          TEXT NOT NULL,
    from_version       INTEGER,
    to_version         INTEGER NOT NULL,
    change_type        TEXT NOT NULL,
    change_score       REAL NOT NULL,
    summary            TEXT,
    detected_at        TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ', 'now')),
    FOREIGN KEY (thesis_id) REFERENCES theses(thesis_id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS ai_usage (
    usage_id           TEXT PRIMARY KEY,
    workload           TEXT    NOT NULL,
    provider           TEXT    NOT NULL,
    model              TEXT    NOT NULL,
    object_type        TEXT,
    object_id          TEXT,
    input_tokens       INTEGER NOT NULL DEFAULT 0,
    cached_input_tokens INTEGER NOT NULL DEFAULT 0,
    output_tokens      INTEGER NOT NULL DEFAULT 0,
    estimated_cost_usd REAL    NOT NULL DEFAULT 0,
    latency_ms         INTEGER NOT NULL DEFAULT 0,
    status             TEXT    NOT NULL,
    error_type         TEXT,
    created_at         TEXT    NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ', 'now'))
);
CREATE INDEX IF NOT EXISTS idx_ai_usage_created ON ai_usage(created_at);
CREATE INDEX IF NOT EXISTS idx_ai_usage_workload ON ai_usage(workload);
"""


def _migrate_to_v4(conn: sqlite3.Connection) -> None:
    """创建 Research Thesis Engine 基础表；全量 IF NOT EXISTS，重复执行安全。"""
    conn.executescript(V4_RESEARCH_ENGINE_SQL)


# v5 只增加审计/派生表，不改动 v4 的事实表和主键。这样已有 Post、Claim、
# Theme、Thesis 都能原位升级，也符合“不要重新设计数据库”的约束。
V5_THESIS_QUALITY_SQL = """
CREATE TABLE IF NOT EXISTS theme_embeddings (
    theme_id           TEXT    NOT NULL,
    model              TEXT    NOT NULL,
    dimensions         INTEGER NOT NULL,
    input_hash         TEXT    NOT NULL,
    embedding_json     TEXT    NOT NULL,
    embedded_at        TEXT    NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ', 'now')),
    PRIMARY KEY (theme_id, model),
    FOREIGN KEY (theme_id) REFERENCES themes(theme_id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS theme_canonicalization_audit (
    audit_id           TEXT PRIMARY KEY,
    left_theme_id      TEXT    NOT NULL,
    right_theme_id     TEXT    NOT NULL,
    embedding_similarity REAL NOT NULL,
    decision           TEXT    NOT NULL CHECK (decision IN ('MERGE_ALIAS','RELATED_DISTINCT','DISTINCT')),
    canonical_theme_id TEXT,
    confidence         REAL    NOT NULL,
    rationale          TEXT    NOT NULL,
    model              TEXT    NOT NULL,
    judged_at          TEXT    NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ', 'now')),
    UNIQUE(left_theme_id, right_theme_id)
);

CREATE TABLE IF NOT EXISTS underlying_sources (
    underlying_source_id TEXT PRIMARY KEY,
    canonical_url      TEXT,
    publisher          TEXT,
    title              TEXT,
    source_class       TEXT NOT NULL CHECK (source_class IN ('PRIMARY','SECONDARY','INDUSTRY','SOCIAL','MEDIA','UNKNOWN')),
    content_hash       TEXT,
    created_at         TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ', 'now')),
    updated_at         TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ', 'now'))
);
CREATE INDEX IF NOT EXISTS idx_underlying_content_hash ON underlying_sources(content_hash);
CREATE UNIQUE INDEX IF NOT EXISTS idx_underlying_canonical_url
    ON underlying_sources(canonical_url) WHERE canonical_url IS NOT NULL;

CREATE TABLE IF NOT EXISTS source_memberships (
    underlying_source_id TEXT NOT NULL,
    evidence_type      TEXT NOT NULL CHECK (evidence_type IN ('external','media','post')),
    evidence_id        TEXT NOT NULL,
    mention_post_id    TEXT,
    relation_type      TEXT NOT NULL DEFAULT 'mentions',
    created_at         TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ', 'now')),
    PRIMARY KEY (underlying_source_id, evidence_type, evidence_id, mention_post_id),
    FOREIGN KEY (underlying_source_id) REFERENCES underlying_sources(underlying_source_id) ON DELETE CASCADE
);
CREATE INDEX IF NOT EXISTS idx_source_memberships_evidence ON source_memberships(evidence_type, evidence_id);
CREATE INDEX IF NOT EXISTS idx_source_memberships_post ON source_memberships(mention_post_id);

CREATE TABLE IF NOT EXISTS claim_verifications (
    claim_id           TEXT    NOT NULL,
    verification_version INTEGER NOT NULL,
    importance_score   REAL    NOT NULL,
    status             TEXT    NOT NULL CHECK (status IN (
        'UNVERIFIED','SUPPORTED_BY_PRIMARY','SUPPORTED_BY_SECONDARY',
        'PARTIALLY_SUPPORTED','CONTRADICTED','UNVERIFIABLE'
    )),
    rationale          TEXT    NOT NULL,
    corrected_claim    TEXT,
    sources_json       TEXT    NOT NULL DEFAULT '[]',
    model              TEXT    NOT NULL,
    verified_at        TEXT    NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ', 'now')),
    PRIMARY KEY (claim_id, verification_version),
    FOREIGN KEY (claim_id) REFERENCES claims(claim_id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS thesis_analyses (
    thesis_id          TEXT    NOT NULL,
    thesis_version     INTEGER NOT NULL,
    analysis_json      TEXT    NOT NULL,
    model              TEXT    NOT NULL,
    analysis_mode      TEXT    NOT NULL DEFAULT 'TERRA',
    created_at         TEXT    NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ', 'now')),
    PRIMARY KEY (thesis_id, thesis_version),
    FOREIGN KEY (thesis_id) REFERENCES theses(thesis_id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS cross_author_theses (
    theme_id           TEXT PRIMARY KEY,
    analysis_json      TEXT    NOT NULL,
    model              TEXT    NOT NULL,
    source_digest      TEXT    NOT NULL,
    updated_at         TEXT    NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ', 'now')),
    FOREIGN KEY (theme_id) REFERENCES themes(theme_id) ON DELETE CASCADE
);
"""


def _migrate_to_v5(conn: sqlite3.Connection) -> None:
    """增加研究质量审计层；全量 IF NOT EXISTS，重复执行安全。"""
    conn.executescript(V5_THESIS_QUALITY_SQL)


V6_RESEARCH_CASE_SQL = """
CREATE TABLE IF NOT EXISTS research_case_analyses (
    case_id            TEXT PRIMARY KEY,
    title              TEXT NOT NULL,
    analysis_json      TEXT NOT NULL,
    source_digest      TEXT NOT NULL,
    model              TEXT NOT NULL,
    updated_at         TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ', 'now'))
);
"""


def _migrate_to_v6(conn: sqlite3.Connection) -> None:
    conn.executescript(V6_RESEARCH_CASE_SQL)


V7_AI_GUARDRAIL_SQL = """
CREATE TABLE IF NOT EXISTS ai_usage_ledger (
    ledger_id          TEXT PRIMARY KEY,
    run_id             TEXT NOT NULL,
    workflow           TEXT NOT NULL,
    stage              TEXT NOT NULL,
    entity_type        TEXT,
    entity_id          TEXT,
    provider           TEXT NOT NULL,
    model              TEXT NOT NULL,
    request_started_at TEXT NOT NULL,
    request_finished_at TEXT,
    input_tokens       INTEGER NOT NULL DEFAULT 0,
    cached_input_tokens INTEGER NOT NULL DEFAULT 0,
    output_tokens      INTEGER NOT NULL DEFAULT 0,
    estimated_cost     REAL NOT NULL DEFAULT 0,
    actual_cost_if_available REAL,
    status             TEXT NOT NULL CHECK (status IN (
        'PENDING','SUCCESS','FAILED','CANCELLED','BUDGET_BLOCKED','DAILY_BUDGET_EXCEEDED',
        'SKIPPED','UNKNOWN_COST'
    )),
    input_hash         TEXT,
    prompt_version     TEXT,
    error_type         TEXT,
    metadata_json      TEXT NOT NULL DEFAULT '{}'
);
CREATE INDEX IF NOT EXISTS idx_ai_ledger_run ON ai_usage_ledger(run_id, stage);
CREATE INDEX IF NOT EXISTS idx_ai_ledger_started ON ai_usage_ledger(request_started_at);
CREATE INDEX IF NOT EXISTS idx_ai_ledger_status ON ai_usage_ledger(status);
CREATE INDEX IF NOT EXISTS idx_ai_ledger_dedup
    ON ai_usage_ledger(stage, model, prompt_version, input_hash, status);

CREATE TABLE IF NOT EXISTS golden_validations (
    case_id            TEXT PRIMARY KEY,
    status             TEXT NOT NULL CHECK (status IN ('PASS','PARTIAL','FAIL')),
    validator_version  TEXT NOT NULL,
    report_json        TEXT NOT NULL,
    source_audit_sha256 TEXT NOT NULL,
    validation_timestamp TEXT NOT NULL,
    mode               TEXT NOT NULL,
    additional_ai_calls INTEGER NOT NULL DEFAULT 0,
    additional_ai_cost_usd REAL NOT NULL DEFAULT 0
);
"""


def _migrate_to_v7(conn: sqlite3.Connection) -> None:
    conn.executescript(V7_AI_GUARDRAIL_SQL)


V8_OPPORTUNITY_ENGINE_SQL = """
CREATE TABLE IF NOT EXISTS logic_chain_analyses (
    candidate_id       TEXT PRIMARY KEY,
    title              TEXT NOT NULL,
    analysis_json      TEXT NOT NULL,
    source_digest      TEXT NOT NULL,
    model              TEXT NOT NULL,
    discovery_type     TEXT NOT NULL CHECK (discovery_type IN ('SEEDED','DISCOVERED')),
    status              TEXT NOT NULL DEFAULT 'ACTIVE' CHECK (status IN ('ACTIVE','THEME_ONLY','REJECTED')),
    updated_at          TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ', 'now'))
);

CREATE TABLE IF NOT EXISTS investment_opportunities (
    opportunity_id     TEXT PRIMARY KEY,
    title              TEXT NOT NULL,
    theme_ids_json     TEXT NOT NULL DEFAULT '[]',
    thesis_ids_json    TEXT NOT NULL DEFAULT '[]',
    companies_json     TEXT NOT NULL DEFAULT '[]',
    primary_company    TEXT,
    direction          TEXT NOT NULL CHECK (direction IN ('LONG','SHORT','HEDGE','MIXED','UNRESOLVED')),
    time_horizon       TEXT,
    driver              TEXT NOT NULL,
    industry_change     TEXT,
    bottleneck          TEXT,
    earnings_mechanism  TEXT,
    valuation_question  TEXT,
    market_expectations TEXT,
    mispricing_hypothesis TEXT,
    catalysts_json      TEXT NOT NULL DEFAULT '[]',
    risks_json          TEXT NOT NULL DEFAULT '[]',
    invalidation_conditions_json TEXT NOT NULL DEFAULT '[]',
    missing_evidence_json TEXT NOT NULL DEFAULT '[]',
    actionability       TEXT NOT NULL CHECK (actionability IN (
        'NOT_ACTIONABLE','WATCH','RESEARCH','BUY_CANDIDATE','HEDGE_CANDIDATE','AVOID'
    )),
    chain_completeness  INTEGER NOT NULL CHECK (chain_completeness BETWEEN 0 AND 6),
    opportunity_score   REAL NOT NULL CHECK (opportunity_score BETWEEN 0 AND 100),
    thesis_quality_score REAL NOT NULL CHECK (thesis_quality_score BETWEEN 0 AND 100),
    evidence_quality_score REAL NOT NULL CHECK (evidence_quality_score BETWEEN 0 AND 100),
    earnings_impact_score REAL NOT NULL CHECK (earnings_impact_score BETWEEN 0 AND 100),
    mispricing_score    REAL NOT NULL CHECK (mispricing_score BETWEEN 0 AND 100),
    catalyst_score      REAL NOT NULL CHECK (catalyst_score BETWEEN 0 AND 100),
    risk_reward_score   REAL NOT NULL CHECK (risk_reward_score BETWEEN 0 AND 100),
    one_line_thesis     TEXT NOT NULL,
    why_now             TEXT,
    ai_verdict          TEXT NOT NULL,
    next_trigger        TEXT,
    positive_exposure_json TEXT NOT NULL DEFAULT '[]',
    negative_exposure_json TEXT NOT NULL DEFAULT '[]',
    authors_json        TEXT NOT NULL DEFAULT '[]',
    source_roots_json   TEXT NOT NULL DEFAULT '[]',
    social_mention_count INTEGER NOT NULL DEFAULT 0,
    independent_evidence_count INTEGER NOT NULL DEFAULT 0,
    valuation_json      TEXT NOT NULL DEFAULT '{}',
    synthesis_json      TEXT NOT NULL DEFAULT '{}',
    source_candidate_id TEXT NOT NULL,
    created_at          TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ', 'now')),
    updated_at          TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ', 'now')),
    FOREIGN KEY (source_candidate_id) REFERENCES logic_chain_analyses(candidate_id) ON DELETE RESTRICT
);
CREATE INDEX IF NOT EXISTS idx_opportunity_rank
    ON investment_opportunities(actionability, opportunity_score DESC);
CREATE INDEX IF NOT EXISTS idx_opportunity_updated
    ON investment_opportunities(updated_at DESC);

CREATE TABLE IF NOT EXISTS opportunity_evidence (
    opportunity_id     TEXT NOT NULL,
    evidence_type      TEXT NOT NULL CHECK (evidence_type IN ('claim','media','post','external','thesis')),
    evidence_id        TEXT NOT NULL,
    evidence_role      TEXT NOT NULL DEFAULT 'SUPPORT' CHECK (evidence_role IN ('SUPPORT','COUNTER','CONTEXT')),
    source_root_id     TEXT,
    evidence_weight    REAL NOT NULL DEFAULT 1,
    PRIMARY KEY (opportunity_id, evidence_type, evidence_id),
    FOREIGN KEY (opportunity_id) REFERENCES investment_opportunities(opportunity_id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS opportunity_versions (
    opportunity_id     TEXT NOT NULL,
    version_number     INTEGER NOT NULL,
    snapshot_json      TEXT NOT NULL,
    source_digest      TEXT NOT NULL,
    model              TEXT NOT NULL,
    created_at          TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ', 'now')),
    PRIMARY KEY (opportunity_id, version_number),
    FOREIGN KEY (opportunity_id) REFERENCES investment_opportunities(opportunity_id) ON DELETE CASCADE
);
"""


def _migrate_to_v8(conn: sqlite3.Connection) -> None:
    conn.executescript(V8_OPPORTUNITY_ENGINE_SQL)


V9_OPPORTUNITY_COVERAGE_SQL = """
CREATE TABLE IF NOT EXISTS candidate_coverage (
    candidate_id       TEXT PRIMARY KEY,
    original_title     TEXT NOT NULL,
    final_status       TEXT NOT NULL CHECK (final_status IN (
        'ANALYZED_AND_PROMOTED','ANALYZED_AND_WATCH','ANALYZED_AND_REJECTED',
        'MERGED_INTO_OTHER_CHAIN','SUPERSEDED','NOT_ANALYZED'
    )),
    reason              TEXT NOT NULL,
    mapped_candidate_id TEXT,
    opportunity_id     TEXT,
    analysis_source     TEXT NOT NULL,
    updated_at          TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ', 'now'))
);

CREATE TABLE IF NOT EXISTS opportunity_best_expressions (
    opportunity_id     TEXT PRIMARY KEY,
    analysis_json      TEXT NOT NULL,
    source_digest      TEXT NOT NULL,
    model              TEXT NOT NULL,
    prompt_version     TEXT NOT NULL,
    updated_at          TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ', 'now')),
    FOREIGN KEY (opportunity_id) REFERENCES investment_opportunities(opportunity_id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS opportunity_funnel_snapshots (
    snapshot_id        TEXT PRIMARY KEY,
    counts_json        TEXT NOT NULL,
    definitions_json   TEXT NOT NULL,
    created_at          TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ', 'now'))
);
"""


def _migrate_to_v9(conn: sqlite3.Connection) -> None:
    conn.executescript(V9_OPPORTUNITY_COVERAGE_SQL)


V10_OPPORTUNITY_ODDS_SQL = """
CREATE TABLE IF NOT EXISTS opportunity_odds (
    odds_id             TEXT PRIMARY KEY,
    opportunity_id      TEXT NOT NULL,
    ticker              TEXT NOT NULL,
    company             TEXT NOT NULL,
    exchange            TEXT,
    currency            TEXT NOT NULL,
    best_expression_rank INTEGER,
    analysis_json       TEXT NOT NULL,
    source_digest       TEXT NOT NULL,
    model               TEXT NOT NULL,
    prompt_version      TEXT NOT NULL,
    as_of_date          TEXT NOT NULL,
    current_price       REAL NOT NULL CHECK (current_price > 0),
    bear_fair_value     REAL CHECK (bear_fair_value IS NULL OR bear_fair_value >= 0),
    base_fair_value     REAL CHECK (base_fair_value IS NULL OR base_fair_value >= 0),
    bull_fair_value     REAL CHECK (bull_fair_value IS NULL OR bull_fair_value >= 0),
    base_upside         REAL,
    bear_downside       REAL,
    reward_risk         REAL,
    expected_fair_value REAL,
    expected_return     REAL,
    earnings_gap        REAL,
    expectations_gap    TEXT NOT NULL CHECK (expectations_gap IN (
        'STRONGLY_POSITIVE','POSITIVE','NEUTRAL','NEGATIVE','STRONGLY_NEGATIVE','UNKNOWN'
    )),
    odds_band           TEXT NOT NULL CHECK (odds_band IN ('VERY_GOOD','GOOD','FAIR','POOR','VERY_POOR','INCOMPLETE')),
    odds_score          REAL CHECK (odds_score IS NULL OR (odds_score BETWEEN 0 AND 100)),
    odds_status         TEXT NOT NULL CHECK (odds_status IN (
        'NOT_ACTIONABLE','WATCH','RESEARCH','BUY_CANDIDATE','AVOID',
        'GOOD_COMPANY_BAD_ODDS','GOOD_ODDS_WEAK_EVIDENCE','VALUATION_INCOMPLETE'
    )),
    valuation_confidence TEXT NOT NULL CHECK (valuation_confidence IN ('LOW','MEDIUM','HIGH')),
    thesis_confidence   TEXT NOT NULL CHECK (thesis_confidence IN ('LOW','MEDIUM','HIGH')),
    created_at          TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ', 'now')),
    updated_at          TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ', 'now')),
    UNIQUE (opportunity_id, ticker, prompt_version),
    FOREIGN KEY (opportunity_id) REFERENCES investment_opportunities(opportunity_id) ON DELETE CASCADE
);
CREATE INDEX IF NOT EXISTS idx_opportunity_odds_rank
    ON opportunity_odds(odds_status, odds_score DESC, base_upside DESC);
CREATE INDEX IF NOT EXISTS idx_opportunity_odds_opportunity
    ON opportunity_odds(opportunity_id, best_expression_rank);

CREATE TABLE IF NOT EXISTS opportunity_odds_runs (
    run_id              TEXT PRIMARY KEY,
    universe_json       TEXT NOT NULL,
    config_json         TEXT NOT NULL,
    summary_json        TEXT NOT NULL,
    status              TEXT NOT NULL CHECK (status IN ('COMPLETED','PARTIAL','FAILED','DRY_RUN')),
    ai_calls            INTEGER NOT NULL DEFAULT 0,
    known_cost_usd      REAL NOT NULL DEFAULT 0,
    risk_cost_usd       REAL NOT NULL DEFAULT 0,
    created_at          TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ', 'now'))
);
"""


def _migrate_to_v10(conn: sqlite3.Connection) -> None:
    conn.executescript(V10_OPPORTUNITY_ODDS_SQL)


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

    _migrate_to_v4(conn)
    _migrate_to_v5(conn)
    _migrate_to_v6(conn)
    _migrate_to_v7(conn)
    _migrate_to_v8(conn)
    _migrate_to_v9(conn)
    _migrate_to_v10(conn)
    conn.execute(f"PRAGMA user_version = {CURRENT_SCHEMA_VERSION}")


@contextmanager
def get_conn(db_path: DbPath) -> Iterator[sqlite3.Connection]:
    """带 row_factory + 外键的连接上下文,异常自动 rollback。

    每日抓取会并发写入多个账号；设置 busy timeout，避免短暂写锁直接把某个
    账号整批判失败。SQLite 仍保持单写者语义，只是在锁释放前安全等待。
    """
    conn = sqlite3.connect(db_path, timeout=30)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    conn.execute("PRAGMA busy_timeout = 30000")
    _register_extensions(conn)
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()
