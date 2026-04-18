from typing import Any

def track_delivery(adapter_dispatch: Any, progress_signal: Any, tracker_config: Any) -> dict[str, Any]:
    if not isinstance(adapter_dispatch, dict) or not isinstance(progress_signal, dict):
        return {"delivery_tracking_status": "invalid"}
    d_ok = adapter_dispatch.get("adapter_dispatch_status") == "dispatched"
    if not d_ok:
        return {"delivery_tracking_status": "invalid"}
    progress = progress_signal.get("progress_value", 0)
    return {
        "delivery_tracking_status": "tracking",
        "adapter_id": adapter_dispatch.get("adapter_id"),
        "progress_value": progress,
    }
