from typing import Any


def finalize_decision(
    autonomous_gate: dict[str, Any],
    decision_validation: dict[str, Any],
    autonomy_cp: dict[str, Any],
) -> dict[str, Any]:
    if (
        not isinstance(autonomous_gate, dict)
        or not isinstance(decision_validation, dict)
        or not isinstance(autonomy_cp, dict)
    ):
        return {
            "decision_finalization_status": "invalid_input",
            "finalized_phase": None,
            "finalized_decision": None,
        }

    gate_open = autonomous_gate.get("autonomous_gate_status") == "open"
    dv_valid = decision_validation.get("decision_validation_status") == "valid"
    cp_op = autonomy_cp.get("autonomy_cp_status") == "operational"

    all_ok = gate_open and dv_valid and cp_op
    any_ok = gate_open or dv_valid or cp_op

    if all_ok:
        return {
            "decision_finalization_status": "finalized",
            "finalized_phase": autonomy_cp.get("autonomy_phase"),
            "finalized_decision": decision_validation.get("validated_decision"),
        }

    if any_ok:
        return {
            "decision_finalization_status": "pending",
            "finalized_phase": None,
            "finalized_decision": None,
        }

    return {
        "decision_finalization_status": "blocked",
        "finalized_phase": None,
        "finalized_decision": None,
    }
