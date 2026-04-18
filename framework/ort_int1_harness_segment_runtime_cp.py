from typing import Any

def harness_segment_runtime_cp(input_dict):
    if not isinstance(input_dict, dict):
        return {"harness_segment_runtime_cp_status": "invalid_input"}
    return {"harness_segment_runtime_cp_status": "valid"}
