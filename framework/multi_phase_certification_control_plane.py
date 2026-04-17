from typing import Any


def control_certification(
    certification_rollup: dict[str, Any],
    evidence_rollup: dict[str, Any],
    cp_config: dict[str, Any],
) -> dict[str, Any]:
    if (
        not isinstance(certification_rollup, dict)
        or not isinstance(evidence_rollup, dict)
        or not isinstance(cp_config, dict)
    ):
        return {
            "cert_cp_status": "offline",
            "cp_phase": None,
            "cp_health": "unknown",
        }

    cert_ok = certification_rollup.get("certification_rollup_status") == "rolled_up"
    ev_ok = evidence_rollup.get("evidence_rollup_status") == "rolled_up"

    if cert_ok and ev_ok:
        return {
            "cert_cp_status": "operational",
            "cp_phase": certification_rollup.get("rollup_phase"),
            "cp_health": "healthy",
        }

    if cert_ok or ev_ok:
        return {
            "cert_cp_status": "degraded",
            "cp_phase": None,
            "cp_health": "degraded",
        }

    return {
        "cert_cp_status": "offline",
        "cp_phase": None,
        "cp_health": "offline",
    }
