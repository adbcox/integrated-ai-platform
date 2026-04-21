#!/usr/bin/env python3
"""P1-06: Validate all Phase 1 hardening contracts and emit pack validation artifact."""
from __future__ import annotations

import json
import sys
from datetime import datetime, timezone
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent

ARTIFACT_PATH = REPO_ROOT / "artifacts/governance/phase1_hardening_pack_validation.json"

GROUNDING_INPUTS = [
    REPO_ROOT / "governance/workspace_contract.v1.yaml",
    REPO_ROOT / "governance/inference_gateway_contract.v1.yaml",
    REPO_ROOT / "governance/wrapped_command_contract.v1.yaml",
    REPO_ROOT / "governance/model_profiles.v1.yaml",
    REPO_ROOT / "governance/definition_of_done.v1.yaml",
    REPO_ROOT / "governance/autonomy_scorecard.v1.yaml",
    REPO_ROOT / "governance/cmdb_lite_registry.v1.yaml",
    REPO_ROOT / "docs/specs/workspace_contract.md",
    REPO_ROOT / "docs/specs/inference_gateway_contract.md",
    REPO_ROOT / "docs/specs/wrapped_command_contract.md",
    REPO_ROOT / "artifacts/governance/core_adr_index.json",
]

CONTRACTS = {
    "artifact_root_contract": {
        "path": REPO_ROOT / "governance/artifact_root_contract.v1.yaml",
        "spec": REPO_ROOT / "docs/specs/artifact_root_contract.md",
        "required_sections": [
            "version", "artifact_root", "separation_rules", "write_policy",
            "retention_policy", "artifact_bundle_rules", "exceptions",
        ],
    },
    "telemetry_normalization_contract": {
        "path": REPO_ROOT / "governance/telemetry_normalization_contract.v1.yaml",
        "spec": REPO_ROOT / "docs/specs/telemetry_normalization_contract.md",
        "required_sections": [
            "version", "telemetry_identity", "required_fields", "normalized_units",
            "event_shapes", "scoring_linkage", "exceptions",
        ],
    },
    "local_run_validation_pack": {
        "path": REPO_ROOT / "governance/local_run_validation_pack.v1.yaml",
        "spec": REPO_ROOT / "docs/specs/local_run_validation_pack.md",
        "required_sections": [
            "version", "validation_sequence", "required_checks", "artifact_requirements",
            "failure_handling", "package_class_rules", "exceptions",
        ],
    },
    "phase1_hardening_baseline": {
        "path": REPO_ROOT / "governance/phase1_hardening_baseline.v1.yaml",
        "spec": REPO_ROOT / "docs/specs/phase1_hardening_baseline.md",
        "required_sections": [
            "version", "phase_id", "objective", "required_contracts",
            "completion_requirements", "blockers", "notes",
        ],
    },
}

REQUIRED_BASELINE_CONTRACTS = [
    "model_profiles",
    "inference_gateway_contract",
    "workspace_contract",
    "wrapped_command_contract",
    "artifact_root_contract",
    "telemetry_normalization_contract",
    "local_run_validation_pack",
]

REQUIRED_TELEMETRY_FIELDS = [
    "session_id", "package_id", "package_label", "selected_profile",
    "selected_backend", "prompt_hash", "response_hash", "latency_ms",
    "retry_count", "escalation_status", "validations_run", "validation_results",
    "artifacts_produced",
]

REQUIRED_VALIDATION_STEPS = [
    "grounding_check", "import_check", "package_runner",
    "emitted_artifact_parse", "package_seam_tests", "make_check",
]

REQUIRED_FAILURE_HANDLING_KEYS = [
    "stop_on_failed_gate", "no_accept_without_validation", "slice_only_rollback",
]

REQUIRED_PACKAGE_CLASS_KEYS = ["local_first", "substrate", "escalation"]


def _load_yaml(path: Path):
    try:
        import yaml  # type: ignore
        return yaml.safe_load(path.read_text(encoding="utf-8")), None
    except ImportError:
        pass
    return _minimal_yaml_keys(path.read_text(encoding="utf-8")), None


