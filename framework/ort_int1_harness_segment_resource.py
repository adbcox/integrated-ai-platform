from typing import Any

def harness_segment_resource(input_dict):
    if not isinstance(input_dict, dict):
        return {"harness_segment_resource_status": "invalid_input"}
    return {"harness_segment_resource_status": "valid"}
