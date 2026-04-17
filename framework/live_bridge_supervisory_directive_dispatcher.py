from typing import Any

def dispatch_directive(authorization: dict, fed_cp: dict, dispatcher_config: dict) -> dict:
    if not isinstance(authorization, dict) or not isinstance(fed_cp, dict) or not isinstance(dispatcher_config, dict):
        return {"directive_dispatch_status": "invalid_input"}
    a_ok = authorization.get("directive_authorization_status") == "authorized"
    cp_op = fed_cp.get("fed_cp_status") == "operational"
    if not a_ok:
        return {"directive_dispatch_status": "not_authorized"}
    if not cp_op:
        return {"directive_dispatch_status": "fed_offline"}
    return {
        "directive_dispatch_status": "dispatched",
        "dispatched_directive_id": authorization.get("authorized_directive_id"),
        "dispatch_target_env_id": fed_cp.get("fed_cp_env_id"),
        "dispatch_ticket": dispatcher_config.get("ticket", "dtkt-0001"),
    }
