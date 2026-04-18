from typing import Any

def entry_control_plane(input_dict):
    if not isinstance(input_dict, dict):
        return {"entry_control_plane_status": "invalid"}
    return {"entry_control_plane_status": "operative"}
