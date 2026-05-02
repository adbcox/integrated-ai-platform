# Capability Audit Template

**Purpose.** Apply D#20 — establish evidence for any retirement
recommendation, OR document why a tool has a unique role and stays.

**Output location.** Per-tool audits at
`docs/audits/capability/{tool-name}-{YYYY-MM-DD}.md`. The audit doc
IS the artifact; the template is the methodology.

**When to trigger.**
- Stack audit (e.g. D-17-01) flagged a tool for review
- New service proposed; capability check ensures non-overlap (D#18)
- Phase-boundary review surfaced a tool that hasn't been audited
- Operator skepticism (always valid — see 2026-05-01 Zabbix lesson:
  pattern-matched "this looks redundant" recommendations are exactly
  what D#20 exists to prevent)

---

## Template structure

Every per-tool audit MUST have these six sections in this order.
Each section's purpose is fixed; the content fills the structure.

### Section 1 — Tool identification

- **Name** (canonical CMDB name)
- **Deployment location** (host, container, plain process)
- **Version** (probed, not assumed)
- **Source** (compose file path, official image, custom build)
- **First deployed** (commit hash and/or phase, if known)
- **Current resource cost** (RAM, CPU, disk, container count)

This section is descriptive, not evaluative.

### Section 2 — Probed capabilities (NOT documented capabilities)

Probe the running instance. What is it ACTUALLY doing right now?
- For databases: row counts, table list, query patterns
- For services: API surface area, integrations, traffic volume
- For schedulers: jobs configured, last-run status
- For monitors: items collected, hosts watched, triggers active

**Rule:** Each capability gets evidence — the probe command and the
output excerpt. No evidence ⇒ the capability doesn't count.
Documented-but-unused capabilities are noted separately as
"available but not exercised."

### Section 3 — Stack-coverage check

For each probed capability from Section 2:
- **What other tool in the stack covers this?** Be specific — cite
  the tool by NetBox name, not "we have something for that."
- **If "no other tool":** this is unique. Document why.
- **If "another tool covers":** is it cleaner there? Why or why not?
  Cleaner means: less config, fewer integrations, better data model
  fit, lower maintenance burden — pick the dimension and justify.

This section is where the D#20 evidence lives. Hand-waving here
defeats the purpose of the audit.

### Section 4 — Verdict

Choose exactly one:

- **KEEP** — unique role; document the role explicitly so future
  audits don't re-litigate
- **KEEP WITH ROLE-CLARIFICATION** — overlaps exist, but distinct
  enough to coexist; clarify which tool owns which capability
- **RETIRE** — every capability has a cleaner home (Section 3 must
  show this for every capability listed in Section 2)
- **FIX-OR-RETIRE** — currently broken; if fixable in <X hours, fix;
  else retire (state the X)

The verdict is the decision; Section 5 is its consequence.

### Section 5 — If RETIRE: migration plan

Skip if verdict is KEEP / KEEP WITH ROLE-CLARIFICATION / FIX-OR-RETIRE.

If RETIRE:
- **What replaces each capability** (1:1 mapping back to Section 2)
- **What data needs migration** (schemas, time-series, configs)
- **What references in repo/Plane need updating** (NetBox device
  links, runbooks, dashboards, alert routes, ADR back-refs)
- **Effort estimate** (hours; calibrated to comparable past
  retirements, not optimistic)

### Section 6 — Decision log

- **Auditor:** (name + role; "Claude session" is acceptable when
  human-reviewed)
- **Date:** (YYYY-MM-DD)
- **Verdict reviewed by operator:** (yes/no/pending)
- **Source of capabilities probed:** (which probe scripts, which
  containers — for reproducibility on a re-audit)
- **Linked ADRs / discoveries / Plane issues:** (back-refs)

---

## Failure mode this prevents

Pattern-matched "this looks redundant" recommendations.

The Zabbix vs VictoriaMetrics analysis (2026-05-01) is the worked
example — see `docs/audits/capability/zabbix-2026-05-01.md`. The
initial recommendation from a stack-level pattern-match was
"retire Zabbix; VictoriaMetrics covers this." Section 2 + Section 3
evidence reversed it: 4,593 SNMP items + 510 JMX items have no
clean home in VictoriaMetrics. Verdict: KEEP WITH ROLE-
CLARIFICATION, with one narrow overlap (706 host-metric items)
queued for cleanup.

Without this template, the retirement would have happened, and the
SNMP + JMX coverage would have silently disappeared until something
broke.

### Audit discipline rule

The logical-plane (D-17-01) stack audit's "quiet duplicate" or
"retire candidate" findings are HYPOTHESES TO TEST, not verdicts.
Each must go through this template to verify. The D-17-07 topology-api
review (2026-05-01) reversed an initial retire-candidate flag after
probing revealed unique Grafana-Node-Graph adapter capability
(field-shape transform + `depends_on`-edge computation that no
other tool in the stack provides). Per D#20: capability evidence
is required before retirement, even when logical analysis suggests
redundancy.

Two reversals so far (2026-05-01):
- D-17-02: Zabbix "retire as redundant with VictoriaMetrics" → KEEP
  WITH ROLE-CLARIFICATION (4,593 SNMP + 510 JMX items unique).
- D-17-07: topology-api "quiet duplicate of xindex_get_service" →
  KEEP WITH ROLE-CLARIFICATION (Grafana Node Graph adapter unique).

The template is doing its job.

---

## Triggering an audit (checklist)

Use this when deciding whether to run an audit:

- [ ] Stack-audit recommendation? (highest signal — usually right
      that an audit IS warranted; not always right about the verdict)
- [ ] Operator skepticism? (always run the audit; see Zabbix above)
- [ ] New tool being proposed that overlaps an existing one?
      (audit the existing one first; the answer might be "the new
      tool is the wrong addition," not "the old tool is the wrong
      retention")
- [ ] Phase boundary? (sweep tools that haven't been audited;
      D#19 codifies this)
- [ ] "Why do we still have this?" thought? (run the audit; the
      answer is the audit doc)

If none of these apply, the audit is probably premature.
