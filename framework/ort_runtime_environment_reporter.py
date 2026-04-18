from typing import Any

def environment_reporter(input_dict):
    if not isinstance(input_dict, dict):
        return {"environment_report_status": "invalid"}
    return {"environment_report_status": "reported"}
