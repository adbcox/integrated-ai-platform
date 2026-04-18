from typing import Any

def workload_intake(input_dict):
    if not isinstance(input_dict, dict):
        return {"workload_intake_status": "invalid"}
    return {"workload_intake_status": "ok"}
