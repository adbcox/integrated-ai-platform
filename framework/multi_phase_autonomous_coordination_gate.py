from typing import Any


def gate_autonomous_coordination(
    cross_plane: dict[str, Any],
    finalization: dict[str, Any],
    recovery_cp: dict[str, Any],
    gate_config: dict[str, Any],
) -> dict[str, Any]:
    if (
        not isinstance(cross_plane, dict)
        or not isinstance(finalization, dict)
        or not isinstance(recovery_cp, dict)
        or not isinstance(gate_config, dict)
    ):
        return {
            "autonomous_gate_status": "invalid_input",
            "gate_phase": None,
            "active_signals": 0,
        }

    cp_aligned = cross_plane.get("cross_plane_status") == "aligned"
    fin_ok = finalization.get("finalization_status") in ("finalized", "pending")
    rec_op = recovery_cp.get("recovery_cp_status") == "operational"

    all_ok = cp_aligned and fin_ok and rec_op
    any_ok = cp_aligned or fin_ok or rec_op
    active_signals = sum([cp_aligned, fin_ok, rec_op])

    if all_ok:
        return {
            "autonomous_gate_status": "open",
            "gate_phase": cross_plane.get("aligned_phase"),
            "active_signals": active_signals,
        }

    if any_ok:
        return {
            "autonomous_gate_status": "partial",
            "gate_phase": None,
            "active_signals": active_signals,
        }

    return {
        "autonomous_gate_status": "closed",
        "gate_phase": None,
        "active_signals": active_signals,
    }
