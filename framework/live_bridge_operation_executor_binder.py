from typing import Any

def bind_executor(dispatch: dict[str, Any], autonomy_routing: dict[str, Any], binder_config: dict[str, Any]) -> dict[str, Any]:
    if not isinstance(dispatch, dict) or not isinstance(autonomy_routing, dict) or not isinstance(binder_config, dict):
        return {"executor_binding_status": "invalid_input", "bound_operation_id": None, "bound_to_phase": None, "executor_binding_id": None}
    d_ok = dispatch.get("dispatch_status") == "dispatched"
    ar_ok = autonomy_routing.get("autonomy_routing_status") == "routed"
    if not d_ok:
        return {"executor_binding_status": "not_dispatched", "bound_operation_id": None, "bound_to_phase": None, "executor_binding_id": None}
    if d_ok and not ar_ok:
        return {"executor_binding_status": "not_routed", "bound_operation_id": None, "bound_to_phase": None, "executor_binding_id": None}
    return {"executor_binding_status": "bound", "bound_operation_id": dispatch.get("dispatched_operation_id"), "bound_to_phase": autonomy_routing.get("routed_to_phase"), "executor_binding_id": binder_config.get("binding_id", "exb-0001")} if d_ok and ar_ok else {"executor_binding_status": "invalid_input", "bound_operation_id": None, "bound_to_phase": None, "executor_binding_id": None}
