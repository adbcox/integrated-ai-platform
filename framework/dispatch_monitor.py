from typing import Any


def measure_dispatch_health(
    queue_depth: int,
    dispatch_latency_ms: float,
    throughput_per_min: float,
) -> dict[str, Any]:
    if queue_depth < 0 or dispatch_latency_ms < 0 or throughput_per_min < 0:
        return {
            "metric_valid": False,
            "queue_depth": 0,
            "dispatch_latency_ms": 0.0,
            "throughput_per_min": 0.0,
            "anomaly_detected": True,
        }
    anomaly_detected = (
        queue_depth > 100
        or dispatch_latency_ms > 5000
        or throughput_per_min < 0.1
    )
    return {
        "metric_valid": True,
        "queue_depth": queue_depth,
        "dispatch_latency_ms": round(dispatch_latency_ms, 3),
        "throughput_per_min": round(throughput_per_min, 3),
        "anomaly_detected": anomaly_detected,
    }


def summarize_dispatch_health(
    metrics: list[dict[str, Any]],
) -> dict[str, Any]:
    if not isinstance(metrics, list):
        return {"summary_valid": False, "metric_count": 0, "anomaly_count": 0}
    valid = [m for m in metrics if isinstance(m, dict)]
    anomaly_count = len(
        [m for m in valid if m.get("anomaly_detected") is True]
    )
    return {
        "summary_valid": True,
        "metric_count": len(valid),
        "anomaly_count": anomaly_count,
    }
