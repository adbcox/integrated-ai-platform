#!/usr/bin/env python3
"""D-17-04 WP-17-04-04 — one-way sync from PROJECT_FRAMEWORK.md to OpenProject.

Replaces scripts/plane-sync-from-framework.py (D-16-02.A doctrine
preserved: repo-owned docs are canonical; OpenProject is an operational
overlay). Manual edits made in the OpenProject UI to synced work
packages will be overwritten on the next run; that is intentional. The
OpenProject UI is the right place to attach comments, sub-WPs, and
operational links — not to redefine deliverable scope or status.

What it syncs (1:1 with the Plane sync, structurally):
  - One OpenProject *version* per phase, keyed by name `Phase-NN`.
  - One OpenProject *work package* per phase, keyed by external_id
    (custom field "External ID") `Phase-NN`, summarising the phase
    header.
  - One OpenProject *work package* per deliverable, keyed by external_id
    (e.g. `D-16-02`, `D-16-02.A`, `D-15-08`, `17.A`), associated with
    the phase version.

What it leaves alone:
  - ADR stubs (anything whose external_id starts with `ADR-`).

Idempotency:
  - Versions and WPs are matched by external_id only (versions encode
    external_id as the name itself per OpenProject's lack of native
    external_id support on Versions).
  - Updates are sent as a minimal diff (subject, description, status,
    version association) compared against the live record.

Modes:
  --dry-run   Plan only; print planned creates / updates / no-ops.
              Exits 0 if no changes pending, 2 if changes pending.
              D-16-06's CI hook uses this exit-code contract for drift.
  (default)   Apply the changes.
  --phase N   Limit to a single phase.

Status mapping (markdown -> OpenProject status name):
    DONE                    -> Closed
    IN PROGRESS             -> In progress
    NOT STARTED             -> New
    DEFERRED [...]          -> On hold

Token: pulled from Vault `secret/openproject/api#token` via the running
vault-server container. The token is the iap-sync user's API key
(provisioned by scripts/openproject-mint-iap-sync-token.sh). Token is
never displayed.

Run from the Mac Mini in the block-4c venv:
    /Users/admin/.venv-block-4c/bin/python \\
        scripts/openproject-sync-from-framework.py [--dry-run] [--phase 16]
"""
from __future__ import annotations

import argparse
import os
import re
import subprocess
import sys
import time
from dataclasses import dataclass
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT))

from framework.openproject_connector import (  # type: ignore  # noqa: E402
    OpenProjectAPI,
    RateLimitError,
)

FRAMEWORK_MD = REPO_ROOT / "docs" / "PROJECT_FRAMEWORK.md"

OPENPROJECT_URL = "http://192.168.10.145:8086"
PROJECT_IDENTIFIER = "roadmap"

# Pacing — OpenProject is permissive (~100 req/sec) but we keep a soft
# floor so a runaway loop doesn't saturate the box.
SLEEP_BETWEEN = 0.1
BACKOFF_429 = 65.0


# ── Status mapping ───────────────────────────────────────────────────────────

STATUS_RE = re.compile(r"^(DONE|IN PROGRESS|NOT STARTED|DEFERRED)\b", re.IGNORECASE)

# We pass the canonical Plane-era state name to ensure_states(), which
# returns OpenProject status IDs for {"Backlog","In Progress","Done",
# "Cancelled","On hold"}. Status mapping is centralised in the connector
# (MARKDOWN_TO_OP_STATUS).
STATUS_TO_OP_STATE = {
    "DONE":        "Done",
    "IN PROGRESS": "In Progress",
    "NOT STARTED": "Backlog",
    "DEFERRED":    "On hold",
}


# ── Parsed-row dataclasses (shape preserved from plane-sync-from-framework) ──

@dataclass
class Deliverable:
    phase: int
    external_id: str
    title: str
    status_word: str
    reference: str


