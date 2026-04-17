from typing import Any

def bind_operator_scope(authority: dict, fed_cp: dict, scope_config: dict) -> dict:
    if not isinstance(authority, dict) or not isinstance(fed_cp, dict) or not isinstance(scope_config, dict):
        return {"scope_binding_status": "invalid_input"}
    a_ok = authority.get("authority_resolution_status") == "resolved"
    cp_op = fed_cp.get("fed_cp_status") == "operational"
    if not a_ok:
        return {"scope_binding_status": "no_authority"}
    if not cp_op:
        return {"scope_binding_status": "fed_offline"}
    return {
        "scope_binding_status": "bound",
        "bound_operator_id": authority.get("authority_operator_id"),
        "bound_fed_env_id": fed_cp.get("fed_cp_env_id"),
        "scope_tag": scope_config.get("scope", "federation"),
    }