def _minimal_yaml_keys(text: str) -> dict:
    import re
    keys: dict = {}
    for line in text.splitlines():
        if line.startswith("#") or not line.strip():
            continue
        m = re.match(r'^([a-zA-Z_][a-zA-Z0-9_]*)\s*:', line)
        if m:
            keys[m.group(1)] = True
    return keys


def _bool_or_value(obj) -> bool | None:
    if isinstance(obj, bool):
        return obj
    if isinstance(obj, dict):
        return obj.get("value")
    return None


def _verify_grounding() -> bool:
    all_ok = True
    for p in GROUNDING_INPUTS:
        ok = p.exists() and p.stat().st_size > 50
        print(f"  grounding [{'OK' if ok else 'FAIL'}]: {p.relative_to(REPO_ROOT)}")
        if not ok:
            all_ok = False
    return all_ok


def _check_contract(name: str, meta: dict) -> tuple[bool, list[str], dict]:
    errors: list[str] = []
    summary: dict = {"name": name, "path": str(meta["path"].relative_to(REPO_ROOT))}

    if not meta["path"].exists():
        errors.append(f"{name}: contract file missing: {meta['path'].relative_to(REPO_ROOT)}")
        summary["loaded"] = False
        return False, errors, summary

    if not meta["spec"].exists():
        errors.append(f"{name}: spec file missing: {meta['spec'].relative_to(REPO_ROOT)}")

    contract, _ = _load_yaml(meta["path"])
    if not isinstance(contract, dict):
        errors.append(f"{name}: contract did not load as a mapping")
        summary["loaded"] = False
        return False, errors, summary

    summary["loaded"] = True
    missing = [s for s in meta["required_sections"] if s not in contract]
    if missing:
        errors.append(f"{name}: missing sections: {missing}")
    summary["sections_present"] = len(missing) == 0
    summary["sections_checked"] = meta["required_sections"]

    return len(errors) == 0, errors, summary


def _check_artifact_root(contract: dict, errors: list[str]) -> None:
    sep = contract.get("separation_rules", {})
    if isinstance(sep, dict):
        rrw = _bool_or_value(sep.get("repo_relative_writes_forbidden"))
        if rrw is not True:
            errors.append("artifact_root_contract: repo_relative_writes_forbidden must be true")
        arw = _bool_or_value(sep.get("arbitrary_repo_writes_forbidden"))
        if arw is not True:
            errors.append("artifact_root_contract: arbitrary_repo_writes_forbidden must be true")


def _check_telemetry(contract: dict, errors: list[str]) -> None:
    rf = contract.get("required_fields", {})
    if isinstance(rf, dict):
        for f in REQUIRED_TELEMETRY_FIELDS:
            if f not in rf:
                errors.append(f"telemetry_normalization_contract: required_fields missing: {f}")
    sl = contract.get("scoring_linkage", {})
    if not isinstance(sl, dict) or len(sl) == 0:
        errors.append("telemetry_normalization_contract: scoring_linkage must be a non-empty mapping")


def _check_validation_pack(contract: dict, errors: list[str]) -> None:
    vs = contract.get("validation_sequence", {})
    if isinstance(vs, dict):
        steps = vs.get("steps", [])
        step_names = [s.get("name") for s in steps if isinstance(s, dict)]
        for req in REQUIRED_VALIDATION_STEPS:
            if req not in step_names:
                errors.append(f"local_run_validation_pack: validation_sequence missing step: {req}")

    fh = contract.get("failure_handling", {})
    if isinstance(fh, dict):
        for k in REQUIRED_FAILURE_HANDLING_KEYS:
            if k not in fh:
                errors.append(f"local_run_validation_pack: failure_handling missing: {k}")

    pc = contract.get("package_class_rules", {})
    if isinstance(pc, dict):
        for k in REQUIRED_PACKAGE_CLASS_KEYS:
            if k not in pc:
                errors.append(f"local_run_validation_pack: package_class_rules missing: {k}")


