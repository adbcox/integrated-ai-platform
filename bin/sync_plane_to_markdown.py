#!/usr/bin/env python3
"""Sync Plane issue status changes → docs/roadmap/ITEMS/*.md + git commit.

Usage:
    # Check for changes (no commit)
    python3 bin/sync_plane_to_markdown.py --dry-run

    # Apply changes and commit
    python3 bin/sync_plane_to_markdown.py

    # Watch mode: poll every N seconds
    python3 bin/sync_plane_to_markdown.py --watch 60

    # Only sync one item
    python3 bin/sync_plane_to_markdown.py --id RM-API-100
"""
from __future__ import annotations

import argparse
import os
import re
import subprocess
import sys
import time
from pathlib import Path
from typing import Optional

_REPO_ROOT = Path(os.environ.get("REPO_ROOT", Path(__file__).parent.parent))
sys.path.insert(0, str(_REPO_ROOT))

from framework.plane_connector import PlaneAPI, PLANE_TO_MARKDOWN_STATE

ITEMS_DIR = _REPO_ROOT / "docs" / "roadmap" / "ITEMS"


# ── Markdown field updater ────────────────────────────────────────────────────

def read_md_status(path: Path) -> Optional[str]:
    m = re.search(r"^\- \*\*Status:\*\*\s+`([^`]+)`", path.read_text(), re.MULTILINE)
    return m.group(1).strip() if m else None


def write_md_status(path: Path, new_status: str) -> bool:
    """Update the Status field in a markdown file. Returns True if changed."""
    text = path.read_text(encoding="utf-8")
    pattern = r"(^\- \*\*Status:\*\*\s+`)[^`]+(`)"
    new_text, count = re.subn(pattern, rf"\g<1>{new_status}\g<2>", text, flags=re.MULTILINE)
    if count == 0 or new_text == text:
        return False
    path.write_text(new_text, encoding="utf-8")
    return True


def extract_id_from_plane_name(name: str) -> Optional[str]:
    """Extract RM-* ID from '[RM-API-100] Title' format."""
    m = re.match(r"^\[(RM-[A-Z0-9/-]+)\]", name)
    return m.group(1) if m else None


def find_md_path(rm_id: str) -> Optional[Path]:
    """Find the markdown file for an RM-* ID."""
    p = ITEMS_DIR / f"{rm_id}.md"
    if p.exists():
        return p
    # Some items have extra suffix like RM-API-100_TITLE.md — try glob
    matches = list(ITEMS_DIR.glob(f"{rm_id}*.md"))
    return matches[0] if matches else None


# ── Git commit ────────────────────────────────────────────────────────────────

def git_commit(changed_paths: list[Path], message: str) -> bool:
    try:
        rel_paths = [str(p.relative_to(_REPO_ROOT)) for p in changed_paths]
        subprocess.run(["git", "add"] + rel_paths, cwd=_REPO_ROOT, check=True, capture_output=True)
        subprocess.run(
            ["git", "commit", "-m", message],
            cwd=_REPO_ROOT, check=True, capture_output=True,
        )
        return True
    except subprocess.CalledProcessError as e:
        print(f"  git error: {e.stderr.decode()[:120]}", file=sys.stderr)
        return False


# ── Sync engine ───────────────────────────────────────────────────────────────

class PlaneToMarkdownSyncer:
    def __init__(self, api: PlaneAPI, dry_run: bool = False) -> None:
        self.api     = api
        self.dry_run = dry_run

    def sync(self, id_filter: str | None = None) -> int:
        """
        Fetch all Plane issues, compare status with markdown.
        Returns number of files updated.
        """
        print("Fetching issues from Plane...")
        t0    = time.monotonic()
        issues = self.api.list_all_issues()
        states = {s["id"]: s["name"] for s in self.api.list_states(use_cache=False)}
        print(f"  {len(issues)} issues fetched in {time.monotonic()-t0:.1f}s")

        changed: list[Path] = []
        change_log: list[str] = []

        for issue in issues:
            name = issue.get("name", "")
            rm_id = extract_id_from_plane_name(name)
            if not rm_id:
                continue
            if id_filter and rm_id != id_filter:
                continue

            plane_state_name = states.get(issue.get("state", ""), "")
            if not plane_state_name:
                continue

            md_status = PLANE_TO_MARKDOWN_STATE.get(plane_state_name)
            if not md_status:
                continue

            md_path = find_md_path(rm_id)
            if not md_path:
                continue

            current_md_status = read_md_status(md_path)
            if current_md_status == md_status:
                continue

            print(f"  {rm_id}: {current_md_status!r} → {md_status!r} (Plane: {plane_state_name!r})")
            if not self.dry_run:
                if write_md_status(md_path, md_status):
                    changed.append(md_path)
                    change_log.append(f"{rm_id}: {current_md_status} → {md_status}")
            else:
                print(f"    [DRY] would update {md_path.name}")

        if not self.dry_run and changed:
            summary = ", ".join(change_log[:5])
            if len(change_log) > 5:
                summary += f" (+{len(change_log)-5} more)"
            msg = f"sync: update {len(changed)} roadmap statuses from Plane\n\n{summary}"
            ok = git_commit(changed, msg)
            if ok:
                print(f"\nCommitted {len(changed)} file(s): {msg.splitlines()[0]}")
            else:
                print(f"\nUpdated {len(changed)} file(s) but git commit failed — check repo state")
        elif not changed:
            print("  No status changes to sync.")

        return len(changed)

    def watch(self, interval: int) -> None:
        print(f"Watch mode: polling Plane every {interval}s (Ctrl+C to stop)")
        while True:
            n = self.sync()
            if n:
                print(f"  Synced {n} change(s)")
            time.sleep(interval)


def main() -> None:
    parser = argparse.ArgumentParser(description="Sync Plane status changes → markdown + git")
    parser.add_argument("--dry-run", action="store_true", help="Show changes without writing")
    parser.add_argument("--id",      metavar="RM_ID",    help="Sync one item by RM-* ID")
    parser.add_argument("--watch",   type=int, metavar="SEC", help="Poll interval in seconds")
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
        print("ERROR: Plane not reachable at", api.base_url)
        sys.exit(1)

    syncer = PlaneToMarkdownSyncer(api, dry_run=args.dry_run)

    if args.watch:
        syncer.watch(args.watch)
    else:
        syncer.sync(id_filter=args.id)


if __name__ == "__main__":
    main()
