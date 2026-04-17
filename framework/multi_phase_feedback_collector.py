from typing import Any


def collect_phase_feedback(
    health: dict[str, Any],
    routing_log: list[Any],
    phase_id: str,
) -> dict[str, Any]:
    if (
        not isinstance(health, dict)
        or not isinstance(routing_log, list)
        or not isinstance(phase_id, str)
        or not phase_id
    ):
        return {
            "feedback_status": "invalid_input",
            "feedback_count": 0,
            "collected_phase": None,
            "health_snapshot": None,
        }

    health_status = health.get("health_status")

    if health_status == "critical":
        return {
            "feedback_status": "health_critical",
            "feedback_count": 0,
            "collected_phase": None,
            "health_snapshot": None,
        }

    if health_status not in ("healthy", "degraded"):
        return {
            "feedback_status": "invalid_input",
            "feedback_count": 0,
            "collected_phase": None,
            "health_snapshot": None,
        }

    return {
        "feedback_status": "collected",
        "feedback_count": len(routing_log),
        "collected_phase": phase_id,
        "health_snapshot": health_status,
    }
