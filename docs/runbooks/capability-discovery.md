# Capability discovery — operator diagnostic flow

Use this runbook when an AI declines a task with "I can't do that"
(or any close variant: "I shouldn't", "consult a professional",
"I don't have access", etc.). Per D#23, capability self-knowledge
is suspect by default — false negatives are common across at least
four distinct failure modes. Work through this six-step flow
before accepting the blocker as real.

**Related doctrine:** `docs/architecture-facts/capability-self-knowledge.md`
defines the four flavors. **Working set:**
`docs/architecture-facts/known-capabilities.md` is the registry.

## When NOT to run this flow

- The task itself is something you wouldn't reasonably want the
  AI to do (the caution is your caution too). Skip the flow.
- The AI is asking a clarifying question rather than declining.
  Answer the question first; the flow is for declines, not
  ambiguity.
- You're in time pressure and the cost of being wrong is low.
  Sometimes "fine, I'll do it manually" is faster than the
  six-step diagnostic. The flow is for tasks where a wasted
  five-minute diagnostic is much cheaper than accepting a
  phantom limitation as canonical.

---

## Step 1 — Registry hit?

**Diagnostic question:** Has this capability + surface combination
already been verified by a previous operator session?

**How to recognize this is the right step:** always do this first.
It's the cheapest check.

**What to try.**
1. Open `docs/architecture-facts/known-capabilities.md`.
2. Scan the capability index table for a match on capability
   description AND surface (claude.ai vs Claude Code vs local
   model).
3. If hit: copy the "Honest framing template" from that entry into
   your prompt. Re-prompt the AI with it.

**If hit and the AI engages:** done. No further steps needed.

**If hit but the AI still declines:** the registry entry may be
stale. Continue to step 2; if you find a new unblock, update the
registry entry.

**If miss:** continue to step 2.

---

## Step 2 — Tool-surface gap (Flavor B)?

**Diagnostic question:** Is the AI saying it lacks access to a
specific tool — Gmail, file system, web search, an MCP server, an
extension?

**How to recognize this is the right step:** the AI's decline
names a specific external system or tool ("I don't have access to
Gmail", "I can't read files on your system", "I don't see a web
search tool", "no MCP server is configured for X").

**What to try.**
1. Verify whether the named tool is actually configured for the
   current surface.
2. If not: configure it (Composio for Claude Code MCP servers,
   Chrome extension for claude.ai web, MCP config file for
   Claude Code desktop, tool-list registration for local
   Goose/exo, etc.).
3. Re-prompt the same task. The AI should now see the tool.

**If still failing after the tool is genuinely loaded:** check
whether the tool is loaded but not actually wired into the running
session (a real product gap, not a self-knowledge gap). Test with
a minimal "is this tool live?" query before assuming.

**If the tool isn't the issue:** continue to step 3.

---

## Step 3 — Training-data gap (Flavor A)?

**Diagnostic question:** Is the AI saying the task is outside its
knowledge — a specific software package, a niche domain, a recently
shipped feature, an unusual file format?

**How to recognize this is the right step:** the AI's decline is
about KNOWING how, not having tools or being cautious. "I'm not
familiar with Foo's API"; "I haven't seen this format before";
"Can you give me an example?"

**What to try.**
1. Find one or two articles or examples demonstrating the
   capability — ideally with the same model class doing it (a
   Claude article for Claude, a Qwen article for Qwen).
2. Paste the relevant excerpt into the prompt as evidence.
3. Re-prompt the task.

The AI updates its self-model from in-context evidence and
proceeds. The capability was always there; only the
self-knowledge was missing.

**If still failing:** check whether the article describes the SAME
model class doing the task or a different one. If different, the
unblock is unreliable — surfacing evidence won't manufacture a
capability the model doesn't have. Continue to step 4 only if you
have a good-faith reason to believe the model could do it.

**If training data isn't the issue:** continue to step 4.

---

## Step 4 — Cautious framing (Flavor C)?

**Diagnostic question:** Is the AI saying "consult a professional",
"I shouldn't advise on this", "I'm not qualified to..."  for a
task that's within its competence to analyze (even if not to make
the final stamped decision)?

