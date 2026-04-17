from typing import Any

def assign_role(catalog: dict, authority: dict, role_config: dict) -> dict:
    if not isinstance(catalog, dict) or not isinstance(authority, dict) or not isinstance(role_config, dict):
        return {"role_assignment_status": "invalid_input"}
    c_ok = catalog.get("operator_catalog_status") == "cataloged"
    a_ok = authority.get("authority_resolution_status") == "resolved"
    supervisory = authority.get("authority_level") in ("supervisor", "root")
    if not c_ok:
        return {"role_assignment_status": "not_cataloged"}
    if not a_ok or not supervisory:
        return {"role_assignment_status": "insufficient_authority"}
    return {
        "role_assignment_status": "assigned",
        "role_operator_id": catalog.get("catalog_operator_id"),
        "role_level": authority.get("authority_level"),
        "role_id": role_config.get("role_id", "role-0001"),
    }
