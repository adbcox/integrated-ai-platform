from typing import Any

def runtime_incident_rollup(input_dict):
    if not isinstance(input_dict, dict):
        return {"runtime_incident_rollup_status": "invalid"}
    return {"runtime_incident_rollup_status": "ok"}
