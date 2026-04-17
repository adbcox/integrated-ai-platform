from typing import Any

def inspect_queue(enqueue: dict[str, Any], inspector_config: dict[str, Any], tracker_state: dict[str, Any]) -> dict[str, Any]:
    if not isinstance(enqueue, dict) or not isinstance(inspector_config, dict) or not isinstance(tracker_state, dict):
        return {"inspector_status": "invalid_input", "depth": 0, "inspected_operation_id": None, "inspector_at_tick": 0}
    return {"inspector_status": "inspected", "depth": int(tracker_state.get("depth", 0)), "inspected_operation_id": enqueue.get("queued_operation_id"), "inspector_at_tick": inspector_config.get("tick", 0)}
