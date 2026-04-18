from typing import Any

def fault_summary(input_dict):
    if not isinstance(input_dict, dict):
        return {"fault_summary_status": "invalid"}
    return {"fault_summary_status": "ok"}
