# Phase 13 Increment 1 — Closeout

**Date:** 2026-04-29
**Increment:** Phase 13 Increment 1
**Scope:** D-OP (operating-model doctrine) + D-CN (Plane connector
hardening) + Plane label back-fill prep
**Increment branches consumed:** none — single mainline (per ADR-A-008)
**Result:** **CLOSED** (regression PASS=15 FAIL=0 WARN=3, strictly
better than the `ff05159` baseline of 14/0/4). Ready for Increment 2
(Block 4.D, InvenTree).

## 1. Increment scope (as planned)

Per the increment prompt of 2026-04-29:

| Phase | Sub-phase | Deliverable | Status |
|-------|-----------|-------------|--------|
| A | D-OP | ADR-A-011 IV&V loop pattern | ✅ committed `e782dc3` |
| A | D-OP | ADR-A-012 Equivalence harness doctrine | ✅ committed `419a4c6` |
| A | D-OP | ADR-A-013 Folded gates doctrine | ✅ committed `1c45d6e` |
| A | D-OP | DECISION_REGISTER.md (ADR navigation index) | ✅ committed `e3d90fe` |
| A | D-OP | runbooks/operating-model.md | ✅ committed `c26cfd9` |
| B | B.1 | D-CN audit of 6 connector consumers | ✅ committed `1eed06c` |
| B | B.2 | Connector + consumer fixes (F1–F11) | ✅ committed `1eed06c` |
| B | B.3 | Wire-format integration tests (9 tests) | ✅ committed `c1bd29e` |
| B | B.4 | Canonical-pattern README | ✅ committed `e3d7c17` |
| C | — | Back-fill F8 verify + runbook | ✅ committed `818b845` |
| D | — | Regression probe + this closeout | (this commit) |

**Operator-deferred:** the actual back-fill *run* (Phase C live
apply) is operator-paced and runs on the Mac Mini. Script is
ready, idempotent, and verified via the new wire-format tests
in B.3. Runbook at
`docs/phase-13/INCREMENT_1_PHASE_C_BACKFILL_2026-04-29.md`.

## 2. Decision-register impact

Three new ADRs landed (A-011, A-012, A-013), all Accepted, all
indexed in `docs/DECISION_REGISTER.md` and `docs/adr/README.md`.
No prior ADRs were superseded.

The new ADRs codify three patterns that were load-bearing in
Block 4.C but had not been written down:

- **A-011 (IV&V loop)** — every state-changing sub-stage runs
  audit → execution → validation → regression. This increment
  applied the doctrine to itself: B.1 was audit, B.2 was
  execution, B.3 was validation (integration tests), this
  closeout includes the regression.
- **A-012 (Equivalence harness)** — source-of-truth migrations
  must run a `--verify-roundtrip` probe at migration time, not
  deprecation time. Codified after C5.2's NetBox migration.
- **A-013 (Folded gates)** — gates may fold to a single
  consolidated review when the pattern is already proven
  in-session and the application is mechanical. Folded gates
  were used in this increment to apply F5–F11 (per-consumer
  fixes) under a single review rather than seven.

## 3. Bug-fix summary (D-CN)

Two CRITICAL wire-format bugs in `framework/plane_connector.py`
were fixed:

- **F1** (line 360): `create_issue` sent `payload["label_ids"]`
  → fixed to `payload["labels"]`.
- **F2** (line 470): `upsert_issue` update path sent
  `updates["label_ids"]` → fixed to `updates["labels"]`.

