from typing import Any

def runtime_incident_classifier(input_dict):
    if not isinstance(input_dict, dict):
        return {"runtime_incident_classifier_status": "invalid"}
    return {"runtime_incident_classifier_status": "ok"}
