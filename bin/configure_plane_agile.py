#!/usr/bin/env python3
"""Configure Plane CE with Agile (Scrum/Kanban) + PMP best practices.

Idempotent — safe to run multiple times. Skips anything that already exists.

Usage:
    # Configure everything
    python3 bin/configure_plane_agile.py

    # Only set up states
    python3 bin/configure_plane_agile.py --states

    # Only create cycles (sprints)
    python3 bin/configure_plane_agile.py --cycles

    # Show current project configuration
    python3 bin/configure_plane_agile.py --show
"""
from __future__ import annotations

import argparse
import json
import os
import sys
import time
from datetime import date, timedelta
from pathlib import Path
from typing import Any, Optional

_REPO_ROOT = Path(os.environ.get("REPO_ROOT", Path(__file__).parent.parent))
sys.path.insert(0, str(_REPO_ROOT))

from framework.plane_connector import PlaneAPI


# ── Agile workflow states ─────────────────────────────────────────────────────
# Matches Scrum board columns + PMP phase gates

AGILE_STATES = [
    # group: backlog
    {"name": "Backlog",     "color": "#64748b", "group": "backlog",    "sequence": 1},
    # group: unstarted
    {"name": "Ready",       "color": "#3b82f6", "group": "unstarted",  "sequence": 2},
    # group: started
    {"name": "In Progress", "color": "#f59e0b", "group": "started",    "sequence": 3},
    {"name": "In Review",   "color": "#8b5cf6", "group": "started",    "sequence": 4},
    {"name": "Testing",     "color": "#06b6d4", "group": "started",    "sequence": 5},
    # group: completed
    {"name": "Done",        "color": "#10b981", "group": "completed",  "sequence": 6},
    # group: cancelled
    {"name": "Cancelled",   "color": "#ef4444", "group": "cancelled",  "sequence": 7},
    {"name": "Deferred",    "color": "#9ca3af", "group": "cancelled",  "sequence": 8},
]

# ── Labels (Agile + PMP tagging) ──────────────────────────────────────────────

AGILE_LABELS = [
    # Type
    {"name": "feature",        "color": "#3b82f6"},
    {"name": "bug",            "color": "#ef4444"},
    {"name": "enhancement",    "color": "#8b5cf6"},
    {"name": "technical-debt", "color": "#f97316"},
    {"name": "spike",          "color": "#14b8a6"},
    {"name": "chore",          "color": "#6b7280"},
    # Agile signals
    {"name": "quick-win",      "color": "#10b981"},
    {"name": "blocked",        "color": "#dc2626"},
    {"name": "needs-review",   "color": "#f59e0b"},
    {"name": "high-priority",  "color": "#ef4444"},
    # PMP / PM signals
    {"name": "risk",           "color": "#b45309"},
    {"name": "dependency",     "color": "#7c3aed"},
    {"name": "milestone",      "color": "#0284c7"},
    {"name": "compliance",     "color": "#065f46"},
    # Tech categories (supplement Plane labels for this repo)
    {"name": "api",            "color": "#3b82f6"},
    {"name": "cli",            "color": "#7c3aed"},
    {"name": "data",           "color": "#0891b2"},
    {"name": "docs",           "color": "#64748b"},
    {"name": "infra",          "color": "#b45309"},
    {"name": "media",          "color": "#db2777"},
    {"name": "security",       "color": "#dc2626"},
    {"name": "testing",        "color": "#65a30d"},
    {"name": "ui-ux",          "color": "#e879f9"},
]

# ── Sprint / Cycle templates (2-week sprints) ─────────────────────────────────

def _generate_sprints(n: int = 6, start: date | None = None) -> list[dict]:
    """Generate N 2-week sprint definitions starting from today's Monday."""
    if start is None:
        today = date.today()
        # Round to nearest Monday
        start = today - timedelta(days=today.weekday())
    sprints = []
    for i in range(n):
        sprint_start = start + timedelta(weeks=2 * i)
        sprint_end   = sprint_start + timedelta(days=13)
        sprints.append({
            "name":       f"Sprint {i + 1}",
            "description": f"2-week sprint {'(current)' if i == 0 else f'#{i+1}'}",
            "start_date": sprint_start.isoformat(),
            "end_date":   sprint_end.isoformat(),
        })
    return sprints


