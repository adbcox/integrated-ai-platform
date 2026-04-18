from typing import Any

def register_adapter(descriptor: Any, kind_registry: Any, governed_fed_seal: Any, registrar_config: Any) -> dict[str, Any]:
    if not isinstance(descriptor, dict) or not isinstance(kind_registry, dict) or not isinstance(governed_fed_seal, dict):
        return {"adapter_registration_status": "invalid_input"}
    d_ok = descriptor.get("adapter_description_status") == "described"
    k_ok = kind_registry.get("registry_status") == "built"
    seal_ok = governed_fed_seal.get("governed_fed_seal_status") == "sealed"
    if not d_ok or not k_ok or not seal_ok:
        return {"adapter_registration_status": "invalid_input"}
    adapter_id = descriptor.get("adapter_id")
    if not adapter_id:
        return {"adapter_registration_status": "invalid_input"}
    return {
        "adapter_registration_status": "registered",
        "adapter_id": adapter_id,
        "kind_registry_count": kind_registry.get("kind_count", 0),
        "seal_verified": True,
    }
