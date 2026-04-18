from typing import Any

def workload_summary(input_dict):
    if not isinstance(input_dict, dict):
        return {"workload_summary_status": "invalid"}
    return {"workload_summary_status": "ok"}
