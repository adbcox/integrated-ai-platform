"""Circuit breaker pattern — prevent cascading failures from dead services."""
from __future__ import annotations

import threading
import time
from typing import Any, Callable, Optional


class CircuitBreaker:
    """
    Three-state circuit breaker:
      closed    – normal; failures accumulate
      open      – service is down; calls skip and return cached data
      half-open – probe one call to test recovery
    """

    def __init__(
        self,
        name: str,
        failures_to_open: int = 5,
        timeout_seconds: float = 30.0,
        successes_to_close: int = 2,
    ) -> None:
        self.name               = name
        self.failures_to_open   = failures_to_open
        self.timeout_seconds    = timeout_seconds
        self.successes_to_close = successes_to_close

        self._state             = "closed"
        self._failures          = 0
        self._probes_ok         = 0
        self._opened_at: Optional[float] = None
        self._last_value: Any   = None
        self._last_ok_at: Optional[float] = None
        self._lock              = threading.Lock()

    # ── Internal state machine ────────────────────────────────────────────────

    def _current_state(self) -> str:
        with self._lock:
            if self._state == "open":
                elapsed = time.monotonic() - (self._opened_at or 0)
                if elapsed >= self.timeout_seconds:
                    self._state    = "half-open"
                    self._probes_ok = 0
            return self._state

    def _record_success(self, value: Any) -> None:
        with self._lock:
            self._last_value  = value
            self._last_ok_at  = time.time()
            if self._state == "half-open":
                self._probes_ok += 1
                if self._probes_ok >= self.successes_to_close:
                    self._state    = "closed"
                    self._failures = 0
            elif self._state == "closed":
                self._failures = 0

    def _record_failure(self) -> None:
        with self._lock:
            self._failures += 1
            if self._state in ("half-open", "closed") and self._failures >= self.failures_to_open:
                self._state     = "open"
                self._opened_at = time.monotonic()

    # ── Public API ────────────────────────────────────────────────────────────

    def call(self, fn: Callable[[], Any], fallback: Any = None) -> tuple[Any, bool]:
        """
        Run fn through the breaker.
        Returns (result, from_cache).
        from_cache=True means the circuit was open and stale/fallback data was returned.
        """
        state = self._current_state()
        if state == "open":
            cached = self._last_value if self._last_value is not None else fallback
            return cached, True

        try:
            result = fn()
            self._record_success(result)
            return result, False
        except Exception:
            self._record_failure()
            cached = self._last_value if self._last_value is not None else fallback
            return cached, True

    def reset(self) -> None:
        with self._lock:
            self._state     = "closed"
            self._failures  = 0
            self._probes_ok = 0
            self._opened_at = None

    def info(self) -> dict:
        with self._lock:
            cache_age = round(time.time() - self._last_ok_at) if self._last_ok_at else None
            open_for  = round(time.monotonic() - self._opened_at) if self._opened_at and self._state == "open" else None
            retry_in  = max(0, round(self.timeout_seconds - (time.monotonic() - (self._opened_at or 0)))) \
                        if self._state == "open" else None
            return {
                "name":          self.name,
                "state":         self._state,
                "failures":      self._failures,
                "cache_age_sec": cache_age,
                "open_for_sec":  open_for,
                "retry_in_sec":  retry_in,
            }
