from typing import Any

def rollup_operators(registration: dict, identity: dict, catalog: dict) -> dict:
    if not isinstance(registration, dict) or not isinstance(identity, dict) or not isinstance(catalog, dict):
        return {"operator_rollup_status": "invalid_input"}
    all_complete = (
        registration.get("operator_registration_status") == "registered" and
        identity.get("operator_identity_status") == "valid" and
        catalog.get("operator_catalog_status") == "cataloged"
    )
    if all_complete:
        return {
            "operator_rollup_status": "rolled_up",
            "rollup_operator_id": catalog.get("catalog_operator_id"),
            "operations_complete": 3,
        }
    return {"operator_rollup_status": "incomplete_source", "operations_complete": 0}
