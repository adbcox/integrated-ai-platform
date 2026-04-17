from typing import Any

def validate_operator_identity(registration: dict, governance_cp: dict, validator_config: dict) -> dict:
    if not isinstance(registration, dict) or not isinstance(governance_cp, dict) or not isinstance(validator_config, dict):
        return {"operator_identity_status": "invalid_input"}
    r_ok = registration.get("operator_registration_status") == "registered"
    g_op = governance_cp.get("governance_cp_status") == "operational"
    if not r_ok:
        return {"operator_identity_status": "not_registered"}
    if not g_op:
        return {"operator_identity_status": "governance_offline"}
    return {
        "operator_identity_status": "valid",
        "validated_operator_id": registration.get("operator_id"),
        "validated_operator_kind": registration.get("operator_kind"),
    }
