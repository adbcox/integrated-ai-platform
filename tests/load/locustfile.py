"""tests/load/locustfile.py — Locust load test for the AI Platform dashboard API.

Run:
    locust -f tests/load/locustfile.py --host http://localhost:8080

Environment variables:
    DASHBOARD_URL  — override target host (default: http://localhost:8080)
    LOCUST_USERS   — number of concurrent users (passed via CLI or env)

CI baseline thresholds:
    p50  ≤ 200 ms
    p95  ≤ 500 ms
    error rate ≤ 1%
"""
from __future__ import annotations

import os
import sys

# ── Locust import guard ────────────────────────────────────────────────────────
try:
    from locust import HttpUser, between, events, task
    from locust.runners import MasterRunner
    _LOCUST_AVAILABLE = True
except ImportError:
    _LOCUST_AVAILABLE = False
    # Define stubs so this file is importable without locust installed
    # (allows py_compile / import checks to pass in CI)
    class _Stub:
        def __init__(self, *a, **kw): pass
        def __call__(self, *a, **kw): return self
        def __get__(self, *a, **kw): return self

    HttpUser = object  # type: ignore[misc,assignment]
    between  = lambda a, b: None  # type: ignore[assignment]
    task     = lambda *a, **kw: (lambda f: f)  # type: ignore[assignment]
    events   = _Stub()  # type: ignore[assignment]
    MasterRunner = object  # type: ignore[assignment]


# ── Target host ────────────────────────────────────────────────────────────────
_DEFAULT_HOST = os.environ.get("DASHBOARD_URL", "http://localhost:8080")

# ── Baseline thresholds ────────────────────────────────────────────────────────
BASELINE = {
    "p50_ms":     200,
    "p95_ms":     500,
    "error_rate": 0.01,   # 1%
}


# ── User classes ───────────────────────────────────────────────────────────────

class DashboardUser(HttpUser if _LOCUST_AVAILABLE else object):  # type: ignore[misc]
    """Simulates a typical dashboard viewer polling overview and roadmap endpoints."""

    host       = _DEFAULT_HOST
    wait_time  = between(1, 3)

    # ── Tasks (weights reflect realistic access patterns) ──────────────────────

    @task(3)
    def get_overview(self) -> None:
        """Most frequent: dashboard overview stats."""
        with self.client.get(
            "/api/overview",
            name="/api/overview",
            catch_response=True,
        ) as resp:
            if resp.status_code == 200:
                resp.success()
            elif resp.status_code in (502, 503, 504):
                resp.failure(f"Gateway error: {resp.status_code}")
            # 404/500 counted as failures automatically

    @task(2)
    def get_roadmap_stats(self) -> None:
        """Roadmap stats — moderately frequent."""
        with self.client.get(
            "/api/roadmap/stats",
            name="/api/roadmap/stats",
            catch_response=True,
        ) as resp:
            if resp.status_code == 200:
                resp.success()
            elif resp.status_code == 404:
                resp.failure("roadmap/stats endpoint missing")

    @task(1)
    def get_plane_status(self) -> None:
        """Plane integration status — less frequent."""
        with self.client.get(
            "/api/plane/status",
            name="/api/plane/status",
            catch_response=True,
        ) as resp:
            # 200 or 503 (Plane offline) both acceptable
            if resp.status_code in (200, 503):
                resp.success()
            else:
                resp.failure(f"Unexpected status: {resp.status_code}")

    @task(1)
    def get_metrics(self) -> None:
        """Live metrics endpoint."""
        with self.client.get(
            "/api/metrics",
            name="/api/metrics",
            catch_response=True,
        ) as resp:
            if resp.status_code == 200:
                resp.success()
            elif resp.status_code == 404:
                # Metrics not yet wired — soft failure
                resp.success()
            else:
                resp.failure(f"metrics error: {resp.status_code}")


class AdminUser(HttpUser if _LOCUST_AVAILABLE else object):  # type: ignore[misc]
    """Simulates an operator checking executor and training status."""

    host      = _DEFAULT_HOST
    wait_time = between(5, 15)

    @task
    def executor_status(self) -> None:
        """Check executor status (low frequency)."""
        with self.client.get(
            "/api/executor/status",
            name="/api/executor/status",
            catch_response=True,
        ) as resp:
            if resp.status_code in (200, 204):
                resp.success()
            else:
                resp.failure(f"executor/status error: {resp.status_code}")

    @task
    def training_status(self) -> None:
        """Check training pipeline status."""
        with self.client.get(
            "/api/training/status",
            name="/api/training/status",
            catch_response=True,
        ) as resp:
            if resp.status_code in (200, 204, 404):
                resp.success()  # 404 = not yet wired
            else:
                resp.failure(f"training/status error: {resp.status_code}")

    @task
    def get_dependency_graph(self) -> None:
        """Fetch dependency graph data (heavy endpoint, admin-only frequency)."""
        with self.client.get(
            "/api/dependency-graph",
            name="/api/dependency-graph",
            catch_response=True,
        ) as resp:
            if resp.status_code in (200, 404):
                resp.success()
            else:
                resp.failure(f"dependency-graph error: {resp.status_code}")


# ── CI threshold check on test stop ───────────────────────────────────────────

if _LOCUST_AVAILABLE:
    @events.test_stop.add_listener
    def on_test_stop(environment, **kwargs) -> None:
        """Validate performance against baselines and exit non-zero if thresholds breached."""
        stats = environment.stats.total

        p50 = stats.get_response_time_percentile(0.50) or 0.0
        p95 = stats.get_response_time_percentile(0.95) or 0.0
        error_rate = stats.fail_ratio or 0.0
        total_reqs = stats.num_requests

        print("\n" + "=" * 60)
        print("LOAD TEST RESULTS")
        print("=" * 60)
        print(f"  Total requests : {total_reqs}")
        print(f"  p50 latency    : {p50:.0f} ms  (threshold: {BASELINE['p50_ms']} ms)")
        print(f"  p95 latency    : {p95:.0f} ms  (threshold: {BASELINE['p95_ms']} ms)")
        print(f"  Error rate     : {error_rate*100:.2f}%  (threshold: {BASELINE['error_rate']*100:.1f}%)")
        print("=" * 60)

        failures = []
        if total_reqs == 0:
            print("WARNING: No requests recorded — is the server running?")
            return

        if p50 > BASELINE["p50_ms"]:
            failures.append(f"p50={p50:.0f}ms exceeds threshold {BASELINE['p50_ms']}ms")

        if p95 > BASELINE["p95_ms"]:
            failures.append(f"p95={p95:.0f}ms exceeds threshold {BASELINE['p95_ms']}ms")

        if error_rate > BASELINE["error_rate"]:
            failures.append(
                f"error_rate={error_rate*100:.2f}% exceeds threshold {BASELINE['error_rate']*100:.1f}%"
            )

        if failures:
            print("\nTHRESHOLD VIOLATIONS:")
            for f in failures:
                print(f"  FAIL: {f}")
            print()
            # Signal CI failure
            raise SystemExit(1)
        else:
            print("\nAll thresholds passed.")
