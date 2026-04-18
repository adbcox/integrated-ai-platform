from typing import Any

def attachment_session_registrar(input_dict):
    if not isinstance(input_dict, dict):
        return {"attachment_session_registrar_status": "invalid"}
    return {"attachment_session_registrar_status": "registered"}
