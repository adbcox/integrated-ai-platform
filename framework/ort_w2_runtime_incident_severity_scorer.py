from typing import Any

def runtime_incident_severity_scorer(input_dict):
    if not isinstance(input_dict, dict):
        return {"runtime_incident_severity_scorer_status": "invalid"}
    return {"runtime_incident_severity_scorer_status": "ok"}
