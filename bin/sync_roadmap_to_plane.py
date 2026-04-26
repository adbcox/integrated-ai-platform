#!/usr/bin/env python3
"""Sync docs/roadmap/ITEMS/*.md → Plane issues.

Preserves all metadata: RM-* IDs, strategic scores, relationships, structure.
Idempotent — safe to run repeatedly. Creates missing items, updates existing ones.

Usage:
    # First-time setup (create states + labels, then sync all 600)
    python3 bin/sync_roadmap_to_plane.py --init

    # Full sync
    python3 bin/sync_roadmap_to_plane.py

    # Dry run
    python3 bin/sync_roadmap_to_plane.py --dry-run

    # Single item
    python3 bin/sync_roadmap_to_plane.py --id RM-API-100

    # Only items with a specific status
    python3 bin/sync_roadmap_to_plane.py --status "In progress"

    # Only items in a specific category
    python3 bin/sync_roadmap_to_plane.py --category API

    # Verbose (print every update, not just creates)
    python3 bin/sync_roadmap_to_plane.py --verbose
"""
from __future__ import annotations

import argparse
import os
import re
import sys
import time
from pathlib import Path
from typing import Optional

_REPO_ROOT = Path(os.environ.get("REPO_ROOT", Path(__file__).parent.parent))
sys.path.insert(0, str(_REPO_ROOT))

from framework.plane_connector import PlaneAPI

ITEMS_DIR = _REPO_ROOT / "docs" / "roadmap" / "ITEMS"


# ── Markdown parser ───────────────────────────────────────────────────────────

def _field(text: str, name: str) -> str:
    """Extract a bold field value: - **Name:** `value` or - **Name:** value"""
    # Match backtick-quoted or plain value
    m = re.search(
        rf"^\-\s+\*\*{re.escape(name)}[:\*]*\*\*[:\s]+`?([^`\n]+)`?",
        text, re.MULTILINE | re.IGNORECASE,
    )
    return m.group(1).strip() if m else ""


def _section(text: str, heading: str) -> str:
    """Extract content of a ## Heading section."""
    m = re.search(
        rf"^##\s+{re.escape(heading)}\s*\n(.*?)(?=\n##|\Z)",
        text, re.DOTALL | re.MULTILINE,
    )
    return m.group(1).strip() if m else ""


def parse_md_item(path: Path) -> Optional[dict]:
    """Parse a roadmap markdown file into a structured dict."""
    try:
        text = path.read_text(encoding="utf-8")
    except OSError:
        return None

    item_id    = _field(text, "ID") or path.stem
    if not item_id.startswith("RM-"):
        return None

    title      = _field(text, "Title")
    if not title:
        # Fall back to first # heading
        m = re.search(r"^#\s+(.+)", text, re.MULTILINE)
        title = m.group(1).strip() if m else item_id

    description = _section(text, "Description")
    # Enrich description with deliverable info if present
    deliverable = _section(text, "Deliverable")
    if deliverable and deliverable not in description:
        description = f"{description}\n\nDeliverable: {deliverable}".strip()

    # Success criteria
    criteria_raw = _section(text, "Success criteria") or _section(text, "Completion contract")
    success_criteria = [
        line.lstrip("-* ").strip()
        for line in criteria_raw.splitlines()
        if line.strip() and not line.strip().startswith("#")
    ]

    # Dependencies
    deps_raw = _section(text, "Dependencies")
    dependencies = [
        line.lstrip("-* ").strip()
        for line in deps_raw.splitlines()
        if line.strip().startswith("RM-")
    ]

    return {
        "id":               item_id,
        "title":            title,
        "category":         _field(text, "Category"),
        "type":             _field(text, "Type"),
        "status":           _field(text, "Status"),
        "priority":         _field(text, "Priority"),
        "priority_cls":     _field(text, "Priority class"),
        "loe":              _field(text, "LOE"),
        "maturity":         _field(text, "Maturity"),
        "strategic_value":  _field(text, "Strategic value"),
        "architecture_fit": _field(text, "Architecture fit"),
        "execution_risk":   _field(text, "Execution risk"),
        "dependency_burden":_field(text, "Dependency burden"),
        "target_horizon":   _field(text, "Target horizon"),
        "readiness":        _field(text, "Readiness"),
        "description":      description[:3000],
        "success_criteria": success_criteria,
        "dependencies":     dependencies,
        "path":             str(path),
    }


