from typing import Any


def extract_phase_intent(
    coordinator: dict[str, Any],
    request: dict[str, Any],
    intent_config: dict[str, Any],
) -> dict[str, Any]:
    if (
        not isinstance(coordinator, dict)
        or not isinstance(request, dict)
        or not isinstance(intent_config, dict)
    ):
        return {
            "intent_status": "invalid_input",
            "intent_id": None,
            "extracted_phase": None,
            "operation": None,
        }

    coord_ok = coordinator.get("coordinator_status") == "initialized"
    request_valid = bool(request.get("intent_id")) and bool(request.get("operation"))

    if coord_ok and request_valid:
        return {
            "intent_status": "extracted",
            "intent_id": request.get("intent_id"),
            "extracted_phase": coordinator.get("phase_id"),
            "operation": request.get("operation"),
        }

    if coord_ok and not request_valid:
        return {
            "intent_status": "invalid_request",
            "intent_id": None,
            "extracted_phase": None,
            "operation": None,
        }

    return {
        "intent_status": "coordinator_not_ready",
        "intent_id": None,
        "extracted_phase": None,
        "operation": None,
    }
