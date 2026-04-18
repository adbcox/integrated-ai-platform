from typing import Any

def b17_aggregate_proof_sealer(input_dict):
    if not isinstance(input_dict, dict):
        return {"pgs_int1_aggregate_proof_seal_status": "invalid_input"}
    if input_dict.get("tenant_release_pipeline_seal") != "sealed":
        return {"pgs_int1_aggregate_proof_seal_status": "upstream_not_sealed"}
    if input_dict.get("proof_aggregation_seal") != "sealed":
        return {"pgs_int1_aggregate_proof_seal_status": "upstream_not_sealed"}
    if input_dict.get("runtime_layer_seal") != "sealed":
        return {"pgs_int1_aggregate_proof_seal_status": "upstream_not_sealed"}
    if input_dict.get("deployment_activation_seal") != "sealed":
        return {"pgs_int1_aggregate_proof_seal_status": "upstream_not_sealed"}
    if input_dict.get("runtime_policy_seal") != "sealed":
        return {"pgs_int1_aggregate_proof_seal_status": "upstream_not_sealed"}
    if input_dict.get("runtime_integrity_seal") != "sealed":
        return {"pgs_int1_aggregate_proof_seal_status": "upstream_not_sealed"}
    if input_dict.get("ort_int2_aggregate_proof_seal") != "sealed":
        return {"pgs_int1_aggregate_proof_seal_status": "upstream_not_sealed"}
    if input_dict.get("operator_terminal_seal") != "sealed":
        return {"pgs_int1_aggregate_proof_seal_status": "upstream_not_sealed"}
    if input_dict.get("obs_layer_seal") != "sealed":
        return {"pgs_int1_aggregate_proof_seal_status": "upstream_not_sealed"}
    if input_dict.get("change_freeze_seal") != "sealed":
        return {"pgs_int1_aggregate_proof_seal_status": "upstream_not_sealed"}
    return {"pgs_int1_aggregate_proof_seal_status": "ok"}
