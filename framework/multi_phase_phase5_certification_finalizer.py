from typing import Any


def finalize_phase5_certification(
    cert_gate: dict[str, Any],
    cert_cp: dict[str, Any],
    certification_summary: dict[str, Any],
) -> dict[str, Any]:
    if (
        not isinstance(cert_gate, dict)
        or not isinstance(cert_cp, dict)
        or not isinstance(certification_summary, dict)
    ):
        return {
            "cert_finalization_status": "failed",
            "finalization_phase": None,
            "finalization_result": None,
        }

    gate_ok = cert_gate.get("cert_gate_status") == "open"
    cp_ok = cert_cp.get("cert_cp_status") == "operational"
    sum_ok = certification_summary.get("certification_summary_status") == "complete"

    if gate_ok and cp_ok and sum_ok:
        return {
            "cert_finalization_status": "finalized",
            "finalization_phase": cert_gate.get("gate_phase"),
            "finalization_result": "cert_finalized",
        }

    return {
        "cert_finalization_status": "failed",
        "finalization_phase": None,
        "finalization_result": None,
    }
