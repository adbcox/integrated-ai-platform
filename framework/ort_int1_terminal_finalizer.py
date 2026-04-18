from typing import Any

def terminal_finalizer(input_dict):
    if not isinstance(input_dict, dict):
        return {"terminal_finalizer_status": "invalid_input"}
    return {"terminal_finalizer_status": "valid"}
