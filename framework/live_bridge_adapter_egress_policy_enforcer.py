from typing import Any

def enforce_egress_policy(egress_policy: Any, payload_validation: Any, enforcer_config: Any) -> dict[str, Any]:
    if not isinstance(egress_policy, dict) or not isinstance(payload_validation, dict):
        return {"egress_policy_enforcement_status": "denied"}
    e_ok = egress_policy.get("egress_policy_resolution_status") == "resolved"
    p_ok = payload_validation.get("payload_validation_status") == "valid"
    if not e_ok or not p_ok:
        return {"egress_policy_enforcement_status": "denied"}
    return {
        "egress_policy_enforcement_status": "allowed",
        "schema_id": payload_validation.get("schema_id"),
    }
