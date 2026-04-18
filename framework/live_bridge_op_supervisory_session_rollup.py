from typing import Any
def rollup_supervisory_session(rollup_input):
    if not isinstance(rollup_input, dict): return {"op_supervisory_session_rollup_status": "invalid"}
    if rollup_input.get("op_supervisory_session_seal_status") != "sealed": return {"op_supervisory_session_rollup_status": "invalid"}
    return {"op_supervisory_session_rollup_status": "rolled_up"}
