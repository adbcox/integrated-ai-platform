# Workspace Contract Specification

**Spec ID**: WORKSPACE-CONTRACT-SPEC-1  
**Status**: active  
**Date**: 2026-04-21  
**Phase linkage**: Phase 1 (runtime_contract_foundation)  
**Authority sources**: ADR-0003 (workspace contract), governance/definition_of_done.v1.yaml, governance/execution_control_package.schema.json

---

## Purpose

This document specifies the workspace contract for all coding runs in the integrated AI platform. A **workspace** is the bounded execution environment in which a session operates. The contract defines what a session may read, what it may write, where outputs must land, and how the workspace is cleaned up at session end.

The machine-readable form is `governance/workspace_contract.v1.yaml`. This document is the human-readable companion.

---

## The Arbitrary-Write Prohibition

> **Runtime work must not write arbitrary repo-relative artifacts during execution.**

This is the defining constraint of the workspace contract. Every persistent output must be declared in the package's `allowed_files` or `artifact_outputs`. An undeclared file appearing in `git status` at session end is a contract violation.

This rule exists because unrestricted writes would allow sessions to silently modify governance artifacts, framework code, or roadmap state — bypassing the authority chain established in ADR-0001.

---

## Three Zones

Every workspace has three distinct zones:

| Zone | Mutability | Persistence | Committed |
|------|-----------|-------------|-----------|
| Source mount | Read-only (writes require `allowed_files`) | Permanent | Yes (via explicit commit) |
| Scratch mount | Writable | Ephemeral | No |
| Artifact root | Writable (declared paths only) | Permanent | Yes (force-add for governance) |

---

## Source Mount

The source mount is the repository working tree. All files in the repo are readable. Writes are forbidden by default.

**A write is authorized only when the target file appears in the package's `allowed_files` list AND does not appear in `forbidden_files`.**

Authorized operations:
- Read any file
- List directory contents
- Compute file hashes for telemetry
- Import Python modules for validation

Forbidden operations:
- Write to any file not in `allowed_files`
- Delete any file not in `rollback_rule.remove_on_failure`
- Rename or move files outside package scope
- Modify git history without explicit user instruction

---

## Scratch Mount

The scratch mount is a temporary writable area for intermediate work. It is:

- Created at session initialization
- Scoped to a single session (not shared)
- Cleaned up at session end
- Never committed to the repository

Scratch is typically the system temp directory (`/tmp`) or the pytest `tmp_path` fixture.

**Scratch paths must never be declared as `artifact_output` paths.** An artifact declared at a `/tmp/...` path would be absent after scratch cleanup.

---

## Artifact Root

All session outputs that must persist are written to an artifact root path:

| Output type | Path |
|-------------|------|
| Governance artifacts | `artifacts/governance/` |
| Baseline validation | `artifacts/baseline_validation/` |
| Capability expansion | `artifacts/expansion/` |
| Escalation records | `artifacts/escalations/` |
| ADR documents | `docs/adr/` |
| Spec documents | `docs/specs/` |
| Governance state files | `governance/` |

The `artifacts/` directory is in `.gitignore`. Governance artifacts under `artifacts/governance/` must be committed with `git add -f`.

---

## Cleanup Policy

### On success

- Scratch contents discarded
- All `allowed_files` changes committed; no uncommitted changes in source mount
- All declared `artifact_outputs` present and committed

### On failure (gate failure or hard stop)

- Scratch discarded (unless `retain_on_failure=true`)
- Execute `rollback_rule.remove_on_failure`; restore any unauthorized writes
- Partial artifacts may remain; listed in `hard_stops_hit`

### On escalation

- Scratch retained for diagnostics
- Source mount not committed; left for control window review
- Artifacts produced before escalation trigger retained

### Preserve unrelated changes

**`preserve_unrelated_changes=true` is non-negotiable.** Cleanup must never remove, overwrite, or revert files not created or modified by the current session. Pre-existing state outside `allowed_files` is inviolable.

---

## Path Scope Rules

### `repo_write_forbidden_by_default = true`

Sessions may not write to arbitrary repository paths. Only paths in `allowed_files` are writable. This is a hard stop — not a warning.

### Allowed workspace targets

New files may be written to:
- `governance/*.yaml`, `governance/*.json` (new files only)
- `docs/adr/*.md`, `docs/specs/*.md` (new files only)
- `artifacts/governance/*.json`, `artifacts/baseline_validation/*.json`
- `bin/run_*.py` (new runner scripts only)
- `tests/test_*_seam.py` (new seam tests only)

### Always forbidden paths

Regardless of `allowed_files`, these paths are never writable without ESCALATION:

- `governance/canonical_roadmap.json`
- `governance/authority_adr_*` (existing files)
- `governance/current_phase.json`
- `governance/phase_gate_status.json`
- `governance/next_package_class.json`
- `governance/schema_contract_registry.json`
- `config/promotion_manifest.json`
- `framework/**` (all files)

---

## Exceptions

### Artifacts `.gitignore` override

`artifacts/` is gitignored. Governance artifacts under `artifacts/governance/` must be committed with `git add -f`. This is the only approved override of the normal git add workflow for artifact persistence.

### Scratch `tmp_path` exception

Pytest `tmp_path` writes during test execution are authorized scratch-mount writes. They do not require `allowed_files` authorization and must not be used as `artifact_output` paths.

### Rollback removes only package files

The rollback exception permits removal of files in `rollback_rule.remove_on_failure`. This never applies to pre-existing files — only to files the current package itself created.

### Runtime artifacts not arbitrary repo writes

Runtime work (stage probes, manager scripts, framework execution) must not write arbitrary repo-relative artifacts during execution. All outputs must go to declared artifact root paths. Any untracked file in `git status` at session end that is not in `allowed_files` and not gitignored is a contract violation.

---

## Relationship to ADRs and Governance

| Contract element | Authority |
|-----------------|-----------|
| Workspace zones | ADR-0003 (workspace contract — `allowed_write_paths`, `forbidden_write_paths`) |
| Preserve unrelated changes | DoD `rollback_semantics.preserve_unrelated_changes` |
| Artifact root paths | ADR-0006 (artifact bundle — `canonical_paths`) |
| Forbidden paths | `execution_control_package.schema.json::forbidden_files` |
| Cleanup semantics | ADR-0003 (`cleanup_policy`, `failed` state) |
| Scratch mount | ADR-0003 (workspace contract — scratch zone) |

---

## Example

A typical SUBSTRATE package declares:

```yaml
allowed_files:
  - governance/workspace_contract.v1.yaml
  - docs/specs/workspace_contract.md
  - bin/run_workspace_contract_check.py
  - tests/test_workspace_contract_seam.py

artifact_outputs:
  - path: artifacts/governance/workspace_contract_validation.json
    artifact_id: P1-03-WORKSPACE-CONTRACT-VALIDATION-1
    required_fields: [artifact_id, generated_at, yaml_loaded, ...]
```

The workspace contract enforces:
1. Only those 4 source files and 1 artifact are writable
2. All other repo paths are read-only for this session
3. Scratch (`tmp_path`) is available for test fixtures
4. The artifact is force-added at commit time
