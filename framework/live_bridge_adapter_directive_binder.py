from typing import Any

def bind_directive(directive_dispatch: Any, adapter_catalog: Any, binder_config: Any) -> dict[str, Any]:
    if not isinstance(directive_dispatch, dict) or not isinstance(adapter_catalog, dict):
        return {"directive_binding_status": "invalid_input"}
    d_ok = directive_dispatch.get("directive_dispatch_status") == "dispatched"
    c_ok = adapter_catalog.get("adapter_catalog_status") == "cataloged"
    if not d_ok or not c_ok:
        return {"directive_binding_status": "invalid_input"}
    return {
        "directive_binding_status": "bound",
        "adapter_id": adapter_catalog.get("adapter_id"),
        "directive_id": directive_dispatch.get("directive_id"),
    }
