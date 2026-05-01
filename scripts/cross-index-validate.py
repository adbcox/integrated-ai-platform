#!/usr/bin/env python3
"""
Cross-index validator: ADR <-> Plane coherence check.
Read-only. Emits gap report and exits 0 (no gaps) or 1 (gaps found).

Usage:
    python3 scripts/cross-index-validate.py [--json] [--verbose] [--quiet]

Environment:
    The script self-bootstraps Plane connection via the same path as
    scripts/plane-sync-from-framework.py — pulls the API token from
    Vault (`secret/plane/api#homepage_token`) using the running
    `vault-server` container, then sets the env vars
    PlaneAPI() expects:
        PLANE_URL         http://localhost:8000
        PLANE_API_TOKEN   (from Vault)
        PLANE_WORKSPACE   iap
        PLANE_PROJECT_ID  dbcd4476-1e37-4812-a443-0914ec8380fc

    If a caller has already set these vars (e.g. CI shell that brought
    in its own PLANE_API_TOKEN), the existing values are honoured.

Exit codes:
    0  no gaps
    1  gaps detected (or unrecoverable Plane rate-limit during fetch)
    2  Plane connection failed (token/URL unreachable)
"""
import argparse
import json
import os
import re
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT))

DECISION_REGISTER = REPO_ROOT / "docs" / "DECISION_REGISTER.md"

# Match scripts/plane-sync-from-framework.py defaults so the two stay in
# step. If the operator moves Plane, both scripts get updated together.
PLANE_URL_DEFAULT = "http://localhost:8000"
PLANE_WORKSPACE_DEFAULT = "iap"
PLANE_PROJECT_ID_DEFAULT = "dbcd4476-1e37-4812-a443-0914ec8380fc"


def load_adrs() -> list:
    adrs = []
    for line in DECISION_REGISTER.read_text().splitlines():
        # Format: | [A-NNN](adr/ADR-A-NNN[-slug].md) | Title | Summary |
        m = re.match(r"\|\s*\[A-(\d+)\]\(adr/ADR-A-\d+[^)]*\.md\)\s*\|\s*(.+?)\s*\|", line)
        if m:
            adr_id = f"ADR-A-{m.group(1).zfill(3)}"
            adrs.append({
                "id":     adr_id,
                "title":  m.group(2).strip(),
                "status": "Accepted",
            })
    return adrs


def fetch_plane_token() -> str:
    """Pull the Plane API token from Vault via the running vault-server
    container. Mirrors scripts/plane-sync-from-framework.py.fetch_token().
    """
    vt = Path.home() / ".vault-token"
    candidate_tokens: list[str] = []
    if vt.is_file():
        tok = vt.read_text().strip()
        if tok:
            candidate_tokens.append(tok)
    fallback_keys = Path.home() / "vault-init-keys-NEW-20260430.txt"
    if fallback_keys.is_file():
        for line in fallback_keys.read_text().splitlines():
            if line.startswith("Initial Root Token:"):
                candidate_tokens.append(line.split(":", 1)[1].strip())
                break
    last_err = ""
    for tok in candidate_tokens:
        try:
            out = subprocess.check_output(
                [
                    "/opt/homebrew/bin/docker", "exec",
                    "-e", f"VAULT_TOKEN={tok}",
                    "-e", "VAULT_ADDR=http://127.0.0.1:8200",
                    "vault-server",
                    "vault", "kv", "get", "-field=homepage_token", "secret/plane/api",
                ],
                text=True,
                stderr=subprocess.PIPE,
            ).strip()
            if out:
                return out
        except subprocess.CalledProcessError as exc:
            last_err = (exc.stderr or "").strip()
            continue
    sys.exit(
        "ERROR: could not read Plane API token from Vault. "
        f"Last error: {last_err or '(none)'}"
    )


def ensure_plane_env(quiet: bool = False) -> None:
    """Populate PLANE_* env vars if the caller didn't set them.
    PLANE_API_TOKEN comes from Vault when missing; the rest get
    sensible defaults that match plane-sync-from-framework.py."""
    if not os.environ.get("PLANE_URL"):
        os.environ["PLANE_URL"] = PLANE_URL_DEFAULT
    if not os.environ.get("PLANE_WORKSPACE"):
        os.environ["PLANE_WORKSPACE"] = PLANE_WORKSPACE_DEFAULT
    if not os.environ.get("PLANE_PROJECT_ID"):
        os.environ["PLANE_PROJECT_ID"] = PLANE_PROJECT_ID_DEFAULT
    if not os.environ.get("PLANE_API_TOKEN"):
        if not quiet:
            print("  (fetching Plane API token from Vault …)")
        os.environ["PLANE_API_TOKEN"] = fetch_plane_token()


def load_plane_adr_issues() -> dict:
    from framework.plane_connector import PlaneAPI, RateLimitError
    api = PlaneAPI()
    try:
        issues = api.list_all_issues()
    except RateLimitError as exc:
        print(f"RATE-LIMIT: {exc}", file=sys.stderr)
        sys.exit(1)
    return {i["external_id"]: i
            for i in issues
            if (i.get("external_id") or "").startswith("ADR-")}


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--verbose", action="store_true")
    ap.add_argument("--quiet", action="store_true",
                    help="suppress progress output (CI use)")
    args = ap.parse_args()

    ensure_plane_env(quiet=args.quiet or args.json)

    adrs             = load_adrs()
    plane_adr_issues = load_plane_adr_issues()

    gaps, covered = [], []
    for adr in adrs:
        if adr["status"].lower() not in ("accepted", "superseded"):
            continue
        if adr["id"] in plane_adr_issues:
            covered.append(adr["id"])
        else:
            gaps.append(adr)

    report = {
        "adrs_checked":             len(adrs),
        "adrs_covered_in_plane":    len(covered),
        "adrs_missing_plane_issue": len(gaps),
        "gaps":    gaps,
        "covered": covered,
    }

    if args.json:
        print(json.dumps(report, indent=2))
    elif not args.quiet:
        print(f"ADRs checked:         {report['adrs_checked']}")
        print(f"Tracked in Plane:     {report['adrs_covered_in_plane']}")
        print(f"Missing Plane issue:  {report['adrs_missing_plane_issue']}")
        if args.verbose or gaps:
            for g in gaps:
                print(f"  GAP: {g['id']} ({g['status']}) — {g['title']}")
    elif gaps:
        # quiet mode: only emit gaps
        for g in gaps:
            print(f"GAP: {g['id']} — {g['title']}", file=sys.stderr)

    return 0 if not gaps else 1


if __name__ == "__main__":
    sys.exit(main())
