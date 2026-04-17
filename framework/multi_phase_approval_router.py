from typing import Any


def route_approval(
    escalation: dict[str, Any],
    coordinator: dict[str, Any],
    approval_map: dict[str, Any],
) -> dict[str, Any]:
    if (
        not isinstance(escalation, dict)
        or not isinstance(coordinator, dict)
        or not isinstance(approval_map, dict)
    ):
        return {
            "approval_status": "invalid_input",
            "approved_phase": None,
            "approver": None,
        }

    esc_status = escalation.get("escalation_status")
    coord_ok = coordinator.get("coordinator_status") == "initialized"

    if (
        not coord_ok
        and esc_status in ("monitoring", "escalated")
    ):
        return {
            "approval_status": "coordinator_not_ready",
            "approved_phase": None,
            "approver": None,
        }

    if (
        esc_status == "monitoring"
        and coord_ok
        and len(approval_map) > 0
    ):
        return {
            "approval_status": "approved",
            "approved_phase": coordinator.get("phase_id"),
            "approver": list(approval_map.keys())[0],
        }

    if esc_status == "escalated" and coord_ok:
        return {
            "approval_status": "pending",
            "approved_phase": None,
            "approver": None,
        }

    if esc_status == "blocked":
        return {
            "approval_status": "rejected",
            "approved_phase": None,
            "approver": None,
        }

    return {
        "approval_status": "invalid_input",
        "approved_phase": None,
        "approver": None,
    }
