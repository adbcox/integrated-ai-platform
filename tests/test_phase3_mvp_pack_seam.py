"""Seam tests for P3-01-DEVELOPER-ASSISTANT-MVP-PACK-1."""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))

ARTIFACT_PATH = REPO_ROOT / "artifacts/substrate/phase3_mvp_pack_check.json"
BASELINE_PATH = REPO_ROOT / "governance/phase3_mvp_baseline.v1.yaml"
BASELINE_SPEC = REPO_ROOT / "docs/specs/phase3_mvp_baseline.md"

_NEW_MODULE_PATHS = [
    REPO_ROOT / "framework/repo_intake_v1.py",
    REPO_ROOT / "framework/developer_task_v1.py",
    REPO_ROOT / "framework/developer_assistant_loop_v1.py",
    REPO_ROOT / "framework/result_package_v1.py",
    REPO_ROOT / "framework/mvp_benchmark_runner_v1.py",
]

_REQUIRED_SESSION_FIELDS = [
    "repo_root", "task_id", "package_id", "package_label",
    "objective", "allowed_files", "forbidden_files",
]

_REQUIRED_TASK_FIELDS = [
    "task_id", "objective", "task_kind", "target_paths",
    "validation_sequence", "retry_budget",
]

_REQUIRED_RESULT_PKG_FIELDS = [
    "intake", "task", "tools_used", "validations_run",
    "artifacts_produced", "final_outcome", "escalation_status",
]

_REQUIRED_BASELINE_MODULES = [
    "repo_intake_v1", "developer_task_v1", "developer_assistant_loop_v1",
    "result_package_v1", "mvp_benchmark_runner_v1",
]

_REQUIRED_BASELINE_CAPABILITIES = [
    "repo_intake", "bounded_task_shape", "substrate_backed_loop",
    "result_packaging", "benchmark_execution",
]

_REQUIRED_COMPLETION_REQS = [
    "bounded_loop_runs", "artifact_complete_outputs",
    "benchmark_pack_executes", "explicit_escalation_accounting",
]


def _make_runtime():
    from framework.workspace_controller_v1 import WorkspaceDescriptorV1
    from framework.substrate_runtime_v1 import SubstrateRuntimeV1
    desc = WorkspaceDescriptorV1(str(REPO_ROOT), "/tmp/p3_test_scratch", "artifacts/substrate", True)
    return SubstrateRuntimeV1(desc)


def _make_intake(task_id="t-001", target="framework/repo_intake_v1.py"):
    from framework.repo_intake_v1 import RepoIntakeV1
    return RepoIntakeV1(
        repo_root=str(REPO_ROOT),
        task_id=task_id,
        package_id="P3-01-TEST",
        package_label="SUBSTRATE",
        objective="test",
        allowed_files=[target],
        forbidden_files=[],
    )


def _make_task(task_id="t-001", target="framework/repo_intake_v1.py"):
    from framework.developer_task_v1 import DeveloperTaskV1
    return DeveloperTaskV1(
        task_id=task_id,
        objective="inspect module",
        task_kind="inspect",
        target_paths=[target],
        validation_sequence=["workspace_valid"],
        retry_budget=1,
    )


# ── File existence ────────────────────────────────────────────────────────────

def test_new_modules_exist():
    for p in _NEW_MODULE_PATHS:
        assert p.exists(), f"missing: {p}"


def test_baseline_yaml_exists():
    assert BASELINE_PATH.exists()


def test_baseline_spec_exists():
    assert BASELINE_SPEC.exists()


# ── repo_intake_v1 ────────────────────────────────────────────────────────────

def test_repo_intake_imports():
    from framework.repo_intake_v1 import RepoIntakeV1
    assert callable(RepoIntakeV1)


def test_repo_intake_creation():
    intake = _make_intake()
    assert intake.repo_root == str(REPO_ROOT)
    assert intake.package_label == "SUBSTRATE"


def test_repo_intake_to_dict():
    intake = _make_intake()
    d = intake.to_dict()
    for f in _REQUIRED_SESSION_FIELDS:
        assert f in d, f"RepoIntakeV1.to_dict() missing: {f}"


def test_repo_intake_allowed_files():
    from framework.repo_intake_v1 import RepoIntakeV1
    intake = RepoIntakeV1(
        repo_root="/r", task_id="t", package_id="P", package_label="SUBSTRATE",
        objective="o", allowed_files=["a.py", "b.py"], forbidden_files=["c.py"],
    )
    assert "a.py" in intake.allowed_files
    assert "c.py" in intake.forbidden_files


