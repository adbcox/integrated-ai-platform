from typing import Any


def rollup_patterns(
    pattern_extraction: dict[str, Any],
    pattern_catalog: dict[str, Any],
    abstraction_builder: dict[str, Any],
    rollup_config: dict[str, Any],
) -> dict[str, Any]:
    if (
        not isinstance(pattern_extraction, dict)
        or not isinstance(pattern_catalog, dict)
        or not isinstance(abstraction_builder, dict)
        or not isinstance(rollup_config, dict)
    ):
        return {
            "pattern_rollup_status": "invalid_input",
            "rollup_phase": None,
            "pattern_count": 0,
        }

    pe_ok = pattern_extraction.get("pattern_status") == "extracted"
    pc_ok = pattern_catalog.get("catalog_status") == "cataloged"
    ab_ok = abstraction_builder.get("abstraction_status") == "built"
    all_ok = pe_ok and pc_ok and ab_ok

    if all_ok:
        return {
            "pattern_rollup_status": "rolled_up",
            "rollup_phase": pattern_extraction.get("pattern_phase"),
            "pattern_count": pattern_extraction.get("pattern_count", 0),
        }

    if (pe_ok and pc_ok) or (pe_ok and ab_ok) or (pc_ok and ab_ok):
        return {
            "pattern_rollup_status": "degraded",
            "rollup_phase": None,
            "pattern_count": 0,
        }

    return {
        "pattern_rollup_status": "offline",
        "rollup_phase": None,
        "pattern_count": 0,
    }
