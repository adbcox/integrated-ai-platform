from typing import Any

def rollup_deliveries(adapter_dispatch: Any, delivery_ack: Any, adapter_receipt_publication: Any) -> dict[str, Any]:
    if not isinstance(adapter_dispatch, dict) or not isinstance(delivery_ack, dict) or not isinstance(adapter_receipt_publication, dict):
        return {"delivery_rollup_status": "failed"}
    d_ok = adapter_dispatch.get("adapter_dispatch_status") == "dispatched"
    a_ok = delivery_ack.get("delivery_acknowledgement_status") == "acknowledged"
    p_ok = adapter_receipt_publication.get("adapter_receipt_publication_status") == "published"
    if not d_ok or not a_ok or not p_ok:
        return {"delivery_rollup_status": "failed"}
    return {
        "delivery_rollup_status": "rolled_up",
        "delivery_count": 1,
    }
