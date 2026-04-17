from typing import Any

def validate_quorum(quorum: dict, governance_cp: dict, validator_config: dict) -> dict:
    if not isinstance(quorum, dict) or not isinstance(governance_cp, dict) or not isinstance(validator_config, dict):
        return {"quorum_validation_status": "invalid_input"}
    q_ok = quorum.get("quorum_composition_status") == "composed"
    g_op = governance_cp.get("governance_cp_status") == "operational"
    if not q_ok:
        return {"quorum_validation_status": "no_quorum"}
    if not g_op:
        return {"quorum_validation_status": "governance_offline"}
    return {
        "quorum_validation_status": "valid",
        "validated_quorum_id": quorum.get("quorum_id"),
        "validated_quorum_size": quorum.get("quorum_size", 0),
    }
