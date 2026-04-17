from typing import Any


def rollup_certification(
    composition: dict[str, Any],
    publication: dict[str, Any],
    ledger_audit: dict[str, Any],
) -> dict[str, Any]:
    if (
        not isinstance(composition, dict)
        or not isinstance(publication, dict)
        or not isinstance(ledger_audit, dict)
    ):
        return {
            "certification_rollup_status": "invalid_input",
            "rollup_phase": None,
            "rollup_count": 0,
        }

    comp_ok = composition.get("composition_status") == "composed"
    pub_ok = publication.get("publication_status") == "published"
    audit_ok = ledger_audit.get("ledger_audit_status") == "passed"
    all_ok = comp_ok and pub_ok and audit_ok

    if all_ok:
        return {
            "certification_rollup_status": "rolled_up",
            "rollup_phase": composition.get("composition_phase"),
            "rollup_count": 1,
        }

    if (comp_ok and pub_ok) or (comp_ok and audit_ok) or (pub_ok and audit_ok):
        return {
            "certification_rollup_status": "degraded",
            "rollup_phase": None,
            "rollup_count": 0,
        }

    return {
        "certification_rollup_status": "offline",
        "rollup_phase": None,
        "rollup_count": 0,
    }
