# D-17-95 WP-06: Tier 1 Backlog Audit
# Date: 2026-05-04
# Status: SURFACE-BACK GATE

Ready-to-run `scripts/aider-task.sh` commands. Copy-paste and execute.
Each item has been classified against `docs/architecture-facts/work-routing-doctrine.md`.

---

## Category A — Standalone Tier 1 tasks (run now, no prerequisite)

### A-1: Add Finding 19 to integration-audit-doctrine.md

RECLASSIFIED TO TIER 2 (D-17-101): multi-paragraph structured finding
append into an existing long chronicle is doc-authoring and no longer
Aider-eligible.

```bash
Use Claude Code/Codex for this item.
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

RECLASSIFIED TO TIER 2 (D-17-101): multi-paragraph net-new doc authoring.

```bash
# Step 1 (run yourself to get the list):
ls docs/runbooks/*.md | sort

Use Claude Code/Codex for this item.
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

RECLASSIFIED TO TIER 2 (D-17-101): net-new runbook authoring.

```bash
Use Claude Code/Codex for this item.
```

---

## Category C — Not Tier 1 (documented for completeness)

| Deliverable | Reason not Tier 1 |
|---|---|
| D-17-35 | Blocked on operator PDF drop — no coding task |
| D-17-43 | CMDB reconciliation requires runtime probes (NetBox API, docker inspect) |
| D-17-45 | Authority decision requires judgment across systems |
| D-17-92 | Deploy Cisco Provenance Kit — new script + integration testing |
| D-17-95 A-1 | Structured finding append to existing chronicle (doc-authoring) |
| D-17-62 B-1 | Net-new runbook index authoring |
| D-17-52 B-3 | Net-new remote-work checklist authoring |

---

## Execution order recommendation

1. A-2 (goose-capability-boundary cross-ref)
2. A-3 (local-prompt-library-doctrine cross-ref)
3. A-5 (aider-task.sh header comment)
4. A-6 (aider-default-workflow.md header update)
5. A-4 (router.py type hints) — lowest priority, pure quality
6. Route A-1/B-1/B-3 to Tier 2 (Claude Code/Codex), not Aider.

Items B-2 requires operator verification of OPNsense path first (TIER 2 prerequisite).
