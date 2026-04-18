from typing import Any

def b18_change_control_sealer(input_dict):
    if not isinstance(input_dict, dict):
        return {"change_control_seal_status": "invalid_input"}
    if input_dict.get("release_layer_seal") != "sealed":
        return {"change_control_seal_status": "upstream_not_sealed"}
    return {"change_control_seal_status": "ok"}
