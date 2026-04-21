# ADR 0023: RM-DEV-005A Adapter Boundary and OSS Authority Closure

**Status**: Ratified  
**Package**: RM-DEV-005A  
**Date**: 2026-04-21  
**Authority owner**: governance

## Decision

For RM-DEV-005A, Aider is ratified as a **controlled adapter / transport target only**.
This decision is **final for RM-DEV-005A**.

### Allowed role

- bounded adapter endpoint for local execution transport
- repo-owned wrapper surface under `framework/*` + `bin/*`
- optional execution target behind local-first policy and governance gates
- any Aider use must sit behind repo-owned runtime, gateway, and authority surfaces

### Prohibited role

- architecture backbone
- primary long-term orchestration engine
- policy authority
- artifact authority
- state authority
- permanent direct coupling between Aider and core runtime
- permanent direct coupling between Aider and Ollama as architecture
- bypass of repo-owned inference, permission, workspace, artifact, or promotion boundaries

## Prohibited patterns (explicitly blocked)

- `aider_as_architecture_backbone`
- `aider_as_policy_authority`
- `aider_as_artifact_authority`
- `aider_as_state_authority`
- `permanent_direct_aider_to_core_runtime_coupling`
- `permanent_direct_aider_to_ollama_coupling`
- `direct_bypass_of_repo_owned_gateway_or_authority_surfaces`

## Boundary and ownership model

- **Boundary owner**: repo-owned adapter layer (`framework/aider_*`, `framework/live_aider_*`, `bin/run_aider_*`)
- **Policy owner**: governance authority artifacts under `governance/`
- **Integration rule**: all Aider usage remains behind adapter boundaries and may be removed/replaced without changing stage/manager architecture

## OSS intake linkage

RM-DEV-005A ratifies OSS intake decisions as repo-visible authority via:

- `governance/oss_intake_registry.v1.yaml`
- `governance/rm_dev_005a_authority_state.v1.yaml`

These files are authoritative for shortlist fields, pins/placeholders, boundaries, and rollback/removal strategy.