@dataclass
class Phase:
    number: int
    header: str
    deliverables: list[Deliverable]


# ── Markdown parsing (verbatim from plane-sync) ──────────────────────────────

ROW_RE = re.compile(
    r"^\|\s*"
    r"(?P<extid>"
    r"D-(?P<phase_d>\d+)-[\w.\-]+"
    r"|"
    r"(?P<phase_t>\d+)\.[A-Z]"
    r")\s*:\s*(?P<title>.+?)\s*"
    r"\|\s*(?P<status>[^|]+?)\s*"
    r"\|\s*(?P<reference>[^|]+?)\s*\|\s*$"
)

PHASE_HEADING_RE = re.compile(r"^##\s+\d+\.\s+(?P<hdr>Phase\s+(?P<n>\d+)[^\n]*)\s*$")


def parse_framework(md_path: Path) -> list[Phase]:
    text = md_path.read_text()
    phases: dict[int, Phase] = {}
    current_phase: int | None = None

    for line in text.splitlines():
        h = PHASE_HEADING_RE.match(line)
        if h:
            n = int(h.group("n"))
            current_phase = n
            phases.setdefault(n, Phase(number=n, header=h.group("hdr"), deliverables=[]))
            continue
        m = ROW_RE.match(line)
        if not m:
            continue
        row_phase = int(m.group("phase_d") or m.group("phase_t"))
        phase_n = row_phase
        phases.setdefault(
            phase_n,
            Phase(number=phase_n, header=f"Phase {phase_n}", deliverables=[]),
        )
        status_word = _normalise_status(m.group("status"))
        if status_word is None:
            print(
                f"WARN: unrecognised status {m.group('status')!r} for "
                f"{m.group('extid')} — skipping row",
                file=sys.stderr,
            )
            continue
        if current_phase is not None and current_phase != phase_n:
            continue
        phases[phase_n].deliverables.append(
            Deliverable(
                phase=phase_n,
                external_id=m.group("extid"),
                title=m.group("title").strip(),
                status_word=status_word,
                reference=m.group("reference").strip(),
            )
        )
    return [phases[n] for n in sorted(phases.keys())]


def _normalise_status(raw: str) -> str | None:
    raw = raw.strip()
    m = STATUS_RE.match(raw)
    if not m:
        return None
    return m.group(1).upper()


# ── Vault token ──────────────────────────────────────────────────────────────

def fetch_token() -> str:
    """Pull the OpenProject iap-sync token from Vault via the running
    vault-server container. Avoids putting the value on argv."""
    vt = Path.home() / ".vault-token"
    if vt.is_file():
        token = vt.read_text().strip()
    else:
        token = ""
    fallback_keys = Path.home() / "vault-init-keys-NEW-20260430.txt"
    candidate_tokens: list[str] = []
    if token:
        candidate_tokens.append(token)
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
    sys.exit(f"ERROR: could not read OpenProject API token from Vault. Last error: {last_err or '(none)'}")


# ── Diff / sync logic ────────────────────────────────────────────────────────

def _description_html(d: Deliverable) -> str:
    return (
        f"<p><strong>Phase {d.phase} deliverable.</strong> "
        f"This work package mirrors PROJECT_FRAMEWORK.md and is rewritten by "
        f"<code>scripts/openproject-sync-from-framework.py</code>. "
        f"Edit the markdown table, not this WP.</p>"
        f"<p>Reference: <code>{_html_escape(d.reference)}</code></p>"
    )


def _phase_description_html(p: Phase) -> str:
    return (
        f"<p><strong>{_html_escape(p.header)}</strong></p>"
        f"<p>This work package mirrors PROJECT_FRAMEWORK.md §"
        f"{'7' if p.number == 15 else '8' if p.number == 16 else '?'} "
        f"and is rewritten by <code>scripts/openproject-sync-from-framework.py</code>.</p>"
    )


