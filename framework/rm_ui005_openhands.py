"""OpenHands local launch-plan support for RM-UI-005."""
from __future__ import annotations

import importlib.util
import shutil
from pathlib import Path
from typing import Any

SUPPORTED_OPENHANDS_MODES = ("docker_web", "cli", "serve")


def _docker_available() -> bool:
    return shutil.which("docker") is not None


def _openhands_binary_available() -> bool:
    return shutil.which("openhands") is not None


def _openhands_module_available() -> bool:
    return importlib.util.find_spec("openhands") is not None


def build_openhands_launch_plan(*, mode: str, repo_root: Path) -> dict[str, Any]:
    """Return launch details for local OpenHands surfaces.

    Modes:
    - docker_web: preferred, dockerized OpenHands web surface
    - cli: local openhands binary invocation
    - serve: local Python module serve path
    """
    root = str(repo_root.resolve())

    if mode == "docker_web":
        ready = _docker_available()
        command = [
            "docker",
            "run",
            "--rm",
            "-p",
            "3000:3000",
            "-e",
            "WORKSPACE_MOUNT_PATH=/workspace",
            "-v",
            f"{root}:/workspace",
            "docker.all-hands.dev/all-hands-ai/openhands:0.23",
        ]
        return {
            "mode": mode,
            "ready": ready,
            "preferred": True,
            "sandbox_posture": "docker",
            "reason": "docker_available" if ready else "docker_not_found",
            "command": command,
            "execution_surface": "openhands_web",
            "authority_model": "subordinate_to_control_window_route_and_completion_contract",
        }

    if mode == "cli":
        ready = _openhands_binary_available()
        command = ["openhands", "--workspace", root]
        return {
            "mode": mode,
            "ready": ready,
            "preferred": False,
            "sandbox_posture": "host",
            "reason": "openhands_binary_available" if ready else "openhands_binary_missing",
            "command": command,
            "execution_surface": "openhands_cli",
            "authority_model": "subordinate_to_control_window_route_and_completion_contract",
        }

    if mode == "serve":
        ready = _openhands_module_available()
        command = ["python3", "-m", "openhands", "serve", "--workspace", root]
        return {
            "mode": mode,
            "ready": ready,
            "preferred": False,
            "sandbox_posture": "host",
            "reason": "openhands_module_available" if ready else "openhands_module_missing",
            "command": command,
            "execution_surface": "openhands_serve",
            "authority_model": "subordinate_to_control_window_route_and_completion_contract",
        }

    return {
        "mode": mode,
        "ready": False,
        "preferred": False,
        "sandbox_posture": "unknown",
        "reason": "unsupported_mode",
        "command": [],
        "execution_surface": "unknown",
        "authority_model": "subordinate_to_control_window_route_and_completion_contract",
    }


def build_openhands_mode_matrix(*, repo_root: Path) -> dict[str, dict[str, Any]]:
    """Return readiness and launch plans for all supported local OpenHands modes."""
    matrix: dict[str, dict[str, Any]] = {}
    for mode in SUPPORTED_OPENHANDS_MODES:
        matrix[mode] = build_openhands_launch_plan(mode=mode, repo_root=repo_root)
    return matrix


__all__ = ["SUPPORTED_OPENHANDS_MODES", "build_openhands_launch_plan", "build_openhands_mode_matrix"]
