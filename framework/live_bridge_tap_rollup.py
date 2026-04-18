from typing import Any

def rollup_tap(tap_catalog: Any) -> dict[str, Any]:
    if not isinstance(tap_catalog, dict):
        return {"tap_rollup_status": "not_rolled_up"}
    catalog_ok = tap_catalog.get("tap_catalog_status") == "cataloged"
    if not catalog_ok:
        return {"tap_rollup_status": "not_rolled_up"}
    return {
        "tap_rollup_status": "rolled_up",
    }
