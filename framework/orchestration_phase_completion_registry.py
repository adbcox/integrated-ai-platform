from typing import Any


def register_completed_phase(
    phase_id: str,
    closure_packet_result: dict[str, Any],
    boundary_result: dict[str, Any],
) -> dict[str, Any]:
    if (
        not isinstance(phase_id, str)
        or not phase_id
        or not isinstance(closure_packet_result, dict)
        or not isinstance(boundary_result, dict)
    ):
        return {
            "registration_valid": False,
            "phase_id": "unknown",
            "packet_ready": False,
            "boundary_ready": False,
            "phase_registered": False,
            "registration_status": "invalid_input",
        }

    packet_ready = closure_packet_result.get("packet_complete") is True
    boundary_ready = boundary_result.get("boundary_crossed") is True
    phase_registered = packet_ready and boundary_ready

    if phase_registered:
        status = "registered"
    elif packet_ready or boundary_ready:
        status = "updated"
    else:
        status = "rejected"

    return {
        "registration_valid": True,
        "phase_id": phase_id,
        "packet_ready": packet_ready,
        "boundary_ready": boundary_ready,
        "phase_registered": phase_registered,
        "registration_status": status,
    }


def summarize_phase_completion_registry(result: dict[str, Any]) -> dict[str, Any]:
    if not isinstance(result, dict) or result.get("registration_valid") is not True:
        return {
            "summary_valid": False,
            "registration_status": "invalid_input",
            "phase_registered": False,
            "phase_id": "unknown",
        }

    return {
        "summary_valid": True,
        "registration_status": result.get("registration_status", "invalid_input"),
        "phase_registered": bool(result.get("phase_registered", False)),
        "phase_id": result.get("phase_id", "unknown"),
    }
