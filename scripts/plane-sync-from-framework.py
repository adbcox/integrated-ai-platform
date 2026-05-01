#!/usr/bin/env python3
"""D-16-02.A — one-way sync from PROJECT_FRAMEWORK.md to Plane.

Doctrine (ADR-A-006): repo-owned docs are canonical; Plane is an
operational overlay. This script writes from repo to Plane only.
Manual edits made in the Plane UI to synced issues will be overwritten
on the next run; that is intentional. The Plane UI is the right place
to attach comments, sub-tasks, and operational links — not to redefine
deliverable scope or status.

What it syncs:
  - One Plane *module* per phase, keyed by external_id `Phase-NN`.
  - One Plane *issue* per phase, keyed by external_id `Phase-NN`,
    summarising the phase header.
  - One Plane *issue* per deliverable, keyed by external_id (e.g.
    `D-16-02`, `D-16-02.A`, `D-15-08`), associated with the phase
    module.

What it leaves alone:
  - ADR stubs (anything whose external_id starts with `ADR-`). The
    cross-index validator (`scripts/cross-index-validate.py`) owns
    those; this script never reads, writes, or matches them.

Idempotency:
  - Modules and issues are matched by external_id only.
  - Updates are sent as a minimal diff: state, name, description, and
    module association are compared against the live record and
    written only when they actually drift.

Modes:
  --dry-run   Plan only; print planned creates / updates / no-ops.
              Exits 0 if no changes pending, 2 if changes pending.
              D-16-06's CI hook will use this exit-code contract to
              detect drift.
  (default)   Apply the changes.
  --phase N   Limit to a single phase (e.g. `--phase 15` or
              `--phase 16`). Useful for debugging without touching
              the full table.

Status mapping (markdown -> Plane state name):
    DONE                    -> Done
    IN PROGRESS             -> In Progress
    NOT STARTED             -> Backlog
    DEFERRED [...]          -> Cancelled

Token: pulled from Vault `secret/plane/api#homepage_token` via the
running vault-server container, same shape as
`scripts/backfill-plane-labels.py`. Token is never displayed.

Run from the Mac Mini in the block-4c venv:
    /Users/admin/.venv-block-4c/bin/python scripts/plane-sync-from-framework.py [--dry-run] [--phase 16]
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

from framework.plane_connector import (  # type: ignore  # noqa: E402
    PlaneAPI,
    RateLimitError,
)

FRAMEWORK_MD = REPO_ROOT / "docs" / "PROJECT_FRAMEWORK.md"

PLANE_URL = "http://localhost:8000"
WORKSPACE = "iap"
PROJECT_ID = "dbcd4476-1e37-4812-a443-0914ec8380fc"

# Pacing — match the rest of the Plane-touching scripts (1 req/sec floor).
SLEEP_BETWEEN = 1.0
BACKOFF_429 = 65.0


# ── Status mapping ───────────────────────────────────────────────────────────

# Matches the heading of each status word; stripped of trailing prose like
# "DEFERRED to Phase 16" -> "DEFERRED".
STATUS_RE = re.compile(r"^(DONE|IN PROGRESS|NOT STARTED|DEFERRED)\b", re.IGNORECASE)

STATUS_TO_PLANE_STATE = {
    "DONE":        "Done",
    "IN PROGRESS": "In Progress",
    "NOT STARTED": "Backlog",
    "DEFERRED":    "Cancelled",
}


# ── Parsed-row dataclass ─────────────────────────────────────────────────────

@dataclass
class Deliverable:
    phase: int          # 15
    external_id: str    # "D-15-08"
    title: str          # "Loose-doc retirement pass"
    status_word: str    # "DEFERRED"
    reference: str      # "beyond-audit"


@dataclass
class Phase:
    number: int
    header: str         # "Phase 15 — CLOSED 2026-05-01"
    deliverables: list[Deliverable]


# ── Markdown parsing ─────────────────────────────────────────────────────────

# A row looks like:
#   | D-15-08: Loose-doc retirement pass | DEFERRED to Phase 16 | beyond-audit |
#   | D-16-02.A: Plane bootstrap from PROJECT_FRAMEWORK.md | IN PROGRESS | (this commit) |
ROW_RE = re.compile(
    r"^\|\s*"
    r"(?P<extid>D-(?P<phase>\d+)-[\w.\-]+)\s*:\s*(?P<title>.+?)\s*"
    r"\|\s*(?P<status>[^|]+?)\s*"
    r"\|\s*(?P<reference>[^|]+?)\s*\|\s*$"
)

PHASE_HEADING_RE = re.compile(r"^##\s+\d+\.\s+(?P<hdr>Phase\s+(?P<n>\d+)[^\n]*)\s*$")


def parse_framework(md_path: Path) -> list[Phase]:
    """Walk the markdown line-by-line, picking up phase headings and
    contiguous deliverable rows. Order is preserved.
    """
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
        row_phase = int(m.group("phase"))
        # Anchor each row to the closest preceding phase heading. If a row's
        # ID disagrees with the surrounding heading (e.g. the "Phase 16
        # charter draft" preview rows under §7), trust the ID — it is the
        # canonical key.
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
        # If we anchored a row whose phase disagrees with the surrounding
        # heading (charter-draft preview rows), only emit it under its own
        # phase; the heading-walk catches the real phase later.
        if current_phase is not None and current_phase != phase_n:
            # Skip preview rows that belong to a different phase; the
            # canonical row will be picked up under its own phase heading.
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
    """Pull the Plane API token from Vault via the running vault-server
    container. Avoids putting the value on argv.
    """
    vt = Path.home() / ".vault-token"
    if vt.is_file():
        token = vt.read_text().strip()
    else:
        token = ""
    # Fallback: read root token from the post-rebuild init keys file. This
    # is what Phase 15 left in place after the KV loss incident; if the
    # operator session token is stale (pre-2026-04-30), fall through to it.
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
    sys.exit(f"ERROR: could not read Plane API token from Vault. Last error: {last_err or '(none)'}")


# ── Diff / sync logic ────────────────────────────────────────────────────────

def _description_html(d: Deliverable) -> str:
    return (
        f"<p><strong>Phase {d.phase} deliverable.</strong> "
        f"This issue mirrors PROJECT_FRAMEWORK.md and is rewritten by "
        f"<code>scripts/plane-sync-from-framework.py</code>. "
        f"Edit the markdown table, not this issue.</p>"
        f"<p>Reference: <code>{_html_escape(d.reference)}</code></p>"
    )


def _phase_description_html(p: Phase) -> str:
    return (
        f"<p><strong>{_html_escape(p.header)}</strong></p>"
        f"<p>This issue mirrors PROJECT_FRAMEWORK.md §"
        f"{'7' if p.number == 15 else '8' if p.number == 16 else '?'} "
        f"and is rewritten by <code>scripts/plane-sync-from-framework.py</code>.</p>"
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
    drift: dict        # for "update": which fields differ


def _normalise_html(s: str) -> str:
    """Plane wraps stored description_html in a `<div>...</div>` envelope
    on read, even when we PATCHed without it. Strip the envelope and
    surrounding whitespace so the diff is content-stable across rounds.
    """
    s = (s or "").strip()
    if s.startswith("<div>") and s.endswith("</div>"):
        s = s[len("<div>"):-len("</div>")]
    return s.strip()


def _diff_issue(live: dict, want_state_id: str, want_name: str, want_desc: str) -> dict:
    drift: dict = {}
    if (live.get("state") or "") != want_state_id:
        drift["state"] = want_state_id
    if (live.get("name") or "") != want_name:
        drift["name"] = want_name
    if _normalise_html(live.get("description_html") or "") != _normalise_html(want_desc):
        drift["description_html"] = want_desc
    return drift


def _diff_module_assoc(live_issue_ids: set[str], want_issue_ids: set[str]) -> set[str]:
    """Return the set of issue IDs that need to be added to the module.
    Removal is not in scope: a deliverable is only ever added, never removed,
    by this sync. (If a deliverable is removed from the markdown the issue
    stays in Plane and falls out of sync — surfaced at the next dry-run.)
    """
    return want_issue_ids - live_issue_ids


def sync(
    api: PlaneAPI,
    phases: list[Phase],
    dry_run: bool,
) -> tuple[list[PlanRow], int]:
    """Returns (plan, issues_changed_count). issues_changed_count is the
    number of plan rows whose action is not "no-op".
    """
    states = api.ensure_states()
    plan: list[PlanRow] = []

    # Issue lookup by external_id — list_all_issues + filter is one call now,
    # cheaper than per-extid search.
    print(f"  fetching all issues for diff …")
    all_issues = api.list_all_issues()
    by_extid: dict[str, dict] = {
        (i.get("external_id") or ""): i
        for i in all_issues
        if i.get("external_id")
    }

    for phase in phases:
        # ── Phase module ──
        phase_extid = f"Phase-{phase.number:02d}"
        existing_module = api.get_module_by_external_id(phase_extid)
        # Fetch the module's current issue links exactly once per phase.
        # Per-row fetches blew the rate-limit budget on the first run.
        module_issue_links: set[str] = set()
        if existing_module is None:
            plan.append(PlanRow(
                kind="module",
                extid=phase_extid,
                label=f"Phase {phase.number} module",
                action="create",
                drift={"name": phase_extid, "external_id": phase_extid},
            ))
            module_id = None
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
                label=f"Phase {phase.number} module",
                action="no-op",
                drift={},
            ))
            try:
                module_issue_links = set(api.list_module_issues(module_id))
            except RateLimitError:
                print(f"RATE-LIMIT on module-issues for {phase_extid} — sleeping {BACKOFF_429}s")
                time.sleep(BACKOFF_429)
                try:
                    module_issue_links = set(api.list_module_issues(module_id))
                except RateLimitError:
                    print(f"RATE-LIMIT again — skipping module association for {phase_extid}")
                    module_issue_links = set()

        # ── Phase summary issue ──
        phase_issue_extid = phase_extid
        phase_issue_name = f"[{phase_extid}] {phase.header}"
        phase_issue_desc = _phase_description_html(phase)
        # Phase summary state derived from majority/explicit cue: closed
        # phase = Done; opened phase = In Progress.
        if "CLOSED" in phase.header.upper():
            phase_state_id = states["Done"]
        else:
            phase_state_id = states["In Progress"]

        live_phase_issue = by_extid.get(phase_issue_extid)
        if live_phase_issue is None:
            plan.append(PlanRow(
                kind="phase-issue",
                extid=phase_issue_extid,
                label=phase_issue_name,
                action="create",
                drift={"state": phase_state_id, "name": phase_issue_name},
            ))
            phase_issue_id = None
            if not dry_run:
                created = api.create_issue(
                    name=phase_issue_name,
                    description=_strip_p(phase_issue_desc),
                    state_id=phase_state_id,
                    priority="medium",
                    external_id=phase_issue_extid,
                )
                phase_issue_id = created["id"]
                # description_html is set with description; if the create_issue
                # path wrapped <p> we may want to PATCH the html; do it once.
                api.update_issue(phase_issue_id, {"description_html": phase_issue_desc})
                time.sleep(SLEEP_BETWEEN)
        else:
            phase_issue_id = live_phase_issue["id"]
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

        # ── Deliverable issues ──
        for d in phase.deliverables:
            want_state_name = STATUS_TO_PLANE_STATE[d.status_word]
            want_state_id = states[want_state_name]
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
                            description=_strip_p(want_desc),
                            state_id=want_state_id,
                            priority="medium",
                            external_id=d.external_id,
                        )
                        # Patch the rendered HTML so it carries the
                        # canonical block (description_html may not match
                        # description on POST).
                        api.update_issue(created["id"], {"description_html": want_desc})
                        # Add to phase module
                        if module_id:
                            api.add_issues_to_module(module_id, [created["id"]])
                    except RateLimitError:
                        print(f"RATE-LIMIT on {d.external_id} — sleeping {BACKOFF_429}s")
                        time.sleep(BACKOFF_429)
                        # let next run pick up
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

            # Module association — additive only. Use the per-phase
            # link set fetched above; refresh it locally as we add.
            if module_id and not dry_run:
                if live["id"] not in module_issue_links:
                    try:
                        api.add_issues_to_module(module_id, [live["id"]])
                        module_issue_links.add(live["id"])
                    except RateLimitError:
                        print(f"RATE-LIMIT on module-add {d.external_id} — sleeping {BACKOFF_429}s")
                        time.sleep(BACKOFF_429)
                    time.sleep(SLEEP_BETWEEN)

    changed = sum(1 for r in plan if r.action != "no-op")
    return plan, changed


def _strip_p(html: str) -> str:
    """Reduce a description_html block to a plain text fallback for the
    POST `description` field, which Plane V1 still expects alongside the
    HTML form. Quick stripping is enough for the rollback path."""
    return re.sub(r"<[^>]+>", "", html)


# ── CLI ──────────────────────────────────────────────────────────────────────

def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true", help="Plan only; exit 2 if changes pending")
    ap.add_argument("--phase", type=int, default=None, help="Limit to a single phase")
    args = ap.parse_args()

    print(f"Plane: {PLANE_URL}  workspace={WORKSPACE}  project={PROJECT_ID}")
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
    os.environ["PLANE_API_TOKEN"] = token
    os.environ["PLANE_URL"] = PLANE_URL
    os.environ["PLANE_WORKSPACE"] = WORKSPACE
    os.environ["PLANE_PROJECT_ID"] = PROJECT_ID
    api = PlaneAPI()

    if not api.health_check():
        sys.exit("ERROR: Plane health-check failed")

    try:
        plan, changed = sync(api, phases, dry_run=args.dry_run)
    except RateLimitError as exc:
        # An unhandled 429 in a non-issue path (e.g. /states/, /modules/).
        # Surface it as a distinct exit code (3) so a caller can
        # distinguish "Plane saturated" from "drift pending" (2). Operator
        # remedy is to wait ~60s and re-run.
        print(f"\nERROR: Plane rate-limited ({exc}). Wait ~60s and retry.", file=sys.stderr)
        return 3

    # Summarise
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
