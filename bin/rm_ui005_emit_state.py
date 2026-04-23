#!/usr/bin/env python3
"""Emit machine-readable RM-UI-005 control window state artifact."""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))

from framework.rm_ui005_control_window import build_control_window_state, emit_control_window_state  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser(description="Emit RM-UI-005 control window state")
    parser.add_argument("--task", default="Implement RM-UI-005 local execution control window")
    parser.add_argument("--objective", default=None)
    parser.add_argument("--mode", default="docker_web", choices=["docker_web", "cli", "serve"])
    args = parser.parse_args()

    state = build_control_window_state(task_input=args.task, objective=args.objective, openhands_mode=args.mode)
    out = emit_control_window_state(state)
    print(json.dumps({"artifact": str(out), "lane": state["current_lane"], "branch": state["current_branch"]}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
