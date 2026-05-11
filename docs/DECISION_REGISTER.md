# Decision Register

Index of platform-level decisions captured in Architecture Decision
Records. One line per decision, with a pointer to the ADR for the
full context, decision, and consequences.

The canonical store for ADRs is `docs/adr/`. This file is the index
that lets a reader navigate the platform's decision history without
opening every ADR. Add a row when you create a new ADR; never write
the decision content here.

## Architecture and runtime

| ADR | Title | One-line summary |
|-----|-------|------------------|
| [A-001](adr/ADR-A-001.md) | Retain the existing control plane | Continue using the Mac Mini as the platform's control plane through Phase 13. |
| [A-002](adr/ADR-A-002.md) | Shared runtime substrate is mandatory | All platform services run on a single shared substrate (Docker on Mac Mini today, portable to Linux). |
| [A-008](adr/ADR-A-008.md) | Branches may not fork the platform | Single mainline; no long-lived feature branches. |

## Coding posture and AI subsystems

| ADR | Title | One-line summary |
|-----|-------|------------------|
| [A-003](adr/ADR-A-003.md) | Ollama-first is the default coding posture | Local Ollama is the default LLM; Anthropic Pro is reserved for high-judgment tasks. |
| [A-004](adr/ADR-A-004.md) | Aider is an adapter, not a backbone | Aider integrates into the platform; the platform does not depend on Aider's lifecycle. |
| [A-005](adr/ADR-A-005.md) | Claude Code is supervisory or exceptional | Routine work runs under `claude-local`; `claude-pro` is for supervisory or genuinely high-judgment tasks. |
| [A-020](adr/ADR-A-020-track2-agent-roles.md) | Track 2 Agent Role Codification | Codifies work-class × LiteLLM-tier × default-model × capability-boundary for the six verified Track 2 agents (Aider/Goose/Serena/OpenCode/Continue/OpenHands). Q-1 through Q-7 resolved 2026-05-11 per Thread A WP-4: cross-cutting `.env`+SSH prohibition (Q-1); OpenCode inherits Aider TIER 1 doc-authoring refusal (Q-2); Serena classified MCP tool (Q-3); Continue pinned to `qwen2.5-coder:7b` T1 (Q-4); Cline v1.1 amendment post-Brief D (Q-5); OpenHands T3 default with operator-supervised T2 escape hatch (Q-6); Goose Posture 0 supervised-only no autonomous recipes (Q-7). |

## Documentation, ADR governance, and external systems

| ADR | Title | One-line summary |
|-----|-------|------------------|
| [A-006](adr/ADR-A-006.md) | Repo docs are canonical for architecture and roadmap planning | The repo is the source of truth; external surfaces (Notion, OpenProject, etc.) are derived views. |
| [A-010](adr/ADR-A-010-external-systems.md) | External systems should be adopted where commodity fit is strong | Adopt commodity tools (Vault, NetBox, OpenProject, Grafana) rather than building from scratch. |
| [A-018](adr/ADR-A-018-replace-plane-with-openproject.md) | Replace Plane CE with OpenProject CE as PM substrate | OpenProject's work-package primitive + HAL JSON API fit the PMP+ITIL framework where Plane CE's Issue model did not; xindex schema renamed `plane_*` → `op_*`. |

## Operations and security

| ADR | Title | One-line summary |
|-----|-------|------------------|
| [A-007](adr/ADR-A-007-media-sync-syncthing.md) | Syncthing replaces rclone SFTP for seedbox→QNAP transfers | Move bulk transfers off SFTP onto Syncthing for reliability and bandwidth telemetry. |
| [A-009](adr/ADR-A-009.md) | Vault as authoritative secret store — migration from .env | All secrets live in Vault; `.env` files for credentials are forbidden. |
| [A-017](adr/ADR-A-017-vault-warm-copy-backup-strategy.md) | Vault file-backend warm-copy is the backup strategy | Warm-copy `/vault/data` to a host-readable snapshot for Restic; routine backup never touches Vault's seal cycle. |

## Operating model (Phase 13 doctrine)

| ADR | Title | One-line summary |
|-----|-------|------------------|
| [A-011](adr/ADR-A-011-ivv-loop-pattern.md) | IV&V loop pattern | Every state-changing sub-stage runs audit → execution → validation → regression. |
| [A-012](adr/ADR-A-012-equivalence-harness-doctrine.md) | Equivalence harness for source-of-truth migrations | Source-of-truth migrations must run a `--verify-roundtrip` probe at migration time, not deprecation time. |
| [A-013](adr/ADR-A-013-folded-gates-doctrine.md) | Folded gates for mechanical pattern applications | Gates fold to a single review when the pattern is already load-bearing in the same session and the application is mechanical. |

## CMDB and data governance

| ADR | Title | One-line summary |
|-----|-------|------------------|
| [A-014](adr/ADR-A-014-netbox-cmdb-authority.md) | NetBox as Authoritative CMDB | NetBox is the single source of truth for service inventory, node inventory, and network topology. |
| [A-015](adr/ADR-A-015-staged-toggle-migration.md) | Staged-Toggle Pattern for Source-of-Truth Migrations | Migrate data sources via env-var toggle with equivalence harness; never hard-cutover. |
| [A-016](adr/ADR-A-016-canonical-patterns-registry.md) | Canonical Patterns Registry | `docs/architecture-patterns/` is the authoritative store for reusable cross-cutting patterns (merged from `docs/canonical-patterns/` 2026-05-03 by D-17-16). |

## Conventions

- New ADRs are added to `docs/adr/` and indexed here in the same commit.
- ADRs are immutable once Accepted; supersede via a new ADR.
- This register is the navigation aid; the ADR itself is the load-
  bearing artefact. If the two disagree, the ADR is canonical.
