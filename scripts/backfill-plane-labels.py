#!/usr/bin/env python3
"""Block 4.C C4.2 — back-fill labels on Plane issues by RM-* prefix.

Reads every issue in the Plane project, extracts the RM-<PREFIX>-NNN
prefix from `name` (which carries `[RM-PREFIX-NNN] ...`), looks up the
matching label, and PATCHes the issue's label_ids list to add it.

Decisions baked in (per C1 audit gate, operator-approved):
  - Run via framework.plane_connector (Decision 6).
  - 1 req/sec floor (Block 4.B addendum: longer-window throttle on
    issues/-rooted endpoints).
  - Unmatched-prefix policy: CI→CI/CD, DEPLOY→Deployment, MON→MONITOR
    (Decision 7 option c).

Modes:
  --dry-run   plan only, no PATCHes.
  (default)   apply.

Token: read from Vault `secret/plane/api#homepage_token` via the
running vault-server container (no token on argv or stdout).

Run from the Mac Mini:
    /Users/admin/.venv-block-4c/bin/python scripts/backfill-plane-labels.py [--dry-run]
"""
from __future__ import annotations

import argparse
import os
import re
import subprocess
import sys
import time
from collections import Counter, defaultdict
from pathlib import Path

# Add repo root so framework.* imports work
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from framework.plane_connector import PlaneAPI, RateLimitError  # type: ignore

PLANE_URL = "http://localhost:8000"
WORKSPACE = "iap"
PROJECT_ID = "dbcd4476-1e37-4812-a443-0914ec8380fc"

# Operator-approved unmatched-prefix mapping (C1 Decision 7).
UNMATCHED_MAP = {
    "CI": "CI/CD",
    "DEPLOY": "Deployment",
    "MON": "MONITOR",
}

# Pacing
REQ_PER_SEC = 1.0  # 1 req/sec floor; backoff on 429
SLEEP_BETWEEN = 1.0 / REQ_PER_SEC
BACKOFF_429 = 65.0  # 60/min plus a 5s cushion

NAME_RE = re.compile(r"^\[RM-([A-Z0-9-]+?)-\d+\]")


def fetch_token() -> str:
    """Pull the Plane API token from Vault via the running vault-server container.

    Avoids putting the value on argv. The subprocess captures stdout, the value
    is held only as a Python str for the lifetime of this process.
    """
    vault_token_path = Path.home() / ".vault-token"
    if not vault_token_path.is_file():
        sys.exit("ERROR: ~/.vault-token missing")
    vault_token = vault_token_path.read_text().strip()
    cmd = [
        "/opt/homebrew/bin/docker", "exec",
        "-e", f"VAULT_TOKEN={vault_token}",
        "-e", "VAULT_ADDR=http://127.0.0.1:8200",
        "vault-server",
        "vault", "kv", "get", "-field=homepage_token", "secret/plane/api",
    ]
    out = subprocess.check_output(cmd, text=True).strip()
    if not out:
        sys.exit("ERROR: empty token from Vault")
    return out


