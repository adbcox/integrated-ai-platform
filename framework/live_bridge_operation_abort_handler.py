from typing import Any

def handle_abort(tracking: dict[str, Any], abort_reason: dict[str, Any], handler_config: dict[str, Any]) -> dict[str, Any]:
    if not isinstance(tracking, dict) or not isinstance(abort_reason, dict) or not isinstance(handler_config, dict):
        return {"abort_status": "invalid_input", "aborted_operation_id": None, "abort_reason_code": None}
    t_ok = tracking.get("execution_tracking_status") == "tracking"
    ar_valid = isinstance(abort_reason, dict) and bool(abort_reason.get("reason"))
    if not t_ok:
        return {"abort_status": "not_tracking", "aborted_operation_id": None, "abort_reason_code": None}
    if t_ok and not ar_valid:
        return {"abort_status": "no_reason", "aborted_operation_id": None, "abort_reason_code": None}
    return {"abort_status": "aborted", "aborted_operation_id": tracking.get("tracked_operation_id"), "abort_reason_code": abort_reason.get("reason")} if t_ok and ar_valid else {"abort_status": "invalid_input", "aborted_operation_id": None, "abort_reason_code": None}
