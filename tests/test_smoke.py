"""冒烟测试,纯 assert 跑,不依赖 pytest。

覆盖矩阵:
A. raw_posts 基础 CRUD
B. raw_posts 幂等 + 删帖标记不被覆盖
C. raw_posts 编辑(content_hash 变化)
D. predictions 基础 CRUD
E. predictions 业务键 UNIQUE(post_id, ticker, direction)
F. predictions FK:引用不存在的 post_id 失败
G. predictions ON DELETE RESTRICT:有引用的 post 删不掉
H. Verification 分阶段更新(r_1w 写完再写 r_1m,r_1w 不丢)
I. Verification status 推进 + pending 不回退
J. Verification quantitative_outcome 逐字段合并
K. 组合查询
L. v1→v2 schema 迁移
"""
from __future__ import annotations

import hashlib
import sqlite3
import sys
import tempfile
import uuid
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from signalboard import (
    ClaimType,
    Direction,
    Horizon,
    Market,
    Platform,
    PriceReturns,
    PredictionRecord,
    QuantitativeClaim,
    QuantitativeOutcome,
    RawPost,
    Verification,
    VerificationStatus,
    count_predictions_by_source,
    get_post_with_predictions,
    get_prediction,
    get_prediction_with_verification,
    get_raw_post,
    get_verification,
    init_db,
    insert_prediction,
    list_pending_verifications,
    list_predictions_by_post,
    list_predictions_by_source,
    list_predictions_by_ticker,
    list_raw_posts_by_source,
    mark_post_deleted,
    upsert_raw_post,
    upsert_verification,
)
from signalboard.db import CURRENT_SCHEMA_VERSION, LEGACY_V1_SCHEMA_SQL
from signalboard.models import _from_json, _to_json, compute_content_hash


# ---------------------------------------------------------------------------
# helpers
# ---------------------------------------------------------------------------

def _new_post_id() -> str:
    return f"post_{uuid.uuid4().hex[:8]}"


def make_raw_post(
    post_id: str = None,
    source_id: str = "tw_alice",
    text: str = "看好 NVDA,目标价上调",
    **kwargs,
) -> RawPost:
    if post_id is None:
        post_id = _new_post_id()
    defaults = dict(
        post_id=post_id,
        source_id=source_id,
        platform=Platform.TWITTER.value,
        published_at="2026-01-12T14:30:00+00:00",
        captured_at="2026-01-12T14:42:00+00:00",
        raw_text=text,
        raw_url=f"https://x.com/{source_id}/status/{post_id}",
    )
    defaults.update(kwargs)
    return RawPost(**defaults)


def make_prediction(
    post_id: str = None,
    ticker: str = "NVDA",
    direction: str = Direction.LONG.value,
    **kwargs,
) -> PredictionRecord:
    if post_id is None:
        post_id = _new_post_id()
    defaults = dict(
        post_id=post_id,
        source_id="tw_alice",
        published_at="2026-01-12T14:30:00+00:00",
        captured_at="2026-01-12T14:42:00+00:00",
        ticker=ticker,
        market=Market.US.value,
        direction=direction,
        claim_type=ClaimType.QUANTITATIVE.value,
        quantitative_claim=QuantitativeClaim(
            metric="fy_revenue_growth",
            predicted_value=0.55,
            consensus_at_time=0.14,
            resolution_date="2026-03-31",
        ),
        horizon=Horizon.THREE_MONTHS.value,
        conviction=4,
        thesis_summary="LLM 一句话论点",
        thesis_category="份额提升",
    )
    defaults.update(kwargs)
    return PredictionRecord(**defaults)


# ===========================================================================
# A. raw_posts 基础 CRUD
# ===========================================================================

