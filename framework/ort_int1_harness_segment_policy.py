from typing import Any

def harness_segment_policy(input_dict):
    if not isinstance(input_dict, dict):
        return {"harness_segment_policy_status": "invalid_input"}
    return {"harness_segment_policy_status": "valid"}
