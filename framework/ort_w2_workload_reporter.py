from typing import Any

def workload_reporter(input_dict):
    if not isinstance(input_dict, dict):
        return {"workload_reporter_status": "invalid"}
    return {"workload_reporter_status": "ok"}
