from typing import Any

def build_adapter_control_plane(adapter_validation: Any, adapter_rollup: Any, event_bus: Any) -> dict[str, Any]:
    if not isinstance(adapter_validation, dict) or not isinstance(adapter_rollup, dict) or not isinstance(event_bus, dict):
        return {"adapter_cp_status": "failed"}
    v_ok = adapter_validation.get("adapter_validation_status") == "valid"
    r_ok = adapter_rollup.get("adapter_rollup_status") == "rolled_up"
    msg_count = event_bus.get("message_count", 0)
    if not v_ok or not r_ok or msg_count < 0:
        return {"adapter_cp_status": "failed"}
    return {
        "adapter_cp_status": "operational",
        "message_count": msg_count,
    }
