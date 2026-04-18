from typing import Any

def entry_post_seal_verifier(input_dict):
    if not isinstance(input_dict, dict):
        return {"runtime_entry_post_seal_verification_status": "invalid"}
    if input_dict.get("runtime_entry_seal_status") != "sealed":
        return {"runtime_entry_post_seal_verification_status": "invalid"}
    return {"runtime_entry_post_seal_verification_status": "verified"}
