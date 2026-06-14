"""数据模型。

架构(从下到上):
    raw_posts         原始内容层,平台抓到的 post/tweet 原文 + API 原始 JSON
        ↑ (post_id)
    predictions       抽取层,一条原文可抽 N 条(对多标的)
        ↑ (prediction_id)
    verifications     验证层,可分阶段更新(r_1w 跑完一次,r_1m 跑完再写)

RawPost 与 PredictionRecord 分离的设计意图:
- LLM 抽取 prompt 多轮迭代时,可"删掉抽取结果保留原料",对同批原文重跑
- 删帖检测 (is_deleted) 和编辑检测 (content_hash 变化) 作用在 raw_posts 层
- 同一原文对不同 ticker 的预测可共存 (UNIQUE(post_id, ticker, direction))
"""
from __future__ import annotations

import hashlib
import json
import uuid
from dataclasses import asdict, dataclass, field, is_dataclass
from enum import Enum
from typing import Any, Optional


# ---------------------------------------------------------------------------
# Enums
# ---------------------------------------------------------------------------

class Market(str, Enum):
    US = "US"
    A_SHARE = "A"
    HK = "HK"
    JP = "JP"
    CRYPTO = "crypto"


class Direction(str, Enum):
    LONG = "long"
    SHORT = "short"
    NEUTRAL = "neutral"


class ClaimType(str, Enum):
    """claim_type 三档决定评分权重:
    quantitative 最高质量(可与共识对比);
    directional 次之(只能用价格验证);
    thematic 仅作叙事风向参考,不计入研究分。
    """
    QUANTITATIVE = "quantitative"
    DIRECTIONAL = "directional"
    THEMATIC = "thematic"


class Horizon(str, Enum):
    ONE_WEEK = "1w"
    ONE_MONTH = "1m"
    THREE_MONTHS = "3m"
    SIX_MONTHS = "6m"
    EVENT_DRIVEN = "event_driven"


class VerificationStatus(str, Enum):
    PENDING = "pending"
    VERIFIED_HIT = "verified_hit"
    VERIFIED_MISS = "verified_miss"
    EXPIRED = "expired"
    UNVERIFIABLE = "unverifiable"


class Platform(str, Enum):
    TWITTER = "twitter"
    ZHIHU = "zhihu"
    REDDIT = "reddit"
    SUBSTACK = "substack"
    XUEQIU = "xueqiu"
    UNKNOWN = "unknown"


# ---------------------------------------------------------------------------
# 嵌套结构
# ---------------------------------------------------------------------------

@dataclass
class QuantitativeClaim:
    metric: str
    predicted_value: float
    consensus_at_time: Optional[float] = None
    actual_value: Optional[float] = None
    resolution_date: Optional[str] = None


@dataclass
class PriceReturns:
    """价格收益。顶层字段可选,允许分阶段填写(r_1w 跑完先写一次,r_1m 跑完再写)。"""
    r_1w: Optional[float] = None
    r_1m: Optional[float] = None
    r_3m: Optional[float] = None
    benchmark_1w: Optional[float] = None
    benchmark_1m: Optional[float] = None
    benchmark_3m: Optional[float] = None
    sector_etf_1m: Optional[float] = None
    excess_1m: Optional[float] = None


@dataclass
class QuantitativeOutcome:
    actual: Optional[float] = None
    error_vs_prediction: Optional[float] = None
    error_vs_consensus: Optional[float] = None
    beat_consensus: Optional[bool] = None


# ---------------------------------------------------------------------------
# 原始内容层
# ---------------------------------------------------------------------------

