# Integrated AI Platform — Roadmap Master

This file is the **human-readable roadmap summary and strategic interpretation view** for the repository.

It is **not** the canonical item-state source.
Canonical item truth lives in:
- `docs/roadmap/items/RM-*.yaml`

## Architecture anchor

The roadmap is downstream of the master architecture.

Read `docs/architecture/MASTER_SYSTEM_ARCHITECTURE.md` first when you need to understand:
- what the system is trying to become
- what the shared runtime architecture is
- what the non-negotiable platform rules are
- why the roadmap is sequenced the way it is

Then use the roadmap files to understand planning, status, execution sequence, and grouped delivery.

## Authority rule

Read planning and roadmap files in this order:

1. `docs/architecture/MASTER_SYSTEM_ARCHITECTURE.md`
2. `docs/roadmap/ROADMAP_AUTHORITY.md`
3. `docs/governance/CURRENT_OPERATING_CONTEXT.md`
4. `docs/governance/DOCUMENT_STATE_INDEX.md`
5. canonical item YAML under `docs/roadmap/items/`
6. derived planning/dependency/data surfaces
7. `docs/roadmap/ROADMAP_STATUS_SYNC.md`
8. `docs/roadmap/ROADMAP_MASTER.md`
9. `docs/roadmap/ROADMAP_INDEX.md`
10. `docs/roadmap/POST_CONVERGENCE_OPERATING_MODE.md`
11. `docs/execution_modes/EXECUTION_ROUTER.md`
12. relevant tool-specific mode doc
13. `docs/governance/PROMPT_PACKET_STANDARD.md`
14. planning/supporting docs as needed

## What this file does

This file explains:
- current operating posture
- strategic priorities
- backlog interpretation
- what kinds of work should be emphasized next

This file does **not** control item completion or archive truth.

## Current operating posture

The repository is now best treated as a **governed local-execution platform in post-convergence mode**.

That means:
- the targeted local-autonomy upgrade chain is no longer the default active build focus
- the autonomy substrate is treated as materially closed unless canonical repo truth shows regression or contradiction
- future work should extend the governed platform rather than re-litigate its foundation by default

## Targeted closure chain now treated as materially closed

The following chain is accepted as closed and no longer provisional unless future canonical repo truth contradicts it.

### Substrate / control layer
- `RM-UI-005`
- `RM-GOV-001`
- `RM-OPS-004`
- `RM-OPS-005`

### NEXT-tier autonomy expansion
- `RM-GOV-009`
- `RM-AUTO-001`
- `RM-DEV-001`

### Integrated post-substrate expansion
- `RM-OPS-006`
- `RM-HOME-005`
- `RM-INTEL-003`
- `RM-INV-003`

### Operational convergence / terminal-state hardening
- `RM-OPS-007`

### Final held-item resolution
- `RM-DEV-008`
- `RM-DEV-009`

No residual `ready_for_archive` hold state should remain for that targeted closure chain.

## What the closed chain means going forward

Those items should now be treated as:
- platform foundations
- operating constraints
- acceptance standards for future work

They should **not** be treated as the default active pull queue unless canonical repo truth shows regression or contradiction.

## Primary objective after convergence

The most important program objective is now to preserve the governed local-execution platform and extend it without drift.

That means future work should prioritize:

1. preserving canonical truth and regeneration discipline
2. preserving bounded execution, artifact evidence, and validator-driven closeout
3. extending the platform through reusable connectors, ingress channels, workflows, and domain branches
4. avoiding summary-doc drift, local-only closeout, and narrative completion claims

## Immediate strategic implication

The repo is no longer in default “build the autonomy substrate” mode.
It is now in **post-convergence operating mode**.

So the next substantive work should come from:
- governed platform extension
- connector/workflow expansion
- domain expansion on top of the governed runtime
- business and operator workflow additions

## Current repo-state interpretation

Current operating interpretation:
- local execution sovereignty: affirmative
- governed selector: active
- chosen next eligible target: none
- blocked placeholder items: none
- current hold set: none

## Post-convergence work categories

### Platform extension
Examples:
- multi-channel ingress
- new control surfaces
- message/voice ingress
- remote operator access
- governed action dispatch

### Connector and workflow expansion
Examples:
- GitHub / Calendar / Gmail reuse
- media system dispatch
- communication and notification workflows
- internal/external system connector reuse

### Domain expansion
Examples:
- voice/ambient assistant behavior
- intelligence/news
- procurement intelligence
- communication workflows
- business operations workflows

### Governance preservation
Examples:
- truth-surface integrity
- archive convergence
- execution/validation discipline
- acceptance-gate hardening

## Closeout acceptance rule

No roadmap closeout is accepted until the change is:
1. committed
2. pushed
3. remote-visible

Local-only state is not accepted closure.

## High-value newly captured directions

The roadmap now explicitly captures or strengthens these directions:

- `RM-HOME-005` — local voice and ambient assistant layer for Alexa/Google Home replacement using Home Assistant as the device bridge
- `RM-INTEL-003` — personalized real-news briefing with interest-aware ranking, source-quality controls, and anti-clickbait summarization
- `RM-OPS-006` — governed desktop computer-use and non-API automation layer for local operator tasks
- `RM-OPS-007` — emulator and governed BlueStacks automation lab for bounded computer-use experiments (conditional/later)
- `RM-OPS-009` — caller identity, reverse phone lookup, and communication screening layer
- `RM-OPS-010` — lawful tenant and worker screening workflow using public-record and approved verification sources
- `RM-GOV-009` — GitHub, Google Calendar, and Gmail connector posture as first-class control-plane priorities
- `RM-INV-003` — hardware upgrade-value and cost/performance justification logic

## Historical note on autonomy planning documents

`LOCAL_AUTONOMY_CRITICAL_PATH.md` should now be treated as a historical transition document.
It remains useful for understanding how the substrate was closed, but it is no longer the default current-state planning posture.

## Durable storage rule

To prevent roadmap drift or split authority:
- do not use this file as direct status truth
- keep this file aligned with canonical item YAML and synchronized status views
- use execution packs for detailed execution context, not completion truth
- keep this file aligned with `MASTER_SYSTEM_ARCHITECTURE.md` and `POST_CONVERGENCE_OPERATING_MODE.md` when platform direction changes

## Reader rule

When in doubt:
1. use `docs/architecture/MASTER_SYSTEM_ARCHITECTURE.md` for architecture truth
2. use `ROADMAP_AUTHORITY.md` for authority rules
3. use `CURRENT_OPERATING_CONTEXT.md` for the short start-here posture
4. use `DOCUMENT_STATE_INDEX.md` to identify document role and authority
5. use canonical item YAML for item truth
6. use derived planning surfaces for machine-generated queue/dependency state
7. use `ROADMAP_STATUS_SYNC.md` for synchronized human-readable status rollup
8. use this file for strategic interpretation
9. use `POST_CONVERGENCE_OPERATING_MODE.md` for operating posture
10. use the execution router and relevant tool-mode doc when selecting an implementer
