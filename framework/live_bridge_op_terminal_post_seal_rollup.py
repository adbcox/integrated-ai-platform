from typing import Any
def rollup_terminal_post_seal(rollup_input):
    if not isinstance(rollup_input, dict): return {"op_terminal_post_seal_rollup_status": "invalid"}
    if rollup_input.get("op_terminal_post_seal_verification_status") != "verified": return {"op_terminal_post_seal_rollup_status": "invalid"}
    return {"op_terminal_post_seal_rollup_status": "rolled_up"}
