from typing import Any
def receive_heartbeat(hb_input):
    if not isinstance(hb_input, dict): return {"op_heartbeat_receive_status": "invalid"}
    if "heartbeat_id" not in hb_input: return {"op_heartbeat_receive_status": "invalid"}
    return {"op_heartbeat_receive_status": "received", "heartbeat_id": hb_input.get("heartbeat_id")}
