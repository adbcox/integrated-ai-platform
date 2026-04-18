from typing import Any

def attachment_session_closer(input_dict):
    if not isinstance(input_dict, dict):
        return {"attachment_session_close_status": "invalid"}
    return {"attachment_session_close_status": "closed"}
