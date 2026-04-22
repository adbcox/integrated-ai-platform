#!/usr/bin/env python3
"""Validate integrated RM-INTEL-002/RM-DEV-005/RM-DEV-003/RM-DEV-002/RM-INTEL-001 slice."""
from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import yaml

REPO_ROOT = Path(__file__).resolve().parents[1]

FILES = {
    "roadmap_master": "docs/roadmap/ROADMAP_MASTER.md",
    "roadmap_index": "docs/roadmap/ROADMAP_INDEX.md",
    "standards": "docs/roadmap/STANDARDS.md",
    "high_priority_guide": "docs/roadmap/HIGH_PRIORITY_IMPLEMENTATION_GUIDE.md",
    "execution_pack_index": "docs/roadmap/EXECUTION_PACK_INDEX.md",
    "rm_intel_002_pack": "docs/roadmap/RM-INTEL-002_EXECUTION_PACK.md",
    "rm_intel_002_dossier": "docs/roadmap/RM-INTEL-002_RESEARCH_DOSSIER_2026-04-21.md",
    "rm_dev_005_pack": "docs/roadmap/RM-DEV-005_EXECUTION_PACK.md",
    "rm_dev_003_pack": "docs/roadmap/RM-DEV-003_EXECUTION_PACK.md",
    "rm_dev_002_pack": "docs/roadmap/RM-DEV-002_EXECUTION_PACK.md",
    "rm_intel_001_pack": "docs/roadmap/RM-INTEL-001_EXECUTION_PACK.md",
    "rm_intel_002_item": "docs/roadmap/items/RM-INTEL-002.yaml",
    "rm_dev_005_item": "docs/roadmap/items/RM-DEV-005.yaml",
    "rm_dev_003_item": "docs/roadmap/items/RM-DEV-003.yaml",
    "rm_dev_002_item": "docs/roadmap/items/RM-DEV-002.yaml",
    "rm_intel_001_item": "docs/roadmap/items/RM-INTEL-001.yaml",
    "roadmap_registry": "docs/roadmap/data/roadmap_registry.yaml",
    "sync_state": "docs/roadmap/data/sync_state.yaml",
    "harvest": "governance/verified_oss_capability_harvest_rm_intel_002.v1.yaml",
    "watchtower": "governance/oss_watchtower_candidates.v1.yaml",
    "linkage": "governance/rm_dev_003_rm_intel_001_linkage.v1.yaml",
    "bounded_contract": "governance/bounded_autonomous_codegen_contract.v1.yaml",
    "qc_schema": "governance/qc_finding_schema_rm_dev_002.v1.yaml",
    "qc_template": "governance/rm_dev_002_qc_result_template.v1.json",
    "oss_intake": "governance/oss_intake_registry.v1.yaml",
    "model_profiles": "governance/model_profiles.v1.yaml",
    "dev005_authority_state": "governance/rm_dev_005a_authority_state.v1.yaml",
    "qc_pattern_store": "governance/qc_pattern_store.v1.yaml",
    "intel_refresh_runner": "bin/run_rm_intel_refresh_delta.py",
    "watchtower_projection_runner": "bin/run_oss_watchtower_projection.py",
    "bounded_codegen_runner": "bin/run_bounded_autonomous_codegen.py",
    "qc_runner": "bin/run_rm_dev_002_qc.py",
    "orchestrator_runner": "bin/run_full_system_orchestrator.py",
    "bounded_task_example": "governance/bounded_codegen_task_example.v1.json",
    "oss_refresh_delta_artifact": "artifacts/governance/oss_refresh_delta.json",
    "oss_watchtower_projection_artifact": "artifacts/governance/oss_watchtower_projection.json",
    "bounded_run_latest_artifact": "artifacts/bounded_autonomy/runs/latest_run.json",
    "qc_latest_artifact": "artifacts/qc/latest_qc_result.json",
    "system_run_latest_artifact": "artifacts/system_runs/latest/system_run_summary.json",
}

