from typing import Any

def harness_segment_incident(input_dict):
    if not isinstance(input_dict, dict):
        return {"harness_segment_incident_status": "invalid_input"}
    return {"harness_segment_incident_status": "valid"}
