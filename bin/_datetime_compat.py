"""Compatibility helpers for datetime APIs across Python versions."""

from __future__ import annotations

from datetime import timezone

try:  # Python 3.11+
    from datetime import UTC as UTC  # type: ignore[attr-defined]
except ImportError:  # pragma: no cover - exercised on Python < 3.11
    UTC = timezone.utc
