from typing import Any

def authorize_directive(normalization: dict, matrix: dict, authorizer_config: dict) -> dict:
    if not isinstance(normalization, dict) or not isinstance(matrix, dict) or not isinstance(authorizer_config, dict):
        return {"directive_authorization_status": "invalid_input"}
    n_ok = normalization.get("directive_normalization_status") == "normalized"
    m_ok = matrix.get("authority_matrix_status") == "built"
    if not n_ok:
        return {"directive_authorization_status": "not_normalized"}
    if not m_ok:
        return {"directive_authorization_status": "no_matrix"}
    return {
        "directive_authorization_status": "authorized",
        "authorized_directive_id": normalization.get("normalized_directive_id"),
        "authorized_by_operator_id": matrix.get("matrix_entry_operator_id"),
        "authorization_tag": authorizer_config.get("tag", "auth-0001"),
    }
