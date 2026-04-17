from typing import Any
def audit_bridge(session_validation: dict[str, Any], operation_authorization: dict[str, Any], response_publication: dict[str, Any]) -> dict[str, Any]:
    if not isinstance(session_validation, dict) or not isinstance(operation_authorization, dict) or not isinstance(response_publication, dict):
        return {"bridge_audit_status": "invalid_input", "audit_session_id": None, "ok_count": 0}
    sv_ok = session_validation.get("session_validation_status") == "valid"
    oa_ok = operation_authorization.get("operation_authorization_status") == "authorized"
    rp_ok = response_publication.get("response_publication_status") == "published"
    all_ok = sv_ok and oa_ok and rp_ok
    any_ok = sv_ok or oa_ok or rp_ok
    if all_ok:
        return {"bridge_audit_status": "passed", "audit_session_id": session_validation.get("validated_session_id"), "ok_count": 3}
    if any_ok:
        return {"bridge_audit_status": "degraded", "audit_session_id": None, "ok_count": sum([sv_ok, oa_ok, rp_ok])}
    return {"bridge_audit_status": "failed", "audit_session_id": None, "ok_count": 0}
