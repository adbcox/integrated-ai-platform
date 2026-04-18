from typing import Any

def rollup_adapters(registration: Any, identity: Any, catalog: Any) -> dict[str, Any]:
    if not isinstance(registration, dict) or not isinstance(identity, dict) or not isinstance(catalog, dict):
        return {"adapter_rollup_status": "failed"}
    r_ok = registration.get("adapter_registration_status") == "registered"
    i_ok = identity.get("adapter_identity_validation_status") == "valid"
    c_ok = catalog.get("adapter_catalog_status") == "cataloged"
    if not r_ok or not i_ok or not c_ok:
        return {"adapter_rollup_status": "failed"}
    return {
        "adapter_rollup_status": "rolled_up",
        "adapter_count": catalog.get("adapter_count", 1),
    }
