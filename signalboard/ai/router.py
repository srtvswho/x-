"""Small provider router with OpenAI Responses API support.

Business code selects a workload, never a provider/model. Routes can be changed
through environment variables without touching extraction or thesis logic.
"""
from __future__ import annotations

import hashlib
import json
import os
import time
import uuid
from dataclasses import dataclass
from typing import Any

import requests

OPENAI_RESPONSES_URL = "https://api.openai.com/v1/responses"
OPENAI_EMBEDDINGS_URL = "https://api.openai.com/v1/embeddings"
DEEPSEEK_CHAT_URL = "https://api.deepseek.com/v1/chat/completions"

DEFAULT_ROUTES: dict[str, tuple[str, str, str]] = {
    "bulk_post_processing": ("deepseek", "deepseek-v4-flash", "none"),
    "daily_summary": ("deepseek", "deepseek-v4-flash", "none"),
    "media_understanding": ("openai", "gpt-5.6-terra", "low"),
    "thesis_update": ("openai", "gpt-5.6-terra", "medium"),
    "cross_author_analysis": ("openai", "gpt-5.6-terra", "medium"),
    "theme_canonicalization": ("openai", "gpt-5.6-terra", "medium"),
    "claim_verification": ("openai", "gpt-5.6-terra", "medium"),
    "ai_analyst": ("openai", "gpt-5.6-terra", "medium"),
    "golden_evaluation": ("openai", "gpt-5.6-terra", "medium"),
    "research_case_synthesis": ("openai", "gpt-5.6-terra", "high"),
    "deep_investment_analysis": ("openai", "gpt-5.6-sol", "high"),
}

# Standard, short-context list prices per 1M tokens. Environment overrides are
# supported so a pricing change never requires a code release.
DEFAULT_PRICING_USD_PER_MILLION: dict[str, tuple[float, float, float]] = {
    "gpt-5.6-terra": (2.0, 0.20, 12.0),
    "gpt-5.6-sol": (4.0, 0.40, 20.0),
    "gpt-5.6-luna": (0.20, 0.02, 1.20),
    "text-embedding-3-small": (0.02, 0.0, 0.0),
    # Conservative DeepSeek peak-hour rates; actual off-peak cost can be 50% lower.
    "deepseek-v4-flash": (0.44, 0.014, 1.32),
    "deepseek-v4-pro": (1.32, 0.044, 3.96),
    "deepseek-v4-flash-vision-exp": (0.44, 0.014, 1.32),
}


@dataclass(frozen=True)
class ResolvedRoute:
    workload: str
    provider: str
    model: str
    reasoning_effort: str


@dataclass
class AIResult:
    text: str
    data: Any
    workload: str
    provider: str
    model: str
    input_tokens: int = 0
    cached_input_tokens: int = 0
    output_tokens: int = 0
    estimated_cost_usd: float = 0.0
    latency_ms: int = 0
    request_id: str | None = None
    sources: list[dict[str, Any]] | None = None


@dataclass
class EmbeddingResult:
    vectors: list[list[float]]
    model: str
    input_tokens: int
    estimated_cost_usd: float
    latency_ms: int
    request_id: str | None = None


def _env_prefix(workload: str) -> str:
    return "AI_ROUTE_" + "".join(c if c.isalnum() else "_" for c in workload.upper())


def resolve_route(workload: str) -> ResolvedRoute:
    if workload not in DEFAULT_ROUTES:
        raise ValueError(f"Unknown AI workload: {workload}")
    provider, model, effort = DEFAULT_ROUTES[workload]
    prefix = _env_prefix(workload)
    provider = os.getenv(f"{prefix}_PROVIDER", provider).strip().lower()
    model = os.getenv(f"{prefix}_MODEL", model).strip()
    effort = os.getenv(f"{prefix}_REASONING_EFFORT", effort).strip().lower()
    if provider not in {"openai", "deepseek"}:
        raise ValueError(f"Unsupported AI provider for {workload}: {provider}")
    if not model:
        raise ValueError(f"Empty AI model for {workload}")
    return ResolvedRoute(workload, provider, model, effort)


