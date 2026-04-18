from typing import Any

def attachment_session_validator(input_dict):
    if not isinstance(input_dict, dict):
        return {"attachment_session_validator_status": "invalid"}
    return {"attachment_session_validator_status": "validated"}
