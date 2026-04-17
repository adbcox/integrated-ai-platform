from typing import Any
def validate_envelope(normalization: dict[str, Any], boundary_policy: dict[str, Any], validator_config: dict[str, Any]) -> dict[str, Any]:
    if not isinstance(normalization, dict) or not isinstance(boundary_policy, dict) or not isinstance(validator_config, dict):
        return {"envelope_validation_status": "invalid_input", "validated_envelope_id": None, "validated_operation_id": None}
    n_ok = normalization.get("envelope_normalization_status") == "normalized"
    p_ok = boundary_policy.get("boundary_policy_status") == "resolved"
    if n_ok and p_ok:
        return {"envelope_validation_status": "valid", "validated_envelope_id": normalization.get("envelope_schema_id"), "validated_operation_id": normalization.get("envelope_operation_id")}
    return {"envelope_validation_status": "not_normalized" if not n_ok else "no_policy", "validated_envelope_id": None, "validated_operation_id": None}
