"""Seam tests for P2-01-MINIMUM-SUBSTRATE-IMPLEMENTATION-PACK-1."""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))

ARTIFACT_PATH = REPO_ROOT / "artifacts/substrate/minimum_substrate_check.json"

_MODULE_PATHS = [
    REPO_ROOT / "framework/session_job_schema_v1.py",
    REPO_ROOT / "framework/tool_contracts_v1.py",
    REPO_ROOT / "framework/tool_registry_v1.py",
    REPO_ROOT / "framework/workspace_controller_v1.py",
    REPO_ROOT / "framework/permission_decision_v1.py",
    REPO_ROOT / "framework/artifact_bundle_v1.py",
]

_REQUIRED_SESSION_FIELDS = [
    "session_id", "package_id", "package_label", "objective",
    "allowed_files", "forbidden_files", "selected_profile", "selected_backend",
    "workspace_root", "artifact_root", "escalation_status", "final_outcome",
]

_REQUIRED_JOB_FIELDS = [
    "job_id", "package_id", "package_label", "objective",
    "allowed_files", "forbidden_files", "selected_profile", "selected_backend",
    "workspace_root", "artifact_root", "escalation_status", "final_outcome",
]

_REQUIRED_TOOL_NAMES = {"read_file", "run_command", "run_tests", "publish_artifact"}


# ── Module existence ──────────────────────────────────────────────────────────

def test_all_substrate_modules_exist():
    for p in _MODULE_PATHS:
        assert p.exists(), f"substrate module missing: {p}"


# ── session_job_schema_v1 ─────────────────────────────────────────────────────

def test_session_record_import():
    from framework.session_job_schema_v1 import SessionRecord, JobRecord
    assert callable(SessionRecord)
    assert callable(JobRecord)


def test_session_record_creation():
    from framework.session_job_schema_v1 import SessionRecord
    s = SessionRecord(
        session_id="s-001",
        package_id="P2-01-TEST",
        package_label="SUBSTRATE",
        objective="test",
        allowed_files=["a.py"],
        forbidden_files=["b.py"],
        selected_profile=None,
        selected_backend="substrate",
        workspace_root="/repo",
        artifact_root="artifacts",
        escalation_status="NOT_ESCALATED",
    )
    assert s.session_id == "s-001"
    assert s.package_label == "SUBSTRATE"


def test_session_record_to_dict():
    from framework.session_job_schema_v1 import SessionRecord
    s = SessionRecord(
        session_id="s-001",
        package_id="P2-01-TEST",
        package_label="SUBSTRATE",
        objective="test",
        allowed_files=[],
        forbidden_files=[],
        selected_profile=None,
        selected_backend="substrate",
        workspace_root="/repo",
        artifact_root="artifacts",
        escalation_status="NOT_ESCALATED",
    )
    d = s.to_dict()
    for f in _REQUIRED_SESSION_FIELDS:
        assert f in d, f"SessionRecord.to_dict() missing field: {f}"


def test_job_record_creation():
    from framework.session_job_schema_v1 import JobRecord
    j = JobRecord(
        job_id="j-001",
        package_id="P2-01-TEST",
        package_label="SUBSTRATE",
        objective="test",
        allowed_files=[],
        forbidden_files=[],
        selected_profile=None,
        selected_backend="substrate",
        workspace_root="/repo",
        artifact_root="artifacts",
        escalation_status="NOT_ESCALATED",
        session_id="s-001",
    )
    assert j.job_id == "j-001"
    assert j.session_id == "s-001"


def test_job_record_to_dict():
    from framework.session_job_schema_v1 import JobRecord
    j = JobRecord(
        job_id="j-001",
        package_id="P2-01-TEST",
        package_label="SUBSTRATE",
        objective="test",
        allowed_files=[],
        forbidden_files=[],
        selected_profile=None,
        selected_backend="substrate",
        workspace_root="/repo",
        artifact_root="artifacts",
        escalation_status="NOT_ESCALATED",
    )
    d = j.to_dict()
    for f in _REQUIRED_JOB_FIELDS:
        assert f in d, f"JobRecord.to_dict() missing field: {f}"


