from typing import Any

def runtime_slo_summary(input_dict):
    if not isinstance(input_dict, dict):
        return {"runtime_slo_summary_status": "invalid"}
    return {"runtime_slo_summary_status": "ok"}
