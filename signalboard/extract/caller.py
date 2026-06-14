"""LLM 调用模块(等 Anthropic API key)。

设计:
- 缓存按 (post_id, prompt_version) 落 extraction_cache 表
- 失败重试 3 次,JSON 解析失败入 human_review_queue
- 支持 mock 模式(评测脚本不需要真 LLM)
"""
from __future__ import annotations

import hashlib
import json
import os
import sqlite3
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Callable, List, Optional, Union

from .config import (
    PROVIDER, ACTIVE_MODEL, ACTIVE_KEY_ENV,
    LLM_MAX_TOKENS, LLM_TEMPERATURE, LLM_MAX_RETRIES,
    ANTHROPIC_BASE_URL, ANTHROPIC_MODEL, ANTHROPIC_VERSION,
    DEEPSEEK_BASE_URL, DEEPSEEK_MODEL, DEEPSEEK_THINKING, DEEPSEEK_RESPONSE_FORMAT,
)

DbPath = Union[str, Path]


# ---------------------------------------------------------------------------
# 数据结构
# ---------------------------------------------------------------------------


@dataclass
class LLMCallResult:
    """单条 LLM 调用结果。"""
    post_id: str
    prompt_version: str
    model: str
    response_json: dict
    input_hash: str
    from_cache: bool = False
    parse_error: Optional[str] = None
    prompt_tokens: int = 0
    completion_tokens: int = 0
    total_tokens: int = 0


# ---------------------------------------------------------------------------
# 缓存读写
# ---------------------------------------------------------------------------


def _input_hash(assembled: str, post_id: str, prompt_version: str) -> str:
    h = hashlib.sha256()
    h.update(post_id.encode())
    h.update(prompt_version.encode())
    h.update(assembled.encode())
    return h.hexdigest()


def _cache_get(db_path: DbPath, post_id: str, prompt_version: str) -> Optional[dict]:
    try:
        with sqlite3.connect(db_path, timeout=10) as conn:
            row = conn.execute(
                "SELECT response_json, input_hash FROM extraction_cache "
                "WHERE post_id = ? AND prompt_version = ?",
                (post_id, prompt_version),
            ).fetchone()
    except sqlite3.OperationalError:
        return None
    if not row:
        return None
    return {"response_json": row[0], "input_hash": row[1]}


def _cache_put(db_path: DbPath, post_id: str, prompt_version: str,
               model: str, response_json: dict, input_hash: str) -> None:
    try:
        with sqlite3.connect(db_path, timeout=10) as conn:
            conn.execute(
                """INSERT OR REPLACE INTO extraction_cache
                   (post_id, prompt_version, model, response_json, input_hash)
                   VALUES (?, ?, ?, ?, ?)""",
                (post_id, prompt_version, model,
                 json.dumps(response_json, ensure_ascii=False), input_hash),
            )
            conn.commit()
    except sqlite3.OperationalError as e:
        print(f"[caller] cache put failed: {e}")


def _queue_put(db_path: DbPath, post_id: str, reason: str, payload: dict) -> None:
    try:
        with sqlite3.connect(db_path, timeout=10) as conn:
            conn.execute(
                """INSERT INTO human_review_queue (post_id, reason, payload)
                   VALUES (?, ?, ?)""",
                (post_id, reason, json.dumps(payload, ensure_ascii=False)),
            )
            conn.commit()
    except sqlite3.OperationalError as e:
        print(f"[caller] queue put failed: {e}")


# ---------------------------------------------------------------------------
# LLM 调用(stub + 真调用)
# ---------------------------------------------------------------------------


