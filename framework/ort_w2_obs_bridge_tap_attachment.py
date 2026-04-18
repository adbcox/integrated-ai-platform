from typing import Any

def obs_bridge_tap_attachment(input_dict):
    if not isinstance(input_dict, dict):
        return {"obs_bridge_tap_attachment_status": "invalid"}
    return {"obs_bridge_tap_attachment_status": "ok"}
