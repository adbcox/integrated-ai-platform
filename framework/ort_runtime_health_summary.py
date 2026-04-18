from typing import Any

def health_summary(input_dict):
    if not isinstance(input_dict, dict):
        return {"health_summary_status": "invalid"}
    return {"health_summary_status": "summarized"}
