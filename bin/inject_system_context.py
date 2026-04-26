#!/usr/bin/env python3
"""Auto-context loader — injects platform knowledge into AI engine prompts.

Reads config/system_knowledge.yaml + key docs and produces a context block
that can be:
  - Written to .aider.conf.yml (via --write-aider-conf)
  - Prepended to a prompt string (via --prompt "...")
  - Exported as a shell variable (via --export-env)
  - Printed as a JSON blob for API consumption (via --json)

Usage:
    # Update .aider.conf.yml with current system knowledge
    python3 bin/inject_system_context.py --write-aider-conf

    # Print context block for use in a script
    python3 bin/inject_system_context.py --print

    # Prepend context to a prompt and output the combined string
    python3 bin/inject_system_context.py --prompt "Fix the executor abstraction"

    # Export as SYSTEM_CONTEXT env var
    eval $(python3 bin/inject_system_context.py --export-env)

    # Return JSON for API calls
    python3 bin/inject_system_context.py --json
"""
from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path
from typing import Any

_REPO = Path(__file__).parent.parent
_CONFIG = _REPO / "config" / "system_knowledge.yaml"
_CLAUDE_MD = _REPO / "CLAUDE.md"
_AGENTS_MD = _REPO / "AGENTS.md"
_CONNECTORS = _REPO / "config" / "connectors.yaml"
_PROGRESS = _REPO / "docs" / "progress-contract.md"
_GATE = _REPO / "docs" / "codex51-replacement-gate.md"
_AIDER_CONF = _REPO / ".aider.conf.yml"


def _load_yaml(path: Path) -> dict[str, Any]:
    try:
        import yaml  # type: ignore
        return yaml.safe_load(path.read_text()) or {}
    except ImportError:
        # Fallback: minimal key-value parse without PyYAML
        result: dict[str, Any] = {}
        for line in path.read_text().splitlines():
            if ":" in line and not line.strip().startswith("#") and not line.strip().startswith("-"):
                k, _, v = line.partition(":")
                k = k.strip()
                v = v.strip()
                if v and not v.startswith("{") and not v.startswith("["):
                    result[k] = v
        return result
    except Exception as exc:
        print(f"Warning: could not load {path}: {exc}", file=sys.stderr)
        return {}


def _read_section(path: Path, max_lines: int = 60) -> str:
    """Read a doc file, returning only the first max_lines lines."""
    if not path.exists():
        return ""
    lines = path.read_text().splitlines()[:max_lines]
    return "\n".join(lines)


def build_context_block() -> str:
    """Build the full system context block as a string."""
    cfg = _load_yaml(_CONFIG) if _CONFIG.exists() else {}

    lines: list[str] = [
        "=" * 72,
        "INTEGRATED AI PLATFORM — SYSTEM CONTEXT",
        "=" * 72,
        "",
    ]

    # Platform identity
    p = cfg.get("platform", {})
    if p:
        lines += [
            f"Platform : {p.get('name', 'Integrated AI Platform')}",
            f"Purpose  : {p.get('purpose', '')}",
            f"Hosts    : {p.get('primary_host', '')}",
            f"Repo     : {p.get('repo_root', str(_REPO))}",
            "",
        ]

    # Primary milestone
    ml = cfg.get("architecture", {})
    if ml.get("primary_milestone"):
        lines += [f"Milestone: {ml['primary_milestone']}", ""]

    # Models
    m = cfg.get("models", {})
    if m:
        lines += [
            "LOCAL MODELS",
            f"  Fast   : {m.get('default_fast', 'qwen2.5-coder:14b')}",
            f"  Hard   : {m.get('default_hard', 'deepseek-coder-v2:latest')}",
            f"  Smart  : {m.get('default_smart', 'qwen2.5-coder:32b')}",
            f"  Ollama : {m.get('ollama_base', 'http://127.0.0.1:11434')}",
            "",
        ]

    # Services
    svc = cfg.get("services", {})
    if svc:
        lines.append("EXTERNAL SERVICES")
        for name, info in svc.items():
            if isinstance(info, dict):
                host = info.get("host", "")
                port = info.get("port", "")
                addr = f"{host}:{port}" if port else host
                note = info.get("note", "")
                lines.append(f"  {name:<18}: {addr}  {note}")
        lines.append("")

    # Constraints
    constraints = cfg.get("constraints", [])
    if constraints:
        lines.append("CONSTRAINTS (apply to all changes)")
        for c in constraints:
            lines.append(f"  - {c}")
        lines.append("")

    # Pipeline stages
    pipe = cfg.get("pipeline", {})
    rag = pipe.get("rag_stages", [])
    if rag:
        lines.append("PIPELINE STAGES")
        for s in rag:
            lines.append(f"  {s.get('stage', '?'):<8}: {s.get('file', '')}  — {s.get('role', '')}")
        lines.append("")

    # Validation commands
    val = cfg.get("validation", {})
    if val:
        lines += [
            "VALIDATION (run after changes)",
            f"  Full   : {val.get('full', 'make check')}",
            f"  Fast   : {val.get('fast', 'make quick')}",
            f"  Tests  : {val.get('offline', 'make test-offline')}",
            "",
        ]

    # Aider-specific instructions
    aider_ctx = cfg.get("aider_context", "")
    if aider_ctx:
        lines += ["AIDER INSTRUCTIONS", aider_ctx.strip(), ""]

    lines.append("=" * 72)
    return "\n".join(lines)


