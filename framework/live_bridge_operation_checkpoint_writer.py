from typing import Any

def write_operation_checkpoint(tracking: dict[str, Any], snapshot_data: dict[str, Any], writer_config: dict[str, Any]) -> dict[str, Any]:
    if not isinstance(tracking, dict) or not isinstance(snapshot_data, dict) or not isinstance(writer_config, dict):
        return {"checkpoint_status": "invalid_input", "checkpoint_operation_id": None, "checkpoint_id": None, "checkpoint_stage": None}
    t_ok = tracking.get("execution_tracking_status") == "tracking"
    if not t_ok:
        return {"checkpoint_status": "no_tracking", "checkpoint_operation_id": None, "checkpoint_id": None, "checkpoint_stage": None}
    return {"checkpoint_status": "written", "checkpoint_operation_id": tracking.get("tracked_operation_id"), "checkpoint_id": writer_config.get("checkpoint_id", "ckp-0001"), "checkpoint_stage": tracking.get("tracked_stage")}
