#!/usr/bin/env python3
"""Emit machine-readable Phase 0 global gate closure evidence."""
from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import yaml

REPO_ROOT = Path(__file__).resolve().parents[1]
ARTIFACT = REPO_ROOT / "artifacts/governance/phase0_global_gate_closure.json"


def _now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def _load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _load_yaml(path: Path) -> dict[str, Any]:
    return yaml.safe_load(path.read_text(encoding="utf-8")) or {}


def _phase0_gate(phase_gate: dict[str, Any]) -> dict[str, Any]:
    return next((g for g in (phase_gate.get("gates") or []) if g.get("phase_id") == 0), {})


def main() -> int:
    checks: list[dict[str, Any]] = []
    failures: list[str] = []

    current_phase_path = REPO_ROOT / "governance/current_phase.json"
    phase_gate_path = REPO_ROOT / "governance/phase_gate_status.json"
    cmdb_path = REPO_ROOT / "governance/cmdb_lite_registry.v1.yaml"
    inventory_path = REPO_ROOT / "artifacts/governance/phase_authority_inventory.json"

    for path in [current_phase_path, phase_gate_path, cmdb_path, inventory_path]:
        ok = path.exists()
        checks.append({"check": f"exists::{path.relative_to(REPO_ROOT)}", "passed": ok})
        if not ok:
            failures.append(f"missing {path.relative_to(REPO_ROOT)}")

    if failures:
        ARTIFACT.parent.mkdir(parents=True, exist_ok=True)
        ARTIFACT.write_text(
            json.dumps(
                {
                    "artifact_id": "PHASE0-GLOBAL-GATE-CLOSURE-1",
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

    current_phase = _load_json(current_phase_path)
    phase_gate = _load_json(phase_gate_path)
    cmdb = _load_yaml(cmdb_path)
    inventory = _load_json(inventory_path)
    gate0_live = _phase0_gate(phase_gate)
    pre_state = {
        "provenance_mode": "immediate_live_snapshot",
        "captured_at": _now(),
        "source_files": [
            "governance/current_phase.json",
            "governance/phase_gate_status.json",
            "governance/cmdb_lite_registry.v1.yaml",
            "artifacts/governance/phase_authority_inventory.json",
        ],
        "current_phase_id": current_phase.get("current_phase_id"),
        "current_phase_status": current_phase.get("current_phase_status"),
        "phase0_gate_classification": gate0_live.get("classification"),
        "cmdb_phase_current": ((cmdb.get("phase") or {}).get("current")),
        "cmdb_phase_status": ((cmdb.get("phase") or {}).get("status")),
        "inventory_conflict_count": inventory.get("conflict_count"),
        "inventory_high_severity_conflicts": inventory.get("high_severity_conflicts"),
        "phase0_blocking_reason_if_open": gate0_live.get("blocking_reason_if_open"),
        "phase0_open_reason": gate0_live.get("blocking_reason_if_open")
        if gate0_live.get("classification") == "open"
        else "Phase 0 already closed at capture time.",
    }

    gate0 = gate0_live
    post_state = {
        "current_phase_id": current_phase.get("current_phase_id"),
        "current_phase_status": current_phase.get("current_phase_status"),
        "phase0_gate_classification": gate0.get("classification"),
        "phase0_gate_closure_evidence_ref": gate0.get("closure_evidence_ref"),
        "cmdb_phase_current": ((cmdb.get("phase") or {}).get("current")),
        "cmdb_phase_status": ((cmdb.get("phase") or {}).get("status")),
        "inventory_conflict_count": inventory.get("conflict_count"),
        "inventory_high_severity_conflicts": inventory.get("high_severity_conflicts"),
    }

    remaining_blockers: list[str] = []
    if gate0.get("classification") != "closed_ratified":
        remaining_blockers.append("Phase 0 gate is not closed_ratified in governance/phase_gate_status.json")
    if current_phase.get("current_phase_id") == 0:
        remaining_blockers.append("governance/current_phase.json still points to Phase 0 as current")
    if (cmdb.get("phase") or {}).get("current") == 0:
        remaining_blockers.append("governance/cmdb_lite_registry.v1.yaml phase.current still points to 0")
    if int(inventory.get("high_severity_conflicts") or 0) > 0:
        remaining_blockers.append("phase_authority_inventory still reports high-severity conflicts")

    phase0_closed = len(remaining_blockers) == 0
    checks.extend(
        [
            {"check": "phase0_gate_closed_ratified", "passed": gate0.get("classification") == "closed_ratified"},
            {"check": "current_phase_advanced_from_0", "passed": current_phase.get("current_phase_id") != 0},
            {"check": "cmdb_phase_advanced_from_0", "passed": (cmdb.get("phase") or {}).get("current") != 0},
            {"check": "inventory_high_severity_zero", "passed": int(inventory.get("high_severity_conflicts") or 0) == 0},
        ]
    )

    payload = {
        "artifact_id": "PHASE0-GLOBAL-GATE-CLOSURE-1",
        "generated_at": _now(),
        "pre_pass_phase0_state": pre_state,
        "post_pass_phase0_state": post_state,
        "phase0_global_closed": phase0_closed,
        "remaining_blockers": remaining_blockers,
        "supporting_surfaces": {
            "current_phase_ref": "governance/current_phase.json",
            "phase_gate_ref": "governance/phase_gate_status.json",
            "cmdb_ref": "governance/cmdb_lite_registry.v1.yaml",
            "inventory_ref": "artifacts/governance/phase_authority_inventory.json",
        },
        "all_checks_passed": phase0_closed,
        "checks": checks,
    }

    ARTIFACT.parent.mkdir(parents=True, exist_ok=True)
    ARTIFACT.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    print(f"artifact={ARTIFACT}")
    return 0 if phase0_closed else 1


if __name__ == "__main__":
    raise SystemExit(main())
