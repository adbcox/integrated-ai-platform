from __future__ import annotations

from pathlib import Path

import framework.rm_ui005_openhands as oh


def test_openhands_docker_plan_ready(monkeypatch):
    monkeypatch.setattr(oh, "_docker_available", lambda: True)
    plan = oh.build_openhands_launch_plan(mode="docker_web", repo_root=Path("."))
    assert plan["mode"] == "docker_web"
    assert plan["ready"] is True
    assert plan["sandbox_posture"] == "docker"
    assert plan["command"][0] == "docker"


def test_openhands_cli_plan_not_ready(monkeypatch):
    monkeypatch.setattr(oh, "_openhands_binary_available", lambda: False)
    plan = oh.build_openhands_launch_plan(mode="cli", repo_root=Path("."))
    assert plan["mode"] == "cli"
    assert plan["ready"] is False
    assert plan["reason"] == "openhands_binary_missing"
    assert plan["command"] == ["openhands", "--workspace", str(Path(".").resolve())]


def test_openhands_unsupported_mode():
    plan = oh.build_openhands_launch_plan(mode="unknown", repo_root=Path("."))
    assert plan["ready"] is False
    assert plan["reason"] == "unsupported_mode"


def test_openhands_mode_matrix_has_supported_modes(monkeypatch):
    monkeypatch.setattr(oh, "_docker_available", lambda: True)
    monkeypatch.setattr(oh, "_openhands_binary_available", lambda: False)
    monkeypatch.setattr(oh, "_openhands_module_available", lambda: False)
    matrix = oh.build_openhands_mode_matrix(repo_root=Path("."))
    assert set(matrix.keys()) == {"docker_web", "cli", "serve"}
    assert matrix["docker_web"]["ready"] is True
    assert matrix["cli"]["ready"] is False
    assert matrix["serve"]["ready"] is False


def test_openhands_serve_mode_ready_by_module(monkeypatch):
    monkeypatch.setattr(oh, "_openhands_module_available", lambda: True)
    plan = oh.build_openhands_launch_plan(mode="serve", repo_root=Path("."))
    assert plan["ready"] is True
    assert plan["reason"] == "openhands_module_available"