def _check_baseline(contract: dict, errors: list[str]) -> None:
    phase_id = contract.get("phase_id")
    if phase_id != "phase_1":
        errors.append(f"phase1_hardening_baseline: phase_id must be 'phase_1', got {phase_id!r}")

    rc = contract.get("required_contracts", {})
    if not isinstance(rc, dict):
        errors.append("phase1_hardening_baseline: required_contracts must be a mapping")
        return
    for c in REQUIRED_BASELINE_CONTRACTS:
        if c not in rc:
            errors.append(f"phase1_hardening_baseline: required_contracts missing: {c}")

    cr = contract.get("completion_requirements", {})
    if isinstance(cr, dict):
        for req in ["reproducible_local_runs", "complete_artifacts",
                    "no_manual_environment_repair", "explicit_escalation_accounting"]:
            if req not in cr:
                errors.append(f"phase1_hardening_baseline: completion_requirements missing: {req}")


def main() -> None:
    print("P1-06: verifying grounding inputs...")
    if not _verify_grounding():
        print("HARD STOP: grounding inputs missing", file=sys.stderr)
        sys.exit(1)

    print("Loading and checking all 4 Phase 1 hardening contracts...")
    all_ok = True
    all_errors: list[str] = []
    contract_summaries: list[dict] = []
    loaded_contracts: dict = {}

    for name, meta in CONTRACTS.items():
        ok, errors, summary = _check_contract(name, meta)
        print(f"  [{name}]: {'OK' if ok else 'FAIL'} — {summary.get('path')}")
        if errors:
            for e in errors:
                print(f"    FAIL: {e}", file=sys.stderr)
        all_ok = all_ok and ok
        all_errors.extend(errors)
        contract_summaries.append(summary)
        if summary.get("loaded"):
            c, _ = _load_yaml(meta["path"])
            loaded_contracts[name] = c

    if not all_ok:
        print("HARD STOP: contract section check failed", file=sys.stderr)
        sys.exit(1)

    print("Checking contract-specific content...")
    content_errors: list[str] = []

    if "artifact_root_contract" in loaded_contracts:
        _check_artifact_root(loaded_contracts["artifact_root_contract"], content_errors)

    if "telemetry_normalization_contract" in loaded_contracts:
        _check_telemetry(loaded_contracts["telemetry_normalization_contract"], content_errors)

    if "local_run_validation_pack" in loaded_contracts:
        _check_validation_pack(loaded_contracts["local_run_validation_pack"], content_errors)

    if "phase1_hardening_baseline" in loaded_contracts:
        _check_baseline(loaded_contracts["phase1_hardening_baseline"], content_errors)

    if content_errors:
        for e in content_errors:
            print(f"  FAIL: {e}", file=sys.stderr)
        print("HARD STOP: content check failed", file=sys.stderr)
        sys.exit(1)

    print("  all contract content checks passed")

    artifact = {
        "artifact_id": "P1-06-PHASE1-HARDENING-PACK-VALIDATION-1",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "contracts_checked": list(CONTRACTS.keys()),
        "contracts_loaded": True,
        "contract_section_summary": contract_summaries,
        "baseline_links_checked": REQUIRED_BASELINE_CONTRACTS,
        "baseline_links_present": True,
        "telemetry_required_fields_checked": REQUIRED_TELEMETRY_FIELDS,
        "telemetry_required_fields_present": True,
        "validation_steps_checked": REQUIRED_VALIDATION_STEPS,
        "validation_steps_present": True,
        "content_errors": [],
        "phase_linkage": "Phase 1 (runtime_contract_foundation)",
        "authority_sources": [
            "ADR-0003",
            "ADR-0006",
            "ADR-0007",
            "governance/definition_of_done.v1.yaml",
            "governance/autonomy_scorecard.v1.yaml",
            "governance/execution_control_package.schema.json",
        ],
    }

    ARTIFACT_PATH.parent.mkdir(parents=True, exist_ok=True)
    ARTIFACT_PATH.write_text(json.dumps(artifact, indent=2), encoding="utf-8")
    print(f"artifact:   {ARTIFACT_PATH.relative_to(REPO_ROOT)}")
    print("P1-06: all checks passed.")


if __name__ == "__main__":
    main()
