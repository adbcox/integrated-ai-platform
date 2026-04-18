from typing import Any

def harness_segment_workload(input_dict):
    if not isinstance(input_dict, dict):
        return {"harness_segment_workload_status": "invalid_input"}
    return {"harness_segment_workload_status": "valid"}
