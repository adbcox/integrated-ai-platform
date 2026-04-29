"""Prometheus metrics for VMAgent scrape.

Endpoint mounted at /metrics. Three counters and one histogram are
sufficient for Phase 2; Phase 3 modules can add module-specific
counters as needed.
"""
from __future__ import annotations

from prometheus_client import Counter, Histogram

actions_total = Counter(
    "control_plane_actions_total",
    "Operator actions invoked, by tier and outcome.",
    ("tier", "action", "outcome"),
)

auth_total = Counter(
    "control_plane_auth_total",
    "Auth events by tier and outcome.",
    ("tier", "outcome"),
)

request_duration = Histogram(
    "control_plane_request_duration_seconds",
    "HTTP request duration.",
    ("method", "endpoint"),
    buckets=(0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0),
)
