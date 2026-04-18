from typing import Any

def reconciliation_planner(input_dict):
    if not isinstance(input_dict, dict):
        return {"reconciliation_planner_status": "invalid_input"}
    return {"reconciliation_planner_status": "valid"}
