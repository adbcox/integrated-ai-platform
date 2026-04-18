from typing import Any

def reconciliation_entry_gate_validator(input_dict):
    if not isinstance(input_dict, dict):
        # HARD GATE: Invalid input type
        return {"reconciliation_gate_status": "invalid_input"}
    if "upstream_seal" in input_dict:
        if input_dict.get("upstream_seal") != "sealed":
            # HARD GATE: Upstream seal not in sealed state
            return {"reconciliation_gate_status": "upstream_not_sealed"}
    if "validation_data" in input_dict:
        if not input_dict.get("validation_data"):
            # HARD GATE: Validation data missing or empty
            return {"reconciliation_gate_status": "validation_failed"}
    return {"reconciliation_gate_status": "ok"}
