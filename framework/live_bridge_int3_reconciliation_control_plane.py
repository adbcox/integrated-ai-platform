from typing import Any

def reconciliation_control_plane(input_dict):
    if not isinstance(input_dict, dict):
        # HARD GATE: Invalid input type
        return {"reconciliation_control_plane_status": "invalid_input"}
    if "upstream_seal" in input_dict:
        if input_dict.get("upstream_seal") != "sealed":
            # HARD GATE: Upstream seal not in sealed state
            return {"reconciliation_control_plane_status": "upstream_not_sealed"}
    if "validation_data" in input_dict:
        if not input_dict.get("validation_data"):
            # HARD GATE: Validation data missing or empty
            return {"reconciliation_control_plane_status": "validation_failed"}
    return {"reconciliation_control_plane_status": "ok"}
