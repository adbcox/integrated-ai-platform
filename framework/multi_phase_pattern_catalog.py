from typing import Any


def catalog_pattern(
    generalization: dict[str, Any],
    pattern: dict[str, Any],
    catalog_config: dict[str, Any],
) -> dict[str, Any]:
    if (
        not isinstance(generalization, dict)
        or not isinstance(pattern, dict)
        or not isinstance(catalog_config, dict)
    ):
        return {
            "catalog_status": "invalid_input",
            "catalog_phase": None,
            "entry_count": 0,
        }

    generalization_ok = generalization.get("generalization_status") == "generalized"
    pattern_ok = pattern.get("pattern_status") == "extracted"

    if generalization_ok and pattern_ok:
        return {
            "catalog_status": "cataloged",
            "catalog_phase": generalization.get("generalization_phase"),
            "entry_count": pattern.get("pattern_count", 0),
        }

    if not generalization_ok:
        return {
            "catalog_status": "no_generalization",
            "catalog_phase": None,
            "entry_count": 0,
        }

    return {
        "catalog_status": "invalid_input",
        "catalog_phase": None,
        "entry_count": 0,
    }
