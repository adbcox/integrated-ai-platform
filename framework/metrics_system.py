"""Prometheus-style metrics collection with aggregation and time-series storage.

Usage::

    from framework.metrics_system import counter, gauge, histogram, timer

    req_count = counter("http_requests_total", labels={"method": "GET"})
    req_count.inc()

    latency = histogram("request_duration_seconds")
    latency.observe(0.042)

    with timer("db_query"):
        rows = db.query(...)
"""
from __future__ import annotations

import logging
import math
import os
import threading
import time
from collections import deque
from dataclasses import dataclass, field
from typing import Any, Callable, Optional

try:
    import psutil as _psutil  # type: ignore[import]
    _PSUTIL_AVAILABLE = True
except ImportError:
    _psutil = None  # type: ignore[assignment]
    _PSUTIL_AVAILABLE = False

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Default histogram bucket boundaries (Prometheus-compatible)
# ---------------------------------------------------------------------------

_DEFAULT_BUCKETS = [0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0, 10.0]

# Interval for built-in process metric collection
_PROCESS_COLLECT_INTERVAL = 10.0


# ---------------------------------------------------------------------------
# Base metric
# ---------------------------------------------------------------------------

class BaseMetric:
    """Abstract base for all metric types.

    Args:
        name: Unique metric name (snake_case recommended).
        labels: Static label dict attached to every observation.
    """

    def __init__(self, name: str, labels: Optional[dict[str, str]] = None) -> None:
        self.name = name
        self.labels: dict[str, str] = labels or {}
        self._lock = threading.Lock()
        # Time-series: deque of (timestamp_float, value_float)
        self._timeseries: deque[tuple[float, float]] = deque(maxlen=10000)

    def _record_ts(self, value: float) -> None:
        self._timeseries.append((time.time(), value))

    def get_timeseries(
        self,
        start: Optional[float] = None,
        end: Optional[float] = None,
    ) -> list[tuple[float, float]]:
        """Return time-series samples within the optional time window.

        Args:
            start: Inclusive lower bound (Unix timestamp).  None means no limit.
            end: Inclusive upper bound (Unix timestamp).  None means no limit.

        Returns:
            List of (timestamp, value) tuples.
        """
        with self._lock:
            series = list(self._timeseries)
        if start is not None:
            series = [(t, v) for t, v in series if t >= start]
        if end is not None:
            series = [(t, v) for t, v in series if t <= end]
        return series

    def get(self) -> float:  # pragma: no cover – overridden
        raise NotImplementedError

    def _label_str(self) -> str:
        if not self.labels:
            return ""
        parts = ",".join(f'{k}="{v}"' for k, v in sorted(self.labels.items()))
        return "{" + parts + "}"


# ---------------------------------------------------------------------------
# Counter
# ---------------------------------------------------------------------------

class Counter(BaseMetric):
    """Monotonically increasing counter.

    Args:
        name: Metric name.
        labels: Static label dict.
    """

    def __init__(self, name: str, labels: Optional[dict[str, str]] = None) -> None:
        super().__init__(name, labels)
        self._value: float = 0.0

    def inc(self, amount: float = 1.0) -> None:
        """Increment the counter.

        Args:
            amount: Positive amount to add (default 1).

        Raises:
            ValueError: If *amount* is negative.
        """
        if amount < 0:
            raise ValueError("Counter.inc: amount must be non-negative")
        with self._lock:
            self._value += amount
            self._record_ts(self._value)

    def get(self) -> float:
        """Return the current counter value.

        Returns:
            Current accumulated total.
        """
        with self._lock:
            return self._value

    def to_prometheus_text(self) -> str:
        """Render in Prometheus text exposition format.

        Returns:
            Text string ending with newline.
        """
        return f"{self.name}{self._label_str()} {self._value}\n"


# ---------------------------------------------------------------------------
# Gauge
# ---------------------------------------------------------------------------

class Gauge(BaseMetric):
    """Arbitrary numeric gauge that can go up and down.

    Args:
        name: Metric name.
        labels: Static label dict.
    """

    def __init__(self, name: str, labels: Optional[dict[str, str]] = None) -> None:
        super().__init__(name, labels)
        self._value: float = 0.0

    def set(self, value: float) -> None:
        """Set the gauge to *value*.

        Args:
            value: New gauge value.
        """
        with self._lock:
            self._value = value
            self._record_ts(self._value)

    def inc(self, amount: float = 1.0) -> None:
        """Increment the gauge.

        Args:
            amount: Amount to add.
        """
        with self._lock:
            self._value += amount
            self._record_ts(self._value)

    def dec(self, amount: float = 1.0) -> None:
        """Decrement the gauge.

        Args:
            amount: Amount to subtract.
        """
        with self._lock:
            self._value -= amount
            self._record_ts(self._value)

    def get(self) -> float:
        """Return the current gauge value.

        Returns:
            Current gauge value.
        """
        with self._lock:
            return self._value

    def to_prometheus_text(self) -> str:
        """Render in Prometheus text exposition format.

        Returns:
            Text string ending with newline.
        """
        return f"{self.name}{self._label_str()} {self._value}\n"


