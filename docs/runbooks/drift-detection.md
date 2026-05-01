# Runbook — drift detection (D-16-06)

| Field            | Value                                                  |
|------------------|--------------------------------------------------------|
| Deliverable      | D-16-06                                                |
| Script (local)   | `scripts/check-repo-coherence.py`                      |
| Script (Plane)   | `scripts/cross-index-validate.py`                      |
| Pre-commit cfg   | `.pre-commit-config.yaml` (3 local hooks)              |
| CI workflow      | `.github/workflows/validate-infrastructure.yml`        |
| Local cron       | mac-mini, nightly — see §2                             |
| Status           | LIVE 2026-05-01                                        |

## §1 — Purpose

Three-leg model for keeping the platform coherent (per ADR-A-006):

  1. **Single source of truth — repo.** Architecture, deliverables,
     decisions live in `docs/`. Anything else is derived.
  2. **One-way sync repo → operational tools.** `plane-sync-from-
     framework.py` mirrors the markdown deliverable tables into Plane.
     `netbox-register-*.py` registers services into NetBox. Both write
     repo → tool only — never the other direction.
  3. **Drift detection — this deliverable.** Catches when leg 2 has
     been bypassed or when an artefact has drifted within the repo
     (an ADR added without an index update, a status word that breaks
     the parser, a Caddy site without a corresponding DNS record).

Detection runs at three points:

  - **Pre-commit** — fast, repo-only, **blocking**. Runs on staged files.
  - **CI on PR + push to main** — medium, no Plane network access,
    **blocking**.
  - **Scheduled CI nightly** — slow, advisory, **non-blocking**.
  - **Local cron on mac-mini nightly** — slow, queries live Plane,
    **alerts on drift**.

## §2 — Architecture

```
            ┌──────────────────────────────────────────────┐
            │  scripts/check-repo-coherence.py             │
            │  (stdlib only — runs anywhere with python3)  │
            └──────────────────────────────────────────────┘
                  ▲                  ▲                ▲
        ┌─────────┘                  │                └────────┐
        │                            │                         │
  ┌──────────┐            ┌────────────────────┐      ┌────────────────┐
  │pre-commit│            │   GitHub Actions   │      │ mac-mini cron  │
  │  hooks   │            │ validate-infra.yml │      │  (nightly)     │
  │ (local)  │            │ pull_request/push  │      │  full Plane    │
  │ blocking │            │     blocking       │      │  dry-run       │
  └──────────┘            └────────────────────┘      └────────────────┘
        │                            │                         │
        │ files staged               │ on PR + push to main    │ alert on
        │ matching `files:`          │                         │ drift
        ▼                            ▼                         ▼
  fix locally before              fail PR / block             cron output
  committing                      merge to main               + email/log
```

Plane-touching dry-run (`scripts/plane-sync-from-framework.py
--dry-run`) **does not run in GitHub-hosted CI** — it requires Vault +
Plane network access on mac-mini, and a deploy-key path adds a
credential surface that the simpler local-cron pattern avoids. Wiring
the cron entry on mac-mini:

```bash
# crontab -e (mac-mini, operator's user)
# Nightly Plane drift check at 03:42 local. Exit 2 = drift; cron's
# default mailer surfaces the body.
42 3 * * * cd /Users/admin/repos/integrated-ai-platform && \
  /Users/admin/.venv-block-4c/bin/python scripts/plane-sync-from-framework.py --dry-run \
    > /tmp/plane-drift-$(date +\%F).log 2>&1 || \
  cat /tmp/plane-drift-$(date +\%F).log | mail -s "Plane drift detected" $LOGNAME
```

`cross-index-validate.py` runs in the same cron block (its harness fix
makes this trivial — same Vault path, same env-derivation, same exit
contract).

## §3 — What each check enforces

| Check | Drift category | Where it runs |
|---|---|---|
| `adr-readme-sync` | ADR file added without `docs/adr/README.md` index update | pre-commit + CI |
| `decision-register-sync` | ADR file added without `docs/DECISION_REGISTER.md` row | pre-commit + CI |
| `framework-table-coherence` | PROJECT_FRAMEWORK row with bad status word or empty reference | pre-commit + CI |
| `caddy-internal-domains` | Inventory only — feeds `caddy-dns-parity` advisory job | scheduled CI |
| `netbox-services-have-adrs` | Phase 17 stub — exits 0 with NotImplemented note | CI (pass-through) |
| `cross-index-validate.py` | ADR not tracked in Plane | mac-mini cron |
| `plane-sync-from-framework.py --dry-run` | Plane state diverged from PROJECT_FRAMEWORK.md | mac-mini cron |

## §4 — How to run a check locally

```bash
# All checks at once (matches CI)
python3 scripts/check-repo-coherence.py all

# Individual subcommands
python3 scripts/check-repo-coherence.py adr-readme-sync
python3 scripts/check-repo-coherence.py decision-register-sync
python3 scripts/check-repo-coherence.py framework-table-coherence
python3 scripts/check-repo-coherence.py caddy-internal-domains
python3 scripts/check-repo-coherence.py netbox-services-have-adrs

# Plane-touching checks (need Vault running on mac-mini)
/Users/admin/.venv-block-4c/bin/python scripts/cross-index-validate.py
/Users/admin/.venv-block-4c/bin/python scripts/cross-index-validate.py --json
/Users/admin/.venv-block-4c/bin/python scripts/cross-index-validate.py --quiet  # CI-friendly

/Users/admin/.venv-block-4c/bin/python scripts/plane-sync-from-framework.py --dry-run
# Exit 0 = clean, exit 2 = drift pending, exit 3 = Plane saturated
```

