#!/usr/bin/env python3
"""CLI for the multi-server Orchestrator.

Usage
-----
    python3 bin/orchestrator_cli.py health
    python3 bin/orchestrator_cli.py topology
    python3 bin/orchestrator_cli.py status [--node mac-mini]
    python3 bin/orchestrator_cli.py scan   [--node mac-mini]
    python3 bin/orchestrator_cli.py import [--node mac-mini] [--dry-run]
    python3 bin/orchestrator_cli.py generate "add logging to ExecutorFactory"
    python3 bin/orchestrator_cli.py ai-item "Add dark-mode toggle to dashboard"
    python3 bin/orchestrator_cli.py train  [--node mac-studio]
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

# Allow running from repo root without installing the package
sys.path.insert(0, str(Path(__file__).parent.parent))

from framework.orchestrator import Orchestrator  # noqa: E402


def _pp(data: dict) -> None:
    """Pretty-print a dict as JSON."""
    print(json.dumps(data, indent=2, default=str))


def cmd_health(orch: Orchestrator, _args: argparse.Namespace) -> int:
    results = orch.health_all()
    any_healthy = False
    for name, info in results.items():
        sym = "✓" if info["healthy"] else "✗"
        lat = f"{info['latency_ms']} ms" if info["healthy"] else "—"
        roles = ", ".join(info["roles"])
        print(f"  {sym}  {name:<14} {info['url']:<35} {lat:<10} [{roles}]")
        if info["healthy"]:
            any_healthy = True
    if not any_healthy:
        print("\n  No healthy nodes found.", file=sys.stderr)
        return 1
    return 0


def cmd_topology(orch: Orchestrator, _args: argparse.Namespace) -> int:
    orch.health_all()  # refresh before reporting
    _pp(orch.topology())
    return 0


def cmd_status(orch: Orchestrator, args: argparse.Namespace) -> int:
    result = orch.status(node=args.node)
    _pp(result)
    return 0 if "_status" in result and result["_status"] == 200 else 1


def cmd_scan(orch: Orchestrator, args: argparse.Namespace) -> int:
    print("Scanning roadmap docs…")
    result = orch.scan_roadmap(node=args.node)
    if "error" in result:
        print(f"Error: {result['error']}", file=sys.stderr)
        return 1
    print(f"  total_files : {result.get('total_files', '?')}")
    print(f"  issue_items : {result.get('issue_items', '?')}")
    print(f"  unique_ids  : {result.get('unique_ids', '?')}")
    print(f"  duplicates  : {result.get('duplicate_ids', '?')}")
    by_cat = result.get("by_category", {})
    if by_cat:
        print(f"\n  Categories ({len(by_cat)}):")
        for cat, cnt in sorted(by_cat.items(), key=lambda x: -x[1])[:15]:
            print(f"    {cat:<12} {cnt:>4}")
    node = result.get("_node", "?")
    print(f"\n  Served by: {node}")
    return 0


def cmd_import(orch: Orchestrator, args: argparse.Namespace) -> int:
    print("Scanning roadmap docs…")
    scan = orch.scan_roadmap(node=args.node)
    if "error" in scan:
        print(f"Scan error: {scan['error']}", file=sys.stderr)
        return 1

    items = scan.get("items", [])
    issue_items = [i for i in items if not i.get("is_exec_pack")]
    print(f"  Found {len(issue_items)} issue items to import.")

    if args.dry_run:
        print("  --dry-run: skipping import.")
        return 0

    confirm = input(f"  Import {len(issue_items)} items into Plane CE? [y/N] ").strip().lower()
    if confirm != "y":
        print("  Aborted.")
        return 0

    print("Importing…")
    result = orch.import_roadmap(issue_items, node=args.node)
    if "error" in result:
        print(f"Import error: {result['error']}", file=sys.stderr)
        return 1
    print(f"  created : {result.get('created', '?')}")
    print(f"  updated : {result.get('updated', '?')}")
    print(f"  errors  : {result.get('errors', '?')}")
    return 0


def cmd_generate(orch: Orchestrator, args: argparse.Namespace) -> int:
    prompt = " ".join(args.prompt)
    if not prompt:
        print("Error: provide a prompt string.", file=sys.stderr)
        return 1
    print(f"Generating code for: {prompt!r}")
    result = orch.generate_code(prompt, engine=args.engine, node=args.node)
    if "error" in result:
        print(f"Error: {result['error']}", file=sys.stderr)
        return 1
    print("\n── code ──")
    print(result.get("code", "(empty)"))
    if result.get("tests"):
        print("\n── tests ──")
        print(result["tests"])
    return 0


def cmd_ai_item(orch: Orchestrator, args: argparse.Namespace) -> int:
    description = " ".join(args.description)
    if not description:
        print("Error: provide a description.", file=sys.stderr)
        return 1
    print(f"Generating AI roadmap item: {description!r}")
    result = orch.ai_roadmap_item(description, node=args.node)
    if "error" in result:
        print(f"Error: {result['error']}", file=sys.stderr)
        return 1
    item = result.get("item", result)
    print(f"  id       : {item.get('id', '?')}")
    print(f"  title    : {item.get('title', '?')}")
    print(f"  category : {item.get('category', '?')}")
    print(f"  priority : {item.get('priority', '?')}")
    return 0


def cmd_train(orch: Orchestrator, args: argparse.Namespace) -> int:
    print("Starting training…")
    result = orch.start_training(node=args.node)
    _pp(result)
    return 0 if "_status" in result and result["_status"] == 200 else 1


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="orchestrator_cli",
        description="Multi-server orchestrator CLI",
    )
    p.add_argument("--node", default=None, metavar="NAME",
                   help="Preferred node name (e.g. mac-mini, mac-studio)")

    sub = p.add_subparsers(dest="command", required=True)

    sub.add_parser("health",   help="Check health of all nodes")
    sub.add_parser("topology", help="Show full topology as JSON")
    sub.add_parser("status",   help="Get platform status from a node")
    sub.add_parser("scan",     help="Scan roadmap RM-*.md files")

    imp = sub.add_parser("import", help="Scan + import roadmap docs into Plane CE")
    imp.add_argument("--dry-run", action="store_true",
                     help="Show what would be imported without doing it")

    gen = sub.add_parser("generate", help="Generate code via AI engine")
    gen.add_argument("prompt", nargs="+", help="Prompt string")
    gen.add_argument("--engine", default="claude",
                     choices=["claude", "aider", "codex"],
                     help="AI engine to use (default: claude)")

    ai = sub.add_parser("ai-item", help="Generate an AI roadmap item")
    ai.add_argument("description", nargs="+", help="Feature description")

    sub.add_parser("train", help="Trigger training on a node")

    return p


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()

    orch = Orchestrator()

    dispatch = {
        "health":   cmd_health,
        "topology": cmd_topology,
        "status":   cmd_status,
        "scan":     cmd_scan,
        "import":   cmd_import,
        "generate": cmd_generate,
        "ai-item":  cmd_ai_item,
        "train":    cmd_train,
    }

    fn = dispatch.get(args.command)
    if fn is None:
        print(f"Unknown command: {args.command}", file=sys.stderr)
        return 1

    return fn(orch, args)


if __name__ == "__main__":
    sys.exit(main())
