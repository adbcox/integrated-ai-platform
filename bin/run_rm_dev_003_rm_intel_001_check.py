#!/usr/bin/env python3
"""Validate integrated RM-DEV-003 + RM-INTEL-001 baseline and emit evidence."""
from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import yaml

REPO_ROOT = Path(__file__).resolve().parents[1]

FILES = {
    "roadmap_master": "docs/roadmap/ROADMAP_MASTER.md",
    "high_priority_guide": "docs/roadmap/HIGH_PRIORITY_IMPLEMENTATION_GUIDE.md",
    "execution_pack_index": "docs/roadmap/EXECUTION_PACK_INDEX.md",
    "rm_dev_003_pack": "docs/roadmap/RM-DEV-003_EXECUTION_PACK.md",
    "rm_intel_001_pack": "docs/roadmap/RM-INTEL-001_EXECUTION_PACK.md",
    "rm_dev_003_item": "docs/roadmap/items/RM-DEV-003.yaml",
    "rm_intel_001_item": "docs/roadmap/items/RM-INTEL-001.yaml",
    "contract": "governance/bounded_autonomous_codegen_contract.v1.yaml",
    "watchtower": "governance/oss_watchtower_candidates.v1.yaml",
    "linkage": "governance/rm_dev_003_rm_intel_001_linkage.v1.yaml",
    "bounded_run_example": "artifacts/bounded_autonomy/runs/rm_dev_003_baseline_example.json",
}
OUT_ARTIFACT = REPO_ROOT / "artifacts/governance/rm_dev_003_rm_intel_001_baseline_validation.json"

REQUIRED_TASK_FIELDS = [
    "objective",
    "allowed_files",
    "forbidden_files",
    "expected_file_posture",
    "validation_sequence",
    "rollback_rule",
    "artifact_outputs",
    "promotion_decision",
]

REQUIRED_CANDIDATE_FIELDS = [
    "name",
    "category",
    "source_url",
    "license",
    "maintenance_signal",
    "integration_role",
    "roadmap_linkage",
    "recommendation_class",
    "removal_fallback_posture",
    "notes",
]

REQUIRED_CANDIDATE_NAMES = [
    "Ollama",
    "Aider",
    "MCP",
    "OpenHands SDK",
    "Qdrant",
    "gVisor",
    "SWE-bench",
    "Continue",
]

REQUIRED_REC_CLASSES = {"adopt-now", "evaluate", "watch", "reject"}
REQUIRED_RUN_SECTIONS = [
    "run_metadata",
    "bounded_task_contract",
    "planned_changes",
    "validation_results",
    "decision",
    "emitted_artifacts",
]


def _iso_now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def _load_yaml(path: Path) -> dict[str, Any]:
    return yaml.safe_load(path.read_text(encoding="utf-8")) or {}


def _check(name: str, passed: bool, detail: str, checks: list[dict[str, Any]], failures: list[str]) -> None:
    checks.append({"check": name, "passed": passed, "detail": detail})
    if not passed:
        failures.append(f"{name}: {detail}")


