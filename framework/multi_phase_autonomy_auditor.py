from typing import Any


def audit_autonomy(
    selection: dict[str, Any],
    arbitration: dict[str, Any],
    decision_validation: dict[str, Any],
) -> dict[str, Any]:
    if (
        not isinstance(selection, dict)
        or not isinstance(arbitration, dict)
        or not isinstance(decision_validation, dict)
    ):
        return {
            "autonomy_audit_status": "invalid_input",
            "ok_count": 0,
            "audit_phase": None,
        }

    sel_ok = selection.get("selection_status") == "selected"
    arb_ok = arbitration.get("arbitration_status") == "arbitrated"
    dec_ok = decision_validation.get("decision_validation_status") in ("valid", "partial")

    all_ok = sel_ok and arb_ok and dec_ok
    any_ok = sel_ok or arb_ok or dec_ok
    ok_count = sum([sel_ok, arb_ok, dec_ok])

    if all_ok:
        return {
            "autonomy_audit_status": "passed",
            "ok_count": ok_count,
            "audit_phase": arbitration.get("arbitrated_phase"),
        }

    if any_ok:
        return {
            "autonomy_audit_status": "degraded",
            "ok_count": ok_count,
            "audit_phase": None,
        }

    return {
        "autonomy_audit_status": "failed",
        "ok_count": ok_count,
        "audit_phase": None,
    }
