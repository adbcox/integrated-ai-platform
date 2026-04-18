from typing import Any

def control_plane_descriptor(input_dict):
    if not isinstance(input_dict, dict):
        return {"control_plane_descriptor_status": "invalid_input"}
    return {"control_plane_descriptor_status": "valid"}
