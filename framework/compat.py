"""Compatibility helpers for Python runtime differences."""

from __future__ import annotations

from datetime import timezone
from enum import Enum

try:  # Python 3.11+
    from enum import StrEnum as StrEnum  # type: ignore[attr-defined]
except ImportError:  # pragma: no cover - exercised on Python < 3.11
    class StrEnum(str, Enum):
        """Backport subset of enum.StrEnum for Python 3.9/3.10."""


try:  # Python 3.11+
    from datetime import UTC as UTC  # type: ignore[attr-defined]
except ImportError:  # pragma: no cover - exercised on Python < 3.11
    UTC = timezone.utc
