"""数据访问层:raw_posts / predictions / verifications 的 CRUD。

设计要点:
- raw_posts.upsert_raw_post 幂等,但不覆盖 is_deleted(避免重抓数据清掉删帖标记)
- predictions 业务键 UNIQUE(post_id, ticker, direction),一条原文可对应多条预测
- verifications.upsert_verification 走"非空字段合并"语义,
  保证 r_1w 跑完不会因为 r_1m 后续写入而丢失
"""
from __future__ import annotations

import dataclasses
from typing import List, Optional, Tuple

from .db import DbPath, get_conn
from .models import (
    PredictionRecord,
    PriceReturns,
    QuantitativeOutcome,
    RawPost,
    Verification,
)


# ---------------------------------------------------------------------------
# RawPost
# ---------------------------------------------------------------------------

def upsert_raw_post(post: RawPost, db_path: DbPath) -> None:
    """按 post_id 幂等插入/更新。

    注意:此函数不覆盖 is_deleted 字段(避免重抓数据意外清掉删帖标记);
    删除标记只能由 mark_post_deleted 显式设置。archive_url 用 COALESCE 保留旧值。
    """
    with get_conn(db_path) as conn:
        conn.execute(
            """
            INSERT INTO raw_posts (
                post_id, source_id, platform, published_at, captured_at,
                raw_text, raw_url, raw_json, content_hash, is_deleted, archive_url
            ) VALUES (
                :post_id, :source_id, :platform, :published_at, :captured_at,
                :raw_text, :raw_url, :raw_json, :content_hash, :is_deleted, :archive_url
            )
            ON CONFLICT(post_id) DO UPDATE SET
                source_id    = excluded.source_id,
                platform     = excluded.platform,
                published_at = excluded.published_at,
                captured_at  = excluded.captured_at,
                raw_text     = excluded.raw_text,
                raw_json     = excluded.raw_json,
                raw_url      = excluded.raw_url,
                content_hash = excluded.content_hash,
                archive_url  = COALESCE(raw_posts.archive_url, excluded.archive_url)
                -- is_deleted 显式不更新
            """,
            post.to_row(),
        )


def get_raw_post(post_id: str, db_path: DbPath) -> Optional[RawPost]:
    with get_conn(db_path) as conn:
        row = conn.execute(
            "SELECT * FROM raw_posts WHERE post_id = ?",
            (post_id,),
        ).fetchone()
        return RawPost.from_row(dict(row)) if row else None


def list_raw_posts_by_source(
    source_id: str,
    db_path: DbPath,
    limit: int = 100,
    offset: int = 0,
) -> List[RawPost]:
    with get_conn(db_path) as conn:
        rows = conn.execute(
            """
            SELECT * FROM raw_posts
            WHERE source_id = ?
            ORDER BY published_at DESC
            LIMIT ? OFFSET ?
            """,
            (source_id, limit, offset),
        ).fetchall()
        return [RawPost.from_row(dict(r)) for r in rows]


def mark_post_deleted(
    post_id: str,
    db_path: DbPath,
    is_deleted: bool = True,
) -> None:
    """标记原文被原作者删除。红旗检测的入口之一。"""
    with get_conn(db_path) as conn:
        conn.execute(
            "UPDATE raw_posts SET is_deleted = ? WHERE post_id = ?",
            (int(is_deleted), post_id),
        )


# ---------------------------------------------------------------------------
# PredictionRecord
# ---------------------------------------------------------------------------

