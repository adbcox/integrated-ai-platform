# Candidate Tools

Tools observed in the 2026-04-30→05-01 article-intake window
(deliverable 17.S) that may warrant evaluation against a specific
platform need. Listed here so the option exists when the need
matures — not endorsed, not committed.

Each entry includes scope-gating: what would have to be true for
this tool to make sense, and what would have to be true for it to
NOT make sense (so the bar to adopt is explicit, not vibes).

---

## Inbox Zero — AI-assisted email triage (Gmail tier scope-gated)

**Tool.** Inbox Zero (open-source, ~MIT-licensed AI email assistant
that proposes archive/label/respond actions and lets the user
batch-approve). Runs against Gmail OAuth.

**Scope-gate (would make sense if).**
- Operator's Gmail volume materially exceeds the 5–10 min/day
  triage budget AND
- A future Gmail OAuth deliverable is in scope (currently gated
  per `secret/gmail/oauth` external prereq) AND
- The triage actions Inbox Zero proposes are inspectable (not
  black-box) and run via the operator's own Gmail OAuth, not a
  third-party broker.

**Scope-gate (would NOT make sense if).**
- Gmail tier is "personal use, low volume" — manual triage is
  faster than reviewing AI proposals AND
- Operator prefers email-as-a-stream rather than email-as-a-task-
  queue (Inbox Zero's whole framing is the latter).

**Adjacent platform fit.** If adopted, deploy in the same pattern
as other AI-touching services: Vault-mediated OAuth (no creds in
env), Caddy site, NetBox CMDB row, xindex registration. Local LLM
backend (litellm → Ollama) — must NOT depend on Anthropic API per
LLM Access Doctrine in CLAUDE.md.

**Action threshold.** Revisit when a Gmail OAuth deliverable is
opened. Until then, this entry is a bookmark, not a commitment.

---
