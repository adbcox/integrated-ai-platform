from typing import Any

def b17_release_layer_sealer(input_dict):
    if not isinstance(input_dict, dict):
        return {"release_layer_seal_status": "invalid_input"}
    if input_dict.get("pgs_w1_seal") != "sealed":
        return {"release_layer_seal_status": "upstream_not_sealed"}
    return {"release_layer_seal_status": "ok"}
