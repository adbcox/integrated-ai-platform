from typing import Any
def validate_credentials(acceptance, credential_policy):
    if not isinstance(acceptance, dict) or not isinstance(credential_policy, dict):
        return {"op_credential_validation_status": "invalid"}
    if acceptance.get("op_credential_accept_status") != "accepted":
        return {"op_credential_validation_status": "invalid"}
    if credential_policy.get("policy_active") != True:
        return {"op_credential_validation_status": "invalid"}
    return {"op_credential_validation_status": "valid", "credential_token": acceptance.get("credential_token")}
