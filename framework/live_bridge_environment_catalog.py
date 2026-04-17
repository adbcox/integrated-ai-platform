from typing import Any

def catalog_environment(validation: dict[str, Any], descriptor: dict[str, Any], catalog_config: dict[str, Any]) -> dict[str, Any]:
    if not isinstance(validation, dict) or not isinstance(descriptor, dict) or not isinstance(catalog_config, dict):
        return {"env_catalog_status": "invalid_input", "catalog_env_id": None, "catalog_entry": None}
    v_ok = validation.get("env_validation_status") == "valid"
    d_ok = descriptor.get("env_descriptor_status") == "described"
    if not v_ok:
        return {"env_catalog_status": "not_validated", "catalog_env_id": None, "catalog_entry": None}
    return {"env_catalog_status": "cataloged", "catalog_env_id": validation.get("validated_env_id"), "catalog_entry": catalog_config.get("entry_id", "cat-0001")} if v_ok and d_ok else {"env_catalog_status": "not_validated", "catalog_env_id": None, "catalog_entry": None}
