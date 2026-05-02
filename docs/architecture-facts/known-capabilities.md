# Known capabilities — operator working registry

**Status:** Operator working set. NOT exhaustive. Anthropic ships
features faster than this registry can track. The purpose is to
preserve hard-won unblocks so each false negative is paid for
once, not repeatedly.

**Doctrine:** D#23 (capability self-knowledge is suspect by default
— see `docs/architecture-facts/capability-self-knowledge.md`).

**How to use this file**
- Hit before accepting "I can't do that" from an AI.
- If a capability + surface combination is here: paste the
  honest-framing template; proceed.
- If it's not here and the operator unblocks something new: add an
  entry so the next operator (often the same operator, three weeks
  later) doesn't re-pay the cost.
- Confirmed-blocker entries (where unblocks were attempted and
  failed) are equally valuable — they prevent wasted re-attempts.

**Add an entry when:** a capability has been verified at least once
with a documented unblock, OR confirmed as a real blocker after
working through the full six-step diagnostic in
`docs/runbooks/capability-discovery.md`.

---

## Capability index

| # | Capability | Surface(s) verified | Failure flavor | Status |
|---|---|---|---|---|
| 1 | Spatial reasoning / floor-plan analysis from architectural PDFs | claude.ai (verified); Claude Code (operator-reported) | C — cautious framing | Verified with unblock |
| 2 | Gmail email retrieval and correspondence search | claude.ai with MCP loaded (verified); Claude Code with Chrome extension (verified) | B — tool-surface gap | Verified with unblock |
| 3 | Multi-turn iterative design with constraint refinement | claude.ai (verified) | D — over-constraint inference | Verified with unblock |

---

## 1. Spatial reasoning / floor-plan analysis from architectural PDFs

**Surfaces verified.** claude.ai (transcript-confirmed 2026-05-02);
Claude Code (operator-reported separate session).

**Failure flavor.** C — cautious framing. Default response declines
on grounds of professional liability ("I should not fabricate
specifics about exact dimensions or setbacks I can't verify";
"I don't think I can responsibly point at the plan and say 'build
it here'"; offers deflection workaround "send to the architect").

**Unblock pattern.**
1. Name the behavior explicitly ("you're being cautious / lazy").
2. Provide a specific anchor in the document ("look at the area
   marked X" / "the references where Y is shown").
3. Grant explicit non-stamping permission — make clear the operator
   is asking for analysis they will verify with the professional,
   not a stamped decision the AI is taking responsibility for.

**Honest framing template (paste into prompt).**

> I'm not asking for a stamped architectural decision. I'm asking
> you to reason about the geometry visible in the plans and offer
> your read. I'll take it to the architect for verification.

**When the unblock doesn't work.** Asking for a stamped decision
the AI should reasonably refuse to make. The unblock is for
"reason and read", not "decide and own."

**Evidence.**
`/Users/admin/intake-parking/2026-05-02-d-17-23-transcript-analysis.md`
Pattern 1 (transcript lines 70–86 — the pivot moment).
Initial intake source articles in
`/Users/admin/intake-parking/2026-05-02-d-17-23-capability-self-knowledge.md`
§"Example 1".

---

## 2. Gmail email retrieval and correspondence search

**Surfaces verified.** claude.ai with Gmail MCP loaded
(transcript-confirmed 2026-05-02 — clean retrieval of real email
threads). Claude Code on web (operator-reported initial decline,
then engagement after Chrome extension was opened).

**Failure flavor.** B — tool-surface gap. The same model class on
two different sessions gives opposite answers about Gmail
capability — both truthful, for their respective tool surfaces.
"I can't see Gmail" is honest when the MCP / extension isn't
loaded; "Here are your threads" is honest when it is.

**Unblock pattern.**
1. Verify Gmail tool is configured for the current surface.
2. If not: configure via Composio (Claude Code) or open Chrome
   extension (claude.ai web).
3. Re-prompt the same task; the AI now sees the tool.

**Honest framing template (paste into prompt when unsure).**

> Do you have Gmail tool access in this session? If not, here's
> how to configure it: <link to Composio / extension docs>. If
> yes, please retrieve <X>.

**When the unblock doesn't work.** The tool exists at the OS level
but isn't actually wired into the running session
(framework-level gap, not self-knowledge gap). Verify via a tool
list or simple test query before assuming the tool is live.

**Evidence.**
`/Users/admin/intake-parking/2026-05-02-d-17-23-transcript-analysis.md`
Pattern 3 (successful retrieval, lines 2050–2310). Empirical
contrast across surfaces in the same intake doc, plus
`/Users/admin/intake-parking/2026-05-02-d-17-23-capability-self-knowledge.md`
§"Example 2" for the source articles operator used.

---

## 3. Multi-turn iterative design with constraint refinement

**Surfaces verified.** claude.ai (transcript-confirmed 2026-05-02
across many turns; pattern persists across the session, with
operator unblocking each instance).

**Failure flavor.** D — over-constraint inference. Operator
describes loose functional requirements; AI collapses them into
specific premature commitments and treats those commitments as
fixed. Operator must walk back the AI's helpful additions every
iteration. Cost is repeated de-confliction work.

**Unblock pattern.**
1. State explicitly that requirements are a list to research, not
   a design to implement.
2. Grant explicit permission for the AI to NOT lock in inferred
   constraints.
3. When the AI collapses anyway, name the collapse ("you added X
   that I didn't ask for"); the AI resets and the next turn is
   usually cleaner.
4. Repeat as needed across the session — this is a per-turn fix,
   not a one-time fix.

**Honest framing template (paste into prompt).**

> Here are functional requirements. They are NOT a design. I want
> you to research solutions, then map them against my physical
> constraints. Don't lock in patterns I haven't asked for. If
> you're inferring something I haven't stated, flag it as an
> inference rather than treating it as a given.

**When the unblock doesn't work.** When the operator actually
wants the AI to propose a design (later phases of the same task);
at that point a different framing — "now propose the design" — is
the right prompt. The unblock is for the discovery phase only.

**Evidence.**
`/Users/admin/intake-parking/2026-05-02-d-17-23-transcript-analysis.md`
Pattern 2 (transcript lines 220–270 — multiple constraint-walkback
cycles in succession).

---

## Adding an entry

When an operator unblocks a new capability (or confirms a
blocker), append a numbered section in the same shape as above:

- **Surfaces verified** — list with a short note on what was tried
- **Failure flavor** — A / B / C / D, with the specific framing the
  AI used
- **Unblock pattern** — numbered, action-oriented
- **Honest framing template** — paste-ready prompt content
- **When the unblock doesn't work** — name the edge cases honestly
- **Evidence** — file paths or transcript references that future
  operators can audit

Confirmed-blocker entries follow the same shape, but the
"unblock pattern" section reads "Confirmed: no working unblock as
of <date>. Attempted: <list>. Current workaround: <description, or
'none — operator-side only'>."

Update the capability index table at the top of the file when
adding an entry; keep numbering monotonic.
