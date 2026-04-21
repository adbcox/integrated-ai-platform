"""Seam tests for P2-02-SUBSTRATE-CONFORMANCE-AND-TOOLS-PACK-1."""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))

ARTIFACT_PATH = REPO_ROOT / "artifacts/substrate/phase2_substrate_pack_check.json"
BASELINE_PATH = REPO_ROOT / "governance/phase2_substrate_baseline.v1.yaml"
BASELINE_SPEC = REPO_ROOT / "docs/specs/phase2_substrate_baseline.md"

_NEW_MODULE_PATHS = [
    REPO_ROOT / "framework/read_file_tool_v1.py",
    REPO_ROOT / "framework/publish_artifact_tool_v1.py",
    REPO_ROOT / "framework/run_command_tool_v1.py",
    REPO_ROOT / "framework/run_tests_tool_v1.py",
    REPO_ROOT / "framework/substrate_runtime_v1.py",
    REPO_ROOT / "framework/substrate_conformance_v1.py",
]

_P2_01_MODULES = [
    REPO_ROOT / "framework/session_job_schema_v1.py",
    REPO_ROOT / "framework/tool_registry_v1.py",
    REPO_ROOT / "framework/workspace_controller_v1.py",
    REPO_ROOT / "framework/artifact_bundle_v1.py",
]

_REQUIRED_BASELINE_MODULES = [
    "session_job_schema_v1", "tool_contracts_v1", "tool_registry_v1",
    "workspace_controller_v1", "permission_decision_v1", "artifact_bundle_v1",
    "read_file_tool_v1", "publish_artifact_tool_v1", "run_command_tool_v1",
    "run_tests_tool_v1", "substrate_runtime_v1", "substrate_conformance_v1",
]

_REQUIRED_TOOLS = {"read_file", "publish_artifact", "run_command", "run_tests"}


# ── File existence ────────────────────────────────────────────────────────────

def test_new_modules_exist():
    for p in _NEW_MODULE_PATHS:
        assert p.exists(), f"missing: {p}"


def test_p2_01_modules_still_exist():
    for p in _P2_01_MODULES:
        assert p.exists(), f"P2-01 module missing: {p}"


def test_baseline_yaml_exists():
    assert BASELINE_PATH.exists()


def test_baseline_spec_exists():
    assert BASELINE_SPEC.exists()


# ── read_file_tool_v1 ─────────────────────────────────────────────────────────

def test_read_file_imports():
    from framework.read_file_tool_v1 import ReadFileToolV1, ReadFileResultV1
    assert callable(ReadFileToolV1)
    assert callable(ReadFileResultV1)


def test_read_file_side_effecting_false():
    from framework.read_file_tool_v1 import ReadFileToolV1
    assert ReadFileToolV1.SIDE_EFFECTING is False


def test_read_file_real_file(tmp_path):
    from framework.read_file_tool_v1 import ReadFileToolV1
    f = tmp_path / "test.txt"
    f.write_text("hello\nworld\n")
    result = ReadFileToolV1().run(str(f))
    assert result.status == "success"
    assert "hello" in result.content
    assert result.line_count > 0
    assert result.side_effecting is False


def test_read_file_not_found():
    from framework.read_file_tool_v1 import ReadFileToolV1
    result = ReadFileToolV1().run("/nonexistent/path/file.txt")
    assert result.status == "not_found"
    assert result.content is None


def test_read_file_result_to_dict():
    from framework.read_file_tool_v1 import ReadFileToolV1
    result = ReadFileToolV1().run(str(REPO_ROOT / "framework/read_file_tool_v1.py"))
    d = result.to_dict()
    for k in ("status", "content", "path", "line_count", "truncated", "side_effecting"):
        assert k in d, f"ReadFileResultV1.to_dict() missing: {k}"


# ── publish_artifact_tool_v1 ──────────────────────────────────────────────────

def test_publish_artifact_imports():
    from framework.publish_artifact_tool_v1 import PublishArtifactToolV1, PublishArtifactResultV1
    assert callable(PublishArtifactToolV1)


def test_publish_artifact_side_effecting_true():
    from framework.publish_artifact_tool_v1 import PublishArtifactToolV1
    assert PublishArtifactToolV1.SIDE_EFFECTING is True


def test_publish_artifact_writes_file(tmp_path):
    from framework.publish_artifact_tool_v1 import PublishArtifactToolV1
    dest = tmp_path / "sub" / "artifact.json"
    result = PublishArtifactToolV1().run(str(dest), {"key": "value"})
    assert result.status == "success"
    assert result.bytes_written > 0
    assert dest.exists()
    data = json.loads(dest.read_text())
    assert data["key"] == "value"


