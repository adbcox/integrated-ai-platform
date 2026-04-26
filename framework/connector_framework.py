"""Abstract base class and connection pooling for all external service connectors.

Usage::

    class MyConnector(BaseConnector):
        def connect(self): ...
        def disconnect(self): ...
        def health_check(self) -> bool: ...
        def _do_request(self, method, *args, **kwargs): ...

    ConnectorRegistry.register("my_service", MyConnector)
    conn = ConnectorRegistry.get("my_service")
"""
from __future__ import annotations

import logging
import threading
import time
import traceback
from abc import ABC, abstractmethod
from collections import deque
from dataclasses import dataclass, field
from functools import wraps
from queue import Empty, Queue
from typing import Any, Callable, Optional, Type

try:
    from framework.event_system import publish as _publish_event

    def _emit(topic: str, payload: dict) -> None:
        try:
            _publish_event(topic, payload, source="connector_framework")
        except Exception:
            pass

except ImportError:
    def _emit(topic: str, payload: dict) -> None:  # type: ignore[misc]
        pass

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Exceptions
# ---------------------------------------------------------------------------

class ConnectorError(Exception):
    """Base class for all connector errors."""


class CircuitOpenError(ConnectorError):
    """Raised when a request is rejected because the circuit breaker is OPEN."""


# ---------------------------------------------------------------------------
# ConnectorConfig
# ---------------------------------------------------------------------------

@dataclass
class ConnectorConfig:
    """Configuration for a single external service connector.

    Attributes:
        host: Hostname or IP address of the service.
        port: TCP port of the service.
        timeout: Per-request timeout in seconds.
        max_retries: Maximum retry attempts for transient failures.
        pool_size: Target connection pool size (capped at module max).
    """

    host: str
    port: int = 443
    timeout: float = 30.0
    max_retries: int = 3
    pool_size: int = 3


# ---------------------------------------------------------------------------
# Retry decorator
# ---------------------------------------------------------------------------

_RETRY_EXCEPTIONS = (ConnectionError, TimeoutError, ConnectorError)


def retry(
    max_attempts: int = 3,
    exceptions: tuple[type[Exception], ...] = _RETRY_EXCEPTIONS,
    base_backoff: float = 0.5,
) -> Callable:
    """Exponential-backoff retry decorator.

    Args:
        max_attempts: Maximum number of total attempts (first try + retries).
        exceptions: Exception types that trigger a retry.
        base_backoff: Base wait in seconds; wait doubles each attempt.

    Returns:
        Decorator that wraps the target function with retry logic.
    """

    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            last_exc: Optional[Exception] = None
            for attempt in range(1, max_attempts + 1):
                try:
                    return func(*args, **kwargs)
                except exceptions as exc:
                    last_exc = exc
                    if attempt == max_attempts:
                        break
                    wait = base_backoff * (2 ** (attempt - 1))
                    logger.debug(
                        "retry: attempt %d/%d failed (%s); sleeping %.2fs",
                        attempt,
                        max_attempts,
                        exc,
                        wait,
                    )
                    time.sleep(wait)
            raise last_exc  # type: ignore[misc]

        return wrapper

    return decorator


# ---------------------------------------------------------------------------
# Circuit breaker
# ---------------------------------------------------------------------------

_CB_CLOSED = "CLOSED"
_CB_OPEN = "OPEN"
_CB_HALF_OPEN = "HALF_OPEN"

_DEFAULT_FAILURE_THRESHOLD = 5
_DEFAULT_RECOVERY_TIMEOUT = 60.0


class _CircuitBreaker:
    """Three-state circuit breaker embedded in BaseConnector.

    States:
        CLOSED: Normal operation; failures accumulate.
        OPEN: Calls are rejected immediately.
        HALF_OPEN: One probe call allowed to test recovery.
    """

    def __init__(
        self,
        failure_threshold: int = _DEFAULT_FAILURE_THRESHOLD,
        recovery_timeout: float = _DEFAULT_RECOVERY_TIMEOUT,
    ) -> None:
        self._state = _CB_CLOSED
        self._failure_count = 0
        self._failure_threshold = failure_threshold
        self._recovery_timeout = recovery_timeout
        self._opened_at: Optional[float] = None
        self._lock = threading.Lock()

    @property
    def state(self) -> str:
        """Current circuit state string (CLOSED / OPEN / HALF_OPEN)."""
        with self._lock:
            return self._resolved_state()

    def _resolved_state(self) -> str:
        """Compute the current state, transitioning OPEN → HALF_OPEN if elapsed."""
        if self._state == _CB_OPEN and self._opened_at is not None:
            if time.monotonic() - self._opened_at >= self._recovery_timeout:
                self._state = _CB_HALF_OPEN
        return self._state

    def allow_request(self) -> bool:
        """Return True if the circuit permits a request to proceed.

        Returns:
            True when CLOSED or HALF_OPEN (probe), False when OPEN.
        """
        with self._lock:
            state = self._resolved_state()
            return state in (_CB_CLOSED, _CB_HALF_OPEN)

    def record_success(self) -> None:
        """Record a successful call, possibly closing the circuit."""
        with self._lock:
            self._failure_count = 0
            self._state = _CB_CLOSED
            self._opened_at = None

    def record_failure(self) -> None:
        """Record a failed call, possibly opening the circuit."""
        with self._lock:
            self._failure_count += 1
            if self._failure_count >= self._failure_threshold:
                if self._state != _CB_OPEN:
                    logger.warning(
                        "CircuitBreaker: opening circuit after %d failures",
                        self._failure_count,
                    )
                self._state = _CB_OPEN
                self._opened_at = time.monotonic()

    def info(self) -> dict[str, Any]:
        """Return a snapshot of the circuit breaker state.

        Returns:
            Dict with keys: state, failure_count, failure_threshold, recovery_timeout.
        """
        with self._lock:
            return {
                "state": self._resolved_state(),
                "failure_count": self._failure_count,
                "failure_threshold": self._failure_threshold,
                "recovery_timeout": self._recovery_timeout,
            }


