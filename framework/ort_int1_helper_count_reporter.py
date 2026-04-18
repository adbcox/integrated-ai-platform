from typing import Any

def helper_count_reporter(input_dict):
    if not isinstance(input_dict, dict):
        return {"helper_count_reporter_status": "invalid_input"}
    return {"helper_count_reporter_status": "valid"}
