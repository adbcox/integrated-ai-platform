from typing import Any

def dequeue_operation(queue_snapshot: dict[str, Any], inspector_result: dict[str, Any], dequeue_config: dict[str, Any]) -> dict[str, Any]:
    if not isinstance(queue_snapshot, dict) or not isinstance(inspector_result, dict) or not isinstance(dequeue_config, dict):
        return {"dequeue_status": "invalid_input", "dequeued_operation_id": None, "dequeued_session_id": None}
    q_ok = queue_snapshot.get("enqueue_status") == "enqueued"
    i_ok = inspector_result.get("inspector_status") == "inspected"
    if not q_ok and i_ok:
        return {"dequeue_status": "empty", "dequeued_operation_id": None, "dequeued_session_id": None}
    return {"dequeue_status": "dequeued", "dequeued_operation_id": queue_snapshot.get("queued_operation_id"), "dequeued_session_id": queue_snapshot.get("queued_session_id")} if q_ok and i_ok else {"dequeue_status": "invalid_input", "dequeued_operation_id": None, "dequeued_session_id": None}