# ── Module definitions (epic-level groupings) ─────────────────────────────────

MODULES = [
    {"name": "Core Platform",   "description": "Foundational infrastructure: executors, RAG pipeline, scheduler"},
    {"name": "API & Integrations", "description": "REST APIs, Ollama client, external connectors"},
    {"name": "Media Pipeline",  "description": "Sonarr/Radarr/Plex automation and self-healing"},
    {"name": "Developer Tools", "description": "CLI, config management, debugging utilities"},
    {"name": "Data & Storage",  "description": "Data pipelines, cache layers, state stores"},
    {"name": "Security & Ops",  "description": "Auth, audit logging, monitoring, compliance"},
    {"name": "Testing & QA",    "description": "Test automation, coverage, regression packs"},
    {"name": "Documentation",   "description": "Runbooks, API docs, architecture guides"},
]


# ── Configuration engine ──────────────────────────────────────────────────────

class PlaneConfigurator:
    def __init__(self, api: PlaneAPI) -> None:
        self.api = api

    def configure_states(self) -> dict[str, str]:
        """Create all Agile workflow states. Returns {name: id}."""
        print("Setting up Agile workflow states...")
        existing = {s["name"]: s["id"] for s in self.api.list_states(use_cache=False)}
        result: dict[str, str] = {}

        for state_def in AGILE_STATES:
            name = state_def["name"]
            if name in existing:
                print(f"  ↷ {name} (exists)")
                result[name] = existing[name]
            else:
                try:
                    s = self.api.create_state(name, state_def["color"], state_def["group"])
                    result[name] = s["id"]
                    print(f"  ✚ {name}")
                except Exception as e:
                    print(f"  ✗ {name}: {e}", file=sys.stderr)
        return result

    def configure_labels(self) -> dict[str, str]:
        """Create all Agile + PMP labels. Returns {name: id}."""
        print("Setting up labels...")
        existing = {l["name"]: l["id"] for l in self.api.list_labels(use_cache=False)}
        result: dict[str, str] = {}

        for lbl in AGILE_LABELS:
            name = lbl["name"]
            if name in existing:
                print(f"  ↷ {name} (exists)")
                result[name] = existing[name]
            else:
                try:
                    l = self.api.create_label(name, lbl["color"])
                    result[name] = l["id"]
                    print(f"  ✚ {name}")
                except Exception as e:
                    print(f"  ✗ {name}: {e}", file=sys.stderr)
        return result

    def configure_cycles(self, n: int = 6) -> list[dict]:
        """Create sprint cycles. Returns created cycle summaries."""
        print(f"Creating {n} sprint cycles (2-week sprints)...")
        sprints = _generate_sprints(n)
        created = []

        # Fetch existing cycles
        try:
            existing = self._list_cycles()
            existing_names = {c["name"] for c in existing}
        except Exception:
            existing_names = set()

        for sprint in sprints:
            if sprint["name"] in existing_names:
                print(f"  ↷ {sprint['name']} (exists)")
                continue
            try:
                c = self._create_cycle(sprint)
                created.append({"name": sprint["name"], "id": c.get("id", "")})
                print(f"  ✚ {sprint['name']}  ({sprint['start_date']} → {sprint['end_date']})")
                time.sleep(1.5)  # Plane enforces 60/min rate limit on API tokens
            except Exception as e:
                print(f"  ✗ {sprint['name']}: {e}", file=sys.stderr)
                time.sleep(3)
        return created

    def configure_modules(self) -> list[dict]:
        """Create epic-level modules for large feature groupings."""
        print("Creating project modules (epics)...")
        created = []

        try:
            existing = self._list_modules()
            existing_names = {m["name"] for m in existing}
        except Exception:
            existing_names = set()

        for mod in MODULES:
            if mod["name"] in existing_names:
                print(f"  ↷ {mod['name']} (exists)")
                continue
            time.sleep(1.5)  # Plane enforces 60/min rate limit
            try:
                m = self._create_module(mod)
                created.append({"name": mod["name"], "id": m.get("id", "")})
                print(f"  ✚ {mod['name']}")
            except Exception as e:
                print(f"  ✗ {mod['name']}: {e}", file=sys.stderr)
        return created

    def show_config(self) -> None:
        """Print current project configuration."""
        print(f"\nPlane project: {self.api.project_id}")
        print(f"Workspace:     {self.api.workspace}")
        print(f"API:           {self.api.base_url}\n")

        states = self.api.list_states(use_cache=False)
        print(f"States ({len(states)}):")
        for s in states:
            print(f"  [{s.get('group','?'):10}] {s['name']}")

        labels = self.api.list_labels(use_cache=False)
        print(f"\nLabels ({len(labels)}):")
        for lbl in labels:
            print(f"  {lbl['name']}")

        try:
            cycles = self._list_cycles()
            print(f"\nCycles/Sprints ({len(cycles)}):")
            for c in cycles:
                print(f"  {c['name']}  {c.get('start_date','')} → {c.get('end_date','')}")
        except Exception:
            print("\nCycles: (could not fetch)")

    # ── Internal Plane API calls for cycles + modules ─────────────────────────

    def _list_cycles(self) -> list[dict]:
        return self.api._get(self.api._proj_url("/cycles/")).get("results", [])

    def _create_cycle(self, data: dict) -> dict:
        # Serializer requires project_id (with underscore), not project
        payload = {**data, "project_id": self.api.project_id}
        return self.api._post(self.api._proj_url("/cycles/"), payload)

    def _list_modules(self) -> list[dict]:
        return self.api._get(self.api._proj_url("/modules/")).get("results", [])

    def _create_module(self, data: dict) -> dict:
        # Serializer requires project_id (with underscore), not project
        payload = {**data, "project_id": self.api.project_id}
        return self.api._post(self.api._proj_url("/modules/"), payload)


