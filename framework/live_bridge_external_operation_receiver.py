from typing import Any
def receive_external_operation(session_validation: dict[str, Any], ingress: dict[str, Any], operation: dict[str, Any]) -> dict[str, Any]:
    if not isinstance(session_validation, dict) or not isinstance(ingress, dict) or not isinstance(operation, dict):
        return {"operation_reception_status": "invalid_input", "received_operation_id": None, "received_operation_type": None, "received_session_id": None}
    sv_ok = session_validation.get("session_validation_status") == "valid"
    i_ok = ingress.get("ingress_channel_status") == "built"
    op_ok = bool(operation.get("operation_id")) and bool(operation.get("operation_type"))
    if sv_ok and i_ok and op_ok:
        return {"operation_reception_status": "received", "received_operation_id": operation.get("operation_id"), "received_operation_type": operation.get("operation_type"), "received_session_id": session_validation.get("validated_session_id")}
    return {"operation_reception_status": "no_session" if not sv_ok else ("no_ingress" if not i_ok else "invalid_operation"), "received_operation_id": None, "received_operation_type": None, "received_session_id": None}
