from typing import Any

def harness_segment_fault(input_dict):
    if not isinstance(input_dict, dict):
        return {"harness_segment_fault_status": "invalid_input"}
    return {"harness_segment_fault_status": "valid"}
