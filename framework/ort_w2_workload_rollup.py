from typing import Any

def workload_rollup(input_dict):
    if not isinstance(input_dict, dict):
        return {"workload_rollup_status": "invalid"}
    return {"workload_rollup_status": "ok"}
