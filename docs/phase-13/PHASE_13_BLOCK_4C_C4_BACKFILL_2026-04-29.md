# Block 4.C C4 — Plane label back-fill

**Date:** 2026-04-29
**Scope:** Apply `RM-<PREFIX>-NNN` labels across 604 Plane issues. Operator-approved mappings (Decision 7) for unmatched prefixes: `CI`→`CI/CD`, `DEPLOY`→`Deployment`, `MON`→`MONITOR`.
**Outcome:** **603/604 issues correctly labeled, 0 mismatches, 1 issue intentionally skipped.**

This document captures the C4 gate sequence, the final state, and
pointers to the discoveries surfaced during execution. The full
discoveries narrative lives in
`PHASE_13_BLOCK_4C_C2_DISCOVERIES_2026-04-29.md` (cumulative #1–#16).

---

## C4.1 — Pre-flight memory hygiene

Discovery #13 surfaced before any C4 code ran: the plaintext Plane
token in `~/.claude/projects/.../memory/plane_deployment.md` and
the canonical `secret/plane/api#homepage_token` had **diverging
sha256 hashes** (memory `4d83dff62161` vs Vault `b90c7b634be7`).
Both tokens read-probed cleanly; the Vault token also passed a
write-probe (PATCH+restore on a label description).

Resolution path (operator-approved A1 + scope-probe):

- Vault token confirmed admin write scope → use it for the back-fill.
- Memory file plaintext redacted to a Vault path reference.
- C6 follow-up #9 registered to revoke the memory token via Plane UI.

A2 (fall back to memory plaintext) was explicitly forbidden — would
have left a plaintext credential in a file consumed by an active
script.

## C4.2 — Script + memory hygiene

`scripts/backfill-plane-labels.py` written. Reads token from Vault
via `docker exec vault-server vault kv get -field=homepage_token
secret/plane/api` (no argv leak). Pacing: 1 req/sec floor with 65s
backoff on 429.

Memory file `plane_deployment.md` line 14 redacted:
`Token reference: secret/plane/api#homepage_token (redacted from
plaintext on 2026-04-29 per Block 4.C C4 pre-flight)`

## C4.3 — Dry-run gate

Three discoveries surfaced before/during the dry-run:

- **Discovery #14:** `framework/plane_connector.py:296-299` had a
  non-terminating pagination loop. Plane V1's `next_cursor` is an
  always-incrementing offset; termination must check
  `next_page_results=False` (or empty `count`/`results`). First
  dry-run attempt ran ~43 minutes idle, accumulating ~2400 wasted
  GETs on empty pages. Connector patched.

- **Discovery #15:** First C4.4 attempt (post-Discovery #14 fix)
  PATCHed 26 issues then collapsed into a 429 storm. Three
  compounding bugs: (1) GET-then-PATCH per issue at 1 req/sec
  sustained = 120/min, double the Plane limit; (2) `RateLimitError`
  on the GET masked under broad `except Exception` (no retry); (3)
  single 65s backoff insufficient against sustained 2× pattern.
  Fix: drop the redundant pre-fetch GET — plan-stage inventory
  already captured each issue's existing labels. Apply loop now
  uses 1 req per issue.

- **Discovery #16 (the most insidious):** the post-Discovery-#15
  C4.4 run reported 603 PATCHes, 0 fails, 0 429s — clean by every
  script-level metric. Independent validation re-read showed
  every issue still had `labels: []`. Plane V1 PATCH expects
  `{"labels": [...]}`; the script sent `{"label_ids": [...]}`,
  which Plane silently accepted (200 OK) without mutating state.
  Two-line fix (rename payload key in both PATCH call sites).

Final dry-run output (post-fixes, after the 1 probe-mutation that
correctly labeled `cbcd3e52-… RM-AUTO-MECH-001`):

| Inventory | Value |
|---|---|
| Issues in project | 604 |
| Issues with `RM-` prefix | 603 |
| Issues without prefix | 1 (skip-no-prefix) |
| Distinct prefixes | 48 |
| Direct case-insensitive matches | 45 |
| Mapped per Decision 7 | 3 (CI, DEPLOY, MON) |
| Unmatched / errors | 0 |

Per-issue plan: `apply: 602`, `skip-already-labeled: 1` (the probe
issue), `skip-no-prefix: 1`.

## C4.4 — Live back-fill

Run started 2026-04-29 14:02:57.

- **Applied:** 602 (all post-Discovery-#16 fix)
- **Failed:** 0
- **429 backoffs:** 1 (handled cleanly by the backoff retry; my
  early-verify probe added 5 extra requests within the same 60s
  window that the apply loop was sharing)
- **Wall time:** ~10 minutes (matches dry-run estimate)
- **Apply log:** `/tmp/c4_apply.log` recorded 602 unique issue
  IDs, 1 `(after-429-retry)` entry, 0 FAIL/WARN.

### Early-verify (per operator step-5)

After the first 5 apply log lines, sampled re-GETs:

| Issue | Prefix | Label name | Re-GET `labels` |
|---|---|---|---|
| `cec76834-…` | AUTO-MECH | AUTO-MECH | `[a2023a0c-…]` ✓ |
| `c0194093-…` | CLI | cli | `[351c499f-…]` ✓ |
| `bd1fa1c6-…` | CLI | cli | `[351c499f-…]` ✓ |
| `6a1c5edc-…` | CLI | cli | `[351c499f-…]` ✓ |
| `7549fda7-…` | CLI | cli | `[351c499f-…]` ✓ |

All 5 mutations verified after PATCH. Discovery #16 fix confirmed
working at the wire level, 30 seconds into the run.

### Final-state validation (full re-read)

| Metric | Value |
|---|---|
| Total issues | 604 |
| Labeled | **603** |
| Unlabeled | 1 (`dfa89508-…` `[TEST] CMDB + AnythingLLM integration validation`, prefix=None — expected `skip-no-prefix`) |
| Mismatches (wrong label for prefix) | **0** |

### Label distribution (issue count per label, descending)

| Count | Label |
|---|---|
| 60 | testing |
| 43 | docs |
| 41 | MONITOR (10 from MON + 31 from MONITOR; Decision 7 collapse, empirically verified) |
| 36 | data |
| 31 | cli |
| 30 | UTIL |
| 30 | security |
| 30 | REFACTOR |
| 30 | CONFIG |
| 30 | api |
| 21 | media |
| 18 | OPS |
| 11 | DEV |
| 10 | UX |
| 10 | USERMGMT |
| 10 | SCALE |
| 10 | PERF |
| 10 | INT |
| 10 | FLOW |
| 10 | **Deployment** (mapped from DEPLOY, Decision 7) |
| 10 | **CI/CD** (mapped from CI, Decision 7) |
| 10 | BACKUP |
| 10 | APIGW |
| 8 | UI |
| 7 | GOV |
| 6 | SHOP |
| 6 | HOME |
| 6 | AUTO |
| 5 | SEC |
| 5 | REL |
| 5 | QA |
| 5 | PLUGIN |
| 5 | OBS |
| 5 | MOBILE |
| 5 | I18N |
| 5 | A11Y |
| 3 | LEARN |
| 3 | INV |
| 2 | HW |
| 2 | DOCAPP |
| 2 | CORE |
| 2 | AUTO-MECH |
| 1 | PERIPH |
| 1 | LANG |
| 1 | KB |
| 1 | INTEL |
| 1 | AI |

**46 distinct labels in use** out of 64 in the project. The 18 unused
labels are the labels that exist in the project but have no
corresponding issues yet (forward-looking categories from the agile
config); they are not a defect.

## Decision 7 — empirical confirmation

The three operator-approved unmatched-prefix mappings produced
exactly the predicted distribution:

| Source prefix | Issues | Target label | Final label count |
|---|---|---|---|
| `CI` | 10 | `CI/CD` | 10 |
| `DEPLOY` | 10 | `Deployment` | 10 |
| `MON` | 10 | `MONITOR` (collapsed with native MONITOR=31) | 41 |

The MON+MONITOR collapse on the `MONITOR` label is registered as a
C6 follow-up (#2) for cleanup decision; it is internally consistent
and not a defect.

## C6 follow-ups added during C4

(Cumulative count is approximate; see discoveries doc for full
narrative.)

- **#9** — Revoke the memory-file Plane token via Plane UI (different
  from the canonical Vault token; hash `4d83dff62161`). Manual
  operator action during C6 closeout.
- **#10** — Audit other consumers of `framework/plane_connector.py`
  for similar pagination assumptions (Discovery #14). Known callers:
  `bin/sync_roadmap_to_plane.py`, `bin/sync_plane_to_markdown.py`,
  `mcp/plane_mcp_server.py`.
- **#11** — Audit connector error class hierarchy: `RateLimitError`
  inherits from `Exception`, easy to mask under broad handlers
  (Discovery #15). Either reparent it or document the catch-order
  contract.
- **#12** — Canonical-pattern README: explicit catch-order requirement
  for connector consumers (specific exceptions before generic).
- **#13** — Dry-run coverage: simulate apply-loop request volume
  (would have caught Discovery #15's 2× rate budget bug).
- **#14** — Fix `framework/plane_connector.py:360`: `create_issue`
  builds `payload["label_ids"]`, the same wrong key as Discovery
  #16. Also explains *why* the back-fill was needed in the first
  place (the create-time bug silently dropped labels at sync). Audit
  other connector payload-builders for similar key mismatches.
- **#15** — Add "first-batch verify" pattern to canonical-pattern
  README: re-GET after the first PATCH and assert mutation took
  before sustaining a write-heavy run.

## Apply log retention

`/tmp/c4_apply.log` (tmpfs) records 602 `applied` lines + 1
`(after-429-retry)` annotation. Not preserved across reboot.
Adequate for the immediate audit window; not a long-term artifact.

## Lessons (carried forward into doctrine)

1. **HTTP 200 ≠ mutation succeeded.** Write-heavy scripts must verify
   by re-read, at least on the first PATCH of a run.
2. **Dry-run is a planning artifact, not a behavioural test.** It
   correctly answered "what will this do" but not "how will this
   consume the rate budget." Future write-amplifying scripts
   should price the apply loop's request cadence into the dry-run.
3. **Silent-noop API responses are real.** Plane V1 doesn't error
   on unknown payload keys. When integrating a new endpoint, probe
   both plausible field names with a re-GET before trusting the
   contract.
4. **API contracts must be tested explicitly.** Discovery #14's
   pagination terminator was a "plausible-sounding claim" never
   verified against actual response shape. The fix (probe an
   empty page directly) should be part of every paginated method's
   initial test.
5. **Catch-order matters.** `RateLimitError` inheriting from
   `Exception` makes it easy to mask. The PATCH handler did this
   right (specific first); the GET handler did not. Doctrine: when
   a script catches a base `Exception`, every specific subclass
   must be caught *first*.

## C4 close

C4 closes with the back-fill complete and validated. Ready for
operator approval to proceed to **C5 — registry deprecation**
(marquee gate).
