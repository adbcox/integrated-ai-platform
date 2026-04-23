#!/usr/bin/env python3
"""Validate integrated ops/home/intel/inventory expansion slice evidence."""
from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

import yaml

REPO_ROOT = Path(__file__).resolve().parent.parent
POLICY_PATH = REPO_ROOT / "governance" / "integrated_ops_home_intel_inventory_policy.v1.yaml"
ARTIFACT_PATH = REPO_ROOT / "artifacts" / "operations" / "integrated_ops_expansion_run.json"
OUTPUT_PATH = REPO_ROOT / "artifacts" / "validation" / "integrated_ops_expansion_validation.json"
REQUIRED_ITEMS = {"RM-OPS-006", "RM-HOME-005", "RM-INTEL-003", "RM-INV-003"}


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def main() -> int:
    errors: list[str] = []

    if not POLICY_PATH.exists():
        errors.append(f"missing policy: {POLICY_PATH}")
    else:
        policy = yaml.safe_load(POLICY_PATH.read_text(encoding="utf-8")) or {}
        if policy.get("kind") != "integrated_ops_home_intel_inventory_policy":
            errors.append("policy kind mismatch")

    if not ARTIFACT_PATH.exists():
        errors.append(f"missing artifact: {ARTIFACT_PATH}")
        artifact = {}
    else:
        artifact = json.loads(ARTIFACT_PATH.read_text(encoding="utf-8"))

    if artifact:
        if set(artifact.get("roadmap_items", [])) != REQUIRED_ITEMS:
            errors.append("artifact roadmap_items mismatch")

        runtime = artifact.get("runtime_session", {})
        if not runtime.get("session_id") or not runtime.get("job_id"):
            errors.append("missing runtime session identifiers")

        truth = artifact.get("control_window_truth", {})
        if not truth.get("current_lane"):
            errors.append("missing control-window lane linkage")

        home_actions = artifact.get("home_operations", {}).get("actions", [])
        if len(home_actions) < 1:
            errors.append("home actions missing")

        intel_recs = artifact.get("intel_watch", {}).get("recommendations", [])
        if len(intel_recs) < 1:
            errors.append("intel recommendations missing")

        decisions = artifact.get("inventory_decision", {}).get("procurement_decisions", [])
        if len(decisions) < 1:
            errors.append("inventory procurement decisions missing")

        queue = artifact.get("ops_execution", {}).get("queue", [])
        if len(queue) < 3:
            errors.append("ops queue incomplete")

    result = {
        "generated_at": utc_now(),
        "status": "PASS" if not errors else "FAIL",
        "error_count": len(errors),
        "errors": errors,
        "required_items": sorted(REQUIRED_ITEMS),
        "artifact": str(ARTIFACT_PATH.relative_to(REPO_ROOT)),
    }

    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT_PATH.write_text(json.dumps(result, indent=2), encoding="utf-8")
    print(json.dumps(result, indent=2))

    return 0 if not errors else 1


if __name__ == "__main__":
    raise SystemExit(main())
