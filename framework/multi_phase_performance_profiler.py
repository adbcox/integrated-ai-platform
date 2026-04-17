from typing import Any


def profile_phase_performance(
    metrics: dict[str, Any],
    resource_tracker: dict[str, Any],
    health: dict[str, Any],
) -> dict[str, Any]:
    if (
        not isinstance(metrics, dict)
        or not isinstance(resource_tracker, dict)
        or not isinstance(health, dict)
    ):
        return {
            "profile_status": "invalid_input",
            "profiled_phase": None,
            "sample_count": 0,
            "baseline_health": None,
        }

    metrics_ok = metrics.get("metrics_status") == "collected"
    res_ok = int(resource_tracker.get("phase_count", 0)) > 0
    health_exists = health.get("health_status") in ("healthy", "degraded", "critical")

    if metrics_ok and res_ok and health_exists:
        return {
            "profile_status": "profiled",
            "profiled_phase": metrics.get("collected_phase"),
            "sample_count": int(resource_tracker.get("phase_count", 0)),
            "baseline_health": health.get("health_status"),
        }

    return {
        "profile_status": "incomplete",
        "profiled_phase": None,
        "sample_count": 0,
        "baseline_health": None,
    }
