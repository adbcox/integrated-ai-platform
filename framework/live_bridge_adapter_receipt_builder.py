from typing import Any

def build_adapter_receipt(delivery_ack: Any, adapter_dispatch: Any, builder_config: Any) -> dict[str, Any]:
    if not isinstance(delivery_ack, dict) or not isinstance(adapter_dispatch, dict):
        return {"adapter_receipt_status": "not_built"}
    d_ok = delivery_ack.get("delivery_acknowledgement_status") == "acknowledged"
    a_ok = adapter_dispatch.get("adapter_dispatch_status") == "dispatched"
    if not d_ok or not a_ok:
        return {"adapter_receipt_status": "not_built"}
    return {
        "adapter_receipt_status": "built",
        "adapter_id": adapter_dispatch.get("adapter_id"),
        "ack_timestamp": "receipt_generated",
    }