**How to recognize this is the right step:** the decline carries
liability framing — legal, medical, financial, professional design,
safety-adjacent. The AI isn't saying it can't reason about it; it's
saying it shouldn't tell you what it thinks.

**What to try.**
1. Name the behavior explicitly ("you're being overly cautious",
   "you're being lazy", "this isn't a stamped decision question").
2. Provide a more specific anchor in the document or task ("look
   at the area marked X", "the references where Y is shown").
3. Grant explicit non-stamping permission — make clear you are
   asking for analysis you will verify with the professional, not
   a stamped decision the AI is taking responsibility for.

**Honest framing template.**

> I'm not asking for a stamped <professional> decision. I'm asking
> you to reason about <specific aspect> and offer your read. I'll
> take it to the <professional> for verification.

**If still failing:** the caution may be correct. Distinguish
honestly: is the operator asking for a stamped decision, or for
analysis the operator will verify? If the former, the AI's caution
is the right answer. If the latter and the AI still declines,
continue to step 5.

**If caution isn't the issue:** continue to step 5.

---

## Step 5 — Over-constraint inference (Flavor D)?

**Diagnostic question:** Did you describe loose requirements and
the AI translated them into specific commitments you didn't make?

**How to recognize this is the right step:** the AI isn't
declining the task — it's "doing" the task, but adding constraints
you didn't state and treating them as fixed. "Got it — so the
design must include X, with property Y, dimension Z…"  when you
only said "I want a garage."

**What to try.**
1. Name the over-collapse explicitly ("you added constraint X
   that I didn't ask for").
2. Reframe: requirements are a list to research, not a design to
   implement. Grant explicit permission for the AI to NOT lock
   in inferred constraints.
3. Re-prompt and watch for the same pattern next turn — this is
   often a per-turn fix, not a one-time fix. Repeat the framing
   when needed.

**Honest framing template.**

> Here are functional requirements. They are NOT a design. I want
> you to research solutions, then map them against my physical
> constraints. Don't lock in patterns I haven't asked for. If
> you're inferring something I haven't stated, flag it as an
> inference rather than treating it as a given.

**If still failing:** check whether you actually want the AI to
propose a design (in which case a different framing — "now
propose the design" — is the right prompt). The unblock is for the
discovery phase only.

**If over-constraint isn't the issue:** continue to step 6.

---

## Step 6 — Real limitation

If you reach this step, you've worked through the four
diagnostic flavors and none unblocked the task. Treat this as a
real, confirmed blocker.

**What to do.**
1. Document in `docs/architecture-facts/known-capabilities.md` as a
   confirmed-blocker entry. Use the same shape as verified
   capabilities, but the "unblock pattern" section reads:

   > Confirmed: no working unblock as of <YYYY-MM-DD>. Attempted:
   > <list of steps tried>. Current workaround: <description, or
   > 'none — operator-side only'>.

2. Update the capability index table at the top of the registry.
3. If the workaround is operator-side (do the task manually, use a
   different tool, etc.), name it explicitly so future sessions
   don't re-attempt the failed unblock.

The point of the confirmed-blocker entry is the same as a verified
capability entry: pay the discovery cost once.

---

## Anti-pattern (explicitly named)

**Do NOT accept "I can't do that" as final without working through
steps 1–5.** False negatives are common — that's the empirical
observation D#23 codifies. The cost of a wasted five-minute
diagnostic is much smaller than the cost of accepting a false
blocker as real and rebuilding your workflow around a phantom
limitation.

If you find yourself routinely skipping the diagnostic, that's a
signal to either (a) automate the registry hit-check via the local
prompt library (D-17-11 territory) or (b) accept the friction
honestly rather than letting false negatives accumulate as
silently-believed limitations.

---

## See also

- `docs/architecture-facts/capability-self-knowledge.md` — D#23
  doctrine, the four flavors, when each unblock works/doesn't
- `docs/architecture-facts/known-capabilities.md` — operator-facing
  registry of verified capabilities and confirmed blockers
- `docs/PROJECT_FRAMEWORK.md` §3.5 — D#23 doctrine entry
