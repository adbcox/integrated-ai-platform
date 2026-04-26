"""Distributed tracing, performance profiling, and alerting rules engine.

Usage::

    from framework.monitoring_system import MonitoringSystem, trace

    ms = MonitoringSystem.instance()

    # Manual span
    span = ms.start_span("process_request")
    ms.finish_span(span, tags={"status": "ok"})

    # Decorator
    @trace("my_function")
    def my_function():
        ...

    # Alerting
    from framework.monitoring_system import AlertRule
    ms.add_rule(AlertRule(
        name="high_error_rate",
        metric_name="http_errors_total",
        condition=">",
        threshold=100.0,
        window_seconds=60,
        cooldown_seconds=300,
    ))
"""
from __future__ import annotations

import cProfile
import io
import logging
import pstats
import threading
import time
import uuid
from collections import deque
from dataclasses import dataclass, field
from functools import wraps
from typing import Any, Callable, Optional

try:
    from framework.metrics_system import MetricsRegistry
    _METRICS_AVAILABLE = True
except ImportError:
    MetricsRegistry = None  # type: ignore[assignment,misc]
    _METRICS_AVAILABLE = False

try:
    from framework.event_system import publish as _publish_event

    def _emit(topic: str, payload: dict) -> None:
        try:
            _publish_event(topic, payload, source="monitoring_system")
        except Exception:
            pass

except ImportError:
    def _emit(topic: str, payload: dict) -> None:  # type: ignore[misc]
        pass

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Distributed tracing
# ---------------------------------------------------------------------------

@dataclass
class Span:
    """A single unit of work within a distributed trace.

    Attributes:
        trace_id: Groups all spans for one logical request.
        span_id: Unique identifier for this span.
        parent_span_id: Span ID of the parent, or empty string for root spans.
        operation: Human-readable name of the work being done.
        start_time: Monotonic start time (seconds).
        end_time: Monotonic end time, or None while still in progress.
        tags: Key/value metadata attached after the fact.
        logs: Ordered list of (timestamp, message) tuples emitted during the span.
    """

    trace_id: str
    span_id: str
    parent_span_id: str
    operation: str
    start_time: float
    end_time: Optional[float] = None
    tags: dict[str, Any] = field(default_factory=dict)
    logs: list[tuple[float, str]] = field(default_factory=list)

    @property
    def duration_ms(self) -> Optional[float]:
        """Elapsed duration in milliseconds, or None if not finished."""
        if self.end_time is None:
            return None
        return (self.end_time - self.start_time) * 1000.0

    def log(self, message: str) -> None:
        """Append a timestamped log entry to this span.

        Args:
            message: Log message string.
        """
        self.logs.append((time.time(), message))


# Thread-local storage for the active span stack
_tl = threading.local()


def _get_span_stack() -> list[Span]:
    if not hasattr(_tl, "stack"):
        _tl.stack = []
    return _tl.stack


# ---------------------------------------------------------------------------
# Profiling
# ---------------------------------------------------------------------------

@dataclass
class ProfileResult:
    """Result of a cProfile-based function profile.

    Attributes:
        total_time_ms: Wall-clock duration of the profiled call in ms.
        calls: Total number of function calls recorded.
        subcalls: Total number of primitive (non-recursive) calls.
        hotspots: Top 5 functions by cumulative time.
    """

    total_time_ms: float
    calls: int
    subcalls: int
    hotspots: list[dict[str, Any]]


# ---------------------------------------------------------------------------
# Alerting
# ---------------------------------------------------------------------------

@dataclass
class AlertRule:
    """Rule that fires an alert when a metric crosses a threshold.

    Attributes:
        name: Unique rule name.
        metric_name: Name of the metric to evaluate.
        condition: Comparison operator string: ``">"``, ``"<"``, ``">="`` ,
            ``"<="``, ``"=="``.
        threshold: Numeric threshold value.
        window_seconds: Rolling window over which to aggregate.
        cooldown_seconds: Minimum seconds between repeat fires for this rule.
    """

    name: str
    metric_name: str
    condition: str
    threshold: float
    window_seconds: int
    cooldown_seconds: int = 300