def test_roundtrip_raw_post(db: Path) -> None:
    post = make_raw_post()
    upsert_raw_post(post, db)
    loaded = get_raw_post(post.post_id, db)
    assert loaded is not None
    assert loaded.post_id == post.post_id
    assert loaded.source_id == post.source_id
    assert loaded.platform == Platform.TWITTER.value
    assert loaded.raw_text == post.raw_text
    assert loaded.raw_url == post.raw_url
    assert loaded.is_deleted is False
    assert loaded.archive_url is None
    assert loaded.content_hash == hashlib.sha256(post.raw_text.encode("utf-8")).hexdigest()
    print("✓ test_roundtrip_raw_post")


def test_raw_post_content_hash_helper() -> None:
    """compute_content_hash 与 __post_init__ 自动算的应该一致。"""
    h1 = hashlib.sha256(b"hello world").hexdigest()
    h2 = compute_content_hash("hello world")
    p = make_raw_post(text="hello world")
    assert h1 == h2 == p.content_hash
    print("✓ test_raw_post_content_hash_helper")


def test_list_raw_posts_by_source(db: Path) -> None:
    # 用独立 source_id 避免和前面测试互相污染
    p1 = make_raw_post(post_id="lp1", source_id="tw_lista")
    p2 = make_raw_post(post_id="lp2", source_id="tw_lista")
    p3 = make_raw_post(post_id="lp3", source_id="tw_listb", published_at="2026-02-01T00:00:00+00:00")
    upsert_raw_post(p1, db)
    upsert_raw_post(p2, db)
    upsert_raw_post(p3, db)

    alice = list_raw_posts_by_source("tw_lista", db)
    assert {p.post_id for p in alice} == {"lp1", "lp2"}
    # 默认按 published_at DESC
    bob = list_raw_posts_by_source("tw_listb", db)
    assert len(bob) == 1 and bob[0].post_id == "lp3"
    print("✓ test_list_raw_posts_by_source")


def test_mark_post_deleted(db: Path) -> None:
    post = make_raw_post()
    upsert_raw_post(post, db)
    mark_post_deleted(post.post_id, db, is_deleted=True)
    assert get_raw_post(post.post_id, db).is_deleted is True
    mark_post_deleted(post.post_id, db, is_deleted=False)
    assert get_raw_post(post.post_id, db).is_deleted is False
    print("✓ test_mark_post_deleted")


# ===========================================================================
# B. raw_posts 幂等 + 删帖标记保护
# ===========================================================================

def test_upsert_raw_post_preserves_deletion(db: Path) -> None:
    """重抓同一 post_id 不应清掉 is_deleted 标记(避免重抓数据意外恢复已删原文)。"""
    post = make_raw_post()
    upsert_raw_post(post, db)
    mark_post_deleted(post.post_id, db, is_deleted=True)
    # 模拟重抓(原文/时间/URL 全相同)
    upsert_raw_post(post, db)
    loaded = get_raw_post(post.post_id, db)
    assert loaded.is_deleted is True
    print("✓ test_upsert_raw_post_preserves_deletion")


def test_upsert_raw_post_preserves_archive_url(db: Path) -> None:
    """已存档的 URL 不应被新抓数据清空(COALESCE 行为)。"""
    p1 = make_raw_post(archive_url="https://archive.example/v1")
    upsert_raw_post(p1, db)
    # 第二次 upsert 没传 archive_url
    p2 = make_raw_post(post_id=p1.post_id, archive_url=None)
    upsert_raw_post(p2, db)
    loaded = get_raw_post(p1.post_id, db)
    assert loaded.archive_url == "https://archive.example/v1"
    print("✓ test_upsert_raw_post_preserves_archive_url")


# ===========================================================================
# C. 编辑检测(content_hash 变化)
# ===========================================================================

