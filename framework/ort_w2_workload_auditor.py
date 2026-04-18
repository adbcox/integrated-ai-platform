from typing import Any

def workload_auditor(input_dict):
    if not isinstance(input_dict, dict):
        return {"workload_auditor_status": "invalid"}
    return {"workload_auditor_status": "ok"}
