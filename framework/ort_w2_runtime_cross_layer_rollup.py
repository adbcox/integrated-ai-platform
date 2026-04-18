from typing import Any

def runtime_cross_layer_rollup(input_dict):
    if not isinstance(input_dict, dict):
        return {"runtime_cross_layer_rollup_status": "invalid"}
    return {"runtime_cross_layer_rollup_status": "ok"}
