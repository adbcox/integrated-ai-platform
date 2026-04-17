from typing import Any
def bind_capability(catalog: dict[str, Any], seal: dict[str, Any], binder_config: dict[str, Any]) -> dict[str, Any]:
    if not isinstance(catalog, dict) or not isinstance(seal, dict) or not isinstance(binder_config, dict):
        return {"capability_binding_status": "invalid_input", "bound_env_id": None, "bound_seal_id": None, "binding_id": None}
    c_ok = catalog.get("env_catalog_status") == "cataloged"
    s_ok = seal.get("seal_status") == "sealed"
    if c_ok and s_ok:
        return {"capability_binding_status": "bound", "bound_env_id": catalog.get("catalog_env_id"), "bound_seal_id": seal.get("seal_id"), "binding_id": binder_config.get("binding_id", "bind-0001")}
    return {"capability_binding_status": "not_cataloged" if not c_ok else "not_sealed", "bound_env_id": None, "bound_seal_id": None, "binding_id": None}
