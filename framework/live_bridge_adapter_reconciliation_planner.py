from typing import Any

def plan_adapter_reconciliation(publication: Any, delivery_ack: Any, planner_config: Any) -> dict[str, Any]:
    if not isinstance(publication, dict) or not isinstance(delivery_ack, dict):
        return {"adapter_reconciliation_plan_status": "failed"}
    p_ok = publication.get("adapter_receipt_publication_status") == "published"
    d_ok = delivery_ack.get("delivery_acknowledgement_status") == "acknowledged"
    if not p_ok or not d_ok:
        return {"adapter_reconciliation_plan_status": "failed"}
    return {
        "adapter_reconciliation_plan_status": "planned",
        "adapter_id": publication.get("adapter_id"),
        "receipt_id": publication.get("adapter_id"),
    }
