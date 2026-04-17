from typing import Any

def build_authority_matrix(role: dict, catalog: dict, matrix_config: dict) -> dict:
    if not isinstance(role, dict) or not isinstance(catalog, dict) or not isinstance(matrix_config, dict):
        return {"authority_matrix_status": "invalid_input"}
    ra_ok = role.get("role_assignment_status") == "assigned"
    c_ok = catalog.get("operator_catalog_status") == "cataloged"
    if not ra_ok:
        return {"authority_matrix_status": "no_role"}
    if not c_ok:
        return {"authority_matrix_status": "not_cataloged"}
    return {
        "authority_matrix_status": "built",
        "matrix_entry_operator_id": role.get("role_operator_id"),
        "matrix_level": role.get("role_level"),
        "matrix_id": matrix_config.get("matrix_id", "mat-0001"),
    }
