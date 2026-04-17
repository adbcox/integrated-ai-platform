from typing import Any

def sign_receipt(receipt: dict[str, Any], signer_config: dict[str, Any], signature_config: dict[str, Any]) -> dict[str, Any]:
    if not isinstance(receipt, dict) or not isinstance(signer_config, dict) or not isinstance(signature_config, dict):
        return {"receipt_signature_status": "invalid_input", "signed_receipt_id": None, "signer_id": None, "receipt_signature": None}
    r_ok = receipt.get("receipt_build_status") == "built"
    if not r_ok:
        return {"receipt_signature_status": "no_receipt", "signed_receipt_id": None, "signer_id": None, "receipt_signature": None}
    return {"receipt_signature_status": "signed", "signed_receipt_id": receipt.get("receipt_id"), "signer_id": signer_config.get("signer_id", "rs-0001"), "receipt_signature": signature_config.get("signature", "rsig-0001")} if r_ok else {"receipt_signature_status": "invalid_input", "signed_receipt_id": None, "signer_id": None, "receipt_signature": None}
