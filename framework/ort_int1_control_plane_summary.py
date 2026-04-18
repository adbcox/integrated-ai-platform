from typing import Any

def control_plane_summary(input_dict):
    if not isinstance(input_dict, dict):
        return {"control_plane_summary_status": "invalid_input"}
    return {"control_plane_summary_status": "valid"}
