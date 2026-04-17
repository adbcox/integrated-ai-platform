from typing import Any


def route_phase_failover(
    retry_result: dict[str, Any],
    coordinator: dict[str, Any],
    fallback_map: dict[str, Any],
) -> dict[str, Any]:
    if (
        not isinstance(retry_result, dict)
        or not isinstance(coordinator, dict)
        or not isinstance(fallback_map, dict)
    ):
        return {
            "failover_status": "invalid_input",
            "failover_target": None,
            "source_phase": None,
        }

    if retry_result.get("retry_status") != "exhausted":
        return {
            "failover_status": "retry_not_exhausted",
            "failover_target": None,
            "source_phase": coordinator.get("phase_id"),
        }

    if coordinator.get("coordinator_status") != "initialized":
        return {
            "failover_status": "invalid_input",
            "failover_target": None,
            "source_phase": None,
        }

    if len(fallback_map) == 0:
        return {
            "failover_status": "no_fallback",
            "failover_target": None,
            "source_phase": coordinator.get("phase_id"),
        }

    return {
        "failover_status": "routed",
        "failover_target": list(fallback_map.keys())[0],
        "source_phase": coordinator.get("phase_id"),
    }
