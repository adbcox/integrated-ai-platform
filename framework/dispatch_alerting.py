from typing import Any


def evaluate_dispatch_alerts(
    metric: dict[str, Any],
    thresholds: dict[str, Any],
) -> dict[str, Any]:
    if not isinstance(metric, dict) or not isinstance(thresholds, dict):
        return {
            "alert_valid": False,
            "alert_triggered": False,
            "severity": "none",
            "trigger_reason": "invalid_input",
        }

    queue_limit = int(thresholds.get("queue_depth_limit", 0))
    latency_limit = float(thresholds.get("latency_limit_ms", 0))
    throughput_floor = float(thresholds.get("throughput_floor_per_min", 0))

    triggered = False
    severity = "none"
    reason = ""

    if metric.get("queue_depth", 0) > queue_limit and queue_limit > 0:
        triggered = True
        severity = "high"
        reason = "queue_depth_exceeded"
    elif (
        metric.get("dispatch_latency_ms", 0.0) > latency_limit
        and latency_limit > 0
    ):
        triggered = True
        severity = "medium"
        reason = "latency_spike"
    elif (
        metric.get("throughput_per_min", 0.0) < throughput_floor
        and throughput_floor > 0
    ):
        triggered = True
        severity = "medium"
        reason = "throughput_drop"

    return {
        "alert_valid": True,
        "alert_triggered": triggered,
        "severity": severity,
        "trigger_reason": reason,
    }
