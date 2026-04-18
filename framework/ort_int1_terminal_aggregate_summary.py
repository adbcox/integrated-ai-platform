from typing import Any

def terminal_aggregate_summary(input_dict):
    if not isinstance(input_dict, dict):
        return {"terminal_aggregate_summary_status": "invalid_input"}
    return {"terminal_aggregate_summary_status": "valid"}
