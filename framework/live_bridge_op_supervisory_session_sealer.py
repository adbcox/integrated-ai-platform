from typing import Any
def seal_supervisory_session(seal_input):
    if not isinstance(seal_input, dict): return {"op_supervisory_session_seal_status": "invalid"}
    if seal_input.get("governed_fed_seal_status") != "sealed": return {"op_supervisory_session_seal_status": "invalid"}
    if seal_input.get("op_terminal_session_validation_status") != "valid": return {"op_supervisory_session_seal_status": "invalid"}
    return {"op_supervisory_session_seal_status": "sealed"}
