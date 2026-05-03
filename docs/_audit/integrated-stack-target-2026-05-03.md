# Integrated stack — target state (D-17-32 WP-02)

**Date:** 2026-05-03
**Deliverable:** D-17-32 (autonomous-coding stack integration audit)
**Status:** Audit input — defines the "integrated" target against which WP-03 traces actual state.

This document does not assert what exists. It enumerates the flows the operator's autonomous-coding goal requires the platform to execute *as a coherent system*, not as a collection of subsystems-that-individually-work.

If a subsystem is operational but its outputs do not flow through the chain to the next consumer, the integration is incomplete even though every box is green.

---

## Operator goal (verbatim, restated for orientation)

> "Phase 17 has produced 25 deliverables tonight + prior. Each closed on its own scope. The integrated flow — autonomous coding agent operating against a stack with InvenTree inventory awareness, cross-index context, asset/firmware tracking, registry consultation, provenance gating — has not been audited end-to-end."

> "Subsystems work; system-as-architecture has not been verified."

The audit treats "integrated" as: an autonomous-coding session can be initiated (Claude Code or local agent), and from that session the agent can transparently consume registry / cross-index / provenance / inventory / asset / project-management state without operator-side context-passing or manual lookup.

---

## Six target flows

Each flow has a **happy-path narrative**, a **structural requirement** (what must hold for the flow to be integrated, not subsystem-only), and an **integration boundary** (the seam most likely to be the gap).

---

### Flow A — Inference path

**Happy path.** Autonomous agent (Claude Code orchestrator OR local agent) issues a model request → consults `~/.platform-registry/inventory.json` for the litellm-gateway endpoint and bearer-credential location → routes to `litellm-gateway:4000` with bearer auth → litellm dispatches to backend (Ollama @ Mini, Ollama @ Studio post-D-17-15, exo @ Mini single-node post-D-17-30) → response returns to operator surface (terminal, Open WebUI, MCP-consumer).

**Structural requirement.**
- Registry is queryable from the agent's session at startup (D#25 doctrine codified).
- Backend route names are stable across registry, litellm config, and agent prompts.
- Each backend has a working tool-calling protocol path for the agent class that targets it (Claude Code → Anthropic native; subagent → Ollama native; Goose → blocked; future agents → unknown).

**Integration boundary.** Agent surface ↔ litellm route name ↔ backend OpenAI-compat fidelity. D-17-13 surfaced two upstream-blocked gaps in this seam (`local-tool-calling.md` Findings 1+2). The seam between "Claude Code talks Anthropic + subagent talks Ollama" and "any other agent host" is where integration breaks.

---

### Flow B — InvenTree inventory awareness

