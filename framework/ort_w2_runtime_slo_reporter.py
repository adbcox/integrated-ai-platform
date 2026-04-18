from typing import Any

def runtime_slo_reporter(input_dict):
    if not isinstance(input_dict, dict):
        return {"runtime_slo_reporter_status": "invalid"}
    return {"runtime_slo_reporter_status": "ok"}
