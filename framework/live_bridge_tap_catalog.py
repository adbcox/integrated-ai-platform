from typing import Any

def catalog_tap(tap_validation: Any, catalog_config: Any) -> dict[str, Any]:
    if not isinstance(tap_validation, dict):
        return {"tap_catalog_status": "not_cataloged"}
    val_ok = tap_validation.get("tap_validation_status") == "valid"
    if not val_ok:
        return {"tap_catalog_status": "not_cataloged"}
    return {
        "tap_catalog_status": "cataloged",
        "tap_entry_count": 1,
    }
