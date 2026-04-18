from typing import Any

def intake_incident(signal_throttling: Any, incident_config: Any) -> dict[str, Any]:
    if not isinstance(signal_throttling, dict):
        return {"incident_intake_status": "not_received"}
    throttle_ok = signal_throttling.get("signal_throttling_status") == "throttled"
    if not throttle_ok:
        return {"incident_intake_status": "not_received"}
    return {
        "incident_intake_status": "received",
        "incident_id": incident_config.get("incident_id", "INC_0"),
    }
