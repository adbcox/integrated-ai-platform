from typing import Any

def runtime_slo_rollup(input_dict):
    if not isinstance(input_dict, dict):
        return {"runtime_slo_rollup_status": "invalid"}
    return {"runtime_slo_rollup_status": "ok"}
