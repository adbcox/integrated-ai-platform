# ADR 0022: Component Adoption Shortlist — Closed Decisions

**Status**: Ratified
**Package**: ADOPT-SHORTLIST-LOCK-1
**Date**: 2026-04-20
**Authority owner**: governance

## Decision

All remaining open software adoption decisions are closed. The canonical machine-readable record is `governance/component_adoption_shortlist.json`.

### Mandatory Core (adopt now, always required)

| Component | Phase | Role |
|---|---|---|
| Ollama | phase1 | default local model manager |
| MCP | phase2 | external tool protocol boundary |
| Qdrant | phase2 | semantic memory and vector retrieval |
| gVisor | phase2 | default execution sandbox |
| Aider RepoMap | phase3 | repo understanding and edit adapter |
| SWE-bench | phase3 | benchmark harness |

### Approved Optional (adopt now, activate on evidence)

| Component | Phase | Role |
|---|---|---|
| vLLM | phase1_optional | heavy-model backend when GPU throughput is the bottleneck |
| OpenHands SDK patterns/components | phase2 | workspace isolation and tool invocation patterns only |

### Approved Later Phase (approved now, integrate in scheduled phase only)

| Component | Phase | Role |
|---|---|---|
| Backstage | phase5 | developer portal and software catalog |
| GLPI | phase5 | default authoritative CMDB |
| CloudQuery | phase5_optional | read-only CMDB enrichment from cloud APIs |

### Conditional Only (approved only on specific evidence trigger, not before Phase 6)

| Component | Phase | Role |
|---|---|---|
| Firecracker | phase6_plus | microVM sandbox if gVisor isolation is proven insufficient |
| Temporal | phase6_plus | durable workflow backbone if checkpoint-resume is proven insufficient |

### Rejected as Default

| Component | Decision |
|---|---|
| i-doit | Not default. Reconsider only if GLPI is rejected operationally or strict ITIL relationship modeling is a hard gate. |

## Rationale

### Adopt commodity infrastructure

All mandatory core components are commodity open-source infrastructure with stable REST/protocol interfaces. None of them own business logic; all business logic lives in repo-owned wrappers and adapters.

### Keep repo-owned contracts local

Every adopted component must route through a repo-owned surface:

- `internal_inference_gateway` — owns all model invocation; no stage or manager calls Ollama, vLLM, or any model backend directly
- `permission_engine` — owns all tool permission decisions; no component bypasses it
- `workspace_contract` — owns all workspace isolation scope; no component self-scopes its filesystem access
- `artifact_schema` — owns all artifact persistence contracts; no component writes directly to `artifacts/` without going through the schema
- `promotion_rules` — owns all promotion and lane decisions; no component self-promotes

### Integrate in phase order

Mandatory core components are integrated in phase order beginning at their `phase_target`. Approved-later and conditional components are not forced into the current critical path regardless of technical feasibility.

### "Fully implement the list" means

All decisions are closed **now** in this ADR and the shortlist artifact. "Implement" means:

1. All 14 decisions are recorded and will not be re-litigated as open decisions.
2. All approved components have pinned source URLs, licenses, wrapper owners, and bypass prohibitions recorded now.
3. Only phase-appropriate components are integrated immediately (mandatory core at phase1–3).
4. Later-phase and conditional components are approved but not forced onto the current critical path.
5. i-doit is rejected as default and does not appear in any implementation plan unless the explicit conditional trigger fires.

## Authority

This ADR ratifies `governance/component_adoption_shortlist.json` (package_id: ADOPT-SHORTLIST-LOCK-1).

No runtime code changes, manifest changes, or test changes are authorized by this ADR.