def _html_escape(s: str) -> str:
    return (
        s.replace("&", "&amp;")
         .replace("<", "&lt;")
         .replace(">", "&gt;")
    )


@dataclass
class PlanRow:
    kind: str          # "module" | "phase-issue" | "deliverable-issue"
    extid: str
    label: str
    action: str        # "create" | "update" | "no-op"
    drift: dict


def _html_to_markdown(s: str) -> str:
    """Reduce the sync's small HTML envelope to the markdown OpenProject
    will store. The connector uses the same conversion before PATCH;
    keeping it duplicated here avoids importing _strip_tags privately."""
    s = (s or "").strip()
    if s.startswith("<div>") and s.endswith("</div>"):
        s = s[len("<div>"):-len("</div>")]
    s = re.sub(r"<strong>(.*?)</strong>", r"**\1**", s, flags=re.DOTALL)
    s = re.sub(r"<code>(.*?)</code>", r"`\1`", s, flags=re.DOTALL)
    s = re.sub(r"<p>(.*?)</p>", r"\1\n\n", s, flags=re.DOTALL)
    s = re.sub(r"<[^>]+>", "", s)
    return s.strip()


def _normalise_md(s: str) -> str:
    return re.sub(r"\s+", " ", (s or "").strip())


def _diff_issue(live: dict, want_state_id: int, want_name: str, want_desc: str) -> dict:
    drift: dict = {}
    if (live.get("state") or 0) != want_state_id:
        drift["state"] = want_state_id
    if (live.get("name") or "") != want_name:
        drift["name"] = want_name
    # Compare on raw markdown — OpenProject stores markdown but renders
    # HTML with op-uc-* class wrappers on read, which would always
    # diff against our plain HTML envelope.
    want_md = _html_to_markdown(want_desc)
    have_md = live.get("description_raw") or ""
    if _normalise_md(have_md) != _normalise_md(want_md):
        drift["description_html"] = want_desc
    return drift


