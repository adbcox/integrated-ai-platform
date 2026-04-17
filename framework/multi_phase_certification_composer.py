from typing import Any


def compose_certification(
    ledger: dict[str, Any],
    verification: dict[str, Any],
    composer_config: dict[str, Any],
) -> dict[str, Any]:
    if (
        not isinstance(ledger, dict)
        or not isinstance(verification, dict)
        or not isinstance(composer_config, dict)
    ):
        return {
            "composition_status": "invalid_input",
            "composition_phase": None,
            "composition_count": 0,
        }

    ledger_ok = ledger.get("ledger_write_status") == "written"
    ver_ok = verification.get("verification_status") == "verified"

    if ledger_ok and ver_ok:
        return {
            "composition_status": "composed",
            "composition_phase": ledger.get("ledger_phase"),
            "composition_count": ledger.get("ledger_entries", 0),
        }

    return {
        "composition_status": "failed",
        "composition_phase": None,
        "composition_count": 0,
    }
