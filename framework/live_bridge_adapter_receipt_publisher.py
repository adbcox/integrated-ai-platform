from typing import Any

def publish_adapter_receipt(signature: Any, egress_channel: Any, publisher_config: Any) -> dict[str, Any]:
    if not isinstance(signature, dict) or not isinstance(egress_channel, dict):
        return {"adapter_receipt_publication_status": "failed"}
    s_ok = signature.get("adapter_receipt_signature_status") == "signed"
    e_ok = egress_channel.get("egress_channel_status") == "built"
    if not s_ok or not e_ok:
        return {"adapter_receipt_publication_status": "failed"}
    return {
        "adapter_receipt_publication_status": "published",
        "adapter_id": signature.get("adapter_id"),
    }