def _call_anthropic(
    system_prompt: str,
    user_prompt: str,
    *,
    model: Optional[str] = None,
    max_tokens: int = LLM_MAX_TOKENS,
    temperature: float = LLM_TEMPERATURE,
    max_retries: int = LLM_MAX_RETRIES,
) -> dict:
    """真调 Anthropic API(需 anthropic SDK + key)。"""
    import anthropic
    model = model or ANTHROPIC_MODEL
    api_key = os.environ.get("ANTHROPIC_API_KEY", "")
    if not api_key:
        raise RuntimeError("ANTHROPIC_API_KEY not set")
    client = anthropic.Anthropic(api_key=api_key)
    last_err = None
    for attempt in range(max_retries):
        try:
            resp = client.messages.create(
                model=model, max_tokens=max_tokens, temperature=temperature,
                system=system_prompt,
                messages=[{"role": "user", "content": user_prompt}],
            )
            text_blocks = [b for b in resp.content if hasattr(b, "text")]
            text = "\n".join(b.text for b in text_blocks) if text_blocks else ""
            text_clean = _strip_json_fence(text)
            return json.loads(text_clean)
        except Exception as e:
            last_err = e
            if attempt < max_retries - 1:
                time.sleep(2 ** attempt)
    raise RuntimeError(f"anthropic call failed after {max_retries} retries: {last_err}")


def _call_deepseek(
    system_prompt: str,
    user_prompt: str,
    *,
    model: Optional[str] = None,
    max_tokens: int = LLM_MAX_TOKENS,
    temperature: float = LLM_TEMPERATURE,
    max_retries: int = LLM_MAX_RETRIES,
) -> dict:
    """真调 DeepSeek API(OpenAI 兼容,走 /v1/chat/completions)。

    关键参数:
      - thinking: {"type": "disabled"}  — 关掉思考模式(spec:抽取是规则判定,不需要推理链)
      - response_format: {"type": "json_object"} — 强制 JSON
        (DeepSeek 要求 prompt 含 "json" 字面量,system prompt 已含 "JSON schema")
      - temperature: 0 — 规则判定要可复现
    """
    import httpx
    model = model or DEEPSEEK_MODEL
    api_key = os.environ.get("DEEPSEEK_API_KEY", "")
    if not api_key:
        raise RuntimeError("DEEPSEEK_API_KEY not set")
    url = DEEPSEEK_BASE_URL.rstrip("/") + "/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }
    body = {
        "model": model,
        "max_tokens": max_tokens,
        "temperature": temperature,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
        "response_format": DEEPSEEK_RESPONSE_FORMAT,
        "thinking": DEEPSEEK_THINKING,
        "stream": False,
    }
    last_err = None
    for attempt in range(max_retries):
        try:
            with httpx.Client(timeout=httpx.Timeout(60.0)) as client:
                r = client.post(url, headers=headers, json=body)
            if r.status_code != 200:
                raise RuntimeError(f"HTTP {r.status_code}: {r.text[:300]}")
            data = r.json()
            choices = data.get("choices", [])
            if not choices:
                raise RuntimeError(f"no choices: {data}")
            content = choices[0].get("message", {}).get("content", "")
            text_clean = _strip_json_fence(content)
            usage = data.get("usage") or {}
            obj = json.loads(text_clean)
            obj["_usage"] = {
                "prompt_tokens": usage.get("prompt_tokens", 0),
                "completion_tokens": usage.get("completion_tokens", 0),
                "total_tokens": usage.get("total_tokens", 0),
            }
            return obj
        except Exception as e:
            last_err = e
            if attempt < max_retries - 1:
                time.sleep(2 ** attempt)
    raise RuntimeError(f"deepseek call failed after {max_retries} retries: {last_err}")


def _call_llm(
    system_prompt: str,
    user_prompt: str,
    *,
    model: Optional[str] = None,
    **kw,
) -> dict:
    """顶层分发:根据 PROVIDER 选 anthropic 或 deepseek。"""
    if PROVIDER == "anthropic":
        return _call_anthropic(system_prompt, user_prompt, model=model, **kw)
    elif PROVIDER == "deepseek":
        return _call_deepseek(system_prompt, user_prompt, model=model, **kw)
    else:
        raise RuntimeError(f"unsupported PROVIDER: {PROVIDER!r}")


def _strip_json_fence(text: str) -> str:
    """去掉 LLM 偶尔包 ```json ... ``` 围栏。"""
    text_clean = text.strip()
    if text_clean.startswith("```"):
        lines = text_clean.splitlines()
        text_clean = "\n".join(l for l in lines if not l.strip().startswith("```"))
    return text_clean


