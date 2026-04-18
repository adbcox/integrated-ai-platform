from typing import Any
def build_terminal_control_plane(cp_input):
    if not isinstance(cp_input, dict): return {"op_terminal_cp_status": "invalid"}
    if "cp_id" not in cp_input: return {"op_terminal_cp_status": "invalid"}
    return {"op_terminal_cp_status": "operational", "cp_id": cp_input.get("cp_id")}
