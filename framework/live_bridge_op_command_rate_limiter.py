from typing import Any
def limit_command_rate(rate_input):
    if not isinstance(rate_input, dict): return {"op_rate_limit_status": "invalid"}
    current = rate_input.get("current_count", 0)
    max_val = rate_input.get("max_count", 1)
    if current >= max_val: return {"op_rate_limit_status": "exceeded"}
    return {"op_rate_limit_status": "limited", "current_count": current}
