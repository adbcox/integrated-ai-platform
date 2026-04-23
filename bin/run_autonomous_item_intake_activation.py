#!/usr/bin/env python3
"""
Validate and emit autonomous canonical item intake activation evidence.
"""

import json
from datetime import datetime, timezone
from pathlib import Path

import yaml

REPO_ROOT = Path(__file__).resolve().parent.parent
CURRENT_PHASE_PATH = REPO_ROOT / "governance/current_phase.json"
NEXT_PACKAGE_PATH = REPO_ROOT / "governance/next_package_class.json"
POLICY_PATH = REPO_ROOT / "governance/autonomous_intake_policy.v1.yaml"
ARTIFACT_PATH = REPO_ROOT / "artifacts/governance/autonomous_item_intake_activation.json"


def _load_json(path: Path) -> dict:
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def _load_yaml(path: Path) -> dict:
    with path.open("r", encoding="utf-8") as handle:
        return yaml.safe_load(handle) or {}


def main() -> int:
    current_phase = _load_json(CURRENT_PHASE_PATH)
    next_package = _load_json(NEXT_PACKAGE_PATH)
    policy = _load_yaml(POLICY_PATH)

    expected_class = "autonomous_roadmap_item_creation"
    checks = {
        "current_phase_next_allowed_matches": current_phase.get("next_allowed_package_class")
        == expected_class,
        "next_package_class_matches": next_package.get("current_allowed_class") == expected_class,
        "policy_allowed_class_matches": (policy.get("rules") or {}).get("allowed_package_class")
        == expected_class,
    }
    all_checks_passed = all(checks.values())

    artifact = {
        "validation_kind": "autonomous_item_intake_activation",
        "generated_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "expected_class": expected_class,
        "checks": checks,
        "activation_enabled": all_checks_passed,
        "policy_ref": str(POLICY_PATH.relative_to(REPO_ROOT)),
    }
    ARTIFACT_PATH.parent.mkdir(parents=True, exist_ok=True)
    with ARTIFACT_PATH.open("w", encoding="utf-8") as handle:
        json.dump(artifact, handle, indent=2)

    print("autonomous_item_intake_activation:", "PASS" if all_checks_passed else "FAIL")
    print("artifact:", ARTIFACT_PATH)
    return 0 if all_checks_passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
