from typing import Any

def correlate_acknowledgements(remediation_rollback_control: Any, incident_intake: Any) -> dict[str, Any]:
    if not isinstance(remediation_rollback_control, dict) or not isinstance(incident_intake, dict):
        return {"ack_correlation_status": "not_correlated"}
    rollback_ok = remediation_rollback_control.get("remediation_rollback_control_status") == "controlled"
    intake_ok = incident_intake.get("incident_intake_status") == "received"
    if not rollback_ok or not intake_ok:
        return {"ack_correlation_status": "not_correlated"}
    return {
        "ack_correlation_status": "correlated",
        "correlated_count": 1,
    }
