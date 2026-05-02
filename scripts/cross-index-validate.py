#!/usr/bin/env python3
"""
Cross-index validator: ADR <-> OpenProject coherence check.
Read-only. Emits gap report and exits 0 (no gaps) or 1 (gaps found).

Replaces the prior Plane-based validator (D-17-04 WP-17-04-05.5,
2026-05-02). The structure is identical — only the source-of-truth
project tracker changed.

Usage:
    python3 scripts/cross-index-validate.py [--json] [--verbose] [--quiet]

Environment:
    The script self-bootstraps OpenProject connection via the same path
    as scripts/openproject-sync-from-framework.py — pulls the API token
    from Vault (`secret/openproject/api#token`) using the running
    `vault-server` container, then sets the env vars
    OpenProjectAPI() expects:
        OPENPROJECT_URL          http://192.168.10.145:8086
        OPENPROJECT_API_TOKEN    (from Vault)
        OPENPROJECT_PROJECT      roadmap

    If a caller has already set these vars (e.g. CI shell that brought
    in its own OPENPROJECT_API_TOKEN), the existing values are honoured.

Exit codes:
    0  no gaps
    1  gaps detected
    2  OpenProject connection failed (token/URL unreachable)
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

# Match scripts/openproject-sync-from-framework.py defaults so the two stay in
# step. If the operator moves OpenProject, both scripts get updated together.
OPENPROJECT_URL_DEFAULT = "http://192.168.10.145:8086"
OPENPROJECT_PROJECT_DEFAULT = "roadmap"


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


def fetch_openproject_token() -> str:
    """Pull the OpenProject API token from Vault via the running vault-server
    container. Mirrors scripts/openproject-sync-from-framework.py.
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
                    "vault", "kv", "get", "-field=token", "secret/openproject/api",
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
        "ERROR: could not read OpenProject API token from Vault. "
        f"Last error: {last_err or '(none)'}"
    )


def ensure_openproject_env(quiet: bool = False) -> None:
    """Populate OPENPROJECT_* env vars if the caller didn't set them.
    OPENPROJECT_API_TOKEN comes from Vault when missing; the rest get
    sensible defaults that match openproject-sync-from-framework.py."""
    if not os.environ.get("OPENPROJECT_URL"):
        os.environ["OPENPROJECT_URL"] = OPENPROJECT_URL_DEFAULT
    if not os.environ.get("OPENPROJECT_PROJECT"):
        os.environ["OPENPROJECT_PROJECT"] = OPENPROJECT_PROJECT_DEFAULT
    if not os.environ.get("OPENPROJECT_API_TOKEN"):
        if not quiet:
            print("  (fetching OpenProject API token from Vault …)")
        os.environ["OPENPROJECT_API_TOKEN"] = fetch_openproject_token()


def load_openproject_adr_workpackages() -> dict:
    from framework.openproject_connector import OpenProjectAPI
    api = OpenProjectAPI()
    try:
        wps = api.list_all_issues()
    except Exception as exc:
        print(f"OPENPROJECT-FETCH-FAILED: {exc}", file=sys.stderr)
        sys.exit(2)
    return {wp["external_id"]: wp
            for wp in wps
            if (wp.get("external_id") or "").startswith("ADR-")}


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--verbose", action="store_true")
    ap.add_argument("--quiet", action="store_true",
                    help="suppress progress output (CI use)")
    args = ap.parse_args()

    ensure_openproject_env(quiet=args.quiet or args.json)

    adrs        = load_adrs()
    op_adr_wps  = load_openproject_adr_workpackages()

    gaps, covered = [], []
    for adr in adrs:
        if adr["status"].lower() not in ("accepted", "superseded"):
            continue
        if adr["id"] in op_adr_wps:
            covered.append(adr["id"])
        else:
            gaps.append(adr)

    report = {
        "adrs_checked":                  len(adrs),
        "adrs_covered_in_openproject":   len(covered),
        "adrs_missing_workpackage":      len(gaps),
        "gaps":    gaps,
        "covered": covered,
    }

    if args.json:
        print(json.dumps(report, indent=2))
    elif not args.quiet:
        print(f"ADRs checked:                {report['adrs_checked']}")
        print(f"Tracked in OpenProject:      {report['adrs_covered_in_openproject']}")
        print(f"Missing OpenProject WP:      {report['adrs_missing_workpackage']}")
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
