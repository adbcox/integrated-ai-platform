from typing import Any
def resolve_identity(claim, catalog):
    if not isinstance(claim, dict) or not isinstance(catalog, dict):
        return {"op_identity_resolution_status": "invalid"}
    if "operator_id" not in claim:
        return {"op_identity_resolution_status": "invalid"}
    if catalog.get("op_console_catalog_status") != "cataloged":
        return {"op_identity_resolution_status": "invalid"}
    return {"op_identity_resolution_status": "resolved", "operator_id": claim.get("operator_id")}