def insert_prediction(pred: PredictionRecord, db_path: DbPath) -> None:
    """Upsert 预测,业务键 (post_id, ticker, direction)。

    v3 行为:prompt_version 更新会触发覆盖,新 LLM 抽取覆盖旧抽取。
    prediction_id 在同一 post_id 重复 upsert 时保持原值(用 COALESCE 保护)。
    """
    with get_conn(db_path) as conn:
        conn.execute(
            """
            INSERT INTO predictions (
                prediction_id, post_id, source_id, published_at, captured_at,
                ticker, market, direction, claim_type, quantitative_claim,
                horizon, conviction, is_repeat_call, repeat_of,
                thesis_summary, thesis_category,
                raw_asset_mention, resolution_status, context_tickers, hedged,
                prompt_version, extraction_notes
            ) VALUES (
                :prediction_id, :post_id, :source_id, :published_at, :captured_at,
                :ticker, :market, :direction, :claim_type, :quantitative_claim,
                :horizon, :conviction, :is_repeat_call, :repeat_of,
                :thesis_summary, :thesis_category,
                :raw_asset_mention, :resolution_status, :context_tickers, :hedged,
                :prompt_version, :extraction_notes
            )
            ON CONFLICT(post_id, ticker, direction) DO UPDATE SET
                source_id         = excluded.source_id,
                published_at      = excluded.published_at,
                captured_at       = excluded.captured_at,
                market            = excluded.market,
                claim_type        = excluded.claim_type,
                quantitative_claim = excluded.quantitative_claim,
                horizon           = excluded.horizon,
                conviction        = excluded.conviction,
                is_repeat_call    = excluded.is_repeat_call,
                repeat_of         = excluded.repeat_of,
                thesis_summary    = excluded.thesis_summary,
                thesis_category   = excluded.thesis_category,
                raw_asset_mention = excluded.raw_asset_mention,
                resolution_status = excluded.resolution_status,
                context_tickers   = excluded.context_tickers,
                hedged            = excluded.hedged,
                prompt_version    = excluded.prompt_version,
                extraction_notes  = excluded.extraction_notes
            """,
            pred.to_row(),
        )


def get_prediction(prediction_id: str, db_path: DbPath) -> Optional[PredictionRecord]:
    with get_conn(db_path) as conn:
        row = conn.execute(
            "SELECT * FROM predictions WHERE prediction_id = ?",
            (prediction_id,),
        ).fetchone()
        return PredictionRecord.from_row(dict(row)) if row else None


def list_predictions_by_source(
    source_id: str,
    db_path: DbPath,
    limit: int = 100,
    offset: int = 0,
) -> List[PredictionRecord]:
    with get_conn(db_path) as conn:
        rows = conn.execute(
            """
            SELECT * FROM predictions
            WHERE source_id = ?
            ORDER BY published_at DESC
            LIMIT ? OFFSET ?
            """,
            (source_id, limit, offset),
        ).fetchall()
        return [PredictionRecord.from_row(dict(r)) for r in rows]


def list_predictions_by_ticker(
    ticker: str,
    db_path: DbPath,
    limit: int = 100,
) -> List[PredictionRecord]:
    with get_conn(db_path) as conn:
        rows = conn.execute(
            """
            SELECT * FROM predictions
            WHERE ticker = ?
            ORDER BY published_at DESC
            LIMIT ?
            """,
            (ticker, limit),
        ).fetchall()
        return [PredictionRecord.from_row(dict(r)) for r in rows]


def list_predictions_by_post(
    post_id: str,
    db_path: DbPath,
) -> List[PredictionRecord]:
    """一条原文可能抽出多条预测(对多标的),用这个函数反查。"""
    with get_conn(db_path) as conn:
        rows = conn.execute(
            "SELECT * FROM predictions WHERE post_id = ?",
            (post_id,),
        ).fetchall()
        return [PredictionRecord.from_row(dict(r)) for r in rows]


def count_predictions_by_source(source_id: str, db_path: DbPath) -> int:
    with get_conn(db_path) as conn:
        row = conn.execute(
            "SELECT COUNT(*) AS n FROM predictions WHERE source_id = ?",
            (source_id,),
        ).fetchone()
        return int(row["n"])


# ---------------------------------------------------------------------------
# Verification
# ---------------------------------------------------------------------------

def upsert_verification(ver: Verification, db_path: DbPath) -> None:
    """部分更新语义:
    - 第一次调用(记录不存在)→ 整行插入
    - 后续调用 → 与旧记录按"非空才覆盖"合并,保证 r_1w 不会因为 r_1m 来了被清空

    合并细节:
    - 顶层字段(status, entry_price_basis, verified_at):新值非空才覆盖
    - JSON 字段(price_returns, quantitative_outcome):逐子字段合并(新值非 None 才覆盖)
    - status 例外:新值是 'pending' 视为"未变",防止已 verified_* 的状态被回退
    """
    with get_conn(db_path) as conn:
        existing = conn.execute(
            "SELECT * FROM verifications WHERE prediction_id = ?",
            (ver.prediction_id,),
        ).fetchone()
        if existing is None:
            conn.execute(
                """
                INSERT INTO verifications (
                    prediction_id, status, price_returns,
                    entry_price_basis, quantitative_outcome, verified_at
                ) VALUES (
                    :prediction_id, :status, :price_returns,
                    :entry_price_basis, :quantitative_outcome, :verified_at
                )
                """,
                ver.to_row(),
            )
        else:
            old = Verification.from_row(dict(existing))
            merged = _merge_verification(old, ver)
            conn.execute(
                """
                UPDATE verifications
                   SET status               = :status,
                       price_returns        = :price_returns,
                       entry_price_basis    = :entry_price_basis,
                       quantitative_outcome = :quantitative_outcome,
                       verified_at          = :verified_at
                 WHERE prediction_id = :prediction_id
                """,
                merged.to_row(),
            )


