from typing import Any

def fault_failure_detector(input_dict):
    if not isinstance(input_dict, dict):
        return {"fault_failure_detector_status": "invalid"}
    return {"fault_failure_detector_status": "ok"}
