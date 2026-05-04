# D-17-95 WP-06: Tier 1 Backlog Audit
# Date: 2026-05-04
# Status: SURFACE-BACK GATE

Ready-to-run `scripts/aider-task.sh` commands. Copy-paste and execute.
Each item has been classified against `docs/architecture-facts/work-routing-doctrine.md`.

---

## Category A — Standalone Tier 1 tasks (run now, no prerequisite)

### A-1: Add Finding 21 to integration-audit-doctrine.md

The work-routing-doctrine.md references Finding 21 in
`docs/architecture-facts/integration-audit-doctrine.md` but it doesn't
exist yet (doc currently ends at Finding 18). This is a pure append
with no live probes needed — the content is fully defined.

```bash
scripts/aider-task.sh --class C1 \
  "Append a new Finding 19 section at the bottom of this file: '## Finding 19 — Tier-classification is a pre-dispatch obligation, not a post-hoc label. Skipping classification and auto-routing to frontier was the root cause of zero operator-initiated LOCAL_AIDER invocations in an 18-day window (D-17-93). Every AI session must classify incoming work against Tier 1/2/3 before emitting the first tool call. Classifier: docs/architecture-facts/work-routing-doctrine.md (D-17-95). Chronicle: 2026-05-04.'" \
  docs/architecture-facts/integration-audit-doctrine.md
```

Note: the work-routing-doctrine.md referenced this as "Finding 21" but
the doc is currently at Finding 18. Append as Finding 19 (next sequential).
Update the work-routing-doctrine.md reference after:

```bash
scripts/aider-task.sh --class C0 \
  "Replace 'Finding 21' with 'Finding 19' in the Finding 21 section at the bottom" \
  docs/architecture-facts/work-routing-doctrine.md
```

---

### A-2: Add D-17-95 cross-reference to goose-capability-boundary.md

The Goose capability boundary doc has no pointer to the work-routing
classifier. The "Sibling chronicles" section at the top should include it.

```bash
scripts/aider-task.sh --class C0 \
  "In the 'Sibling chronicles' list near the top of the file, add a new bullet: '- \`docs/architecture-facts/work-routing-doctrine.md\` — Tier 1/2/3 work-routing classifier; Goose handles TIER 2 MCP-driven tasks (D-17-95)'" \
  docs/architecture-facts/goose-capability-boundary.md
```

---

### A-3: Add D-17-95 cross-reference to local-prompt-library-doctrine.md

The prompt library doctrine should reference the work-routing classifier
since they share the task-class (C0/C1/C2/C3) taxonomy.

```bash
scripts/aider-task.sh --class C0 \
  "In the cross-references section or related-docs section at the bottom of the file, add: 'Work-routing classifier (Tier 1/2/3): \`docs/architecture-facts/work-routing-doctrine.md\` (D-17-95)'" \
  docs/architecture-facts/local-prompt-library-doctrine.md
```

---

### A-4: Add type hints to domains/router.py public methods

`domains/router.py` has `classify()` and `_infer_task_type()` with no
type annotations. Inferrable from code without runtime.

```bash
scripts/aider-task.sh --class C0 \
  "Add type hints to all function signatures in this file that currently lack them. Use types from the existing imports (List, Optional, str, float). Do not add new imports." \
  domains/router.py
```

---

### A-5: Add docstring to scripts/aider-task.sh inline help

`scripts/aider-task.sh` has a `usage()` function built from comment
lines 2–20. It's missing a short one-liner at the very top of the file
(line 1 says `#!/usr/bin/env bash` then immediately dives into the
copyright comment block). Add a one-sentence description.

```bash
scripts/aider-task.sh --class C0 \
  "After the shebang line, add a comment line: '# Operator entry point for LOCAL_AIDER tasks. Routes via domains/router.py; executes bin/aider_local.sh. See docs/runbooks/aider-default-workflow.md.'" \
  scripts/aider-task.sh
```

---

### A-6: Fix the section heading numbering note in aider-default-workflow.md

The runbook now has sections 1–10 but the original D-17-94 header says
"D-17-94". Update header to note D-17-95 extension.

