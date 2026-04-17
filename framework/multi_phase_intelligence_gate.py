from typing import Any


def gate_intelligence(
    cross_layer: dict[str, Any],
    finalization: dict[str, Any],
    governance_cp: dict[str, Any],
    gate_config: dict[str, Any],
) -> dict[str, Any]:
    if (
        not isinstance(cross_layer, dict)
        or not isinstance(finalization, dict)
        or not isinstance(governance_cp, dict)
        or not isinstance(gate_config, dict)
    ):
        return {
            "intelligence_gate_status": "invalid_input",
            "gate_phase": None,
            "active_signals": 0,
        }

    cl_aligned = cross_layer.get("cross_layer_status") == "aligned"
    fin_ok = finalization.get("finalization_status") in ("finalized", "pending")
    gov_op = governance_cp.get("governance_cp_status") == "operational"
    all_ok = cl_aligned and fin_ok and gov_op
    any_ok = cl_aligned or fin_ok or gov_op
    active_signals = sum([cl_aligned, fin_ok, gov_op])

    if all_ok:
        return {
            "intelligence_gate_status": "open",
            "gate_phase": cross_layer.get("aligned_phase"),
            "active_signals": active_signals,
        }

    if any_ok:
        return {
            "intelligence_gate_status": "partial",
            "gate_phase": None,
            "active_signals": active_signals,
        }

    return {
        "intelligence_gate_status": "closed",
        "gate_phase": None,
        "active_signals": active_signals,
    }
