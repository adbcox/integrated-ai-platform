from typing import Any

from framework.dispatch_alerting import evaluate_dispatch_alerts
from framework.dispatch_monitor import measure_dispatch_health


def validate_dispatch_readiness(
    queue_depth: int,
    latency_ms: float,
    throughput_per_min: float,
    thresholds: dict[str, Any],
) -> dict[str, Any]:
    metric = measure_dispatch_health(queue_depth, latency_ms, throughput_per_min)
    alert = evaluate_dispatch_alerts(metric, thresholds)

    failed_checks = []
    warnings = []

    if not metric.get("metric_valid", False):
        failed_checks.append("invalid_metric")

    if alert.get("alert_triggered", False):
        warnings.append(alert.get("trigger_reason", "alert"))

    is_ready = (
        metric.get("metric_valid", False)
        and metric.get("anomaly_detected", False) is False
    )

    return {
        "is_ready": is_ready,
        "failed_checks": failed_checks,
        "warnings": warnings,
        "ready_at": "2026-04-17T00:00:00Z" if is_ready else "",
    }
