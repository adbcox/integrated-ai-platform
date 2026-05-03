# D-17-13 WP-08 chronicle — pending findings/notes

**Status: PROMOTED 2026-05-03.** Scratchpad retained as audit trail
of what was promoted where.

| Item | Promoted to |
|---|---|
| Finding 14 candidate (mDNSResponder negative-cache) | `integration-audit-doctrine.md` Finding 14 + `opnsense-dns-authority.md` "Consumer-side cache invalidation" section |
| F1.B refinement (qwen3-coder × Ollama 0.22.1 streaming) | `local-tool-calling.md` Finding 1.B (between F1 and F2) |
| F1.B.1 sub-finding (`<function` token leak in prose) | `local-tool-calling.md` Finding 1.B sub-section |
| WP-06 75/25 split + Phase-A baseline | `goose-capability-boundary.md` "Observed behavior" section |
| WP-06 cautious-by-default pattern | `goose-capability-boundary.md` "Patterns to preserve at Phase-A re-enable" |
| WP-06 padding tendency / self-blind to encountered failures | `goose-capability-boundary.md` "Patterns to correct via prompt engineering" |
| WP-06 cost/economics datapoint | `goose-capability-boundary.md` "Cost / economics observation" |
| smart_approve headless gotcha | `goose-capability-boundary.md` "Headless invocation gotcha" + `docs/runbooks/goose-operations.md` §1 + §3.4 |
| WP-07 PM-side dual-review observations | folded into the `goose-capability-boundary.md` sections above |

Backlog (not promoted; not D-17-13-blocking):

| Item | Where it should land |
|---|---|
| Framework script gap: `roadmap-create.sh --reopen` for DONE→IN PROGRESS | OpenProject backlog (RM-17 or follow-on) |
| D-17-12 WP-07/WP-08 unparking | Awaiting operator hand-grade returns |
| Mac Studio Ollama launchd plist registration | D-17-51 (separate deliverable) |

The original scratchpad content is preserved below for audit trail.

---

## Finding 14 candidate — macOS mDNSResponder negative-response cache

**Surface:** Mac Mini consumer-side DNS resolution after Dnsmasq record
creation on OPNsense.

**Observation (2026-05-03, D-17-13 WP-03):** After adding the
`mac-studio.internal` Shape 1 host record via OPNsense Dnsmasq API,
the Mac Mini continued to fail to resolve the hostname for an extended
window:

- `dig mac-studio.internal @192.168.10.1` → 192.168.10.142 (correct)
- `dns-sd -q mac-studio.internal` → `0.0.0.0 No Such Record` (negative cache)
- `python3 -c "import socket; socket.gethostbyname('mac-studio.internal')"` → `gaierror: nodename nor servname provided`
- `curl http://mac-studio.internal:11434` → `Could not resolve host`
- `dscacheutil -flushcache` → no effect

**Root cause:** macOS `mDNSResponder` caches negative responses
(NXDOMAIN) independently from the legacy `DirectoryService` cache that
`dscacheutil` flushes. A query that landed pre-record-creation pins the
NXDOMAIN until the mDNSResponder cache TTL expires or the daemon is
HUP'd.

**Fix:** `sudo killall -HUP mDNSResponder` (interactive sudo required).

**Sub-doctrine — D-17-21 runbook addition:** when adding a `.internal`
record via OPNsense Dnsmasq, the runbook must include a downstream
consumer-side flush step on any macOS host that may have queried the
hostname pre-creation. Specifically:

```
# After adding host record on OPNsense:
sudo killall -HUP mDNSResponder    # macOS consumers
sudo systemd-resolve --flush-caches # systemd-resolved consumers (Linux)
# Linux nscd/dnsmasq-local: nscd -i hosts / systemctl restart dnsmasq
```

**Sibling-not-duplicate of D-17-21 doctrine:**
- D-17-21 = DNS *authority* surface (who answers `*.internal` — Dnsmasq sole authority).
- F14 = DNS *cache invalidation* surface (how consumers learn the answer changed).
- Both must be correct for end-to-end resolution to work post-record-add.

**Promote to:** `docs/architecture-facts/opnsense-dns-authority.md`
(new section "Consumer-side cache invalidation") + cross-reference in
`docs/architecture-facts/integration-audit-doctrine.md` Finding 14.

**Verified blocking case:** D-17-13 WP-03 Goose end-to-end smoke test
against `mac-studio.internal:11434` was blocked until operator ran
`sudo killall -HUP mDNSResponder` on Mac Mini.

## WP-06 observations — Goose first test deliverable

**Date:** 2026-05-03 (D-17-13 WP-06)
**Test:** Goose drafts `docs/runbooks/goose-operations.md` from 3
source files (config/goose/config.yaml + scripts/goose/README.md +
goose-capability-boundary.md). Pure read+author, zero enaction.

**Session metrics:**
- Wall-clock: 51 seconds
- Tool calls: 6 (4× read_text_file, 1× list_allowed_directories,
  1× todo_write)
- All tool calls structurally valid; all paths within scope
- Capability-validation autonomous pattern held: model invoked
  list_allowed_directories before reads (same as WP-03 smoke test)

**Output split (empirical Phase-A baseline candidate):**
- ~75% of corrected runbook content originated in Goose's draft
- ~25% added/restructured during operator+frontier review:
  - Dropped padding sections (§5 Security checklist, §6 Backups)
  - Added GOOSE_MODE=auto headless invocation pattern (§1) — Goose
    didn't surface this even though it's the failure mode I just
    hit running the test itself
  - Deepened §3.3 (three distinct hang causes vs "Ctrl+C, restart")
  - Dropped redundant capability list, kept chronicle link only
  - Added (D-17-13) provenance suffix to title
  - Added §4 operator-review-obligation section (not in draft)

