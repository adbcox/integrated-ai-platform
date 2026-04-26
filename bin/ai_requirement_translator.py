#!/usr/bin/env python3
"""Translate natural language requirements → fully structured Plane roadmap items.

Uses Ollama (local, 100% open source) — no cloud AI services.

Usage:
    # Translate a single requirement
    python3 bin/ai_requirement_translator.py "We need OAuth2 login with GitHub and Google"

    # Translate and create in Plane immediately
    python3 bin/ai_requirement_translator.py --create "Add rate limiting to the API gateway"

    # Translate a file of requirements (one per line)
    python3 bin/ai_requirement_translator.py --file requirements.txt --create

    # Interactive mode
    python3 bin/ai_requirement_translator.py --interactive

    # Batch from stdin
    echo "Add dark mode to dashboard" | python3 bin/ai_requirement_translator.py --stdin
"""
from __future__ import annotations

import argparse
import json
import os
import re
import sys
import time
import urllib.request
from pathlib import Path
from typing import Any

_REPO_ROOT = Path(os.environ.get("REPO_ROOT", Path(__file__).parent.parent))
sys.path.insert(0, str(_REPO_ROOT))

from framework.plane_connector import PlaneAPI

OLLAMA_HOST  = os.environ.get("OLLAMA_HOST", "localhost:11434")
OLLAMA_MODEL = os.environ.get("OLLAMA_MODEL", "qwen2.5-coder:14b")


# ── Prompt template ───────────────────────────────────────────────────────────

TRANSLATION_PROMPT = '''You are a senior Project Manager with Agile and PMP expertise.

Convert the following requirement into a fully structured project management item.

Requirement:
{requirement}

Context (existing roadmap categories for reference):
{categories}

Return ONLY a single valid JSON object — no markdown, no explanation, no code fences.
Use exactly this schema:

{{
  "id_suggestion": "RM-CATEGORY-NNN",
  "title": "Clear, actionable title, max 80 chars, starts with a verb",
  "description": "2-4 sentences: what, why, and acceptance criteria",
  "category": "one of: API CLI CONFIG CORE DATA DEV DOCS FLOW MEDIA MONITOR OPS PERF REFACTOR SCALE SECURITY TESTING UI UX UTIL",
  "type": "Feature | Enhancement | Bug | System | Chore",
  "priority": "Critical | High | Medium | Low",
  "priority_class": "P1 | P2 | P3 | P4",
  "loe": "S | M | L | XL",
  "estimate_points": 1,
  "strategic_value": 5,
  "architecture_fit": 4,
  "execution_risk": 2,
  "dependency_burden": 0,
  "labels": ["feature"],
  "dependencies": [],
  "business_value": 7,
  "risk_level": "low | medium | high | critical",
  "success_criteria": ["Criterion 1", "Criterion 2"],
  "subtasks": ["Subtask 1", "Subtask 2", "Subtask 3"],
  "target_horizon": "immediate | soon | later | future",
  "readiness": "immediate | near | dependent | speculative",
  "notes": "One sentence on autonomous-executor suitability"
}}

Rules:
- title: imperative verb first ("Add", "Build", "Migrate", "Fix", "Improve")
- estimate_points: Fibonacci (1 2 3 5 8 13) matching LOE: S=1-3, M=5, L=8, XL=13
- strategic_value: 1-5 (5 = critical to platform goals)
- architecture_fit: 1-5 (5 = perfectly aligned with current architecture)
- execution_risk: 1-5 (1 = no risk, 5 = very high risk)
- dependency_burden: 0-5 (0 = no deps, 5 = many blocking deps)
- subtasks: 3-6 concrete implementation steps
- success_criteria: 2-4 measurable outcomes'''


# ── Ollama caller ─────────────────────────────────────────────────────────────

def _ollama_url() -> str:
    host = OLLAMA_HOST
    if "://" not in host:
        host = f"http://{host}"
    return host


def call_ollama(prompt: str, model: str = OLLAMA_MODEL, retries: int = 2) -> str:
    """Call Ollama and return the response text."""
    payload = json.dumps({
        "model":   model,
        "prompt":  prompt,
        "stream":  False,
        "options": {"temperature": 0.2, "num_predict": 800},
    }).encode()

    for attempt in range(retries + 1):
        try:
            req = urllib.request.Request(
                f"{_ollama_url()}/api/generate",
                data    = payload,
                headers = {"Content-Type": "application/json"},
                method  = "POST",
            )
            with urllib.request.urlopen(req, timeout=90) as resp:
                return json.loads(resp.read()).get("response", "").strip()
        except Exception as exc:
            if attempt < retries:
                time.sleep(2)
                continue
            raise RuntimeError(f"Ollama call failed: {exc}") from exc
    return ""


