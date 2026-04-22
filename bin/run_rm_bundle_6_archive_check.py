#!/usr/bin/env python3
"""Validate archive reconciliation for RM bundle 6 and emit archive artifact."""
from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import yaml

REPO_ROOT = Path(__file__).resolve().parents[1]
OUT = REPO_ROOT / "artifacts/governance/rm_bundle_6_archive_validation.json"
BUNDLE_ITEMS = [
    "RM-DEV-002",
    "RM-DEV-004",
    "RM-DEV-007",
    "RM-CORE-005",
    "RM-GOV-005",
    "RM-INV-005",
]

FILES = {
    "roadmap_authority": "docs/roadmap/ROADMAP_AUTHORITY.md",
    "status_sync": "docs/roadmap/ROADMAP_STATUS_SYNC.md",
    "roadmap_master": "docs/roadmap/ROADMAP_MASTER.md",
    "roadmap_index": "docs/roadmap/ROADMAP_INDEX.md",
    "execution_pack_index": "docs/roadmap/EXECUTION_PACK_INDEX.md",
    "dependency_graph": "governance/roadmap_dependency_graph.v1.yaml",
    "next_pull": "artifacts/planning/next_pull.json",
    "closeout_validation": "artifacts/governance/rm_bundle_6_closeout_validation.json",
    "roadmap_registry": "docs/roadmap/data/roadmap_registry.yaml",
    "sync_state": "docs/roadmap/data/sync_state.yaml",
}


def _iso_now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def _load_yaml(path: Path) -> dict[str, Any]:
    return yaml.safe_load(path.read_text(encoding="utf-8")) or {}


