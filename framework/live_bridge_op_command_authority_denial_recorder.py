from typing import Any
def record_command_denial(denial_input):
    if not isinstance(denial_input, dict): return {"op_denial_record_status": "invalid"}
    if "denial_reason" not in denial_input: return {"op_denial_record_status": "invalid"}
    return {"op_denial_record_status": "recorded", "denial_reason": denial_input.get("denial_reason")}