def test_job_record_has_validations_and_artifacts():
    from framework.session_job_schema_v1 import JobRecord
    j = JobRecord(
        job_id="j-002",
        package_id="P2-01-TEST",
        package_label="SUBSTRATE",
        objective="test",
        allowed_files=[],
        forbidden_files=[],
        selected_profile=None,
        selected_backend="substrate",
        workspace_root="/repo",
        artifact_root="artifacts",
        escalation_status="NOT_ESCALATED",
        validations_run=["make_check"],
        validation_results={"make_check": "pass"},
        artifacts_produced=["artifacts/substrate/x.json"],
    )
    assert "make_check" in j.validations_run
    assert j.validation_results["make_check"] == "pass"


# ── tool_contracts_v1 ─────────────────────────────────────────────────────────

def test_tool_contracts_import():
    from framework.tool_contracts_v1 import ToolContractV1, ALL_CONTRACTS
    assert isinstance(ALL_CONTRACTS, list)
    assert len(ALL_CONTRACTS) == 4


def test_all_tool_contracts_have_required_fields():
    from framework.tool_contracts_v1 import ALL_CONTRACTS
    for c in ALL_CONTRACTS:
        assert c.tool_name in _REQUIRED_TOOL_NAMES
        assert isinstance(c.action_fields, list) and len(c.action_fields) > 0
        assert isinstance(c.observation_fields, list) and len(c.observation_fields) > 0
        assert isinstance(c.side_effecting, bool)


def test_read_file_is_not_side_effecting():
    from framework.tool_contracts_v1 import READ_FILE
    assert READ_FILE.side_effecting is False


def test_run_command_is_side_effecting():
    from framework.tool_contracts_v1 import RUN_COMMAND
    assert RUN_COMMAND.side_effecting is True


def test_publish_artifact_is_side_effecting():
    from framework.tool_contracts_v1 import PUBLISH_ARTIFACT
    assert PUBLISH_ARTIFACT.side_effecting is True


def test_run_tests_observation_includes_status():
    from framework.tool_contracts_v1 import RUN_TESTS
    assert "status" in RUN_TESTS.observation_fields


# ── tool_registry_v1 ─────────────────────────────────────────────────────────

def test_tool_registry_import():
    from framework.tool_registry_v1 import ToolRegistryV1
    assert callable(ToolRegistryV1)


def test_tool_registry_contains_required_tools():
    from framework.tool_registry_v1 import ToolRegistryV1
    r = ToolRegistryV1()
    assert set(r.list_tool_names()) == _REQUIRED_TOOL_NAMES


def test_tool_registry_get_contract():
    from framework.tool_registry_v1 import ToolRegistryV1
    r = ToolRegistryV1()
    for name in _REQUIRED_TOOL_NAMES:
        c = r.get_contract(name)
        assert c is not None
        assert c.tool_name == name


def test_tool_registry_get_unknown_returns_none():
    from framework.tool_registry_v1 import ToolRegistryV1
    r = ToolRegistryV1()
    assert r.get_contract("nonexistent_tool") is None


def test_tool_registry_register_new_tool():
    from framework.tool_registry_v1 import ToolRegistryV1
    from framework.tool_contracts_v1 import ToolContractV1
    r = ToolRegistryV1()
    custom = ToolContractV1(
        tool_name="custom_tool",
        action_fields=["param"],
        observation_fields=["result"],
        side_effecting=False,
    )
    r.register(custom)
    assert "custom_tool" in r.list_tool_names()
    assert r.get_contract("custom_tool") is custom


# ── workspace_controller_v1 ───────────────────────────────────────────────────

def test_workspace_controller_import():
    from framework.workspace_controller_v1 import WorkspaceDescriptorV1, WorkspaceControllerV1
    assert callable(WorkspaceDescriptorV1)
    assert callable(WorkspaceControllerV1)


def test_workspace_descriptor_fields():
    from framework.workspace_controller_v1 import WorkspaceDescriptorV1
    d = WorkspaceDescriptorV1(
        source_root="/repo",
        scratch_root="/tmp/scratch",
        artifact_root="artifacts",
        source_read_only=True,
    )
    assert d.source_root == "/repo"
    assert d.source_read_only is True


def test_workspace_valid_layout():
    from framework.workspace_controller_v1 import WorkspaceDescriptorV1, WorkspaceControllerV1
    d = WorkspaceDescriptorV1(
        source_root="/repo",
        scratch_root="/tmp/scratch",
        artifact_root="artifacts",
        source_read_only=True,
    )
    c = WorkspaceControllerV1(d)
    assert c.validate_layout() is True


