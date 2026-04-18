from typing import Any

def runtime_integrity_rollup(input_dict):
    if not isinstance(input_dict, dict):
        return {"runtime_integrity_rollup_status": "invalid"}
    return {"runtime_integrity_rollup_status": "ok"}
