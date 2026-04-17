from typing import Any

def detect_completion(tracking: dict[str, Any], completion_signal: dict[str, Any], detector_config: dict[str, Any]) -> dict[str, Any]:
    if not isinstance(tracking, dict) or not isinstance(completion_signal, dict) or not isinstance(detector_config, dict):
        return {"completion_status": "invalid_input", "completed_operation_id": None, "completion_outcome": None}
    t_ok = tracking.get("execution_tracking_status") == "tracking"
    cs_complete = isinstance(completion_signal, dict) and completion_signal.get("stage") == "finished"
    cs_running = isinstance(completion_signal, dict) and completion_signal.get("stage") in ("running", "pending")
    if not t_ok:
        return {"completion_status": "not_tracking", "completed_operation_id": None, "completion_outcome": None}
    if t_ok and cs_running:
        return {"completion_status": "running", "completed_operation_id": None, "completion_outcome": None}
    if t_ok and cs_complete:
        return {"completion_status": "completed", "completed_operation_id": tracking.get("tracked_operation_id"), "completion_outcome": completion_signal.get("outcome", "success")}
    return {"completion_status": "invalid_input", "completed_operation_id": None, "completion_outcome": None}
