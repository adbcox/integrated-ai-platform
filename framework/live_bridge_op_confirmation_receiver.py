from typing import Any
def receive_confirmation(confirmation_input):
    if not isinstance(confirmation_input, dict): return {"op_confirmation_receive_status": "invalid"}
    if "confirmation_response" not in confirmation_input: return {"op_confirmation_receive_status": "invalid"}
    return {"op_confirmation_receive_status": "received", "confirmation_response": confirmation_input.get("confirmation_response")}