def test_upsert_raw_post_detects_edit(db: Path) -> None:
    """编辑后 raw_text 和 content_hash 都会变 — 给编辑检测用。"""
    p1 = make_raw_post(text="原文 v1")
    upsert_raw_post(p1, db)
    assert get_raw_post(p1.post_id, db).content_hash == compute_content_hash("原文 v1")
    p2 = make_raw_post(post_id=p1.post_id, text="原文 v2 已编辑")
    upsert_raw_post(p2, db)
    loaded = get_raw_post(p1.post_id, db)
    assert loaded.raw_text == "原文 v2 已编辑"
    assert loaded.content_hash == compute_content_hash("原文 v2 已编辑")
    assert loaded.content_hash != compute_content_hash("原文 v1")
    print("✓ test_upsert_raw_post_detects_edit")


# ===========================================================================
# D. predictions 基础 CRUD
# ===========================================================================

def test_roundtrip_prediction(db: Path) -> None:
    post = make_raw_post()
    upsert_raw_post(post, db)
    pred = make_prediction(post_id=post.post_id)
    insert_prediction(pred, db)
    loaded = get_prediction(pred.prediction_id, db)
    assert loaded is not None
    assert loaded.post_id == post.post_id
    assert loaded.source_id == "tw_alice"
    assert loaded.ticker == "NVDA"
    assert loaded.market == Market.US.value
    assert loaded.direction == Direction.LONG.value
    assert loaded.claim_type == ClaimType.QUANTITATIVE.value
    assert loaded.horizon == Horizon.THREE_MONTHS.value
    assert loaded.conviction == 4
    # 嵌套对象往返
    assert loaded.quantitative_claim is not None
    assert loaded.quantitative_claim.metric == "fy_revenue_growth"
    assert loaded.quantitative_claim.predicted_value == 0.55
    assert loaded.quantitative_claim.consensus_at_time == 0.14
    assert loaded.quantitative_claim.resolution_date == "2026-03-31"
    print("✓ test_roundtrip_prediction")


def test_list_predictions_by_source_and_ticker(db: Path) -> None:
    # 独立 source_id 避免和前面测试冲突
    p_a1 = make_raw_post(post_id="lpa1", source_id="tw_lpsrca")
    p_a2 = make_raw_post(post_id="lpa2", source_id="tw_lpsrca")
    p_b1 = make_raw_post(post_id="lpb1", source_id="tw_lpsrcb")
    upsert_raw_post(p_a1, db)
    upsert_raw_post(p_a2, db)
    upsert_raw_post(p_b1, db)
    insert_prediction(make_prediction(post_id="lpa1", ticker="LPSRCA", source_id="tw_lpsrca"), db)
    insert_prediction(make_prediction(post_id="lpa2", ticker="LPSRCB", source_id="tw_lpsrca"), db)
    insert_prediction(make_prediction(post_id="lpb1", ticker="LPSRCA", source_id="tw_lpsrcb"), db)

    alice = list_predictions_by_source("tw_lpsrca", db)
    assert {p.ticker for p in alice} == {"LPSRCA", "LPSRCB"}

    rpi = list_predictions_by_ticker("LPSRCA", db)
    assert {p.source_id for p in rpi} == {"tw_lpsrca", "tw_lpsrcb"}

    assert count_predictions_by_source("tw_lpsrca", db) == 2
    assert count_predictions_by_source("tw_lpsrcb", db) == 1
    print("✓ test_list_predictions_by_source_and_ticker")


def test_null_optional_fields(db: Path) -> None:
    """thematic 类型不带 quantitative_claim,minimal 记录能落库。"""
    post = make_raw_post(post_id="tweet_thematic_001")
    upsert_raw_post(post, db)
    pred = PredictionRecord(
        post_id=post.post_id, source_id=post.source_id,
        published_at=post.published_at, captured_at=post.captured_at,
        ticker="NVDA", market=Market.US.value,
        direction=Direction.LONG.value, claim_type=ClaimType.THEMATIC.value,
        horizon=Horizon.SIX_MONTHS.value, conviction=2,
        thesis_summary="叙事看好", thesis_category="叙事",
    )
    insert_prediction(pred, db)
    loaded = get_prediction(pred.prediction_id, db)
    assert loaded.quantitative_claim is None
    assert loaded.repeat_of is None
    assert loaded.claim_type == ClaimType.THEMATIC.value
    print("✓ test_null_optional_fields")


