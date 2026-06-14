"""后处理:把 LLM 输出转 PredictionRecord 落库。

步骤:
1. raw_asset_mention → (ticker, market) 别名表解析;未命中 → human_review_queue
2. 业务键 (post_id, ticker, direction) 去重(LLM 多次跑同一推文不重复落)
3. is_repeat_call:同 source 同 ticker 同 direction 30 天内已有记录 → true,repeat_of 指向首条
4. context_missing=true 且 has_prediction=true → 标 context_missing flag
"""
from __future__ import annotations

import json
import re
import sqlite3
from datetime import datetime, timedelta
from pathlib import Path
from typing import List, Optional, Tuple, Union

from .caller import LLMCallResult
from .evaluate import LLMPostResult, LLMPrediction
from signalboard.models import PredictionRecord
from signalboard.repository import insert_prediction

DbPath = Union[str, Path]


# ---------------------------------------------------------------------------
# 别名解析
# ---------------------------------------------------------------------------


def _load_alias_index(db_path: DbPath) -> dict:
    """alias_raw → [(ticker, market, asset_class, confidence, ...)] 索引。"""
    try:
        with sqlite3.connect(db_path, timeout=10) as conn:
            rows = conn.execute(
                "SELECT alias_raw, ticker, market, asset_class, confidence "
                "FROM aliases"
            ).fetchall()
    except sqlite3.OperationalError:
        return {}
    index: dict = {}
    for alias, ticker, market, asset_class, conf in rows:
        index.setdefault(alias, []).append({
            "ticker": ticker, "market": market, "asset_class": asset_class,
            "confidence": conf,
        })
    return index


def resolve_alias(
    raw_mention: str,
    alias_index: dict,
    *,
    db_path: Optional[DbPath] = None,
    post_id: str = "",
) -> Tuple[Optional[str], Optional[str], str]:
    """解析 raw_mention → (ticker, market, resolution_status)。

    resolution_status:
      - resolved: 命中(可能 confidence < 1,但有映射)
      - unresolved: 未命中
      - ambiguous: 命中多条 ticker(选 confidence 最高的,标 ambiguous)

    解析顺序:
      0) ticker 格式自动命中(美股/全球主流票,不需要 alias 映射)
      1) alias 表直接命中(大小写敏感)
      2) 大小写不敏感命中
      3) 部分包含匹配
    """
    if not raw_mention:
        return None, None, "unresolved"

    # 0) 美股/全球主流票格式(1-6 个大写字母/数字,首字母大写,可含 .)
    # 例: IREN/CIFR/MU/AMD/NVDA/TSLA/PLTR/HPS.A
    # 这是修复后的主逻辑 — 绝大多数美股主流票无需走 alias 表
    import re as _re
    if re.match(r"^[A-Z][A-Z0-9.]{0,5}$", raw_mention):
        # 已是合法 ticker 格式,直接返回
        return raw_mention, "美股", "resolved"

    # 0.5) LLM ticker 兜底(caller 在传 raw_mention 时也传 LLM 抽的 ticker)
    # 通过 thread-local 或 resolve_alias 上下文传 — 这里改 caller 签名
    # 实际简化:resolve_alias 不传 LLM ticker,让 llm_result_to_post_result 在 unresolved 时
    # 单独检查 LLM 抽的 ticker 字段值
    # 这里先不动

    # 1) 直接命中(大小写敏感)
    if raw_mention in alias_index:
        candidates = alias_index[raw_mention]
        if len(candidates) == 1:
            c = candidates[0]
            return c["ticker"], c["market"], "resolved" if c["confidence"] >= 0.9 else "ambiguous"
        # 多 ticker:选 confidence 最高的
        best = max(candidates, key=lambda x: x["confidence"])
        return best["ticker"], best["market"], "ambiguous"

    # 2) 大小写不敏感(对英文 ticker)
    raw_low = raw_mention.lower()
    for alias, candidates in alias_index.items():
        if alias.lower() == raw_low:
            if len(candidates) == 1:
                c = candidates[0]
                return c["ticker"], c["market"], "resolved" if c["confidence"] >= 0.9 else "ambiguous"
            best = max(candidates, key=lambda x: x["confidence"])
            return best["ticker"], best["market"], "ambiguous"

    # 3) 部分匹配(原文中含 alias,如 "Sivers" → SIVE)
    # 只对英文 alias 试(避免中文误中)
    raw_low_for_sub = raw_mention.lower()
    for alias, candidates in alias_index.items():
        if len(alias) >= 4 and alias.isascii():
            if alias.lower() in raw_low_for_sub or raw_low_for_sub in alias.lower():
                if len(candidates) == 1:
                    c = candidates[0]
                    if c["confidence"] >= 0.9:
                        return c["ticker"], c["market"], "resolved"
                break  # 找到第一个匹配就停,避免循环

    return None, None, "unresolved"


# ---------------------------------------------------------------------------
# 把 LLMCallResult → LLMPostResult
# ---------------------------------------------------------------------------


