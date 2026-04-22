#!/usr/bin/env python3
"""Emit machine-readable residual closure evidence for Phase 0 authority issues."""
from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[1]
ARTIFACT = REPO_ROOT / "artifacts/governance/phase0_residual_authority_closure.json"
INVENTORY = REPO_ROOT / "artifacts/governance/phase_authority_inventory.json"
BEFORE_LOCK = REPO_ROOT / "artifacts/governance/phase_authority_inventory_before_lock.json"
CURRENT_PHASE = REPO_ROOT / "governance/current_phase.json"
PHASE_GATE = REPO_ROOT / "governance/phase_gate_status.json"


def _load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def main() -> int:
    failures: list[str] = []
    checks: list[dict[str, Any]] = []

    for required in [INVENTORY, BEFORE_LOCK, CURRENT_PHASE, PHASE_GATE]:
        ok = required.exists()
        checks.append(
            {
                "check": f"exists::{required.relative_to(REPO_ROOT)}",
                "passed": ok,
            }
        )
        if not ok:
            failures.append(f"missing: {required.relative_to(REPO_ROOT)}")

    if failures:
        ARTIFACT.parent.mkdir(parents=True, exist_ok=True)
        ARTIFACT.write_text(
            json.dumps(
                {
                    "artifact_id": "PHASE0-RESIDUAL-AUTHORITY-CLOSURE-1",
                    "generated_at": _now(),
                    "all_checks_passed": False,
                    "failure_reasons": failures,
                    "checks": checks,
                },
                indent=2,
            ),
            encoding="utf-8",
        )
        print(f"artifact={ARTIFACT}")
        return 1

    before = _load_json(BEFORE_LOCK)
    after = _load_json(INVENTORY)
    current_phase = _load_json(CURRENT_PHASE)
    phase_gate = _load_json(PHASE_GATE)

    before_conflicts = {
        c.get("conflict_id"): c for c in before.get("conflicts", before.get("authority_conflicts", []))
    }
    after_conflicts = {
        c.get("conflict_id"): c for c in after.get("conflicts", after.get("authority_conflicts", []))
    }

    conf03_resolved = "CONF-03" in before_conflicts and "CONF-03" not in after_conflicts
    conf04_resolved = "CONF-04" in before_conflicts and "CONF-04" not in after_conflicts
    phase0_gate = next((gate for gate in phase_gate.get("gates", []) if gate.get("phase_id") == 0), {})

    remaining_blockers: list[str] = []
    phase0_closed_in_current_phase = (
        current_phase.get("phase0_status") == "closed_ratified"
        or current_phase.get("current_phase_id") != 0
    )
    if not phase0_closed_in_current_phase:
        remaining_blockers.append("Phase 0 global status remains open in governance/current_phase.json")
    if phase0_gate.get("classification") != "closed_ratified":
        remaining_blockers.append("Phase 0 gate remains open in governance/phase_gate_status.json")

    payload = {
        "artifact_id": "PHASE0-RESIDUAL-AUTHORITY-CLOSURE-1",
        "generated_at": _now(),
        "phase_scope": "phase0_residual_authority_closure",
        "pre_pass_remaining_issues": ["CONF-03", "CONF-04"],
        "post_pass_remaining_issues": sorted(after_conflicts.keys()),
        "issues_resolution": {
            "CONF-03": "resolved" if conf03_resolved else "open",
            "CONF-04": "resolved" if conf04_resolved else "open",
        },
        "phase0_completion": {
            "is_complete": len(remaining_blockers) == 0,
            "remaining_blockers": remaining_blockers,
        },
        "inventory_summary": {
            "before": {
                "conflict_count": before.get("conflict_count"),
                "high_severity_conflicts": before.get("high_severity_conflicts"),
            },
            "after": {
                "conflict_count": after.get("conflict_count"),
                "high_severity_conflicts": after.get("high_severity_conflicts"),
            },
        },
        "all_checks_passed": conf03_resolved and conf04_resolved,
        "checks": checks,
    }

    ARTIFACT.parent.mkdir(parents=True, exist_ok=True)
    ARTIFACT.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    print(f"artifact={ARTIFACT}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