# ===========================================================================
# E. 业务键 UNIQUE(post_id, ticker, direction)
# ===========================================================================

def test_same_post_multiple_tickers(db: Path) -> None:
    """一条原文可抽出多个 ticker 的预测,均能插入。"""
    post = make_raw_post(post_id="tweet_multi_001")
    upsert_raw_post(post, db)
    p1 = make_prediction(post_id=post.post_id, ticker="NVDA")
    p2 = make_prediction(post_id=post.post_id, ticker="AMD")
    insert_prediction(p1, db)
    insert_prediction(p2, db)
    rows = list_predictions_by_post(post.post_id, db)
    assert len(rows) == 2
    assert {r.ticker for r in rows} == {"NVDA", "AMD"}
    print("✓ test_same_post_multiple_tickers")


def test_same_post_same_ticker_different_direction(db: Path) -> None:
    """同一 (post_id, ticker) 不同 direction 也是独立预测。"""
    post = make_raw_post()
    upsert_raw_post(post, db)
    long = make_prediction(post_id=post.post_id, ticker="NVDA", direction=Direction.LONG.value)
    short = make_prediction(post_id=post.post_id, ticker="NVDA", direction=Direction.SHORT.value)
    insert_prediction(long, db)
    insert_prediction(short, db)
    rows = list_predictions_by_post(post.post_id, db)
    assert len(rows) == 2
    assert {r.direction for r in rows} == {"long", "short"}
    print("✓ test_same_post_same_ticker_different_direction")


def test_duplicate_business_key_upserts(db: Path) -> None:
    """(post_id, ticker, direction) 重复时 upsert(LLM 重跑同一推文不报错,只覆盖)。

    v3 行为(2026-06-12):insert_prediction 改 ON CONFLICT DO UPDATE。
    """
    post = make_raw_post()
    upsert_raw_post(post, db)
    p1 = make_prediction(post_id=post.post_id, ticker="NVDA", direction=Direction.LONG.value, conviction=3)
    insert_prediction(p1, db)
    # 改 conviction 再插,应 upsert
    p2 = make_prediction(post_id=post.post_id, ticker="NVDA", direction=Direction.LONG.value, conviction=5)
    insert_prediction(p2, db)
    import sqlite3 as _sq
    with _sq.connect(db) as conn:
        rows = list(conn.execute("SELECT conviction FROM predictions WHERE post_id = ? AND ticker = 'NVDA'", (post.post_id,)))
    assert len(rows) == 1, f"expected 1 row, got {len(rows)}"
    assert rows[0][0] == 5, f"expected upsert to conviction=5, got {rows[0][0]}"
    print("✓ test_duplicate_business_key_upserts")


# ===========================================================================
# F. FK:post_id 必须存在
# ===========================================================================

def test_fk_post_id_required(db: Path) -> None:
    pred = make_prediction(post_id="does-not-exist")
    try:
        insert_prediction(pred, db)
    except sqlite3.IntegrityError:
        print("✓ test_fk_post_id_required")
        return
    raise AssertionError("expected IntegrityError on FK violation")


# ===========================================================================
# G. ON DELETE RESTRICT:有引用的 post 删不掉
# ===========================================================================

def test_cannot_delete_post_with_predictions(db: Path) -> None:
    post = make_raw_post()
    upsert_raw_post(post, db)
    pred = make_prediction(post_id=post.post_id)
    insert_prediction(pred, db)

    with sqlite3.connect(db) as conn:
        conn.execute("PRAGMA foreign_keys = ON")
        try:
            conn.execute("DELETE FROM raw_posts WHERE post_id = ?", (post.post_id,))
            conn.commit()
        except sqlite3.IntegrityError:
            print("✓ test_cannot_delete_post_with_predictions")
            return
    raise AssertionError("expected IntegrityError on ON DELETE RESTRICT")


