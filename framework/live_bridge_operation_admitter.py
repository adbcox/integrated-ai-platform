from typing import Any

def admit_operation(dequeue: dict[str, Any], rate_limit: dict[str, Any], admission_config: dict[str, Any]) -> dict[str, Any]:
    if not isinstance(dequeue, dict) or not isinstance(rate_limit, dict) or not isinstance(admission_config, dict):
        return {"admission_status": "invalid_input", "admitted_operation_id": None, "admitted_session_id": None, "admission_token": None}
    d_ok = dequeue.get("dequeue_status") == "dequeued"
    rl_ok = rate_limit.get("rate_limit_status") == "allowed"
    if not d_ok:
        return {"admission_status": "not_dequeued", "admitted_operation_id": None, "admitted_session_id": None, "admission_token": None}
    if d_ok and not rl_ok:
        return {"admission_status": "rate_limited", "admitted_operation_id": None, "admitted_session_id": None, "admission_token": None}
    return {"admission_status": "admitted", "admitted_operation_id": dequeue.get("dequeued_operation_id"), "admitted_session_id": dequeue.get("dequeued_session_id"), "admission_token": admission_config.get("token", "adm-0001")} if d_ok and rl_ok else {"admission_status": "invalid_input", "admitted_operation_id": None, "admitted_session_id": None, "admission_token": None}
