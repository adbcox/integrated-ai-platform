from typing import Any


def gate_stack_readiness(
    transfer_control_plane: dict[str, Any],
    generalization_control_plane: dict[str, Any],
    curriculum_rollup: dict[str, Any],
    gate_config: dict[str, Any],
) -> dict[str, Any]:
    if (
        not isinstance(transfer_control_plane, dict)
        or not isinstance(generalization_control_plane, dict)
        or not isinstance(curriculum_rollup, dict)
        or not isinstance(gate_config, dict)
    ):
        return {
            "stack_readiness_status": "blocked",
            "gate_phase": None,
            "readiness_level": None,
        }

    tcp_ok = transfer_control_plane.get("transfer_cp_status") == "operational"
    gcp_ok = generalization_control_plane.get("generalization_cp_status") == "operational"
    cr_ok = curriculum_rollup.get("curriculum_rollup_status") == "rolled_up"
    all_ok = tcp_ok and gcp_ok and cr_ok

    if all_ok:
        return {
            "stack_readiness_status": "ready",
            "gate_phase": transfer_control_plane.get("cp_phase"),
            "readiness_level": gate_config.get("level", "full"),
        }

    if (tcp_ok and gcp_ok) or (tcp_ok and cr_ok) or (gcp_ok and cr_ok):
        return {
            "stack_readiness_status": "partial",
            "gate_phase": None,
            "readiness_level": None,
        }

    return {
        "stack_readiness_status": "blocked",
        "gate_phase": None,
        "readiness_level": None,
    }
