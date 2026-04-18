from typing import Any

def harness_segment_obs_bridge(input_dict):
    if not isinstance(input_dict, dict):
        return {"harness_segment_obs_bridge_status": "invalid_input"}
    return {"harness_segment_obs_bridge_status": "valid"}