@dataclass
class RawPost:
    """平台抓到的 post/tweet/帖子原样存档。
    业务键:post_id(平台原生 ID),重抓时 upsert 幂等。
    """

    post_id: str                                 # 平台原生 ID,主键
    source_id: str
    platform: str                                # Platform enum value
    published_at: str
    captured_at: str
    raw_text: str
    raw_url: str = ""
    raw_json: Optional[str] = None               # API 返回完整 JSON 字符串
    content_hash: str = ""                       # sha256(raw_text),hex
    is_deleted: bool = False                     # 删帖检测标记
    archive_url: Optional[str] = None

    def __post_init__(self) -> None:
        # 默认空时自动算;若调用方传了值(测试/迁移场景)则尊重其值
        if not self.content_hash and self.raw_text:
            self.content_hash = hashlib.sha256(self.raw_text.encode("utf-8")).hexdigest()

    def to_row(self) -> dict[str, Any]:
        return {
            "post_id": self.post_id,
            "source_id": self.source_id,
            "platform": self.platform,
            "published_at": self.published_at,
            "captured_at": self.captured_at,
            "raw_text": self.raw_text,
            "raw_url": self.raw_url,
            "raw_json": self.raw_json,
            "content_hash": self.content_hash,
            "is_deleted": int(self.is_deleted),
            "archive_url": self.archive_url,
        }

    @classmethod
    def from_row(cls, row: dict[str, Any]) -> "RawPost":
        return cls(
            post_id=row["post_id"],
            source_id=row["source_id"],
            platform=row["platform"],
            published_at=row["published_at"],
            captured_at=row["captured_at"],
            raw_text=row["raw_text"],
            raw_url=row["raw_url"],
            raw_json=row["raw_json"],
            content_hash=row["content_hash"],
            is_deleted=bool(row["is_deleted"]),
            archive_url=row["archive_url"],
        )


# ---------------------------------------------------------------------------
# 抽取层
# ---------------------------------------------------------------------------

@dataclass
class PredictionRecord:
    """一条原文可抽出多条 PredictionRecord(对多标的)。
    业务键:UNIQUE(post_id, ticker, direction)。
    source_id / published_at / captured_at 是冗余(同 raw_post),
    保留它们是为了避免常见查询时的频繁 join。
    """

    prediction_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    post_id: str = ""
    source_id: str = ""
    published_at: str = ""
    captured_at: str = ""

    ticker: str = ""
    market: str = ""
    direction: str = ""
    claim_type: str = ""
    quantitative_claim: Optional[QuantitativeClaim] = None
    horizon: str = ""
    conviction: int = 3
    is_repeat_call: bool = False
    repeat_of: Optional[str] = None
    thesis_summary: str = ""
    thesis_category: str = ""
    # v3 字段(LLM 抽取层产出)
    raw_asset_mention: str = ""               # LLM 输出的原文写法(可能跟 ticker 不同)
    resolution_status: str = "resolved"        # resolved | unresolved
    context_tickers: List[str] = field(default_factory=list)  # 看到的语境标的(未入 predictions 但可审计)
    hedged: bool = False                       # 是否有对冲措辞(对 conviction 有约束)
    prompt_version: str = ""                   # LLM 抽取用的 prompt 版本
    extraction_notes: str = ""                 # LLM 边界判定说明

    def to_row(self) -> dict[str, Any]:
        return {
            "prediction_id": self.prediction_id,
            "post_id": self.post_id,
            "source_id": self.source_id,
            "published_at": self.published_at,
            "captured_at": self.captured_at,
            "ticker": self.ticker,
            "market": self.market,
            "direction": self.direction,
            "claim_type": self.claim_type,
            "quantitative_claim": _to_json(self.quantitative_claim),
            "horizon": self.horizon,
            "conviction": self.conviction,
            "is_repeat_call": int(self.is_repeat_call),
            "repeat_of": self.repeat_of,
            "thesis_summary": self.thesis_summary,
            "thesis_category": self.thesis_category,
            "raw_asset_mention": self.raw_asset_mention,
            "resolution_status": self.resolution_status,
            "context_tickers": _to_json(self.context_tickers) if self.context_tickers else None,
            "hedged": int(self.hedged),
            "prompt_version": self.prompt_version,
            "extraction_notes": self.extraction_notes,
        }

    @classmethod
    def from_row(cls, row: dict[str, Any]) -> "PredictionRecord":
        return cls(
            prediction_id=row["prediction_id"],
            post_id=row["post_id"],
            source_id=row["source_id"],
            published_at=row["published_at"],
            captured_at=row["captured_at"],
            ticker=row["ticker"],
            market=row["market"],
            direction=row["direction"],
            claim_type=row["claim_type"],
            quantitative_claim=_from_json(QuantitativeClaim, row["quantitative_claim"]),
            horizon=row["horizon"],
            conviction=row["conviction"],
            is_repeat_call=bool(row["is_repeat_call"]),
            repeat_of=row["repeat_of"],
            thesis_summary=row["thesis_summary"],
            thesis_category=row["thesis_category"],
            raw_asset_mention=row.get("raw_asset_mention") or "",
            resolution_status=row.get("resolution_status") or "resolved",
            context_tickers=_from_json(list, row.get("context_tickers")) if row.get("context_tickers") else [],
            hedged=bool(row.get("hedged", 0)),
            prompt_version=row.get("prompt_version") or "",
            extraction_notes=row.get("extraction_notes") or "",
        )


