from typing import Any

def status_key_map_builder(input_dict):
    if not isinstance(input_dict, dict):
        return {"status_key_map_builder_status": "invalid_input"}
    return {"status_key_map_builder_status": "valid"}