def test_publish_artifact_creates_parent_dirs(tmp_path):
    from framework.publish_artifact_tool_v1 import PublishArtifactToolV1
    dest = tmp_path / "a" / "b" / "c" / "out.json"
    result = PublishArtifactToolV1().run(str(dest), {"x": 1})
    assert result.status == "success"
    assert dest.exists()


def test_publish_artifact_result_to_dict(tmp_path):
    from framework.publish_artifact_tool_v1 import PublishArtifactToolV1
    dest = tmp_path / "x.json"
    result = PublishArtifactToolV1().run(str(dest), "plain text")
    d = result.to_dict()
    for k in ("status", "written_path", "bytes_written", "side_effecting"):
        assert k in d


# ── run_command_tool_v1 ───────────────────────────────────────────────────────

def test_run_command_imports():
    from framework.run_command_tool_v1 import RunCommandToolV1, RunCommandResultV1
    assert callable(RunCommandToolV1)


def test_run_command_success():
    from framework.run_command_tool_v1 import RunCommandToolV1
    result = RunCommandToolV1().run([sys.executable, "-c", "print('hello')"])
    assert result.status == "success"
    assert result.exit_code == 0
    assert "hello" in result.stdout
    assert result.duration_ms >= 0


def test_run_command_failure():
    from framework.run_command_tool_v1 import RunCommandToolV1
    result = RunCommandToolV1().run([sys.executable, "-c", "import sys; sys.exit(1)"])
    assert result.status == "failure"
    assert result.exit_code == 1


def test_run_command_result_to_dict():
    from framework.run_command_tool_v1 import RunCommandToolV1
    result = RunCommandToolV1().run([sys.executable, "--version"])
    d = result.to_dict()
    for k in ("status", "command", "exit_code", "stdout", "stderr", "duration_ms"):
        assert k in d


def test_run_command_side_effecting_true():
    from framework.run_command_tool_v1 import RunCommandToolV1
    assert RunCommandToolV1.SIDE_EFFECTING is True


# ── run_tests_tool_v1 ─────────────────────────────────────────────────────────

def test_run_tests_imports():
    from framework.run_tests_tool_v1 import RunTestsToolV1, RunTestsResultV1
    assert callable(RunTestsToolV1)


def test_run_tests_side_effecting_false():
    from framework.run_tests_tool_v1 import RunTestsToolV1
    assert RunTestsToolV1.SIDE_EFFECTING is False


def test_run_tests_result_to_dict():
    from framework.run_tests_tool_v1 import RunTestsResultV1
    r = RunTestsResultV1(
        status="success", test_target="tests/", exit_code=0,
        stdout="1 passed", stderr="", duration_ms=100,
        passed=1, failed=0, errors=0,
    )
    d = r.to_dict()
    for k in ("status", "test_target", "exit_code", "stdout", "stderr", "duration_ms",
               "passed", "failed", "errors", "side_effecting"):
        assert k in d


def test_run_tests_parses_pytest_output():
    from framework.run_tests_tool_v1 import _parse_pytest_summary
    out = "3 passed, 1 failed, 2 errors in 1.23s"
    counts = _parse_pytest_summary(out)
    assert counts["passed"] == 3
    assert counts["failed"] == 1
    assert counts["errors"] == 2


# ── substrate_runtime_v1 ─────────────────────────────────────────────────────

def test_substrate_runtime_imports():
    from framework.substrate_runtime_v1 import SubstrateRuntimeV1
    assert callable(SubstrateRuntimeV1)


def test_substrate_runtime_assembles():
    from framework.workspace_controller_v1 import WorkspaceDescriptorV1
    from framework.substrate_runtime_v1 import SubstrateRuntimeV1
    d = WorkspaceDescriptorV1(str(REPO_ROOT), "/tmp/scratch", "artifacts/substrate", True)
    rt = SubstrateRuntimeV1(d)
    assert rt.is_ready()


def test_substrate_runtime_has_all_tools():
    from framework.workspace_controller_v1 import WorkspaceDescriptorV1
    from framework.substrate_runtime_v1 import SubstrateRuntimeV1
    d = WorkspaceDescriptorV1(str(REPO_ROOT), "/tmp/scratch", "artifacts/substrate", True)
    rt = SubstrateRuntimeV1(d)
    for name in _REQUIRED_TOOLS:
        tool = rt.get_tool(name)
        assert tool is not None, f"runtime missing tool: {name}"


