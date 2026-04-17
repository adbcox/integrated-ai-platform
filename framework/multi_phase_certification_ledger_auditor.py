from typing import Any


def audit_certification_ledger(
    ledger: dict[str, Any],
    certification_composer: dict[str, Any],
    auditor_config: dict[str, Any],
) -> dict[str, Any]:
    if (
        not isinstance(ledger, dict)
        or not isinstance(certification_composer, dict)
        or not isinstance(auditor_config, dict)
    ):
        return {
            "ledger_audit_status": "invalid_input",
            "audit_phase": None,
            "audit_result": None,
        }

    ledger_ok = ledger.get("ledger_write_status") == "written"
    comp_ok = certification_composer.get("composition_status") == "composed"

    if ledger_ok and comp_ok:
        return {
            "ledger_audit_status": "passed",
            "audit_phase": ledger.get("ledger_phase"),
            "audit_result": "ledger_valid",
        }

    return {
        "ledger_audit_status": "failed",
        "audit_phase": None,
        "audit_result": None,
    }
