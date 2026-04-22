#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path

from control_window import RouteRequest, build_aider_packet, detect_route, estimate_context_pressure


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Route a task into an RM-UI-005 execution lane and emit the packet.")
    parser.add_argument("--repo-root", default=".", help="Repository root to inspect")
    parser.add_argument("--objective", required=True, help="Task objective")
    parser.add_argument("--current-item", default="RM-UI-005", help="Current roadmap item")
    parser.add_argument("--file", dest="files", action="append", default=[], help="File to include in scope")
    parser.add_argument("--changed-file", dest="changed_files", action="append", default=[], help="Changed file to display")
    parser.add_argument("--lane-hint", default=None, help="Optional explicit lane hint")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    repo_root = Path(args.repo_root)
    request = RouteRequest(
        objective=args.objective,
        files=args.files,
        changed_files=args.changed_files,
        current_item=args.current_item,
        lane_hint=args.lane_hint,
    )
    route = detect_route(request, repo_root)
    context = estimate_context_pressure(repo_root, args.files, args.changed_files, route.selected_lane)
    packet = build_aider_packet(request, route, context)
    print(json.dumps(
        {
            "route": route.model_dump(),
            "context_pressure": context.model_dump(),
            "aider_packet": packet.model_dump(),
        },
        indent=2,
    ))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
