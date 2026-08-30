"""Provider-neutral AI access for SignalBoard."""

from .router import (
    AIResult,
    ResolvedRoute,
    call_json,
    call_json_web,
    call_text,
    embed_texts,
    record_usage,
    resolve_route,
)

__all__ = [
    "AIResult",
    "ResolvedRoute",
    "call_json",
    "call_json_web",
    "call_text",
    "embed_texts",
    "record_usage",
    "resolve_route",
]
