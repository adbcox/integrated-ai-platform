"""Conformance tests for packet_1: RMCC1-RUNTIME-ADOPTION-SEAM-1."""
from __future__ import annotations

import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))

from framework.session_job_adapters import make_session_adapter, make_job_adapter, session_to_context_dict
from framework.read_file_dispatch import dispatch_read_file
from framework.runtime_adoption_proof import make_bounded_context
from framework.runtime_execution_adapter import extract_session_id
from framework.tool_schema import ReadFileAction, ReadFileObservation
from framework.workspace_scope import ToolPathScope
from framework.canonical_session_schema import CanonicalSession
from framework.canonical_job_schema import CanonicalJob


# --- Inspection gates ---

def test_inspection_gate_session_schema():
    assert hasattr(CanonicalSession, "__dataclass_fields__")
    assert "session_id" in CanonicalSession.__dataclass_fields__


def test_inspection_gate_job_schema():
    assert hasattr(CanonicalJob, "__dataclass_fields__")
    assert hasattr(CanonicalJob, "from_session")


# --- session_job_adapters ---

def test_make_session_adapter_produces_canonical_session():
    session = make_session_adapter("sess-test", "task-1", objective="test objective")
    assert isinstance(session, CanonicalSession)
    assert session.session_id == "sess-test"
    assert session.task_id == "task-1"
    assert session.objective == "test objective"


def test_make_job_adapter_from_canonical_session():
    session = make_session_adapter("sess-abc", "task-2", task_class="bounded_coding")
    job = make_job_adapter(session, job_id="job-xyz")
    assert isinstance(job, CanonicalJob)
    assert job.session_id == "sess-abc"
    assert job.job_id == "job-xyz"


def test_make_job_adapter_from_dict():
    job = make_job_adapter({"session_id": "sess-dict"}, job_id="job-from-dict")
    assert job.session_id == "sess-dict"
    assert job.job_id == "job-from-dict"


def test_make_job_adapter_auto_job_id():
    session = make_session_adapter("sess-auto", "task-auto")
    job = make_job_adapter(session)
    assert job.job_id.startswith("job-")


def test_session_to_context_dict_from_canonical_session():
    session = make_session_adapter("sess-ctx", "task-ctx")
    ctx = session_to_context_dict(session)
    assert ctx["session_id"] == "sess-ctx"


def test_session_to_context_dict_accepted_by_extract_session_id():
    session = make_session_adapter("sess-extract", "task-x")
    ctx = session_to_context_dict(session)
    assert extract_session_id(ctx) == "sess-extract"


def test_session_to_context_dict_from_mapping():
    ctx = session_to_context_dict({"session_id": "sess-map"})
    assert ctx["session_id"] == "sess-map"
    assert extract_session_id(ctx) == "sess-map"


# --- dispatch_read_file ---

def test_dispatch_read_file_reads_real_file(tmp_path):
    f = tmp_path / "hello.py"
    f.write_text("# hello\n", encoding="utf-8")
    scope = ToolPathScope(source_root=tmp_path, writable_roots=())
    action = ReadFileAction(path=str(f))
    obs = dispatch_read_file(action, scope)
    assert isinstance(obs, ReadFileObservation)
    assert "hello" in obs.content
    assert obs.error is None


def test_dispatch_read_file_returns_typed_error_on_missing_file(tmp_path):
    scope = ToolPathScope(source_root=tmp_path, writable_roots=())
    action = ReadFileAction(path=str(tmp_path / "nonexistent.py"))
    obs = dispatch_read_file(action, scope)
    assert isinstance(obs, ReadFileObservation)
    assert obs.content == ""
    assert obs.error is not None


def test_dispatch_read_file_uses_no_subprocess():
    import framework.read_file_dispatch as mod
    src = Path(mod.__file__).read_text()
    assert "subprocess" not in src


# --- make_bounded_context ---

def test_make_bounded_context_returns_required_keys(tmp_path):
    session = make_session_adapter("sess-ctx2", "task-ctx2")
    base = tmp_path / "base"
    base.mkdir()
    ctx = make_bounded_context(session, tmp_path, base)
    assert "session" in ctx
    assert "workspace" in ctx
    assert "scope" in ctx
    assert "gate" in ctx


def test_make_bounded_context_gate_allows_by_default(tmp_path):
    session = make_session_adapter("sess-gate", "task-gate")
    base = tmp_path / "base"
    base.mkdir()
    ctx = make_bounded_context(session, tmp_path, base, allow_commands=True)
    from framework.tool_schema import RunCommandAction
    from framework.typed_permission_gate import ToolPermission
    gate = ctx["gate"]
    assert gate.evaluate(RunCommandAction(command="ls")) == ToolPermission.ALLOW


def test_make_bounded_context_gate_denies_when_allow_commands_false(tmp_path):
    session = make_session_adapter("sess-deny", "task-deny")
    base = tmp_path / "base"
    base.mkdir()
    ctx = make_bounded_context(session, tmp_path, base, allow_commands=False)
    from framework.tool_schema import RunCommandAction
    from framework.typed_permission_gate import ToolPermission
    gate = ctx["gate"]
    assert gate.evaluate(RunCommandAction(command="ls")) == ToolPermission.DENY


# --- package surface ---

def test_package_surface_export():
    import framework
    assert hasattr(framework, "make_session_adapter")
    assert hasattr(framework, "make_job_adapter")
    assert hasattr(framework, "session_to_context_dict")
    assert hasattr(framework, "dispatch_read_file")
    assert hasattr(framework, "make_bounded_context")
