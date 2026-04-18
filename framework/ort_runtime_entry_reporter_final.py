from typing import Any

def entry_reporter_final(input_dict):
    if not isinstance(input_dict, dict):
        return {"entry_reporter_final_status": "invalid"}
    return {"entry_reporter_final_status": "reported"}