# ===========================================================================
# H. Verification 分阶段更新
# ===========================================================================

def test_upsert_preserves_r1w_when_adding_r1m(db: Path) -> None:
    """核心场景:先写 r_1w,再写 r_1m,r_1w 不丢。"""
    post = make_raw_post()
    upsert_raw_post(post, db)
    pred = make_prediction(post_id=post.post_id)
    insert_prediction(pred, db)

    # 第 1 轮:1w 周期成熟
    upsert_verification(
        Verification(
            prediction_id=pred.prediction_id,
            status="pending",
            entry_price_basis="captured_at 后下一分钟均价",
            price_returns=PriceReturns(r_1w=0.05, benchmark_1w=0.01),
        ),
        db,
    )
    # 第 2 轮:1m 周期成熟(r_1w 不在这次传入)
    upsert_verification(
        Verification(
            prediction_id=pred.prediction_id,
            status="pending",
            price_returns=PriceReturns(r_1m=0.12, benchmark_1m=0.03),
        ),
        db,
    )

    loaded = get_verification(pred.prediction_id, db)
    assert loaded is not None
    pr = loaded.price_returns
    assert pr is not None
    assert pr.r_1w == 0.05, "r_1w 不应被 r_1m 写入清空"
    assert pr.benchmark_1w == 0.01, "benchmark_1w 也不应丢"
    assert pr.r_1m == 0.12
    assert pr.benchmark_1m == 0.03
    # 旧 entry_price_basis 保留
    assert loaded.entry_price_basis == "captured_at 后下一分钟均价"
    # status 仍 pending(两次都没改)
    assert loaded.status == "pending"
    print("✓ test_upsert_preserves_r1w_when_adding_r1m")


def test_upsert_preserves_zero_value(db: Path) -> None:
    """0 / False / 0.0 是合法值,不应被当作"空"误判。"""
    post = make_raw_post()
    upsert_raw_post(post, db)
    pred = make_prediction(post_id=post.post_id)
    insert_prediction(pred, db)

    upsert_verification(
        Verification(
            prediction_id=pred.prediction_id,
            price_returns=PriceReturns(r_1w=0.0, r_1m=0.0),
            entry_price_basis="x",
        ),
        db,
    )
    # 再写一次 r_3m,前两个 0 应保留
    upsert_verification(
        Verification(
            prediction_id=pred.prediction_id,
            price_returns=PriceReturns(r_3m=0.20),
        ),
        db,
    )
    loaded = get_verification(pred.prediction_id, db)
    assert loaded.price_returns.r_1w == 0.0
    assert loaded.price_returns.r_1m == 0.0
    assert loaded.price_returns.r_3m == 0.20
    print("✓ test_upsert_preserves_zero_value")


# ===========================================================================
# I. status 推进 + pending 不回退
# ===========================================================================

def test_upsert_advances_status(db: Path) -> None:
    """pending → verified_hit,中间 r_1w 写入不应改变 status。"""
    post = make_raw_post()
    upsert_raw_post(post, db)
    pred = make_prediction(post_id=post.post_id)
    insert_prediction(pred, db)

    upsert_verification(
        Verification(prediction_id=pred.prediction_id, status="pending",
                     price_returns=PriceReturns(r_1w=0.05), entry_price_basis="x"),
        db,
    )
    assert get_verification(pred.prediction_id, db).status == "pending"

    upsert_verification(
        Verification(
            prediction_id=pred.prediction_id,
            status=VerificationStatus.VERIFIED_HIT.value,
            price_returns=PriceReturns(r_1m=0.12),
        ),
        db,
    )
    loaded = get_verification(pred.prediction_id, db)
    assert loaded.status == "verified_hit"
    assert loaded.price_returns.r_1w == 0.05  # 之前的 r_1w 还在
    assert loaded.price_returns.r_1m == 0.12
    print("✓ test_upsert_advances_status")