# ---------------------------------------------------------------------------
# 验证层
# ---------------------------------------------------------------------------

@dataclass
class Verification:
    """每条 PredictionRecord 最多一条 Verification。
    1:1 关系。可分阶段更新(merge 语义,非空字段才覆盖)。
    """

    prediction_id: str
    status: str = "pending"
    price_returns: Optional[PriceReturns] = None
    entry_price_basis: str = ""
    quantitative_outcome: Optional[QuantitativeOutcome] = None
    verified_at: Optional[str] = None

    def to_row(self) -> dict[str, Any]:
        return {
            "prediction_id": self.prediction_id,
            "status": self.status,
            "price_returns": _to_json(self.price_returns),
            "entry_price_basis": self.entry_price_basis,
            "quantitative_outcome": _to_json(self.quantitative_outcome),
            "verified_at": self.verified_at,
        }

    @classmethod
    def from_row(cls, row: dict[str, Any]) -> "Verification":
        return cls(
            prediction_id=row["prediction_id"],
            status=row["status"],
            price_returns=_from_json(PriceReturns, row["price_returns"]),
            entry_price_basis=row["entry_price_basis"],
            quantitative_outcome=_from_json(QuantitativeOutcome, row["quantitative_outcome"]),
            verified_at=row["verified_at"],
        )


# ---------------------------------------------------------------------------
# helpers
# ---------------------------------------------------------------------------

def _to_json(obj: Any) -> Optional[str]:
    if obj is None:
        return None
    if isinstance(obj, (list, tuple, dict, str, int, float, bool)):
        return json.dumps(obj, ensure_ascii=False, sort_keys=True)
    if is_dataclass(obj):
        return json.dumps(asdict(obj), ensure_ascii=False, sort_keys=True)
    return json.dumps(obj, ensure_ascii=False)


def _from_json(cls: type, raw: Optional[str]) -> Any:
    if raw is None or raw == "":
        return None
    loaded = json.loads(raw)
    # 原始类型(list/dict/str/int/float/bool)直接返回
    if cls in (list, dict, str, int, float, bool) or cls is Any:
        return loaded
    # dataclass 类用 kwargs 构造
    if is_dataclass(cls):
        return cls(**loaded)
    # 其他(cls 是 type 但不是 dataclass):尝试直接当 list 元素用
    if isinstance(loaded, list):
        return loaded
    return loaded


def compute_content_hash(text: str) -> str:
    """外部需要重新算 hash 时(比如编辑检测)用这个,保证与 RawPost.__post_init__ 一致。"""
    return hashlib.sha256(text.encode("utf-8")).hexdigest()
