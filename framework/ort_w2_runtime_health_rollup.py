from typing import Any

def runtime_health_rollup(input_dict):
    if not isinstance(input_dict, dict):
        return {"runtime_health_rollup_status": "invalid"}
    return {"runtime_health_rollup_status": "ok"}
