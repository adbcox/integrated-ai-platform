from typing import Any


def build_handoff_manifest(
    seal: dict[str, Any],
    phase5_exit_readiness: dict[str, Any],
    manifest_config: dict[str, Any],
) -> dict[str, Any]:
    if (
        not isinstance(seal, dict)
        or not isinstance(phase5_exit_readiness, dict)
        or not isinstance(manifest_config, dict)
    ):
        return {
            "manifest_status": "invalid_input",
            "manifest_phase": None,
            "manifest_entries": 0,
        }

    seal_ok = seal.get("seal_status") == "sealed"
    exit_ok = phase5_exit_readiness.get("exit_readiness_status") == "valid"

    if seal_ok and exit_ok:
        return {
            "manifest_status": "built",
            "manifest_phase": seal.get("seal_phase"),
            "manifest_entries": seal.get("seal_count", 0),
        }

    return {
        "manifest_status": "failed",
        "manifest_phase": None,
        "manifest_entries": 0,
    }
