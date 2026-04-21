"""Conformance tests for framework/typed_permission_gate.py (RUNTIME-CONTRACT-A1-PERMISSION-SEAM-1)."""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))

from framework.typed_permission_gate import PermissionRule, ToolPermission, TypedPermissionGate
from framework.tool_schema import ReadFileAction, RunCommandAction, ApplyPatchAction
from framework.tool_system import ToolAction as LegacyToolAction, ToolName


def test_enum_values():
    assert ToolPermission.ALLOW == "allow"
    assert ToolPermission.ASK == "ask"
    assert ToolPermission.DENY == "deny"


def test_rule_construction():
    rule = PermissionRule(tool_name="read_file", permission=ToolPermission.ALLOW)
    assert rule.tool_name == "read_file"
    assert rule.permission == ToolPermission.ALLOW
    assert rule.command_pattern is None


def test_default_deny():
    gate = TypedPermissionGate()
    action = ReadFileAction(path="x.py")
    assert gate.evaluate(action) == ToolPermission.DENY


def test_default_allow_override():
    gate = TypedPermissionGate(default_permission=ToolPermission.ALLOW)
    action = ReadFileAction(path="x.py")
    assert gate.evaluate(action) == ToolPermission.ALLOW


def test_explicit_allow_for_read_file():
    gate = TypedPermissionGate(rules=[
        PermissionRule(tool_name="read_file", permission=ToolPermission.ALLOW),
    ])
    assert gate.evaluate(ReadFileAction(path="x.py")) == ToolPermission.ALLOW


def test_explicit_deny_for_apply_patch():
    gate = TypedPermissionGate(rules=[
        PermissionRule(tool_name="apply_patch", permission=ToolPermission.DENY),
    ], default_permission=ToolPermission.ALLOW)
    assert gate.evaluate(ApplyPatchAction(path="f", old_string="a", new_string="b")) == ToolPermission.DENY


def test_wildcard_allow():
    gate = TypedPermissionGate(rules=[
        PermissionRule(tool_name="*", permission=ToolPermission.ALLOW),
    ])
    assert gate.evaluate(ReadFileAction(path="x.py")) == ToolPermission.ALLOW
    assert gate.evaluate(RunCommandAction(command="ls")) == ToolPermission.ALLOW


def test_command_pattern_deny():
    gate = TypedPermissionGate(rules=[
        PermissionRule(tool_name="run_command", permission=ToolPermission.DENY, command_pattern=r"rm\s+-rf"),
        PermissionRule(tool_name="run_command", permission=ToolPermission.ALLOW),
    ])
    assert gate.evaluate(RunCommandAction(command="rm -rf /tmp/x")) == ToolPermission.DENY
    assert gate.evaluate(RunCommandAction(command="ls -la")) == ToolPermission.ALLOW


def test_no_match_falls_through_to_default():
    gate = TypedPermissionGate(rules=[
        PermissionRule(tool_name="apply_patch", permission=ToolPermission.ALLOW),
    ], default_permission=ToolPermission.DENY)
    assert gate.evaluate(ReadFileAction(path="x.py")) == ToolPermission.DENY


def test_first_match_wins():
    gate = TypedPermissionGate(rules=[
        PermissionRule(tool_name="read_file", permission=ToolPermission.ALLOW),
        PermissionRule(tool_name="read_file", permission=ToolPermission.DENY),
    ])
    assert gate.evaluate(ReadFileAction(path="x.py")) == ToolPermission.ALLOW


def test_legacy_tool_action_rejected():
    gate = TypedPermissionGate(default_permission=ToolPermission.ALLOW)
    legacy = LegacyToolAction(job_id="j1", tool=ToolName.RUN_COMMAND)
    with pytest.raises(TypeError):
        gate.evaluate(legacy)


def test_package_surface_export():
    import framework
    assert hasattr(framework, "TypedPermissionGate")
    assert hasattr(framework, "ToolPermission")
    assert hasattr(framework, "PermissionRule")
    gate = framework.TypedPermissionGate()
    assert gate.evaluate(ReadFileAction(path="x")) == framework.ToolPermission.DENY