def test_upsert_status_pending_does_not_revert(db: Path) -> None:
    """状态推进到 verified_hit 后,再写 status=pending 不应回退。"""
    post = make_raw_post()
    upsert_raw_post(post, db)
    pred = make_prediction(post_id=post.post_id)
    insert_prediction(pred, db)

    upsert_verification(
        Verification(prediction_id=pred.prediction_id,
                     status=VerificationStatus.VERIFIED_HIT.value,
                     entry_price_basis="x"),
        db,
    )
    # 后续 r_3m 来了,status 默认是 pending,但不应回退
    upsert_verification(
        Verification(prediction_id=pred.prediction_id,
                     status="pending",
                     price_returns=PriceReturns(r_3m=0.20)),
        db,
    )
    loaded = get_verification(pred.prediction_id, db)
    assert loaded.status == "verified_hit", "不应被 pending 回退"
    assert loaded.price_returns.r_3m == 0.20  # r_3m 该填还是填
    print("✓ test_upsert_status_pending_does_not_revert")


# ===========================================================================
# J. quantitative_outcome 逐字段合并
# ===========================================================================

def test_upsert_merges_quantitative_outcome(db: Path) -> None:
    post = make_raw_post()
    upsert_raw_post(post, db)
    pred = make_prediction(post_id=post.post_id)
    insert_prediction(pred, db)

    # 1 轮:actual 出来了
    upsert_verification(
        Verification(
            prediction_id=pred.prediction_id, status="pending",
            entry_price_basis="x",
            quantitative_outcome=QuantitativeOutcome(actual=0.58),
        ),
        db,
    )
    # 2 轮:error / beat_consensus 算出来了
    upsert_verification(
        Verification(
            prediction_id=pred.prediction_id,
            status=VerificationStatus.VERIFIED_HIT.value,
            quantitative_outcome=QuantitativeOutcome(
                error_vs_prediction=0.03,
                error_vs_consensus=0.44,
                beat_consensus=True,
            ),
        ),
        db,
    )
    qo = get_verification(pred.prediction_id, db).quantitative_outcome
    assert qo is not None
    assert qo.actual == 0.58
    assert qo.error_vs_prediction == 0.03
    assert qo.error_vs_consensus == 0.44
    assert qo.beat_consensus is True
    print("✓ test_upsert_merges_quantitative_outcome")


# ===========================================================================
# K. 组合查询
# ===========================================================================

def test_get_prediction_with_verification(db: Path) -> None:
    post = make_raw_post()
    upsert_raw_post(post, db)
    pred = make_prediction(post_id=post.post_id)
    insert_prediction(pred, db)
    p, v = get_prediction_with_verification(pred.prediction_id, db)
    assert p is not None and v is None
    upsert_verification(
        Verification(prediction_id=pred.prediction_id, status="pending",
                     entry_price_basis="x"),
        db,
    )
    p, v = get_prediction_with_verification(pred.prediction_id, db)
    assert p is not None and v is not None
    print("✓ test_get_prediction_with_verification")


def test_get_post_with_predictions(db: Path) -> None:
    post = make_raw_post()
    upsert_raw_post(post, db)
    insert_prediction(make_prediction(post_id=post.post_id, ticker="NVDA"), db)
    insert_prediction(make_prediction(post_id=post.post_id, ticker="AMD"), db)
    loaded_post, preds = get_post_with_predictions(post.post_id, db)
    assert loaded_post is not None
    assert loaded_post.post_id == post.post_id
    assert {p.ticker for p in preds} == {"NVDA", "AMD"}
    print("✓ test_get_post_with_predictions")


