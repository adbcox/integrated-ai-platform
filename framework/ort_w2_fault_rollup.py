from typing import Any

def fault_rollup(input_dict):
    if not isinstance(input_dict, dict):
        return {"fault_rollup_status": "invalid"}
    return {"fault_rollup_status": "ok"}