def main() -> int:
    failures: list[str] = []
    checks: dict[str, list[dict[str, Any]]] = {
        "file_presence": [],
        "rm_dev_003_contract": [],
        "rm_dev_003_run_artifact": [],
        "rm_intel_001_watchtower": [],
        "integrated_linkage": [],
        "roadmap_docs": [],
    }

    resolved_paths = {name: REPO_ROOT / rel for name, rel in FILES.items()}
    for name, path in resolved_paths.items():
        _check(
            f"{name}_exists",
            path.exists(),
            str(path.relative_to(REPO_ROOT)),
            checks["file_presence"],
            failures,
        )

    if failures:
        payload = {
            "schema_version": 1,
            "package_id": "RM-DEV-003-RM-INTEL-001-INTEGRATED-BASELINE",
            "generated_at": _iso_now(),
            "validated_files": FILES,
            "checks": checks,
            "gate_results": {
                "rm_dev_003_gate": False,
                "rm_intel_001_gate": False,
                "integrated_linkage_gate": False,
                "validation_gate": False,
            },
            "overall_result": "fail",
            "failure_reasons": failures,
        }
        OUT_ARTIFACT.parent.mkdir(parents=True, exist_ok=True)
        OUT_ARTIFACT.write_text(json.dumps(payload, indent=2), encoding="utf-8")
        print(f"artifact={OUT_ARTIFACT}")
        return 1

    contract = _load_yaml(resolved_paths["contract"])
    watchtower = _load_yaml(resolved_paths["watchtower"])
    linkage = _load_yaml(resolved_paths["linkage"])

    required_fields = ((contract.get("task_contract") or {}).get("required_fields") or [])
    _check(
        "task_contract_required_fields_complete",
        all(field in required_fields for field in REQUIRED_TASK_FIELDS),
        f"required_fields={required_fields}",
        checks["rm_dev_003_contract"],
        failures,
    )

    run_sections = ((contract.get("run_artifact_structure") or {}).get("required_sections") or [])
    _check(
        "run_artifact_structure_present",
        all(section in run_sections for section in REQUIRED_RUN_SECTIONS),
        f"required_sections={run_sections}",
        checks["rm_dev_003_contract"],
        failures,
    )

    run_example = json.loads(resolved_paths["bounded_run_example"].read_text(encoding="utf-8"))
    _check(
        "run_example_has_required_sections",
        all(section in run_example for section in REQUIRED_RUN_SECTIONS),
        f"run_example_sections={sorted(run_example.keys())}",
        checks["rm_dev_003_run_artifact"],
        failures,
    )
    run_contract = run_example.get("bounded_task_contract") or {}
    _check(
        "run_example_has_required_task_fields",
        all(field in run_contract for field in REQUIRED_TASK_FIELDS),
        f"run_contract_fields={sorted(run_contract.keys())}",
        checks["rm_dev_003_run_artifact"],
        failures,
    )
    _check(
        "run_example_promotion_decision_valid",
        (run_contract.get("promotion_decision") in {"promote", "hold", "escalate"})
        and ((run_example.get("decision") or {}).get("promotion_decision") in {"promote", "hold", "escalate"}),
        f"bounded_task_contract.promotion_decision={run_contract.get('promotion_decision')}, decision.promotion_decision={(run_example.get('decision') or {}).get('promotion_decision')}",
        checks["rm_dev_003_run_artifact"],
        failures,
    )

    candidates = watchtower.get("candidates") or []
    candidate_names = [candidate.get("name") for candidate in candidates]
    _check(
        "candidate_shortlist_complete",
        all(name in candidate_names for name in REQUIRED_CANDIDATE_NAMES),
        f"candidate_names={candidate_names}",
        checks["rm_intel_001_watchtower"],
        failures,
    )

    rec_classes = set(watchtower.get("recommendation_classes") or [])
    _check(
        "recommendation_classes_complete",
        REQUIRED_REC_CLASSES.issubset(rec_classes),
        f"recommendation_classes={sorted(rec_classes)}",
        checks["rm_intel_001_watchtower"],
        failures,
    )

    missing_fields_by_candidate: dict[str, list[str]] = {}
    for candidate in candidates:
        name = str(candidate.get("name"))
        missing = [field for field in REQUIRED_CANDIDATE_FIELDS if field not in candidate or candidate.get(field) in (None, "", [])]
        if missing:
            missing_fields_by_candidate[name] = missing
    _check(
        "candidate_required_fields_complete",
        not missing_fields_by_candidate,
        f"missing_fields={missing_fields_by_candidate}",
        checks["rm_intel_001_watchtower"],
        failures,
    )

    needs = linkage.get("rm_dev_003_needs") or []
    _check(
        "linkage_has_needs",
        len(needs) >= 4,
        f"need_count={len(needs)}",
        checks["integrated_linkage"],
        failures,
    )

    unknown_candidates: dict[str, list[str]] = {}
    known_names = set(candidate_names)
    for need in needs:
        need_id = str(need.get("need_id"))
        mapped = need.get("directly_supported_candidates") or []
        unknown = [name for name in mapped if name not in known_names]
        if unknown:
            unknown_candidates[need_id] = unknown
    _check(
        "linkage_references_known_candidates",
        not unknown_candidates,
        f"unknown_candidates={unknown_candidates}",
        checks["integrated_linkage"],
        failures,
    )

    _check(
        "linkage_maps_rm_dev_003_to_rm_intel_001",
        any("Aider" in (need.get("directly_supported_candidates") or []) for need in needs)
        and any("MCP" in (need.get("directly_supported_candidates") or []) for need in needs)
        and any("Ollama" in (need.get("directly_supported_candidates") or []) for need in needs),
        "needs must map core RM-DEV-003 requirements to tracked OSS candidates",
        checks["integrated_linkage"],
        failures,
    )
    candidate_map = {str(candidate.get("name")): candidate for candidate in candidates}
    unmapped_rm_dev003: dict[str, list[str]] = {}
    for need in needs:
        need_id = str(need.get("need_id"))
        mapped = need.get("directly_supported_candidates") or []
        missing_rm_dev003 = [
            name
            for name in mapped
            if "RM-DEV-003" not in (candidate_map.get(name, {}).get("roadmap_linkage") or [])
        ]
        if missing_rm_dev003:
            unmapped_rm_dev003[need_id] = missing_rm_dev003
    _check(
        "linkage_candidates_include_rm_dev_003_roadmap_linkage",
        not unmapped_rm_dev003,
        f"missing_rm_dev003_linkage={unmapped_rm_dev003}",
        checks["integrated_linkage"],
        failures,
    )

    roadmap_text_checks = {
        "rm_dev_003_pack_has_required_field_list": "required bounded task fields" in resolved_paths["rm_dev_003_pack"].read_text(encoding="utf-8").lower(),
        "rm_intel_001_pack_has_required_field_list": "required candidate fields" in resolved_paths["rm_intel_001_pack"].read_text(encoding="utf-8").lower(),
        "execution_pack_index_links_both": "RM-DEV-003_EXECUTION_PACK.md" in resolved_paths["execution_pack_index"].read_text(encoding="utf-8")
        and "RM-INTEL-001_EXECUTION_PACK.md" in resolved_paths["execution_pack_index"].read_text(encoding="utf-8"),
    }
    for key, passed in roadmap_text_checks.items():
        _check(key, passed, key, checks["roadmap_docs"], failures)

    gate_results = {
        "rm_dev_003_gate": all(check["passed"] for check in checks["rm_dev_003_contract"])
        and all(check["passed"] for check in checks["rm_dev_003_run_artifact"]),
        "rm_intel_001_gate": all(check["passed"] for check in checks["rm_intel_001_watchtower"]),
        "integrated_linkage_gate": all(check["passed"] for check in checks["integrated_linkage"]),
    }
    gate_results["validation_gate"] = len(failures) == 0

    payload = {
        "schema_version": 1,
        "package_id": "RM-DEV-003-RM-INTEL-001-INTEGRATED-BASELINE",
        "generated_at": _iso_now(),
        "validated_files": FILES,
        "checks": checks,
        "gate_results": gate_results,
        "overall_result": "pass" if all(gate_results.values()) else "fail",
        "failure_reasons": failures,
    }
    OUT_ARTIFACT.parent.mkdir(parents=True, exist_ok=True)
    OUT_ARTIFACT.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    print(f"artifact={OUT_ARTIFACT}")
    return 0 if payload["overall_result"] == "pass" else 1


if __name__ == "__main__":
    raise SystemExit(main())
