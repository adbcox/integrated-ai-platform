#!/usr/bin/env python3
"""Local control-window status probe for first reuse-first OSS wave."""

from __future__ import annotations

import json
import shutil
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]


def exists(path: Path) -> bool:
    return path.exists()


def command_available(name: str) -> bool:
    return shutil.which(name) is not None


def main() -> int:
    payload = {
        "openhands": {
            "wrapper": exists(REPO_ROOT / "bin/oss_wave_openhands.sh"),
            "config_template": exists(REPO_ROOT / "config/oss_wave/openhands.env.example"),
            "docker_available": command_available("docker"),
        },
        "markitdown": {
            "wrapper": exists(REPO_ROOT / "bin/markitdown_wrapper.py"),
            "orchestrator": exists(REPO_ROOT / "bin/oss_wave_markitdown.sh"),
            "uv_available": command_available("uv"),
            "uvx_available": command_available("uvx"),
        },
        "mcp": {
            "wrapper": exists(REPO_ROOT / "bin/oss_wave_mcp.sh"),
            "config": exists(REPO_ROOT / "config/oss_wave/mcp_servers.json"),
            "node_available": command_available("node"),
            "npm_available": command_available("npm"),
        },
        "pr_agent": {
            "wrapper": exists(REPO_ROOT / "bin/oss_wave_pr_agent.sh"),
            "config_template": exists(REPO_ROOT / "config/oss_wave/pr_agent.env.example"),
            "workflow_template": exists(REPO_ROOT / ".github/workflows/pr-agent.yml.disabled"),
        },
        "n8n": {
            "evaluation_note": exists(REPO_ROOT / "docs/roadmap/N8N_EVALUATION_BOUNDARY.md"),
            "broad_rollout": False,
        },
    }
    print(json.dumps(payload, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
