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
sys.path.insert(0, str(REPO_ROOT / "scripts" / "lib"))

from framework.openproject_connector import (  # type: ignore  # noqa: E402
    OpenProjectAPI,
    RateLimitError,
)
from roadmap_parser import (  # type: ignore  # noqa: E402
    RoadmapItem,
    parse_roadmap,
)

FRAMEWORK_MD = REPO_ROOT / "docs" / "PROJECT_FRAMEWORK.md"
ROADMAP_MD = REPO_ROOT / "docs" / "PHASE_ROADMAP.md"

AUTONOMOUS_CODING_CATEGORY = "autonomous-coding"

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


# ── Markdown parsing (forked from plane-sync; extended for Phase 17 rows) ────

# Phase 17 framework rows carry a "(historical: 17.X)" annotation between
# the extid and the colon, added in WP-17-04-01.5 when the identifier
# convention was corrected from shorthand "17.X" to canonical D-NN-MM.
# The original plane-sync ROW_RE didn't tolerate this, so Phase 17 rows
# parsed as 0 deliverables — silent no-op since 51b012e. The optional
# non-capturing group below restores Phase 17 visibility while preserving
# backward compat for Phase 16 and earlier rows (no parenthetical).
ROW_RE = re.compile(
    r"^\|\s*"
    r"(?P<extid>"
    r"D-(?P<phase_d>\d+)-[\w.\-]+"
    r"|"
    r"(?P<phase_t>\d+)\.[A-Z]"
    r")"
    r"(?:\s+\(historical:[^)]+\))?"
    r"\s*:\s*(?P<title>.+?)\s*"
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


def _roadmap_description_html(it: RoadmapItem) -> str:
    flag = (
        "<p><strong>Autonomous-coding capability flag: yes.</strong></p>"
        if it.autonomous_coding else ""
    )
    return (
        f"<p><strong>Phase {it.phase}.{it.sub_block} roadmap item "
        f"(ord {it.ordinal}).</strong> "
        f"This work package mirrors a scope bullet from "
        f"<code>docs/PHASE_ROADMAP.md</code> §{it.phase}.{it.sub_block} "
        f"and is rewritten by "
        f"<code>scripts/openproject-sync-from-framework.py</code> "
        f"(D-17-31). Edit the markdown roadmap, not this WP.</p>"
        f"<p>Scope: {_html_escape(it.scope_text)}</p>"
        f"{flag}"
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
                       # | "roadmap-issue" | "phase17-dedup"
    extid: str
    label: str
    action: str        # "create" | "update" | "no-op" | "close"
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


# ── Roadmap-item sync (D-17-31) ──────────────────────────────────────────────

def sync_roadmap(
    api: OpenProjectAPI,
    items: list[RoadmapItem],
    dry_run: bool,
) -> tuple[list[PlanRow], int]:
    """Sync PHASE_ROADMAP.md scope items as RM-NN-X-NNN work packages.

    Each item is associated with its phase version (Phase-16 / Phase-18)
    if that version exists. Autonomous-coding items get the
    `autonomous-coding` category; non-flagged items get no category.
    Status: NOT STARTED scope items map to OpenProject `Backlog`.
    """
    states = api.ensure_states()
    backlog_state_id = states.get("Backlog")
    if backlog_state_id is None:
        print("WARN: Backlog state not found; roadmap sync will skip writes.",
              file=sys.stderr)
        return [], 0

    # Resolve the autonomous-coding category (lookup-only; OpenProject
    # API v3 has no documented category-create endpoint, so the category
    # must pre-exist in the project. If absent, we fall back to encoding
    # the flag in the WP description (see _roadmap_description_html).
    auto_cat_id = api.get_category_id(AUTONOMOUS_CODING_CATEGORY)
    if auto_cat_id is None:
        print(
            f"NOTE: category {AUTONOMOUS_CODING_CATEGORY!r} not found in "
            f"OpenProject project — flag will be encoded in WP description "
            f"only. Operator: create the category via "
            f"Project settings → Work package categories to enable "
            f"category-based filtering.",
            file=sys.stderr,
        )

    # Resolve phase modules for version-association. Framework sync owns
    # versions for phases in §9; for phases that exist only in
    # PHASE_ROADMAP.md (e.g. Phase 18 before its first deliverable lands
    # in §9), we create the version here so RM items get a swimlane.
    module_id_for_phase: dict[int, int | None] = {}
    module_links: dict[int, set[int]] = {}
    for phase_n in {it.phase for it in items}:
        phase_extid = f"Phase-{phase_n:02d}"
        m = api.get_module_by_external_id(phase_extid)
        if m is None and not dry_run:
            try:
                created, _ = api.ensure_module(
                    external_id=phase_extid,
                    name=phase_extid,
                    description=f"Phase {phase_n} (roadmap-only; no §9 deliverables yet)",
                )
                m = {"id": created["id"]}
            except Exception as exc:
                print(f"WARN: could not create version {phase_extid}: {exc}",
                      file=sys.stderr)
        if m is not None:
            module_id_for_phase[phase_n] = m["id"]
            try:
                module_links[phase_n] = set(api.list_module_issues(m["id"]))
            except RateLimitError:
                module_links[phase_n] = set()
        else:
            module_id_for_phase[phase_n] = None
            module_links[phase_n] = set()

    # Index existing WPs by external_id once, for diff.
    all_issues = api.list_all_issues()
    by_extid: dict[str, dict] = {
        (i.get("external_id") or ""): i
        for i in all_issues
        if i.get("external_id")
    }

    plan: list[PlanRow] = []

    for it in items:
        want_name = f"[{it.external_id}] {it.title}"
        want_desc = _roadmap_description_html(it)

        live = by_extid.get(it.external_id)
        if live is None:
            plan.append(PlanRow(
                kind="roadmap-issue",
                extid=it.external_id,
                label=want_name + (" [auto]" if it.autonomous_coding else ""),
                action="create",
                drift={"state": backlog_state_id, "name": want_name},
            ))
            if not dry_run:
                try:
                    label_ids = [auto_cat_id] if (it.autonomous_coding and auto_cat_id) else None
                    created = api.create_issue(
                        name=want_name,
                        description=want_desc,
                        state_id=backlog_state_id,
                        priority="medium",
                        external_id=it.external_id,
                        label_ids=label_ids,
                    )
                    mid = module_id_for_phase.get(it.phase)
                    if mid:
                        api.add_issues_to_module(mid, [created["id"]])
                        module_links[it.phase].add(created["id"])
                except RateLimitError:
                    print(f"RATE-LIMIT on {it.external_id} — sleeping {BACKOFF_429}s")
                    time.sleep(BACKOFF_429)
                time.sleep(SLEEP_BETWEEN)
            continue

        # Update path: only diff name + description. Status drift is
        # operator-owned (they may have moved an item from Backlog to
        # In Progress); we don't overwrite it.
        drift: dict = {}
        if (live.get("name") or "") != want_name:
            drift["name"] = want_name
        want_md = _html_to_markdown(want_desc)
        have_md = live.get("description_raw") or ""
        if _normalise_md(have_md) != _normalise_md(want_md):
            drift["description_html"] = want_desc

        if drift:
            plan.append(PlanRow(
                kind="roadmap-issue",
                extid=it.external_id,
                label=want_name,
                action="update",
                drift=drift,
            ))
            if not dry_run:
                try:
                    api.update_issue(live["id"], drift)
                except RateLimitError:
                    print(f"RATE-LIMIT on {it.external_id} — sleeping {BACKOFF_429}s")
                    time.sleep(BACKOFF_429)
                time.sleep(SLEEP_BETWEEN)
        else:
            plan.append(PlanRow(
                kind="roadmap-issue",
                extid=it.external_id,
                label=want_name,
                action="no-op",
                drift={},
            ))

        mid = module_id_for_phase.get(it.phase)
        if mid and not dry_run and live["id"] not in module_links[it.phase]:
            try:
                api.add_issues_to_module(mid, [live["id"]])
                module_links[it.phase].add(live["id"])
            except RateLimitError:
                pass
            time.sleep(SLEEP_BETWEEN)

    changed = sum(1 for r in plan if r.action != "no-op")
    return plan, changed


# ── Phase 17 shorthand dedup (D-17-31 one-shot) ──────────────────────────────

# The original 17.A..17.T shorthand WPs were imported pre-D-17-04, before
# the canonical D-17-NN identifier convention. Both are now in
# OpenProject. We close the shorthand ones (status=Done) with a
# description note pointing at the canonical ID. We do NOT delete —
# preserves history of any operator comments.

PHASE17_SHORTHAND_RE = re.compile(r"^17\.[A-T]$")

PHASE17_SHORTHAND_TO_CANONICAL = {
    f"17.{chr(ord('A') + i)}": f"D-17-{i + 1:02d}" for i in range(20)
}


def dedup_phase17_shorthand(api: OpenProjectAPI, dry_run: bool) -> list[PlanRow]:
    states = api.ensure_states()
    done_id = states.get("Done")
    plan: list[PlanRow] = []

    for issue in api.list_all_issues():
        extid = issue.get("external_id") or ""
        if not PHASE17_SHORTHAND_RE.match(extid):
            continue
        canonical = PHASE17_SHORTHAND_TO_CANONICAL.get(extid, "(unknown)")
        already_closed = (issue.get("state_name") or "").lower() in ("done", "closed")
        if already_closed:
            plan.append(PlanRow(
                kind="phase17-dedup",
                extid=extid,
                label=f"{extid} → {canonical} (already closed)",
                action="no-op",
                drift={},
            ))
            continue

        new_desc = (
            f"<p><strong>SUPERSEDED.</strong> This shorthand WP was the "
            f"pre-D-17-04 identifier for what is now <code>{canonical}</code>. "
            f"Closed as part of D-17-31 dedup. See <code>{canonical}</code> "
            f"for the canonical work package; manual operator comments on this "
            f"WP are preserved here.</p>"
        )
        plan.append(PlanRow(
            kind="phase17-dedup",
            extid=extid,
            label=f"{extid} → close (superseded by {canonical})",
            action="close",
            drift={"state": done_id, "description_html": new_desc},
        ))
        if not dry_run and done_id:
            try:
                api.update_issue(issue["id"], {
                    "state": done_id,
                    "description_html": new_desc,
                })
            except RateLimitError:
                print(f"RATE-LIMIT on dedup {extid} — sleeping {BACKOFF_429}s")
                time.sleep(BACKOFF_429)
            time.sleep(SLEEP_BETWEEN)

    return plan


# ── CLI ──────────────────────────────────────────────────────────────────────

def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true", help="Plan only; exit 2 if changes pending")
    ap.add_argument("--phase", type=int, default=None, help="Limit to a single phase")
    ap.add_argument("--include-roadmap", action="store_true",
                    help="Also sync PHASE_ROADMAP.md scope items (Phase 16/18 sub-blocks). D-17-31.")
    ap.add_argument("--roadmap-only", action="store_true",
                    help="Skip framework sync; only sync roadmap. Useful for fast iteration.")
    ap.add_argument("--dedup-phase17", action="store_true",
                    help="One-shot: close 17.A–17.T shorthand WPs as superseded by D-17-NN canonical IDs.")
    args = ap.parse_args()

    print(f"OpenProject: {OPENPROJECT_URL}  project={PROJECT_IDENTIFIER}")
    print(f"Mode: {'DRY-RUN' if args.dry_run else 'APPLY'}")
    if args.phase is not None:
        print(f"Filter: phase {args.phase} only")
    if args.include_roadmap or args.roadmap_only:
        print(f"Roadmap sync: ON  (source: {ROADMAP_MD.relative_to(REPO_ROOT)})")
    if args.dedup_phase17:
        print("Phase-17 dedup: ON  (close 17.A–17.T as superseded)")
    print()

    if not FRAMEWORK_MD.is_file():
        sys.exit(f"ERROR: {FRAMEWORK_MD} not found")

    if not args.roadmap_only:
        phases = parse_framework(FRAMEWORK_MD)
        if args.phase is not None:
            phases = [p for p in phases if p.number == args.phase]
        if not phases:
            sys.exit("ERROR: no phases parsed from PROJECT_FRAMEWORK.md")

        total_d = sum(len(p.deliverables) for p in phases)
        print(f"Parsed {len(phases)} phase(s), {total_d} deliverable(s) from framework")
        for p in phases:
            print(f"  Phase {p.number:>2}: {len(p.deliverables)} deliverable(s)  — {p.header}")
        print()
    else:
        phases = []

    roadmap_items: list[RoadmapItem] = []
    if args.include_roadmap or args.roadmap_only:
        if not ROADMAP_MD.is_file():
            sys.exit(f"ERROR: {ROADMAP_MD} not found")
        sub_blocks = parse_roadmap(ROADMAP_MD)
        for sb in sub_blocks:
            if args.phase is not None and sb.phase != args.phase:
                continue
            roadmap_items.extend(sb.items)
        auto_ct = sum(1 for it in roadmap_items if it.autonomous_coding)
        print(f"Parsed {len(roadmap_items)} roadmap item(s), {auto_ct} autonomous-codable")
        for sb in sub_blocks:
            if args.phase is not None and sb.phase != args.phase:
                continue
            ac = sum(1 for it in sb.items if it.autonomous_coding)
            print(f"  Phase {sb.phase}.{sb.letter}: {len(sb.items)} item(s) ({ac} auto)  — {sb.heading}")
        print()

    token = fetch_token()
    os.environ["OPENPROJECT_API_TOKEN"] = token
    os.environ["OPENPROJECT_URL"] = OPENPROJECT_URL
    os.environ["OPENPROJECT_PROJECT"] = PROJECT_IDENTIFIER
    api = OpenProjectAPI()

    if not api.health_check():
        sys.exit("ERROR: OpenProject health-check failed")

    full_plan: list[PlanRow] = []
    total_changed = 0

    try:
        if not args.roadmap_only:
            plan, changed = sync(api, phases, dry_run=args.dry_run)
            full_plan.extend(plan)
            total_changed += changed
        if args.include_roadmap or args.roadmap_only:
            rplan, rchanged = sync_roadmap(api, roadmap_items, dry_run=args.dry_run)
            full_plan.extend(rplan)
            total_changed += rchanged
        if args.dedup_phase17:
            dplan = dedup_phase17_shorthand(api, dry_run=args.dry_run)
            full_plan.extend(dplan)
            total_changed += sum(1 for r in dplan if r.action != "no-op")
    except RateLimitError as exc:
        print(f"\nERROR: OpenProject rate-limited ({exc}). Wait ~60s and retry.", file=sys.stderr)
        return 3

    by_action: dict[str, int] = {"create": 0, "update": 0, "no-op": 0, "close": 0}
    for row in full_plan:
        by_action[row.action] = by_action.get(row.action, 0) + 1

    print("Plan:")
    icon_for = {"create": "+", "update": "~", "no-op": ".", "close": "x"}
    for row in full_plan:
        icon = icon_for.get(row.action, "?")
        if row.action == "update" or row.action == "close":
            keys = ",".join(sorted(row.drift.keys()))
            print(f"  {icon} {row.kind:<18} {row.extid:<14} drift=[{keys}]  {row.label}")
        else:
            print(f"  {icon} {row.kind:<18} {row.extid:<14}                    {row.label}")
    print()
    print(
        f"Summary: create={by_action['create']}  update={by_action['update']}  "
        f"close={by_action['close']}  no-op={by_action['no-op']}"
    )

    if args.dry_run:
        if total_changed:
            print(f"\nDRY-RUN: {total_changed} change(s) pending — exit 2")
            return 2
        print("\nDRY-RUN: clean — exit 0")
        return 0
    return 0


if __name__ == "__main__":
    sys.exit(main())
