from typing import Any


def adapt_routing(
    preemption: dict[str, Any],
    coordinator: dict[str, Any],
    routing_table: dict[str, Any],
) -> dict[str, Any]:
    if (
        not isinstance(preemption, dict)
        or not isinstance(coordinator, dict)
        or not isinstance(routing_table, dict)
    ):
        return {
            "adaptive_routing_status": "invalid_input",
            "adapted_route": None,
            "source_phase": None,
        }

    preempt_active = preemption.get("preemption_status") == "preempted"
    coord_ok = coordinator.get("coordinator_status") == "initialized"

    if preemption.get("preemption_status") in ("monitoring", "no_incident"):
        return {
            "adaptive_routing_status": "no_preemption",
            "adapted_route": None,
            "source_phase": None,
        }

    if preempt_active and not coord_ok:
        return {
            "adaptive_routing_status": "coordinator_not_ready",
            "adapted_route": None,
            "source_phase": None,
        }

    if preempt_active and coord_ok and len(routing_table) > 0:
        return {
            "adaptive_routing_status": "adapted",
            "adapted_route": list(routing_table.keys())[0],
            "source_phase": coordinator.get("phase_id"),
        }

    return {
        "adaptive_routing_status": "invalid_input",
        "adapted_route": None,
        "source_phase": None,
    }
