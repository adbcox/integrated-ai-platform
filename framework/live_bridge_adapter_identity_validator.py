from typing import Any

def validate_adapter_identity(registration: Any, governance_cp: Any, validator_config: Any) -> dict[str, Any]:
    if not isinstance(registration, dict) or not isinstance(governance_cp, dict):
        return {"adapter_identity_validation_status": "invalid_input"}
    r_ok = registration.get("adapter_registration_status") == "registered"
    g_ok = governance_cp.get("governance_cp_status") == "operational"
    if not r_ok or not g_ok:
        return {"adapter_identity_validation_status": "invalid_input"}
    return {
        "adapter_identity_validation_status": "valid",
        "adapter_id": registration.get("adapter_id"),
        "governance_operational": True,
    }
