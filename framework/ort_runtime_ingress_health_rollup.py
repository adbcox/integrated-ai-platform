from typing import Any

def ingress_health_rollup(input_dict):
    if not isinstance(input_dict, dict):
        return {"ingress_health_rollup_status": "invalid"}
    return {"ingress_health_rollup_status": "rolled_up"}