def _extract_json(text: str) -> dict:
    """Extract first JSON object from a response that may contain prose."""
    # Try direct parse first
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass

    # Find JSON block (possibly wrapped in ```json ... ```)
    for pattern in [r"```json\s*([\s\S]+?)\s*```", r"\{[\s\S]+\}"]:
        m = re.search(pattern, text)
        if m:
            candidate = m.group(1) if "```" in pattern else m.group(0)
            try:
                return json.loads(candidate)
            except json.JSONDecodeError:
                pass

    raise ValueError(f"No valid JSON found in response:\n{text[:300]}")


# ── Translation ───────────────────────────────────────────────────────────────

KNOWN_CATEGORIES = [
    "API", "CLI", "CONFIG", "CORE", "DATA", "DEV", "DOCS", "FLOW",
    "MEDIA", "MONITOR", "OPS", "PERF", "REFACTOR", "SCALE",
    "SECURITY", "TESTING", "UI", "UX", "UTIL",
]


def translate_requirement(requirement: str) -> dict:
    """
    Translate a natural language requirement into a structured roadmap item.

    Returns a dict ready to pass to PlaneAPI.upsert_issue() or write as markdown.
    """
    prompt = TRANSLATION_PROMPT.format(
        requirement = requirement.strip(),
        categories  = ", ".join(KNOWN_CATEGORIES),
    )

    print(f"  Translating via {OLLAMA_MODEL}...", flush=True)
    raw = call_ollama(prompt)

    try:
        item = _extract_json(raw)
    except ValueError as exc:
        print(f"  WARNING: {exc}", file=sys.stderr)
        # Fallback: return minimal structured item
        return {
            "title":        requirement[:80],
            "description":  requirement,
            "category":     "UTIL",
            "type":         "Feature",
            "priority":     "Medium",
            "loe":          "M",
            "estimate_points": 5,
            "labels":       ["feature"],
            "subtasks":     [],
            "success_criteria": [],
            "_raw":         raw,
        }

    # Normalize and validate key fields
    item.setdefault("category", "UTIL")
    item.setdefault("type",     "Feature")
    item.setdefault("priority", "Medium")
    item.setdefault("loe",      "M")
    item.setdefault("estimate_points", 5)
    item.setdefault("labels",   ["feature"])
    item.setdefault("subtasks", [])
    item.setdefault("success_criteria", [])

    if item["category"].upper() not in KNOWN_CATEGORIES:
        item["category"] = "UTIL"

    return item


def _next_id(category: str) -> str:
    """Suggest the next RM-CATEGORY-NNN ID by scanning ITEMS directory."""
    items_dir = _REPO_ROOT / "docs" / "roadmap" / "ITEMS"
    prefix    = f"RM-{category.upper()}-"
    existing  = []
    for p in items_dir.glob(f"{prefix}*.md"):
        m = re.search(r"-(\d+)\.md$", p.name)
        if m:
            existing.append(int(m.group(1)))
    next_n = (max(existing) + 1) if existing else 1
    return f"{prefix}{next_n:03d}"


def print_item(item: dict) -> None:
    """Pretty-print a translated item."""
    print(f"\n{'─'*60}")
    print(f"  ID:         {item.get('id_suggestion', '(auto)')}")
    print(f"  Title:      {item.get('title', '')}")
    print(f"  Category:   {item.get('category', '')}  |  Type: {item.get('type', '')}")
    print(f"  Priority:   {item.get('priority', '')}  |  LOE: {item.get('loe', '')}  |  Points: {item.get('estimate_points', '?')}")
    print(f"  Risk:       {item.get('risk_level', '')}  |  Biz value: {item.get('business_value', '?')}/10")
    print(f"  Labels:     {', '.join(item.get('labels', []))}")
    print(f"\n  Description:\n    {item.get('description', '')}")
    crit = item.get("success_criteria", [])
    if crit:
        print(f"\n  Success criteria:")
        for c in crit:
            print(f"    ✓ {c}")
    tasks = item.get("subtasks", [])
    if tasks:
        print(f"\n  Subtasks:")
        for i, t in enumerate(tasks, 1):
            print(f"    {i}. {t}")
    print(f"{'─'*60}")


def create_in_plane(item: dict, api: PlaneAPI) -> dict:
    """Push the translated item to Plane."""
    issue, created = api.upsert_issue(
        external_id = item.get("id_suggestion") or _next_id(item.get("category", "UTIL")),
        title       = item["title"],
        description = item.get("description", ""),
        state_name  = "Accepted",
        category    = item.get("category", "UTIL"),
        priority    = item.get("priority", "Medium"),
    )
    verb = "created" if created else "updated"
    print(f"  Plane: issue {verb} → ID {issue.get('id', '?')}")
    return issue


