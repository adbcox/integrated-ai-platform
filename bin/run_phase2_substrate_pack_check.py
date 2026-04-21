#!/usr/bin/env python3
"""P2-02: Run Phase 2 substrate conformance checks and emit pack artifact."""
from __future__ import annotations

import json
import sys
from datetime import datetime, timezone
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))

ARTIFACT_PATH = REPO_ROOT / "artifacts/substrate/phase2_substrate_pack_check.json"

REQUIRED_MODULES = [
    "framework.session_job_schema_v1",
    "framework.tool_contracts_v1",
    "framework.tool_registry_v1",
    "framework.workspace_controller_v1",
    "framework.permission_decision_v1",
    "framework.artifact_bundle_v1",
    "framework.read_file_tool_v1",
    "framework.publish_artifact_tool_v1",
    "framework.run_command_tool_v1",
    "framework.run_tests_tool_v1",
    "framework.substrate_runtime_v1",
    "framework.substrate_conformance_v1",
]

REQUIRED_TOOL_NAMES = {"read_file", "run_command", "run_tests", "publish_artifact"}

BASELINE_PATH = REPO_ROOT / "governance/phase2_substrate_baseline.v1.yaml"
BASELINE_REQUIRED_CONTRACTS = [
    "session_job_schema_v1", "tool_contracts_v1", "tool_registry_v1",
    "workspace_controller_v1", "permission_decision_v1", "artifact_bundle_v1",
    "read_file_tool_v1", "publish_artifact_tool_v1", "run_command_tool_v1",
    "run_tests_tool_v1", "substrate_runtime_v1", "substrate_conformance_v1",
]


def _check_modules_loadable() -> tuple[bool, list[str]]:
    errors = []
    for mod in REQUIRED_MODULES:
        try:
            __import__(mod)
        except Exception as exc:
            errors.append(f"{mod}: {exc}")
    return len(errors) == 0, errors


def _check_tool_registry() -> tuple[bool, list[str]]:
    from framework.tool_registry_v1 import ToolRegistryV1
    r = ToolRegistryV1()
    registered = set(r.list_tool_names())
    missing = REQUIRED_TOOL_NAMES - registered
    if missing:
        return False, [f"tool registry missing: {missing}"]
    return True, []


def _check_runtime_assembles() -> tuple[bool, list[str]]:
    from framework.workspace_controller_v1 import WorkspaceDescriptorV1
    from framework.substrate_runtime_v1 import SubstrateRuntimeV1
    d = WorkspaceDescriptorV1(
        source_root=str(REPO_ROOT),
        scratch_root="/tmp/phase2_scratch",
        artifact_root="artifacts/substrate",
        source_read_only=True,
    )
    rt = SubstrateRuntimeV1(d)
    if not rt.is_ready():
        return False, ["SubstrateRuntimeV1.is_ready() returned False"]
    return True, []


def _check_conformance() -> tuple[bool, list[str], dict]:
    from framework.substrate_conformance_v1 import SubstrateConformanceCheckerV1
    result = SubstrateConformanceCheckerV1().run()
    return result.all_passed, result.errors, result.to_dict()


def _check_baseline() -> tuple[bool, list[str]]:
    if not BASELINE_PATH.exists():
        return False, [f"baseline not found: {BASELINE_PATH.relative_to(REPO_ROOT)}"]
    try:
        import yaml  # type: ignore
        baseline = yaml.safe_load(BASELINE_PATH.read_text(encoding="utf-8"))
    except ImportError:
        import re
        keys: dict = {}
        for line in BASELINE_PATH.read_text(encoding="utf-8").splitlines():
            if line.startswith("#") or not line.strip():
                continue
            m = re.match(r'^([a-zA-Z_][a-zA-Z0-9_]*)\s*:', line)
            if m:
                keys[m.group(1)] = True
        baseline = keys

    errors = []
    if not isinstance(baseline, dict):
        return False, ["baseline did not parse as a mapping"]
    if baseline.get("phase_id") != "phase_2":
        errors.append(f"baseline phase_id must be 'phase_2', got {baseline.get('phase_id')!r}")
    rm = baseline.get("required_modules", {})
    if isinstance(rm, dict):
        for name in BASELINE_REQUIRED_CONTRACTS:
            if name not in rm:
                errors.append(f"baseline required_modules missing: {name}")
    return len(errors) == 0, errors


