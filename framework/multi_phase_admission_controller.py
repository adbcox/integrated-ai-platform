from typing import Any


def evaluate_admission(
    coordinator: dict[str, Any],
    request: dict[str, Any],
    policy: dict[str, Any],
) -> dict[str, Any]:
    if (
        not isinstance(coordinator, dict)
        or not isinstance(request, dict)
        or not isinstance(policy, dict)
    ):
        return {
            "admission_status": "invalid_input",
            "request_id": None,
            "admitted_phase": None,
        }

    coord_ok = coordinator.get("coordinator_status") == "initialized"
    if not coord_ok:
        return {
            "admission_status": "coordinator_not_ready",
            "request_id": None,
            "admitted_phase": None,
        }

    request_valid = bool(request.get("request_id")) and bool(
        request.get("operation")
    )
    if request_valid:
        return {
            "admission_status": "admitted",
            "request_id": request.get("request_id"),
            "admitted_phase": coordinator.get("phase_id"),
        }

    return {
        "admission_status": "rejected",
        "request_id": None,
        "admitted_phase": None,
    }