def _api_key(provider: str) -> str:
    env_name = "OPENAI_API_KEY" if provider == "openai" else "DEEPSEEK_API_KEY"
    value = os.getenv(env_name, "").strip()
    if not value:
        raise RuntimeError(f"{env_name} not set")
    return value


def _pricing(model: str) -> tuple[float, float, float]:
    default = DEFAULT_PRICING_USD_PER_MILLION.get(model, (0.0, 0.0, 0.0))
    safe_model = "".join(c if c.isalnum() else "_" for c in model.upper())
    return (
        float(os.getenv(f"AI_PRICE_{safe_model}_INPUT_PER_1M", default[0])),
        float(os.getenv(f"AI_PRICE_{safe_model}_CACHED_INPUT_PER_1M", default[1])),
        float(os.getenv(f"AI_PRICE_{safe_model}_OUTPUT_PER_1M", default[2])),
    )


def _estimate_cost(model: str, input_tokens: int, cached_tokens: int, output_tokens: int) -> float:
    input_rate, cached_rate, output_rate = _pricing(model)
    uncached = max(0, input_tokens - cached_tokens)
    return round((uncached * input_rate + cached_tokens * cached_rate + output_tokens * output_rate) / 1_000_000, 8)


def _openai_output_text(payload: dict[str, Any]) -> str:
    pieces: list[str] = []
    for item in payload.get("output") or []:
        if item.get("type") != "message":
            continue
        for content in item.get("content") or []:
            if content.get("type") == "output_text" and content.get("text"):
                pieces.append(content["text"])
    if not pieces and isinstance(payload.get("output_text"), str):
        pieces.append(payload["output_text"])
    return "\n".join(pieces).strip()


def _request_openai(
    route: ResolvedRoute,
    system: str,
    user: str,
    *,
    schema: dict[str, Any] | None,
    schema_name: str,
    image_urls: list[str] | None,
    max_output_tokens: int,
    timeout: int,
    web_search: bool = False,
) -> tuple[str, dict[str, Any], str | None]:
    user_content: list[dict[str, Any]] = [{"type": "input_text", "text": user}]
    for url in image_urls or []:
        user_content.append({"type": "input_image", "image_url": url, "detail": "high"})
    body: dict[str, Any] = {
        "model": route.model,
        "input": [
            {"role": "system", "content": [{"type": "input_text", "text": system}]},
            {"role": "user", "content": user_content},
        ],
        "max_output_tokens": max_output_tokens,
        "text": {"verbosity": "low"},
        "store": False,
    }
    if route.reasoning_effort != "none":
        body["reasoning"] = {"effort": route.reasoning_effort}
    if schema is not None:
        body["text"]["format"] = {
            "type": "json_schema",
            "name": schema_name,
            "strict": True,
            "schema": schema,
        }
    if web_search:
        body["tools"] = [{"type": "web_search"}]
        body["include"] = ["web_search_call.action.sources"]
    response = requests.post(
        OPENAI_RESPONSES_URL,
        headers={"Authorization": f"Bearer {_api_key('openai')}", "Content-Type": "application/json"},
        json=body,
        timeout=timeout,
    )
    request_id = response.headers.get("x-request-id")
    response.raise_for_status()
    payload = response.json()
    if payload.get("status") == "incomplete":
        raise RuntimeError(f"OpenAI response incomplete: {payload.get('incomplete_details')}")
    text = _openai_output_text(payload)
    if not text:
        raise RuntimeError("OpenAI Responses API returned no output_text")
    return text, payload, request_id


