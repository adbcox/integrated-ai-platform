from typing import Any


def normalize_evidence(
    evidence: dict[str, Any],
    schema_config: dict[str, Any],
    normalize_config: dict[str, Any],
) -> dict[str, Any]:
    if (
        not isinstance(evidence, dict)
        or not isinstance(schema_config, dict)
        or not isinstance(normalize_config, dict)
    ):
        return {
            "normalization_status": "invalid_input",
            "normalization_phase": None,
            "normalized_count": 0,
        }

    ev_ok = evidence.get("evidence_status") == "collected"

    if ev_ok:
        return {
            "normalization_status": "normalized",
            "normalization_phase": evidence.get("evidence_phase"),
            "normalized_count": evidence.get("evidence_count", 0),
        }

    return {
        "normalization_status": "failed",
        "normalization_phase": None,
        "normalized_count": 0,
    }
