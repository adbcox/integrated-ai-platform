from typing import Any

def b19_change_freeze_sealer(input_dict):
    if not isinstance(input_dict, dict):
        return {"change_freeze_seal_status": "invalid_input"}
    if input_dict.get("change_control_seal") != "sealed":
        return {"change_freeze_seal_status": "upstream_not_sealed"}
    if input_dict.get("release_layer_seal") != "sealed":
        return {"change_freeze_seal_status": "upstream_not_sealed"}
    return {"change_freeze_seal_status": "ok"}