# ── developer_task_v1 ─────────────────────────────────────────────────────────

def test_developer_task_imports():
    from framework.developer_task_v1 import DeveloperTaskV1
    assert callable(DeveloperTaskV1)


def test_developer_task_creation():
    task = _make_task()
    assert task.task_kind == "inspect"
    assert task.retry_budget == 1


def test_developer_task_to_dict():
    task = _make_task()
    d = task.to_dict()
    for f in _REQUIRED_TASK_FIELDS:
        assert f in d, f"DeveloperTaskV1.to_dict() missing: {f}"


def test_developer_task_kinds():
    from framework.developer_task_v1 import DeveloperTaskV1
    for kind in ("inspect", "patch", "validate", "benchmark"):
        t = DeveloperTaskV1(
            task_id="x", objective="o", task_kind=kind,
            target_paths=[], validation_sequence=[], retry_budget=1,
        )
        assert t.task_kind == kind


# ── developer_assistant_loop_v1 ───────────────────────────────────────────────

def test_loop_imports():
    from framework.developer_assistant_loop_v1 import DeveloperAssistantLoopV1, LoopResultV1
    assert callable(DeveloperAssistantLoopV1)
    assert callable(LoopResultV1)


def test_loop_runs_and_returns_structured_output():
    from framework.developer_assistant_loop_v1 import DeveloperAssistantLoopV1
    rt = _make_runtime()
    loop = DeveloperAssistantLoopV1(rt)
    intake = _make_intake()
    task = _make_task()
    result = loop.run(intake, task)
    assert result.final_outcome in ("success", "failure", "escalated")
    assert result.escalation_status == "NOT_ESCALATED"
    assert isinstance(result.inspected_paths, list)
    assert isinstance(result.validations_run, list)
    assert isinstance(result.validation_results, dict)


def test_loop_inspects_existing_file():
    from framework.developer_assistant_loop_v1 import DeveloperAssistantLoopV1
    rt = _make_runtime()
    loop = DeveloperAssistantLoopV1(rt)
    intake = _make_intake(target="framework/repo_intake_v1.py")
    task = _make_task(target="framework/repo_intake_v1.py")
    result = loop.run(intake, task)
    assert "framework/repo_intake_v1.py" in result.inspected_paths
    assert result.validation_results.get("inspect:framework/repo_intake_v1.py") == "success"


def test_loop_result_to_dict():
    from framework.developer_assistant_loop_v1 import DeveloperAssistantLoopV1
    rt = _make_runtime()
    loop = DeveloperAssistantLoopV1(rt)
    result = loop.run(_make_intake(), _make_task())
    d = result.to_dict()
    for k in ("task_id", "inspected_paths", "validations_run", "validation_results",
               "final_outcome", "escalation_status", "artifacts_produced"):
        assert k in d


def test_loop_produces_artifact(tmp_path):
    from framework.developer_assistant_loop_v1 import DeveloperAssistantLoopV1
    rt = _make_runtime()
    loop = DeveloperAssistantLoopV1(rt)
    dest = str(tmp_path / "loop_result.json")
    result = loop.run(_make_intake(), _make_task(), artifact_dest=dest)
    assert dest in result.artifacts_produced
    assert Path(dest).exists()
    data = json.loads(Path(dest).read_text())
    assert "task_id" in data


def test_loop_success_outcome():
    from framework.developer_assistant_loop_v1 import DeveloperAssistantLoopV1
    rt = _make_runtime()
    loop = DeveloperAssistantLoopV1(rt)
    result = loop.run(_make_intake(), _make_task())
    assert result.final_outcome == "success"


# ── result_package_v1 ─────────────────────────────────────────────────────────

def test_result_package_imports():
    from framework.result_package_v1 import ResultPackageV1
    assert callable(ResultPackageV1)


def test_result_package_assembles():
    from framework.result_package_v1 import ResultPackageV1
    intake = _make_intake()
    task = _make_task()
    pkg = ResultPackageV1(
        intake=intake,
        task=task,
        tools_used=["read_file"],
        validations_run=["workspace_valid"],
        artifacts_produced=[],
        final_outcome="success",
        escalation_status="NOT_ESCALATED",
        validation_results={"workspace_valid": "pass"},
    )
    assert pkg.final_outcome == "success"
    assert pkg.escalation_status == "NOT_ESCALATED"


