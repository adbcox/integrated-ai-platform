from typing import Any


def rollup_dispatch_metrics(
    metrics: list[dict[str, Any]],
) -> dict[str, Any]:
    if not isinstance(metrics, list) or not metrics:
        return {
            "rollup_valid": True,
            "sample_count": 0,
            "avg_latency_ms": 0.0,
            "avg_throughput_per_min": 0.0,
            "max_queue_depth": 0,
        }

    valid = [m for m in metrics if isinstance(m, dict)]
    if not valid:
        return {
            "rollup_valid": True,
            "sample_count": 0,
            "avg_latency_ms": 0.0,
            "avg_throughput_per_min": 0.0,
            "max_queue_depth": 0,
        }

    avg_latency = sum(
        float(m.get("dispatch_latency_ms", 0.0)) for m in valid
    ) / float(len(valid))
    avg_throughput = sum(
        float(m.get("throughput_per_min", 0.0)) for m in valid
    ) / float(len(valid))
    max_queue = max(int(m.get("queue_depth", 0)) for m in valid)

    return {
        "rollup_valid": True,
        "sample_count": len(valid),
        "avg_latency_ms": round(avg_latency, 3),
        "avg_throughput_per_min": round(avg_throughput, 3),
        "max_queue_depth": max_queue,
    }