def sync(
    api: OpenProjectAPI,
    phases: list[Phase],
    dry_run: bool,
) -> tuple[list[PlanRow], int]:
    """Returns (plan, issues_changed_count)."""
    states = api.ensure_states()

    missing = [k for k in ("Backlog", "In Progress", "Done", "On hold") if k not in states]
    if missing:
        print(f"WARN: missing OP statuses for: {missing}; sync will skip writes for those.",
              file=sys.stderr)

    plan: list[PlanRow] = []

    print(f"  fetching all work packages for diff …")
    all_issues = api.list_all_issues()
    by_extid: dict[str, dict] = {
        (i.get("external_id") or ""): i
        for i in all_issues
        if i.get("external_id")
    }
    print(f"  loaded {len(all_issues)} WP(s); {len(by_extid)} have external_id")

    for phase in phases:
        # ── Phase version (Plane "module" analog) ──
        phase_extid = f"Phase-{phase.number:02d}"
        existing_module = api.get_module_by_external_id(phase_extid)
        module_issue_links: set[int] = set()
        if existing_module is None:
            plan.append(PlanRow(
                kind="module",
                extid=phase_extid,
                label=f"Phase {phase.number} version",
                action="create",
                drift={"name": phase_extid},
            ))
            module_id: int | None = None
            if not dry_run:
                created, _ = api.ensure_module(
                    external_id=phase_extid,
                    name=phase_extid,
                    description=phase.header,
                )
                module_id = created["id"]
                time.sleep(SLEEP_BETWEEN)
        else:
            module_id = existing_module["id"]
            plan.append(PlanRow(
                kind="module",
                extid=phase_extid,
                label=f"Phase {phase.number} version",
                action="no-op",
                drift={},
            ))
            try:
                module_issue_links = set(api.list_module_issues(module_id))
            except RateLimitError:
                print(f"RATE-LIMIT on version-issues for {phase_extid} — sleeping {BACKOFF_429}s")
                time.sleep(BACKOFF_429)
                try:
                    module_issue_links = set(api.list_module_issues(module_id))
                except RateLimitError:
                    print(f"RATE-LIMIT again — skipping version association for {phase_extid}")
                    module_issue_links = set()

        # ── Phase summary work package ──
        phase_issue_extid = phase_extid
        phase_issue_name = f"[{phase_extid}] {phase.header}"
        phase_issue_desc = _phase_description_html(phase)
        if "CLOSED" in phase.header.upper():
            phase_state_id = states.get("Done")
        else:
            phase_state_id = states.get("In Progress")

        live_phase_issue = by_extid.get(phase_issue_extid)
        if live_phase_issue is None:
            plan.append(PlanRow(
                kind="phase-issue",
                extid=phase_issue_extid,
                label=phase_issue_name,
                action="create",
                drift={"state": phase_state_id, "name": phase_issue_name},
            ))
            if not dry_run and phase_state_id:
                created = api.create_issue(
                    name=phase_issue_name,
                    description=phase_issue_desc,
                    state_id=phase_state_id,
                    priority="medium",
                    external_id=phase_issue_extid,
                )
                phase_issue_id = created["id"]
                if module_id:
                    api.add_issues_to_module(module_id, [phase_issue_id])
                time.sleep(SLEEP_BETWEEN)
        else:
            phase_issue_id = live_phase_issue["id"]
            if phase_state_id is None:
                drift = {}
            else:
                drift = _diff_issue(
                    live_phase_issue,
                    want_state_id=phase_state_id,
                    want_name=phase_issue_name,
                    want_desc=phase_issue_desc,
                )
            if drift:
                plan.append(PlanRow(
                    kind="phase-issue",
                    extid=phase_issue_extid,
                    label=phase_issue_name,
                    action="update",
                    drift=drift,
                ))
                if not dry_run:
                    api.update_issue(phase_issue_id, drift)
                    time.sleep(SLEEP_BETWEEN)
            else:
                plan.append(PlanRow(
                    kind="phase-issue",
                    extid=phase_issue_extid,
                    label=phase_issue_name,
                    action="no-op",
                    drift={},
                ))
            if module_id and not dry_run and phase_issue_id not in module_issue_links:
                api.add_issues_to_module(module_id, [phase_issue_id])
                module_issue_links.add(phase_issue_id)

        # ── Deliverable work packages ──
        for d in phase.deliverables:
            want_state_name = STATUS_TO_OP_STATE[d.status_word]
            want_state_id = states.get(want_state_name)
            if want_state_id is None:
                print(f"WARN: skipping {d.external_id}: status {want_state_name!r} not in project",
                      file=sys.stderr)
                continue
            want_name = f"[{d.external_id}] {d.title}"
            want_desc = _description_html(d)

            live = by_extid.get(d.external_id)
            if live is None:
                plan.append(PlanRow(
                    kind="deliverable-issue",
                    extid=d.external_id,
                    label=want_name,
                    action="create",
                    drift={"state": want_state_id, "name": want_name},
                ))
                if not dry_run:
                    try:
                        created = api.create_issue(
                            name=want_name,
                            description=want_desc,
                            state_id=want_state_id,
                            priority="medium",
                            external_id=d.external_id,
                        )
                        if module_id:
                            api.add_issues_to_module(module_id, [created["id"]])
                            module_issue_links.add(created["id"])
                    except RateLimitError:
                        print(f"RATE-LIMIT on {d.external_id} — sleeping {BACKOFF_429}s")
                        time.sleep(BACKOFF_429)
                    time.sleep(SLEEP_BETWEEN)
                continue

            drift = _diff_issue(
                live,
                want_state_id=want_state_id,
                want_name=want_name,
                want_desc=want_desc,
            )
            if drift:
                plan.append(PlanRow(
                    kind="deliverable-issue",
                    extid=d.external_id,
                    label=want_name,
                    action="update",
                    drift=drift,
                ))
                if not dry_run:
                    try:
                        api.update_issue(live["id"], drift)
                    except RateLimitError:
                        print(f"RATE-LIMIT on {d.external_id} — sleeping {BACKOFF_429}s")
                        time.sleep(BACKOFF_429)
                    time.sleep(SLEEP_BETWEEN)
            else:
                plan.append(PlanRow(
                    kind="deliverable-issue",
                    extid=d.external_id,
                    label=want_name,
                    action="no-op",
                    drift={},
                ))

            # Version association — additive only
            if module_id and not dry_run:
                if live["id"] not in module_issue_links:
                    try:
                        api.add_issues_to_module(module_id, [live["id"]])
                        module_issue_links.add(live["id"])
                    except RateLimitError:
                        print(f"RATE-LIMIT on version-add {d.external_id} — sleeping {BACKOFF_429}s")
                        time.sleep(BACKOFF_429)
                    time.sleep(SLEEP_BETWEEN)

    changed = sum(1 for r in plan if r.action != "no-op")
    return plan, changed


