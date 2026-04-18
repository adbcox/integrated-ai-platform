from typing import Any

def close_incident(ack_correlation: Any, incident_closure_config: Any) -> dict[str, Any]:
    if not isinstance(ack_correlation, dict):
        return {"incident_closure_status": "not_closed"}
    corr_ok = ack_correlation.get("ack_correlation_status") == "correlated"
    if not corr_ok:
        return {"incident_closure_status": "not_closed"}
    return {
        "incident_closure_status": "closed",
        "closure_reason": incident_closure_config.get("closure_reason", "resolved"),
    }
