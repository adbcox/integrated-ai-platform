from typing import Any

def ingress_rollup(input_dict):
    if not isinstance(input_dict, dict):
        return {"ingress_rollup_status": "invalid"}
    return {"ingress_rollup_status": "rolled_up"}
