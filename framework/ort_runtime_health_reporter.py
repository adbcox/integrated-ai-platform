from typing import Any

def health_reporter(input_dict):
    if not isinstance(input_dict, dict):
        return {"health_report_status": "invalid"}
    return {"health_report_status": "reported"}