```bash
scripts/aider-task.sh --class C0 \
  "In the first line, change '# Aider default workflow (D-17-94)' to '# Aider default workflow (D-17-94, extended D-17-95)'" \
  docs/runbooks/aider-default-workflow.md
```

---

## Category B — Tier 1 components extractable from open deliverables

These are TIER 1 sub-tasks embedded in larger TIER 2 deliverables.
Run these now to make progress without opening a full Claude Code session.

### B-1: D-17-62 — Runbooks index doc (from D-17-62: Runbooks index + legacy-reference scan)

The index authoring is TIER 1 once the file list is in hand. The
legacy-reference scan is TIER 2 (grep + judgment). Run the index part now:

```bash
# Step 1 (run yourself to get the list):
ls docs/runbooks/*.md | sort

# Step 2 (Aider authors the index from the runbook files):
scripts/aider-task.sh --class C1 \
  "Author docs/runbooks/INDEX.md: a markdown table with columns 'Runbook', 'Description', 'Deliverable origin'. One row per file in docs/runbooks/. Derive descriptions only from the first paragraph of each file passed. Do not add facts not in the source files. Leave 'Deliverable origin' blank if not in the file." \
  docs/runbooks/aider-default-workflow.md \
  docs/runbooks/goose-operations.md \
  docs/runbooks/add-new-service.md \
  docs/runbooks/incident-response.md \
  docs/runbooks/vault-unseal.md
```

Run a second pass for the remaining runbooks (≤ 5 per invocation).

---

### B-2: D-17-54 — Apply frontier-verified corrections to opnsense-dhcp-dns-push.md

Once operator verifies the OPNsense Kea UI path (a prerequisite for D-17-54
close), the correction is a pure TIER 1 text edit:

```bash
# After operator confirms: "Services → Kea DHCPv4 → [Subnet] → DHCP options → option 6"
scripts/aider-task.sh --class C0 \
  "In the section that describes the OPNsense UI navigation path, replace the placeholder path with: 'Services → Kea DHCPv4 → [Subnet] → DHCP options → domain-name-servers (option 6)'" \
  docs/runbooks/opnsense-dhcp-dns-push.md
```

---

### B-3: D-17-52 — MacBook operator runbook skeleton (from Remote-work readiness)

The pre-departure checklist structure is fully deterministic from the
scope doc — no live probes needed for the skeleton:

```bash
scripts/aider-task.sh --class C1 \
  "Author docs/runbooks/macbook-remote-work-checklist.md: a pre-departure checklist for Singapore travel. Sections: (1) Headscale client status check, (2) .internal DNS resolution verification, (3) Vault access via Headscale, (4) If Headscale drops — fallback procedure (direct SSH to .145). Format as numbered checklist. Derive checklist steps only from the files passed; mark any step you cannot derive with [VERIFY]." \
  docs/runbooks/headscale-client-onboarding.md \
  docs/runbooks/macbook-headscale-enrollment.md
```

---

## Category C — Not Tier 1 (documented for completeness)

| Deliverable | Reason not Tier 1 |
|---|---|
| D-17-35 | Blocked on operator PDF drop — no coding task |
| D-17-43 | CMDB reconciliation requires runtime probes (NetBox API, docker inspect) |
| D-17-45 | Authority decision requires judgment across systems |
| D-17-92 | Deploy Cisco Provenance Kit — new script + integration testing |

---

## Execution order recommendation

1. A-1 (Finding 19 append) — closes a hanging cross-ref from work-routing-doctrine
2. A-1 follow-up (fix "Finding 21" ref in work-routing-doctrine)
3. A-2 (goose-capability-boundary cross-ref)
4. A-3 (local-prompt-library-doctrine cross-ref)
5. A-5 (aider-task.sh header comment)
6. A-6 (aider-default-workflow.md header update)
7. A-4 (router.py type hints) — lowest priority, pure quality
8. B-1 (runbooks INDEX.md) — start here for D-17-62 progress
9. B-3 (MacBook checklist skeleton) — unblocks D-17-52 partial progress

Items B-2 requires operator verification of OPNsense path first (TIER 2 prerequisite).