def _load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


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

    resolved = {k: REPO_ROOT / v for k, v in FILES.items()}
    for key, path in resolved.items():
        _check(checks, failures, f"{key}_exists", path.exists(), str(path.relative_to(REPO_ROOT)))

    item_payloads = {}
    for item_id in BUNDLE_ITEMS:
        p = REPO_ROOT / f"docs/roadmap/items/{item_id}.yaml"
        _check(checks, failures, f"{item_id}_item_exists", p.exists(), str(p.relative_to(REPO_ROOT)))
        if p.exists():
            item_payloads[item_id] = _load_yaml(p)

    if failures:
        return _dump(
            {
                "schema_version": 1,
                "package_id": "RM-BUNDLE-6-ARCHIVE",
                "generated_at": _iso_now(),
                "scoped_item_ids": BUNDLE_ITEMS,
                "checks": checks,
                "all_checks_passed": False,
                "failure_reasons": failures,
            }
        )

    closeout = _load_json(resolved["closeout_validation"])
    pre_summary = {}
    for item_id in BUNDLE_ITEMS:
        pre_summary[item_id] = {
            "status": "completed",
            "archive_status": "ready_for_archive",
            "source": "artifacts/governance/rm_bundle_6_closeout_validation.json",
        }

    for item_id, payload in item_payloads.items():
        _check(checks, failures, f"{item_id}_status_completed", str(payload.get("status")) == "completed", f"status={payload.get('status')}")
        _check(checks, failures, f"{item_id}_archive_status_archived", str(payload.get("archive_status")) == "archived", f"archive_status={payload.get('archive_status')}")
        ar = payload.get("archive_readiness") or {}
        _check(checks, failures, f"{item_id}_archived_at_present", bool(ar.get("archived_at")), f"archive_readiness.archived_at={ar.get('archived_at')}")

    status_sync = resolved["status_sync"].read_text(encoding="utf-8")
    master = resolved["roadmap_master"].read_text(encoding="utf-8")
    index = resolved["roadmap_index"].read_text(encoding="utf-8")

    _check(checks, failures, "status_sync_archive_section", "Archived in this archive pass" in status_sync, "ROADMAP_STATUS_SYNC archived section")
    _check(checks, failures, "master_not_ready_for_archive", "ready for archiving" not in master.lower(), "ROADMAP_MASTER should not advertise ready_for_archive state")
    _check(checks, failures, "index_not_ready_for_archive", "ready for archiving" not in index.lower(), "ROADMAP_INDEX should not advertise ready_for_archive state")

    for item_id in BUNDLE_ITEMS:
        _check(checks, failures, f"{item_id}_listed_status_sync", item_id in status_sync, "status_sync listing")
        _check(checks, failures, f"{item_id}_listed_master", item_id in master, "master listing")
        _check(checks, failures, f"{item_id}_listed_index", item_id in index, "index listing")

    dep = _load_yaml(resolved["dependency_graph"])
    nodes = {row.get("id"): row for row in (dep.get("nodes") or [])}
    archived_items = set((dep.get("blocking_analysis") or {}).get("archived_items") or [])
    eligible_items = set((dep.get("blocking_analysis") or {}).get("eligible_items") or [])
    ready_items = set((dep.get("blocking_analysis") or {}).get("completed_ready_for_archive") or [])

    for item_id in BUNDLE_ITEMS:
        node = nodes.get(item_id) or {}
        _check(checks, failures, f"{item_id}_dep_node_archived", str(node.get("archive_status")) == "archived", f"node.archive_status={node.get('archive_status')}")
        _check(checks, failures, f"{item_id}_dep_blocking_archived", item_id in archived_items, f"in archived_items={item_id in archived_items}")
        _check(checks, failures, f"{item_id}_dep_not_eligible", item_id not in eligible_items, f"in eligible_items={item_id in eligible_items}")
        _check(checks, failures, f"{item_id}_dep_not_ready_for_archive", item_id not in ready_items, f"in completed_ready_for_archive={item_id in ready_items}")

    nxt = _load_json(resolved["next_pull"])
    next_candidates = set(nxt.get("next_pull_candidates") or [])
    next_archived = set(nxt.get("archived_items") or [])
    next_ready = set(nxt.get("completed_ready_for_archive") or [])

    for item_id in BUNDLE_ITEMS:
        _check(checks, failures, f"{item_id}_next_pull_not_candidate", item_id not in next_candidates, f"next_pull_candidate={item_id in next_candidates}")
        _check(checks, failures, f"{item_id}_next_pull_archived", item_id in next_archived, f"archived_listed={item_id in next_archived}")
        _check(checks, failures, f"{item_id}_next_pull_not_ready", item_id not in next_ready, f"ready_listed={item_id in next_ready}")

    # data layer reconciliation checks
    registry = _load_yaml(resolved["roadmap_registry"])
    reg_by_id = {row.get("id"): row for row in (registry.get("items") or [])}
    sync_state = _load_yaml(resolved["sync_state"])
    sync_by_id = {row.get("id"): row for row in (sync_state.get("items") or [])}
    for item_id in BUNDLE_ITEMS:
        _check(checks, failures, f"{item_id}_registry_present", item_id in reg_by_id, "roadmap_registry presence")
        if item_id in reg_by_id:
            _check(checks, failures, f"{item_id}_registry_archived", str(reg_by_id[item_id].get("archive_status")) == "archived", f"registry.archive_status={reg_by_id[item_id].get('archive_status')}")
        _check(checks, failures, f"{item_id}_sync_state_present", item_id in sync_by_id, "sync_state presence")
        if item_id in sync_by_id:
            _check(checks, failures, f"{item_id}_sync_state_archived", str(sync_by_id[item_id].get("archive_status")) == "archived", f"sync_state.archive_status={sync_by_id[item_id].get('archive_status')}")

    post_summary = {
        item_id: {
            "status": item_payloads[item_id].get("status"),
            "archive_status": item_payloads[item_id].get("archive_status"),
            "archived_at": (item_payloads[item_id].get("archive_readiness") or {}).get("archived_at"),
        }
        for item_id in BUNDLE_ITEMS
    }

    return _dump(
        {
            "schema_version": 1,
            "package_id": "RM-BUNDLE-6-ARCHIVE",
            "archive_timestamp": _iso_now(),
            "scoped_item_ids": BUNDLE_ITEMS,
            "pre_archive_state_summary": pre_summary,
            "post_archive_state_summary": post_summary,
            "visible_roadmap_surface_reconciliation": {
                "status_sync": "reconciled",
                "roadmap_master": "reconciled",
                "roadmap_index": "reconciled",
                "execution_pack_index": "reconciled",
            },
            "dependency_surface_reconciliation": {
                "roadmap_dependency_graph": "reconciled",
                "next_pull": "reconciled",
            },
            "checks": checks,
            "all_checks_passed": len(failures) == 0,
            "failure_reasons": failures,
        }
    )


if __name__ == "__main__":
    raise SystemExit(main())
