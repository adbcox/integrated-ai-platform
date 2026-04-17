from typing import Any


def finalize_phase5_exit(
    phase5_promotion_gate: dict[str, Any],
    exit_readiness_validator: dict[str, Any],
    self_evaluation_control_plane: dict[str, Any],
) -> dict[str, Any]:
    if (
        not isinstance(phase5_promotion_gate, dict)
        or not isinstance(exit_readiness_validator, dict)
        or not isinstance(self_evaluation_control_plane, dict)
    ):
        return {
            "exit_finalization_status": "invalid_input",
            "finalized_phase": None,
            "finalization_result": None,
        }

    ppg_ok = phase5_promotion_gate.get("promotion_gate_status") == "promoted"
    erv_ok = exit_readiness_validator.get("exit_readiness_status") == "valid"
    secp_ok = self_evaluation_control_plane.get("self_eval_cp_status") == "operational"
    all_ok = ppg_ok and erv_ok and secp_ok

    if all_ok:
        return {
            "exit_finalization_status": "finalized",
            "finalized_phase": phase5_promotion_gate.get("promotion_phase"),
            "finalization_result": "phase5_exit_finalized",
        }

    if (ppg_ok and erv_ok) or (ppg_ok and secp_ok) or (erv_ok and secp_ok):
        return {
            "exit_finalization_status": "pending",
            "finalized_phase": None,
            "finalization_result": None,
        }

    return {
        "exit_finalization_status": "failed",
        "finalized_phase": None,
        "finalization_result": None,
    }
