#!/usr/bin/env python3
"""Validate scoped phase-authority lock closure and emit closure artifact."""
from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import yaml

REPO_ROOT = Path(__file__).resolve().parents[1]
OUT = REPO_ROOT / "artifacts/governance/phase_authority_lock_closure.json"

SCOPED_ITEMS = ["RM-GOV-004", "RM-GOV-005"]


def _iso_now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def _load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _load_yaml(path: Path) -> dict[str, Any]:
    return yaml.safe_load(path.read_text(encoding="utf-8")) or {}


def _check(checks: list[dict[str, Any]], failures: list[str], name: str, passed: bool, detail: str) -> None:
    checks.append({"check": name, "passed": passed, "detail": detail})
    if not passed:
        failures.append(f"{name}: {detail}")


def _dump(payload: dict[str, Any]) -> int:
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    print(f"artifact={OUT}")
    return 0 if payload.get("all_checks_passed") else 1


def main() -> int:
    checks: list[dict[str, Any]] = []
    failures: list[str] = []

    before_path = REPO_ROOT / "artifacts/governance/phase_authority_inventory_before_lock.json"
    after_path = REPO_ROOT / "artifacts/governance/phase_authority_inventory.json"
    registry_path = REPO_ROOT / "docs/roadmap/data/roadmap_registry.yaml"
    sync_path = REPO_ROOT / "docs/roadmap/data/sync_state.yaml"
    cp_path = REPO_ROOT / "governance/current_phase.json"
    pg_path = REPO_ROOT / "governance/phase_gate_status.json"
    cmdb_path = REPO_ROOT / "governance/cmdb_lite_registry.v1.yaml"

    for p in [before_path, after_path, registry_path, sync_path, cp_path, pg_path, cmdb_path]:
        _check(checks, failures, f"exists::{p.relative_to(REPO_ROOT)}", p.exists(), str(p.relative_to(REPO_ROOT)))

    if failures:
        return _dump(
            {
                "schema_version": 1,
                "artifact_id": "PHASE-AUTHORITY-LOCK-CLOSURE-1",
                "generated_at": _iso_now(),
                "all_checks_passed": False,
                "failure_reasons": failures,
                "checks": checks,
            }
        )

    before = _load_json(before_path)
    after = _load_json(after_path)
    registry = _load_yaml(registry_path)
    sync = _load_yaml(sync_path)
    current_phase = _load_json(cp_path)
    phase_gate = _load_json(pg_path)
    cmdb = _load_yaml(cmdb_path)

    before_high = int(before.get("high_severity_conflicts") or 0)
    after_high = int(after.get("high_severity_conflicts") or 0)
    _check(checks, failures, "before_had_high_conflicts", before_high > 0, f"before_high={before_high}")
    _check(checks, failures, "after_high_conflicts_resolved", after_high == 0, f"after_high={after_high}")

    _check(checks, failures, "after_closure_ready", bool(after.get("closure_ready")), f"closure_ready={after.get('closure_ready')}")

    reg_map = {row.get("id"): row for row in (registry.get("items") or [])}
    sync_map = {row.get("id"): row for row in (sync.get("items") or [])}

    scoped_state = {}
    for item_id in SCOPED_ITEMS:
        item = _load_yaml(REPO_ROOT / f"docs/roadmap/items/{item_id}.yaml")
        reg_row = reg_map.get(item_id) or {}
        sync_row = sync_map.get(item_id) or {}
        _check(checks, failures, f"{item_id}_title_match", reg_row.get("title") == item.get("title"), f"registry={reg_row.get('title')} item={item.get('title')}")
        _check(checks, failures, f"{item_id}_status_match", reg_row.get("status") == item.get("status"), f"registry={reg_row.get('status')} item={item.get('status')}")
        _check(checks, failures, f"{item_id}_archive_match_registry", reg_row.get("archive_status") == item.get("archive_status"), f"registry={reg_row.get('archive_status')} item={item.get('archive_status')}")
        _check(checks, failures, f"{item_id}_archive_match_sync", sync_row.get("archive_status") == item.get("archive_status"), f"sync={sync_row.get('archive_status')} item={item.get('archive_status')}")
        scoped_state[item_id] = {
            "title": item.get("title"),
            "status": item.get("status"),
            "archive_status": item.get("archive_status"),
        }

    cp_lock = (current_phase.get("phase_authority_lock") or {})
    pg_lock = (phase_gate.get("phase_authority_lock") or {})
    cmdb_phase = (cmdb.get("phase") or {})

    _check(checks, failures, "current_phase_lock_status", cp_lock.get("status") == "scoped_lock_closed", f"status={cp_lock.get('status')}")
    _check(checks, failures, "phase_gate_lock_status", pg_lock.get("status") == "scoped_lock_closed", f"status={pg_lock.get('status')}")
    _check(checks, failures, "cmdb_lock_status", cmdb_phase.get("authority_lock_status") == "scoped_lock_closed", f"status={cmdb_phase.get('authority_lock_status')}")

    return _dump(
        {
            "schema_version": 1,
            "artifact_id": "PHASE-AUTHORITY-LOCK-CLOSURE-1",
            "generated_at": _iso_now(),
            "scoped_items": SCOPED_ITEMS,
            "conflicts_before": {
                "conflict_count": int(before.get("conflict_count") or 0),
                "high_severity_conflicts": before_high,
            },
            "conflicts_after": {
                "conflict_count": int(after.get("conflict_count") or 0),
                "high_severity_conflicts": after_high,
            },
            "scoped_item_reconciliation": scoped_state,
            "phase_authority_alignment": {
                "current_phase": {
                    "current_phase_id": current_phase.get("current_phase_id"),
                    "current_phase_status": current_phase.get("current_phase_status"),
                    "phase_authority_lock": cp_lock,
                },
                "phase_gate_status": {
                    "phase0_classification": next((g.get("classification") for g in (phase_gate.get("gates") or []) if g.get("phase_id") == 0), None),
                    "phase_authority_lock": pg_lock,
                },
                "cmdb_phase": {
                    "current": cmdb_phase.get("current"),
                    "status": cmdb_phase.get("status"),
                    "authority_lock_status": cmdb_phase.get("authority_lock_status"),
                },
            },
            "all_checks_passed": len(failures) == 0,
            "failure_reasons": failures,
            "checks": checks,
        }
    )


if __name__ == "__main__":
    raise SystemExit(main())
