from typing import Any


def analyze_dispatch_latencies(
    latencies_ms: list[float],
) -> dict[str, Any]:
    if not isinstance(latencies_ms, list) or not latencies_ms:
        return {
            "analysis_valid": True,
            "count": 0,
            "p50_ms": 0.0,
            "p95_ms": 0.0,
            "p99_ms": 0.0,
            "max_ms": 0.0,
        }

    ordered = sorted(
        [float(x) for x in latencies_ms if float(x) >= 0.0]
    )
    if not ordered:
        return {
            "analysis_valid": True,
            "count": 0,
            "p50_ms": 0.0,
            "p95_ms": 0.0,
            "p99_ms": 0.0,
            "max_ms": 0.0,
        }

    def pct(values: list[float], fraction: float) -> float:
        idx = int((len(values) - 1) * fraction)
        return values[idx]

    return {
        "analysis_valid": True,
        "count": len(ordered),
        "p50_ms": round(pct(ordered, 0.50), 3),
        "p95_ms": round(pct(ordered, 0.95), 3),
        "p99_ms": round(pct(ordered, 0.99), 3),
        "max_ms": round(ordered[-1], 3),
    }
