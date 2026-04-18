from typing import Any

def classify_incident(incident_intake: Any, classifier_config: Any) -> dict[str, Any]:
    if not isinstance(incident_intake, dict):
        return {"incident_classification_status": "not_classified"}
    intake_ok = incident_intake.get("incident_intake_status") == "received"
    if not intake_ok:
        return {"incident_classification_status": "not_classified"}
    return {
        "incident_classification_status": "classified",
        "incident_class": "service_degradation",
    }