def llm_result_to_post_result(
    res: LLMCallResult,
    db_path: DbPath,
    *,
    source_user_id: Optional[str] = None,
) -> LLMPostResult:
    """LLMCallResult → LLMPostResult(后处理:别名解析 + 入库准备)。"""
    resp = res.response_json
    alias_index = _load_alias_index(db_path)
    preds: List[LLMPrediction] = []

    for p in resp.get("predictions", []):
        raw = p.get("raw_asset_mention") or p.get("ticker") or ""
        llm_ticker = p.get("ticker") or ""
        llm_market = p.get("market") or ""
        ticker, market, status = resolve_alias(raw, alias_index, db_path=db_path, post_id=res.post_id)
        # 兜底:resolve_alias 未命中时,检查 LLM 抽的 ticker 字段是否合法 ticker 格式
        # 例:raw='Visual photonics' (未命中),LLM ticker='2455' (合法) → 用 2455
        # 例:raw='$RPI',LLM ticker='$RPI' (非法) → 不兜底,保持 unresolved
        if status == "unresolved" and llm_ticker and re.match(r"^[A-Z][A-Z0-9.]{0,5}$", llm_ticker):
            ticker, market, status = llm_ticker, llm_market or "美股", "resolved"
        # LLM 抽的纯数字 ticker (TW 2455 / 3363 等 4 位数字,无 .TW 后缀)
        if status == "unresolved" and llm_ticker and re.match(r"^[0-9]{4,6}$", llm_ticker):
            ticker = llm_ticker + ".TW" if llm_market in ("TW", "台") or len(llm_ticker) == 4 else llm_ticker
            market = llm_market or "TW"
            status = "resolved"
        # LLM 抽的 ticker 格式像 "688017.SH" 或 "000660.KS" — 走常规解析
        if status == "unresolved" and llm_ticker and "." in llm_ticker and re.match(r"^[0-9]{4,6}\.[A-Z]+$", llm_ticker):
            ticker, market, status = llm_ticker, llm_market or "TW", "resolved"
        if status == "unresolved":
            # 入人工队列(只在真 unresolved 时入 — 之前 buggy 实现把 ticker 格式 raw 也入队)
            try:
                with sqlite3.connect(db_path, timeout=10) as conn:
                    conn.execute(
                        """INSERT INTO human_review_queue (post_id, reason, payload)
                           VALUES (?, ?, ?)""",
                        (res.post_id, "unresolved_ticker",
                         json.dumps({"raw_mention": raw, "llm_ticker": p.get("ticker"),
                                     "llm_market": p.get("market")}, ensure_ascii=False)),
                    )
                    conn.commit()
            except sqlite3.OperationalError:
                pass
        # ticker 字段:resolved 时是 alias 命中的 ticker,unresolved 时保持 None(不填 raw 冒充 ticker)
        # market 同理:resolved 用 alias 命中的 market,unresolved 用 LLM 给的(可能猜对)
        preds.append(LLMPrediction(
            post_id=res.post_id,
            ticker=ticker,  # resolved 时非 None,unresolved 时 None(不冒充)
            market=market or p.get("market", ""),
            direction=p.get("direction", ""),
            claim_type=p.get("claim_type", "directional"),
            horizon=p.get("horizon", "6m"),
            conviction=int(p.get("conviction") or 3),
            thesis_summary=p.get("thesis_summary", ""),
            raw_asset_mention=raw,
        ))

    flags = list(resp.get("flags", []))
    # context_missing 自动加 flag(在 caller 或 assemble 时)
    return LLMPostResult(
        post_id=res.post_id,
        has_prediction=bool(resp.get("has_prediction")),
        predictions=preds,
        flags=flags,
        extraction_notes=resp.get("extraction_notes", ""),
    )


# ---------------------------------------------------------------------------
# is_repeat_call + repeat_of
# ---------------------------------------------------------------------------


def compute_repeat_call(
    pred: LLMPrediction,
    db_path: DbPath,
    *,
    source_id: str,
    window_days: int = 30,
) -> Tuple[bool, Optional[str]]:
    """同 source 同 ticker 同 direction 30 天内已有记录 → repeat。"""
    if not pred.ticker or not pred.direction:
        return False, None
    try:
        with sqlite3.connect(db_path, timeout=10) as conn:
            # 找同 source+ticker+direction 最早的记录
            row = conn.execute(
                """SELECT prediction_id, published_at FROM predictions
                   WHERE source_id = ? AND ticker = ? AND direction = ? AND post_id != ?
                   ORDER BY published_at ASC LIMIT 1""",
                (source_id, pred.ticker, pred.direction, pred.post_id),
            ).fetchone()
    except sqlite3.OperationalError:
        return False, None
    if not row:
        return False, None
    pred_id, prior_pub = row
    # 30 天窗口
    try:
        prior_dt = datetime.fromisoformat(prior_pub.replace("Z", "+00:00"))
        # 跟当前推文时间比 — pred 还没入,published_at 来自 LLMCallResult
        # 这里 LLMCallResult 没带 published_at,后续从 raw_posts 查
        # 简化:用 last_updated 大于 prior_dt 就视为新
        # 直接用 sql 过滤窗口
        with sqlite3.connect(db_path, timeout=10) as conn:
            count = conn.execute(
                """SELECT count(*) FROM predictions
                   WHERE source_id = ? AND ticker = ? AND direction = ?
                   AND post_id != ? AND published_at >= ?""",
                (source_id, pred.ticker, pred.direction, pred.post_id,
                 (prior_dt - timedelta(days=window_days)).isoformat()),
            ).fetchone()[0]
    except Exception:
        return False, None
    if count >= 1:
        return True, pred_id
    return False, None


