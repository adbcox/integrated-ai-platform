from typing import Any

def runtime_tick_validator(input_dict):
    if not isinstance(input_dict, dict):
        return {"runtime_tick_validator_status": "invalid"}
    return {"runtime_tick_validator_status": "ok"}