**Sub-findings to promote at WP-08:**

1. **Phase-A promotion baseline:** 75/25 Goose/frontier split is the
   first measured data point. Promotion gate criterion 1 ("N>=5
   clean reviewed executions") should track this ratio over N=5+
   sessions; if the ratio doesn't move toward Goose-dominant, that
   itself is a signal capability-validation should extend or the
   model is at its ceiling for this work-class.

2. **F1.B sub-finding — emission-noise glitch:** During WP-06,
   qwen3-coder:30b emitted a stray `<functionI'll draft...` prefix
   that mixed prose continuation with a partial function-call
   token. Did NOT corrupt the actual tool_calls JSON (those were
   structurally valid). This is occasional emission noise specific
   to qwen3-coder:30b in extended-prose contexts, not a blocking
   defect. Append to local-tool-calling.md under F1.B.

3. **Padding-section tendency:** Goose's draft added §5 Security
   checklist and §6 Backups that weren't asked for and didn't fit
   the runbook's reference-style. Prompt-engineering opportunity:
   future briefs should explicitly instruct "if uncertain about a
   section, omit rather than pad." Track in capability-boundary
   chronicle as a posture note for Phase-A prompt construction.

4. **Capability-validation autonomous pattern (positive signal):**
   Model autonomously runs list_allowed_directories before reads
   despite no instruction to do so. This cautious-by-default
   posture is exactly what capability-validation wants to *preserve*
   when promoting to Phase-A — re-enabling `developer` should not
   regress this pattern. Note in goose-capability-boundary.md
   "Posture 2 — Phase-A active" section when authored.

5. **Headless-invocation gotcha (smart_approve mode):** Goose's
   default `smart_approve` mode blocks any non-interactive run that
   triggers a tool-approval prompt. Even read-only tools (todo_write
   to internal state) fire the gate. Headless invocation requires
   `GOOSE_MODE=auto` env override per-invocation. Documented in
   goose-operations.md §1; sub-doctrine: per-invocation override is
   correct (don't change config default), so interactive sessions
   keep the approval gate.

## WP-07 — Dual-review observation (PM-side)

**Date:** 2026-05-03 (D-17-13 WP-07)
**Method:** No separate artifact; observations folded into WP-08
chronicle per operator decision. The "dual-review" is the WP-06
test packet itself: Goose proposed → operator reviewed → frontier
authored → operator approved.

### PM-side observations (operator + frontier shared view)

1. **Surface-back fidelity: high.** Goose's draft surfaced its own
   defects at the same grain as Codex/Claude Code surface-backs —
   padding sections + missing GOOSE_MODE failure mode were both
   findable in the draft without operator running the script
   themselves. This matters for promotion: it means operator can
   review Goose output as a *peer* of frontier output rather than
   needing a different review modality.

2. **Reasoning quality: 75/25 split.** Goose-draft / frontier-
   correction. Acceptable Phase-A baseline. Track over N=5+ to
   confirm directionality (toward Goose-dominant = capability-
   validation working; flat or regressing = either model ceiling
   or work-class mismatch).

3. **Cost delta validates §18.O migration economics.** 51 seconds
   wall-clock + local compute on Mac Studio = meaningfully cheaper
   than the equivalent Codex/Claude Code invocation for the same
   work-class (read 3 files, draft a runbook). The §18.O thesis —
   migrate execution surface progressively to local T3-B with
   frontier doing correctness review — has its first measured
   data point on this side of the move.

4. **Cautious-by-default pattern is dual-confirmed.** Goose ran
   `list_allowed_directories` autonomously in BOTH WP-03 (smoke
   test) and WP-06 (runbook draft) without instruction. Two
   datapoints isn't proof of habit, but it's enough to mark this
   as a behavior-to-preserve when re-enabling `developer` at
   Phase-A: capability scope-checks before write/exec are the
   model's own posture, not just operator-imposed.

5. **Prompt-engineering opportunity: standard Goose preamble.**
   Goose's tendency to pad uncertain sections (§5/§6 in the
   runbook draft) suggests a recurring corrective instruction
   should live in a standard prompt preamble rather than each
   per-task brief: "If uncertain about whether a section is
   necessary, omit rather than pad. Reference-style runbooks are
   concise; sections-because-runbooks-have-them is wrong." Track
   as Phase-A prompt-construction sub-doctrine.

### What this adds to F1.B

F1.B (qwen3-coder:30b structured tool_calls in streaming mode) is
the substrate-level unblocker. WP-07 observations are the
*workflow-level* corollary: at the substrate level the model emits
correctly; at the workflow level the model also surfaces its own
defects at frontier-grade resolution. Both are needed for
capability-validation phase to clear; neither alone is sufficient.

## Other items pending for WP-08

- F1.B refinement: qwen3-coder:30b emits structured tool_calls in
  *streaming* mode via Ollama 0.22.1 — refines original F1
  (qwen2.5-coder via Ollama 0.20.7 streaming dropped tool_calls) along
  the (model-family × Ollama-version) axis. Promote to
  `docs/architecture-facts/local-tool-calling.md`.
- Framework script gap (operator-flagged backlog, NOT D-17-13 blocker):
  `roadmap-create.sh` lacks a `--reopen` mode for DONE → IN PROGRESS
  reopens on unblocker resolution. WP-08 should record this; not in
  scope to fix.
- CLAUDE.md execution-surface section: add Goose to the
  "execution-surface" mental model (Claude Code + Codex + Goose), with
  capability-boundary note (developer extension disabled in
  capability-validation phase).
- Capability-boundary chronicle: `goose-capability-boundary.md` —
  documents the disabled-extension list, the rationale ("no docker/
  ssh/Vault access initially"), and the Phase-A promotion gate (N>=5
  clean executions before re-enabling `developer`).
