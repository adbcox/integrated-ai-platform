from typing import Any

def full_pipeline_post_seal_verifier(input_dict):
    if not isinstance(input_dict, dict):
        return {"ort_int2_full_pipeline_post_seal_verification_status": "invalid_input"}
    if "upstream_seal" in input_dict:
        if input_dict.get("upstream_seal") != "sealed":
            return {"ort_int2_full_pipeline_post_seal_verification_status": "upstream_not_sealed"}
    if "validation_context" in input_dict:
        if not input_dict.get("validation_context"):
            return {"ort_int2_full_pipeline_post_seal_verification_status": "validation_context_failed"}
    return {"ort_int2_full_pipeline_post_seal_verification_status": "ok"}
