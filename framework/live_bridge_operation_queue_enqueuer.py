from typing import Any

def enqueue_operation(reception: dict[str, Any], authorization: dict[str, Any], enqueue_config: dict[str, Any]) -> dict[str, Any]:
    if not isinstance(reception, dict) or not isinstance(authorization, dict) or not isinstance(enqueue_config, dict):
        return {"enqueue_status": "invalid_input", "queued_operation_id": None, "queued_session_id": None, "queue_position": 0}
    r_ok = reception.get("operation_reception_status") == "received"
    a_ok = authorization.get("operation_authorization_status") == "authorized"
    if not r_ok:
        return {"enqueue_status": "no_reception", "queued_operation_id": None, "queued_session_id": None, "queue_position": 0}
    if r_ok and not a_ok:
        return {"enqueue_status": "not_authorized", "queued_operation_id": None, "queued_session_id": None, "queue_position": 0}
    return {"enqueue_status": "enqueued", "queued_operation_id": reception.get("received_operation_id"), "queued_session_id": reception.get("received_session_id"), "queue_position": enqueue_config.get("position", 1)} if r_ok and a_ok else {"enqueue_status": "invalid_input", "queued_operation_id": None, "queued_session_id": None, "queue_position": 0}
