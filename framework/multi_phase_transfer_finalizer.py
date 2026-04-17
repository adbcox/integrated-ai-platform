from typing import Any


def finalize_transfer(
    phase_completion_gate: dict[str, Any],
    transfer_validation: dict[str, Any],
    transfer_control_plane: dict[str, Any],
    finalize_config: dict[str, Any],
) -> dict[str, Any]:
    if (
        not isinstance(phase_completion_gate, dict)
        or not isinstance(transfer_validation, dict)
        or not isinstance(transfer_control_plane, dict)
        or not isinstance(finalize_config, dict)
    ):
        return {
            "transfer_finalization_status": "invalid_input",
            "finalized_phase": None,
            "finalization_result": None,
        }

    pcg_ok = phase_completion_gate.get("phase_completion_status") == "open"
    tv_ok = transfer_validation.get("transfer_validation_status") == "valid"
    tcp_ok = transfer_control_plane.get("transfer_cp_status") == "operational"
    all_ok = pcg_ok and tv_ok and tcp_ok

    if all_ok:
        return {
            "transfer_finalization_status": "finalized",
            "finalized_phase": phase_completion_gate.get("gate_phase"),
            "finalization_result": "transfer_complete",
        }

    if (pcg_ok and tv_ok) or (pcg_ok and tcp_ok) or (tv_ok and tcp_ok):
        return {
            "transfer_finalization_status": "pending",
            "finalized_phase": None,
            "finalization_result": None,
        }

    return {
        "transfer_finalization_status": "failed",
        "finalized_phase": None,
        "finalization_result": None,
    }
