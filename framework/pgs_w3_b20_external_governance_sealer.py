from typing import Any

def b20_external_governance_sealer(input_dict):
    # HARD GATE: type check
    if not isinstance(input_dict, dict):
        return {"external_governance_seal_status": "invalid_input"}
    # HARD GATE: upstream seal
    if input_dict.get("disclosure_bundle_seal_status") != "sealed":
        return {"external_governance_seal_status": "upstream_not_sealed"}
    # HARD GATE: upstream seal
    if input_dict.get("regulator_handshake_seal_status") != "sealed":
        return {"external_governance_seal_status": "upstream_not_sealed"}
    # HARD GATE: upstream seal
    if input_dict.get("compliance_evidence_seal_status") != "sealed":
        return {"external_governance_seal_status": "upstream_not_sealed"}
    # HARD GATE: upstream seal
    if input_dict.get("pgs_int1_aggregate_proof_seal_status") != "sealed":
        return {"external_governance_seal_status": "upstream_not_sealed"}
    # HARD GATE: upstream attestation seal
    if input_dict.get("pgs_int1_cross_tenant_divergence_attestation_status") != "attested":
        return {"external_governance_seal_status": "upstream_not_sealed"}
    return {"external_governance_seal_status": "ok"}
