"""Async/await template for bounded service calls."""

from __future__ import annotations

import asyncio
from typing import Any


async def run_with_timeout(coro: Any, timeout_seconds: float = 10.0) -> Any:
    """Run an async operation with a timeout."""
    return await asyncio.wait_for(coro, timeout=timeout_seconds)


async def fetch_data() -> dict[str, Any]:
    """Template async call."""
    return {}
