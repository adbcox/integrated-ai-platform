from typing import Any

def resource_saturation_detector(input_dict):
    if not isinstance(input_dict, dict):
        return {"resource_saturation_detector_status": "invalid"}
    return {"resource_saturation_detector_status": "ok"}