def _request_deepseek(
    route: ResolvedRoute,
    system: str,
    user: str,
    *,
    schema: dict[str, Any] | None,
    max_output_tokens: int,
    timeout: int,
) -> tuple[str, dict[str, Any], str | None]:
    body: dict[str, Any] = {
        "model": route.model,
        "messages": [
            {"role": "system", "content": system},
            {"role": "user", "content": user},
        ],
        "temperature": 0.1,
        "max_tokens": max_output_tokens,
        "thinking": {"type": "disabled"},
    }
    if schema is not None:
        body["response_format"] = {"type": "json_object"}
    response = requests.post(
        DEEPSEEK_CHAT_URL,
        headers={"Authorization": f"Bearer {_api_key('deepseek')}", "Content-Type": "application/json"},
        json=body,
        timeout=timeout,
    )
    request_id = response.headers.get("x-request-id")
    response.raise_for_status()
    payload = response.json()
    text = payload["choices"][0]["message"]["content"].strip()
    return text, payload, request_id


def _usage(provider: str, model: str, payload: dict[str, Any]) -> tuple[int, int, int, float]:
    usage = payload.get("usage") or {}
    if provider == "openai":
        input_tokens = int(usage.get("input_tokens") or 0)
        output_tokens = int(usage.get("output_tokens") or 0)
        details = usage.get("input_tokens_details") or {}
        cached = int(details.get("cached_tokens") or 0)
    else:
        input_tokens = int(usage.get("prompt_tokens") or 0)
        output_tokens = int(usage.get("completion_tokens") or 0)
        details = usage.get("prompt_tokens_details") or {}
        cached = int(details.get("cached_tokens") or details.get("prompt_cache_hit_tokens") or 0)
    return input_tokens, cached, output_tokens, _estimate_cost(model, input_tokens, cached, output_tokens)


def _call(
    workload: str,
    system: str,
    user: str,
    *,
    schema: dict[str, Any] | None = None,
    schema_name: str = "signalboard_output",
    image_urls: list[str] | None = None,
    max_output_tokens: int = 1800,
    timeout: int = 90,
    max_retries: int = 2,
    web_search: bool = False,
) -> AIResult:
    route = resolve_route(workload)
    if image_urls and route.provider != "openai":
        raise ValueError(f"Configured provider {route.provider} does not support this router's image path")
    started = time.monotonic()
    last_error: Exception | None = None
    for attempt in range(max_retries + 1):
        try:
            if route.provider == "openai":
                text, payload, request_id = _request_openai(
                    route, system, user, schema=schema, schema_name=schema_name,
                    image_urls=image_urls, max_output_tokens=max_output_tokens, timeout=timeout,
                    web_search=web_search,
                )
            else:
                text, payload, request_id = _request_deepseek(
                    route, system, user, schema=schema,
                    max_output_tokens=max_output_tokens, timeout=timeout,
                )
            in_tok, cached_tok, out_tok, cost = _usage(route.provider, route.model, payload)
            return AIResult(
                text=text,
                data=json.loads(text) if schema is not None else text,
                workload=workload,
                provider=route.provider,
                model=route.model,
                input_tokens=in_tok,
                cached_input_tokens=cached_tok,
                output_tokens=out_tok,
                estimated_cost_usd=cost,
                latency_ms=int((time.monotonic() - started) * 1000),
                request_id=request_id,
                sources=_openai_web_sources(payload),
            )
        except Exception as exc:
            last_error = exc
            if attempt < max_retries:
                time.sleep(1 + 2 * attempt)
    assert last_error is not None
    raise last_error


def call_json(
    workload: str,
    system: str,
    user: str,
    schema: dict[str, Any],
    *,
    schema_name: str = "signalboard_output",
    image_urls: list[str] | None = None,
    max_output_tokens: int = 1800,
    timeout: int = 90,
    max_retries: int = 2,
) -> AIResult:
    return _call(
        workload, system, user, schema=schema, schema_name=schema_name,
        image_urls=image_urls, max_output_tokens=max_output_tokens,
        timeout=timeout, max_retries=max_retries,
    )


def call_text(
    workload: str,
    system: str,
    user: str,
    *,
    max_output_tokens: int = 600,
    timeout: int = 90,
    max_retries: int = 2,
) -> AIResult:
    return _call(
        workload, system, user, max_output_tokens=max_output_tokens,
        timeout=timeout, max_retries=max_retries,
    )


