from typing import Any

def runtime_dispatch_aggregate_summary(input_dict):
    if not isinstance(input_dict, dict):
        return {"runtime_dispatch_aggregate_summary_status": "invalid"}
    return {"runtime_dispatch_aggregate_summary_status": "ok"}
