from typing import Any


def audit_registry(
    registry_result: dict[str, Any], required_phase_ids: list[str]
) -> dict[str, Any]:
    if not isinstance(registry_result, dict) or not isinstance(required_phase_ids, list):
        return {
            "audit_valid": False,
            "registered_count": 0,
            "required_count": 0,
            "missing_phases": [],
            "incomplete_phases": [],
            "coverage_pct": 0.0,
            "registry_audit_status": "invalid_input",
        }

    phases = registry_result.get("phases", {})
    if not isinstance(phases, dict):
        phases = {}

    missing_phases = [pid for pid in required_phase_ids if pid not in phases]
    incomplete_phases = [
        pid
        for pid in phases
        if pid in required_phase_ids
        and isinstance(phases.get(pid), dict)
        and phases.get(pid, {}).get("packet_status") != "complete"
    ]

    required_count = len(required_phase_ids)
    coverage_pct = (
        round(((required_count - len(missing_phases)) / float(required_count)) * 100.0, 3)
        if required_count > 0
        else 100.0
    )

    if required_count == 0:
        status = "empty"
    elif len(missing_phases) == 0 and len(incomplete_phases) == 0:
        status = "complete"
    elif len(missing_phases) > 0:
        status = "missing_phases"
    else:
        status = "incomplete_entries"

    return {
        "audit_valid": True,
        "registered_count": len(phases),
        "required_count": required_count,
        "missing_phases": missing_phases,
        "incomplete_phases": incomplete_phases,
        "coverage_pct": coverage_pct,
        "registry_audit_status": status,
    }


def summarize_registry_audit(result: dict[str, Any]) -> dict[str, Any]:
    if not isinstance(result, dict) or result.get("audit_valid") is not True:
        return {
            "summary_valid": False,
            "registry_audit_status": "invalid_input",
            "coverage_pct": 0.0,
            "missing_phase_count": 0,
        }

    return {
        "summary_valid": True,
        "registry_audit_status": result.get("registry_audit_status", "invalid_input"),
        "coverage_pct": float(result.get("coverage_pct", 0.0)),
        "missing_phase_count": (
            len(result.get("missing_phases", []))
            if isinstance(result.get("missing_phases", []), list)
            else 0
        ),
    }