def main() -> None:
    print("P2-02: running Phase 2 substrate pack checks...")
    all_ok = True
    checks: dict = {}

    print("  [1] loading required modules...")
    ok, errs = _check_modules_loadable()
    checks["modules_loadable"] = {"ok": ok, "errors": errs}
    print(f"      modules_loadable: {'OK' if ok else 'FAIL'}")
    if not ok:
        for e in errs:
            print(f"    FAIL: {e}", file=sys.stderr)
        all_ok = False

    print("  [2] checking tool registry...")
    ok, errs = _check_tool_registry()
    checks["tool_registry"] = {"ok": ok, "errors": errs}
    print(f"      tool_registry: {'OK' if ok else 'FAIL'}")
    if not ok:
        all_ok = False

    print("  [3] assembling substrate runtime...")
    ok, errs = _check_runtime_assembles()
    checks["runtime_assembled"] = {"ok": ok, "errors": errs}
    print(f"      runtime_assembled: {'OK' if ok else 'FAIL'}")
    if not ok:
        all_ok = False

    print("  [4] running conformance checker...")
    ok, errs, conf_detail = _check_conformance()
    checks["conformance"] = {"ok": ok, "errors": errs, "detail": conf_detail}
    print(f"      conformance: {'OK' if ok else 'FAIL'}")
    if not ok:
        for e in errs:
            print(f"    FAIL: {e}", file=sys.stderr)
        all_ok = False

    print("  [5] checking phase2 baseline...")
    ok, errs = _check_baseline()
    checks["baseline"] = {"ok": ok, "errors": errs}
    print(f"      baseline: {'OK' if ok else 'FAIL'}")
    if not ok:
        all_ok = False

    if not all_ok:
        print("HARD STOP: phase2 substrate pack check failed", file=sys.stderr)
        sys.exit(1)

    component_summary = [
        {"module": "framework/read_file_tool_v1.py", "classes": ["ReadFileToolV1"]},
        {"module": "framework/publish_artifact_tool_v1.py", "classes": ["PublishArtifactToolV1"]},
        {"module": "framework/run_command_tool_v1.py", "classes": ["RunCommandToolV1"]},
        {"module": "framework/run_tests_tool_v1.py", "classes": ["RunTestsToolV1"]},
        {"module": "framework/substrate_runtime_v1.py", "classes": ["SubstrateRuntimeV1"]},
        {"module": "framework/substrate_conformance_v1.py", "classes": ["SubstrateConformanceCheckerV1"]},
        {"module": "governance/phase2_substrate_baseline.v1.yaml", "type": "baseline"},
    ]

    artifact = {
        "substrate_pack": "phase2_substrate_pack_v1",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "required_modules_loaded": checks["modules_loadable"]["ok"],
        "required_tools_loaded": sorted(REQUIRED_TOOL_NAMES),
        "runtime_assembled": checks["runtime_assembled"]["ok"],
        "conformance_passed": checks["conformance"]["ok"],
        "baseline_loaded": checks["baseline"]["ok"],
        "all_checks_passed": all_ok,
        "component_summary": component_summary,
        "check_details": checks,
        "phase_linkage": "Phase 2 (minimum_substrate_implementation)",
        "authority_sources": [
            "governance/phase2_substrate_baseline.v1.yaml",
            "governance/phase1_hardening_baseline.v1.yaml",
            "governance/local_run_validation_pack.v1.yaml",
            "ADR-0003", "ADR-0006",
        ],
    }

    ARTIFACT_PATH.parent.mkdir(parents=True, exist_ok=True)
    ARTIFACT_PATH.write_text(json.dumps(artifact, indent=2), encoding="utf-8")
    print(f"artifact:   {ARTIFACT_PATH.relative_to(REPO_ROOT)}")
    print("P2-02: all Phase 2 substrate checks passed.")


if __name__ == "__main__":
    main()
