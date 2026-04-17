from typing import Any


def gate_handoff(
    manifest: dict[str, Any],
    briefing: dict[str, Any],
    checklist: dict[str, Any],
) -> dict[str, Any]:
    if (
        not isinstance(manifest, dict)
        or not isinstance(briefing, dict)
        or not isinstance(checklist, dict)
    ):
        return {
            "handoff_gate_status": "blocked",
            "gate_phase": None,
            "gate_result": None,
        }

    manifest_ok = manifest.get("manifest_status") == "built"
    brief_ok = briefing.get("briefing_status") == "generated"
    checklist_ok = checklist.get("checklist_status") == "built"

    if manifest_ok and brief_ok and checklist_ok:
        return {
            "handoff_gate_status": "open",
            "gate_phase": manifest.get("manifest_phase"),
            "gate_result": "handoff_ready",
        }

    return {
        "handoff_gate_status": "blocked",
        "gate_phase": None,
        "gate_result": None,
    }
