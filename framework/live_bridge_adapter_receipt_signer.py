from typing import Any

def sign_adapter_receipt(receipt: Any, signer_config: Any, signature_config: Any) -> dict[str, Any]:
    if not isinstance(receipt, dict):
        return {"adapter_receipt_signature_status": "not_signed"}
    r_ok = receipt.get("adapter_receipt_status") == "built"
    if not r_ok:
        return {"adapter_receipt_signature_status": "not_signed"}
    return {
        "adapter_receipt_signature_status": "signed",
        "adapter_id": receipt.get("adapter_id"),
        "signature_format": "sig_timestamp_hash",
    }
