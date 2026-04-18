from typing import Any

def workload_classifier(input_dict):
    if not isinstance(input_dict, dict):
        return {"workload_classifier_status": "invalid"}
    return {"workload_classifier_status": "ok"}
