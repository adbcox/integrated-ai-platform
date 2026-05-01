#!/usr/bin/env python3
"""
Backfill missing ADR-* stub issues in Plane.

Idempotent. Walks docs/DECISION_REGISTER.md for ADR ids + titles, looks up
which external_ids already exist in Plane, and creates a stub for each gap.

Stub shape mirrors the originals created in Phase 14 D-XINDEX (commit
410ed6f):
    external_id  ADR-A-NNN
    name         "[ADR-A-NNN] <title from DR>"
    state        "Done" (per Accepted→Done sync mapping)
    description  brief; reference to docs/adr/<file>.md
    module       none (ADR stubs are not in phase modules)

Usage:
    python3 scripts/plane-backfill-adr-stubs.py [--dry-run]

Reads token from Vault via the running vault-server container (same path
plane-sync-from-framework.py uses).
"""
from __future__ import annotations

import argparse
import os
import re
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(REPO_ROOT))

DECISION_REGISTER = REPO_ROOT / "docs" / "DECISION_REGISTER.md"
ADR_DIR_REL       = "docs/adr"
PLANE_URL         = "http://localhost:8000"
WORKSPACE         = "iap"
PROJECT_ID        = "dbcd4476-1e37-4812-a443-0914ec8380fc"


def fetch_token() -> str:
    """Pull Plane API token from Vault (same path as plane-sync)."""
    fallback_keys = Path.home() / "vault-init-keys-NEW-20260430.txt"
    if not fallback_keys.is_file():
        sys.exit(f"ERROR: {fallback_keys} not found")
    root = ""
    for line in fallback_keys.read_text().splitlines():
        if line.startswith("Initial Root Token:"):
            root = line.split(":", 1)[1].strip()
            break
    if not root:
        sys.exit("ERROR: could not parse root token from vault keys file")
    out = subprocess.check_output(
        [
            "/opt/homebrew/bin/docker", "exec",
            "-e", f"VAULT_TOKEN={root}",
            "-e", "VAULT_ADDR=http://127.0.0.1:8200",
            "vault-server",
            "vault", "kv", "get", "-field=homepage_token", "secret/plane/api",
        ],
        text=True,
        stderr=subprocess.PIPE,
    ).strip()
    if not out:
        sys.exit("ERROR: empty token from Vault")
    return out


def parse_adrs() -> list[dict]:
    """Return [{id, title, file_rel}] for every ADR row in DECISION_REGISTER."""
    rows = []
    pattern = re.compile(
        r"\|\s*\[A-(\d+)\]\(adr/(ADR-A-\d+[^)]*\.md)\)\s*\|\s*(.+?)\s*\|"
    )
    for line in DECISION_REGISTER.read_text().splitlines():
        m = pattern.match(line)
        if m:
            rows.append({
                "id":       f"ADR-A-{m.group(1).zfill(3)}",
                "file_rel": f"{ADR_DIR_REL}/{m.group(2)}",
                "title":    m.group(3).strip(),
            })
    return rows


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    adrs = parse_adrs()
    print(f"Parsed {len(adrs)} ADR rows from DECISION_REGISTER.md")

    os.environ["PLANE_API_TOKEN"]  = fetch_token()
    os.environ["PLANE_URL"]        = PLANE_URL
    os.environ["PLANE_WORKSPACE"]  = WORKSPACE
    os.environ["PLANE_PROJECT_ID"] = PROJECT_ID

    from framework.plane_connector import PlaneAPI, RateLimitError
    api = PlaneAPI()
    if not api.health_check():
        sys.exit("ERROR: Plane health-check failed")

    try:
        existing_ids = {
            (i.get("external_id") or "")
            for i in api.list_all_issues()
            if (i.get("external_id") or "").startswith("ADR-")
        }
    except RateLimitError as exc:
        sys.exit(f"RATE-LIMIT: {exc}")

    print(f"Plane has {len(existing_ids)} ADR stub issues already")

    gaps = [a for a in adrs if a["id"] not in existing_ids]
    print(f"Missing: {len(gaps)}")
    for a in gaps:
        print(f"  + {a['id']}  {a['title']}")

    if not gaps:
        print("Nothing to do — already up to date.")
        return 0

    if args.dry_run:
        print("\nDRY-RUN: would create the rows above.")
        return 2

    done_id = api.get_state_id("Done")
    if not done_id:
        sys.exit("ERROR: Plane state 'Done' not found")

    created = 0
    for a in gaps:
        desc = (
            f"<p><strong>ADR stub.</strong> Mirrors {a['file_rel']} "
            f"in the repository (canonical source). Created by "
            f"<code>scripts/plane-backfill-adr-stubs.py</code>.</p>"
        )
        try:
            issue = api.create_issue(
                name=f"[{a['id']}] {a['title']}",
                description=desc,
                state_id=done_id,
                priority="none",
                external_id=a["id"],
            )
        except RateLimitError:
            print(f"  RATE-LIMIT during create — partial run; safe to re-run.")
            return 1
        if issue.get("external_id") != a["id"]:
            print(f"  WARN: external_id mismatch on {a['id']} — got "
                  f"{issue.get('external_id')!r}; PATCH may have failed")
            continue
        created += 1
        print(f"  ✓ {a['id']}  id={issue.get('id')}")

    print(f"\nCreated {created}/{len(gaps)} stubs.")
    return 0 if created == len(gaps) else 1


if __name__ == "__main__":
    sys.exit(main())
