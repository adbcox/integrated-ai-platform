from typing import Any

def deployment_activation_rollup(input_dict):
    if not isinstance(input_dict, dict):
        return {"deployment_activation_rollup_status": "invalid"}
    return {"deployment_activation_rollup_status": "ok"}