# ---------------------------------------------------------------------------
# Connection pool
# ---------------------------------------------------------------------------

_POOL_MIN = 1
_POOL_MAX = 3


class ConnectionPool:
    """Fixed-size pool of raw connection objects for a single connector type.

    Connections are borrowed with :meth:`acquire` and returned with
    :meth:`release`.  The pool lazily creates connections up to *max_size*.

    Args:
        factory: Zero-argument callable that returns a new connection object.
        min_size: Minimum connections to pre-create on initialisation.
        max_size: Hard limit on connections held in the pool.
        acquire_timeout: Seconds to wait when the pool is exhausted.
    """

    def __init__(
        self,
        factory: Callable[[], Any],
        min_size: int = _POOL_MIN,
        max_size: int = _POOL_MAX,
        acquire_timeout: float = 10.0,
    ) -> None:
        self._factory = factory
        self._min_size = max(_POOL_MIN, min_size)
        self._max_size = min(_POOL_MAX, max(self._min_size, max_size))
        self._acquire_timeout = acquire_timeout
        self._pool: Queue = Queue(maxsize=self._max_size)
        self._total_created = 0
        self._lock = threading.Lock()
        self._init_pool()

    def _init_pool(self) -> None:
        for _ in range(self._min_size):
            conn = self._factory()
            self._pool.put(conn)
            self._total_created += 1

    def acquire(self) -> Any:
        """Borrow a connection from the pool, creating one if needed.

        Returns:
            A connection object.

        Raises:
            ConnectorError: When the pool is exhausted and timeout expires.
        """
        try:
            return self._pool.get_nowait()
        except Empty:
            pass
        with self._lock:
            if self._total_created < self._max_size:
                conn = self._factory()
                self._total_created += 1
                return conn
        try:
            return self._pool.get(timeout=self._acquire_timeout)
        except Empty as exc:
            raise ConnectorError("ConnectionPool: acquire timed out") from exc

    def release(self, conn: Any) -> None:
        """Return a connection to the pool.

        Args:
            conn: The connection object to return.
        """
        try:
            self._pool.put_nowait(conn)
        except Exception:
            pass  # pool is full; discard silently

    def close_all(self) -> None:
        """Drain and discard all pooled connections."""
        while not self._pool.empty():
            try:
                self._pool.get_nowait()
            except Empty:
                break

    @property
    def size(self) -> int:
        """Number of connections currently idle in the pool."""
        return self._pool.qsize()


# ---------------------------------------------------------------------------
# Base connector
# ---------------------------------------------------------------------------

