from typing import Any


def detect_invariants(
    pattern: dict[str, Any],
    trend: dict[str, Any],
    invariant_config: dict[str, Any],
) -> dict[str, Any]:
    if (
        not isinstance(pattern, dict)
        or not isinstance(trend, dict)
        or not isinstance(invariant_config, dict)
    ):
        return {
            "invariant_status": "invalid_input",
            "invariant_phase": None,
            "invariant_count": 0,
        }

    pattern_ok = pattern.get("pattern_status") == "extracted"
    trend_ok = trend.get("trend_status") == "analyzed"

    if pattern_ok and trend_ok:
        return {
            "invariant_status": "detected",
            "invariant_phase": pattern.get("pattern_phase"),
            "invariant_count": 1,
        }

    if not pattern_ok:
        return {
            "invariant_status": "no_pattern",
            "invariant_phase": None,
            "invariant_count": 0,
        }

    return {
        "invariant_status": "invalid_input",
        "invariant_phase": None,
        "invariant_count": 0,
    }
