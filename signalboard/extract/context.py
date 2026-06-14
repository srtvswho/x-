"""上下文拼装器(R11)。

规则:
  - 自线程(回复自己/引用自己):按 conversationId 拼成完整线程,整体抽取一次
  - 引用他人:正文 + quote 字段被引全文一起给 LLM
  - 回复他人:仅本人正文(父推文不在库中),无法判断指代时标 context_missing=true
  - 转推:跳过
"""
from __future__ import annotations

import json
import sqlite3
from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Optional, Union

DbPath = Union[str, Path]


@dataclass
class AssembledContext:
    """一条抽取引擎的输入单元。"""
    anchor_post_id: str           # 抽取结果挂到的 post_id(线程首条 / 引用者 / 单独)
    anchor_raw_text: str          # 主推文正文
    quote_full_text: Optional[str] = None    # 被引全文(若主推是 quote)
    parent_in_library: bool = False          # 父推文是否在本 db 中
    context_missing: bool = False            # 无法判断指代(回信而父不在库)
    self_thread_post_ids: List[str] = field(default_factory=list)  # 自线程其他 post_id
    is_retweet: bool = False                 # 转推(直接跳过)


# ---------------------------------------------------------------------------
# 辅助
# ---------------------------------------------------------------------------


def _has_field(item: dict, field: str) -> bool:
    return field in item and item[field] is not None




def _get_quoted_status_id(item: dict) -> Optional[str]:
    """apidojo:quotedStatusId / quotedTweetId / quotedId."""
    for k in ("quotedStatusId", "quotedTweetId", "quotedId", "quoted_status_id"):
        v = item.get(k)
        if v:
            return str(v)
    # 也可能在 quotedTweet 内部
    q = item.get("quotedTweet") or item.get("quoted_tweet")
    if isinstance(q, dict):
        return str(q.get("id") or q.get("tweetId") or q.get("restId") or "")
    return None
def _is_retweet(item: dict) -> bool:
    """apidojo 的 retweet 通常有 isRetweet=True 或 retweeted_status_id 字段。"""
    return bool(item.get("isRetweet")) or bool(item.get("retweetedStatusId"))


def _is_quote(item: dict) -> bool:
    return bool(item.get("isQuote"))


def _is_reply(item: dict) -> bool:
    return bool(item.get("isReply"))


def _get_quoted_text(item: dict) -> Optional[str]:
    """从 apidojo 输出中拿被引全文。常见字段:
    quoted_tweet / quotedStatus / quotedTweet / quote."""
    for k in ("quotedTweet", "quoted_tweet", "quotedStatus", "quote", "quotedText"):
        v = item.get(k)
        if isinstance(v, dict):
            return v.get("text") or v.get("full_text") or v.get("rawContent")
        if isinstance(v, str):
            return v
    # 也可能在 raw_json 引用的 quoted 字段
    return None


def _get_conversation_id(item: dict) -> Optional[str]:
    """apidojo:conversationId / conversation_id / inReplyToStatusId 等。"""
    for k in ("conversationId", "conversation_id", "threadId", "thread_id"):
        v = item.get(k)
        if v:
            return str(v)
    # 退而求其次:同 conversation 算同一线程(in_reply_to_status_id 链向上)
    in_reply = item.get("inReplyToStatusId") or item.get("in_reply_to_status_id")
    if in_reply:
        return str(in_reply)
    return None


def _get_user_id(item: dict) -> Optional[str]:
    for k in ("userId", "user_id", "authorId", "author_id"):
        v = item.get(k)
        if v:
            return str(v)
    return None


# ---------------------------------------------------------------------------
# 拼装主流程
# ---------------------------------------------------------------------------