def _merge_verification(old: Verification, new: Verification) -> Verification:
    """按字段合并。status 例外:新值为 pending 不覆盖(防止回退)。"""
    # status 合并:verified_* / expired / unverifiable 覆盖;'pending' 不覆盖已有非 pending 状态
    if new.status and new.status != "pending":
        status = new.status
    elif not old.status:
        status = new.status or "pending"
    else:
        status = old.status

    entry_price_basis = new.entry_price_basis if new.entry_price_basis else old.entry_price_basis
    verified_at = new.verified_at if new.verified_at else old.verified_at

    return Verification(
        prediction_id=new.prediction_id,
        status=status,
        price_returns=_merge_dataclass(old.price_returns, new.price_returns, PriceReturns),
        entry_price_basis=entry_price_basis,
        quantitative_outcome=_merge_dataclass(
            old.quantitative_outcome, new.quantitative_outcome, QuantitativeOutcome
        ),
        verified_at=verified_at,
    )


def _merge_dataclass(old_dc, new_dc, cls):
    """逐子字段合并:新值非 None 才覆盖。"""
    if new_dc is None:
        return old_dc
    if old_dc is None:
        return new_dc
    merged_kwargs = {}
    for f in dataclasses.fields(cls):
        old_v = getattr(old_dc, f.name)
        new_v = getattr(new_dc, f.name)
        # 用 `is not None` 而不是真值判断,这样 0 / False / '' 等合法值不会被误判为"空"
        merged_kwargs[f.name] = new_v if new_v is not None else old_v
    return cls(**merged_kwargs)


def get_verification(prediction_id: str, db_path: DbPath) -> Optional[Verification]:
    with get_conn(db_path) as conn:
        row = conn.execute(
            "SELECT * FROM verifications WHERE prediction_id = ?",
            (prediction_id,),
        ).fetchone()
        return Verification.from_row(dict(row)) if row else None


def list_pending_verifications(
    db_path: DbPath,
    limit: int = 100,
) -> List[Verification]:
    """拉取所有 status='pending' 的验证,供批处理作业跑回测用。"""
    with get_conn(db_path) as conn:
        rows = conn.execute(
            "SELECT * FROM verifications WHERE status = 'pending' LIMIT ?",
            (limit,),
        ).fetchall()
        return [Verification.from_row(dict(r)) for r in rows]


# ---------------------------------------------------------------------------
# 组合查询
# ---------------------------------------------------------------------------

def get_prediction_with_verification(
    prediction_id: str,
    db_path: DbPath,
) -> Tuple[Optional[PredictionRecord], Optional[Verification]]:
    with get_conn(db_path) as conn:
        pred_row = conn.execute(
            "SELECT * FROM predictions WHERE prediction_id = ?",
            (prediction_id,),
        ).fetchone()
        ver_row = conn.execute(
            "SELECT * FROM verifications WHERE prediction_id = ?",
            (prediction_id,),
        ).fetchone()

    pred = PredictionRecord.from_row(dict(pred_row)) if pred_row else None
    ver = Verification.from_row(dict(ver_row)) if ver_row else None
    return pred, ver


def get_post_with_predictions(
    post_id: str,
    db_path: DbPath,
) -> Tuple[Optional[RawPost], List[PredictionRecord]]:
    """原文 + 抽出的所有预测。LLM 抽取迭代时常这样取:看原文、看看上次抽了啥。"""
    with get_conn(db_path) as conn:
        post_row = conn.execute(
            "SELECT * FROM raw_posts WHERE post_id = ?", (post_id,)
        ).fetchone()
        pred_rows = conn.execute(
            "SELECT * FROM predictions WHERE post_id = ?", (post_id,)
        ).fetchall()

    post = RawPost.from_row(dict(post_row)) if post_row else None
    preds = [PredictionRecord.from_row(dict(r)) for r in pred_rows]
    return post, preds
