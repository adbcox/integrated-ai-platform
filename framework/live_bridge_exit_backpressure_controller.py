from typing import Any
def control_exit_backpressure(bp_input):
    if not isinstance(bp_input, dict): return {"exit_backpressure_status": "invalid"}
    current = bp_input.get("current_pressure", 0)
    max_val = bp_input.get("max_pressure", 1)
    if current >= max_val: return {"exit_backpressure_status": "exceeded"}
    return {"exit_backpressure_status": "controlled", "current_pressure": current}
