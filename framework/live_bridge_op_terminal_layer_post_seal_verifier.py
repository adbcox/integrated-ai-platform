from typing import Any
def verify_terminal_post_seal(verify_input):
    if not isinstance(verify_input, dict): return {"op_terminal_post_seal_verification_status": "invalid"}
    if verify_input.get("operator_terminal_seal_status") != "sealed": return {"op_terminal_post_seal_verification_status": "invalid"}
    return {"op_terminal_post_seal_verification_status": "verified"}
