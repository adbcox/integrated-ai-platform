from typing import Any

def plan_reconciliation(receipt_publication: dict[str, Any], acknowledgement: dict[str, Any], planner_config: dict[str, Any]) -> dict[str, Any]:
    if not isinstance(receipt_publication, dict) or not isinstance(acknowledgement, dict) or not isinstance(planner_config, dict):
        return {"reconciliation_plan_status": "invalid_input", "reconciliation_operation_id": None, "reconciliation_plan_id": None}
    rp_ok = receipt_publication.get("receipt_publication_status") == "published"
    a_ok = acknowledgement.get("acknowledgement_status") == "acknowledged"
    if not rp_ok:
        return {"reconciliation_plan_status": "not_published", "reconciliation_operation_id": None, "reconciliation_plan_id": None}
    if rp_ok and not a_ok:
        return {"reconciliation_plan_status": "not_acknowledged", "reconciliation_operation_id": None, "reconciliation_plan_id": None}
    return {"reconciliation_plan_status": "planned", "reconciliation_operation_id": acknowledgement.get("acked_operation_id"), "reconciliation_plan_id": planner_config.get("plan_id", "rec-0001")} if rp_ok and a_ok else {"reconciliation_plan_status": "invalid_input", "reconciliation_operation_id": None, "reconciliation_plan_id": None}
