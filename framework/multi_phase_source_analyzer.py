from typing import Any


def analyze_source(
    transfer_mapping: dict[str, Any],
    pattern_catalog: dict[str, Any],
    analyze_config: dict[str, Any],
) -> dict[str, Any]:
    if (
        not isinstance(transfer_mapping, dict)
        or not isinstance(pattern_catalog, dict)
        or not isinstance(analyze_config, dict)
    ):
        return {
            "analysis_status": "invalid_input",
            "analysis_phase": None,
            "analyzed_entries": 0,
        }

    transfer_ok = transfer_mapping.get("transfer_mapping_status") == "mapped"
    catalog_ok = pattern_catalog.get("catalog_status") == "cataloged"

    if transfer_ok and catalog_ok:
        return {
            "analysis_status": "analyzed",
            "analysis_phase": transfer_mapping.get("mapped_phase"),
            "analyzed_entries": pattern_catalog.get("entry_count", 0),
        }

    if not transfer_ok:
        return {
            "analysis_status": "no_mapping",
            "analysis_phase": None,
            "analyzed_entries": 0,
        }

    return {
        "analysis_status": "invalid_input",
        "analysis_phase": None,
        "analyzed_entries": 0,
    }