# ---------------------------------------------------------------------------
# Histogram
# ---------------------------------------------------------------------------

class Histogram(BaseMetric):
    """Bucketed observation histogram.

    Args:
        name: Metric name.
        buckets: Sorted list of upper-bound values.
        labels: Static label dict.
    """

    def __init__(
        self,
        name: str,
        buckets: Optional[list[float]] = None,
        labels: Optional[dict[str, str]] = None,
    ) -> None:
        super().__init__(name, labels)
        self._buckets: list[float] = sorted(buckets or _DEFAULT_BUCKETS)
        self._bucket_counts: list[int] = [0] * len(self._buckets)
        self._inf_count: int = 0
        self._sum: float = 0.0
        self._count: int = 0
        self._observations: deque[float] = deque(maxlen=10000)

    def observe(self, value: float) -> None:
        """Record one observation.

        Args:
            value: The measured value (e.g. request duration in seconds).
        """
        with self._lock:
            self._sum += value
            self._count += 1
            self._observations.append(value)
            self._record_ts(value)
            placed = False
            for i, bound in enumerate(self._buckets):
                if value <= bound:
                    self._bucket_counts[i] += 1
                    placed = True
                    break
            if not placed:
                self._inf_count += 1

    def get(self) -> float:
        """Return the total sum of all observations.

        Returns:
            Sum of all observed values.
        """
        with self._lock:
            return self._sum

    def get_sum(self) -> float:
        """Return the sum of all observed values.

        Returns:
            Sum of observed values.
        """
        with self._lock:
            return self._sum

    def get_count(self) -> int:
        """Return the number of observations recorded.

        Returns:
            Observation count.
        """
        with self._lock:
            return self._count

    def get_buckets(self) -> dict[float, int]:
        """Return cumulative bucket counts keyed by upper bound.

        Returns:
            Dict mapping upper-bound → cumulative count (including lower buckets).
        """
        with self._lock:
            result: dict[float, int] = {}
            cumulative = 0
            for bound, count in zip(self._buckets, self._bucket_counts):
                cumulative += count
                result[bound] = cumulative
            result[math.inf] = cumulative + self._inf_count
            return result

    def get_percentile(self, p: float) -> float:
        """Estimate the *p*-th percentile from raw observations.

        Args:
            p: Percentile in [0.0, 1.0], e.g. 0.95 for P95.

        Returns:
            Estimated percentile value, or 0.0 if no observations.
        """
        with self._lock:
            obs = sorted(self._observations)
        if not obs:
            return 0.0
        idx = max(0, min(len(obs) - 1, int(math.ceil(p * len(obs))) - 1))
        return obs[idx]

    def to_prometheus_text(self) -> str:
        """Render in Prometheus text exposition format.

        Returns:
            Multi-line text string.
        """
        lines: list[str] = []
        label_str = self._label_str()
        cumulative = 0
        with self._lock:
            for bound, count in zip(self._buckets, self._bucket_counts):
                cumulative += count
                bucket_label = (
                    label_str[:-1] + f',le="{bound}"' + "}"
                    if label_str
                    else '{' + f'le="{bound}"' + "}"
                )
                lines.append(f"{self.name}_bucket{bucket_label} {cumulative}")
            inf_label = (
                label_str[:-1] + ',le="+Inf"}'
                if label_str
                else '{le="+Inf"}'
            )
            lines.append(
                f"{self.name}_bucket{inf_label} {cumulative + self._inf_count}"
            )
            lines.append(f"{self.name}_sum{label_str} {self._sum}")
            lines.append(f"{self.name}_count{label_str} {self._count}")
        return "\n".join(lines) + "\n"


# ---------------------------------------------------------------------------
# Timer context manager
# ---------------------------------------------------------------------------

