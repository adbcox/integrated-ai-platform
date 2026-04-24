"""Try/except patterns for bounded error handling."""

from __future__ import annotations

from typing import Any, Callable, TypeVar

T = TypeVar("T")


def safe_call(func: Callable[[], T], default: T) -> T:
    """Wrap a small operation and return a fallback on error."""
    try:
        return func()
    except Exception:
        return default


def safe_result(value: Any) -> dict[str, Any]:
    """Template for wrapping errors in a structured response."""
    try:
        return {"success": True, "value": value}
    except Exception as exc:
        return {"success": False, "error": str(exc)}
