from typing import Any

def score_incident_severity(incident_classifier: Any, severity_config: Any) -> dict[str, Any]:
    if not isinstance(incident_classifier, dict):
        return {"incident_severity_scoring_status": "not_scored"}
    class_ok = incident_classifier.get("incident_classification_status") == "classified"
    if not class_ok:
        return {"incident_severity_scoring_status": "not_scored"}
    return {
        "incident_severity_scoring_status": "scored",
        "severity_level": "P2",
        "severity_score": 7,
    }
