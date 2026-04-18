from typing import Any

def harness_segment_slo(input_dict):
    if not isinstance(input_dict, dict):
        return {"harness_segment_slo_status": "invalid_input"}
    return {"harness_segment_slo_status": "valid"}
