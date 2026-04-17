from typing import Any


def audit_witness_chain(
    witness: dict[str, Any],
    chain: dict[str, Any],
    verification: dict[str, Any],
) -> dict[str, Any]:
    if (
        not isinstance(witness, dict)
        or not isinstance(chain, dict)
        or not isinstance(verification, dict)
    ):
        return {
            "witness_audit_status": "failed",
            "audit_phase": None,
            "audit_result": None,
        }

    wit_ok = witness.get("witness_status") == "recorded"
    chain_ok = chain.get("chain_status") == "chained"
    ver_ok = verification.get("verification_status") == "verified"
    all_ok = wit_ok and chain_ok and ver_ok

    if all_ok:
        return {
            "witness_audit_status": "passed",
            "audit_phase": witness.get("witness_phase"),
            "audit_result": "witness_chain_valid",
        }

    if (wit_ok and chain_ok) or (wit_ok and ver_ok) or (chain_ok and ver_ok):
        return {
            "witness_audit_status": "degraded",
            "audit_phase": None,
            "audit_result": None,
        }

    return {
        "witness_audit_status": "failed",
        "audit_phase": None,
        "audit_result": None,
    }