@dataclass
class _AlertFired:
    rule_name: str
    metric_name: str
    value: float
    threshold: float
    condition: str
    fired_at: float = field(default_factory=time.time)


_CONDITION_OPS: dict[str, Callable[[float, float], bool]] = {
    ">": lambda a, b: a > b,
    "<": lambda a, b: a < b,
    ">=": lambda a, b: a >= b,
    "<=": lambda a, b: a <= b,
    "==": lambda a, b: a == b,
}

# ---------------------------------------------------------------------------
# Health check
# ---------------------------------------------------------------------------

@dataclass
class _HealthCheck:
    name: str
    check_fn: Callable[[], bool]
    timeout_seconds: float


# ---------------------------------------------------------------------------
# MonitoringSystem
# ---------------------------------------------------------------------------

class MonitoringSystem:
    """Singleton providing distributed tracing, profiling, alerting, and health checks."""

    _instance: Optional[MonitoringSystem] = None
    _instance_lock = threading.Lock()

    def __init__(self) -> None:
        # Tracing
        self._traces: dict[str, list[Span]] = {}
        self._trace_lock = threading.Lock()

        # Alerting
        self._rules: dict[str, AlertRule] = {}
        self._last_fired: dict[str, float] = {}
        self._alert_history: deque[_AlertFired] = deque(maxlen=1000)
        self._rule_lock = threading.Lock()
        self._alert_timer: Optional[threading.Timer] = None
        self._start_alert_loop()

        # Health checks
        self._health_checks: dict[str, _HealthCheck] = {}
        self._health_lock = threading.Lock()

    # -- Singleton ------------------------------------------------------------

    @classmethod
    def instance(cls) -> MonitoringSystem:
        """Return (creating if necessary) the process-wide singleton.

        Returns:
            Singleton MonitoringSystem.
        """
        if cls._instance is None:
            with cls._instance_lock:
                if cls._instance is None:
                    cls._instance = cls()
        return cls._instance

    # =========================================================================
    # Distributed tracing
    # =========================================================================

    def start_span(
        self,
        operation: str,
        parent_span_id: str = "",
        trace_id: str = "",
    ) -> Span:
        """Begin a new span.

        If no *trace_id* is supplied, inherits from the active span on the
        current thread, or creates a new trace.

        Args:
            operation: Human-readable name of the work.
            parent_span_id: ID of the parent span; empty for root spans.
            trace_id: Trace group ID; inferred from context if omitted.

        Returns:
            A new, in-progress Span.
        """
        stack = _get_span_stack()
        if not trace_id:
            trace_id = stack[-1].trace_id if stack else str(uuid.uuid4())
        if not parent_span_id and stack:
            parent_span_id = stack[-1].span_id

        span = Span(
            trace_id=trace_id,
            span_id=str(uuid.uuid4()),
            parent_span_id=parent_span_id,
            operation=operation,
            start_time=time.monotonic(),
        )
        stack.append(span)
        with self._trace_lock:
            self._traces.setdefault(trace_id, []).append(span)
        logger.debug("trace: started span '%s' in trace %s", operation, trace_id)
        return span

    def finish_span(self, span: Span, tags: Optional[dict[str, Any]] = None) -> None:
        """Mark a span as finished.

        Args:
            span: The span to finish.
            tags: Optional additional tags to attach.
        """
        span.end_time = time.monotonic()
        if tags:
            span.tags.update(tags)
        stack = _get_span_stack()
        if stack and stack[-1] is span:
            stack.pop()
        logger.debug(
            "trace: finished span '%s' (%.2f ms)",
            span.operation,
            span.duration_ms or 0.0,
        )

    def get_trace(self, trace_id: str) -> list[Span]:
        """Return all spans belonging to *trace_id*.

        Args:
            trace_id: The trace group ID.

        Returns:
            List of Span objects in creation order.
        """
        with self._trace_lock:
            return list(self._traces.get(trace_id, []))

    def current_span(self) -> Optional[Span]:
        """Return the innermost active span on this thread, or None.

        Returns:
            The current Span, or None.
        """
        stack = _get_span_stack()
        return stack[-1] if stack else None

    # =========================================================================
    # Performance profiling
    # =========================================================================

    def profile(self, func: Callable, *args: Any, **kwargs: Any) -> tuple[Any, ProfileResult]:
        """Profile *func* with cProfile and return result + statistics.

        Args:
            func: The callable to profile.
            *args: Positional arguments forwarded to *func*.
            **kwargs: Keyword arguments forwarded to *func*.

        Returns:
            Tuple of (function_result, ProfileResult).
        """
        profiler = cProfile.Profile()
        wall_start = time.monotonic()
        result = profiler.runcall(func, *args, **kwargs)
        wall_elapsed_ms = (time.monotonic() - wall_start) * 1000.0

        stream = io.StringIO()
        ps = pstats.Stats(profiler, stream=stream)
        ps.sort_stats(pstats.SortKey.CUMULATIVE)
        ps.print_stats(5)

        hotspots: list[dict[str, Any]] = []
        for func_info, stat in list(ps.stats.items())[:5]:  # type: ignore[attr-defined]
            filename, lineno, fname = func_info
            cc, nc, tt, ct, _ = stat
            hotspots.append({
                "function": fname,
                "file": filename,
                "line": lineno,
                "cumulative_time_ms": round(ct * 1000, 3),
                "total_time_ms": round(tt * 1000, 3),
                "calls": cc,
            })

        profile_result = ProfileResult(
            total_time_ms=round(wall_elapsed_ms, 3),
            calls=profiler.getstats().__len__(),
            subcalls=sum(s.callcount for s in profiler.getstats()),
            hotspots=hotspots,
        )
        return result, profile_result

    # =========================================================================
    # Alerting rules engine
    # =========================================================================

    def add_rule(self, rule: AlertRule) -> None:
        """Register an alerting rule.

        Args:
            rule: The AlertRule to add.
        """
        with self._rule_lock:
            self._rules[rule.name] = rule
        logger.debug("monitoring: added alert rule '%s'", rule.name)

    def remove_rule(self, name: str) -> None:
        """Remove an alerting rule by name.

        Args:
            name: The rule name to remove.
        """
        with self._rule_lock:
            self._rules.pop(name, None)
        logger.debug("monitoring: removed alert rule '%s'", name)

    def _start_alert_loop(self) -> None:
        self._alert_timer = threading.Timer(30.0, self._evaluate_rules)
        self._alert_timer.daemon = True
        self._alert_timer.start()

    def _evaluate_rules(self) -> None:
        try:
            with self._rule_lock:
                rules = list(self._rules.values())
            for rule in rules:
                self._evaluate_one(rule)
        except Exception as exc:
            logger.warning("monitoring: alert evaluation error: %s", exc)
        finally:
            self._start_alert_loop()

    def _evaluate_one(self, rule: AlertRule) -> None:
        if not _METRICS_AVAILABLE or MetricsRegistry is None:
            return
        try:
            reg = MetricsRegistry.instance()
            value = reg.aggregate(rule.metric_name, rule.window_seconds, "avg")
        except Exception:
            return
        op = _CONDITION_OPS.get(rule.condition)
        if op is None:
            logger.warning("monitoring: unknown condition '%s'", rule.condition)
            return
        if not op(value, rule.threshold):
            return
        now = time.time()
        last = self._last_fired.get(rule.name, 0.0)
        if now - last < rule.cooldown_seconds:
            return
        self._last_fired[rule.name] = now
        fired = _AlertFired(
            rule_name=rule.name,
            metric_name=rule.metric_name,
            value=value,
            threshold=rule.threshold,
            condition=rule.condition,
        )
        self._alert_history.append(fired)
        logger.warning(
            "monitoring: ALERT '%s' fired — %s %s %s (value=%.4f)",
            rule.name,
            rule.metric_name,
            rule.condition,
            rule.threshold,
            value,
        )
        _emit("monitoring.alert.fired", {
            "rule": rule.name,
            "metric": rule.metric_name,
            "value": value,
            "threshold": rule.threshold,
            "condition": rule.condition,
            "fired_at": fired.fired_at,
        })

    def get_alert_history(self) -> list[dict[str, Any]]:
        """Return all fired alerts as a list of dicts.

        Returns:
            List of alert dicts, most recent last.
        """
        return [
            {
                "rule": a.rule_name,
                "metric": a.metric_name,
                "value": a.value,
                "threshold": a.threshold,
                "condition": a.condition,
                "fired_at": a.fired_at,
            }
            for a in self._alert_history
        ]

    # =========================================================================
    # Health check aggregator
    # =========================================================================

    def register_health_check(
        self,
        name: str,
        check_fn: Callable[[], bool],
        timeout_seconds: float = 5.0,
    ) -> None:
        """Register a named health check function.

        Args:
            name: Unique name for this check.
            check_fn: Zero-argument callable returning True if healthy.
            timeout_seconds: Max time allowed before declaring the check failed.
        """
        with self._health_lock:
            self._health_checks[name] = _HealthCheck(
                name=name,
                check_fn=check_fn,
                timeout_seconds=timeout_seconds,
            )
        logger.debug("monitoring: registered health check '%s'", name)

    def run_all_checks(self) -> dict[str, bool]:
        """Run all registered health checks concurrently.

        Returns:
            Dict mapping check name → True (healthy) / False (unhealthy).
        """
        with self._health_lock:
            checks = list(self._health_checks.values())

        results: dict[str, bool] = {}
        threads: list[threading.Thread] = []
        lock = threading.Lock()

        def run_one(hc: _HealthCheck) -> None:
            ok = False
            try:
                result_holder: list[bool] = []

                def target() -> None:
                    try:
                        result_holder.append(hc.check_fn())
                    except Exception:
                        result_holder.append(False)

                t = threading.Thread(target=target, daemon=True)
                t.start()
                t.join(timeout=hc.timeout_seconds)
                ok = result_holder[0] if result_holder else False
            except Exception:
                ok = False
            with lock:
                results[hc.name] = ok

        for hc in checks:
            t = threading.Thread(target=run_one, args=(hc,), daemon=True)
            t.start()
            threads.append(t)

        for t in threads:
            t.join(timeout=max(hc.timeout_seconds for hc in checks) + 1.0 if checks else 6.0)

        return results

    def get_system_health(self) -> dict[str, Any]:
        """Return an aggregated system health summary.

        Returns:
            Dict with keys ``"status"`` (``"healthy"``, ``"degraded"``,
            ``"unhealthy"``) and ``"checks"`` mapping check name → bool.
        """
        checks = self.run_all_checks()
        if not checks:
            status = "healthy"
        else:
            failed = sum(1 for v in checks.values() if not v)
            total = len(checks)
            if failed == 0:
                status = "healthy"
            elif failed < total:
                status = "degraded"
            else:
                status = "unhealthy"
        return {"status": status, "checks": checks}


# ---------------------------------------------------------------------------
# @trace decorator
# ---------------------------------------------------------------------------

def trace(operation: str) -> Callable:
    """Decorator that wraps a function with automatic span start/finish.

    Args:
        operation: Label attached to the span.

    Returns:
        Decorator function.
    """

    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            ms = MonitoringSystem.instance()
            span = ms.start_span(operation)
            try:
                result = func(*args, **kwargs)
                ms.finish_span(span, tags={"success": True})
                return result
            except Exception as exc:
                ms.finish_span(span, tags={"success": False, "error": str(exc)})
                raise

        return wrapper

    return decorator
