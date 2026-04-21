"""Conformance tests for framework/tool_bridge.py (RUNTIME-CONTRACT-A1-TOOL-BRIDGE-1)."""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))

from framework.tool_bridge import SCHEMA_TOOL_NAMES, is_schema_action, tool_name_for
from framework.tool_schema import ReadFileAction, RunCommandAction
from framework.tool_system import ToolAction as LegacyToolAction, ToolName


def test_schema_tool_names_has_nine():
    assert len(SCHEMA_TOOL_NAMES) == 9


def test_schema_tool_names_contains_expected():
    for name in (
        "read_file", "search", "run_command", "run_tests",
        "apply_patch", "git_diff", "list_dir", "repo_map", "publish_artifact",
    ):
        assert name in SCHEMA_TOOL_NAMES


def test_is_schema_action_true_for_read_file():
    assert is_schema_action(ReadFileAction(path="x.py")) is True


def test_is_schema_action_true_for_run_command():
    assert is_schema_action(RunCommandAction(command="ls")) is True


def test_is_schema_action_false_for_legacy_action():
    legacy = LegacyToolAction(job_id="j1", tool=ToolName.RUN_COMMAND)
    assert is_schema_action(legacy) is False


def test_is_schema_action_false_for_string():
    assert is_schema_action("run_command") is False


def test_tool_name_for_read_file():
    assert tool_name_for(ReadFileAction(path="x.py")) == "read_file"


def test_tool_name_for_run_command():
    assert tool_name_for(RunCommandAction(command="ls")) == "run_command"


def test_tool_name_for_raises_type_error_for_wrong_input():
    with pytest.raises(TypeError):
        tool_name_for("not_an_action")


def test_framework_exports_schema_surface():
    import framework
    assert hasattr(framework, "ReadFileAction")
    assert hasattr(framework, "RunCommandAction")
    assert hasattr(framework, "DEFAULT_REGISTRY")
    assert hasattr(framework, "SCHEMA_TOOL_NAMES")
    assert len(framework.DEFAULT_REGISTRY) == 9
