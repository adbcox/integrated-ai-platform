from typing import Any

def acknowledge_delivery(tracking: Any, ack_signal: Any, ack_config: Any) -> dict[str, Any]:
    if not isinstance(tracking, dict) or not isinstance(ack_signal, dict):
        return {"delivery_acknowledgement_status": "not_acknowledged"}
    t_ok = tracking.get("delivery_tracking_status") == "tracking"
    if not t_ok:
        return {"delivery_acknowledgement_status": "not_acknowledged"}
    ack_result = ack_signal.get("ack_result")
    if ack_result != "accepted":
        return {"delivery_acknowledgement_status": "not_acknowledged"}
    return {
        "delivery_acknowledgement_status": "acknowledged",
        "adapter_id": tracking.get("adapter_id"),
        "ack_result": "accepted",
    }
