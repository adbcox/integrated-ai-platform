from typing import Any

def rollout_auditor(input_dict):
    if not isinstance(input_dict, dict):
        return {"rollout_auditor_status": "invalid"}
    return {"rollout_auditor_status": "ok"}
