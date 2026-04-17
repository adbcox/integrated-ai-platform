from typing import Any


def detect_phase_failure(
    health: dict[str, Any],
    dispatch_result: dict[str, Any],
    threshold: dict[str, Any],
) -> dict[str, Any]:
    if (
        not isinstance(health, dict)
        or not isinstance(dispatch_result, dict)
        or not isinstance(threshold, dict)
    ):
        return {
            "failure_status": "invalid_input",
            "failure_type": "none",
            "failed_phase": None,
        }

    failure_detected = (
        health.get("health_status") in ("degraded", "critical")
        or dispatch_result.get("dispatch_status")
        in ("coordinator_not_ready", "control_plane_offline")
    )

    if failure_detected:
        failure_type = (
            "health"
            if health.get("health_status") in ("degraded", "critical")
            else "dispatch"
        )
        failed_phase = health.get("phase_id") or dispatch_result.get("target_phase") or None
        return {
            "failure_status": "detected",
            "failure_type": failure_type,
            "failed_phase": failed_phase,
        }

    return {
        "failure_status": "none",
        "failure_type": "none",
        "failed_phase": None,
    }
