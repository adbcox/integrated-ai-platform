from typing import Any


def record_release_decision(
    existing_ledger: dict[str, Any],
    release_id: str,
    enforcement_result: dict[str, Any],
    packet_result: dict[str, Any],
) -> dict[str, Any]:
    if (
        not isinstance(existing_ledger, dict)
        or not isinstance(release_id, str)
        or not release_id
        or not isinstance(enforcement_result, dict)
        or not isinstance(packet_result, dict)
    ):
        return {
            "ledger_valid": False,
            "release_count": 0,
            "releases": {},
            "approved_count": 0,
            "ledger_status": "invalid_input",
        }

    prior_releases = existing_ledger.get("releases", {})
    if not isinstance(prior_releases, dict):
        prior_releases = {}

    approved = (
        enforcement_result.get("release_approved", False)
        and packet_result.get("packet_complete", False)
    )
    enforcement_status = enforcement_result.get("enforcement_status", "unknown")
    packet_status = packet_result.get("packet_status", "unknown")

    releases = dict(prior_releases)
    ledger_status = "updated" if release_id in releases else "recorded"
    releases[release_id] = {
        "approved": approved,
        "enforcement_status": enforcement_status,
        "packet_status": packet_status,
    }
    approved_count = len(
        [rid for rid, entry in releases.items() if isinstance(entry, dict) and entry.get("approved") is True]
    )

    return {
        "ledger_valid": True,
        "release_count": len(releases),
        "releases": releases,
        "approved_count": approved_count,
        "ledger_status": ledger_status,
    }


def summarize_release_ledger(result: dict[str, Any]) -> dict[str, Any]:
    if not isinstance(result, dict) or result.get("ledger_valid") is not True:
        return {
            "summary_valid": False,
            "ledger_status": "invalid_input",
            "release_count": 0,
            "approved_count": 0,
        }

    return {
        "summary_valid": True,
        "ledger_status": result.get("ledger_status", "invalid_input"),
        "release_count": int(result.get("release_count", 0)),
        "approved_count": int(result.get("approved_count", 0)),
    }