def test_list_pending_verifications(db: Path) -> None:
    p1 = make_raw_post(post_id="p_p1")
    p2 = make_raw_post(post_id="p_p2")
    upsert_raw_post(p1, db)
    upsert_raw_post(p2, db)
    pred1 = make_prediction(post_id="p_p1")
    pred2 = make_prediction(post_id="p_p2")
    insert_prediction(pred1, db)
    insert_prediction(pred2, db)
    upsert_verification(
        Verification(prediction_id=pred1.prediction_id, status="pending",
                     entry_price_basis="x"),
        db,
    )
    upsert_verification(
        Verification(prediction_id=pred2.prediction_id,
                     status=VerificationStatus.VERIFIED_HIT.value,
                     entry_price_basis="x"),
        db,
    )
    pending = list_pending_verifications(db)
    pending_ids = {p.prediction_id for p in pending}
    assert pred1.prediction_id in pending_ids
    assert pred2.prediction_id not in pending_ids
    print("✓ test_list_pending_verifications")


def test_json_helpers() -> None:
    qc = QuantitativeClaim(metric="x", predicted_value=0.1)
    raw = _to_json(qc)
    assert raw is not None
    rt = _from_json(QuantitativeClaim, raw)
    assert isinstance(rt, QuantitativeClaim)
    assert rt.metric == "x" and rt.predicted_value == 0.1
    assert _to_json(None) is None
    assert _from_json(QuantitativeClaim, None) is None
    print("✓ test_json_helpers")


# ===========================================================================
# L. v1 → v2 迁移
# ===========================================================================

