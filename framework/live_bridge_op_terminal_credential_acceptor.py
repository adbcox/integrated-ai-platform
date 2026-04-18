from typing import Any
def accept_credentials(credential_input, identity_validation):
    if not isinstance(credential_input, dict) or not isinstance(identity_validation, dict):
        return {"op_credential_accept_status": "invalid"}
    if "credential_token" not in credential_input:
        return {"op_credential_accept_status": "invalid"}
    if identity_validation.get("op_identity_validation_status") != "valid":
        return {"op_credential_accept_status": "invalid"}
    return {"op_credential_accept_status": "accepted", "credential_token": credential_input.get("credential_token")}
