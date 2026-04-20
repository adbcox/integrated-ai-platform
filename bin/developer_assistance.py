#!/usr/bin/env python3
"""Developer assistance CLI — Phase 1.

Usage:
    python3 bin/developer_assistance.py status
    python3 bin/developer_assistance.py tools [--all]
    python3 bin/developer_assistance.py manifest
"""

from __future__ import annotations  # PEP-563

import argparse
import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT))

from framework.developer_assistance_service import (
    get_status,
    list_tools,
    load_manifest,
    MANIFEST_PATH,
    TOOL_REGISTRY_PATH,
)


def _print_json(obj: object) -> None:
    print(json.dumps(obj, indent=2, ensure_ascii=False))


def cmd_status() -> int:
    result = get_status()
    _print_json(result)
    return 0


def cmd_tools(*, all_tools: bool = False) -> int:
    try:
        tools = list_tools(enabled_only=not all_tools)
    except FileNotFoundError as exc:
        print(json.dumps({"error": f"tool registry not found: {TOOL_REGISTRY_PATH}"}), file=sys.stderr)
        return 1
    _print_json(tools)
    return 0


def cmd_manifest() -> int:
    try:
        manifest = load_manifest()
    except FileNotFoundError:
        print(json.dumps({"error": f"manifest not found: {MANIFEST_PATH}"}), file=sys.stderr)
        return 1
    _print_json(manifest)
    return 0


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Developer assistance CLI")
    sub = parser.add_subparsers(dest="command", required=True)

    sub.add_parser("status", help="Print subsystem status as JSON")

    tools_p = sub.add_parser("tools", help="List tools as JSON array")
    tools_p.add_argument("--all", action="store_true", dest="all_tools", help="Include disabled tools")

    sub.add_parser("manifest", help="Print manifest as JSON")

    return parser.parse_args()


if __name__ == "__main__":
    args = _parse_args()
    if args.command == "status":
        raise SystemExit(cmd_status())
    elif args.command == "tools":
        raise SystemExit(cmd_tools(all_tools=args.all_tools))
    elif args.command == "manifest":
        raise SystemExit(cmd_manifest())
    else:
        print(f"unknown command: {args.command}", file=sys.stderr)
        raise SystemExit(1)