def test_substrate_runtime_permission_read_only_is_allow():
    from framework.workspace_controller_v1 import WorkspaceDescriptorV1
    from framework.substrate_runtime_v1 import SubstrateRuntimeV1
    from framework.permission_decision_v1 import Decision
    d = WorkspaceDescriptorV1(str(REPO_ROOT), "/tmp/scratch", "artifacts/substrate", True)
    rt = SubstrateRuntimeV1(d)
    p = rt.decide_permission("read_file", "framework/x.py")
    assert p.decision == Decision.ALLOW


def test_substrate_runtime_permission_side_effecting_is_ask():
    from framework.workspace_controller_v1 import WorkspaceDescriptorV1
    from framework.substrate_runtime_v1 import SubstrateRuntimeV1
    from framework.permission_decision_v1 import Decision
    d = WorkspaceDescriptorV1(str(REPO_ROOT), "/tmp/scratch", "artifacts/substrate", True)
    rt = SubstrateRuntimeV1(d)
    p = rt.decide_permission("run_command", "make check")
    assert p.decision == Decision.ASK


def test_substrate_runtime_summary():
    from framework.workspace_controller_v1 import WorkspaceDescriptorV1
    from framework.substrate_runtime_v1 import SubstrateRuntimeV1
    d = WorkspaceDescriptorV1(str(REPO_ROOT), "/tmp/scratch", "artifacts/substrate", True)
    rt = SubstrateRuntimeV1(d)
    s = rt.summary()
    assert s["is_ready"] is True
    assert s["workspace_valid"] is True
    assert set(s["tool_instances"]) >= _REQUIRED_TOOLS


# ── substrate_conformance_v1 ──────────────────────────────────────────────────

def test_substrate_conformance_imports():
    from framework.substrate_conformance_v1 import SubstrateConformanceCheckerV1, ConformanceResultV1
    assert callable(SubstrateConformanceCheckerV1)


def test_substrate_conformance_passes():
    from framework.substrate_conformance_v1 import SubstrateConformanceCheckerV1
    result = SubstrateConformanceCheckerV1().run()
    assert result.all_passed, f"conformance failed: {result.errors}"


def test_conformance_result_fields():
    from framework.substrate_conformance_v1 import SubstrateConformanceCheckerV1
    result = SubstrateConformanceCheckerV1().run()
    d = result.to_dict()
    for k in ("tool_registry_complete", "workspace_validates", "artifact_bundle_assembles",
               "substrate_artifact_emitted", "modules_loadable", "all_passed", "errors"):
        assert k in d


def test_conformance_all_flags_true():
    from framework.substrate_conformance_v1 import SubstrateConformanceCheckerV1
    result = SubstrateConformanceCheckerV1().run()
    assert result.tool_registry_complete is True
    assert result.workspace_validates is True
    assert result.artifact_bundle_assembles is True
    assert result.substrate_artifact_emitted is True
    assert result.modules_loadable is True


# ── phase2_substrate_baseline YAML ───────────────────────────────────────────

def test_baseline_yaml_loads():
    try:
        import yaml  # type: ignore
        data = yaml.safe_load(BASELINE_PATH.read_text())
    except ImportError:
        import re
        data = {}
        for line in BASELINE_PATH.read_text().splitlines():
            m = re.match(r'^([a-zA-Z_][a-zA-Z0-9_]*)\s*:', line)
            if m:
                data[m.group(1)] = True
    assert isinstance(data, dict) and len(data) > 0


def test_baseline_phase_id_is_phase_2():
    import yaml  # type: ignore
    data = yaml.safe_load(BASELINE_PATH.read_text())
    assert data["phase_id"] == "phase_2"


def test_baseline_required_modules_complete():
    import yaml  # type: ignore
    data = yaml.safe_load(BASELINE_PATH.read_text())
    rm = data["required_modules"]
    for name in _REQUIRED_BASELINE_MODULES:
        assert name in rm, f"baseline required_modules missing: {name}"


def test_baseline_required_tools_complete():
    import yaml  # type: ignore
    data = yaml.safe_load(BASELINE_PATH.read_text())
    rt = data["required_tools"]
    for name in _REQUIRED_TOOLS:
        assert name in rt, f"baseline required_tools missing: {name}"