def load_all_items() -> list[dict]:
    """Load and parse all RM-*.md files."""
    items = []
    for md in sorted(ITEMS_DIR.glob("RM-*.md")):
        item = parse_md_item(md)
        if item:
            items.append(item)
    return items


# ── LOE → story points ────────────────────────────────────────────────────────

LOE_POINTS = {"S": 2, "M": 5, "L": 8, "XL": 13, "L-M": 5}

def _loe_points(loe: str) -> int:
    return LOE_POINTS.get(loe.strip(), 3)


# ── Enhanced description builder ──────────────────────────────────────────────

def _build_description(item: dict) -> str:
    """Build a rich Plane description from all markdown metadata."""
    parts = []

    if item["description"]:
        parts.append(item["description"])

    meta_lines = []
    if item["strategic_value"]:
        meta_lines.append(f"Strategic value: {item['strategic_value']}/5")
    if item["architecture_fit"]:
        meta_lines.append(f"Architecture fit: {item['architecture_fit']}/5")
    if item["execution_risk"]:
        meta_lines.append(f"Execution risk: {item['execution_risk']}/5")
    if item["dependency_burden"]:
        meta_lines.append(f"Dependency burden: {item['dependency_burden']}/5")
    if item["target_horizon"]:
        meta_lines.append(f"Target horizon: {item['target_horizon']}")
    if item["readiness"]:
        meta_lines.append(f"Readiness: {item['readiness']}")
    if meta_lines:
        parts.append("**Metadata:** " + " · ".join(meta_lines))

    if item["success_criteria"]:
        criteria = "\n".join(f"- {c}" for c in item["success_criteria"][:5])
        parts.append(f"**Success criteria:**\n{criteria}")

    if item["dependencies"]:
        parts.append(f"**Dependencies:** {', '.join(item['dependencies'])}")

    return "\n\n".join(parts)[:3000]


# ── Sync engine ───────────────────────────────────────────────────────────────

class RoadmapSyncer:
    def __init__(self, api: PlaneAPI, dry_run: bool = False, verbose: bool = False) -> None:
        self.api     = api
        self.dry_run = dry_run
        self.verbose = verbose
        self.created = 0
        self.updated = 0
        self.errors  = 0
        self.skipped = 0

    def sync_item(self, item: dict) -> str:
        """Sync one roadmap item. Returns 'created' | 'updated' | 'skipped' | 'error'."""
        try:
            if self.dry_run:
                print(f"  [DRY] {item['id']}: {item['status']} → {item['title'][:55]}")
                return "skipped"

            description = _build_description(item)

            _, created = self.api.upsert_issue(
                external_id = item["id"],
                title       = item["title"],
                description = description,
                state_name  = item["status"],
                category    = item["category"],
                priority    = item["priority"],
            )
            return "created" if created else "updated"
        except Exception as exc:
            print(f"  ERROR {item['id']}: {exc}", file=sys.stderr)
            return "error"

    def sync_all(self, items: list[dict]) -> None:
        total = len(items)
        print(f"Syncing {total} items to Plane (dry_run={self.dry_run})...")
        t0 = time.monotonic()

        for n, item in enumerate(items, 1):
            result = self.sync_item(item)
            if result == "created":
                self.created += 1
                print(f"  [{n:>3}/{total}] ✚ {item['id']} — {item['title'][:50]}")
            elif result == "updated":
                self.updated += 1
                if self.verbose:
                    print(f"  [{n:>3}/{total}] ↺ {item['id']} — {item['title'][:50]}")
                elif n % 50 == 0:
                    print(f"  [{n:>3}/{total}] ↺ {n} items processed…")
            elif result == "error":
                self.errors += 1
            else:
                self.skipped += 1

            # Light rate-limiting — avoids hammering Plane API
            if n % 10 == 0:
                time.sleep(0.15)

        elapsed = time.monotonic() - t0
        rate = total / elapsed if elapsed > 0 else 0
        print(f"\nFinished in {elapsed:.0f}s ({rate:.1f} items/s)")
        print(f"  ✚ created={self.created}  ↺ updated={self.updated}  "
              f"✗ errors={self.errors}  skip={self.skipped}")


