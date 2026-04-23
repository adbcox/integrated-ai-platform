#!/usr/bin/env python3
"""Validate roadmap execution contracts for governed autonomous pull."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

import yaml

REPO_ROOT = Path(__file__).resolve().parent.parent
ITEMS_DIR = REPO_ROOT / "docs/roadmap/items"
OUTPUT_PATH = REPO_ROOT / "artifacts/validation/roadmap_execution_contract_validation.json"

REQUIRED_ITEMS = {
    "RM-GOV-001",
    "RM-OPS-004",
    "RM-OPS-005",
    "RM-AUTO-001",
    "RM-GOV-009",
}
PLANNABLE_STATUSES = {
    "proposed",
    "planned",
    "ready",
    "in_progress",
    "in_execution",
    "planned_for_execution",
}
AUTONOMOUS_STATUSES = {"eligible", "eligible_with_guardrails", "blocked"}
REQUIRED_TOP_LEVEL = {
    "autonomous_execution_status",
    "next_bounded_slice",
    "max_autonomous_scope",
    "validation_contract",
    "artifact_contract",
    "completion_contract",
    "truth_surface_updates_required",
    "external_dependency_readiness",
}


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def normalize(value: str | None) -> str:
    return (value or "").strip().lower()


def missing_fields(contract: dict) -> list[str]:
    missing: list[str] = []
    for field in sorted(REQUIRED_TOP_LEVEL):
        value = contract.get(field)
        if value in (None, "", [], {}):
            missing.append(field)

    validation = contract.get("validation_contract") or {}
    for field in ("required_validations", "pass_criteria"):
        if validation.get(field) in (None, "", [], {}):
            missing.append(f"validation_contract.{field}")

    artifact = contract.get("artifact_contract") or {}
    for field in ("required_artifacts", "evidence_outputs"):
        if artifact.get(field) in (None, "", [], {}):
            missing.append(f"artifact_contract.{field}")

    completion = contract.get("completion_contract") or {}
    for field in (
        "substep_complete_when",
        "bounded_slice_complete_when",
        "item_complete_when",
        "blocker_chain_cleared_when",
        "small_patch_is_not_completion",
    ):
        if completion.get(field) in (None, "", [], {}):
            missing.append(f"completion_contract.{field}")

    if completion.get("small_patch_is_not_completion") is not True:
        missing.append("completion_contract.small_patch_is_not_completion=true")

    external = contract.get("external_dependency_readiness") or {}
    for field in (
        "required",
        "readiness_status",
        "blocks_autonomous_execution",
        "blocking_dependencies",
    ):
        if external.get(field) in (None, ""):
            missing.append(f"external_dependency_readiness.{field}")

    return missing


def main() -> int:
    errors: list[str] = []
    checked_items = 0

    for item_file in sorted(ITEMS_DIR.glob("RM-*.yaml")):
        payload = yaml.safe_load(item_file.read_text(encoding="utf-8")) or {}
        item_id = payload.get("id") or item_file.stem
        status = normalize(payload.get("status"))
        contract = payload.get("execution_contract") or {}

        should_validate = item_id in REQUIRED_ITEMS or status in PLANNABLE_STATUSES
        if not should_validate:
            continue

        checked_items += 1

        if not contract:
            errors.append(f"{item_id}: missing execution_contract")
            continue

        missing = missing_fields(contract)
        if missing:
            errors.append(f"{item_id}: missing/invalid fields: {', '.join(sorted(set(missing)))}")

        auto_status = normalize(contract.get("autonomous_execution_status"))
        if auto_status not in AUTONOMOUS_STATUSES:
            errors.append(
                f"{item_id}: invalid autonomous_execution_status={contract.get('autonomous_execution_status')!r}"
            )

    result = {
        "generated_at": now_iso(),
        "checked_items": checked_items,
        "required_items": sorted(REQUIRED_ITEMS),
        "error_count": len(errors),
        "errors": errors,
        "status": "PASS" if not errors else "FAIL",
    }

    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT_PATH.write_text(json.dumps(result, indent=2), encoding="utf-8")

    print(json.dumps(result, indent=2))
    return 0 if not errors else 1


if __name__ == "__main__":
    raise SystemExit(main())
