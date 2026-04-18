from typing import Any

def plan_remediation(incident_acknowledgement_receipt: Any, remedy_config: Any) -> dict[str, Any]:
    if not isinstance(incident_acknowledgement_receipt, dict):
        return {"remediation_plan_status": "not_planned"}
    ack_ok = incident_acknowledgement_receipt.get("incident_acknowledgement_receipt_status") == "received"
    if not ack_ok:
        return {"remediation_plan_status": "not_planned"}
    return {
        "remediation_plan_status": "planned",
        "plan_id": remedy_config.get("plan_id", "PLAN_0"),
    }
