from typing import Any
def gate_terminal_stability(gate_input):
    if not isinstance(gate_input, dict): return {"op_terminal_stability_gate_status": "failed"}
    if "stability_threshold" not in gate_input: return {"op_terminal_stability_gate_status": "failed"}
    return {"op_terminal_stability_gate_status": "passed", "stability_threshold": gate_input.get("stability_threshold")}
