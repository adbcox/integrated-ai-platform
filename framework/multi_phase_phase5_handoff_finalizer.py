from typing import Any


def finalize_phase5_handoff(
    handoff_gate: dict[str, Any],
    manifest: dict[str, Any],
    briefing: dict[str, Any],
) -> dict[str, Any]:
    if (
        not isinstance(handoff_gate, dict)
        or not isinstance(manifest, dict)
        or not isinstance(briefing, dict)
    ):
        return {
            "handoff_finalization_status": "failed",
            "finalization_phase": None,
            "finalization_result": None,
        }

    gate_ok = handoff_gate.get("handoff_gate_status") == "open"
    manifest_ok = manifest.get("manifest_status") == "built"
    brief_ok = briefing.get("briefing_status") == "generated"

    if gate_ok and manifest_ok and brief_ok:
        return {
            "handoff_finalization_status": "finalized",
            "finalization_phase": handoff_gate.get("gate_phase"),
            "finalization_result": "handoff_finalized",
        }

    return {
        "handoff_finalization_status": "failed",
        "finalization_phase": None,
        "finalization_result": None,
    }
