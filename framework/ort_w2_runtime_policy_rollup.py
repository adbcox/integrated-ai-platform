from typing import Any

def runtime_policy_rollup(input_dict):
    if not isinstance(input_dict, dict):
        return {"runtime_policy_rollup_status": "invalid"}
    return {"runtime_policy_rollup_status": "ok"}
