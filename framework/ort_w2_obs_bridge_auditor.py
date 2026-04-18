from typing import Any

def obs_bridge_auditor(input_dict):
    if not isinstance(input_dict, dict):
        return {"obs_bridge_auditor_status": "invalid"}
    return {"obs_bridge_auditor_status": "ok"}