class Timer:
    """Context manager that records elapsed time as a Histogram observation.

    Args:
        operation_name: Name used as the histogram metric name.
        registry: MetricsRegistry to register in (defaults to singleton).
    """

    def __init__(
        self,
        operation_name: str,
        registry: Optional[MetricsRegistry] = None,
    ) -> None:
        self._name = operation_name
        self._registry = registry
        self._start: float = 0.0

    def __enter__(self) -> Timer:
        self._start = time.monotonic()
        return self

    def __exit__(self, *_: Any) -> None:
        elapsed = time.monotonic() - self._start
        reg = self._registry or MetricsRegistry.instance()
        try:
            hist = reg.get(self._name)
            if not isinstance(hist, Histogram):
                hist = Histogram(self._name)
                reg.register(hist)
        except KeyError:
            hist = Histogram(self._name)
            reg.register(hist)
        hist.observe(elapsed)


# ---------------------------------------------------------------------------
# MetricsRegistry
# ---------------------------------------------------------------------------

class MetricsRegistry:
    """Singleton registry that holds all metrics and provides aggregation.

    Built-in process metrics (CPU, memory) are automatically collected every
    10 seconds when *psutil* is available.
    """

    _instance: Optional[MetricsRegistry] = None
    _instance_lock = threading.Lock()

    def __init__(self) -> None:
        self._metrics: dict[str, BaseMetric] = {}
        self._lock = threading.RLock()
        self._process_timer: Optional[threading.Timer] = None
        self._register_builtin_metrics()
        self._start_process_collection()

    # -- Singleton ------------------------------------------------------------

    @classmethod
    def instance(cls) -> MetricsRegistry:
        """Return (creating if necessary) the process-wide singleton.

        Returns:
            The singleton MetricsRegistry.
        """
        if cls._instance is None:
            with cls._instance_lock:
                if cls._instance is None:
                    cls._instance = cls()
        return cls._instance

    # -- Built-in metrics -----------------------------------------------------

    def _register_builtin_metrics(self) -> None:
        self._cpu_gauge = Gauge("process_cpu_percent")
        self._mem_gauge = Gauge("process_memory_bytes")
        self.register(self._cpu_gauge)
        self.register(self._mem_gauge)

    def _start_process_collection(self) -> None:
        self._process_timer = threading.Timer(
            _PROCESS_COLLECT_INTERVAL, self._collect_process_metrics
        )
        self._process_timer.daemon = True
        self._process_timer.start()

    def _collect_process_metrics(self) -> None:
        try:
            if _PSUTIL_AVAILABLE and _psutil is not None:
                proc = _psutil.Process(os.getpid())
                self._cpu_gauge.set(proc.cpu_percent(interval=None))
                self._mem_gauge.set(proc.memory_info().rss)
            else:
                # Fallback: use resource module if available
                try:
                    import resource as _resource
                    usage = _resource.getrusage(_resource.RUSAGE_SELF)
                    self._mem_gauge.set(float(usage.ru_maxrss))
                except Exception:
                    pass
        except Exception as exc:
            logger.debug("MetricsRegistry: process metric collection error: %s", exc)
        finally:
            self._start_process_collection()

    # -- Registration ---------------------------------------------------------

    def register(self, metric: BaseMetric) -> BaseMetric:
        """Register a metric.

        If a metric with the same name already exists, returns the existing one.

        Args:
            metric: The metric to register.

        Returns:
            The registered metric (may be a pre-existing instance).
        """
        with self._lock:
            if metric.name in self._metrics:
                return self._metrics[metric.name]
            self._metrics[metric.name] = metric
            return metric

    def get(self, name: str) -> BaseMetric:
        """Retrieve a metric by name.

        Args:
            name: The metric name.

        Returns:
            The BaseMetric instance.

        Raises:
            KeyError: If no metric is registered under *name*.
        """
        with self._lock:
            if name not in self._metrics:
                raise KeyError(f"MetricsRegistry: no metric named '{name}'")
            return self._metrics[name]

    def get_all(self) -> dict[str, BaseMetric]:
        """Return all registered metrics.

        Returns:
            Dict mapping name → BaseMetric.
        """
        with self._lock:
            return dict(self._metrics)

    # -- Time-series access ---------------------------------------------------

    def get_timeseries(
        self,
        name: str,
        start: Optional[float] = None,
        end: Optional[float] = None,
    ) -> list[tuple[float, float]]:
        """Return time-series for a named metric.

        Args:
            name: Metric name.
            start: Optional start timestamp.
            end: Optional end timestamp.

        Returns:
            List of (timestamp, value) tuples.

        Raises:
            KeyError: If the metric does not exist.
        """
        metric = self.get(name)
        return metric.get_timeseries(start, end)

    # -- Aggregation ----------------------------------------------------------

    def aggregate(
        self,
        name: str,
        window_seconds: int,
        func: str,
    ) -> float:
        """Aggregate time-series values over a rolling window.

        Args:
            name: Metric name.
            window_seconds: How many seconds back to consider.
            func: One of ``"sum"``, ``"avg"``, ``"min"``, ``"max"``,
                ``"p95"``, ``"p99"``.

        Returns:
            Aggregated scalar value, or 0.0 if no data in window.

        Raises:
            ValueError: If *func* is not recognised.
            KeyError: If the metric does not exist.
        """
        start = time.time() - window_seconds
        series = self.get_timeseries(name, start=start)
        values = [v for _, v in series]
        if not values:
            return 0.0
        if func == "sum":
            return sum(values)
        if func == "avg":
            return sum(values) / len(values)
        if func == "min":
            return min(values)
        if func == "max":
            return max(values)
        if func in ("p95", "p99"):
            p = 0.95 if func == "p95" else 0.99
            sorted_vals = sorted(values)
            idx = max(0, min(len(sorted_vals) - 1, int(math.ceil(p * len(sorted_vals))) - 1))
            return sorted_vals[idx]
        raise ValueError(f"MetricsRegistry.aggregate: unknown func '{func}'")

    # -- Export ---------------------------------------------------------------

    def to_prometheus_text(self) -> str:
        """Render all metrics in Prometheus text exposition format.

        Returns:
            Full Prometheus text exposition string.
        """
        with self._lock:
            metrics = list(self._metrics.values())
        lines: list[str] = []
        for metric in metrics:
            if hasattr(metric, "to_prometheus_text"):
                lines.append(metric.to_prometheus_text())
        return "".join(lines)

    def to_dict(self) -> dict[str, Any]:
        """Serialise all metrics to a dict suitable for JSON endpoints.

        Returns:
            Dict mapping metric name → value summary.
        """
        with self._lock:
            metrics = list(self._metrics.values())
        result: dict[str, Any] = {}
        for metric in metrics:
            entry: dict[str, Any] = {
                "type": type(metric).__name__,
                "labels": metric.labels,
                "value": metric.get(),
            }
            if isinstance(metric, Histogram):
                entry["count"] = metric.get_count()
                entry["sum"] = metric.get_sum()
                entry["p50"] = metric.get_percentile(0.50)
                entry["p95"] = metric.get_percentile(0.95)
                entry["p99"] = metric.get_percentile(0.99)
            result[metric.name] = entry
        return result


