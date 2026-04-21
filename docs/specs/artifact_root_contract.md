# Artifact Root Contract Specification

**Spec ID**: ARTIFACT-ROOT-CONTRACT-SPEC-1  
**Status**: active  
**Date**: 2026-04-21  
**Phase linkage**: Phase 1 (runtime_contract_foundation)  
**Authority sources**: ADR-0006 (artifact bundle), governance/definition_of_done.v1.yaml, governance/execution_control_package.schema.json

---

## Purpose

This document specifies the artifact root contract for all coding runs in the integrated AI platform. The **artifact root** is the collection of declared repository paths where session outputs that must persist are written. The contract defines what qualifies as an artifact root path, what may be written there, how artifacts are retained, and what separates the artifact root from the source mount and scratch mount.

The machine-readable form is `governance/artifact_root_contract.v1.yaml`. This document is the human-readable companion.

---

## The Arbitrary-Write Prohibition

> **Sessions must not write arbitrary repo-relative artifacts during execution.**

Every persistent output must be declared in the package's `artifact_outputs` or `allowed_files`. An undeclared file appearing in `git status` at session end is an artifact root separation violation.

---

## Artifact Root Paths

The canonical artifact root paths are:

| Output type | Path |
|-------------|------|
| Governance artifacts | `artifacts/governance/` |
| Baseline validation | `artifacts/baseline_validation/` |
| Capability expansion | `artifacts/expansion/` |
| Escalation records | `artifacts/escalations/` |
| ADR documents | `docs/adr/` |
| Spec documents | `docs/specs/` |
| Governance state files | `governance/` |

`artifacts/` is in `.gitignore`. Governance artifacts under `artifacts/governance/` must be committed with `git add -f`. This is the approved exception to normal git add behavior.

---

## Separation Rules

The artifact root is distinct from the source mount and scratch mount:

| Property | Source mount | Scratch mount | Artifact root |
|----------|-------------|---------------|---------------|
| Mutability | Read-only by default | Fully writable | Declared paths only |
| Persistence | Permanent | Ephemeral | Permanent |
| Committed | Yes (via explicit commit) | No | Yes (force-add for governance) |
| Authorization | `allowed_files` entry | None required | `artifact_outputs` declaration |

Key separation rules:
- `repo_relative_writes_forbidden = true` — arbitrary repo-relative writes are prohibited
- `arbitrary_repo_writes_forbidden = true` — outputs must land at declared artifact root paths
- `scratch_cannot_be_artifact = true` — `/tmp` and `pytest tmp_path` are never artifact root paths
- `framework_is_not_artifact_root = true` — `framework/` paths are never valid artifact outputs

---

## Write Policy

Writes to the artifact root require declaration:

- **JSON/YAML artifacts**: must appear in `artifact_outputs` with `artifact_id` and `required_fields`
- **Source files** (specs, ADRs, governance YAML): must appear in `allowed_files`

An undeclared artifact root write is a violation even if the path is canonical.

Overwriting an existing artifact requires an explicit `allowed_files` or `artifact_outputs` entry naming that exact file. The "new files only" convention applies by default.

---

## Retention Policy

| Path | Retention | Commit required | Force-add required |
|------|-----------|-----------------|-------------------|
| `artifacts/governance/` | Indefinite | Yes | Yes |
| `artifacts/baseline_validation/` | Per CMDB policy | Yes | Yes |
| `artifacts/expansion/` | Per CMDB policy | No | No |
| `artifacts/escalations/` | Indefinite | Yes | No |
| `docs/adr/`, `docs/specs/` | Indefinite | Yes | No |

Governance artifacts (`artifacts/governance/`) are retained indefinitely — they are authority-chain evidence and must never be auto-purged.

---

## Artifact Bundle Rules

Every governance artifact must include:

| Field | Description |
|-------|-------------|
| `artifact_id` | Unique identifier following `P<N>-<NN>-<SLUG>-<N>` pattern |
| `generated_at` | ISO 8601 timestamp with timezone |
| `artifact_outputs` | List of paths produced |
| `content_hash` | SHA-256 of artifact content (hex) |
| `phase_linkage` | Phase and package this artifact belongs to |
| `authority_sources` | ADRs and governance files grounding this artifact |

`artifact_id` pattern: `^[A-Z][A-Z0-9]*-[A-Z0-9]+-[A-Z0-9-]+-[0-9]+$`

---

## Exceptions

### `.gitignore` override for `artifacts/governance/`

`artifacts/` is gitignored. Governance artifacts must be committed with `git add -f`. Approved exception for governance artifact persistence only.

### Seam test `tmp_path` writes

Seam tests may write artifacts to `pytest tmp_path` to verify artifact shape without persisting. These are scratch-mount writes and must not be declared in `artifact_outputs`.

### `latest.json` overwrite

`artifacts/baseline_validation/latest.json` may be overwritten without a new `artifact_id` if the package's `allowed_files` explicitly names it. Approved for rolling baseline snapshots only.

### Partial artifacts on failure

On gate failure, partial artifacts may remain in artifact root paths. They must be listed in `hard_stops_hit` and `residual_notes`. They are not accepted until the full validation sequence reruns and passes.

---

## Relationship to ADRs and Governance

| Contract element | Authority |
|-----------------|-----------|
| Canonical paths | ADR-0006 (artifact bundle — `canonical_paths`) |
| Separation rules | workspace_contract.v1.yaml `separation_rules` |
| Write policy | ADR-0003 (workspace contract — `allowed_write_paths`) |
| Retention | governance/cmdb_lite_registry.v1.yaml `artifact_policy` |
| gitignore override | workspace_contract.v1.yaml `exceptions.artifacts_gitignore_override` |
