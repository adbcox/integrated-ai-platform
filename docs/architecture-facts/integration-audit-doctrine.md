# Stack-integration audit — doctrine

Chronicle of the doctrine that governs how subsystem closure is
verified to compose into integrated-system capability. Items here
outlive any single deliverable; new findings append to the bottom
with date + originating WP.

This chronicle exists because Phase 17 produced 25 deliverables that
each closed cleanly on their own scope, yet the operator's
autonomous-coding goal — agent transparently consuming registry /
cross-index / provenance / inventory / asset / project-management
state — was not verified end-to-end. Subsystems work;
system-as-architecture had not been verified. D-17-32 traced the
gap.

---

## Finding 1 — Stack-integration audit becomes recurring at every phase boundary

**Date:** 2026-05-03
**Originating WP:** D-17-32 (autonomous coding stack integration audit)
**Severity:** Doctrine (governs how subsequent phases close)

### What

Subsystem-level closure does not equal integrated-system-level
capability. A deliverable can be DONE on its own scope and still leave
the integrated flow it participates in broken at the seam.

D-17-32 audited Phase 17 against six target flows (Inference,
InvenTree, Asset/firmware, Provenance, Documentation, Project
management) and found 16 gaps — three B-severity blockers
concentrated in seams between subsystems, not within any single
subsystem:

- **F1** — `autonomous-coding` category missing in OpenProject;
  CLAUDE.md doctrine references a filter that returns nothing
  (D-17-31 close-loose-end)
- **X1** — Service registry has no MCP/agent surface; D#25 doctrine
  has no clean execution path (D-17-29 close-extension)
- **C1** — No asset/firmware/OS register exists; the 2026-05-02
  macOS-upgrade incident was the worked example (asset-mgmt family
  intake-doc'd but not framework-authored)

All three are seams *between* subsystems, not failures within them.
Each subsystem (OpenProject, registry, asset-tracking-substrate)
either works or is correctly framed as out-of-scope; the integration
points are what's missing.

### Why it bit us

Phase-17's deliverable charter optimized for closing scoped work
items. Each closeout verified the subsystem in isolation. No
deliverable explicitly took on "is the *combined* surface usable by
an agent without operator hand-holding."

CLAUDE.md doctrine ("filter by category=autonomous-coding";
"convenience reader for registry") asserted integration paths that
agents would follow — but the surfaces those paths assume (the
category, an MCP wrapper) had not been built. Doctrine drift in two
directions: (a) doctrine asserting features that don't exist (F1, F2);
(b) doctrine assuming agent ergonomics around a substrate that's only
operator-ergonomic (X1).

### Doctrine takeaway

**Every phase plan must include a stack-integration audit as a
phase-close deliverable** (named `D-NN-INT` or equivalent). Audit
format:

1. Enumerate target flows for the phase's autonomous-coding posture
   (typically 4-8 flows that compose the integrated system the
   operator is working toward).
2. For each flow: state happy path, structural requirement (what must
   hold for the flow to be integrated, not subsystem-only),
   integration boundary (the seam most likely to be the gap).
3. Trace each flow end-to-end against actual current state. Verify by
   command output, not by inference from "subsystem X is DONE".
4. Classify gaps: B (blocks autonomous coding outright), D (degrades
   quality), N (nice-to-have). Map each gap to: roadmap item present?
   in OpenProject queue? tagged correctly?
5. Surface back to operator BEFORE queueing remediation deliverables.
   Operator confirms backlog ordering matches the autonomous-coding
   goal.
6. Commit audit doc + gap report + prioritized backlog as the
   deliverable; remediation gets queued in the next planning pass,
   not in the audit.

Constraint: audits are AUDIT-only. No code changes during the audit
window. Hard cap on audit duration (D-17-32 used 4h for 6 flows + 16
gaps).

### Sub-doctrine — close-loose-end discipline

When a deliverable's close asserts a doctrine line ("agents can do X
via Y"), the closer MUST verify that Y exists at close time. D-17-31
asserted two lines that did not match reality:

- "filter by `category=autonomous-coding`" — the category did not
  exist
- "convenience: `--query-backlog [--autonomous-coding-only]`" — those
  flags were not implemented

Both were caught by D-17-32 (Gaps F1 + F2). Future deliverables that
update CLAUDE.md or any doctrine surface must include an explicit
verification step ("doctrine line X verified against actual surface Y
on date Z") in the closeout.

### Sub-doctrine — operator-side actions count as gaps

Some integration gaps require operator action that no deliverable can
perform autonomously (e.g., F1 needs the operator to click through
OpenProject UI to create the category). These are gaps; they must
appear in the gap report; they should be surfaced explicitly so the
operator can schedule them. "Operator-only" is not a reason to omit
from the inventory — it's exactly the kind of thing that gets
forgotten without a tracked surface.

### Sub-doctrine — negative datapoints count

D-17-32 WP-04 included a parallel-session audit (operator concern that
a different chat window may have created a roadmap artifact). The
audit found nothing was created. Per operator instruction:
**document this as an honest negative datapoint, not as positive
validation.** D-17-31's roadmap → OpenProject sync mechanism remains
untested by external work since its 2026-05-03 close. Future audits
should preserve the same discipline: report what was verified, not
what would have been nice to verify.

### Status

**Active doctrine.** Applies to every phase boundary going forward.
First application: D-17-32 (this deliverable). Next expected
application: Phase-18 close.

Cross-references:
- Audit format reference: `docs/_audit/integrated-stack-target-2026-05-03.md`
- Audit gap report reference: `docs/_audit/integrated-stack-gaps-2026-05-03.md`
- Audit backlog reference: `docs/_audit/integrated-stack-backlog-2026-05-03.md`
- Related: D#22 (architecture-facts as canonical), D#25 (registry consultation), D#23 (capability self-knowledge is suspect)