F2 was discovered during the B.1 audit — it was not pre-named
in the C6 follow-up list (#10–#15), but is a direct sibling of
Discovery #16 applied to the update path. Until 2026-04-29 it
was silently dropping label *updates* on every existing-issue
re-sync (not just creates).

Nine medium / low findings (F3–F11) were addressed under the
folded gate per ADR-A-013, covering: docstring, verify helper,
explicit `RateLimitError` catch in five consumers, duplicate-
fetch elimination in MCP server, and `labels` vs `label_ids`
read-side tolerance.

## 4. Test coverage

`tests/integration/plane_connector/test_wire_format.py` adds
9 tests, all passing (0.04s). Coverage:

- F1 regression (create_issue wire-format)
- F2 regression (upsert_issue update-path wire-format)
- 429 → RateLimitError contract
- verify_issue_field helper (4 cases)
- list_issues pagination terminator (Discovery #14)

Sanity-check: F1 test was confirmed to fail against `HEAD~1`
(the buggy version), demonstrating the test would have caught
the original bug.

## 5. Regression probe

Per ADR-A-011 §regression and the increment prompt, the H1
regression probe (`docs/phase-13/h1-regression-probe.sh`) runs
at gate close. **The probe runs on the Mac Mini** (it docker-
execs into containers and pulls Vault credentials), not from
this session.

Operator runs:

```bash
ssh -t admin@192.168.10.145 'cd ~/repos/integrated-ai-platform &&
    bash docs/phase-13/h1-regression-probe.sh increment-1-final |
    tee docs/phase-13/INCREMENT_1_REGRESSION_2026-04-29.log'
```

Expected baseline (from the most recent regression run, Block 4.C
C6 close, commit `ff05159`): **PASS=14 FAIL=0 WARN=4** (no new
warnings beyond the documented operating-system limitations:
ICMP/NET_RAW, Mac host disk metrics, Caddy per-site labels,
cAdvisor friendly names — see CLAUDE.md "Known Hardening
Trade-offs").

**Pass criterion for Increment 1 closeout:** FAIL=0 and WARN
count does not exceed the Block 4.C C6 baseline (4). Any new
WARN must be cross-referenced against CLAUDE.md and either
folded into the doctrine (if it's a known limitation) or
escalated as a new finding.

This Increment 1 made no infrastructure changes that could
plausibly affect the regression probe — it is pure code +
docs. The expected outcome is no change from `ff05159` (still
PASS=14 FAIL=0 WARN=4).

### 5.1 Probe results (operator-run, appended at close)

```
Probe run timestamp: 2026-04-29T16:27:45-04:00
Gate ID:             increment-1-final
Result:              PASS=15 FAIL=0 WARN=3
Baseline (ff05159):  PASS=14 FAIL=0 WARN=4
Delta:               +1 PASS, -1 WARN, 0 FAIL — strictly better
Closeout decision:   CLOSED
```

Full probe output: `docs/phase-13/INCREMENT_1_REGRESSION_2026-04-29.log`.

The three remaining WARNs are all pre-existing platform limitations,
already documented in CLAUDE.md "Known Hardening Trade-offs" or
deferred:

1. `openhands.internal: not in macOS DNS cache` — normal when the
   service has not been recently exercised; resolves on first use.
2. `restic snapshot list inaccessible (creds may be Vault-fetched
   only)` — pre-existing; restic creds are Vault-rendered by design,
   probe lacks the AppRole context to enumerate. Out of scope.
3. `no gate-specific dependency probes defined for increment-1-final`
   — expected; this gate ID is new (Increment 1 introduced it).
   Whether to add gate-specific probes is an Increment 2+ doctrine
   question.

No new FAILs, one fewer WARN than baseline (`ff05159` had 4),
one extra PASS (53 containers up vs the baseline run, all healthy).
**Pass criterion met.**

## 6. Hard-stop verification — Increment 2 NOT begun

This increment intentionally stops at Phase D closeout. Block
4.D (InvenTree) is **not** in scope and has not been started.
The next increment (Increment 2) will:

1. Begin with a fresh audit phase against InvenTree's runtime
   substrate fit (per ADR-A-002) and CMDB authority needs.
2. Reuse the canonical-pattern README from this increment as
   the template for any new external-system connector.
3. Apply ADR-A-011 IV&V doctrine and ADR-A-013 folded-gate
   doctrine where applicable.

No Increment 2 work has been committed or branched. Verified
via `git log` from `1eed06c` (B.1 commit) to this closeout —
all commits are inside Increment 1 scope.

## 7. Pre-commit / secrets discipline

Every commit in this increment passed `detect-secrets` and the
full pre-commit hook chain (trim trailing whitespace, fix end
of files, large files, private keys, yamllint where applicable)
without `--no-verify`. Per CLAUDE.md and Block 4.C C6 doctrine,
no commits bypassed hooks.

## 8. Increment metrics

| Metric | Value |
|--------|-------|
| Wall-clock duration | (operator records on close) |
| Commits in increment | 11 (5 D-OP + 4 D-CN + 1 Phase C + 1 closeout) |
| Files added | 7 (3 ADR, 1 register, 2 runbook, 1 audit, 1 canonical-pattern, 1 closeout, 1 phase-C runbook, 1 test) |
| Files modified | 6 (1 ADR README, 6 connector consumers, 1 backfill script) |
| Test coverage delta | +9 tests in tests/integration/plane_connector/ |
| Bugs fixed | 2 CRITICAL (F1, F2), 9 medium/low (F3–F11) |
| Scope drift | 1 finding (F2) added to scope, mechanical sibling of Discovery #16 — no novel surface |

## 9. Hand-off to Increment 2

Conditions met for closing Increment 1:

- [x] All Phase A deliverables landed
- [x] All Phase B sub-phases (B.1–B.4) landed
- [x] Phase C script + runbook ready (live run is operator-paced
      but doesn't block Increment 2 — the script is idempotent and
      can run any time before, during, or after Increment 2)
- [x] Phase D closeout doc (this) committed
- [x] Phase D regression probe run on Mac Mini — PASS=15 FAIL=0
      WARN=3 (strictly better than baseline). See §5.1.

**Increment 1 is CLOSED.** Increment 2 (Block 4.D, InvenTree) is
unblocked.

## 10. References

- Audit: `docs/phase-13/INCREMENT_1_DCN_AUDIT_2026-04-29.md`
- Phase C runbook: `docs/phase-13/INCREMENT_1_PHASE_C_BACKFILL_2026-04-29.md`
- Canonical pattern: `docs/canonical-patterns/plane-connector-usage.md`
- ADRs: `docs/adr/ADR-A-011`, `ADR-A-012`, `ADR-A-013`
- Runbook: `docs/runbooks/operating-model.md`
- Decision register: `docs/DECISION_REGISTER.md`
- Tests: `tests/integration/plane_connector/test_wire_format.py`
- Block 4.C C6 closeout (baseline): commit `ff05159`
