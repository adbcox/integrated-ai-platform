from typing import Any


def generate_dispatch_coordination_summary(
    queue_status: dict[str, Any],
    routing_status: dict[str, Any],
    monitoring_status: dict[str, Any],
    readiness_status: dict[str, Any],
) -> dict[str, Any]:
    if (
        not isinstance(queue_status, dict)
        or not isinstance(routing_status, dict)
        or not isinstance(monitoring_status, dict)
        or not isinstance(readiness_status, dict)
    ):
        return {
            "summary_valid": False,
            "system_ready": False,
            "readiness_score": 0,
            "next_actions": [],
        }

    readiness_score = 100
    next_actions = []

    if readiness_status.get("is_ready", False) is False:
        readiness_score -= 40
        next_actions.append("fix_readiness")

    if monitoring_status.get("anomaly_detected", False):
        readiness_score -= 30
        next_actions.append("investigate_anomaly")

    if routing_status.get("route_valid", True) is False:
        readiness_score -= 20
        next_actions.append("repair_routing")

    if queue_status.get("queue_size", 0) > 100:
        readiness_score -= 10
        next_actions.append("drain_queue")

    readiness_score = max(0, readiness_score)

    return {
        "summary_valid": True,
        "system_ready": readiness_score >= 70,
        "readiness_score": readiness_score,
        "next_actions": sorted(next_actions),
    }
