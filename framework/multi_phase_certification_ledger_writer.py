from typing import Any


def write_certification_ledger(
    verification: dict[str, Any],
    ledger_config: dict[str, Any],
    writer_config: dict[str, Any],
) -> dict[str, Any]:
    if (
        not isinstance(verification, dict)
        or not isinstance(ledger_config, dict)
        or not isinstance(writer_config, dict)
    ):
        return {
            "ledger_write_status": "invalid_input",
            "ledger_phase": None,
            "ledger_entries": 0,
        }

    ver_ok = verification.get("verification_status") == "verified"

    if ver_ok:
        return {
            "ledger_write_status": "written",
            "ledger_phase": verification.get("verification_phase"),
            "ledger_entries": 1,
        }

    return {
        "ledger_write_status": "failed",
        "ledger_phase": None,
        "ledger_entries": 0,
    }
