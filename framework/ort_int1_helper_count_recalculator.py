from typing import Any

def helper_count_recalculator(input_dict):
    if not isinstance(input_dict, dict):
        return {"helper_count_recalculator_status": "invalid_input"}
    return {"helper_count_recalculator_status": "valid"}
