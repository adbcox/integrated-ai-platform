from typing import Any
def authorize_operation(envelope_validation: dict[str, Any], scope_negotiation: dict[str, Any], authorizer_config: dict[str, Any]) -> dict[str, Any]:
    if not isinstance(envelope_validation, dict) or not isinstance(scope_negotiation, dict) or not isinstance(authorizer_config, dict):
        return {"operation_authorization_status": "invalid_input", "authorized_operation_id": None, "authorized_identity_id": None}
    ev_ok = envelope_validation.get("envelope_validation_status") == "valid"
    sn_ok = scope_negotiation.get("scope_negotiation_status") == "negotiated"
    if ev_ok and sn_ok:
        return {"operation_authorization_status": "authorized", "authorized_operation_id": envelope_validation.get("validated_operation_id"), "authorized_identity_id": scope_negotiation.get("negotiated_identity_id")}
    return {"operation_authorization_status": "not_validated" if not ev_ok else "not_negotiated", "authorized_operation_id": None, "authorized_identity_id": None}