def main() -> None:
    parser = argparse.ArgumentParser(description="Configure Plane CE with Agile + PMP setup")
    parser.add_argument("--states",  action="store_true", help="Only set up workflow states")
    parser.add_argument("--labels",  action="store_true", help="Only set up labels")
    parser.add_argument("--cycles",  action="store_true", help="Only create sprint cycles")
    parser.add_argument("--modules", action="store_true", help="Only create epic modules")
    parser.add_argument("--show",    action="store_true", help="Show current config")
    parser.add_argument("--sprints", type=int, default=6,  help="Number of sprints to create (default 6)")
    parser.add_argument("--url",      default=os.environ.get("PLANE_URL",        "http://localhost:8000"))
    parser.add_argument("--token",    default=os.environ.get("PLANE_API_TOKEN",  ""))
    parser.add_argument("--workspace",default=os.environ.get("PLANE_WORKSPACE",  "iap"))
    parser.add_argument("--project",  default=os.environ.get("PLANE_PROJECT_ID", ""))
    args = parser.parse_args()

    api = PlaneAPI(
        base_url   = args.url,
        api_token  = args.token,
        workspace  = args.workspace,
        project_id = args.project,
    )

    if not api.health_check():
        print(f"ERROR: Plane not reachable at {api.base_url}")
        print("  → Start: docker compose -f docker/docker-compose-plane.yml up -d")
        sys.exit(1)
    if not api.api_token:
        print("ERROR: PLANE_API_TOKEN not set — create a token in Plane UI: Profile → API Tokens")
        sys.exit(1)
    if not api.project_id:
        print("ERROR: PLANE_PROJECT_ID not set — copy UUID from project URL in Plane UI")
        sys.exit(1)

    cfg = PlaneConfigurator(api)

    if args.show:
        cfg.show_config()
        return

    run_all = not any([args.states, args.labels, args.cycles, args.modules])

    if run_all or args.states:
        cfg.configure_states()

    if run_all or args.labels:
        cfg.configure_labels()

    if run_all or args.cycles:
        cfg.configure_cycles(n=args.sprints)

    if run_all or args.modules:
        cfg.configure_modules()

    print("\n✅ Plane configured with Agile + PMP best practices")
    print(f"   Open: http://localhost:3001/{api.workspace}/projects/{api.project_id}/issues/")


if __name__ == "__main__":
    main()
