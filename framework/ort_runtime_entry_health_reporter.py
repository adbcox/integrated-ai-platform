from typing import Any

def entry_health_reporter(input_dict):
    if not isinstance(input_dict, dict):
        return {"entry_health_report_status": "invalid"}
    return {"entry_health_report_status": "reported"}