def _call_mock(system_prompt: str, user_prompt: str, **kw) -> dict:
    """Mock LLM:从文件读预存响应(用于评测脚本 dry-run)。"""
    # 不实现 - 调用方应该用 mock_factory 注入
    raise NotImplementedError("use mock_factory to inject a fake LLM")


# ---------------------------------------------------------------------------
# 顶层入口
# ---------------------------------------------------------------------------


def extract_one(
    post_id: str,
    assembled: str,
    db_path: DbPath,
    *,
    prompt_version: Optional[str] = None,       # None → 用 config.CACHE_KEY_PROMPT_VERSION
    model: Optional[str] = None,                # None → 用 config.ACTIVE_MODEL
    use_cache: bool = True,
    caller: Optional[Callable[..., dict]] = None,
) -> LLMCallResult:
    """单条抽取。caller 是 (system, user, **kw) -> dict;None 用 _call_llm。"""
    from .config import CACHE_KEY_PROMPT_VERSION, ACTIVE_MODEL
    actual_pv = prompt_version or CACHE_KEY_PROMPT_VERSION
    actual_model = model or ACTIVE_MODEL
    if caller is None:
        caller = _call_llm

    # 1) cache hit?
    in_hash = _input_hash(assembled, post_id, actual_pv)
    if use_cache:
        cached = _cache_get(db_path, post_id, actual_pv)
        if cached and cached["input_hash"] == in_hash:
            try:
                return LLMCallResult(
                    post_id=post_id, prompt_version=actual_pv, model=actual_model,
                    response_json=json.loads(cached["response_json"]),
                    input_hash=in_hash, from_cache=True,
                )
            except (ValueError, TypeError):
                pass  # cache 损坏,继续真调

    # 2) 真调
    from .prompts import get_system_prompt
    system_prompt = get_system_prompt()
    user_prompt = f"现在请抽取这条推文:\n{assembled}\n\n(这条推文的 post_id: {post_id})"

    try:
        resp = caller(system_prompt, user_prompt, model=actual_model)
        usage_block = resp.pop("_usage", None) or {}
        pt = usage_block.get("prompt_tokens", 0)
        ct = usage_block.get("completion_tokens", 0)
        tt = usage_block.get("total_tokens", 0)
    except Exception as e:
        _queue_put(db_path, post_id, "llm_call_error", {"error": str(e), "input": assembled[:500]})
        return LLMCallResult(
            post_id=post_id, prompt_version=actual_pv, model=actual_model,
            response_json={"has_prediction": False, "predictions": [], "flags": [],
                          "extraction_notes": f"LLM call failed: {e}"},
            input_hash=in_hash, parse_error=str(e),
        )

    # 3) 写 cache
    _cache_put(db_path, post_id, actual_pv, actual_model, resp, in_hash)
    return LLMCallResult(
        post_id=post_id, prompt_version=actual_pv, model=actual_model,
        response_json=resp, input_hash=in_hash, from_cache=False,
        prompt_tokens=pt, completion_tokens=ct, total_tokens=tt,
    )


# ---------------------------------------------------------------------------
# 批抽
# ---------------------------------------------------------------------------


def extract_batch(
    items: List[tuple],   # [(post_id, assembled), ...]
    db_path: DbPath,
    *,
    prompt_version: Optional[str] = None,
    model: Optional[str] = None,
    use_cache: bool = True,
    caller: Optional[Callable[..., dict]] = None,
    progress: bool = True,
) -> List[LLMCallResult]:
    """批抽。"""
    results = []
    for i, (post_id, assembled) in enumerate(items, 1):
        r = extract_one(post_id, assembled, db_path,
                        prompt_version=prompt_version, model=model,
                        use_cache=use_cache, caller=caller)
        results.append(r)
        if progress and i % 10 == 0:
            print(f"  [{i}/{len(items)}] {r.post_id} (cache={r.from_cache}, err={r.parse_error})", flush=True)
    return results
