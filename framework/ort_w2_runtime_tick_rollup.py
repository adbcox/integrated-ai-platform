from typing import Any

def runtime_tick_rollup(input_dict):
    if not isinstance(input_dict, dict):
        return {"runtime_tick_rollup_status": "invalid"}
    return {"runtime_tick_rollup_status": "ok"}
