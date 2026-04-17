from typing import Any

def dispatch_operation(admission: dict[str, Any], backpressure: dict[str, Any], dispatcher_config: dict[str, Any]) -> dict[str, Any]:
    if not isinstance(admission, dict) or not isinstance(backpressure, dict) or not isinstance(dispatcher_config, dict):
        return {"dispatch_status": "invalid_input", "dispatched_operation_id": None, "dispatched_session_id": None, "dispatch_ticket": None}
    a_ok = admission.get("admission_status") == "admitted"
    bp_ok = backpressure.get("backpressure_status") == "normal"
    if not a_ok:
        return {"dispatch_status": "not_admitted", "dispatched_operation_id": None, "dispatched_session_id": None, "dispatch_ticket": None}
    if a_ok and not bp_ok:
        return {"dispatch_status": "backpressured", "dispatched_operation_id": None, "dispatched_session_id": None, "dispatch_ticket": None}
    return {"dispatch_status": "dispatched", "dispatched_operation_id": admission.get("admitted_operation_id"), "dispatched_session_id": admission.get("admitted_session_id"), "dispatch_ticket": dispatcher_config.get("ticket", "tkt-0001")} if a_ok and bp_ok else {"dispatch_status": "invalid_input", "dispatched_operation_id": None, "dispatched_session_id": None, "dispatch_ticket": None}
