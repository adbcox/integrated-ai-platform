from typing import Any
def route_to_autonomy(authorization: dict[str, Any], autonomy_cp: dict[str, Any], router_config: dict[str, Any]) -> dict[str, Any]:
    if not isinstance(authorization, dict) or not isinstance(autonomy_cp, dict) or not isinstance(router_config, dict):
        return {"autonomy_routing_status": "invalid_input", "routed_operation_id": None, "routed_to_phase": None}
    a_ok = authorization.get("operation_authorization_status") == "authorized"
    acp_ok = autonomy_cp.get("autonomy_cp_status") == "operational"
    if a_ok and acp_ok:
        return {"autonomy_routing_status": "routed", "routed_operation_id": authorization.get("authorized_operation_id"), "routed_to_phase": autonomy_cp.get("autonomy_phase")}
    return {"autonomy_routing_status": "not_authorized" if not a_ok else "autonomy_offline", "routed_operation_id": None, "routed_to_phase": None}
