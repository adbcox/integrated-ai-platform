#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path

from control_window import build_dashboard_snapshot


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Emit the RM-UI-005 control-window snapshot as JSON.")
    parser.add_argument("--repo-root", default=".", help="Repository root to inspect")
    parser.add_argument("--objective", default="Implement RM-UI-005 first slice", help="Current objective")
    parser.add_argument("--current-item", default="RM-UI-005", help="Current roadmap item")
    parser.add_argument("--file", dest="files", action="append", default=[], help="File to include in context")
    parser.add_argument("--changed-file", dest="changed_files", action="append", default=[], help="Changed file to display")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    snapshot = build_dashboard_snapshot(
        repo_root=Path(args.repo_root),
        objective=args.objective,
        files=args.files,
        changed_files=args.changed_files,
        current_item=args.current_item,
    )
    print(json.dumps(snapshot.model_dump(), indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
