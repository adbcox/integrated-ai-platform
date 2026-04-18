from typing import Any

def runtime_policy_summary(input_dict):
    if not isinstance(input_dict, dict):
        return {"runtime_policy_summary_status": "invalid"}
    return {"runtime_policy_summary_status": "ok"}
