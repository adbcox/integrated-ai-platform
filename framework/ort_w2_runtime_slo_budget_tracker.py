from typing import Any

def runtime_slo_budget_tracker(input_dict):
    if not isinstance(input_dict, dict):
        return {"runtime_slo_budget_tracker_status": "invalid"}
    return {"runtime_slo_budget_tracker_status": "ok"}
