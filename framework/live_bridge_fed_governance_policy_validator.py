from typing import Any

def validate_fed_policy(composition: dict, governance_cp: dict, validator_config: dict) -> dict:
    if not isinstance(composition, dict) or not isinstance(governance_cp, dict) or not isinstance(validator_config, dict):
        return {"fed_policy_validation_status": "invalid_input"}
    c_ok = composition.get("fed_policy_composition_status") == "composed"
    g_op = governance_cp.get("governance_cp_status") == "operational"
    if not c_ok:
        return {"fed_policy_validation_status": "not_composed"}
    if not g_op:
        return {"fed_policy_validation_status": "governance_offline"}
    return {
        "fed_policy_validation_status": "valid",
        "validated_fed_policy_id": composition.get("fed_policy_id"),
    }
