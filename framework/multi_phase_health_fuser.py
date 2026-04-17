from typing import Any


def fuse_health_signals(
    health: dict[str, Any],
    resilience_cp: dict[str, Any],
    governance_cp: dict[str, Any],
) -> dict[str, Any]:
    if (
        not isinstance(health, dict)
        or not isinstance(resilience_cp, dict)
        or not isinstance(governance_cp, dict)
    ):
        return {
            "fusion_status": "invalid_input",
            "fused_phase": None,
            "signal_count": 0,
        }

    h_ok = health.get("health_status") in ("healthy", "degraded")
    res_ok = resilience_cp.get("resilience_cp_status") in ("operational", "degraded")
    gov_ok = governance_cp.get("governance_cp_status") in ("operational", "degraded")

    all_ok = h_ok and res_ok and gov_ok
    any_ok = h_ok or res_ok or gov_ok
    signal_count = sum([h_ok, res_ok, gov_ok])

    if all_ok:
        return {
            "fusion_status": "fused",
            "fused_phase": health.get("phase_id"),
            "signal_count": signal_count,
        }

    if any_ok:
        return {
            "fusion_status": "partial",
            "fused_phase": None,
            "signal_count": signal_count,
        }

    return {
        "fusion_status": "invalid_input",
        "fused_phase": None,
        "signal_count": signal_count,
    }
