from typing import Any
def gate_exit_channel_attachment(gate_input):
    if not isinstance(gate_input, dict): return {"exit_channel_attachment_gate_status": "closed"}
    if "attachment_id" not in gate_input: return {"exit_channel_attachment_gate_status": "closed"}
    if gate_input.get("exit_channel_governance_bind_status") != "bound": return {"exit_channel_attachment_gate_status": "closed"}
    return {"exit_channel_attachment_gate_status": "open", "attachment_id": gate_input.get("attachment_id")}