def create_markdown(item: dict, dry_run: bool = False) -> Path:
    """Write the translated item as a markdown file in docs/roadmap/ITEMS/."""
    rm_id    = item.get("id_suggestion") or _next_id(item.get("category", "UTIL"))
    filename = f"{rm_id}.md"
    path     = _REPO_ROOT / "docs" / "roadmap" / "ITEMS" / filename

    if path.exists():
        print(f"  Markdown: {filename} already exists, skipping")
        return path

    subtasks_md = "\n".join(f"- {t}" for t in item.get("subtasks", []))
    criteria_md = "\n".join(f"- {c}" for c in item.get("success_criteria", []))

    content = f"""# {rm_id}

- **ID:** `{rm_id}`
- **Title:** {item['title']}
- **Category:** `{item.get('category', 'UTIL')}`
- **Type:** `{item.get('type', 'Feature')}`
- **Status:** `Accepted`
- **Maturity:** `M0`
- **Priority:** `{item.get('priority', 'Medium')}`
- **Priority class:** `{item.get('priority_class', 'P3')}`
- **Queue rank:** `TBD`
- **Target horizon:** `{item.get('target_horizon', 'soon')}`
- **LOE:** `{item.get('loe', 'M')}`
- **Strategic value:** `{item.get('strategic_value', 3)}`
- **Architecture fit:** `{item.get('architecture_fit', 3)}`
- **Execution risk:** `{item.get('execution_risk', 2)}`
- **Dependency burden:** `{item.get('dependency_burden', 0)}`
- **Readiness:** `{item.get('readiness', 'near')}`

## Description

{item.get('description', '')}

## Success criteria

{criteria_md or '- (define before starting)'}

## Subtasks

{subtasks_md or '- (break down during sprint planning)'}

## Dependencies

{', '.join(item.get('dependencies', [])) or '- no external blocking dependencies'}

## Status transition notes

- Expected next status: `In progress`
- Transition condition: implementation started
- Validation / closeout condition: success criteria verified

## Notes

{item.get('notes', 'Self-contained task — assess for autonomous executor suitability.')}
Business value: {item.get('business_value', '?')}/10 · Risk: {item.get('risk_level', '?')}
"""

    if not dry_run:
        path.write_text(content, encoding="utf-8")
        print(f"  Markdown: wrote {filename}")
    else:
        print(f"  [DRY] would write {filename}")
    return path


# ── CLI ───────────────────────────────────────────────────────────────────────

def main() -> None:
    parser = argparse.ArgumentParser(
        description="Translate natural language requirements → structured Plane items (uses local Ollama)"
    )
    parser.add_argument("requirement", nargs="*", help="Requirement text")
    parser.add_argument("--create",      action="store_true", help="Create issue in Plane after translating")
    parser.add_argument("--markdown",    action="store_true", help="Also write a markdown file in docs/roadmap/ITEMS/")
    parser.add_argument("--dry-run",     action="store_true", help="Translate but don't write anything")
    parser.add_argument("--file",        metavar="FILE",      help="File with one requirement per line")
    parser.add_argument("--interactive", action="store_true", help="Interactive REPL mode")
    parser.add_argument("--stdin",       action="store_true", help="Read requirements from stdin")
    parser.add_argument("--model",       default="", help="Ollama model override")
    parser.add_argument("--url",         default=os.environ.get("PLANE_URL",        "http://localhost:8000"))
    parser.add_argument("--token",       default=os.environ.get("PLANE_API_TOKEN",  ""))
    parser.add_argument("--workspace",   default=os.environ.get("PLANE_WORKSPACE",  "iap"))
    parser.add_argument("--project",     default=os.environ.get("PLANE_PROJECT_ID", ""))
    args = parser.parse_args()

    global OLLAMA_MODEL
    if args.model:
        OLLAMA_MODEL = args.model

    api: PlaneAPI | None = None
    if args.create and not args.dry_run:
        api = PlaneAPI(
            base_url   = args.url,
            api_token  = args.token,
            workspace  = args.workspace,
            project_id = args.project,
        )
        if not api.health_check():
            print(f"ERROR: Plane not reachable at {args.url}")
            sys.exit(1)

    def process(req: str) -> None:
        print(f"\nRequirement: {req[:100]}{'…' if len(req)>100 else ''}")
        item = translate_requirement(req)
        print_item(item)
        if not args.dry_run:
            if args.create and api:
                create_in_plane(item, api)
            if args.markdown:
                create_markdown(item)

    if args.interactive:
        print("AI Requirement Translator (type 'quit' to exit)")
        print(f"Model: {OLLAMA_MODEL}  |  Ollama: {_ollama_url()}\n")
        while True:
            try:
                req = input("Requirement> ").strip()
            except (KeyboardInterrupt, EOFError):
                break
            if req.lower() in ("quit", "exit", "q"):
                break
            if req:
                process(req)
        return

    if args.stdin:
        for line in sys.stdin:
            line = line.strip()
            if line and not line.startswith("#"):
                process(line)
        return

    if args.file:
        lines = Path(args.file).read_text().splitlines()
        for line in lines:
            line = line.strip()
            if line and not line.startswith("#"):
                process(line)
        return

    if args.requirement:
        req = " ".join(args.requirement)
        process(req)
        return

    parser.print_help()


if __name__ == "__main__":
    main()