def build_aider_conf() -> str:
    """Build a complete .aider.conf.yml content."""
    cfg = _load_yaml(_CONFIG) if _CONFIG.exists() else {}
    m = cfg.get("models", {})
    repo = cfg.get("platform", {}).get("repo_root", str(_REPO))

    # Build list of --read files (only include files that exist)
    read_files = []
    for candidate in [_CLAUDE_MD, _AGENTS_MD, _CONFIG, _CONNECTORS]:
        if candidate.exists():
            rel = candidate.relative_to(_REPO)
            read_files.append(f"  - {rel}")

    read_block = "\n".join(read_files) if read_files else "  []"

    ollama_base = m.get("ollama_base", "http://127.0.0.1:11434")
    model       = m.get("default_fast", "qwen2.5-coder:14b")
    editor      = "qwen2.5-coder:7b"

    # Detect ollama prefix format
    model_str  = f"ollama/{model}"
    editor_str = f"ollama/{editor}"

    return f"""# .aider.conf.yml — auto-generated by bin/inject_system_context.py
# Edit config/system_knowledge.yaml to change content; re-run to regenerate.
# Source: {repo}

model: {model_str}
editor-model: {editor_str}
ollama-api-base: {ollama_base}

no-auto-commits: true
auto-lint: true
git: true

# Files loaded as read-only context for every aider session
read:
{read_block}

# Lint commands run after every edit
lint-cmd:
  python: "python3 -m py_compile {{file}}"
  sh: "bash -n {{file}}"
  bash: "bash -n {{file}}"

# Auto-test after edits (optional — comment out if slow)
# test-cmd: "make quick"

# Preferred diff format
pretty: true
"""


def _push_metric(name: str, value: float) -> None:
    """Push a context-load metric to VictoriaMetrics if available."""
    vm_url = os.environ.get("VICTORIA_URL", "http://localhost:8428")
    try:
        import urllib.request
        body = f"{name} {value}\n".encode()
        req = urllib.request.Request(
            f"{vm_url}/api/v1/import/prometheus",
            data=body,
            headers={"Content-Type": "text/plain"},
            method="POST",
        )
        urllib.request.urlopen(req, timeout=2)
    except Exception:
        pass  # Non-critical; observability stack may not be running


def main() -> int:
    parser = argparse.ArgumentParser(description="Inject system context into AI prompts")
    parser.add_argument("--print",            action="store_true", help="Print context block to stdout")
    parser.add_argument("--json",             action="store_true", help="Output context as JSON")
    parser.add_argument("--export-env",       action="store_true", help="Output shell export statement")
    parser.add_argument("--write-aider-conf", action="store_true", help="Write/update .aider.conf.yml")
    parser.add_argument("--prompt",           default="",          help="Prepend context to this prompt string")
    parser.add_argument("--dry-run",          action="store_true", help="Show what would be written without writing")
    args = parser.parse_args()

    if not any([args.print, args.json, args.export_env, args.write_aider_conf, args.prompt]):
        parser.print_help()
        return 0

    _push_metric("context_inject_total", 1)

    if args.write_aider_conf:
        content = build_aider_conf()
        if args.dry_run:
            print("Would write to .aider.conf.yml:")
            print(content)
        else:
            _AIDER_CONF.write_text(content)
            print(f"✓ Wrote {_AIDER_CONF}")
        return 0

    ctx = build_context_block()

    if args.json:
        cfg = _load_yaml(_CONFIG) if _CONFIG.exists() else {}
        print(json.dumps({"context": ctx, "config": cfg}, indent=2))
        return 0

    if args.export_env:
        escaped = ctx.replace("'", "'\\''")
        print(f"export SYSTEM_CONTEXT='{escaped}'")
        return 0

    if args.prompt:
        print(ctx)
        print()
        print(args.prompt)
        return 0

    if args.print:
        print(ctx)

    return 0


if __name__ == "__main__":
    sys.exit(main())
