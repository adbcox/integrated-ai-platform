from typing import Any


def build_benchmark_control_plane(
    benchmark_rollup: dict[str, Any],
    promotion_readiness: dict[str, Any],
    event_bus: dict[str, Any],
) -> dict[str, Any]:
    if (
        not isinstance(benchmark_rollup, dict)
        or not isinstance(promotion_readiness, dict)
        or not isinstance(event_bus, dict)
    ):
        return {
            "benchmark_cp_status": "offline",
            "cp_phase": None,
            "message_count": 0,
        }

    br_ok = benchmark_rollup.get("benchmark_rollup_status") == "rolled_up"
    pr_ok = promotion_readiness.get("promotion_readiness_status") == "ready"
    eb_ok = event_bus.get("message_count", 0) >= 0
    all_ok = br_ok and pr_ok and eb_ok

    if all_ok:
        return {
            "benchmark_cp_status": "operational",
            "cp_phase": benchmark_rollup.get("rollup_phase"),
            "message_count": event_bus.get("message_count", 0),
        }

    if (br_ok and pr_ok) or (br_ok and eb_ok) or (pr_ok and eb_ok):
        return {
            "benchmark_cp_status": "degraded",
            "cp_phase": None,
            "message_count": 0,
        }

    return {
        "benchmark_cp_status": "offline",
        "cp_phase": None,
        "message_count": 0,
    }
