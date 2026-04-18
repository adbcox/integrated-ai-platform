from typing import Any

def proof_aggregation_sealer(input_dict):
    if not isinstance(input_dict, dict):
        return {"ort_int2_proof_aggregation_seal_status": "invalid_input"}
    if "upstream_seal" in input_dict:
        if input_dict.get("upstream_seal") != "sealed":
            return {"ort_int2_proof_aggregation_seal_status": "upstream_not_sealed"}
    if "validation_context" in input_dict:
        if not input_dict.get("validation_context"):
            return {"ort_int2_proof_aggregation_seal_status": "validation_context_failed"}
    return {"ort_int2_proof_aggregation_seal_status": "ok"}
