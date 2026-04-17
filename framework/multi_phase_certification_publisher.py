from typing import Any


def publish_certification(
    composition: dict[str, Any],
    ledger_audit: dict[str, Any],
    publisher_config: dict[str, Any],
) -> dict[str, Any]:
    if (
        not isinstance(composition, dict)
        or not isinstance(ledger_audit, dict)
        or not isinstance(publisher_config, dict)
    ):
        return {
            "publication_status": "invalid_input",
            "publication_phase": None,
            "publication_count": 0,
        }

    comp_ok = composition.get("composition_status") == "composed"
    audit_ok = ledger_audit.get("ledger_audit_status") == "passed"

    if comp_ok and audit_ok:
        return {
            "publication_status": "published",
            "publication_phase": composition.get("composition_phase"),
            "publication_count": composition.get("composition_count", 0),
        }

    return {
        "publication_status": "failed",
        "publication_phase": None,
        "publication_count": 0,
    }
