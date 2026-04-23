#!/usr/bin/env python3
"""Validate NEXT-tier autonomy expansion contracts and emit evidence artifact."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import yaml


REPO_ROOT = Path(__file__).resolve().parents[1]
ARTIFACT_PATH = REPO_ROOT / "artifacts/validation/next_tier_autonomy_expansion_validation.json"


class ValidationError(Exception):
    pass


def _load_yaml(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as f:
        data = yaml.safe_load(f)
    if not isinstance(data, dict):
        raise ValidationError(f"{path} did not parse to a mapping")
    return data


def _assert(cond: bool, message: str, errors: list[str]) -> None:
    if not cond:
        errors.append(message)


def main() -> int:
    errors: list[str] = []

    connector_policy = _load_yaml(REPO_ROOT / "governance/connector_control_plane_policy.v1.yaml")
    autonomy_contract = _load_yaml(REPO_ROOT / "governance/autonomy_goal_execution_contract.v1.yaml")
    apple_contract = _load_yaml(REPO_ROOT / "governance/apple_xcode_runtime_contract.v1.yaml")

    rm_gov_009 = _load_yaml(REPO_ROOT / "docs/roadmap/items/RM-GOV-009.yaml")
    rm_auto_001 = _load_yaml(REPO_ROOT / "docs/roadmap/items/RM-AUTO-001.yaml")
    rm_dev_001 = _load_yaml(REPO_ROOT / "docs/roadmap/items/RM-DEV-001.yaml")

    connectors = [c.get("id") for c in connector_policy.get("approved_connectors", [])]
    _assert(set(connectors) == {"github", "gmail", "google_calendar"}, "connector policy must include exactly github/gmail/google_calendar", errors)
    _assert(connector_policy.get("connector_boundary_rules", {}).get("default_mode") == "deny_unlisted", "connector policy must enforce deny_unlisted", errors)

    _assert("required_packet_fields" in autonomy_contract.get("packet_shaping", {}), "autonomy contract must define required packet fields", errors)
    _assert("allowed_routes" in autonomy_contract.get("route_selection", {}), "autonomy contract must define allowed routes", errors)

    _assert(apple_contract.get("runtime_integration", {}).get("unmanaged_parallel_apple_flow_allowed") is False, "apple contract must disable unmanaged parallel flow", errors)
    _assert(apple_contract.get("runtime_integration", {}).get("execution_authority") == "runtime/runtime_executor.py", "apple contract must link runtime executor", errors)

    _assert(rm_gov_009.get("status") == "completed", "RM-GOV-009 status must be completed", errors)
    _assert(rm_gov_009.get("planning", {}).get("planning_status") in {"complete", "completed"}, "RM-GOV-009 planning must be terminal", errors)
    _assert(rm_gov_009.get("execution", {}).get("execution_status") in {"complete", "completed"}, "RM-GOV-009 execution must be terminal", errors)
    _assert(rm_gov_009.get("validation", {}).get("validation_status") == "passed", "RM-GOV-009 validation must be passed", errors)

    _assert(rm_auto_001.get("status") == "completed", "RM-AUTO-001 status must be completed", errors)
    _assert(rm_auto_001.get("planning", {}).get("planning_status") in {"complete", "completed"}, "RM-AUTO-001 planning must be terminal", errors)
    _assert(rm_auto_001.get("execution", {}).get("execution_status") in {"complete", "completed"}, "RM-AUTO-001 execution must be terminal", errors)
    _assert(rm_auto_001.get("validation", {}).get("validation_status") == "passed", "RM-AUTO-001 validation must be passed", errors)

    _assert(rm_dev_001.get("status") == "completed", "RM-DEV-001 status must be completed", errors)
    _assert(rm_dev_001.get("archive_status") == "archived", "RM-DEV-001 archive_status must remain archived", errors)
    _assert(rm_dev_001.get("validation", {}).get("validation_status") == "passed", "RM-DEV-001 validation must be passed", errors)

    artifact = {
        "generated_at": "generated_by_runtime",
        "validator": "bin/validate_next_tier_autonomy_expansion.py",
        "checked_items": ["RM-GOV-009", "RM-AUTO-001", "RM-DEV-001"],
        "connector_policy_connectors": connectors,
        "errors": errors,
        "status": "PASS" if not errors else "FAIL",
    }

    ARTIFACT_PATH.parent.mkdir(parents=True, exist_ok=True)
    ARTIFACT_PATH.write_text(json.dumps(artifact, indent=2) + "\n", encoding="utf-8")

    print(json.dumps(artifact, indent=2))
    return 0 if not errors else 1


if __name__ == "__main__":
    raise SystemExit(main())