# ---------------------------------------------------------------------------
# Module-level factory functions
# ---------------------------------------------------------------------------

def counter(name: str, labels: Optional[dict[str, str]] = None) -> Counter:
    """Get or create a Counter in the global registry.

    Args:
        name: Metric name.
        labels: Optional label dict.

    Returns:
        Counter instance.
    """
    reg = MetricsRegistry.instance()
    try:
        existing = reg.get(name)
        if isinstance(existing, Counter):
            return existing
    except KeyError:
        pass
    return reg.register(Counter(name, labels))  # type: ignore[return-value]


def gauge(name: str, labels: Optional[dict[str, str]] = None) -> Gauge:
    """Get or create a Gauge in the global registry.

    Args:
        name: Metric name.
        labels: Optional label dict.

    Returns:
        Gauge instance.
    """
    reg = MetricsRegistry.instance()
    try:
        existing = reg.get(name)
        if isinstance(existing, Gauge):
            return existing
    except KeyError:
        pass
    return reg.register(Gauge(name, labels))  # type: ignore[return-value]


def histogram(
    name: str,
    buckets: Optional[list[float]] = None,
    labels: Optional[dict[str, str]] = None,
) -> Histogram:
    """Get or create a Histogram in the global registry.

    Args:
        name: Metric name.
        buckets: Optional bucket boundaries.
        labels: Optional label dict.

    Returns:
        Histogram instance.
    """
    reg = MetricsRegistry.instance()
    try:
        existing = reg.get(name)
        if isinstance(existing, Histogram):
            return existing
    except KeyError:
        pass
    return reg.register(Histogram(name, buckets, labels))  # type: ignore[return-value]


def timer(operation_name: str) -> Timer:
    """Create a Timer context manager that records into the global registry.

    Args:
        operation_name: Used as the histogram metric name.

    Returns:
        Timer context manager.
    """
    return Timer(operation_name, registry=MetricsRegistry.instance())
