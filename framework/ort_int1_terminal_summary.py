from typing import Any

def terminal_summary(input_dict):
    if not isinstance(input_dict, dict):
        return {"terminal_summary_status": "invalid_input"}
    return {"terminal_summary_status": "valid"}
