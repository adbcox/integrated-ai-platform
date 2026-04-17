from typing import Any

def track_execution(binding: dict[str, Any], progress_signal: dict[str, Any], tracker_config: dict[str, Any]) -> dict[str, Any]:
    if not isinstance(binding, dict) or not isinstance(progress_signal, dict) or not isinstance(tracker_config, dict):
        return {"execution_tracking_status": "invalid_input", "tracked_operation_id": None, "tracked_progress_id": None, "tracked_stage": None}
    b_ok = binding.get("executor_binding_status") == "bound"
    ps_valid = isinstance(progress_signal, dict) and bool(progress_signal.get("progress_id"))
    if not b_ok:
        return {"execution_tracking_status": "no_binding", "tracked_operation_id": None, "tracked_progress_id": None, "tracked_stage": None}
    if b_ok and not ps_valid:
        return {"execution_tracking_status": "no_progress", "tracked_operation_id": None, "tracked_progress_id": None, "tracked_stage": None}
    return {"execution_tracking_status": "tracking", "tracked_operation_id": binding.get("bound_operation_id"), "tracked_progress_id": progress_signal.get("progress_id"), "tracked_stage": progress_signal.get("stage", "running")} if b_ok and ps_valid else {"execution_tracking_status": "invalid_input", "tracked_operation_id": None, "tracked_progress_id": None, "tracked_stage": None}