## §5 — What to do when a check fails

### `adr-readme-sync` failure

```
FAIL: ADR files NOT linked from docs/adr/README.md:
  - ADR-A-017  (file: ADR-A-017-foo-bar.md)
```

Fix: open `docs/adr/README.md`, add a row in the index table:

```markdown
| [ADR-A-017](ADR-A-017-foo-bar.md) | Title from the ADR | Accepted |
```

Re-stage and commit. The hook re-runs and passes.

### `decision-register-sync` failure

Same shape. Open `docs/DECISION_REGISTER.md`, find the right category
section (or add one), and add:

```markdown
| [A-017](adr/ADR-A-017-foo-bar.md) | Title | One-line summary |
```

### `framework-table-coherence` failure

```
FAIL: PROJECT_FRAMEWORK.md row coherence (1 bad rows of 24 parsed):
  D-16-NN        status=`Maybe` (no valid prefix; expected one of [...])
```

Status column must begin with one of `DONE | IN PROGRESS | NOT
STARTED | DEFERRED`. Suffixes are allowed (`DEFERRED to Phase 17`,
`IN PROGRESS — blocked on R-12`). Reference column must be non-empty
— if you don't have a hash yet, use a placeholder like `(this commit)`
or `pending`.

### `cross-index-validate.py` failure (gap detected)

```
GAP: ADR-A-017 (Accepted) — Foo bar widget
```

Fix: backfill a Plane stub for the ADR using the same pattern as
`scripts/backfill-plane-labels.py`. The cron alert will clear on the
next run after the stub lands.

### `plane-sync-from-framework.py --dry-run` failure (exit 2)

The dry-run prints exactly which deliverables drifted and why:

```
~ deliverable-issue D-16-04        drift=[state]                   [D-16-04] Vault data in backup chain (raft snapshot)
```

Resolution path is **always: edit the markdown, re-run**. If the Plane
state was changed manually in the UI, the next APPLY run rewrites it
back to the markdown's truth (per ADR-A-006). To accept the Plane
edit, copy the new state into the markdown table first.

### `caddy-dns-parity` advisory annotation

This is informational. The CI runner can't query OPNsense Unbound, so
it prints the canonical Caddy site list and reminds the operator to
verify each domain resolves to `192.168.10.145` internally.

When OPNsense gains an exposed query API (or a DNS resolver becomes
reachable from CI), this advisory check is the natural upgrade
point — flip its `if:` filter and let it block.

## §6 — Adding a new check

Pattern (in `scripts/check-repo-coherence.py`):

```python
def cmd_my_new_check() -> int:
    # Read what you need; do the comparison; print FAIL/OK; return 1/0.
    ...
    return 0

CHECKS["my-new-check"] = cmd_my_new_check
```

Then add a corresponding pre-commit local hook (if applicable) and a
CI runner call. If the check needs network or credentials, route it
through the **mac-mini cron** path instead of CI — see §2.

## §7 — Disabling a check temporarily (emergency commit)

If a check is wrong (false positive) and you need to commit *now*:

```bash
git commit --no-verify -m "..."   # bypasses ALL pre-commit hooks
```

The CI side will still flag it on push; you have until the PR opens
to fix the underlying issue. **Always** log a known-issue (KI-NNN) if
you skip — the commit message should reference which check was
bypassed and why.

If a check is permanently wrong, fix the script — don't add a
per-file ignore. The hook is supposed to be authoritative.

## §8 — Doctrine D#15: pre-deliverable cleanliness gate

Doctrine D#15 (`docs/PROJECT_FRAMEWORK.md` §3.5) mandates that the
checks in §1–§5 of this runbook be run at the **start of every
deliverable** as preflight #0, BEFORE any substantive work begins.

The gate has two acceptable resolutions on failure:

1. Fix the drift as preflight #0 with explicit explanation in the
   resulting commit message, OR
2. Operator explicitly waives with a written reason, captured verbatim
   in the deliverable's commit message under a
   `Cleanliness gate waiver:` header.

Carrying drift silently into substantive work is treated as Sev-3
minimum. The gate result is surfaced before substantive work in the
form:

```
PREFLIGHT #0:
  git status:                    clean | <list>
  check-repo-coherence:          PASS | FAIL <detail>
  cross-index-validate:          PASS | FAIL <detail>
  phase-deliverable-count <N>:   <X of Y> | FAIL
  plane-sync --dry-run:          clean (exit 0) | drift (exit 1)
  xindex /healthz:               <N>/<N> sources ok | <detail>
  inherited KI:                  <list or "none">
GATE: PASS | FAIL — <action>
```

See also ADR-A-006 (single source of truth) and `docs/PROJECT_FRAMEWORK.md`
§3.5 (D#15 + D#16 doctrine entries).

## §9 — References

- ADR-A-006 — repo docs are canonical for architecture and roadmap planning
- `scripts/check-repo-coherence.py` — local checks (this deliverable)
- `scripts/cross-index-validate.py` — ADR ↔ Plane validator
- `scripts/plane-sync-from-framework.py` — repo → Plane one-way sync
- `.github/workflows/validate-infrastructure.yml` — CI runner
- `.pre-commit-config.yaml` — local hooks
- `docs/PROJECT_FRAMEWORK.md` §3.5 — D#15 + D#16 doctrine entries
- `docs/PROJECT_FRAMEWORK.md` §4 — surface format the dry-run feeds
