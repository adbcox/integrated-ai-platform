from typing import Any


def build_abstraction(
    pattern: dict[str, Any],
    synthesis: dict[str, Any],
    abstraction_config: dict[str, Any],
) -> dict[str, Any]:
    if (
        not isinstance(pattern, dict)
        or not isinstance(synthesis, dict)
        or not isinstance(abstraction_config, dict)
    ):
        return {
            "abstraction_status": "invalid_input",
            "abstraction_phase": None,
            "abstraction_level": None,
        }

    pattern_ok = pattern.get("pattern_status") == "extracted"
    synthesis_ok = synthesis.get("synthesis_status") == "synthesized"

    if pattern_ok and synthesis_ok:
        return {
            "abstraction_status": "built",
            "abstraction_phase": pattern.get("pattern_phase"),
            "abstraction_level": abstraction_config.get("level", "high"),
        }

    if not pattern_ok:
        return {
            "abstraction_status": "no_pattern",
            "abstraction_phase": None,
            "abstraction_level": None,
        }

    return {
        "abstraction_status": "invalid_input",
        "abstraction_phase": None,
        "abstraction_level": None,
    }
