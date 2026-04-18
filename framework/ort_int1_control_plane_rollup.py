from typing import Any

def control_plane_rollup(input_dict):
    if not isinstance(input_dict, dict):
        return {"control_plane_rollup_status": "invalid_input"}
    return {"control_plane_rollup_status": "valid"}