**Happy path.** Agent task references a hardware component (Mac Studio config, network gear, BLE printer) → agent queries InvenTree for component metadata (part #, supplier SKU, location, BOM context) → uses that context to make a recommendation that is grounded in real platform inventory rather than generic public knowledge.

**Structural requirement.**
- InvenTree contains the components the operator's autonomous-coding work depends on (hardware, accessories, firmware-bearing devices).
- An agent-consumable surface exists: either an InvenTree MCP server, an xindex axis covering InvenTree, or a documented HTTP path the agent can call directly.
- Cross-index normalization (D-16-02 lineage) covers InvenTree alongside NetBox + ADRs + OpenProject so a single agent query returns blended context.

**Integration boundary.** InvenTree → cross-index. RM-16-B-008 ("Cross-index service 4.E: extend cross-index-validate.py with InvenTree axis") is in Phase-16 backlog. Until that ships, the agent has access to NetBox + ADRs + OpenProject through xindex but NOT to InvenTree — InvenTree is queryable directly via REST but is not blended into the agent's normalized topology view. Bigger seam: InvenTree CSV import (RM-16-B-004) hasn't run, so InvenTree is empty even where xindex would surface it.

---

### Flow C — Asset / firmware / OS state awareness

**Happy path.** Agent considers an upgrade or change recommendation → consults asset state (OS version per node, firmware versions, container image versions, library dependencies) → flags pre-conditions ("Mac Mini is on 26.4.1 — RDMA-over-TB5 needs major-version match per Finding I, do not recommend upgrading until aligned with Studio") → does not recommend changes blind to current state.

**Structural requirement.**
- A per-asset state register exists, queryable by agent.
- Coverage spans OS / firmware / containers / images / library deps for hosts AND attached accessories (Garmin / Oura / Zigbee / 3D printer mainboards / ESP32) per Finding T scope.
- Refresh cadence is defined and the agent knows freshness ("last updated X minutes ago").

**Integration boundary.** Asset register ↔ agent context. **No asset register exists today.** Finding T is canonical: the 2026-05-02 macOS upgrade recommendation that triggered the D-17-25 reboot was AI-recommended without any asset-state consult because there was nothing to consult. Asset-management deliverable family is intake-doc'd (operator memory) but not yet framework-authored — the closest analog in the active backlog is RM-18-C-007 (Vault token rotation automation, narrow scope).

---

### Flow D — Provenance gate

**Happy path.** Agent suggests pulling a model → wrapper (`scripts/ollama-pull-verified.sh` or `hf-download-verified.sh`) runs Cisco Provenance Kit → exit 0 (verified-specific) or exit 3 (verified-base-family) lets the pull through; exit 1/2 blocks unless `PROVENANCE_OVERRIDE_REASON` is set → pull lands → registry sees the new image on next refresh → agent can consult registry to confirm the model is now available.

**Structural requirement.**
- Wrappers are the canonical interface for model pulls (no naked `ollama pull`).
- The wrapper output is captured to a per-pull provenance JSON record (`docs/_provenance/`).
- New models pulled through the wrapper appear in the registry on next refresh and in the agent's tool inventory if they're routable.

**Integration boundary.** Provenance JSON → agent context. The gate exists and is enforced by convention; the wrapper output exists as JSON; but **nothing currently surfaces "what models have been pulled, with what verdict, when" to the agent in a structured form**. Operator can read `docs/_provenance/*` manually; the agent cannot enumerate them via xindex / registry / MCP.

---

### Flow E — Documentation flow

**Happy path.** Agent consults CLAUDE.md → CLAUDE.md points to canonical sources (architecture-facts chronicles, runbooks, registry, framework §9) → agent reads the canonical source for the topic at hand (e.g., DNS authority → `opnsense-dns-authority.md`; exo cluster → `exo-cluster.md`; capability question → `known-capabilities.md`) → context loaded into the active turn before the agent acts.

**Structural requirement.**
- CLAUDE.md is current (D-17-24 closed) and points to canonical sources rather than duplicating their state.
- Architecture-facts chronicles are durable, versioned, and indexed by xindex so the agent can find them via tool call rather than guess at filenames.
- Each chronicle states its scope explicitly ("if this disagrees with X, this wins" per D#22).

**Integration boundary.** Chronicles ↔ xindex search. xindex MCP exposes `xindex_get_runbook`, `xindex_get_adr`, `xindex_get_service`, `xindex_search`, but **no `xindex_get_architecture_fact` or equivalent**. Agents must `Read` chronicles by guessed path, with no enumeration surface. CLAUDE.md doctrine block lists the 8 chronicles by name — that's the current surface.

---

### Flow F — Project management flow

**Happy path.** Operator (or auto-prioritization rule) asks "what's next?" → agent consults BOTH `PROJECT_FRAMEWORK.md` §9 (current phase deliverables) AND OpenProject queue (filter Backlog/In Progress, optionally `category=autonomous-coding`) → ranks candidate work by priority + dependency + autonomous-codability → recommends a single next deliverable → operator approves → agent executes.

**Structural requirement.**
- Framework §9 is canonical for the active phase (D-17-24 doctrine).
- OpenProject mirror is sync-current (D-17-04 + D-17-31).
- Autonomous-coding-relevant items are *queryably tagged* in OpenProject so the agent can filter for them without reading every backlog item.
- Sync flag inventory in CLAUDE.md matches the actual sync script CLI (D-17-31 doctrine claim).

**Integration boundary.** OpenProject categorization. The `autonomous-coding` category does not exist in OpenProject (verified 2026-05-03 via API: 65 categories present, including A11Y/AI/AUTO/AUTO-MECH/INT/INTEL but NOT `autonomous-coding`). The D-17-31 sync script falls back to a description-text marker (`[auto]` suffix in the title-label) when the category lookup returns None. 21 RM items carry the `[auto]` marker today; none carry the category. **Result: agents cannot filter OpenProject for autonomous-coding work via category — the doctrine in CLAUDE.md ("filter by category=autonomous-coding") is aspirational, not actual.**

---

## Cross-flow integration points

These are NOT flows themselves but are the seams every flow depends on:

1. **Service registry as universal substrate (D#25).** Every flow assumes the agent can query the registry at session start. The registry exists, refresh is launchd-scheduled (`Y` finding caveat: launchd not registered yet; loads on next login). Today an agent must run a 4-line python snippet (CLAUDE.md "convenience reader") to query — there is no MCP surface (`xindex-mcp` exposes service nodes but not registry credentials/ports/depended_on metadata).

2. **Xindex as the agent-consumable index of everything else.** Cross-index covers NetBox devices + services + ADRs + OpenProject WPs + runbooks. It does NOT cover: InvenTree parts, provenance records, registry credential metadata, architecture-facts chronicles, capability registry, asset state. Each of these is a separate enumeration surface (or none).

3. **Vault as credential mediator (Finding Z reservation).** Every agent path depends on Vault being unsealed. Cold-start order (seal-vault → vault-server → consumers) is documented but not automated. Finding Z flagged the architectural review as post-demo work; not in active backlog.

4. **CLAUDE.md as the agent's session-bootstrap doctrine.** Every Claude Code session loads CLAUDE.md verbatim. This is the agent's first context. If CLAUDE.md is stale or misclaims sync flags (current case for `--query-backlog`), all downstream agent reasoning is downstream of the staleness.

---

## What "integrated" looks like when done

A new Claude Code session in this repo can answer the following without operator hand-holding, by following pointers from CLAUDE.md only:

1. "What is the canonical port for service X?" → registry lookup, no guessing.
2. "What models can I route to?" → registry → litellm config → backend health, returns a clean route list with backends.
3. "Is this model attested?" → provenance JSON enumeration → answer per-model.
4. "What's my next autonomous-coding work?" → framework §9 + OpenProject filter by category → ranked list.
5. "What hardware do I have for this task?" → InvenTree query via cross-index axis → matched components.
6. "Is this upgrade safe?" → asset register → version-compatibility check → recommend / defer / block.

Today (pre-D-17-32 audit): #1 works (D-17-29). #2 partial (Goose blocked, Claude Code path works). #3 manual. #4 partial (no category filter). #5 not wired (cross-index InvenTree axis missing). #6 not wired (no asset register).

WP-03 traces each in detail.
