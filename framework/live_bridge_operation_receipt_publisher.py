from typing import Any

def publish_receipt(signature: dict[str, Any], egress: dict[str, Any], publisher_config: dict[str, Any]) -> dict[str, Any]:
    if not isinstance(signature, dict) or not isinstance(egress, dict) or not isinstance(publisher_config, dict):
        return {"receipt_publication_status": "invalid_input", "published_receipt_id": None, "published_receipt_channel": None}
    s_ok = signature.get("receipt_signature_status") == "signed"
    e_ok = egress.get("egress_channel_status") == "built"
    if not s_ok:
        return {"receipt_publication_status": "not_signed", "published_receipt_id": None, "published_receipt_channel": None}
    if s_ok and not e_ok:
        return {"receipt_publication_status": "no_egress", "published_receipt_id": None, "published_receipt_channel": None}
    return {"receipt_publication_status": "published", "published_receipt_id": signature.get("signed_receipt_id"), "published_receipt_channel": egress.get("egress_channel_id")} if s_ok and e_ok else {"receipt_publication_status": "invalid_input", "published_receipt_id": None, "published_receipt_channel": None}
