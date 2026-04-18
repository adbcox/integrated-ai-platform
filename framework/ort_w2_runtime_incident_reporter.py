from typing import Any

def runtime_incident_reporter(input_dict):
    if not isinstance(input_dict, dict):
        return {"runtime_incident_reporter_status": "invalid"}
    return {"runtime_incident_reporter_status": "ok"}
