from typing import Any

def build_receipt(acknowledgement: dict[str, Any], response_publication: dict[str, Any], builder_config: dict[str, Any]) -> dict[str, Any]:
    if not isinstance(acknowledgement, dict) or not isinstance(response_publication, dict) or not isinstance(builder_config, dict):
        return {"receipt_build_status": "invalid_input", "receipt_operation_id": None, "receipt_id": None, "receipt_response_id": None}
    a_ok = acknowledgement.get("acknowledgement_status") == "acknowledged"
    rp_ok = response_publication.get("response_publication_status") == "published"
    if not a_ok:
        return {"receipt_build_status": "not_acknowledged", "receipt_operation_id": None, "receipt_id": None, "receipt_response_id": None}
    if a_ok and not rp_ok:
        return {"receipt_build_status": "not_published", "receipt_operation_id": None, "receipt_id": None, "receipt_response_id": None}
    return {"receipt_build_status": "built", "receipt_operation_id": acknowledgement.get("acked_operation_id"), "receipt_id": builder_config.get("receipt_id", "rcp-0001"), "receipt_response_id": response_publication.get("published_response_id")} if a_ok and rp_ok else {"receipt_build_status": "invalid_input", "receipt_operation_id": None, "receipt_id": None, "receipt_response_id": None}
