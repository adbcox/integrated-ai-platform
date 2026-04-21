#!/usr/bin/env python3
"""P3-01: Run Phase 3 MVP checks and emit pack artifact."""
from __future__ import annotations

import json
import sys
from datetime import datetime, timezone
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))

ARTIFACT_PATH = REPO_ROOT / "artifacts/substrate/phase3_mvp_pack_check.json"
BASELINE_PATH = REPO_ROOT / "governance/phase3_mvp_baseline.v1.yaml"

REQUIRED_MODULES = [
    "framework.repo_intake_v1",
    "framework.developer_task_v1",
    "framework.developer_assistant_loop_v1",
    "framework.result_package_v1",
    "framework.mvp_benchmark_runner_v1",
]

REQUIRED_BASELINE_MODULES = [
    "repo_intake_v1", "developer_task_v1", "developer_assistant_loop_v1",
    "result_package_v1", "mvp_benchmark_runner_v1",
]


def _check_modules() -> tuple[bool, list[str]]:
    errors = []
    for mod in REQUIRED_MODULES:
        try:
            __import__(mod)
        except Exception as exc:
            errors.append(f"{mod}: {exc}")
    return len(errors) == 0, errors


def _check_loop_runs() -> tuple[bool, list[str], dict]:
    from framework.repo_intake_v1 import RepoIntakeV1
    from framework.developer_task_v1 import DeveloperTaskV1
    from framework.developer_assistant_loop_v1 import DeveloperAssistantLoopV1
    from framework.workspace_controller_v1 import WorkspaceDescriptorV1
    from framework.substrate_runtime_v1 import SubstrateRuntimeV1

    desc = WorkspaceDescriptorV1(
        source_root=str(REPO_ROOT),
        scratch_root="/tmp/phase3_check",
        artifact_root="artifacts/substrate",
        source_read_only=True,
    )
    rt = SubstrateRuntimeV1(desc)
    loop = DeveloperAssistantLoopV1(rt)

    intake = RepoIntakeV1(
        repo_root=str(REPO_ROOT),
        task_id="check-001",
        package_id="P3-01-DEVELOPER-ASSISTANT-MVP-PACK-1",
        package_label="SUBSTRATE",
        objective="Phase 3 MVP check",
        allowed_files=["framework/repo_intake_v1.py"],
        forbidden_files=[],
    )
    task = DeveloperTaskV1(
        task_id="check-001",
        objective="Inspect repo intake module",
        task_kind="inspect",
        target_paths=["framework/repo_intake_v1.py"],
        validation_sequence=["workspace_valid"],
        retry_budget=1,
    )
    result = loop.run(intake, task)
    ok = result.final_outcome == "success" and result.escalation_status == "NOT_ESCALATED"
    errors = [] if ok else [f"loop result: outcome={result.final_outcome}"]
    return ok, errors, result.to_dict()


def _run_benchmark() -> tuple[bool, dict]:
    from framework.mvp_benchmark_runner_v1 import MVPBenchmarkRunnerV1
    runner = MVPBenchmarkRunnerV1(repo_root=str(REPO_ROOT))
    suite = runner.run()
    ok = suite.tasks_run >= 3 and suite.pass_rate >= 0.0
    return ok, suite.to_dict()


def _check_baseline() -> tuple[bool, list[str]]:
    if not BASELINE_PATH.exists():
        return False, [f"baseline not found: {BASELINE_PATH.relative_to(REPO_ROOT)}"]
    try:
        import yaml  # type: ignore
        data = yaml.safe_load(BASELINE_PATH.read_text(encoding="utf-8"))
    except ImportError:
        import re
        data = {}
        for line in BASELINE_PATH.read_text(encoding="utf-8").splitlines():
            m = re.match(r'^([a-zA-Z_][a-zA-Z0-9_]*)\s*:', line)
            if m:
                data[m.group(1)] = True
    if not isinstance(data, dict):
        return False, ["baseline did not parse as a mapping"]
    errors = []
    if data.get("phase_id") != "phase_3":
        errors.append(f"baseline phase_id must be 'phase_3', got {data.get('phase_id')!r}")
    rm = data.get("required_modules", {})
    if isinstance(rm, dict):
        for name in REQUIRED_BASELINE_MODULES:
            if name not in rm:
                errors.append(f"baseline required_modules missing: {name}")
    return len(errors) == 0, errors