def assemble(
    anchor: dict,            # apidojo item(dict)
    db_path: DbPath,
    *,
    source_user_id: Optional[str] = None,    # 主推作者 id(用于自线程判断)
) -> AssembledContext:
    """对单条 apidojo item 拼装上下文。"""
    post_id = anchor.get("id") or anchor.get("tweetId") or anchor.get("post_id")
    raw_text = anchor.get("text") or anchor.get("full_text") or anchor.get("rawContent") or ""
    if not post_id:
        raise ValueError("anchor item has no id/tweetId/post_id")

    ctx = AssembledContext(anchor_post_id=post_id, anchor_raw_text=raw_text)

    # 1) 转推 → 跳过
    if _is_retweet(anchor):
        ctx.is_retweet = True
        return ctx

    # 2) 引用:加被引全文
    if _is_quote(anchor):
        ctx.quote_full_text = _get_quoted_text(anchor)
        if ctx.quote_full_text is None:
            qid = _get_quoted_status_id(anchor)
            if qid:
                ctx.quote_full_text = _lookup_raw_text(db_path, str(qid))
                if ctx.quote_full_text:
                    ctx.parent_in_library = True

    # 3) 回复:找父推文
    if _is_reply(anchor):
        in_reply = (anchor.get("inReplyToId") or anchor.get("inReplyToStatusId")
                    or anchor.get("in_reply_to_status_id") or anchor.get("inReplyToTweetId"))
        if not in_reply:
            # isReply=True 但 inReplyToId 缺失,父推不在库
            ctx.context_missing = True
        if in_reply:
            parent_text = _lookup_raw_text(db_path, str(in_reply))
            if parent_text:
                # 如果父推是 author 自己 = 自线程(同 conversation 后续拼接)
                parent_user = _lookup_user_id(db_path, str(in_reply))
                if parent_user and source_user_id and parent_user == source_user_id:
                    ctx.self_thread_post_ids.extend(_collect_self_thread(db_path, str(in_reply), source_user_id))
                else:
                    ctx.parent_in_library = True
                    # 把父推文也作为参考加到 quote 字段(类似"被引")
                    ctx.quote_full_text = (ctx.quote_full_text or "") + "\n\n[Parent tweet]:\n" + parent_text
            else:
                ctx.context_missing = True

    return ctx


# ---------------------------------------------------------------------------
# DB 查
# ---------------------------------------------------------------------------


def _lookup_raw_text(db_path: DbPath, post_id: str) -> Optional[str]:
    """从 raw_posts 表查 post_id 对应正文。"""
    try:
        with sqlite3.connect(db_path, timeout=10) as conn:
            row = conn.execute(
                "SELECT raw_text FROM raw_posts WHERE post_id = ?", (post_id,)
            ).fetchone()
    except sqlite3.OperationalError:
        return None
    return row[0] if row else None


def _lookup_user_id(db_path: DbPath, post_id: str) -> Optional[str]:
    """从 raw_json 取 userId。"""
    try:
        with sqlite3.connect(db_path, timeout=10) as conn:
            row = conn.execute(
                "SELECT raw_json FROM raw_posts WHERE post_id = ?", (post_id,)
            ).fetchone()
    except sqlite3.OperationalError:
        return None
    if not row:
        return None
    try:
        item = json.loads(row[0])
    except (ValueError, TypeError):
        return None
    return _get_user_id(item)


def _collect_self_thread(db_path: DbPath, start_post_id: str, user_id: str) -> List[str]:
    """从 start_post_id 向上爬 in_reply_to_status_id 链,收集同一 user 的所有 post_id。"""
    out = []
    cur = start_post_id
    seen = set()
    try:
        with sqlite3.connect(db_path, timeout=10) as conn:
            while cur and cur not in seen:
                seen.add(cur)
                row = conn.execute(
                    "SELECT raw_json FROM raw_posts WHERE post_id = ?", (cur,)
                ).fetchone()
                if not row:
                    break
                try:
                    item = json.loads(row[0])
                except (ValueError, TypeError):
                    break
                if _get_user_id(item) != user_id:
                    break
                out.append(cur)
                cur = (item.get("inReplyToId") or item.get("inReplyToStatusId")
                       or item.get("in_reply_to_status_id"))
    except sqlite3.OperationalError:
        pass
    return out


# ---------------------------------------------------------------------------
# 渲染(给 LLM 看)
# ---------------------------------------------------------------------------


def render_for_llm(ctx: AssembledContext) -> str:
    """把 AssembledContext 渲染成一段给 LLM 的输入文本。"""
    parts = []
    parts.append(f"### 主推文(post_id: {ctx.anchor_post_id})")
    parts.append(ctx.anchor_raw_text or "(空)")
    if ctx.quote_full_text:
        parts.append("")
        parts.append("### 被引推文(quote)")
        parts.append(ctx.quote_full_text)
    if ctx.self_thread_post_ids:
        parts.append("")
        parts.append(f"### 自线程(同作者串):{', '.join(ctx.self_thread_post_ids)}")
    if ctx.context_missing:
        parts.append("")
        parts.append("[context_missing=true: 此条是回复,父推文不在库中,可能指代不明]")
    return "\n".join(parts)
