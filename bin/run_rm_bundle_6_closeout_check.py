#!/usr/bin/env python3
"""Validate RM-DEV-002/004/007 + RM-CORE-005 + RM-GOV-005 + RM-INV-005 integrated closeout."""
from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import yaml

REPO_ROOT = Path(__file__).resolve().parents[1]
OUT = REPO_ROOT / "artifacts/governance/rm_bundle_6_closeout_validation.json"

BUNDLE_ITEMS = [
    "RM-DEV-002",
    "RM-DEV-004",
    "RM-DEV-007",
    "RM-CORE-005",
    "RM-GOV-005",
    "RM-INV-005",
]

FILES = {
    "status_sync": "docs/roadmap/ROADMAP_STATUS_SYNC.md",
    "roadmap_master": "docs/roadmap/ROADMAP_MASTER.md",
    "roadmap_index": "docs/roadmap/ROADMAP_INDEX.md",
    "execution_pack_index": "docs/roadmap/EXECUTION_PACK_INDEX.md",
    "rm_dev_002_item": "docs/roadmap/items/RM-DEV-002.yaml",
    "rm_dev_004_item": "docs/roadmap/items/RM-DEV-004.yaml",
    "rm_dev_007_item": "docs/roadmap/items/RM-DEV-007.yaml",
    "rm_core_005_item": "docs/roadmap/items/RM-CORE-005.yaml",
    "rm_gov_005_item": "docs/roadmap/items/RM-GOV-005.yaml",
    "rm_inv_005_item": "docs/roadmap/items/RM-INV-005.yaml",
    "rm_dev_002_pack": "docs/roadmap/RM-DEV-002_EXECUTION_PACK.md",
    "rm_dev_004_pack": "docs/roadmap/RM-DEV-004_EXECUTION_PACK.md",
    "rm_dev_007_pack": "docs/roadmap/RM-DEV-007_EXECUTION_PACK.md",
    "rm_core_005_pack": "docs/roadmap/RM-CORE-005_EXECUTION_PACK.md",
    "rm_gov_005_pack": "docs/roadmap/RM-GOV-005_EXECUTION_PACK.md",
    "rm_inv_005_pack": "docs/roadmap/RM-INV-005_EXECUTION_PACK.md",
    "qc_schema": "governance/qc_finding_schema_rm_dev_002.v1.yaml",
    "qc_template": "governance/rm_dev_002_qc_result_template.v1.json",
    "firmware_baseline": "governance/firmware_assistant_baseline.v1.yaml",
    "indexed_retrieval": "governance/indexed_retrieval_backend.v1.yaml",
    "trust_boundary": "governance/trust_boundary_policy.v1.yaml",
    "cycle_batch": "governance/roadmap_cycle_batch_governance.v1.yaml",
    "asset_linkage": "governance/asset_execution_linkage.v1.yaml",
    "integrated_bundle": "governance/rm_bundle_6_integrated_closeout.v1.yaml",
    "local_command_runner": "framework/local_command_runner.py",
}


def _iso_now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def _load_yaml(path: Path) -> dict[str, Any]:
    return yaml.safe_load(path.read_text(encoding="utf-8")) or {}


def _load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _check(
    checks: dict[str, list[dict[str, Any]]],
    failures: list[str],
    section: str,
    name: str,
    passed: bool,
    detail: str,
) -> None:
    checks[section].append({"check": name, "passed": passed, "detail": detail})
    if not passed:
        failures.append(f"{section}.{name}: {detail}")


def _dump(payload: dict[str, Any]) -> int:
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    print(f"artifact={OUT}")
    return 0 if payload.get("overall_result") == "pass" else 1