OUT_ARTIFACT = REPO_ROOT / "artifacts/governance/rm_integrated_5_item_validation.json"
REQUIRED_RECOMMENDATION_CLASSES = {"adopt-now", "evaluate", "watch", "reject"}
REQUIRED_CANDIDATES = {
    "Ollama",
    "Aider",
    "MCP",
    "OpenHands SDK",
    "Qdrant",
    "gVisor",
    "SWE-bench",
    "Continue",
    "Tree-sitter",
    "LSP",
    "ast-grep",
    "Zoekt",
    "OpenCode",
    "Goose",
    "Plandex",
    "Mem0",
    "OpenGrep",
}
REQUIRED_BOUNDED_FIELDS = {
    "objective",
    "allowed_files",
    "forbidden_files",
    "expected_file_posture",
    "validation_sequence",
    "rollback_rule",
    "artifact_outputs",
    "promotion_decision",
}
REQUIRED_QC_CATEGORIES = {"correctness", "safety", "structural", "style_noise"}


def _iso_now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def _read_yaml(path: Path) -> dict[str, Any]:
    return yaml.safe_load(path.read_text(encoding="utf-8")) or {}


def _read_json(path: Path) -> dict[str, Any]:
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
    OUT_ARTIFACT.parent.mkdir(parents=True, exist_ok=True)
    OUT_ARTIFACT.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    print(f"artifact={OUT_ARTIFACT}")
    return 0 if payload.get("overall_result") == "pass" else 1