def _openai_web_sources(payload: dict[str, Any]) -> list[dict[str, Any]]:
    """Collect the full source list returned by Responses web search."""
    sources: dict[str, dict[str, Any]] = {}
    for item in payload.get("output") or []:
        action = item.get("action") or {}
        for source in action.get("sources") or []:
            url = str(source.get("url") or "").strip()
            if url:
                sources[url] = dict(source)
        if item.get("type") != "message":
            continue
        for content in item.get("content") or []:
            for annotation in content.get("annotations") or []:
                url = str(annotation.get("url") or "").strip()
                if url:
                    sources.setdefault(url, dict(annotation))
    return list(sources.values())


def call_json_web(
    workload: str,
    system: str,
    user: str,
    schema: dict[str, Any],
    *,
    schema_name: str = "signalboard_web_output",
    max_output_tokens: int = 2400,
    timeout: int = 180,
    max_retries: int = 2,
) -> AIResult:
    """Structured Responses call with the built-in web_search tool and source capture."""
    route = resolve_route(workload)
    if route.provider != "openai":
        raise ValueError(f"Web search requires OpenAI, got {route.provider}")
    return _call(
        workload, system, user, schema=schema, schema_name=schema_name,
        max_output_tokens=max_output_tokens, timeout=timeout,
        max_retries=max_retries, web_search=True,
    )


def embed_texts(
    texts: list[str], *, model: str = "text-embedding-3-small",
    dimensions: int = 256, timeout: int = 90,
) -> EmbeddingResult:
    """Batch embeddings for semantic candidate generation; merge decisions remain LLM-judged."""
    if not texts:
        return EmbeddingResult([], model, 0, 0.0, 0)
    started = time.monotonic()
    body: dict[str, Any] = {"model": model, "input": texts, "encoding_format": "float"}
    if dimensions:
        body["dimensions"] = dimensions
    response = requests.post(
        OPENAI_EMBEDDINGS_URL,
        headers={"Authorization": f"Bearer {_api_key('openai')}", "Content-Type": "application/json"},
        json=body,
        timeout=timeout,
    )
    request_id = response.headers.get("x-request-id")
    response.raise_for_status()
    payload = response.json()
    vectors = [row["embedding"] for row in sorted(payload.get("data") or [], key=lambda x: x["index"])]
    if len(vectors) != len(texts):
        raise RuntimeError(f"Embedding count mismatch: expected {len(texts)}, got {len(vectors)}")
    input_tokens = int((payload.get("usage") or {}).get("prompt_tokens") or 0)
    return EmbeddingResult(
        vectors=vectors, model=model, input_tokens=input_tokens,
        estimated_cost_usd=_estimate_cost(model, input_tokens, 0, 0),
        latency_ms=int((time.monotonic() - started) * 1000), request_id=request_id,
    )


def record_usage(
    conn: Any,
    result: AIResult | None,
    *,
    workload: str,
    object_type: str | None = None,
    object_id: str | None = None,
    error: Exception | None = None,
    latency_ms: int = 0,
) -> str:
    usage_id = uuid.uuid4().hex
    if result is not None:
        provider, model = result.provider, result.model
        input_tokens, cached_tokens = result.input_tokens, result.cached_input_tokens
        output_tokens, cost, latency = result.output_tokens, result.estimated_cost_usd, result.latency_ms
        status, error_type = "ok", None
    else:
        route = resolve_route(workload)
        provider, model = route.provider, route.model
        input_tokens = cached_tokens = output_tokens = 0
        cost, latency = 0.0, latency_ms
        status, error_type = "error", type(error).__name__ if error else "UnknownError"
    conn.execute(
        """
        INSERT INTO ai_usage (
            usage_id, workload, provider, model, object_type, object_id,
            input_tokens, cached_input_tokens, output_tokens,
            estimated_cost_usd, latency_ms, status, error_type
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            usage_id, workload, provider, model, object_type, object_id,
            input_tokens, cached_tokens, output_tokens, cost, latency, status, error_type,
        ),
    )
    return usage_id


def stable_input_hash(*parts: str) -> str:
    return hashlib.sha256("\n\x1f\n".join(parts).encode("utf-8")).hexdigest()