# ── CLI ──────────────────────────────────────────────────────────────────────

def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true", help="Plan only; exit 2 if changes pending")
    ap.add_argument("--phase", type=int, default=None, help="Limit to a single phase")
    args = ap.parse_args()

    print(f"OpenProject: {OPENPROJECT_URL}  project={PROJECT_IDENTIFIER}")
    print(f"Mode: {'DRY-RUN' if args.dry_run else 'APPLY'}")
    if args.phase is not None:
        print(f"Filter: phase {args.phase} only")
    print()

    if not FRAMEWORK_MD.is_file():
        sys.exit(f"ERROR: {FRAMEWORK_MD} not found")

    phases = parse_framework(FRAMEWORK_MD)
    if args.phase is not None:
        phases = [p for p in phases if p.number == args.phase]
    if not phases:
        sys.exit("ERROR: no phases parsed from PROJECT_FRAMEWORK.md")

    total_d = sum(len(p.deliverables) for p in phases)
    print(f"Parsed {len(phases)} phase(s), {total_d} deliverable(s)")
    for p in phases:
        print(f"  Phase {p.number:>2}: {len(p.deliverables)} deliverable(s)  — {p.header}")
    print()

    token = fetch_token()
    os.environ["OPENPROJECT_API_TOKEN"] = token
    os.environ["OPENPROJECT_URL"] = OPENPROJECT_URL
    os.environ["OPENPROJECT_PROJECT"] = PROJECT_IDENTIFIER
    api = OpenProjectAPI()

    if not api.health_check():
        sys.exit("ERROR: OpenProject health-check failed")

    try:
        plan, changed = sync(api, phases, dry_run=args.dry_run)
    except RateLimitError as exc:
        print(f"\nERROR: OpenProject rate-limited ({exc}). Wait ~60s and retry.", file=sys.stderr)
        return 3

    by_action: dict[str, int] = {"create": 0, "update": 0, "no-op": 0}
    for row in plan:
        by_action[row.action] = by_action.get(row.action, 0) + 1

    print("Plan:")
    for row in plan:
        icon = {"create": "+", "update": "~", "no-op": "."}[row.action]
        if row.action == "update":
            keys = ",".join(sorted(row.drift.keys()))
            print(f"  {icon} {row.kind:<18} {row.extid:<14} drift=[{keys}]  {row.label}")
        else:
            print(f"  {icon} {row.kind:<18} {row.extid:<14}                    {row.label}")
    print()
    print(
        f"Summary: create={by_action['create']}  update={by_action['update']}  "
        f"no-op={by_action['no-op']}"
    )

    if args.dry_run:
        if changed:
            print(f"\nDRY-RUN: {changed} change(s) pending — exit 2")
            return 2
        print("\nDRY-RUN: clean — exit 0")
        return 0
    return 0


if __name__ == "__main__":
    sys.exit(main())
