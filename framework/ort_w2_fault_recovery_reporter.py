from typing import Any

def fault_recovery_reporter(input_dict):
    if not isinstance(input_dict, dict):
        return {"fault_recovery_reporter_status": "invalid"}
    return {"fault_recovery_reporter_status": "ok"}
