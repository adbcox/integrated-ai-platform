from typing import Any

def runtime_incident_postmortem_builder(input_dict):
    if not isinstance(input_dict, dict):
        return {"runtime_incident_postmortem_builder_status": "invalid"}
    return {"runtime_incident_postmortem_builder_status": "ok"}
