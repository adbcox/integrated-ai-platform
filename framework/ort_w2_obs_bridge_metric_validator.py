from typing import Any

def obs_bridge_metric_validator(input_dict):
    if not isinstance(input_dict, dict):
        return {"obs_bridge_metric_validator_status": "invalid"}
    return {"obs_bridge_metric_validator_status": "ok"}