def test_baseline_conformance_requirements_present():
    import yaml  # type: ignore
    data = yaml.safe_load(BASELINE_PATH.read_text())
    cr = data["conformance_requirements"]
    for req in ["tool_registry_complete", "workspace_validates",
                "artifact_bundle_assembles", "substrate_artifact_emitted"]:
        assert req in cr


def test_baseline_completion_gate_exists():
    import yaml  # type: ignore
    data = yaml.safe_load(BASELINE_PATH.read_text())
    assert "completion_gate" in data
    cg = data["completion_gate"]
    assert isinstance(cg, dict)


def test_baseline_remaining_blockers_exists():
    import yaml  # type: ignore
    data = yaml.safe_load(BASELINE_PATH.read_text())
    assert "remaining_blockers" in data


# ── spec ─────────────────────────────────────────────────────────────────────

def test_baseline_spec_sections():
    text = BASELINE_SPEC.read_text()
    for heading in (
        "## Purpose",
        "## Phase Identity",
        "## Required Modules",
        "## Required Tools",
        "## Conformance Requirements",
        "## Completion Gate",
        "## Remaining Blockers",
        "## Relationship to Governance",
    ):
        assert heading in text, f"baseline spec missing: {heading}"


def test_baseline_spec_references_yaml():
    assert "phase2_substrate_baseline.v1.yaml" in BASELINE_SPEC.read_text()


# ── End-to-end substrate flow ─────────────────────────────────────────────────

def test_end_to_end_substrate_flow(tmp_path):
    """Read a file → decide permission → run a command → publish an artifact."""
    from framework.workspace_controller_v1 import WorkspaceDescriptorV1
    from framework.substrate_runtime_v1 import SubstrateRuntimeV1
    from framework.permission_decision_v1 import Decision

    desc = WorkspaceDescriptorV1(str(REPO_ROOT), str(tmp_path / "scratch"),
                                  str(tmp_path / "artifacts"), True)
    rt = SubstrateRuntimeV1(desc)
    assert rt.is_ready()

    # Step 1: read a file
    read_tool = rt.get_tool("read_file")
    r_result = read_tool.run(str(REPO_ROOT / "framework/read_file_tool_v1.py"))
    assert r_result.status == "success"

    # Step 2: permission check on side-effecting tool
    perm = rt.decide_permission("publish_artifact", str(tmp_path / "artifacts"))
    assert perm.decision == Decision.ASK   # side-effecting = ask

    # Step 3: run a command
    cmd_tool = rt.get_tool("run_command")
    c_result = cmd_tool.run([sys.executable, "-c", "print('substrate ok')"])
    assert c_result.status == "success"
    assert "substrate ok" in c_result.stdout

    # Step 4: publish an artifact
    pub_tool = rt.get_tool("publish_artifact")
    dest = tmp_path / "artifacts" / "e2e_test.json"
    p_result = pub_tool.run(str(dest), {"flow": "complete", "status": "success"})
    assert p_result.status == "success"
    assert dest.exists()
    loaded = json.loads(dest.read_text())
    assert loaded["flow"] == "complete"


# ── Artifact and runner ───────────────────────────────────────────────────────

def test_emit_artifact(tmp_path):
    artifact = {
        "substrate_pack": "phase2_substrate_pack_v1",
        "generated_at": "2026-04-21T00:00:00+00:00",
        "required_modules_loaded": True,
        "required_tools_loaded": sorted(_REQUIRED_TOOLS),
        "runtime_assembled": True,
        "conformance_passed": True,
        "baseline_loaded": True,
        "all_checks_passed": True,
        "component_summary": [],
    }
    out = tmp_path / "phase2_substrate_pack_check.json"
    out.write_text(json.dumps(artifact, indent=2))
    loaded = json.loads(out.read_text())
    assert loaded["substrate_pack"] == "phase2_substrate_pack_v1"
    assert loaded["all_checks_passed"] is True


def test_runner_script_executes():
    result = subprocess.run(
        [sys.executable, str(REPO_ROOT / "bin" / "run_phase2_substrate_pack_check.py")],
        capture_output=True, text=True, cwd=str(REPO_ROOT),
    )
    assert result.returncode == 0, f"runner failed:\n{result.stderr}"
    assert ARTIFACT_PATH.exists()
    data = json.loads(ARTIFACT_PATH.read_text())
    assert data["substrate_pack"] == "phase2_substrate_pack_v1"
    assert data["all_checks_passed"] is True
    assert data["conformance_passed"] is True
    assert len(data["component_summary"]) == 7
