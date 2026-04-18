from typing import Any

def b15_proof_aggregation_sealer(input_dict):
    if not isinstance(input_dict, dict):
        return {"pgs_int1_proof_aggregation_seal_status": "invalid_input"}
    if input_dict.get("tenant_release_pipeline_seal") != "sealed":
        return {"pgs_int1_proof_aggregation_seal_status": "upstream_not_sealed"}
    if input_dict.get("release_layer_seal") != "sealed":
        return {"pgs_int1_proof_aggregation_seal_status": "upstream_not_sealed"}
    if input_dict.get("change_control_seal") != "sealed":
        return {"pgs_int1_proof_aggregation_seal_status": "upstream_not_sealed"}
    if input_dict.get("release_attestation_seal") != "sealed":
        return {"pgs_int1_proof_aggregation_seal_status": "upstream_not_sealed"}
    return {"pgs_int1_proof_aggregation_seal_status": "ok"}
