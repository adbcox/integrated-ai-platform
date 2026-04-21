# CMDB-Lite Registry Specification

**Spec ID**: CMDB-LITE-SPEC-1  
**Status**: active  
**Date**: 2026-04-21  
**Phase linkage**: Phase 0 (governance_source_of_truth_reconciliation), Phase 1 (runtime_contract_foundation)  
**Authority sources**: P0-01-AUTHORITY-SURFACE-INVENTORY-1, ADR-0001 through ADR-0007, governance/canonical_roadmap.json, governance/runtime_contract_version.json, governance/next_package_class.json

---

## Purpose

The **CMDB-lite registry** is the architecture/runtime authority surface for the integrated AI platform. It provides a single machine-readable YAML file that records the current state of:

- Phase and phase history
- Subsystem inventory
- Migration map for legacy/frozen surfaces
- Model profiles for LOCAL-FIRST routing
- Runtime contract components
- Artifact policy
- Adapter status
- Active waivers and deferrals
- Autonomy scorecard baseline
- Environment inventory

The registry is not a substitute for the detailed governance artifacts under `governance/`. It is a consolidated view that enables:
1. Quick auditing of platform state across all major dimensions
2. Machine-verifiable checks that required sections are present
3. A single anchor point for cross-cutting governance queries

---

## Registry File

**Path**: `governance/cmdb_lite_registry.v1.yaml`  
**Format**: YAML (stdlib `PyYAML` / `yaml` module)  
**Version field**: `registry_version` (semver string, e.g. `"1.0.0"`)

---

## Required Top-Level Sections

All 11 sections are required. Missing any section is a hard stop in the validation script.

| Section | Description | Primary authority |
|---------|-------------|-------------------|
| `registry_version` | Semver version of this registry file | This spec |
| `phase` | Current phase, status, allowed class, history | `governance/canonical_roadmap.json`, `governance/current_phase.json` |
| `subsystems` | Named subsystem inventory | `governance/canonical_roadmap.json` |
| `migration_map` | Disposition of legacy/frozen surfaces | `governance/authority_adr_0001_source_of_truth.md` |
| `model_profiles` | LOCAL-FIRST model routing profiles | `CLAUDE.md`, ADR-0004 |
| `runtime_contract` | Runtime contract components and ADR refs | `governance/runtime_contract_version.json`, ADR-0001 through ADR-0006 |
| `artifact_policy` | Artifact root, retention, canonical paths | ADR-0006 |
| `adapter_status` | Aider, Claude, Codex, Ollama status | ADR-0004 |
| `waivers` | Active governance exceptions and deferrals | Per-waiver authority |
| `autonomy_scorecard` | Phase 7 baseline and dimension scores | ADR-0007, `governance/phase7_closure_evidence.json` |
| `environments` | Host/environment inventory (placeholder permitted) | This spec |

---

## Required Subsystem Keys

The `subsystems` section must include at minimum:

- `control_plane` — governance authority, ADR chain, phase gate enforcement
- `inference_fabric` — inference backend routing (Ollama + remote API)
- `agent_runtime` — job scheduling, worker pool, executor abstraction
- `retrieval_memory` — stage RAG pipeline, BM25/entity-aware retrieval
- `evaluation_governance` — benchmarking, validation, autonomy scoring

Additional subsystems may be added. Existing subsystem keys must not be removed without a superseding registry version and migration map entry.

---

## Required Model Profiles

The `model_profiles` section must include at minimum:

- `fast` — default local iteration model
- `balanced` — bounded multi-file modification profile
- `hard` — complex task model

Additional profiles may be added.

---

## Required Runtime Contract Components

The `runtime_contract` section must include at minimum:

- `session_job_schema` — ADR-0001 anchor + Python impl reference
- `tool_contract` — ADR-0002 anchor + Python impl reference
- `workspace_contract` — ADR-0003 anchor + Python impl reference
- `artifact_contract` — ADR-0006 anchor + Python impl reference

---

## Required Autonomy Scorecard Fields

The `autonomy_scorecard` section must include at minimum:

- `first_pass_success` — semantic/primary generation rate
- `retry_count` — average retries before validation pass
- `escalation_rate` — fraction of steps requiring escalation
- `artifact_completeness` — fraction of required artifacts produced

---

## Versioning

The registry uses semver (`MAJOR.MINOR.PATCH`):
- **MAJOR**: Breaking structural change (section removed or renamed)
- **MINOR**: New section added or existing section substantially extended
- **PATCH**: Content update within existing structure (e.g., phase status change)

When the registry is updated, the `registry_version` field must be incremented. The file is named `cmdb_lite_registry.v{MAJOR}.yaml` — a MAJOR version bump requires a new file.

---

## Relationship to Governance Artifacts

The CMDB-lite registry is a **read surface** — it reads from and summarizes authoritative governance artifacts but does not replace them:

| Registry field | Authoritative source |
|----------------|---------------------|
| `phase.current` | `governance/current_phase.json` |
| `phase.current_allowed_class` | `governance/next_package_class.json` |
| `runtime_contract.contract_version` | `governance/runtime_contract_version.json` |
| `phase.phase_history` | `governance/canonical_roadmap.json` |
| `autonomy_scorecard` | `governance/phase7_closure_evidence.json` + ADR-0007 |
| `migration_map` | `governance/authority_adr_0001_source_of_truth.md` |

If any registry field conflicts with its authoritative source, the authoritative source wins.

---

## Relationship to ADRs

- **ADR-0001**: `runtime_contract.session_job_schema` references this ADR
- **ADR-0002**: `runtime_contract.tool_contract` references this ADR
- **ADR-0003**: `runtime_contract.workspace_contract` references this ADR; `artifact_policy.canonical_paths` implements the workspace contract path conventions
- **ADR-0004**: `model_profiles` and `adapter_status` implement the inference gateway routing rules
- **ADR-0005**: `runtime_contract.permission_model` references this ADR
- **ADR-0006**: `artifact_policy` implements the artifact bundle path conventions
- **ADR-0007**: `autonomy_scorecard` implements the scorecard dimensions defined in this ADR

---

## Example

See `governance/cmdb_lite_registry.v1.yaml` for the current v1 registry.
