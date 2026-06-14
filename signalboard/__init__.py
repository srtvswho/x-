"""信号源记分牌系统 — 数据访问层。

v2 schema(raw_posts / predictions / verifications 三层分离)。
Source / SourceScore / RedFlag 等按设计文档分阶段补。
"""
from .db import get_conn, init_db
from .models import (
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
    compute_content_hash,
)
from .repository import (
    count_predictions_by_source,
    get_post_with_predictions,
    get_prediction,
    get_prediction_with_verification,
    get_raw_post,
    get_verification,
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

__all__ = [
    # enums
    "ClaimType",
    "Direction",
    "Horizon",
    "Market",
    "Platform",
    "VerificationStatus",
    # dataclasses
    "PriceReturns",
    "PredictionRecord",
    "QuantitativeClaim",
    "QuantitativeOutcome",
    "RawPost",
    "Verification",
    # helpers
    "compute_content_hash",
    # db
    "get_conn",
    "init_db",
    # raw_posts
    "upsert_raw_post",
    "get_raw_post",
    "list_raw_posts_by_source",
    "mark_post_deleted",
    # predictions
    "insert_prediction",
    "get_prediction",
    "list_predictions_by_source",
    "list_predictions_by_ticker",
    "list_predictions_by_post",
    "count_predictions_by_source",
    # verifications
    "upsert_verification",
    "get_verification",
    "list_pending_verifications",
    # 组合
    "get_prediction_with_verification",
    "get_post_with_predictions",
    # scraper
    "ACTOR_ID",
    "ENV_API_TOKEN",
    "FieldMap",
    "ResponseCache",
    "default_field_map",
    "fetch_account_history",
]

# scraper 走懒加载,避免 `python -m signalboard.scraper` 触发
# __init__.py 预 import 后再二次 import 产生的 RuntimeWarning
_SCRAPER_NAMES = {
    "ACTOR_ID",
    "ENV_API_TOKEN",
    "FieldMap",
    "ResponseCache",
    "default_field_map",
    "fetch_account_history",
}


def __getattr__(name):
    if name in _SCRAPER_NAMES:
        from . import scraper as _scraper
        value = getattr(_scraper, name)
        globals()[name] = value  # 缓存,后续访问不再走 __getattr__
        return value
    raise AttributeError(f"module 'signalboard' has no attribute {name!r}")


def __dir__():
    return sorted(list(globals().keys()) + list(_SCRAPER_NAMES))
