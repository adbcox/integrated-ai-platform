from typing import Any

def control_plane_completion_reporter(input_dict):
    if not isinstance(input_dict, dict):
        return {"control_plane_completion_reporter_status": "invalid_input"}
    return {"control_plane_completion_reporter_status": "valid"}