# ── Init helper ───────────────────────────────────────────────────────────────

def init_plane(api: PlaneAPI, items: list[dict]) -> None:
    """First-time setup: create states and all category labels."""
    print("Initializing Plane project (states + labels)...")

    # States
    states = api.ensure_states()
    print(f"  States: {list(states.keys())}")

    # Collect all unique categories from items
    categories = sorted({i["category"] for i in items if i["category"]})
    print(f"  Creating {len(categories)} category labels (bulk)...")
    label_map = api.ensure_labels_bulk(categories)
    for cat, lid in label_map.items():
        print(f"    {cat} → {lid}")

    print("Init complete.")


# ── Connection guard ──────────────────────────────────────────────────────────

def check_connection(api: PlaneAPI) -> bool:
    if not api.health_check():
        print(f"ERROR: Plane not reachable at {api.base_url}")
        print("  Start: docker compose -f docker/docker-compose-plane.yml up -d")
        return False
    if not api.api_token:
        print("ERROR: PLANE_API_TOKEN not set")
        print("  In Plane UI: Profile → API Tokens → create a token")
        return False
    if not api.project_id:
        print("ERROR: PLANE_PROJECT_ID not set")
        print("  In Plane UI: open your project, copy UUID from URL bar")
        return False
    return True


# ── CLI ───────────────────────────────────────────────────────────────────────

def main() -> None:
    parser = argparse.ArgumentParser(description="Sync roadmap markdown items → Plane issues")
    parser.add_argument("--dry-run",  action="store_true", help="Show what would change, without writing")
    parser.add_argument("--init",     action="store_true", help="Create states and labels first (run once)")
    parser.add_argument("--id",       metavar="RM_ID",     help="Sync a single item by RM-* ID")
    parser.add_argument("--status",   metavar="STATUS",    help="Filter by status (e.g. 'In progress')")
    parser.add_argument("--category", metavar="CAT",       help="Filter by category (e.g. API)")
    parser.add_argument("--verbose",  action="store_true", help="Print every update, not just creates")
    parser.add_argument("--url",       default=os.environ.get("PLANE_URL",        "http://localhost:8000"))
    parser.add_argument("--token",     default=os.environ.get("PLANE_API_TOKEN",  ""))
    parser.add_argument("--workspace", default=os.environ.get("PLANE_WORKSPACE",  "iap"))
    parser.add_argument("--project",   default=os.environ.get("PLANE_PROJECT_ID", ""))
    args = parser.parse_args()

    api = PlaneAPI(
        base_url   = args.url,
        api_token  = args.token,
        workspace  = args.workspace,
        project_id = args.project,
    )

    if not check_connection(api):
        sys.exit(1)

    items = load_all_items()
    print(f"Loaded {len(items)} roadmap items from {ITEMS_DIR}")

    if args.init:
        init_plane(api, items)

    # Apply filters
    if args.id:
        items = [i for i in items if i["id"] == args.id]
        if not items:
            print(f"No item found with ID: {args.id}")
            sys.exit(1)
    if args.status:
        items = [i for i in items if i["status"] == args.status]
    if args.category:
        items = [i for i in items if i["category"].upper() == args.category.upper()]

    if not items:
        print("No items match the given filters.")
        return

    syncer = RoadmapSyncer(api, dry_run=args.dry_run, verbose=args.verbose)
    syncer.sync_all(items)


if __name__ == "__main__":
    main()
