from typing import Any

def b19_compliance_evidence_sealer(input_dict):
    # HARD GATE: type check
    if not isinstance(input_dict, dict):
        return {"compliance_evidence_seal_status": "invalid_input"}
    # HARD GATE: upstream seal
    if input_dict.get("pgs_int1_aggregate_proof_seal_status") != "sealed":
        return {"compliance_evidence_seal_status": "upstream_not_sealed"}
    # HARD GATE: upstream attestation seal
    if input_dict.get("release_attestation_seal_status") != "attested":
        return {"compliance_evidence_seal_status": "upstream_not_sealed"}
    # HARD GATE: upstream seal
    if input_dict.get("tenant_boundary_seal_status") != "sealed":
        return {"compliance_evidence_seal_status": "upstream_not_sealed"}
    return {"compliance_evidence_seal_status": "ok"}