def extract_prefix(name: str) -> str | None:
    m = NAME_RE.match(name or "")
    return m.group(1).upper() if m else None


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true", help="Plan only, no writes")
    args = ap.parse_args()

    print(f"Plane: {PLANE_URL}  workspace={WORKSPACE}  project={PROJECT_ID}")
    print(f"Mode: {'DRY-RUN' if args.dry_run else 'APPLY'}")
    print(f"Pacing: {REQ_PER_SEC} req/sec floor; 429 backoff {BACKOFF_429}s\n")

    token = fetch_token()
    api = PlaneAPI(
        base_url=PLANE_URL,
        api_token=token,
        workspace=WORKSPACE,
        project_id=PROJECT_ID,
    )

    # Build label name → id map (case-insensitive)
    print("── Inventory ─────────────────────────────────────────────")

    def _with_429_retry(fn, label, max_retries=3):
        """Wrap a connector call in 429 backoff. The connector raises
        RateLimitError on 429 without sleeping; we sleep + retry here."""
        for attempt in range(max_retries + 1):
            try:
                return fn()
            except RateLimitError:
                if attempt == max_retries:
                    raise
                print(f"  RATE  429 on {label}; sleeping {BACKOFF_429}s (attempt {attempt+1}/{max_retries})")
                time.sleep(BACKOFF_429)

    labels = _with_429_retry(api.list_labels, "labels list")
    label_by_name_ci = {l["name"].lower(): l for l in labels}
    print(f"labels in project: {len(labels)}")

    # Paginate issues with pacing between pages to stay under 60/min.
    print("paginating issues (1s between pages, 65s backoff on 429)...")
    issues: list[dict] = []
    cursor = None
    page = 0
    while True:
        page += 1
        cur = cursor
        batch, cursor = _with_429_retry(
            lambda c=cur: api.list_issues(cursor=c, page_size=100),
            f"issues page {page}",
        )
        issues.extend(batch)
        print(f"  page {page}: +{len(batch)} (total {len(issues)})")
        if not cursor:
            break
        time.sleep(SLEEP_BETWEEN)
    print(f"issues in project: {len(issues)}")

    # Bucket by extracted prefix
    by_prefix: dict[str, list[dict]] = defaultdict(list)
    no_prefix: list[dict] = []
    for issue in issues:
        p = extract_prefix(issue.get("name", ""))
        if p is None:
            no_prefix.append(issue)
        else:
            by_prefix[p].append(issue)

    print(f"issues with RM- prefix: {sum(len(v) for v in by_prefix.values())}")
    print(f"issues without RM- prefix: {len(no_prefix)}")
    print(f"distinct prefixes seen: {len(by_prefix)}\n")

    # Compute the label name to apply for each prefix
    print("── Per-prefix plan ───────────────────────────────────────")
    print(f"{'PREFIX':<14} {'ISSUES':>6}  {'LABEL':<14}  RESOLUTION")

    prefix_to_label_name: dict[str, str | None] = {}
    plan_actions: list[tuple[str, str, str]] = []  # (verb, prefix, label)

    for prefix in sorted(by_prefix.keys()):
        count = len(by_prefix[prefix])
        if prefix.lower() in label_by_name_ci:
            label_name = label_by_name_ci[prefix.lower()]["name"]
            prefix_to_label_name[prefix] = label_name
            plan_actions.append(("match-direct", prefix, label_name))
            print(f"{prefix:<14} {count:>6}  {label_name:<14}  direct case-insensitive match")
        elif prefix in UNMATCHED_MAP:
            label_name = UNMATCHED_MAP[prefix]
            if label_name.lower() not in label_by_name_ci:
                print(f"{prefix:<14} {count:>6}  {label_name:<14}  ERROR: mapping target label not present in project")
                prefix_to_label_name[prefix] = None
                continue
            prefix_to_label_name[prefix] = label_name
            plan_actions.append(("match-mapped", prefix, label_name))
            print(f"{prefix:<14} {count:>6}  {label_name:<14}  mapped (Decision 7)")
        else:
            print(f"{prefix:<14} {count:>6}  -               UNMATCHED (no mapping); will skip")
            prefix_to_label_name[prefix] = None

    # Tally per-issue actions
    print("\n── Per-issue plan ────────────────────────────────────────")
    action_counts = Counter()
    issue_actions: list[tuple[str, str, str, str]] = []  # (verb, issue_id, prefix, target_label)

    for prefix, issues_in in by_prefix.items():
        target = prefix_to_label_name.get(prefix)
        if not target:
            for i in issues_in:
                action_counts["skip-unmatched-prefix"] += 1
                issue_actions.append(("skip-unmatched-prefix", i["id"], prefix, ""))
            continue
        target_id = label_by_name_ci[target.lower()]["id"]
        for i in issues_in:
            current = set(i.get("labels") or [])
            if target_id in current:
                action_counts["skip-already-labeled"] += 1
                issue_actions.append(("skip-already-labeled", i["id"], prefix, target))
            else:
                action_counts["apply"] += 1
                issue_actions.append(("apply", i["id"], prefix, target))

    for i in no_prefix:
        action_counts["skip-no-prefix"] += 1

    for verb, n in sorted(action_counts.items()):
        print(f"  {verb:<26} {n}")
    total_writes = action_counts["apply"]
    print(f"\nplanned PATCHes (live mode): {total_writes}")
    est_seconds = total_writes * SLEEP_BETWEEN
    print(f"estimated wall time at {REQ_PER_SEC} req/sec: ~{int(est_seconds//60)}m {int(est_seconds%60)}s")

    if args.dry_run:
        print("\nDRY-RUN complete; no writes. Re-run without --dry-run to apply.")
        return 0

    # Apply
    print("\n── Applying ──────────────────────────────────────────────")
    applied = 0
    failed = 0
    last_progress = 0
    rate_limit_hits = 0

    # Map name→id once for fast lookup
    label_id_by_target: dict[str, str] = {n.lower(): l["id"] for n, l in (
        (l["name"], l) for l in labels
    )}
    # Refresh in case mappings target labels with mixed-case names
    for l in labels:
        label_id_by_target[l["name"].lower()] = l["id"]

    for verb, issue_id, prefix, target in issue_actions:
        if verb != "apply":
            continue
        target_id = label_id_by_target[target.lower()]
        # Re-fetch the issue's current labels to avoid stale-cache races
        try:
            issue = api.get_issue(issue_id)
        except Exception as e:
            print(f"  WARN  {issue_id} GET failed: {e}")
            failed += 1
            continue
        current = list(issue.get("labels") or [])
        if target_id in current:
            applied += 1  # treat as already-applied success
            continue
        new_labels = current + [target_id]
        try:
            api.update_issue(issue_id, {"label_ids": new_labels})
            applied += 1
        except RateLimitError:
            rate_limit_hits += 1
            print(f"  RATE  429 hit; sleeping {BACKOFF_429}s before retry")
            time.sleep(BACKOFF_429)
            try:
                api.update_issue(issue_id, {"label_ids": new_labels})
                applied += 1
            except Exception as e:
                print(f"  FAIL  {issue_id}: {e}")
                failed += 1
        except Exception as e:
            print(f"  FAIL  {issue_id}: {e}")
            failed += 1

        # Pacing
        time.sleep(SLEEP_BETWEEN)

        # Progress every 50 applied
        if applied - last_progress >= 50:
            print(f"  ...progress: {applied}/{total_writes} applied, {failed} failed, {rate_limit_hits} 429s")
            last_progress = applied

    print(f"\n── Result ────────────────────────────────────────────────")
    print(f"applied:        {applied}")
    print(f"failed:         {failed}")
    print(f"429 backoffs:   {rate_limit_hits}")
    print(f"target writes:  {total_writes}")
    return 0 if failed == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