class BaseConnector(ABC):
    """Abstract base class for all external service connectors.

    Subclasses must implement :meth:`connect`, :meth:`disconnect`,
    :meth:`health_check`, and :meth:`_do_request`.

    The :meth:`execute` method wraps :meth:`_do_request` with retry logic
    and circuit-breaker protection, and publishes lifecycle events.

    Args:
        config: ConnectorConfig holding host/port/timeout/retry settings.
    """

    def __init__(self, config: ConnectorConfig) -> None:
        self.config = config
        self._circuit_breaker = _CircuitBreaker(
            failure_threshold=_DEFAULT_FAILURE_THRESHOLD,
            recovery_timeout=_DEFAULT_RECOVERY_TIMEOUT,
        )
        self._latency_ms: deque[float] = deque(maxlen=1000)
        self._success_count: int = 0
        self._error_count: int = 0
        self._last_error: Optional[str] = None
        self._lock = threading.Lock()

    # -- Abstract interface ---------------------------------------------------

    @abstractmethod
    def connect(self) -> None:
        """Establish the underlying connection to the remote service."""

    @abstractmethod
    def disconnect(self) -> None:
        """Close and release the underlying connection."""

    @abstractmethod
    def health_check(self) -> bool:
        """Verify the service is reachable and responding.

        Returns:
            True if healthy, False otherwise.
        """

    @abstractmethod
    def _do_request(self, method: str, *args: Any, **kwargs: Any) -> Any:
        """Perform the actual request to the remote service.

        Args:
            method: Logical method name (e.g. "GET", "query", "infer").
            *args: Positional arguments forwarded to the underlying call.
            **kwargs: Keyword arguments forwarded to the underlying call.

        Returns:
            Service response (type determined by subclass).
        """

    # -- Public execute -------------------------------------------------------

    def execute(self, method: str, *args: Any, **kwargs: Any) -> Any:
        """Execute a request through the circuit breaker and retry logic.

        Args:
            method: Logical method name passed to :meth:`_do_request`.
            *args: Positional arguments forwarded to :meth:`_do_request`.
            **kwargs: Keyword arguments forwarded to :meth:`_do_request`.

        Returns:
            The result from :meth:`_do_request`.

        Raises:
            CircuitOpenError: When the circuit breaker is OPEN.
            ConnectorError: When all retry attempts are exhausted.
        """
        if not self._circuit_breaker.allow_request():
            _emit("connector.circuit.open", {
                "connector": type(self).__name__,
                "method": method,
            })
            raise CircuitOpenError(
                f"{type(self).__name__}: circuit is OPEN, request rejected"
            )

        start = time.monotonic()

        @retry(
            max_attempts=self.config.max_retries,
            exceptions=_RETRY_EXCEPTIONS,
        )
        def _attempt() -> Any:
            return self._do_request(method, *args, **kwargs)

        try:
            result = _attempt()
            elapsed_ms = (time.monotonic() - start) * 1000.0
            self._record_success(elapsed_ms)
            return result
        except Exception as exc:
            elapsed_ms = (time.monotonic() - start) * 1000.0
            self._record_error(exc, elapsed_ms)
            raise

    # -- Metrics --------------------------------------------------------------

    def _record_success(self, latency_ms: float) -> None:
        with self._lock:
            self._latency_ms.append(latency_ms)
            self._success_count += 1
        self._circuit_breaker.record_success()
        _emit("connector.request.success", {
            "connector": type(self).__name__,
            "latency_ms": round(latency_ms, 2),
        })

    def _record_error(self, exc: Exception, latency_ms: float) -> None:
        with self._lock:
            self._latency_ms.append(latency_ms)
            self._error_count += 1
            self._last_error = str(exc)
        self._circuit_breaker.record_failure()
        _emit("connector.request.error", {
            "connector": type(self).__name__,
            "error": str(exc),
            "latency_ms": round(latency_ms, 2),
        })

    @property
    def success_rate(self) -> float:
        """Fraction of requests that succeeded (0.0–1.0).

        Returns:
            Float between 0.0 and 1.0, or 1.0 if no requests have been made.
        """
        with self._lock:
            total = self._success_count + self._error_count
            if total == 0:
                return 1.0
            return self._success_count / total

    def metrics(self) -> dict[str, Any]:
        """Return a snapshot of connector metrics.

        Returns:
            Dict with keys: success_rate, error_count, last_error,
            avg_latency_ms, circuit_breaker.
        """
        with self._lock:
            lats = list(self._latency_ms)
        avg_lat = sum(lats) / len(lats) if lats else 0.0
        return {
            "success_rate": round(self.success_rate, 4),
            "error_count": self._error_count,
            "last_error": self._last_error,
            "avg_latency_ms": round(avg_lat, 2),
            "circuit_breaker": self._circuit_breaker.info(),
        }

    # -- Context manager ------------------------------------------------------

    def __enter__(self) -> BaseConnector:
        self.connect()
        return self

    def __exit__(self, *_: Any) -> None:
        self.disconnect()


# ---------------------------------------------------------------------------
# ConnectorRegistry
# ---------------------------------------------------------------------------

class ConnectorRegistry:
    """Global registry mapping names to connector classes.

    Usage::

        ConnectorRegistry.register("slack", SlackConnector)
        cls = ConnectorRegistry.get("slack")
        instance = cls(config)
    """

    _registry: dict[str, Type[BaseConnector]] = {}
    _lock: threading.Lock = threading.Lock()

    @classmethod
    def register(cls, name: str, connector_class: Type[BaseConnector]) -> None:
        """Register a connector class under *name*.

        Args:
            name: Unique service name (e.g. "slack", "postgres").
            connector_class: Subclass of BaseConnector to register.
        """
        with cls._lock:
            cls._registry[name] = connector_class
        logger.debug("ConnectorRegistry: registered '%s'", name)

    @classmethod
    def get(cls, name: str) -> Type[BaseConnector]:
        """Retrieve a connector class by *name*.

        Args:
            name: Previously registered service name.

        Returns:
            The connector class.

        Raises:
            KeyError: If *name* is not registered.
        """
        with cls._lock:
            if name not in cls._registry:
                raise KeyError(f"ConnectorRegistry: no connector registered for '{name}'")
            return cls._registry[name]

    @classmethod
    def list_names(cls) -> list[str]:
        """Return all registered connector names.

        Returns:
            Sorted list of registered names.
        """
        with cls._lock:
            return sorted(cls._registry.keys())