def test_result_package_to_dict():
    from framework.result_package_v1 import ResultPackageV1
    pkg = ResultPackageV1(
        intake=_make_intake(), task=_make_task(),
        tools_used=["read_file"], validations_run=[], artifacts_produced=[],
        final_outcome="success", escalation_status="NOT_ESCALATED",
    )
    d = pkg.to_dict()
    for k in _REQUIRED_RESULT_PKG_FIELDS:
        assert k in d, f"ResultPackageV1.to_dict() missing: {k}"


def test_result_package_contains_intake_fields():
    from framework.result_package_v1 import ResultPackageV1
    pkg = ResultPackageV1(
        intake=_make_intake(), task=_make_task(),
        tools_used=[], validations_run=[], artifacts_produced=[],
        final_outcome="success", escalation_status="NOT_ESCALATED",
    )
    d = pkg.to_dict()
    assert d["intake"]["package_id"] == "P3-01-TEST"
    assert d["task"]["task_kind"] == "inspect"


# ── mvp_benchmark_runner_v1 ───────────────────────────────────────────────────

def test_benchmark_runner_imports():
    from framework.mvp_benchmark_runner_v1 import MVPBenchmarkRunnerV1, BenchmarkSuiteResultV1
    assert callable(MVPBenchmarkRunnerV1)


def test_benchmark_runner_executes():
    from framework.mvp_benchmark_runner_v1 import MVPBenchmarkRunnerV1
    runner = MVPBenchmarkRunnerV1(repo_root=str(REPO_ROOT))
    suite = runner.run()
    assert suite.tasks_run >= 3
    assert 0.0 <= suite.pass_rate <= 1.0
    assert isinstance(suite.failure_modes, list)


def test_benchmark_runner_case_results():
    from framework.mvp_benchmark_runner_v1 import MVPBenchmarkRunnerV1
    runner = MVPBenchmarkRunnerV1(repo_root=str(REPO_ROOT))
    suite = runner.run()
    assert len(suite.case_results) == suite.tasks_run
    for c in suite.case_results:
        assert c.task_id
        assert c.task_kind in ("inspect", "validate", "patch", "benchmark")
        assert isinstance(c.passed, bool)


def test_benchmark_suite_to_dict():
    from framework.mvp_benchmark_runner_v1 import MVPBenchmarkRunnerV1
    runner = MVPBenchmarkRunnerV1(repo_root=str(REPO_ROOT))
    d = runner.run().to_dict()
    for k in ("tasks_run", "tasks_passed", "pass_rate", "failure_modes", "case_results"):
        assert k in d


def test_benchmark_pass_rate_is_float():
    from framework.mvp_benchmark_runner_v1 import MVPBenchmarkRunnerV1
    suite = MVPBenchmarkRunnerV1(repo_root=str(REPO_ROOT)).run()
    assert isinstance(suite.pass_rate, float)


def test_benchmark_custom_cases():
    from framework.mvp_benchmark_runner_v1 import MVPBenchmarkRunnerV1
    from framework.developer_task_v1 import DeveloperTaskV1
    custom = [
        DeveloperTaskV1("c1", "inspect x", "inspect",
                        ["framework/repo_intake_v1.py"], ["workspace_valid"], 1),
        DeveloperTaskV1("c2", "inspect y", "inspect",
                        ["framework/developer_task_v1.py"], ["workspace_valid"], 1),
        DeveloperTaskV1("c3", "inspect z", "inspect",
                        ["governance/phase3_mvp_baseline.v1.yaml"], ["workspace_valid"], 1),
    ]
    runner = MVPBenchmarkRunnerV1(repo_root=str(REPO_ROOT))
    suite = runner.run(cases=custom)
    assert suite.tasks_run == 3


# ── Phase 3 baseline YAML ─────────────────────────────────────────────────────

def test_baseline_loads():
    import yaml  # type: ignore
    data = yaml.safe_load(BASELINE_PATH.read_text())
    assert isinstance(data, dict) and len(data) > 0


def test_baseline_phase_id_is_phase_3():
    import yaml  # type: ignore
    data = yaml.safe_load(BASELINE_PATH.read_text())
    assert data["phase_id"] == "phase_3"