def test_workspace_invalid_scratch_equals_source():
    from framework.workspace_controller_v1 import WorkspaceDescriptorV1, WorkspaceControllerV1
    d = WorkspaceDescriptorV1(
        source_root="same",
        scratch_root="same",
        artifact_root="artifacts",
        source_read_only=True,
    )
    assert WorkspaceControllerV1(d).validate_layout() is False


def test_workspace_artifact_root_not_tmp():
    from framework.workspace_controller_v1 import WorkspaceDescriptorV1, WorkspaceControllerV1
    d = WorkspaceDescriptorV1(
        source_root="/repo",
        scratch_root="/tmp/scratch",
        artifact_root="/tmp/artifacts",
        source_read_only=True,
    )
    assert WorkspaceControllerV1(d).validate_layout() is False


def test_workspace_to_dict():
    from framework.workspace_controller_v1 import WorkspaceDescriptorV1, WorkspaceControllerV1
    d = WorkspaceDescriptorV1("/repo", "/tmp/s", "artifacts", True)
    w = WorkspaceControllerV1(d).to_dict()
    assert w["layout_valid"] is True
    assert w["source_read_only"] is True


# ── permission_decision_v1 ────────────────────────────────────────────────────

def test_permission_decision_import():
    from framework.permission_decision_v1 import PermissionDecisionV1, Decision
    assert Decision.ALLOW.value == "allow"
    assert Decision.DENY.value == "deny"
    assert Decision.ASK.value == "ask"


def test_permission_decision_allow():
    from framework.permission_decision_v1 import PermissionDecisionV1, Decision
    p = PermissionDecisionV1("read_file", "framework/x.py", Decision.ALLOW, "in allowed_files")
    d = p.to_dict()
    assert d["decision"] == "allow"
    assert d["tool_name"] == "read_file"
    assert d["rationale"] == "in allowed_files"


def test_permission_decision_deny():
    from framework.permission_decision_v1 import PermissionDecisionV1, Decision
    p = PermissionDecisionV1("run_command", "framework/__init__.py", Decision.DENY, "forbidden")
    assert p.to_dict()["decision"] == "deny"


def test_permission_decision_ask():
    from framework.permission_decision_v1 import PermissionDecisionV1, Decision
    p = PermissionDecisionV1("publish_artifact", "artifacts/", Decision.ASK, "needs confirm")
    assert p.to_dict()["decision"] == "ask"


# ── artifact_bundle_v1 ────────────────────────────────────────────────────────

def test_artifact_bundle_import():
    from framework.artifact_bundle_v1 import ArtifactBundleV1
    assert callable(ArtifactBundleV1)


def test_artifact_bundle_assembly():
    from framework.session_job_schema_v1 import SessionRecord, JobRecord
    from framework.artifact_bundle_v1 import ArtifactBundleV1

    s = SessionRecord(
        session_id="s-001", package_id="P2-01-TEST", package_label="SUBSTRATE",
        objective="test", allowed_files=[], forbidden_files=[],
        selected_profile=None, selected_backend="substrate",
        workspace_root="/repo", artifact_root="artifacts",
        escalation_status="NOT_ESCALATED", final_outcome="success",
    )
    j = JobRecord(
        job_id="j-001", package_id="P2-01-TEST", package_label="SUBSTRATE",
        objective="test", allowed_files=[], forbidden_files=[],
        selected_profile=None, selected_backend="substrate",
        workspace_root="/repo", artifact_root="artifacts",
        escalation_status="NOT_ESCALATED", final_outcome="success",
        session_id="s-001",
    )
    bundle = ArtifactBundleV1(
        session=s, job=j,
        tools_used=["read_file"],
        validations_run=["make_check"],
        artifacts_produced=["artifacts/substrate/x.json"],
        escalation_status="NOT_ESCALATED",
        final_outcome="success",
    )
    d = bundle.to_dict()
    assert "session" in d
    assert "job" in d
    assert d["escalation_status"] == "NOT_ESCALATED"
    assert d["final_outcome"] == "success"
    assert "tools_used" in d
    assert "validations_run" in d
    assert "artifacts_produced" in d


