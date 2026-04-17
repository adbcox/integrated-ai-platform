from typing import Any


def finalize_learning(
    intelligence_gate: dict[str, Any],
    knowledge_validation: dict[str, Any],
    learning_cp: dict[str, Any],
) -> dict[str, Any]:
    if (
        not isinstance(intelligence_gate, dict)
        or not isinstance(knowledge_validation, dict)
        or not isinstance(learning_cp, dict)
    ):
        return {
            "learning_finalization_status": "invalid_input",
            "finalized_phase": None,
            "knowledge_complete": False,
        }

    gate_open = intelligence_gate.get("intelligence_gate_status") == "open"
    kv_valid = knowledge_validation.get("knowledge_validation_status") == "valid"
    cp_op = learning_cp.get("learning_cp_status") == "operational"
    all_ok = gate_open and kv_valid and cp_op
    any_ok = gate_open or kv_valid or cp_op

    if all_ok:
        return {
            "learning_finalization_status": "finalized",
            "finalized_phase": learning_cp.get("learning_phase"),
            "knowledge_complete": knowledge_validation.get("knowledge_complete", False),
        }

    if any_ok:
        return {
            "learning_finalization_status": "pending",
            "finalized_phase": None,
            "knowledge_complete": False,
        }

    return {
        "learning_finalization_status": "blocked",
        "finalized_phase": None,
        "knowledge_complete": False,
    }
