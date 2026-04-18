from typing import Any
def quorum_gate(quorum_input):
    if not isinstance(quorum_input, dict): return {"op_quorum_gate_status": "failed"}
    available = quorum_input.get("available_members", 0)
    min_required = quorum_input.get("min_members", 1)
    if available < min_required: return {"op_quorum_gate_status": "failed"}
    return {"op_quorum_gate_status": "passed", "available_members": available}
