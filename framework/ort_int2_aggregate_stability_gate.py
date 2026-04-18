from typing import Any

def aggregate_stability_gate(input_dict):
    if not isinstance(input_dict, dict):
        return {"aggregate_stability_gate_status": "invalid_input"}
    if "upstream_seal" in input_dict:
        if input_dict.get("upstream_seal") != "sealed":
            return {"aggregate_stability_gate_status": "upstream_not_sealed"}
    if "validation_context" in input_dict:
        if not input_dict.get("validation_context"):
            return {"aggregate_stability_gate_status": "validation_context_failed"}
    return {"aggregate_stability_gate_status": "ok"}