def main() -> int:
    checks: dict[str, list[dict[str, Any]]] = {
        "file_presence": [],
        "item_status": [],
        "rm_dev_002": [],
        "rm_dev_004": [],
        "rm_dev_007": [],
        "rm_core_005": [],
        "rm_gov_005": [],
        "rm_inv_005": [],
        "integration": [],
        "status_sync": [],
    }
    failures: list[str] = []
    resolved = {name: REPO_ROOT / rel for name, rel in FILES.items()}

    for key, path in resolved.items():
        _check(checks, failures, "file_presence", f"{key}_exists", path.exists(), str(path.relative_to(REPO_ROOT)))

    if failures:
        return _dump(
            {
                "schema_version": 1,
                "package_id": "RM-BUNDLE-6-CLOSEOUT",
                "generated_at": _iso_now(),
                "validated_files": FILES,
                "checks": checks,
                "gate_results": {
                    "rm_dev_002_gate": False,
                    "rm_dev_004_gate": False,
                    "rm_dev_007_gate": False,
                    "rm_core_005_gate": False,
                    "rm_gov_005_gate": False,
                    "rm_inv_005_gate": False,
                    "integration_gate": False,
                    "validation_gate": False,
                },
                "overall_result": "fail",
                "failure_reasons": failures,
            }
        )

    item_payloads = {
        item_id: _load_yaml(REPO_ROOT / f"docs/roadmap/items/{item_id}.yaml")
        for item_id in BUNDLE_ITEMS
    }
    for item_id, payload in item_payloads.items():
        _check(
            checks,
            failures,
            "item_status",
            f"{item_id}_status_completed",
            str(payload.get("status")) == "completed",
            f"status={payload.get('status')}",
        )
        _check(
            checks,
            failures,
            "item_status",
            f"{item_id}_archive_ready",
            str(payload.get("archive_status")) in {"ready_for_archive", "archived"},
            f"archive_status={payload.get('archive_status')}",
        )

    qc_schema = _load_yaml(resolved["qc_schema"])
    qc_template = _load_json(resolved["qc_template"])
    _check(
        checks,
        failures,
        "rm_dev_002",
        "qc_categories_present",
        set(qc_schema.get("finding_categories") or []) == {"correctness", "safety", "structural", "style_noise"},
        f"categories={qc_schema.get('finding_categories')}",
    )
    _check(
        checks,
        failures,
        "rm_dev_002",
        "qc_template_has_findings",
        isinstance(qc_template.get("findings"), list),
        "rm_dev_002_qc_result_template must include findings list",
    )

    firmware = _load_yaml(resolved["firmware_baseline"])
    platforms = [row.get("id") for row in (firmware.get("platform_scope") or [])]
    _check(checks, failures, "rm_dev_004", "firmware_scope_has_nordic_esp", {"nordic_nrf52", "esp32"}.issubset(set(platforms)), f"platforms={platforms}")
    _check(
        checks,
        failures,
        "rm_dev_004",
        "firmware_workflow_stage_count",
        len((firmware.get("workflow_contract") or {}).get("stages") or []) >= 4,
        f"stages={len((firmware.get('workflow_contract') or {}).get('stages') or [])}",
    )

    retrieval = _load_yaml(resolved["indexed_retrieval"])
    primary = ((retrieval.get("backend_decisions") or {}).get("primary_backend") or {}).get("name")
    _check(checks, failures, "rm_dev_007", "primary_backend_selected", bool(primary), f"primary={primary}")
    _check(
        checks,
        failures,
        "rm_dev_007",
        "multi_repo_roots_present",
        len((retrieval.get("multi_repo_contract") or {}).get("index_roots") or []) >= 2,
        f"roots={((retrieval.get('multi_repo_contract') or {}).get('index_roots') or [])}",
    )

    trust = _load_yaml(resolved["trust_boundary"])
    _check(
        checks,
        failures,
        "rm_core_005",
        "identity_principals_present",
        len(((trust.get("identity_model") or {}).get("principals") or [])) >= 3,
        f"principals={((trust.get('identity_model') or {}).get('principals') or [])}",
    )
    _check(
        checks,
        failures,
        "rm_core_005",
        "secrets_repo_prohibited",
        any(row.get("repo_allowed") is False for row in ((trust.get("secrets_policy") or {}).get("secret_classes") or [])),
        "at least one secret class must be repo disallowed",
    )

    cycle = _load_yaml(resolved["cycle_batch"])
    _check(
        checks,
        failures,
        "rm_gov_005",
        "cycle_length_defined",
        int(((cycle.get("cycle_model") or {}).get("cycle_length_days") or 0)) > 0,
        f"cycle_length_days={((cycle.get('cycle_model') or {}).get('cycle_length_days'))}",
    )
    _check(
        checks,
        failures,
        "rm_gov_005",
        "batch_fields_present",
        len(((cycle.get("batch_model") or {}).get("required_batch_fields") or [])) >= 5,
        f"required_batch_fields={((cycle.get('batch_model') or {}).get('required_batch_fields') or [])}",
    )

    linkage = _load_yaml(resolved["asset_linkage"])
    links = linkage.get("asset_links") or []
    linked_items = {row.get("roadmap_item") for row in links}
    _check(checks, failures, "rm_inv_005", "asset_links_cover_bundle", set(BUNDLE_ITEMS).issubset(linked_items), f"linked_items={sorted(linked_items)}")
    _check(
        checks,
        failures,
        "rm_inv_005",
        "asset_link_required_fields",
        all(
            all(field in row for field in ["asset_id", "asset_path", "roadmap_item", "execution_pack", "role", "validation_ref"])
            for row in links
        ),
        "each asset link must include required fields",
    )

    integrated = _load_yaml(resolved["integrated_bundle"])
    integrated_items = set(integrated.get("roadmap_items") or [])
    _check(checks, failures, "integration", "bundle_contains_all_items", integrated_items == set(BUNDLE_ITEMS), f"integrated_items={sorted(integrated_items)}")
    chain = integrated.get("integration_chain") or []
    _check(checks, failures, "integration", "integration_chain_has_all_steps", len(chain) >= 6, f"chain_steps={len(chain)}")

    status_sync_text = resolved["status_sync"].read_text(encoding="utf-8")
    _check(
        checks,
        failures,
        "status_sync",
        "start_in_progress_section_present",
        "In Progress (Start-of-pass" in status_sync_text,
        "missing start-of-pass section",
    )
    _check(
        checks,
        failures,
        "status_sync",
        "end_closed_section_present",
        "Completed / Closed (End-of-pass" in status_sync_text,
        "missing end-of-pass closed section",
    )
    for item_id in BUNDLE_ITEMS:
        _check(
            checks,
            failures,
            "status_sync",
            f"{item_id}_listed_closed",
            item_id in status_sync_text,
            f"{item_id} missing from status sync",
        )

    master_text = resolved["roadmap_master"].read_text(encoding="utf-8")
    index_text = resolved["roadmap_index"].read_text(encoding="utf-8")
    _check(checks, failures, "status_sync", "master_no_active_bundle_claim", "Active integrated closeout bundle (in progress)" not in master_text, "master still marks bundle in progress")
    _check(checks, failures, "status_sync", "index_no_in_progress_bundle_claim", "In-progress closeout bundle" not in index_text, "index still marks bundle in progress")

    gate_results = {
        "rm_dev_002_gate": not any(f.startswith("rm_dev_002") for f in failures),
        "rm_dev_004_gate": not any(f.startswith("rm_dev_004") for f in failures),
        "rm_dev_007_gate": not any(f.startswith("rm_dev_007") for f in failures),
        "rm_core_005_gate": not any(f.startswith("rm_core_005") for f in failures),
        "rm_gov_005_gate": not any(f.startswith("rm_gov_005") for f in failures),
        "rm_inv_005_gate": not any(f.startswith("rm_inv_005") for f in failures),
        "integration_gate": not any(f.startswith("integration") for f in failures),
        "validation_gate": len(failures) == 0,
    }

    return _dump(
        {
            "schema_version": 1,
            "package_id": "RM-BUNDLE-6-CLOSEOUT",
            "generated_at": _iso_now(),
            "validated_files": FILES,
            "checks": checks,
            "gate_results": gate_results,
            "overall_result": "pass" if not failures else "fail",
            "failure_reasons": failures,
        }
    )


if __name__ == "__main__":
    raise SystemExit(main())
