from typing import Any

def metrics_summary(input_dict):
    if not isinstance(input_dict, dict):
        return {"metrics_summary_status": "invalid_input"}
    return {"metrics_summary_status": "valid"}
