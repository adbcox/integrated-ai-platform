from typing import Any
def control_command_retry(retry_input):
    if not isinstance(retry_input, dict): return {"op_retry_control_status": "invalid"}
    if "retry_count" not in retry_input: return {"op_retry_control_status": "invalid"}
    return {"op_retry_control_status": "controlled", "retry_count": retry_input.get("retry_count")}