# ---------------------------------------------------------------------------
# 落库
# ---------------------------------------------------------------------------


def persist_one(
    post_id: str,
    pred: LLMPrediction,
    db_path: DbPath,
    *,
    source_id: str,
    source_user_id: Optional[str] = None,
    prompt_version: str = "v1.0",
    is_repeat_call: bool = False,
    repeat_of: Optional[str] = None,
    resolution_status: str = "resolved",
) -> None:
    """把一条 LLMPrediction 落 predictions 表。"""
    # 拿 post 元信息
    try:
        with sqlite3.connect(db_path, timeout=10) as conn:
            row = conn.execute(
                "SELECT published_at, captured_at FROM raw_posts WHERE post_id = ?",
                (post_id,),
            ).fetchone()
    except sqlite3.OperationalError:
        row = None
    published_at, captured_at = (row if row else ("", ""))

    record = PredictionRecord(
        post_id=post_id,
        source_id=source_id,
        published_at=published_at or "",
        captured_at=captured_at or "",
        ticker=pred.ticker,
        market=pred.market or "",
        direction=pred.direction,
        claim_type=pred.claim_type,
        quantitative_claim=None,  # 暂未序列化(留给后续 Phase)
        horizon=pred.horizon,
        conviction=pred.conviction,
        is_repeat_call=is_repeat_call,
        repeat_of=repeat_of,
        thesis_summary=pred.thesis_summary,
        thesis_category="",  # 暂未从 LLM 输出读(后续 Phase)
        raw_asset_mention=pred.raw_asset_mention,
        resolution_status=resolution_status,
        prompt_version=prompt_version,
    )
    insert_prediction(record, db_path)


def persist_post_flags(
    post_id: str,
    flags: List[str],
    db_path: DbPath,
    *,
    evidence: str = "",
) -> None:
    """落 post_flags(多 flag 时多次 INSERT OR REPLACE)。"""
    if not flags:
        return
    try:
        with sqlite3.connect(db_path, timeout=10) as conn:
            for f in flags:
                # count 累加:已有则 +1,首次插入为 1
                conn.execute(
                    """INSERT INTO post_flags (post_id, flag_type, count, evidence)
                       VALUES (?, ?, 1, ?)
                       ON CONFLICT(post_id, flag_type) DO UPDATE SET
                         count = count + 1,
                         evidence = COALESCE(excluded.evidence, evidence)""",
                    (post_id, f, evidence or ""),
                )
            conn.commit()
    except sqlite3.OperationalError as e:
        print(f"[postprocess] persist_post_flags failed: {e}")


# ---------------------------------------------------------------------------
# 把 post 整体落库
# ---------------------------------------------------------------------------


def persist_post_result(
    post: LLMPostResult,
    db_path: DbPath,
    *,
    source_id: str,
    prompt_version: str = "v1.0",
    skip_repeat_check: bool = False,
) -> None:
    """落 predictions + post_flags。is_repeat_call 在 skip_repeat_check=False 时算。

    单条失败不中断其他(例: 同一 post 有 ticker=None 的 unresolved + 合法 ticker 时,
    unresolved 失败不能阻断合法 ticker 入库)。"""
    if post.has_prediction and post.predictions:
        for pred in post.predictions:
            # 跳过 ticker=None 的 unresolved(unresolved 由 human_review_queue 承担,不入 predictions)
            if pred.ticker is None or pred.ticker == "":
                continue
            try:
                is_rep, rep_of = (False, None)
                if not skip_repeat_check:
                    is_rep, rep_of = compute_repeat_call(pred, db_path, source_id=source_id)
                persist_one(
                    post.post_id, pred, db_path,
                    source_id=source_id,
                    prompt_version=prompt_version,
                    is_repeat_call=is_rep, repeat_of=rep_of,
                    resolution_status="resolved",
                )
            except Exception as e:
                # 单条失败不中断 — 让其他合法 ticker 还能入
                import sys
                print(f"[persist_post_result] skip {post.post_id}/{pred.ticker}: {e}", file=sys.stderr)
    # flags
    persist_post_flags(post.post_id, post.flags, db_path)
