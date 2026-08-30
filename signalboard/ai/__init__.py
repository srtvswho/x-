"""Provider-neutral AI access for SignalBoard."""

from .router import (
    AIResult,
    ResolvedRoute,
    call_json,
    call_text,
    record_usage,
    resolve_route,
)

__all__ = [
    "AIResult",
    "ResolvedRoute",
    "call_json",
    "call_text",
    "record_usage",
    "resolve_route",
]