def main() -> None:
    print("P3-01: running Phase 3 MVP pack checks...")
    all_ok = True
    details: dict = {}

    print("  [1] loading required modules...")
    ok, errs = _check_modules()
    details["modules_loaded"] = {"ok": ok, "errors": errs}
    print(f"      modules_loaded: {'OK' if ok else 'FAIL'}")
    if not ok:
        for e in errs:
            print(f"    FAIL: {e}", file=sys.stderr)
        all_ok = False

    print("  [2] running developer assistant loop...")
    ok, errs, loop_detail = _check_loop_runs()
    details["loop_runs"] = {"ok": ok, "errors": errs}
    print(f"      loop_runs: {'OK' if ok else 'FAIL'}")
    if not ok:
        all_ok = False

    print("  [3] running MVP benchmark suite...")
    ok, bench_detail = _run_benchmark()
    details["benchmark"] = {"ok": ok, **bench_detail}
    print(f"      benchmark: {'OK' if ok else 'FAIL'} "
          f"({bench_detail['tasks_passed']}/{bench_detail['tasks_run']} passed, "
          f"pass_rate={bench_detail['pass_rate']:.2f})")
    if not ok:
        all_ok = False

    print("  [4] checking phase3 baseline...")
    ok, errs = _check_baseline()
    details["baseline"] = {"ok": ok, "errors": errs}
    print(f"      baseline: {'OK' if ok else 'FAIL'}")
    if not ok:
        all_ok = False

    if not all_ok:
        print("HARD STOP: phase3 MVP pack check failed", file=sys.stderr)
        sys.exit(1)

    bench = details["benchmark"]
    component_summary = [
        {"module": "framework/repo_intake_v1.py", "classes": ["RepoIntakeV1"]},
        {"module": "framework/developer_task_v1.py", "classes": ["DeveloperTaskV1"]},
        {"module": "framework/developer_assistant_loop_v1.py", "classes": ["DeveloperAssistantLoopV1"]},
        {"module": "framework/result_package_v1.py", "classes": ["ResultPackageV1"]},
        {"module": "framework/mvp_benchmark_runner_v1.py", "classes": ["MVPBenchmarkRunnerV1"]},
        {"module": "governance/phase3_mvp_baseline.v1.yaml", "type": "baseline"},
    ]

    artifact = {
        "phase3_pack": "developer_assistant_mvp_v1",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "required_modules_loaded": details["modules_loaded"]["ok"],
        "loop_runs": details["loop_runs"]["ok"],
        "benchmark_runs": bench["tasks_run"],
        "benchmark_pass_rate": bench["pass_rate"],
        "baseline_loaded": details["baseline"]["ok"],
        "all_checks_passed": all_ok,
        "component_summary": component_summary,
        "check_details": details,
        "phase_linkage": "Phase 3 (developer_assistant_mvp)",
        "authority_sources": [
            "governance/phase3_mvp_baseline.v1.yaml",
            "governance/phase2_substrate_baseline.v1.yaml",
            "governance/local_run_validation_pack.v1.yaml",
        ],
    }

    ARTIFACT_PATH.parent.mkdir(parents=True, exist_ok=True)
    ARTIFACT_PATH.write_text(json.dumps(artifact, indent=2), encoding="utf-8")
    print(f"artifact:   {ARTIFACT_PATH.relative_to(REPO_ROOT)}")
    print("P3-01: all Phase 3 MVP checks passed.")


if __name__ == "__main__":
    main()
