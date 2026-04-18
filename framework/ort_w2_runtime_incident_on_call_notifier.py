from typing import Any

def runtime_incident_on_call_notifier(input_dict):
    if not isinstance(input_dict, dict):
        return {"runtime_incident_on_call_notifier_status": "invalid"}
    return {"runtime_incident_on_call_notifier_status": "ok"}