def test_artifact_bundle_to_dict_has_all_required_keys():
    from framework.session_job_schema_v1 import SessionRecord, JobRecord
    from framework.artifact_bundle_v1 import ArtifactBundleV1

    s = SessionRecord("s", "P", "SUBSTRATE", "o", [], [], None, "substrate", "/r", "a", "NOT_ESCALATED")
    j = JobRecord("j", "P", "SUBSTRATE", "o", [], [], None, "substrate", "/r", "a", "NOT_ESCALATED")
    bundle = ArtifactBundleV1(s, j, [], [], [], "NOT_ESCALATED")
    d = bundle.to_dict()
    for key in ["session", "job", "tools_used", "validations_run",
                "artifacts_produced", "escalation_status", "final_outcome"]:
        assert key in d, f"ArtifactBundleV1.to_dict() missing: {key}"


# ── Cross-module interop ──────────────────────────────────────────────────────

def test_registry_and_permission_interop():
    from framework.tool_registry_v1 import ToolRegistryV1
    from framework.permission_decision_v1 import PermissionDecisionV1, Decision
    r = ToolRegistryV1()
    for name in r.list_tool_names():
        c = r.get_contract(name)
        decision = Decision.ALLOW if not c.side_effecting else Decision.ASK
        p = PermissionDecisionV1(name, "test_scope", decision, "test")
        assert p.tool_name == name
        assert p.decision in (Decision.ALLOW, Decision.ASK)


def test_workspace_and_bundle_interop():
    from framework.workspace_controller_v1 import WorkspaceDescriptorV1, WorkspaceControllerV1
    from framework.session_job_schema_v1 import SessionRecord, JobRecord
    from framework.artifact_bundle_v1 import ArtifactBundleV1

    d = WorkspaceDescriptorV1("/repo", "/tmp/scratch", "artifacts", True)
    ctrl = WorkspaceControllerV1(d)
    assert ctrl.validate_layout()

    s = SessionRecord(
        session_id="s-x", package_id="P-x", package_label="SUBSTRATE",
        objective="interop test", allowed_files=[], forbidden_files=[],
        selected_profile=None, selected_backend="substrate",
        workspace_root=d.source_root, artifact_root=d.artifact_root,
        escalation_status="NOT_ESCALATED",
    )
    j = JobRecord(
        job_id="j-x", package_id="P-x", package_label="SUBSTRATE",
        objective="interop test", allowed_files=[], forbidden_files=[],
        selected_profile=None, selected_backend="substrate",
        workspace_root=d.source_root, artifact_root=d.artifact_root,
        escalation_status="NOT_ESCALATED",
    )
    bundle = ArtifactBundleV1(s, j, [], ["workspace_check"], [], "NOT_ESCALATED")
    bundle_d = bundle.to_dict()
    assert bundle_d["session"]["workspace_root"] == d.source_root


# ── Artifact validation ───────────────────────────────────────────────────────

def test_emit_artifact(tmp_path):
    artifact = {
        "substrate_pack": "minimum_substrate_v1",
        "generated_at": "2026-04-21T00:00:00+00:00",
        "schema_loaded": True,
        "tool_registry_loaded": True,
        "workspace_contract_loaded": True,
        "permission_model_loaded": True,
        "artifact_bundle_loaded": True,
        "all_checks_passed": True,
        "component_summary": [{"module": "framework/session_job_schema_v1.py"}],
    }
    out = tmp_path / "minimum_substrate_check.json"
    out.write_text(json.dumps(artifact, indent=2))
    loaded = json.loads(out.read_text())
    assert loaded["substrate_pack"] == "minimum_substrate_v1"
    assert loaded["all_checks_passed"] is True


def test_runner_script_executes():
    result = subprocess.run(
        [sys.executable, str(REPO_ROOT / "bin" / "run_minimum_substrate_check.py")],
        capture_output=True, text=True, cwd=str(REPO_ROOT),
    )
    assert result.returncode == 0, f"runner failed:\n{result.stderr}"
    assert ARTIFACT_PATH.exists()
    data = json.loads(ARTIFACT_PATH.read_text())
    assert data["substrate_pack"] == "minimum_substrate_v1"
    assert data["all_checks_passed"] is True
    assert len(data["component_summary"]) == 6
    for key in ["schema_loaded", "tool_registry_loaded", "workspace_contract_loaded",
                "permission_model_loaded", "artifact_bundle_loaded"]:
        assert data[key] is True, f"artifact missing True for: {key}"