def test_baseline_required_modules_complete():
    import yaml  # type: ignore
    data = yaml.safe_load(BASELINE_PATH.read_text())
    rm = data["required_modules"]
    for name in _REQUIRED_BASELINE_MODULES:
        assert name in rm, f"baseline required_modules missing: {name}"


def test_baseline_required_capabilities_complete():
    import yaml  # type: ignore
    data = yaml.safe_load(BASELINE_PATH.read_text())
    rc = data["required_capabilities"]
    for cap in _REQUIRED_BASELINE_CAPABILITIES:
        assert cap in rc, f"baseline required_capabilities missing: {cap}"


def test_baseline_completion_requirements():
    import yaml  # type: ignore
    data = yaml.safe_load(BASELINE_PATH.read_text())
    cr = data["completion_requirements"]
    for req in _REQUIRED_COMPLETION_REQS:
        assert req in cr, f"baseline completion_requirements missing: {req}"


def test_baseline_completion_gate_exists():
    import yaml  # type: ignore
    data = yaml.safe_load(BASELINE_PATH.read_text())
    assert "completion_gate" in data
    assert isinstance(data["completion_gate"], dict)


def test_baseline_remaining_blockers_exists():
    import yaml  # type: ignore
    data = yaml.safe_load(BASELINE_PATH.read_text())
    assert "remaining_blockers" in data


# ── Spec content ──────────────────────────────────────────────────────────────

def test_baseline_spec_sections():
    text = BASELINE_SPEC.read_text()
    for heading in (
        "## Purpose",
        "## Phase Identity",
        "## Required Modules",
        "## Required Capabilities",
        "## Developer Assistant Loop",
        "## Benchmark Runner",
        "## Completion Requirements",
        "## Completion Gate",
        "## Remaining Blockers",
        "## Relationship to Governance",
    ):
        assert heading in text, f"spec missing: {heading}"


def test_spec_references_baseline_yaml():
    assert "phase3_mvp_baseline.v1.yaml" in BASELINE_SPEC.read_text()


# ── Integration: loop → result package ───────────────────────────────────────

def test_loop_to_result_package_integration():
    from framework.developer_assistant_loop_v1 import DeveloperAssistantLoopV1
    from framework.result_package_v1 import ResultPackageV1
    rt = _make_runtime()
    loop = DeveloperAssistantLoopV1(rt)
    intake = _make_intake()
    task = _make_task()
    loop_result = loop.run(intake, task)
    pkg = ResultPackageV1(
        intake=intake,
        task=task,
        tools_used=["read_file"],
        validations_run=loop_result.validations_run,
        artifacts_produced=loop_result.artifacts_produced,
        final_outcome=loop_result.final_outcome,
        escalation_status=loop_result.escalation_status,
        validation_results=loop_result.validation_results,
    )
    d = pkg.to_dict()
    assert d["final_outcome"] == "success"
    assert d["escalation_status"] == "NOT_ESCALATED"
    assert d["task"]["task_id"] == task.task_id


# ── Artifact and runner ───────────────────────────────────────────────────────

def test_emit_artifact(tmp_path):
    artifact = {
        "phase3_pack": "developer_assistant_mvp_v1",
        "generated_at": "2026-04-21T00:00:00+00:00",
        "required_modules_loaded": True,
        "loop_runs": True,
        "benchmark_runs": 4,
        "benchmark_pass_rate": 1.0,
        "baseline_loaded": True,
        "all_checks_passed": True,
        "component_summary": [],
    }
    out = tmp_path / "phase3_mvp_pack_check.json"
    out.write_text(json.dumps(artifact, indent=2))
    loaded = json.loads(out.read_text())
    assert loaded["phase3_pack"] == "developer_assistant_mvp_v1"
    assert loaded["all_checks_passed"] is True


def test_runner_script_executes():
    result = subprocess.run(
        [sys.executable, str(REPO_ROOT / "bin" / "run_phase3_mvp_pack_check.py")],
        capture_output=True, text=True, cwd=str(REPO_ROOT),
    )
    assert result.returncode == 0, f"runner failed:\n{result.stderr}"
    assert ARTIFACT_PATH.exists()
    data = json.loads(ARTIFACT_PATH.read_text())
    assert data["phase3_pack"] == "developer_assistant_mvp_v1"
    assert data["all_checks_passed"] is True
    assert data["benchmark_runs"] >= 3
    assert isinstance(data["benchmark_pass_rate"], float)
    assert len(data["component_summary"]) == 6
