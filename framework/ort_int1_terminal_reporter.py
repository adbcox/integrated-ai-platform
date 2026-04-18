from typing import Any

def terminal_reporter(input_dict):
    if not isinstance(input_dict, dict):
        return {"terminal_reporter_status": "invalid_input"}
    return {"terminal_reporter_status": "valid"}