def test_migrate_v1_to_v2(tmp_dir: Path) -> None:
    """模拟 v1 库 → 跑 init_db 升级 → 验证表结构 + 数据完整迁移。"""
    db = tmp_dir / "v1.db"
    with sqlite3.connect(db) as conn:
        conn.executescript(LEGACY_V1_SCHEMA_SQL)
        conn.execute(
            """INSERT INTO predictions (
                prediction_id, source_id, published_at, captured_at,
                raw_url, raw_text, archive_url, is_deleted,
                ticker, market, direction, claim_type, quantitative_claim,
                horizon, conviction, is_repeat_call, repeat_of,
                thesis_summary, thesis_category
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            ("pred1", "tw_alice", "2026-01-01T00:00:00+00:00", "2026-01-01T00:01:00+00:00",
             "https://x.com/alice/1", "NVDA 看多,目标价上调", "https://archive/1", 0,
             "NVDA", "US", "long", "directional", None,
             "1m", 3, 0, None, "看好 AI 芯片", "份额提升"),
        )
        conn.execute(
            """INSERT INTO predictions (
                prediction_id, source_id, published_at, captured_at,
                raw_url, raw_text, archive_url, is_deleted,
                ticker, market, direction, claim_type, quantitative_claim,
                horizon, conviction, is_repeat_call, repeat_of,
                thesis_summary, thesis_category
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            ("pred2", "tw_bob", "2026-01-02T00:00:00+00:00", "2026-01-02T00:01:00+00:00",
             "https://x.com/bob/1", "AMD 也不错", None, 0,
             "AMD", "US", "long", "directional", None,
             "1m", 3, 0, None, "AMD 也看好", "份额提升"),
        )
        conn.commit()

    # 升级
    init_db(db)

    with sqlite3.connect(db) as conn:
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA foreign_keys = ON")

        # user_version 升级到 2
        ver = conn.execute("PRAGMA user_version").fetchone()[0]
        assert ver == CURRENT_SCHEMA_VERSION == 3

        # predictions 表结构变了
        cols = {row[1] for row in conn.execute("PRAGMA table_info(predictions)").fetchall()}
        assert "raw_text" not in cols
        assert "raw_url" not in cols
        assert "archive_url" not in cols
        assert "is_deleted" not in cols
        assert "post_id" in cols

        # raw_posts 表存在并保留了原文
        posts = list(conn.execute("SELECT * FROM raw_posts").fetchall())
        assert len(posts) == 2
        post_by_id = {p["post_id"]: p for p in posts}
        # post_id 用 prediction_id 兼任
        assert set(post_by_id) == {"pred1", "pred2"}
        p1 = post_by_id["pred1"]
        assert p1["raw_text"] == "NVDA 看多,目标价上调"
        assert p1["raw_url"] == "https://x.com/alice/1"
        assert p1["archive_url"] == "https://archive/1"
        assert p1["platform"] == "unknown"  # v1 没记,占位
        assert p1["content_hash"] == compute_content_hash("NVDA 看多,目标价上调")
        assert p1["is_deleted"] == 0

        # 旧预测数据完整迁移
        preds = list(conn.execute("SELECT * FROM predictions").fetchall())
        assert len(preds) == 2
        for p in preds:
            assert p["post_id"] == p["prediction_id"]  # 迁移时两者相等
            assert p["source_id"] in {"tw_alice", "tw_bob"}

        # 迁移后,业务键 UNIQUE 生效
        try:
            conn.execute(
                """INSERT INTO predictions (
                    prediction_id, post_id, source_id, published_at, captured_at,
                    ticker, market, direction, claim_type, quantitative_claim,
                    horizon, conviction, is_repeat_call, repeat_of,
                    thesis_summary, thesis_category
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                ("pred1_dup", "pred1", "tw_alice", "2026-01-01T00:00:00+00:00",
                 "2026-01-01T00:01:00+00:00", "NVDA", "US", "long", "directional",
                 None, "1m", 3, 0, None, "dup", "dup"),
            )
        except sqlite3.IntegrityError:
            pass
        else:
            raise AssertionError("expected IntegrityError on duplicate after migration")

        # ON DELETE RESTRICT 也已生效:有 prediction 引用的 post 删不掉
        try:
            conn.execute("DELETE FROM raw_posts WHERE post_id = ?", ("pred1",))
            conn.commit()
        except sqlite3.IntegrityError:
            print("✓ test_migrate_v1_to_v2")
            return
    raise AssertionError("expected IntegrityError on delete restricted by FK")


def test_init_db_idempotent(db: Path) -> None:
    """重复调用 init_db 不应出错(幂等)。"""
    init_db(db)
    init_db(db)
    init_db(db)
    # user_version 仍是 2
    with sqlite3.connect(db) as conn:
        ver = conn.execute("PRAGMA user_version").fetchone()[0]
    assert ver == CURRENT_SCHEMA_VERSION
    print("✓ test_init_db_idempotent")


# ===========================================================================
# main
# ===========================================================================

def main() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        tmp_dir = Path(tmp)
        db = tmp_dir / "test.db"
        init_db(db)

        # A
        test_roundtrip_raw_post(db)
        test_raw_post_content_hash_helper()
        test_list_raw_posts_by_source(db)
        test_mark_post_deleted(db)
        # B
        test_upsert_raw_post_preserves_deletion(db)
        test_upsert_raw_post_preserves_archive_url(db)
        # C
        test_upsert_raw_post_detects_edit(db)
        # D
        test_roundtrip_prediction(db)
        test_list_predictions_by_source_and_ticker(db)
        test_null_optional_fields(db)
        # E
        test_same_post_multiple_tickers(db)
        test_same_post_same_ticker_different_direction(db)
        test_duplicate_business_key_upserts(db)
        # F
        test_fk_post_id_required(db)
        # G
        test_cannot_delete_post_with_predictions(db)
        # H
        test_upsert_preserves_r1w_when_adding_r1m(db)
        test_upsert_preserves_zero_value(db)
        # I
        test_upsert_advances_status(db)
        test_upsert_status_pending_does_not_revert(db)
        # J
        test_upsert_merges_quantitative_outcome(db)
        # K
        test_get_prediction_with_verification(db)
        test_get_post_with_predictions(db)
        test_list_pending_verifications(db)
        test_json_helpers()
        # L
        test_migrate_v1_to_v2(tmp_dir)
        test_init_db_idempotent(db)

    print("\nAll tests passed ✅")


if __name__ == "__main__":
    main()
