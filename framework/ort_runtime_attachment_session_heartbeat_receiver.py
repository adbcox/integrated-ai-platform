from typing import Any

def attachment_session_heartbeat_receiver(input_dict):
    if not isinstance(input_dict, dict):
        return {"attachment_session_heartbeat_status": "invalid"}
    return {"attachment_session_heartbeat_status": "received"}