def main() -> int:
    checks: dict[str, list[dict[str, Any]]] = {
        "file_presence": [],
        "rm_intel_002": [],
        "rm_intel_001": [],
        "rm_dev_005": [],
        "rm_dev_003": [],
        "rm_dev_002": [],
        "operational_flows": [],
        "orchestration": [],
        "integration": [],
        "roadmap_registry_sync": [],
    }
    failures: list[str] = []
    resolved = {name: REPO_ROOT / rel for name, rel in FILES.items()}

    for name, path in resolved.items():
        _check(checks, failures, "file_presence", f"{name}_exists", path.exists(), str(path.relative_to(REPO_ROOT)))

    if failures:
        return _dump(
            {
                "schema_version": 1,
                "package_id": "RM-INTEGRATED-5-ITEM-ADVANCEMENT",
                "generated_at": _iso_now(),
                "validated_files": FILES,
                "checks": checks,
                "gate_results": {
                    "rm_intel_002_gate": False,
                    "rm_intel_001_gate": False,
                    "rm_dev_005_gate": False,
                    "rm_dev_003_gate": False,
                    "rm_dev_002_gate": False,
                    "operational_flow_gate": False,
                    "integration_gate": False,
                    "validation_gate": False,
                },
                "overall_result": "fail",
                "failure_reasons": failures,
            }
        )

    harvest = _read_yaml(resolved["harvest"])
    watchtower = _read_yaml(resolved["watchtower"])
    linkage = _read_yaml(resolved["linkage"])
    bounded = _read_yaml(resolved["bounded_contract"])
    qc_schema = _read_yaml(resolved["qc_schema"])
    qc_template = _read_json(resolved["qc_template"])
    refresh_delta = _read_json(resolved["oss_refresh_delta_artifact"])
    watchtower_projection = _read_json(resolved["oss_watchtower_projection_artifact"])
    bounded_run_latest = _read_json(resolved["bounded_run_latest_artifact"])
    qc_latest = _read_json(resolved["qc_latest_artifact"])
    authority = _read_yaml(resolved["dev005_authority_state"])
    model_profiles = _read_yaml(resolved["model_profiles"])
    registry = _read_yaml(resolved["roadmap_registry"])
    sync_state = _read_yaml(resolved["sync_state"])

    harvest_classes = set(harvest.get("recommendation_classes") or [])
    _check(
        checks,
        failures,
        "rm_intel_002",
        "harvest_recommendation_classes_complete",
        REQUIRED_RECOMMENDATION_CLASSES.issubset(harvest_classes),
        f"harvest_classes={sorted(harvest_classes)}",
    )
    harvest_candidates = harvest.get("candidates") or []
    harvest_names = {str(row.get("name")) for row in harvest_candidates}
    _check(
        checks,
        failures,
        "rm_intel_002",
        "harvest_candidate_coverage",
        REQUIRED_CANDIDATES.issubset(harvest_names),
        f"missing={sorted(REQUIRED_CANDIDATES - harvest_names)}",
    )
    missing_harvest_fields: dict[str, list[str]] = {}
    required_harvest_fields = {
        "name",
        "category",
        "source_url",
        "license",
        "recommendation_class",
        "architecture_compatibility",
        "duplication_risk",
        "privacy_local_first_constraints",
        "architecture_drift_risk",
        "roadmap_linkage",
    }
    for row in harvest_candidates:
        missing = [field for field in required_harvest_fields if row.get(field) in (None, "", [])]
        if missing:
            missing_harvest_fields[str(row.get("name"))] = missing
    _check(
        checks,
        failures,
        "rm_intel_002",
        "harvest_required_fields_present",
        not missing_harvest_fields,
        f"missing={missing_harvest_fields}",
    )
    _check(
        checks,
        failures,
        "rm_intel_002",
        "refresh_delta_uses_harvest_source",
        str((refresh_delta.get("source") or {}).get("harvest")) == FILES["harvest"],
        f"refresh_delta.source.harvest={((refresh_delta.get('source') or {}).get('harvest'))}",
    )

    watchtower_classes = set(watchtower.get("recommendation_classes") or [])
    _check(
        checks,
        failures,
        "rm_intel_001",
        "watchtower_recommendation_classes_complete",
        REQUIRED_RECOMMENDATION_CLASSES.issubset(watchtower_classes),
        f"watchtower_classes={sorted(watchtower_classes)}",
    )
    watchtower_candidates = watchtower.get("candidates") or []
    watchtower_names = {str(row.get("name")) for row in watchtower_candidates}
    _check(
        checks,
        failures,
        "rm_intel_001",
        "watchtower_candidate_projection_from_harvest",
        harvest_names.issubset(watchtower_names),
        f"missing_from_watchtower={sorted(harvest_names - watchtower_names)}",
    )
    missing_linkage_intel: dict[str, list[str]] = {}
    for row in watchtower_candidates:
        links = row.get("roadmap_linkage") or []
        missing = [needed for needed in ("RM-INTEL-001", "RM-INTEL-002") if needed not in links]
        if missing:
            missing_linkage_intel[str(row.get("name"))] = missing
    _check(
        checks,
        failures,
        "rm_intel_001",
        "watchtower_roadmap_linkage_has_intel_ids",
        not missing_linkage_intel,
        f"missing={missing_linkage_intel}",
    )
    _check(
        checks,
        failures,
        "rm_intel_001",
        "watchtower_projection_chain_flag",
        bool(((watchtower_projection.get("integrated_chain") or {}).get("rm_intel_002_to_rm_intel_001"))),
        f"integrated_chain={watchtower_projection.get('integrated_chain')}",
    )

    _check(
        checks,
        failures,
        "rm_dev_005",
        "aider_adapter_boundary_enforced",
        authority.get("adapter_status", {}).get("aider", {}).get("backbone_allowed") is False,
        "aider.backbone_allowed must be false",
    )
    _check(
        checks,
        failures,
        "rm_dev_005",
        "model_profiles_ollama_default",
        str(model_profiles.get("default_backend")) == "ollama",
        f"default_backend={model_profiles.get('default_backend')}",
    )
    _check(
        checks,
        failures,
        "rm_dev_005",
        "dev005_execution_pack_exists",
        "RM-DEV-005 Execution Pack" in resolved["rm_dev_005_pack"].read_text(encoding="utf-8"),
        "RM-DEV-005 execution pack heading missing",
    )

    bounded_required = set(((bounded.get("task_contract") or {}).get("required_fields") or []))
    _check(
        checks,
        failures,
        "rm_dev_003",
        "bounded_required_fields_present",
        REQUIRED_BOUNDED_FIELDS.issubset(bounded_required),
        f"missing={sorted(REQUIRED_BOUNDED_FIELDS - bounded_required)}",
    )
    run_sections = set(((bounded.get("run_artifact_structure") or {}).get("required_sections") or []))
    _check(
        checks,
        failures,
        "rm_dev_003",
        "bounded_run_sections_present",
        {"run_metadata", "bounded_task_contract", "validation_results", "decision", "emitted_artifacts"}.issubset(run_sections),
        f"run_sections={sorted(run_sections)}",
    )
    _check(
        checks,
        failures,
        "rm_dev_003",
        "bounded_run_latest_has_required_sections",
        {"run_metadata", "bounded_task_contract", "planned_changes", "validation_results", "decision", "emitted_artifacts"}.issubset(
            set(bounded_run_latest.keys())
        ),
        f"run_sections={sorted(bounded_run_latest.keys())}",
    )

    qc_categories = set(qc_schema.get("finding_categories") or [])
    _check(
        checks,
        failures,
        "rm_dev_002",
        "qc_categories_complete",
        REQUIRED_QC_CATEGORIES == qc_categories,
        f"qc_categories={sorted(qc_categories)}",
    )
    _check(
        checks,
        failures,
        "rm_dev_002",
        "qc_template_has_category_counts",
        REQUIRED_QC_CATEGORIES.issubset(set((qc_template.get("category_counts") or {}).keys())),
        f"category_counts_keys={sorted((qc_template.get('category_counts') or {}).keys())}",
    )
    _check(
        checks,
        failures,
        "rm_dev_002",
        "qc_template_has_writeback_actions",
        isinstance(qc_template.get("writeback_actions"), list) and len(qc_template["writeback_actions"]) >= 1,
        f"writeback_actions={qc_template.get('writeback_actions')}",
    )
    _check(
        checks,
        failures,
        "rm_dev_002",
        "qc_latest_category_coverage",
        REQUIRED_QC_CATEGORIES.issubset(set((qc_latest.get("category_counts") or {}).keys())),
        f"qc_latest.category_counts={qc_latest.get('category_counts')}",
    )
    _check(
        checks,
        failures,
        "rm_dev_002",
        "qc_latest_links_to_bounded_run",
        bool(((qc_latest.get("integration_refs") or {}).get("bounded_run_artifact"))),
        f"integration_refs={qc_latest.get('integration_refs')}",
    )

    _check(
        checks,
        failures,
        "operational_flows",
        "oss_refresh_delta_summary_present",
        bool(refresh_delta.get("summary")),
        f"summary={refresh_delta.get('summary')}",
    )
    _check(
        checks,
        failures,
        "operational_flows",
        "watchtower_projection_grouped_recommendations_present",
        bool(watchtower_projection.get("grouped_recommendations")),
        f"grouped_recommendations={watchtower_projection.get('grouped_recommendations')}",
    )
    _check(
        checks,
        failures,
        "operational_flows",
        "bounded_run_validation_results_present",
        bool((bounded_run_latest.get("validation_results") or {}).get("command_results")),
        f"validation_results={bounded_run_latest.get('validation_results')}",
    )
    _check(
        checks,
        failures,
        "operational_flows",
        "qc_result_findings_present",
        isinstance(qc_latest.get("findings"), list) and len(qc_latest["findings"]) >= 1,
        f"finding_count={len(qc_latest.get('findings') or [])}",
    )

    qc_pattern_store = _read_yaml(resolved["qc_pattern_store"])
    _check(
        checks,
        failures,
        "orchestration",
        "qc_pattern_store_schema_valid",
        qc_pattern_store.get("schema_version") == "1.0.0" and "failure_classes" in qc_pattern_store,
        f"schema={qc_pattern_store.get('schema_version')}",
    )
    system_run_latest = _read_json(resolved["system_run_latest_artifact"])
    _check(
        checks,
        failures,
        "orchestration",
        "system_run_summary_schema_valid",
        system_run_latest.get("schema_version") == 1
        and "session_id" in system_run_latest
        and "pipeline_stages" in system_run_latest
        and "gate_status" in system_run_latest,
        f"fields={sorted(system_run_latest.keys())}",
    )
    _check(
        checks,
        failures,
        "orchestration",
        "system_run_gate_cleared",
        system_run_latest.get("gate_status", {}).get("gate_cleared") is True,
        f"gate_cleared={system_run_latest.get('gate_status', {}).get('gate_cleared')}",
    )
    _check(
        checks,
        failures,
        "orchestration",
        "system_run_all_stages_passed",
        system_run_latest.get("gate_status", {}).get("all_passed") is True,
        f"all_passed={system_run_latest.get('gate_status', {}).get('all_passed')}",
    )
    _check(
        checks,
        failures,
        "orchestration",
        "system_run_promotion_readiness_valid",
        system_run_latest.get("promotion_readiness", {}).get("system_operational") is True,
        f"promotion_readiness={system_run_latest.get('promotion_readiness')}",
    )

    _check(
        checks,
        failures,
        "integration",
        "intelligence_to_watchtower_flow_present",
        bool(linkage.get("intelligence_to_watchtower_flow")),
        "missing intelligence_to_watchtower_flow",
    )
    _check(
        checks,
        failures,
        "integration",
        "watchtower_to_dev005_flow_present",
        bool(linkage.get("watchtower_and_harvest_to_local_autonomy")),
        "missing watchtower_and_harvest_to_local_autonomy",
    )
    _check(
        checks,
        failures,
        "integration",
        "dev005_to_dev003_flow_present",
        bool(linkage.get("local_autonomy_to_bounded_codegen")),
        "missing local_autonomy_to_bounded_codegen",
    )
    _check(
        checks,
        failures,
        "integration",
        "dev002_to_dev003_qc_flow_present",
        bool(linkage.get("qc_feedback_to_bounded_codegen")),
        "missing qc_feedback_to_bounded_codegen",
    )

    registry_ids = {str(row.get("id")) for row in (registry.get("items") or [])}
    sync_ids = {str(row.get("id")) for row in (sync_state.get("items") or [])}
    required_ids = {"RM-INTEL-002", "RM-DEV-005", "RM-DEV-003", "RM-DEV-002", "RM-INTEL-001"}
    _check(
        checks,
        failures,
        "roadmap_registry_sync",
        "registry_contains_all_integrated_ids",
        required_ids.issubset(registry_ids),
        f"missing={sorted(required_ids - registry_ids)}",
    )
    _check(
        checks,
        failures,
        "roadmap_registry_sync",
        "sync_state_contains_all_integrated_ids",
        required_ids.issubset(sync_ids),
        f"missing={sorted(required_ids - sync_ids)}",
    )

    gate_results = {
        "rm_intel_002_gate": all(row["passed"] for row in checks["rm_intel_002"]),
        "rm_intel_001_gate": all(row["passed"] for row in checks["rm_intel_001"]),
        "rm_dev_005_gate": all(row["passed"] for row in checks["rm_dev_005"]),
        "rm_dev_003_gate": all(row["passed"] for row in checks["rm_dev_003"]),
        "rm_dev_002_gate": all(row["passed"] for row in checks["rm_dev_002"]),
        "operational_flow_gate": all(row["passed"] for row in checks["operational_flows"]),
        "orchestration_gate": all(row["passed"] for row in checks["orchestration"]),
        "integration_gate": all(row["passed"] for row in checks["integration"]),
        "validation_gate": len(failures) == 0,
    }
    payload = {
        "schema_version": 1,
        "package_id": "RM-INTEGRATED-5-ITEM-ADVANCEMENT",
        "generated_at": _iso_now(),
        "validated_files": FILES,
        "checks": checks,
        "gate_results": gate_results,
        "overall_result": "pass" if all(gate_results.values()) else "fail",
        "failure_reasons": failures,
    }
    return _dump(payload)


if __name__ == "__main__":
    raise SystemExit(main())
